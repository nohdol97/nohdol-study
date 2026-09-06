# ADR 005 — Place external runtime leak gate on separate hook

- Date: 2026-08-01
- Status: Active
- Target: New `.agents/hooks/study-egress-guard.py`, `.claude/settings.json`,
  `.codex/config.toml`, `AGENTS.md` Section 5
- Relation: [Move the safety rules of ADR 001](001-initial-study-harness.md) to the enforcement mechanism.
  Leave `study-tool-guard` as is and do not touch it.

## context

Section 5 of `AGENTS.md` already states that “vault contents may not pass through such servers without separate explicit approval.”
2026-08-01 What was revealed in the first actual use of Colab MCP was that
It is true that there was **no device** behind the sentence.

Approval prompts don't fill this hole. The prompt asks "Use this tool
Should I run it?” rather than “Does this payload contain the user’s notes?”
Accepting `add_code_cell` means authorizing "turning the cell", and the cell is not
It's a chunk of code that doesn't read line by line.

The failure you need to prepare for is not a careless paste, but a **plausible step** —
Putting the text of the note into a cell, saying, “Let’s compare the existing numbers in the note in the notebook.”
It seems like an ordinary task, but moving private data to someone else's machine.

## decision

Instead of extending the existing `study-tool-guard.py`, create a **separate hook**.

`study-tool-guard` only displays when `STUDY_SURFACE` displays a surface without prompting.
Waking up, the evidence was that "in interactive mode, the prompt already does that." that
The evidence holds **where the writing falls**, but **what is in the payload**.
It does not apply to whether it exists. So the outflow gate is always
It turns on.

If we had pushed it into the same file, the documented premise of the existing hook would have quietly expanded.
If you separate the two, each hook's docstring will remain true.

There is one more secondary but practical reason. Protected by `study-tool-guard`
The Telegram bot was retired on 2026-07-31, so the hook is currently dormant. living
Do not place the gate on a dormant gate.

## What to block and what not to block

What's blocking it is the structure of the vault — knowledge root absolute path, knowledge root directory name,
`vault/wiki|raw|index.md|log.md|hot.md` relative path, fingerprint of note contract
(Simultaneous appearance of `verification:` and `checked:`), Wikilink.

It's a **shame** not to stop it. The actual distribution measured from the public dataset is recorded in the vault.
This gate makes lab impossible if the public dataset code is blocked because of its presence.
Cell actually run on 2026-08-01 — WM-811K with the number of 9 classes as the contrast constant
Cell — Passing was fixed by regression testing.

Wikilink checking intentionally ignores the shape `[[1, 2]]`. Blocking nested list literals
The entire numerical calculation code takes place. Instead, it's a short, Latin-only note with a comma.
Titles can escape this filter. The real line of defense is route inspection and front matter.
He is a prosecutor, and Wikilink is an assistant.

## Limits — state them

This is **targeted scanning of a single known channel**, not general data leak prevention.
no. What pattern do you need when you rewrite, encode, or summarize the content and put it in a cell?
I can't even find a match. Catching is literal — note text, wikilink,
The knowledge root path goes straight into the cell — and that's what a realistic mistake looks like.

Colab MCP's three cell creation tools (`add_code_cell`·`update_cell`·`add_text_cell`)
It is a target. Other exfiltration vectors (e.g. file uploads from browser tools) are outside the scope of this ADR.
No, add tools to the same hook as needed.

**Codex's support for `PreToolUse` was not confirmed in the live session.**
Although it was registered symmetrically in `.codex/config.toml` and TOML parsing was verified,
The path is Claude Code.

## Conditions for review

When cases where false positives actually block the lab are observed, the test items are narrowed. Conversely, the pattern
If bypassed outflow is observed, then the pattern should not be increased but the channel itself should be shortened.
Review pages first — make cell creation tools approval-required, or contain only public code.
The method is to create a separate file and upload only that file.
