#!/usr/bin/env python3
"""Pre-check diagrams in study notes and say when one has outgrown Mermaid.

Mermaid renders inside Obsidian, so a note can carry a diagram with no
toolchain at all. That only holds while the diagram stays small: past a
certain size Mermaid's layout stops being readable and the diagram belongs in
D2, rendered to SVG and embedded. Deciding that by feel produces tangled
diagrams nobody redraws, so the threshold is counted here instead.

This is a pre-check, not a renderer. Mermaid's own parser is JavaScript and
this repository keeps its scripts dependency-free, so what is checked is the
set of mistakes that are decidable from the text: an unknown diagram type,
unbalanced delimiters, and embedded assets that do not exist. A file that
passes may still fail to render.

Usage: check.py [--max-nodes N] PATH [PATH ...]
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


FENCE_OPEN = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_-]*)\s*$")
EMBED = re.compile(r"!\[\[([^\[\]\n|]+)(?:\|[^\[\]\n]*)?\]\]")
IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")

# Types bundled with Obsidian's Mermaid. An unknown type renders as an error
# block in the note, which is easy to miss when writing many diagrams.
DIAGRAM_TYPES = {
    "architecture-beta", "block-beta", "c4component", "c4container",
    "c4context", "c4deployment", "c4dynamic", "classdiagram", "erdiagram",
    "flowchart", "flowchart-elk", "gantt", "gitgraph", "graph", "journey",
    "kanban", "mindmap", "packet-beta", "pie", "quadrantchart",
    "requirementdiagram", "sankey-beta", "sequencediagram", "statediagram",
    "statediagram-v2", "timeline", "xychart-beta", "zenuml",
}
NODE_SHAPED = {"flowchart", "flowchart-elk", "graph"}
# Words that appear where a node id would and are not nodes.
NOT_NODES = {
    "subgraph", "end", "direction", "style", "classdef", "class", "click",
    "linkstyle", "tb", "td", "bt", "rl", "lr", "href", "call", "callback",
}

DEFAULT_MAX_NODES = 15


def fences(lines: list[str]) -> list[tuple[int, str, list[str]]]:
    """Return (start line, info string, body lines) for every fenced block."""
    blocks: list[tuple[int, str, list[str]]] = []
    marker: str | None = None
    info = ""
    start = 0
    body: list[str] = []
    for number, line in enumerate(lines, start=1):
        match = FENCE_OPEN.match(line)
        if marker is None:
            if match:
                marker = match.group(1)
                info = match.group(2).lower()
                start = number
                body = []
            continue
        if match and match.group(1)[0] == marker[0] and len(match.group(1)) >= len(marker):
            blocks.append((start, info, body))
            marker = None
            continue
        body.append(line)
    if marker is not None:
        blocks.append((start, info, body))
    return blocks


def strip_labels(text: str) -> str:
    """Remove quoted strings and bracketed label text.

    What remains is node ids, arrows, and keywords, so counting identifiers
    afterwards does not also count every word inside a label.
    """
    text = re.sub(r'"[^"\n]*"', " ", text)
    text = re.sub(r"'[^'\n]*'", " ", text)
    for opening, closing in (("[", "]"), ("(", ")"), ("{", "}")):
        pattern = re.compile(re.escape(opening) + r"[^" + re.escape(opening + closing) + r"\n]*" + re.escape(closing))
        while True:
            replaced = pattern.sub(" ", text)
            if replaced == text:
                break
            text = replaced
    return text


def count_nodes(body: list[str]) -> int:
    found: set[str] = set()
    for line in body:
        stripped = line.strip()
        if not stripped or stripped.startswith("%%"):
            continue
        first = stripped.split()[0].lower().rstrip(":")
        if first in {"style", "classdef", "click", "linkstyle", "class"}:
            continue
        for token in IDENTIFIER.findall(strip_labels(stripped)):
            if token.lower() not in NOT_NODES:
                found.add(token)
    return len(found)


def unbalanced(body: list[str]) -> list[str]:
    text = "\n".join(body)
    text = re.sub(r'"[^"\n]*"', " ", text)
    text = re.sub(r"'[^'\n]*'", " ", text)
    problems: list[str] = []
    for opening, closing, label in (
        ("[", "]", "square bracket"),
        ("(", ")", "parenthesis"),
        ("{", "}", "brace"),
    ):
        if text.count(opening) != text.count(closing):
            problems.append(
                f"unbalanced {label}: {text.count(opening)} {opening!r} "
                f"and {text.count(closing)} {closing!r}"
            )
    if text.count('"') % 2:
        problems.append("odd number of double quotes")
    return problems


def check_markdown(
    path: Path, max_nodes: int, problems: list[str], advice: list[str]
) -> int:
    lines = path.read_text(encoding="utf-8").splitlines()
    diagrams = 0

    for start, info, body in fences(lines):
        if info != "mermaid":
            continue
        diagrams += 1
        declaration = ""
        for line in body:
            if line.strip() and not line.strip().startswith("%%"):
                declaration = line.strip()
                break
        if not declaration:
            problems.append(f"{path}:{start}: mermaid block is empty")
            continue
        kind = declaration.split()[0].lower().rstrip(";")
        if kind not in DIAGRAM_TYPES:
            problems.append(
                f"{path}:{start}: unknown mermaid diagram type {kind!r}"
            )
            continue
        for problem in unbalanced(body):
            problems.append(f"{path}:{start}: {problem}")
        if kind in NODE_SHAPED:
            nodes = count_nodes(body[1:] if body and body[0].strip() else body)
            if nodes > max_nodes:
                advice.append(
                    f"{path}:{start}: about {nodes} nodes, over the {max_nodes} "
                    "Mermaid stays readable at - render this one with D2 and "
                    "embed the SVG"
                )

    # An embedded image that does not exist renders as a broken link, which is
    # invisible until someone opens the note.
    for number, line in enumerate(lines, start=1):
        for target in EMBED.findall(line):
            target = target.strip()
            if not target.lower().endswith((".svg", ".png", ".jpg", ".jpeg", ".webp")):
                continue
            if (path.parent / target).exists():
                continue
            if any((path.parent / "assets" / Path(target).name).exists() for _ in [0]):
                continue
            problems.append(f"{path}:{number}: embedded asset not found: {target}")

    return diagrams


def check_svg(path: Path, problems: list[str]) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    if "<svg" not in text:
        problems.append(f"{path}: does not contain an <svg> element")
        return
    # A renderer that failed often still writes a file, and an empty canvas is
    # easy to embed without noticing.
    if not re.search(r"<(path|rect|circle|ellipse|line|polyline|polygon|text|g)\b", text):
        problems.append(f"{path}: contains no drawable elements")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-nodes", type=int, default=DEFAULT_MAX_NODES)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    problems: list[str] = []
    advice: list[str] = []
    diagrams = 0
    for path in args.paths:
        if not path.is_file():
            problems.append(f"{path}: not a file")
            continue
        suffix = path.suffix.lower()
        if suffix in {".md", ".markdown"}:
            diagrams += check_markdown(path, args.max_nodes, problems, advice)
        elif suffix == ".svg":
            check_svg(path, problems)
        else:
            problems.append(f"{path}: unsupported file type {suffix or '(none)'}")

    for line in advice:
        print(f"diagram: {line}", file=sys.stderr)
    if problems:
        for problem in sorted(problems):
            print(f"diagram: {problem}", file=sys.stderr)
        return 1
    print(f"diagram: {diagrams} mermaid block(s) checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
