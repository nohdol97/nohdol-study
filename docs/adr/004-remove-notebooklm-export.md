# ADR 004 — Remove NotebookLM export skill

- Date: 2026-07-25
- Status: Active
- Target: All `notebooklm-export` skills, NotebookLM mode of `study-install`,
  NotebookLM field in `REGISTRY.md`
- Relationship: [Replaces the NotebookLM part of ADR 003](003-cli-learning-integrations.md).
  The Understand Anything·Obsidian decision remains in effect.

## context

ADR 003 is a verified export packet and an optional CLI that will be opened once it passes the security gate.
bridge was adopted. After actually making it and measuring it, the results are as follows.

- Total of skill, script, and test **763 lines**.
- **1 actual use packet**.
- **0 cases** where NotebookLM creations were returned to the vault.
- CLI bridge determines blocking at the release gate ([2b-E record](../reviews/2026-07-25-notebooklm-understand-anything-security.md),
  Download redirect fix absent in latest stable release v0.7.3).

What is decisive is that there has never been a recall. Manifest, Hash, Timestamp
The directory is a ledger for “reverting the product to its original source later.”
If no action occurs, the ledger guarantees nothing. not happening
It meant maintaining 763 lines for work.

## decision

Removes `notebooklm-export` skill. I'm not saying you shouldn't use NotebookLM —
It is always possible to write directly in the browser, and the discipline needed to do so is already in place elsewhere.
It's in a place.

Remove together:

- NotebookLM mode interview of `study-install` and `bootstrap.sh --notebooklm` flag
- `NotebookLM`·`NotebookLM workflow` field of `REGISTRY.md`
- `verify-packet.sh` (packet revalidation before upload) and `bridge-gate.sh` (release gate).
  The former will not be caught if there is no retrieval workflow, and the latter has a conclusion of “don’t use it.”
  It is a gate for tools.

## What is left behind

- **"AI output is not independent evidence"** rule (see AGENTS section 4, `note-writer` type 2).
  NotebookLM is used as an example, but this also applies when used directly in the browser.
  This is a general rule. Rather, it is more important now that automation is gone.
- Existing packet from `_workspace/notebooklm/`. Do not delete it as it is untracked user output.
  No.
- ADR 003 and Security Review Document. Records are not changed.

## result

If you want to select verified notes by topic and upload them to NotebookLM, you can now
Select a file. What is lost is the automatic rejection of the `unverified` note, and that decision is
`note-writer` is already doing it on a note basis — the note has status `verification`
Because it is logged, what has been verified can still be read from the file.

## Conditions for review

There is a flow to actually retrieve the NotebookLM creation to the vault, and then “Which answer is this?”
If the need to look back on "which file the version came from" is observed, it is recreated.
Even in this case, do not create the manifest first, but run the recovery flow first.
