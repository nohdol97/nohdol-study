#!/usr/bin/env python3
"""Build a deterministic wikilink graph from curated Markdown notes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any
import unicodedata


WIKILINK = re.compile(r"\[\[([^\[\]\n]+)\]\]")
H1 = re.compile(r"^#\s+(.+?)\s*$")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"(`+)[^\n]*?\1")


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


def content_without_fences(body: str, strip_inline_code: bool = True) -> str:
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
            kept.append(INLINE_CODE.sub("", line) if strip_inline_code else line)
    return "\n".join(kept)


def normalized_target(raw: str) -> str:
    target = raw.split("|", 1)[0].strip()
    target = target.split("#", 1)[0].split("^", 1)[0].strip()
    if target.lower().endswith(".md"):
        target = target[:-3]
    return target


def note_title(body: str, path: Path) -> str:
    # Inline code is dropped for link scanning only. A title like
    # "# Using `rg` for search" must keep its backticked words, or two notes
    # differing only inside code spans collapse into one name and the whole
    # graph fails as a duplicate title.
    for line in content_without_fences(body, strip_inline_code=False).splitlines():
        match = H1.match(line)
        if match:
            return match.group(1).strip()
    return path.stem


def identity(value: str) -> str:
    # macOS returns filenames in NFD, while note bodies are usually typed in
    # NFC. Without normalization a Korean [[링크]] silently fails to resolve
    # against a file of the same visible name.
    return unicodedata.normalize("NFC", value).strip().casefold()


def build(wiki: Path) -> dict[str, Any]:
    files = sorted(path for path in wiki.rglob("*.md") if path.is_file())
    notes: list[dict[str, Any]] = []
    title_map: dict[str, dict[str, Any]] = {}
    stem_owners: dict[str, list[dict[str, Any]]] = {}

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
        stem_owners.setdefault(identity(path.stem), []).append(note)
        notes.append(note)

    # Obsidian resolves [[target]] by filename while this graph names notes by
    # their H1. Both keys must resolve, or a note whose filename differs from
    # its heading is reported broken here and fine in Obsidian. A filename
    # shared by several notes stays unresolved rather than picking one.
    stem_map = {
        stem: owners[0] for stem, owners in stem_owners.items() if len(owners) == 1
    }

    backlinks: dict[str, set[str]] = {key: set() for key in title_map}
    missing: dict[str, dict[str, Any]] = {}
    nodes: list[dict[str, Any]] = []

    for note in notes:
        raw_links = WIKILINK.findall(content_without_fences(note.pop("_body")))
        # Link variants that differ only by case or Unicode form are one edge.
        seen_targets: dict[str, str] = {}
        for raw in raw_links:
            target = normalized_target(raw)
            if target:
                seen_targets.setdefault(identity(Path(target).name), target)
        targets = sorted(
            seen_targets.values(), key=lambda item: (item.casefold(), item)
        )
        # Filename and title spellings of the same note are one edge.
        resolved: dict[str, str] = {}
        unresolved: list[str] = []
        for target in targets:
            target_key = identity(Path(target).name)
            target_note = title_map.get(target_key) or stem_map.get(target_key)
            if target_note is None:
                unresolved.append(target)
                entry = missing.setdefault(
                    target_key, {"target": target, "referenced_by": set()}
                )
                entry["referenced_by"].add(note["title"])
            else:
                target_title = target_note["title"]
                resolved.setdefault(identity(target_title), target_title)
                backlinks[identity(target_title)].add(note["title"])
        nodes.append(
            {
                "title": note["title"],
                "path": note["path"],
                "frontmatter": note["frontmatter"],
                "links": sorted(
                    resolved.values(), key=lambda item: (item.casefold(), item)
                ),
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
            "target": entry["target"],
            "referenced_by": sorted(
                entry["referenced_by"], key=lambda item: (item.casefold(), item)
            ),
        }
        for entry in sorted(
            missing.values(),
            key=lambda item: (item["target"].casefold(), item["target"]),
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
