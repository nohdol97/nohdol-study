---
name: diagram
description: Draw a diagram for a study note and pick the tool that fits it - Mermaid inline by default, D2 rendered to SVG when the structure outgrows Mermaid, JSON Canvas for a map of existing notes, and matplotlib for anything with real coordinates. Use for 다이어그램, 그림, 도식, 아키텍처 그리기, 플로우차트, 시퀀스 다이어그램, 개념도, 지식 맵, and 그래프 그려줘. Do NOT use it to decide what is true (that is note-writer and the evidence rules), and do NOT reach for a heavier tool than the diagram needs.
---

# diagram — Pick the tool the diagram needs

## Why

A diagram in a study note earns its place by making a structure easier to hold
than the prose would. That fails in two directions: a tool too weak leaves a
tangle nobody redraws, and a tool too heavy leaves a picture nobody can edit.

Mermaid is the default because Obsidian renders it with nothing installed, the
source stays in the note, and a diff shows what changed. Everything else here
is an escalation with a reason.

## Choose

| The diagram is | Use | Why |
|---|---|---|
| a flow, sequence, state, class, or ER structure | Mermaid, inline | renders in Obsidian, no toolchain, diffable source |
| the same but large - past about 15 nodes or three levels of nesting | D2 → SVG, embedded | Mermaid's layout stops being readable at that size |
| a map of notes that already exist | JSON Canvas → the `obsidian` skill | a canvas can embed the notes themselves, not restate them |
| anything with real coordinates - a trajectory, a transform, a plot | matplotlib → SVG, embedded | only a renderer gets the geometry right |

Escalate when the check says so, not by taste:

```sh
python3 .agents/skills/diagram/scripts/check.py NOTE.md
```

It reports an unknown Mermaid diagram type, unbalanced delimiters, an embedded
asset that does not exist, and an SVG a failed render left empty. It also
counts nodes and says when a diagram has outgrown Mermaid. That count is
advice - the note still renders - but it is the signal to escalate rather than
adding one more edge to a diagram already too dense.

The check is a pre-check, not a renderer. Mermaid's parser is JavaScript and
this repository keeps its scripts dependency-free, so a file that passes may
still fail to render. Look at the diagram in Obsidian before calling it done.

## Rendering to SVG

D2 and matplotlib produce files, and files go stale silently. So:

- Write the source next to the note it serves, under `assets/`, with the same
  base name as the SVG. A rendered file with no source beside it cannot be
  corrected, only redrawn.
- Render with `d2 assets/name.d2 assets/name.svg`, or a small matplotlib
  script saved beside its output. Embed with `![[assets/name.svg]]`.
- Run the check on the SVG too. A failed render often still writes a file, and
  an empty canvas embeds without complaint.
- `d2` is optional. When it is missing, say so and keep the diagram in Mermaid
  rather than installing it mid-task; a dense Mermaid diagram the user can see
  beats a perfect one that does not exist.

## Boundaries

- A diagram is an explanation, not evidence. It carries no verification state
  of its own, and a relationship drawn in a diagram is not established by
  having been drawn. `note-writer` and the evidence rules still decide what the
  note may claim.
- Generated images are not sources. When one is produced by an image model
  rather than a renderer, record that provenance in the note and say the image
  is illustrative.
- Do not send note or source content to an external rendering or image service.
  A scene description is enough (AGENTS.md section 5).
- Redraw from the source, never by editing an SVG by hand.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Tool choice | Habit, or whatever is installed | Matched to structure, escalated on a counted threshold |
| Editability | Rendered image with no source | Source beside the output, same base name |
| Silent failure | Empty SVG or broken embed ships | Both caught before the note is done |
| Authority | Diagram read as a finding | Explanation only; evidence rules unchanged |
