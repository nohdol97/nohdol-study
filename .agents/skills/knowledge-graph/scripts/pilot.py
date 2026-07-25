#!/usr/bin/env python3
"""Measure the deterministic baseline against a candidate index, safely.

Comparing another index means pointing a tool at notes the user wrote. The
rule that matters more than any measurement is that the corpus comes back
unchanged, so this hashes every file before and after and fails when one moved,
whatever the candidate reported.

The candidate command is supplied rather than assumed. This repository does not
ship invocations for a tool it has not run: a command line written from memory
for an uninstalled CLI is the kind of unverified claim the harness exists to
prevent. Install the tool, read its help, and pass the exact read-only command.

Usage:
  pilot.py --corpus PATH [--candidate 'CMD'] [--label NAME]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time


GRAPH_SCRIPT = Path(__file__).with_name("build_graph.py")
# Anything that could write, reformat, or reset is refused before it runs.
# Matching is per hyphen- or underscore-separated segment, so `write-note` is
# caught while `format` does not trip on the `rm` inside it.
FORBIDDEN = {
    "format", "write", "reset", "import", "sync", "delete", "remove", "rm",
    "move", "mv", "edit", "force", "init", "overwrite", "prune",
}


def segments(word: str) -> set[str]:
    parts = {word}
    for separator in "-_=/":
        parts = {piece for part in parts for piece in part.split(separator)}
    return {piece for piece in parts if piece}


def snapshot(corpus: Path) -> dict[str, str]:
    digests: dict[str, str] = {}
    for path in sorted(corpus.rglob("*.md")):
        if not path.is_file() or path.is_symlink():
            continue
        if any(part.startswith(".") for part in path.relative_to(corpus).parts):
            continue
        digests[path.relative_to(corpus).as_posix()] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    return digests


def describe_change(before: dict[str, str], after: dict[str, str]) -> list[str]:
    changes: list[str] = []
    for relative in sorted(set(before) - set(after)):
        changes.append(f"removed: {relative}")
    for relative in sorted(set(after) - set(before)):
        changes.append(f"added: {relative}")
    for relative in sorted(set(before) & set(after)):
        if before[relative] != after[relative]:
            changes.append(f"modified: {relative}")
    return changes


def run_baseline(corpus: Path, output: Path) -> tuple[dict, float]:
    started = time.monotonic()
    result = subprocess.run(
        [sys.executable, str(GRAPH_SCRIPT), "--wiki", str(corpus), "--output", str(output)],
        check=False,
        capture_output=True,
        text=True,
    )
    elapsed = time.monotonic() - started
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or "baseline failed")
    return json.loads(output.read_text(encoding="utf-8")), elapsed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument(
        "--candidate",
        help="exact read-only command to compare against the baseline",
    )
    parser.add_argument("--label", default="candidate")
    args = parser.parse_args()

    corpus = args.corpus
    if not corpus.is_dir():
        print(f"pilot: corpus directory not found: {corpus}", file=sys.stderr)
        return 2

    if args.candidate:
        try:
            words = shlex.split(args.candidate)
        except ValueError as exc:
            print(f"pilot: candidate command could not be parsed: {exc}", file=sys.stderr)
            return 2
        if not words:
            print("pilot: candidate command is empty", file=sys.stderr)
            return 2
        for word in words:
            hit = sorted(segments(word.lower()) & FORBIDDEN)
            if hit:
                print(
                    f"pilot: candidate command contains {hit[0]!r} in {word!r}; the "
                    "pilot is read-only and will not run a command that can change "
                    "the corpus",
                    file=sys.stderr,
                )
                return 2

    before = snapshot(corpus)
    if not before:
        print(f"pilot: no Markdown files under {corpus}", file=sys.stderr)
        return 2

    output = corpus.parent / ".pilot-graph.json"
    try:
        graph, baseline_seconds = run_baseline(corpus, output)
    except (OSError, ValueError) as exc:
        print(f"pilot: {exc}", file=sys.stderr)
        return 1
    finally:
        output.unlink(missing_ok=True)

    candidate_seconds = None
    candidate_status = "not run"
    candidate_output = ""
    if args.candidate:
        started = time.monotonic()
        result = subprocess.run(
            words, check=False, capture_output=True, text=True, cwd=str(corpus.parent)
        )
        candidate_seconds = time.monotonic() - started
        candidate_status = "exit 0" if result.returncode == 0 else f"exit {result.returncode}"
        candidate_output = (result.stdout or result.stderr).strip()

    after = snapshot(corpus)
    changes = describe_change(before, after)

    print(f"# Pilot report — {corpus}")
    print(f"\nFiles measured: {len(before)}")
    print("\n## Baseline (deterministic graph)\n")
    print(f"- articles: {graph['counts']['article']}")
    print(f"- topics: {graph['counts']['topic']}")
    print(f"- sources: {graph['counts']['source']}")
    print(f"- edges: {graph['counts']['edge']}")
    print(f"- links pointing at nothing: {len(graph['missing_targets'])}")
    print(f"- notes with no link either way: {len(graph['orphans'])}")
    print(f"- runtime: {baseline_seconds:.2f}s")
    print("- needs: python3 only, no server, no index to keep in sync")

    print(f"\n## {args.label}\n")
    if args.candidate:
        print(f"- command: `{args.candidate}`")
        print(f"- result: {candidate_status}")
        print(f"- runtime: {candidate_seconds:.2f}s")
        if candidate_output:
            first = candidate_output.splitlines()
            print(f"- output: {len(first)} line(s), first: {first[0][:120]}")
    else:
        print("- not run: no candidate command was given")

    print("\n## Corpus integrity\n")
    if changes:
        for change in changes:
            print(f"- {change}")
        print(
            "\n**The corpus changed during the pilot.** Whatever was measured, the "
            "candidate is disqualified until it can run without touching the notes."
        )
        return 1
    print(f"- unchanged: all {len(before)} file(s) match their pre-run hashes")

    print(
        "\nRuntime and counts are not the decision. Judge retrieval on questions "
        "written before the run, and weigh what each option costs to keep alive: "
        "the baseline has no state to rebuild, and an index does."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
