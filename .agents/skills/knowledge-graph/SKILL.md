---
name: knowledge-graph
description: Rebuild and inspect a deterministic typed JSON graph of article, topic, and source nodes from curated Markdown, covering wikilinks, backlinks, index categories, cited sources, missing targets, duplicate titles, and orphan notes, and validate model-inferred entity and claim records against the evidence they cite. Use for 지식 그래프, 백링크 점검, 고아 노트, 깨진 링크, 주제 분류 확인, 근거 검증, graph rebuild, or graph quality measurement. Do NOT treat the JSON as a knowledge source or compare another index without an explicitly scoped non-modifying corpus.
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
  --raw vault/raw \
  --output _workspace/knowledge-graph.json
```

`--raw` is optional and changes only `missing_targets`. Obsidian resolves
`[[target]]` against the whole vault, so a note citing a capture by filename
has a link that works in the app; without this the graph reports it broken.
Only filenames are read — nothing under `raw/` becomes a node, and its
contents are never parsed for links.

The graph has three node types, all read straight from the files:

- `article` — one per note in `wiki/`, with its links, backlinks, missing
  links, and cited sources;
- `topic` — one per category grouping in `index.md`. A top-level bullet naming
  no note whose nested bullets link to notes is a category; a bullet that links
  directly is a chronology entry, so the recent-changes list is not mistaken
  for categories;
- `source` — one per entry in a note's `sources` frontmatter, marked `url` or
  `file`, with `present` recording whether a `raw/` path actually exists.

Edges are `links_to`, `categorized_under`, and `cites`. A knowledge root with a
single note still produces a real graph, because topics and sources exist
independently of note-to-note links.

The parser uses only the Python standard library. It:

- reads YAML frontmatter conservatively without requiring a YAML package;
- uses the H1 as title, falling back to the filename stem;
- resolves a link by title or by filename, because Obsidian resolves filenames
  and this graph names notes by their H1; a filename shared by several notes
  stays unresolved instead of being guessed;
- normalizes Unicode to NFC before matching, so a decomposed Korean filename
  still matches a composed link;
- ignores wikilinks inside fenced code blocks and inline code spans, including
  a span whose closing backtick run sits on a later line - a code span carries
  a line ending inside it, so a link written across the break is still code;
- normalizes aliases, headings, and block references to their note targets, and
  counts case or spelling variants of one note as a single edge;
- calculates backlinks, missing targets, and notes with no links in either
  direction;
- sorts every emitted collection and writes stable JSON;
- fails on duplicate normalized titles rather than guessing a target.

Edges come from wikilinks in the note body only. A relationship recorded solely
in the `related` frontmatter field is not an edge, so such a note can still be
reported as an orphan. Indented four-space code blocks are not stripped.

Two link shapes are outside what it resolves. A wikilink whose text contains a
code span is dropped with that span, so link by filename instead. A path-style
link matches on the final name only, so `[[wrong/dir/note]]` still resolves to
`note` while Obsidian reports it broken. Embeds (`![[note]]`) count as links,
matching the Obsidian graph.

No note body is copied into the graph, so the file can be shared or inspected
without carrying the knowledge base inside it.

## Semantic enrichment (opt-in)

Entities, claims, and implicit relationships are model inferences, so they
never enter the deterministic run. Produce them separately - for example with
`understand-knowledge` - as a JSON file of `records`, then validate them:

```sh
python3 .agents/skills/knowledge-graph/scripts/build_graph.py \
  --wiki vault/wiki \
  --output _workspace/knowledge-graph.json \
  --semantic _workspace/understand-anything/records.json
```

Each record must carry `kind` (`entity` or `claim`), `label`, `source_path`
naming a note in this wiki, `evidence_anchor`, `extractor`, `confidence`
between 0 and 1, and a `verification` state from the note contract. The anchor
is a heading (`## Section`) or a phrase that appears literally in that note.

Validation resolves the anchor inside the cited note. A record whose anchor
resolves nowhere is **dropped**, not filed as low confidence - an unfalsifiable
claim is worse in a knowledge base than a missing one. Dropped records are
listed with a reason, and the output counts `verified` (`primary-confirmed` or
`cross-checked`) apart from `inferred`.

Only the anchor and a hash of the matched excerpt are stored. Note text is
never copied, and the validator only reads structured fields, so
instruction-like sentences inside a note are data here and nothing else.

An accepted record is still a candidate. Promote it to knowledge through
`note-writer` after reading the note and its underlying source.

## Review

1. Fix duplicate titles first; no graph is emitted for ambiguous identity.
2. Review `missing_targets` for broken links or intentional future notes. Pass
   `--raw` first, or a link to a preserved capture reads as a broken one.
3. Review `orphans` for notes that need a meaningful relationship. Do not add
   decorative links just to make the count zero.
4. Regenerate after Markdown changes. Never hand-edit the JSON.

## Comparing another index

Pointing another tool at the user's notes needs one rule above the
measurement: the corpus comes back unchanged. The pilot enforces it.

```sh
python3 .agents/skills/knowledge-graph/scripts/pilot.py \
  --corpus vault/wiki \
  --candidate 'the exact read-only command' \
  --label basic-memory
```

It hashes every Markdown file before and after, measures the baseline, runs the
candidate, and **fails when any file was added, removed, or modified** -
whatever the candidate reported. A command containing a segment like `write`,
`format`, `reset`, or `sync` is refused before it runs rather than judged
afterwards.

The candidate command is supplied, never assumed. Do not write an invocation
for a CLI you have not installed and read the help of; a command line from
memory is the same unverified claim this harness refuses everywhere else.

Only run this on a corpus the user named. Runtime and counts do not decide it:
judge retrieval on questions written before the run, and weigh what each option
costs to keep alive - the baseline has no state to rebuild, an index does.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Broken-link review | Manual Obsidian inspection | Sorted missing-target report |
| Backlinks | UI-dependent | Portable deterministic JSON |
| Ambiguous titles | Silent or tool-specific resolution | Hard failure |
| Small knowledge base | One note yields an empty graph | Topics and sources make it useful from the first note |
| Inferred claims | Filed beside facts | Evidence resolved or the record dropped |
| Note text | Copied into the derived artifact | Anchor and hash only |
| Source authority | Index may become another store | Markdown remains the only source |
