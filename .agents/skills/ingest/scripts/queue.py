#!/usr/bin/env python3
"""Report which captured sources have a note and which are still waiting.

Why progress is derived rather than recorded.

A batch of sources is bigger than one context. Two sessions in this vault's
history ran a whole course archive from a single instruction — 3 and 4 user
turns, ~300k and ~470k output tokens, peak contexts over 700k — and both ended
with the user cleaning up afterwards ("깨져있는 링크 제거해"). What made the
tail of those sessions unreliable is that the work-list lived only in the
conversation: by note forty, the model no longer had the file list in view and
started writing source paths from memory. Six citations landed with the wrong
separator, naming files that do not exist while reading like evidence.

A checklist file would inherit the same weakness, because ticking it is
another thing to remember. So nothing is recorded here. Coverage is computed
by reading what the notes actually cite: a source counts as done when some
note names its exact path in `sources:`. That makes the answer correct after
an interrupted session, a crash, or a sync, and it cannot drift from reality,
because the thing being measured is the thing that matters.

It also gives the batch a path to copy instead of recall. Everything printed
under "waiting" is a real relative path, verified to exist.

Usage: queue.py --vault PATH --raw SUBPATH [--ext .md,.py] [--limit N]
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys
import unicodedata


def key(reference: str) -> str:
    """Normalize a path for comparison.

    macOS hands back decomposed Unicode from the filesystem while a note is
    written composed, so `효율화` in a filename and `효율화` in `sources:` are
    equal on disk and unequal as strings. Comparing them raw reported all 45
    captured course files as uncited when six of them were cited by name. The
    OS hides this from `Path.exists()`, which is why it survives elsewhere and
    only surfaces where paths are compared as text.
    """
    return unicodedata.normalize("NFC", reference)


GRAPH_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "knowledge-graph" / "scripts" / "build_graph.py"
)


def load_graph_module():
    spec = importlib.util.spec_from_file_location("study_build_graph", GRAPH_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cited_paths(wiki: Path, graph_module) -> set[str]:
    """Every non-URL `sources:` entry across the curated layer.

    The frontmatter parser is borrowed rather than rewritten. A second reader
    of the same YAML disagrees with the first one eventually, and then this
    reports a source as waiting while the gardening report calls it cited.
    """
    cited: set[str] = set()
    for note in wiki.rglob("*.md"):
        try:
            text = note.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        frontmatter, _ = graph_module.split_frontmatter(text)
        declared = frontmatter.get("sources")
        if not isinstance(declared, list):
            continue
        for entry in declared:
            reference = str(entry).strip()
            if reference and "://" not in reference:
                cited.add(key(reference))
    return cited


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, required=True)
    parser.add_argument(
        "--raw",
        required=True,
        help="path of the capture directory, relative to the knowledge root",
    )
    parser.add_argument(
        "--ext",
        default="",
        help="comma-separated extensions to count; default is every file",
    )
    parser.add_argument("--limit", type=int, default=20, help="how many waiting items to print")
    args = parser.parse_args()

    vault = args.vault
    wiki = vault / "wiki"
    capture = vault / args.raw
    if not wiki.is_dir():
        print(f"ingest-queue: wiki directory not found: {wiki}", file=sys.stderr)
        return 2
    if not capture.is_dir():
        print(f"ingest-queue: capture directory not found: {capture}", file=sys.stderr)
        return 2

    wanted = {value.strip().lower() for value in args.ext.split(",") if value.strip()}
    sources = sorted(
        path for path in capture.rglob("*")
        if path.is_file()
        and not path.name.startswith(".")
        and (not wanted or path.suffix.lower() in wanted)
    )
    if not sources:
        print(f"ingest-queue: no files under {args.raw}")
        return 0

    cited = cited_paths(wiki, load_graph_module())
    waiting = [
        key(path.relative_to(vault).as_posix())
        for path in sources
        if key(path.relative_to(vault).as_posix()) not in cited
    ]
    done = len(sources) - len(waiting)

    print(f"ingest-queue: {done}/{len(sources)} captured source(s) cited by a note")
    if not waiting:
        print("\nNothing waiting.")
        return 0

    print(f"\n## waiting ({len(waiting)})")
    for reference in waiting[: args.limit]:
        print(f"- {reference}")
    if len(waiting) > args.limit:
        print(f"- ... {len(waiting) - args.limit} more")

    print(
        "\nCopy these paths into `sources:` rather than retyping them. Work them "
        "one at a time and in one session: linking two notes correctly needs both "
        "of their current states in the same context. Re-run this to see progress; "
        "nothing here is stored, so an interrupted session resumes from the notes "
        "themselves."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
