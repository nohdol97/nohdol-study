---
name: vault-gardening
description: Report what has drifted in the knowledge root - links pointing at nothing, notes with no link and no category, frontmatter that breaks the note contract, cited sources missing from raw/, and a session cache over budget. Use for vault 점검, 지식 정리, 깨진 링크 찾기, 고아 노트, 노트 상태 점검, and periodic upkeep of the notes. Do NOT use it to add links or edit notes automatically, and do NOT treat an empty report as evidence that the knowledge is correct.
---

# vault-gardening — Find the drift, decide by hand

## Why

A vault degrades quietly. A rename leaves a link pointing at nothing, a note
loses a frontmatter field, the hot cache grows past the budget that made it
cheap to load. None of it breaks anything today, which is why it accumulates
until the vault is untrustworthy in a way nobody can date.

## Run

```sh
python3 .agents/skills/vault-gardening/scripts/garden.py --vault vault
```

It reports and never edits. Five sections:

- **links pointing at nothing** — with who pointed at them, so the fix is
  either the link or the missing note, decided per case.
- **notes with no link and no category** — a note the index groups is filed,
  not lost, so only the genuinely unreachable are listed.
- **frontmatter that breaks the note contract** — missing required fields,
  a status or verification state outside the contract, a non-ISO date, an
  `updated` earlier than `created`, and a note claiming it was cross-checked
  without recording when.
- **cited sources that are not in raw/** — a note citing a file that is not
  there cannot have its evidence re-examined.
- **session context** — a missing `index.md`, `log.md`, or `hot.md`, and a
  hot cache over its byte budget.

It scans `wiki/`, the three derived files, and `raw/` existence. **It does not
walk the rest of the knowledge root.** A real vault holds unrelated
directories, and on cloud storage walking them is slow and pointless.

## Then decide, one at a time

The report is a list of questions, not a task list.

- **A broken link** is either a typo, a rename to follow, or a note worth
  writing. All three are fine; guessing which is not.
- **An orphan** is a note nobody connected yet. Link it where a real
  relationship exists, put it under a topic in `index.md`, or leave it alone.
  **Never add a link to empty the list** — a decorative link makes the graph
  say something false, which is worse than an honest orphan.
- **A contract violation** is usually a real gap: a missing `checked` date on a
  cross-checked note means nobody can tell whether it is still true. Fix it by
  re-checking, not by writing today's date.
- **A missing source** means the evidence is gone. Either restore it to `raw/`
  or lower the note's verification state to match what can still be shown.
- **An over-budget `hot.md`** is trimmed by deciding what a session actually
  needs, not by deleting the tail.

Record what you changed through `note-writer` so `index.md`, `log.md`, and
`hot.md` stay consistent. Gardening is a knowledge change like any other.

## What a clean report does not mean

An empty report says the structure holds. It says nothing about whether the
notes are true, current, or worth keeping. Staleness of content is judged by
re-reading against sources under the evidence rules, and this script never
opens a source.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Drift | Found by accident, months later | Listed with the note and field that drifted |
| Orphans | Linked decoratively to look tidy | Left honest unless a real relationship exists |
| Scope | A vault-wide walk over unrelated content | Curated layer only |
| Authority | Clean report read as "knowledge is good" | Structure only; content still judged by evidence |
