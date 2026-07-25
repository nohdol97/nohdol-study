#!/usr/bin/env python3
"""Check Obsidian file formats without opening Obsidian.

Canvas and Markdown are checked against rules that hold on their own, so a
file can be produced and verified on a machine with no Obsidian installed.
Bases files are YAML, and this repository keeps its scripts dependency-free,
so the base check is a deliberate structural pre-check rather than a YAML
validator: it catches the mistakes that make a file fail to load and says
nothing about the rest. Obsidian remains the authority.

Usage: validate.py PATH [PATH ...]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
WIKILINK = re.compile(r"!?\[\[([^\[\]\n]*)\]\]")
OPEN_LINK = re.compile(r"!?\[\[")
CALLOUT = re.compile(r"^\s*>\s*\[!([^\]\n]*)\]([+-]?)(.*)$")
BASE_TOP_LEVEL = {"filters", "formulas", "properties", "views", "summaries"}
CANVAS_NODE_TYPES = {"text", "file", "link", "group"}
CANVAS_SIDES = {"top", "right", "bottom", "left"}
CANVAS_REQUIRED_BY_TYPE = {"text": "text", "file": "file", "link": "url"}

# Used when the pinned reference is unavailable. The pin is preferred so the
# list tracks upstream instead of drifting into a private copy.
FALLBACK_CALLOUTS = {
    "note", "abstract", "summary", "tldr", "info", "todo", "tip", "hint",
    "important", "success", "check", "done", "question", "help", "faq",
    "warning", "caution", "attention", "failure", "fail", "missing", "danger",
    "error", "bug", "example", "quote", "cite",
}


def known_callouts(study_root: Path) -> tuple[set[str], str]:
    reference = (
        study_root
        / ".tools/obsidian-skills/skills/obsidian-markdown/references/CALLOUTS.md"
    )
    if not reference.is_file():
        return FALLBACK_CALLOUTS, "built-in list"
    found: set[str] = set()
    for line in reference.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        for cell in cells[:2]:
            for name in re.findall(r"`([a-z][a-z0-9-]*)`", cell):
                found.add(name)
    if not found:
        return FALLBACK_CALLOUTS, "built-in list"
    return found, "pinned reference"


def strip_fences(lines: list[str]) -> list[tuple[int, str]]:
    kept: list[tuple[int, str]] = []
    marker: str | None = None
    for number, line in enumerate(lines, start=1):
        match = FENCE.match(line)
        if match:
            found = match.group(1)
            if marker is None:
                marker = found
            elif found[0] == marker[0] and len(found) >= len(marker):
                marker = None
            continue
        if marker is None:
            kept.append((number, line))
    return kept


def check_canvas(path: Path, problems: list[str]) -> None:
    def report(message: str) -> None:
        problems.append(f"{path}: {message}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        report(f"not valid JSON: {exc}")
        return
    if not isinstance(data, dict):
        report("top level must be an object")
        return

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    if not isinstance(nodes, list) or not isinstance(edges, list):
        report("nodes and edges must be arrays")
        return

    node_ids: set[str] = set()
    for position, node in enumerate(nodes):
        where = f"node {position}"
        if not isinstance(node, dict):
            report(f"{where}: must be an object")
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id:
            report(f"{where}: id must be a non-empty string")
        elif node_id in node_ids:
            report(f"{where}: duplicate id {node_id!r}")
        else:
            node_ids.add(node_id)
        node_type = node.get("type")
        if node_type not in CANVAS_NODE_TYPES:
            report(f"{where}: type must be one of {sorted(CANVAS_NODE_TYPES)}")
        else:
            required = CANVAS_REQUIRED_BY_TYPE.get(node_type)
            if required and not node.get(required):
                report(f"{where}: type {node_type} requires {required!r}")
        for field in ("x", "y", "width", "height"):
            value = node.get(field)
            if not isinstance(value, int) or isinstance(value, bool):
                report(f"{where}: {field} must be an integer")

    edge_ids: set[str] = set()
    for position, edge in enumerate(edges):
        where = f"edge {position}"
        if not isinstance(edge, dict):
            report(f"{where}: must be an object")
            continue
        edge_id = edge.get("id")
        if not isinstance(edge_id, str) or not edge_id:
            report(f"{where}: id must be a non-empty string")
        elif edge_id in edge_ids:
            report(f"{where}: duplicate id {edge_id!r}")
        else:
            edge_ids.add(edge_id)
        for field in ("fromNode", "toNode"):
            target = edge.get(field)
            if not isinstance(target, str) or not target:
                report(f"{where}: {field} must be a non-empty string")
            elif target not in node_ids:
                report(f"{where}: {field} {target!r} is not a node in this canvas")
        for field in ("fromSide", "toSide"):
            side = edge.get(field)
            if side is not None and side not in CANVAS_SIDES:
                report(f"{where}: {field} must be one of {sorted(CANVAS_SIDES)}")


def check_base(path: Path, problems: list[str]) -> None:
    def report(number: int | None, message: str) -> None:
        location = f"{path}:{number}" if number else f"{path}"
        problems.append(f"{location}: {message}")

    lines = path.read_text(encoding="utf-8").splitlines()
    if not any(line.strip() for line in lines):
        report(None, "file is empty")
        return

    top_level: list[str] = []
    in_views = False
    # The indent of the first "- " under views fixes the level of a view
    # entry. Anything deeper is that entry's own content - an order list, for
    # instance - and must not be counted as another view.
    entry_indent: int | None = None
    view_entries: list[tuple[int, dict[str, bool]]] = []
    current: dict[str, bool] | None = None

    def absorb(fields: dict[str, bool], text: str) -> None:
        for field in ("type", "name"):
            if text.startswith(f"{field}:"):
                fields[field] = bool(text[len(field) + 1 :].strip())

    for number, line in enumerate(lines, start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line[: len(line) - len(line.lstrip())]:
            report(number, "indent with spaces; a tab makes YAML fail to load")
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if indent == 0 and stripped.endswith(":"):
            key = stripped[:-1].strip()
            top_level.append(key)
            if key not in BASE_TOP_LEVEL:
                report(number, f"unknown top-level key {key!r}")
            in_views = key == "views"
            entry_indent = None
            current = None
            continue
        if not in_views:
            continue
        if stripped.startswith("- "):
            if entry_indent is None:
                entry_indent = indent
            if indent == entry_indent:
                current = {"type": False, "name": False}
                view_entries.append((number, current))
                absorb(current, stripped[2:].strip())
            continue
        if current is not None and entry_indent is not None and indent == entry_indent + 2:
            absorb(current, stripped)

    if "views" not in top_level:
        report(None, "a base needs a 'views' section")
    for number, entry in view_entries:
        for field in ("type", "name"):
            if not entry[field]:
                report(number, f"view is missing {field!r}")


def check_markdown(path: Path, callouts: set[str], problems: list[str]) -> None:
    def report(number: int, message: str) -> None:
        problems.append(f"{path}:{number}: {message}")

    lines = path.read_text(encoding="utf-8").splitlines()
    for number, line in strip_fences(lines):
        # Inline code may legitimately show the syntax, so it is removed
        # before the link and callout checks.
        scannable = re.sub(r"(`+)[^\n]*?\1", "", line)
        if len(OPEN_LINK.findall(scannable)) != len(WIKILINK.findall(scannable)):
            report(number, "wikilink is not closed with ]]")
        for target in WIKILINK.findall(scannable):
            if not target.strip():
                report(number, "wikilink has an empty target")
            elif target.strip().startswith("#") and "|" not in target:
                # [[#Heading]] is a same-note link and is fine; flag only the
                # shape that names nothing at all.
                if not target.strip().lstrip("#").strip():
                    report(number, "wikilink names no heading")
        callout = CALLOUT.match(scannable)
        if callout:
            name = callout.group(1).strip().lower()
            if not name:
                report(number, "callout has no type")
            elif name not in callouts:
                report(number, f"unknown callout type {name!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    study_root = Path(__file__).resolve().parents[4]
    callouts, callout_source = known_callouts(study_root)

    problems: list[str] = []
    checked = 0
    for path in args.paths:
        if not path.is_file():
            problems.append(f"{path}: not a file")
            continue
        suffix = path.suffix.lower()
        if suffix == ".canvas":
            check_canvas(path, problems)
        elif suffix == ".base":
            check_base(path, problems)
        elif suffix in {".md", ".markdown"}:
            check_markdown(path, callouts, problems)
        else:
            problems.append(f"{path}: unsupported file type {suffix or '(none)'}")
            continue
        checked += 1

    if problems:
        for problem in sorted(problems):
            print(problem, file=sys.stderr)
        return 1
    print(f"obsidian: {checked} file(s) valid (callouts from the {callout_source})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
