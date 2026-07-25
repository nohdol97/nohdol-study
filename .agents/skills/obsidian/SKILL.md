---
name: obsidian
description: Author and verify Obsidian file formats - Obsidian Flavored Markdown, Bases (.base), JSON Canvas (.canvas) - and drive a running vault through the official CLI, routing internally to the right mode. Use for 위키링크, 콜아웃, 임베드, 프론트매터 속성, 캔버스, 마인드맵, 지식 맵, .base, 테이블 뷰, 필터, and Obsidian CLI 조작. Do NOT use it to decide whether a note's content is true (that is note-writer and the evidence rules), to rebuild the knowledge graph (that is knowledge-graph), or to run CLI commands that change a vault without saying what will change.
---

# obsidian — Obsidian formats and vault CLI

## Why

Obsidian's own extensions - wikilinks, callouts, properties, canvases, bases -
are what make a vault more than a folder of text. Writing them by memory
produces files that look right and silently fail to render or load.

Three of the four modes are plain file formats, so they work on a machine with
no Obsidian installed. Only the CLI needs the app, and its absence limits that
one mode rather than the skill.

## Route

| The user wants | Mode | Needs |
|---|---|---|
| a note with wikilinks, embeds, callouts, properties | `obsidian-markdown` | nothing |
| a database-like view over notes | `obsidian-bases` | nothing |
| a canvas, mind map, or knowledge map | `json-canvas` | nothing |
| to read or change a vault from the command line | `obsidian-cli` | Obsidian running |

Per-mode procedure is in `references/modes.md`. The upstream workflow for each
is at `.tools/obsidian-skills/skills/<mode>/SKILL.md`; read it and follow it
inside the boundaries below.

The pin also ships an upstream `defuddle` skill. It is not adopted - this
repository's own `defuddle` skill carries the immutable-capture and evidence
rules that one lacks.

## Verify what you write

Every file this skill produces gets checked before it is called done:

```sh
python3 .agents/skills/obsidian/scripts/validate.py PATH [PATH ...]
```

It checks canvases against JSON Canvas 1.0 (node types, geometry, unique ids,
and edges that actually point at nodes), Markdown for unclosed or empty
wikilinks and unknown callout types, and bases for the structural mistakes
that stop a file from loading. The callout list is read from the pinned
reference, so it tracks upstream instead of a private copy.

The base check is a structural pre-check, not a YAML validator - this
repository keeps scripts dependency-free. Passing it means the file is not
obviously broken, not that Obsidian will accept every field. Say that plainly
rather than reporting a base as verified.

## Boundaries

- **Preflight**: `install-phase2b-tools.sh --check` must report `obsidian-skills`
  as `ready`. Without the pin, write formats from the validator's rules and say
  the upstream reference was unavailable.
- **The vault is knowledge, not scratch space.** Generated canvases and bases
  belong beside the notes they describe only when the user asked for a durable
  artifact; anything exploratory goes to `_workspace/`.
- **Never rewrite existing notes to fit a format.** A note that renders fine is
  not a defect. Fix what the user asked about.
- **CLI writes are stated first.** Before any `obsidian` command that creates,
  edits, moves, or deletes, say which vault and which files it touches. Read
  commands need no ceremony.
- **Obsidian absent** means the CLI mode is unavailable, never a failure of the
  other three. Report it and continue with the file formats.
- Content correctness is not this skill's job. Whether a claim belongs in the
  vault is decided by `note-writer` and the evidence rules.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Format correctness | Syntax written from memory, fails silently | Checked against the spec before completion |
| Callout and link errors | Found later in the app | Named with file and line |
| App dependency | Canvas and base work assumed to need Obsidian | Three modes work headless, CLI reports unavailable |
| Vault safety | Generated files scattered among notes | Durable and exploratory output separated |
