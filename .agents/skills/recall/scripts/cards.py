#!/usr/bin/env python3
"""Check that review cards can still be traced back to what they came from.

A flashcard is the most compressed form knowledge takes here, and compression
is where a claim quietly loses its evidence. A card that cannot be traced to
the note it came from is memorised without anyone able to re-examine it, which
is the opposite of what this harness is for.

So every card carries a provenance comment naming a note and an anchor inside
it, and this resolves both. The anchor rule is the one the knowledge graph
already uses for inferred records, loaded from there rather than restated, so
the two cannot drift apart.

Card format (Obsidian spaced-repetition compatible):

    Question text
    ?
    Answer text
    <!-- from: note-file.md#Heading -->

Usage: cards.py --wiki PATH FILE [FILE ...]
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import re
import sys


GRAPH_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "knowledge-graph" / "scripts" / "build_graph.py"
)
PROVENANCE = re.compile(r"<!--\s*from:\s*([^#>]+?)(?:#(.+?))?\s*-->")
SCHEDULING = re.compile(r"<!--\s*SR:.*?-->")
SEPARATOR = re.compile(r"^\?{1,2}$")


def load_graph_module():
    specification = importlib.util.spec_from_file_location("build_graph", GRAPH_SCRIPT)
    if specification is None or specification.loader is None:
        raise ValueError(f"could not load the anchor rule from {GRAPH_SCRIPT}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def split_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[index + 1 :])
    return text


def parse_cards(text: str) -> list[dict]:
    """Split a card file into cards on the ? separator."""
    cards: list[dict] = []
    question: list[str] = []
    answer: list[str] = []
    target: list[str] | None = question
    start = 0

    def flush() -> None:
        if not question and not answer:
            return
        cards.append(
            {
                "line": start,
                "question": "\n".join(question).strip(),
                "answer": "\n".join(answer).strip(),
            }
        )

    for number, raw in enumerate(split_frontmatter(text).splitlines(), start=1):
        line = raw.rstrip()
        if not line.strip():
            if target is answer and (question or answer):
                flush()
                question, answer = [], []
                target = question
            continue
        if SEPARATOR.match(line.strip()):
            target = answer
            continue
        if target is question and not question:
            start = number
        if line.lstrip().startswith("#") and target is question and not question:
            continue
        target.append(line)
    flush()
    return [card for card in cards if card["question"] or card["answer"]]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wiki", type=Path, required=True)
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()

    if not args.wiki.is_dir():
        print(f"recall: wiki directory not found: {args.wiki}", file=sys.stderr)
        return 2
    try:
        graph = load_graph_module()
    except (OSError, ValueError) as exc:
        print(f"recall: {exc}", file=sys.stderr)
        return 2

    problems: list[str] = []
    total = 0
    bodies: dict[Path, str] = {}

    for path in args.files:
        if not path.is_file():
            problems.append(f"{path}: not a file")
            continue
        cards = parse_cards(path.read_text(encoding="utf-8"))
        if not cards:
            problems.append(f"{path}: contains no cards")
            continue
        for card in cards:
            total += 1
            where = f"{path}:{card['line']}"
            answer = SCHEDULING.sub("", card["answer"])
            provenance = PROVENANCE.search(answer)
            answer_text = PROVENANCE.sub("", answer).strip()

            if not card["question"]:
                problems.append(f"{where}: card has no question")
            if not answer_text:
                problems.append(f"{where}: card has no answer")
            if provenance is None:
                # Without this the card is a claim nobody can re-examine.
                problems.append(
                    f"{where}: card has no provenance comment "
                    "(<!-- from: note.md#Anchor -->)"
                )
                continue

            note_name = (provenance.group(1) or "").strip()
            anchor = (provenance.group(2) or "").strip()
            note_path = args.wiki / note_name
            if not note_path.is_file():
                problems.append(f"{where}: provenance names a note that is not in the wiki: {note_name}")
                continue
            if not anchor:
                problems.append(f"{where}: provenance has no anchor after '#'")
                continue
            if note_path not in bodies:
                _, body = graph.split_frontmatter(
                    note_path.read_text(encoding="utf-8")
                )
                bodies[note_path] = body
            if graph.anchor_excerpt(bodies[note_path], anchor) is None:
                problems.append(
                    f"{where}: anchor does not resolve in {note_name}: {anchor!r}"
                )

    if problems:
        for problem in problems:
            print(f"recall: {problem}", file=sys.stderr)
        return 1
    print(f"recall: {total} card(s) traceable to their notes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
