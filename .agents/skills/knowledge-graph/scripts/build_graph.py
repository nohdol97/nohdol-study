#!/usr/bin/env python3
"""Build a deterministic typed graph from curated Markdown notes.

The deterministic layer holds only what the files state outright: articles,
the topics an index groups them under, the sources they cite, and the links
between them. Anything a model inferred enters through --semantic and must
carry evidence that resolves in the note it claims to come from.

No note body is copied into the output. Evidence is kept as an anchor plus a
hash of the matched excerpt, so the graph can be shared without carrying the
knowledge base inside it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any
import unicodedata


WIKILINK = re.compile(r"\[\[([^\[\]\n]+)\]\]")
H1 = re.compile(r"^#\s+(.+?)\s*$")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
# A code span does not end at the line ending. CommonMark closes it at the next
# backtick run of the same length and turns any line ending inside into a space,
# so `rg --files\n[[Note]]` is code, not a link. Reading one line at a time never
# sees the closing run, and the wikilink between them is reported as a link
# pointing at nothing while the note renders exactly as written. A blank line
# ends the block, so a span cannot reach past one.
INLINE_CODE = re.compile(r"(`+)(?:(?!\n[ \t]*\n).)*?\1", re.DOTALL)
LIST_ITEM = re.compile(r"^(\s*)[-*+]\s+(.*)$")
HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*$")

# An embedded image is an illustration inside a note, not a link to another
# note. Counting one as a wikilink makes every note that shows a figure report
# a broken link to a file that is sitting right there, which trains a reader to
# ignore the one section that matters most.
MEDIA_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".avif",
    ".pdf", ".mp4", ".webm", ".mov", ".mp3", ".wav", ".m4a", ".ogg",
}

VERIFICATION_STATES = {
    "unverified",
    "source-backed",
    "primary-confirmed",
    "cross-checked",
    "contested",
}
CONFIRMED_STATES = {"primary-confirmed", "cross-checked"}
SEMANTIC_KINDS = {"entity", "claim"}
EXCERPT_LENGTH = 200


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


def without_inline_code(text: str) -> str:
    # One newline is kept for every one the span consumed, so a caller that
    # reads the result a line at a time still sees the original line structure.
    return INLINE_CODE.sub(lambda match: "\n" * match.group(0).count("\n"), text)


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
            kept.append(line)
    # Spans are removed after the lines are rejoined, not per line: the closing
    # backtick run may sit on a later line than the opening one.
    text = "\n".join(kept)
    return without_inline_code(text) if strip_inline_code else text


def normalized_target(raw: str) -> str:
    # Inside a Markdown table the alias pipe must be escaped - `[[Note\|alias]]` -
    # because a bare `|` would end the cell. Obsidian still reads it as the alias
    # separator, so splitting on the bare pipe leaves a trailing backslash: the
    # edge is lost and the note is reported as a broken link while it renders
    # perfectly. Unescape first, then split.
    target = raw.replace("\\|", "|").split("|", 1)[0].strip()
    target = target.split("#", 1)[0].split("^", 1)[0].strip()
    # An asset embed carries no note body, so it is not an edge in a knowledge
    # graph and must not be reported as a link with no target.
    if Path(target).suffix.lower() in MEDIA_SUFFIXES:
        return ""
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


def sorted_by_text(values: Any) -> list[str]:
    return sorted(values, key=lambda item: (item.casefold(), item))


def index_topics(index_text: str) -> list[tuple[str, list[str]]]:
    """Read topic groupings out of the master index.

    A top-level bullet naming no note, whose nested bullets link to notes, is
    a category. A top-level bullet that links directly is a chronology entry,
    not a topic, so the recent-changes list does not become categories.
    """
    body = content_without_fences(index_text, strip_inline_code=False)
    groups: list[tuple[str, list[str]]] = []
    current: str | None = None
    current_indent = 0
    members: list[str] = []

    def flush() -> None:
        if current is not None and members:
            groups.append((current, list(members)))

    for line in body.splitlines():
        match = LIST_ITEM.match(line)
        if not match:
            if HEADING.match(line):
                flush()
                current = None
                members.clear()
            continue
        indent = len(match.group(1).expandtabs(4))
        content = match.group(2).strip()
        links = [normalized_target(raw) for raw in WIKILINK.findall(content)]
        links = [link for link in links if link]
        if current is not None and indent > current_indent and links:
            members.extend(links)
            continue
        flush()
        members.clear()
        if links:
            current = None
            continue
        label = content.split("—", 1)[0].split(" - ", 1)[0].strip()
        current = label or None
        current_indent = indent
    flush()
    return groups


def anchor_excerpt(body: str, anchor: str) -> str | None:
    """Return the text an evidence anchor points at, or None when it is absent.

    A heading anchor matches a heading line; anything else must appear
    literally. An anchor that resolves nowhere is the signal that a record was
    invented, so it is never approximated.
    """
    anchor = anchor.strip()
    if not anchor:
        return None
    if anchor.startswith("#"):
        wanted = identity(HEADING.sub(r"\1", anchor))
        lines = body.splitlines()
        for position, line in enumerate(lines):
            heading = HEADING.match(line)
            if heading and identity(heading.group(1)) == wanted:
                return "\n".join(lines[position:])[:EXCERPT_LENGTH]
        return None
    location = identity(body).find(identity(anchor))
    if location < 0:
        return None
    return body[location : location + EXCERPT_LENGTH]


def load_semantic(
    path: Path, articles_by_path: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Validate model-produced records against the notes they cite.

    Every record must name a note, an anchor that resolves inside it, the
    extractor, a confidence, and a verification state. A record missing any of
    those is dropped rather than filed as low quality, because an unfalsifiable
    claim is worse in a knowledge base than a missing one.
    """
    accepted: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"semantic input could not be read: {exc}") from exc
    records = payload.get("records") if isinstance(payload, dict) else None
    if not isinstance(records, list):
        raise ValueError("semantic input must hold a 'records' list")

    for position, record in enumerate(records):
        label = ""
        reason = None
        if not isinstance(record, dict):
            dropped.append({"record": str(position), "reason": "not an object"})
            continue
        label = str(record.get("label", "")).strip() or f"record {position}"
        kind = str(record.get("kind", "")).strip()
        source_path = str(record.get("source_path", "")).strip()
        anchor = str(record.get("evidence_anchor", "")).strip()
        extractor = str(record.get("extractor", "")).strip()
        verification = str(record.get("verification", "")).strip()
        confidence = record.get("confidence")

        if kind not in SEMANTIC_KINDS:
            reason = "kind must be entity or claim"
        elif not label.strip():
            reason = "label is required"
        elif not extractor:
            reason = "extractor is required"
        elif verification not in VERIFICATION_STATES:
            reason = "verification state is not recognized"
        elif not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            reason = "confidence must be a number"
        elif not 0.0 <= float(confidence) <= 1.0:
            reason = "confidence must fall between 0 and 1"
        elif source_path not in articles_by_path:
            reason = "source_path does not name a note in this wiki"
        elif not anchor:
            reason = "evidence_anchor is required"
        else:
            excerpt = anchor_excerpt(articles_by_path[source_path]["_body"], anchor)
            if excerpt is None:
                reason = "evidence_anchor does not resolve in the cited note"

        if reason is not None:
            dropped.append({"record": label, "reason": reason})
            continue

        accepted.append(
            {
                "id": f"{kind}:{label}",
                "type": kind,
                "label": label,
                "source_path": source_path,
                "evidence_anchor": anchor,
                # The excerpt itself stays out of the graph; the hash proves
                # which text was read without copying the note into the file.
                "evidence_sha256": hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
                "extractor": extractor,
                "confidence": round(float(confidence), 4),
                "verification": verification,
            }
        )

    accepted.sort(key=lambda item: (identity(item["id"]), item["source_path"]))
    dropped.sort(key=lambda item: (identity(item["record"]), item["reason"]))
    confirmed = [item for item in accepted if item["verification"] in CONFIRMED_STATES]
    return {
        "enabled": True,
        "accepted": len(accepted),
        "verified": len(confirmed),
        "inferred": len(accepted) - len(confirmed),
        "dropped": dropped,
        "records": accepted,
    }


