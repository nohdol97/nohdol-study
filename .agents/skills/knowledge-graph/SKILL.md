---
name: knowledge-graph
description: Rebuild and inspect a deterministic JSON graph from curated Markdown wikilinks, including frontmatter, outgoing links, backlinks, missing targets, duplicate titles, and orphan notes. Use for 지식 그래프, 백링크 점검, 고아 노트, 깨진 링크, graph rebuild, or graph quality measurement. Do NOT treat the JSON as a knowledge source or run basic-memory comparison below 100 curated notes.
---

# knowledge-graph — Reproducible Markdown graph

## Why

Obsidian visualizes links but does not provide a portable, testable graph
artifact for both Claude and Codex. This parser makes link quality measurable
without introducing a server or replacing Markdown as the source of truth.

## Rebuild

From the harness root:

```sh
python3 .agents/skills/knowledge-graph/scripts/build_graph.py \
  --wiki vault/wiki \
  --output _workspace/knowledge-graph.json
```

The parser uses only the Python standard library. It:

- reads YAML frontmatter conservatively without requiring a YAML package;
- uses the H1 as title, falling back to the filename stem;
- ignores wikilinks inside fenced code blocks;
- normalizes aliases, headings, and block references to their note targets;
- calculates backlinks, missing targets, and notes with no links in either
  direction;
- sorts every emitted collection and writes stable JSON;
- fails on duplicate normalized titles rather than guessing a target.

## Review

1. Fix duplicate titles first; no graph is emitted for ambiguous identity.
2. Review `missing_targets` for broken links or intentional future notes.
3. Review `orphans` for notes that need a meaningful relationship. Do not add
   decorative links just to make the count zero.
4. Regenerate after Markdown changes. Never hand-edit the JSON.

Do not compare or adopt basic-memory until `vault/wiki/` has at least 100
Markdown notes. At that gate, compare backlink accuracy, missing/orphan
detection, representative retrieval, runtime cost, source non-modification,
and server-free portability against this baseline.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Broken-link review | Manual Obsidian inspection | Sorted missing-target report |
| Backlinks | UI-dependent | Portable deterministic JSON |
| Ambiguous titles | Silent or tool-specific resolution | Hard failure |
| Source authority | Index may become another store | Markdown remains the only source |
