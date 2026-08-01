#!/usr/bin/env python3
"""PreToolUse guard against sending vault material into an external runtime.

Why this exists
---------------
`AGENTS.md` section 5 already says vault content never goes through an MCP
server that executes code elsewhere. Until now that was a rule with nothing
behind it. The permission prompt does not close the gap: it asks whether to run
a tool, not whether the payload it carries contains the user's notes. Approving
`add_code_cell` is approving "run a cell", and a cell is a wall of code nobody
reads line by line before clicking yes.

The failure this is built for is not a careless paste. It is a plausible one:
"let me cross-check the note's existing numbers in the notebook", and the note
body goes into a cell. That is exactly the kind of step that looks like ordinary
work while moving private material onto someone else's machine.

Why this is separate from study-tool-guard
------------------------------------------
`study-tool-guard.py` engages only when `STUDY_SURFACE` marks a surface that
runs without a permission prompt, and stays silent otherwise on the reasoning
that an interactive prompt already does its job. That reasoning holds for where
a write lands. It does not hold for what a payload contains, so this guard runs
on every surface, prompt or no prompt. Keeping the two apart also keeps the
older guard's stated premise true instead of quietly widening it.

Contract
--------
Reads a PreToolUse payload on stdin, prints nothing when the call is allowed,
and prints a deny decision when it is not. Exit status stays 0 either way: a
crashing guard must not look like a blocked tool. Both CLI dialects are handled
the same way `study-tool-guard.py` handles them.

Scope and limits
----------------
This guards the Colab cell-writing tools, which are the egress path this
harness actually has. It is a targeted check on a known channel, not general
data-loss prevention: content can still be paraphrased, encoded, or read aloud
into a cell, and no pattern match catches that. What it does catch is the
literal case - a note body, a wikilink, or a knowledge-root path pasted into a
cell - which is the form the realistic mistake takes.

Public facts that happen to be recorded in the vault are not vault material. A
class distribution measured from a public dataset stays allowed, because the
check looks for vault *structure* (paths, wikilinks, the note contract), never
for numbers.

The wikilink test deliberately ignores `[[1, 2]]`-shaped matches so ordinary
nested-list code is not blocked. A note title that is short, Latin-only, and
comma-bearing can slip past that filter; the knowledge-root path check and the
frontmatter check are the load-bearing ones.
"""

import json
import os
import re
import sys

DIALECT_CLAUDE = "claude"
DIALECT_ANTIGRAVITY = "antigravity"

# Cell-writing tools on the Colab MCP server. Matched loosely on the server
# segment so a differently-registered prefix still resolves; the verb suffix is
# what identifies a call that carries author-supplied content.
CELL_WRITE_SUFFIXES = ("add_code_cell", "update_cell", "add_text_cell")

# The note contract's fingerprint. These two keys co-occur in every curated
# note and in no plausible training script.
NOTE_CONTRACT = (re.compile(r"(?m)^\s*verification:\s*\S"), re.compile(r"(?m)^\s*checked:\s*\S"))

# `[[Some Note]]`. Filtered below so `[[1, 2]]` and similar code do not match.
WIKILINK = re.compile(r"\[\[([^\[\]\n]{2,120})\]\]")
HANGUL = re.compile(r"[가-힣]")

# A vault-relative path written out in full.
VAULT_PATH = re.compile(r"(?:^|[\s'\"(=/])vault/(?:wiki|raw|index\.md|log\.md|hot\.md)")
KNOWLEDGE_FILES = re.compile(r"(?:^|[\s'\"(/])(?:index|log|hot)\.md\b")


def emit_deny(reason, dialect):
    if dialect == DIALECT_ANTIGRAVITY:
        payload = {"decision": "deny", "reason": reason}
    else:
        payload = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            },
            "decision": "block",
            "reason": reason,
        }
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")
    sys.exit(0)


def study_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def knowledge_root(root):
    """Where `vault` points, if it is connected. Absent on a fresh install."""
    link = os.path.join(root, "vault")
    if not os.path.exists(link):
        return ""
    return os.path.realpath(link)


def read_call(payload):
    call = payload.get("toolCall")
    if isinstance(call, dict):
        args = call.get("args")
        return DIALECT_ANTIGRAVITY, call.get("name", ""), args if isinstance(args, dict) else {}
    args = payload.get("tool_input")
    return DIALECT_CLAUDE, payload.get("tool_name", ""), args if isinstance(args, dict) else {}


def is_cell_write(tool):
    return "colab" in tool.lower() and tool.endswith(CELL_WRITE_SUFFIXES)


def strings_in(value):
    """Every string anywhere in the argument object.

    Checking known keys by name would go blind the moment the server renames
    one, and the cost of walking the whole object is nothing.
    """
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings_in(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings_in(item)


def looks_like_wikilink(text):
    for inner in WIKILINK.findall(text):
        if HANGUL.search(inner):
            return inner
        if " " in inner and not re.search(r"[,'\"]", inner):
            return inner
    return ""


def find_vault_material(text, kroot):
    """What in this string identifies it as vault material, or "" if nothing."""
    if kroot and kroot in text:
        return "the knowledge-root path %s" % kroot
    if kroot:
        base = os.path.basename(kroot)
        if base and len(base) > 3 and base in text:
            return "the knowledge-root directory name %r" % base
    if VAULT_PATH.search(text):
        return "a vault-relative path"
    if all(pattern.search(text) for pattern in NOTE_CONTRACT):
        return "a curated note's frontmatter (verification/checked)"
    link = looks_like_wikilink(text)
    if link:
        return "a wikilink [[%s]]" % link
    if KNOWLEDGE_FILES.search(text) and ("wiki" in text or "raw/" in text):
        return "knowledge-root filenames"
    return ""


def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return
    if not isinstance(payload, dict):
        return

    dialect, tool, args = read_call(payload)
    if not is_cell_write(tool):
        return

    kroot = knowledge_root(study_root())
    for text in strings_in(args):
        found = find_vault_material(text, kroot)
        if found:
            emit_deny(
                "This notebook cell carries %s. The Colab runtime is an external machine, and "
                "AGENTS.md section 5 keeps vault content off it without separate explicit "
                "approval. Public data and public code are fine here; so are figures measured "
                "from a public dataset. What is not fine is the note itself - its body, its "
                "wikilinks, or its path. Put the public form in the cell and keep the note on "
                "this machine." % found,
                dialect,
            )


if __name__ == "__main__":
    main()
