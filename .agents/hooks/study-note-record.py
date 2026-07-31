#!/usr/bin/env python3
"""Ask whether the notes written this session were actually recorded.

Three questions, one per line on stdout, most important first. Empty output
means nothing to say. Exit 1 means the check could not run, which is a problem
with this script and never a reason to block finishing.

Question one is whether the note was recorded, answered by looking for its
title in index.md or log.md. That is unchanged.

Question two is whether anything points at the note, and it is why this file
exists. The Stop hook used to treat question one as the answer to both. But a
title appears in index.md for either of two very different reasons: because a
topic hub files it, which is durable, or because it sits in "recent updates",
a list that keeps five entries and drops the rest. A note passed at the moment
it was written and went unreachable once five newer notes pushed it out. That
is how the A100 guide shipped with nothing pointing at it (session `f2a3fae4`
@395: "왜 진입점이 없어"). `vault-gardening` was corrected to judge by inbound
links on 2026-07-26; this hook was not, so the two disagreed for five days.
The definition now lives once, in `garden.unreachable_notes`, and both callers
ask it.

Question three is whether the links written this session resolve. Reachability
asks what points at a note; this asks whether what the note points at exists.
A wikilink lives between files, so no per-file check can see it break — the
note that names a target stays valid Markdown whether or not the target was
ever written. It reuses `missing_targets` from the same graph for the same
reason question two moved: a second definition of "broken link" would drift
from the one `vault-gardening` reports.

Scope is only the notes newer than the records. Reporting every unreachable
note in the vault would mean an old gap blocks every turn until someone fixes
it, which trains the reminder away — the exact failure this hook already had
to recover from once. Existing debt belongs to `vault-gardening`.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys


SKILLS = Path(__file__).resolve().parent.parent / "skills"
GARDEN_SCRIPT = SKILLS / "vault-gardening" / "scripts" / "garden.py"
GRAPH_SCRIPT = SKILLS / "knowledge-graph" / "scripts" / "build_graph.py"

GENERATED_TYPES = {"index", "moc"}
GENERATED_TAGS = {"feed", "daily-scrap"}


def load(script: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def candidates(wiki: Path, cutoff: float, graph_module) -> list[Path]:
    """Notes modified after the records, excluding generated listings.

    Timestamps bound the search rather than decide anything: a note older than
    both records was either handled long ago or is a known gap the gardening
    report covers, and walking the whole curated layer on cloud storage every
    turn is slow enough to matter. A sync client can rewrite modification
    times, so this is a hint about where to look, never proof of freshness.
    """
    found = []
    for path in sorted(wiki.rglob("*.md")):
        try:
            if path.stat().st_mtime <= cutoff:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        frontmatter, _ = graph_module.split_frontmatter(text)
        if str(frontmatter.get("type") or "") in GENERATED_TYPES:
            continue
        tags = frontmatter.get("tags")
        if isinstance(tags, list) and {str(tag) for tag in tags} & GENERATED_TAGS:
            continue
        found.append(path)
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, required=True)
    args = parser.parse_args()

    vault = args.vault
    wiki = vault / "wiki"
    index_path = vault / "index.md"
    log_path = vault / "log.md"
    if not wiki.is_dir() or not index_path.is_file() or not log_path.is_file():
        return 0

    graph_module = load(GRAPH_SCRIPT, "study_build_graph")
    cutoff = min(index_path.stat().st_mtime, log_path.stat().st_mtime)
    fresh = candidates(wiki, cutoff, graph_module)
    if not fresh:
        return 0

    recorded = index_path.read_text(encoding="utf-8", errors="replace")
    recorded += log_path.read_text(encoding="utf-8", errors="replace")
    findings: list[str] = []

    # Being named in either record still counts, exactly as before. Saving a
    # note seconds after updating the index is ordinary, and a sync client can
    # rewrite modification times outright, so tightening this to log.md alone
    # would buy correctness the rules already state at the cost of false alarms
    # that have twice trained this reminder away.
    #
    # What changed is that this answer is no longer reused for reachability.
    # Conflating the two is the actual defect: a title under the index's capped
    # "recent updates" list satisfied both questions, and only one of them
    # honestly.
    unrecorded = [path.stem for path in fresh if path.stem not in recorded]
    if unrecorded:
        findings.append(
            f'Curated note "{unrecorded[0]}" is not recorded in index.md or log.md. '
            "Update the index, append the log, and refresh the compact hot cache "
            "before finishing."
        )

    # The graph is built only when something was written, which keeps an
    # ordinary turn free of it. It costs about a second over ~286 notes.
    try:
        garden = load(GARDEN_SCRIPT, "study_garden")
        graph = garden.build_graph(wiki)
    except (OSError, ValueError) as exc:
        print(f"study-note-record: graph build failed: {exc}", file=sys.stderr)
        return 1

    written = {path.stem for path in fresh}
    stranded = [title for title in garden.unreachable_notes(graph) if title in written]
    if stranded:
        findings.append(
            f'Nothing points at "{stranded[0]}". A note is reachable when something '
            "links it or the index files it under a topic hub; its own outgoing "
            "links do not count. Link it from the hub note for its topic."
        )

    # Question three: does a link written this session resolve to anything?
    #
    # Git-style thinking does not reach this. A wikilink is a reference between
    # files, so renaming or not-yet-writing its target leaves every individual
    # file well-formed and the navigation broken. Nothing else in the loop
    # notices: the note saves, the record check passes, and the gap surfaces
    # whenever someone next follows the link.
    #
    # Scope matches the two checks above and for the same reason — only links
    # written this session. Existing broken links belong to `vault-gardening`;
    # blocking on them would make every turn end with someone else's debt.
    #
    # `missing_targets` already excludes a name that resolves under raw/, so a
    # note citing a preserved capture is not reported here.
    broken = [
        (source, item["target"])
        for item in graph["missing_targets"]
        for source in item["referenced_by"]
        if source in written
    ]
    if broken:
        source, target = broken[0]
        findings.append(
            f'"{source}" links [[{target}]], which is not a note in the vault. '
            "Write that note, or correct the link, before finishing. A link "
            "pointing at nothing fails silently: the file is valid and only the "
            "navigation is broken."
        )

    for finding in findings:
        print(finding)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