def raw_file_stems(raw: Path | None) -> set[str]:
    """Filenames under `raw/`, so a link to captured source material is not
    reported as pointing at nothing.

    Obsidian resolves `[[target]]` against the whole vault. This graph names
    notes from `wiki/` alone, so a note citing a preserved capture by filename
    had a link that works in the app and was reported broken here. Two such
    links sat in the vault when the Stop hook was about to start blocking on
    this list, which would have spent the warning on correct notes.

    Only names are read. `raw/` holds immutable captures: nothing in it becomes
    a node, and its contents are never parsed for links.
    """
    if raw is None or not raw.is_dir():
        return set()
    return {
        identity(path.stem) for path in raw.rglob("*") if path.is_file()
    }


def build(
    wiki: Path, semantic: Path | None = None, raw: Path | None = None
) -> dict[str, Any]:
    files = sorted(path for path in wiki.rglob("*.md") if path.is_file())
    raw_stems = raw_file_stems(raw)
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
    # shared by several notes stays unresolved rather than being guessed.
    stem_map = {
        stem: owners[0] for stem, owners in stem_owners.items() if len(owners) == 1
    }

    backlinks: dict[str, set[str]] = {key: set() for key in title_map}
    missing: dict[str, dict[str, Any]] = {}
    articles: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    sources: dict[str, dict[str, Any]] = {}

    for note in notes:
        raw_links = WIKILINK.findall(content_without_fences(note["_body"]))
        # Link variants that differ only by case or Unicode form are one edge.
        seen_targets: dict[str, str] = {}
        for raw in raw_links:
            target = normalized_target(raw)
            if target:
                seen_targets.setdefault(identity(Path(target).name), target)
        targets = sorted_by_text(seen_targets.values())

        # Filename and title spellings of the same note are one edge.
        resolved: dict[str, str] = {}
        unresolved: list[str] = []
        for target in targets:
            target_key = identity(Path(target).name)
            target_note = title_map.get(target_key) or stem_map.get(target_key)
            if target_note is None:
                # A capture under raw/ resolves in Obsidian but is not a note,
                # so the link is neither broken nor an edge between articles.
                if target_key in raw_stems:
                    continue
                unresolved.append(target)
                entry = missing.setdefault(
                    target_key, {"target": target, "referenced_by": set()}
                )
                entry["referenced_by"].add(note["title"])
            else:
                target_title = target_note["title"]
                resolved.setdefault(identity(target_title), target_title)
                backlinks[identity(target_title)].add(note["title"])

        cited: list[str] = []
        declared = note["frontmatter"].get("sources")
        if isinstance(declared, list):
            for entry in declared:
                reference = str(entry).strip()
                if not reference:
                    continue
                node_id = f"source:{reference}"
                if node_id not in sources:
                    sources[node_id] = {
                        "id": node_id,
                        "type": "source",
                        "reference": reference,
                        "kind": "url" if "://" in reference else "file",
                        # A path is recorded relative to the knowledge root,
                        # which sits one level above the wiki directory.
                        "present": (
                            True
                            if "://" in reference
                            else (wiki.parent / reference).exists()
                        ),
                    }
                if node_id not in cited:
                    cited.append(node_id)

        articles.append(
            {
                "id": f"article:{note['title']}",
                "type": "article",
                "title": note["title"],
                "path": note["path"],
                "frontmatter": note["frontmatter"],
                "links": sorted_by_text(resolved.values()),
                "missing_links": unresolved,
                "sources": sorted(cited),
            }
        )
        for node_id in sorted(cited):
            edges.append(
                {"type": "cites", "from": f"article:{note['title']}", "to": node_id}
            )

    for article in articles:
        article["backlinks"] = sorted_by_text(backlinks[identity(article["title"])])
        for link in article["links"]:
            edges.append(
                {"type": "links_to", "from": article["id"], "to": f"article:{link}"}
            )

    # Topics come from the index, which sits beside the wiki directory. A
    # knowledge root without one still produces a valid graph with no topics.
    topics: list[dict[str, Any]] = []
    index_path = wiki.parent / "index.md"
    if index_path.is_file():
        for label, members in index_topics(index_path.read_text(encoding="utf-8")):
            resolved_members: list[str] = []
            for member in members:
                member_note = title_map.get(identity(member)) or stem_map.get(
                    identity(member)
                )
                if member_note is None:
                    entry = missing.setdefault(
                        identity(member), {"target": member, "referenced_by": set()}
                    )
                    entry["referenced_by"].add("index.md")
                    continue
                if member_note["title"] not in resolved_members:
                    resolved_members.append(member_note["title"])
            topics.append(
                {
                    "id": f"topic:{label}",
                    "type": "topic",
                    "label": label,
                    "path": "index.md",
                    "members": sorted_by_text(resolved_members),
                }
            )
            for member in sorted_by_text(resolved_members):
                edges.append(
                    {
                        "type": "categorized_under",
                        "from": f"article:{member}",
                        "to": f"topic:{label}",
                    }
                )
    topics.sort(key=lambda item: (identity(item["label"]), item["id"]))

    articles.sort(key=lambda item: (identity(item["title"]), item["path"]))
    orphans = sorted_by_text(
        [
            article["title"]
            for article in articles
            if not article["links"] and not article["backlinks"]
        ]
    )
    missing_targets = [
        {
            "target": entry["target"],
            "referenced_by": sorted_by_text(entry["referenced_by"]),
        }
        for entry in sorted(
            missing.values(),
            key=lambda item: (item["target"].casefold(), item["target"]),
        )
    ]
    edges.sort(key=lambda item: (item["type"], identity(item["from"]), identity(item["to"])))

    semantic_layer: dict[str, Any] = {
        "enabled": False,
        "accepted": 0,
        "verified": 0,
        "inferred": 0,
        "dropped": [],
        "records": [],
    }
    if semantic is not None:
        semantic_layer = load_semantic(
            semantic, {note["path"]: note for note in notes}
        )

    nodes = articles + topics + sorted(sources.values(), key=lambda item: item["id"])

    return {
        "schema_version": 2,
        "source": "wiki Markdown",
        "counts": {
            "article": len(articles),
            "topic": len(topics),
            "source": len(sources),
            "edge": len(edges),
        },
        "nodes": nodes,
        "edges": edges,
        "missing_targets": missing_targets,
        "orphans": orphans,
        "semantic": semantic_layer,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wiki", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--semantic",
        type=Path,
        help="JSON file of model-produced records to validate and include",
    )
    parser.add_argument(
        "--raw",
        type=Path,
        help=(
            "raw/ directory whose filenames also resolve a wikilink in Obsidian; "
            "only names are read and nothing in it becomes a node"
        ),
    )
    args = parser.parse_args()

    if not args.wiki.is_dir():
        print(f"knowledge-graph: wiki directory not found: {args.wiki}", file=sys.stderr)
        return 2
    if args.semantic is not None and not args.semantic.is_file():
        print(
            f"knowledge-graph: semantic input not found: {args.semantic}",
            file=sys.stderr,
        )
        return 2

    try:
        graph = build(args.wiki, args.semantic, args.raw)
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
