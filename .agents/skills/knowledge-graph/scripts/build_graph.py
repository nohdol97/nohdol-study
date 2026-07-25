#!/usr/bin/env python3
"""Build a deterministic wikilink graph from curated Markdown notes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


WIKILINK = re.compile(r"\[\[([^\[\]\n]+)\]\]")
H1 = re.compile(r"^#\s+(.+?)\s*$")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value == "[]":
        return []
    if value in {"true", "false"}:
        return value == "true"
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    closing = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if closing is None:
        return {}, text

    result: dict[str, Any] = {}
    active_list: str | None = None
    for line in lines[1:closing]:
        if active_list and re.match(r"^\s+-\s+", line):
            result[active_list].append(parse_scalar(re.sub(r"^\s+-\s+", "", line)))
            continue
        active_list = None
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if not key:
            continue
        parsed = parse_scalar(value)
        result[key] = parsed
        if parsed == "" and value.strip() == "":
            result[key] = []
            active_list = key
    return result, "\n".join(lines[closing + 1 :])


def content_without_fences(body: str) -> str:
    kept: list[str] = []
    fence_marker: str | None = None
    for line in body.splitlines():
        match = FENCE.match(line)
        if match:
            marker = match.group(1)
            marker_char = marker[0]
            if fence_marker is None:
                fence_marker = marker
            elif marker_char == fence_marker[0] and len(marker) >= len(fence_marker):
                fence_marker = None
            continue
        if fence_marker is None:
            kept.append(line)
    return "\n".join(kept)


def normalized_target(raw: str) -> str:
    target = raw.split("|", 1)[0].strip()
    target = target.split("#", 1)[0].split("^", 1)[0].strip()
    if target.lower().endswith(".md"):
        target = target[:-3]
    return target


def note_title(body: str, path: Path) -> str:
    for line in content_without_fences(body).splitlines():
        match = H1.match(line)
        if match:
            return match.group(1).strip()
    return path.stem


def identity(value: str) -> str:
    return value.strip().casefold()


def build(wiki: Path) -> dict[str, Any]:
    files = sorted(path for path in wiki.rglob("*.md") if path.is_file())
    notes: list[dict[str, Any]] = []
    title_map: dict[str, dict[str, Any]] = {}

    for path in files:
        text = path.read_text(encoding="utf-8")
        frontmatter, body = split_frontmatter(text)
        title = note_title(body, path)
        key = identity(title)
        if key in title_map:
            previous = title_map[key]["path"]
            raise ValueError(
                f"duplicate note title {title!r}: {previous} and "
                f"{path.relative_to(wiki).as_posix()}"
            )
        note = {
            "title": title,
            "path": path.relative_to(wiki).as_posix(),
            "frontmatter": frontmatter,
            "_body": body,
        }
        title_map[key] = note
        notes.append(note)

    backlinks: dict[str, set[str]] = {key: set() for key in title_map}
    missing: dict[str, set[str]] = {}
    nodes: list[dict[str, Any]] = []

    for note in notes:
        source_key = identity(note["title"])
        raw_links = WIKILINK.findall(content_without_fences(note.pop("_body")))
        targets = sorted(
            {normalized_target(raw) for raw in raw_links if normalized_target(raw)},
            key=lambda item: (item.casefold(), item),
        )
        resolved: list[str] = []
        unresolved: list[str] = []
        for target in targets:
            target_key = identity(Path(target).name)
            target_note = title_map.get(target_key)
            if target_note is None:
                unresolved.append(target)
                missing.setdefault(target, set()).add(note["title"])
            else:
                resolved.append(target_note["title"])
                backlinks[target_key].add(note["title"])
        nodes.append(
            {
                "title": note["title"],
                "path": note["path"],
                "frontmatter": note["frontmatter"],
                "links": sorted(resolved, key=lambda item: (item.casefold(), item)),
                "missing_links": unresolved,
            }
        )

    for node in nodes:
        node["backlinks"] = sorted(
            backlinks[identity(node["title"])],
            key=lambda item: (item.casefold(), item),
        )

    nodes.sort(key=lambda item: (identity(item["title"]), item["path"]))
    orphans = sorted(
        [
            node["title"]
            for node in nodes
            if not node["links"] and not node["backlinks"]
        ],
        key=lambda item: (item.casefold(), item),
    )
    missing_targets = [
        {
            "target": target,
            "referenced_by": sorted(
                sources, key=lambda item: (item.casefold(), item)
            ),
        }
        for target, sources in sorted(
            missing.items(), key=lambda item: (item[0].casefold(), item[0])
        )
    ]

    return {
        "schema_version": 1,
        "source": "wiki Markdown",
        "node_count": len(nodes),
        "nodes": nodes,
        "missing_targets": missing_targets,
        "orphans": orphans,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wiki", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not args.wiki.is_dir():
        print(f"knowledge-graph: wiki directory not found: {args.wiki}", file=sys.stderr)
        return 2

    try:
        graph = build(args.wiki)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"knowledge-graph: {exc}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(graph, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temporary = args.output.with_name(f".{args.output.name}.tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
