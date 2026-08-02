#!/usr/bin/env python3
"""PreToolUse guard for study surfaces that run without a permission prompt.

Why this exists
---------------
Every interactive surface has one gate that catches an overreaching tool call:
the permission prompt. The Telegram bot removes it — it launches the CLI with
`--dangerously-skip-permissions` because nobody is at the keyboard to approve
anything — and two failures followed directly from that missing gate.

1. A plain "write this up" request turned into `find ~ -maxdepth 3 -name ...`
   while hunting for a vault that `REGISTRY.md` already named. The sweep walked
   into `~/Library/Reminders`, and macOS raised a privacy prompt attributed to
   `python3.11`, because TCC blames the responsible process — the bot — rather
   than the CLI it spawned.
2. Notes were written straight into `wiki/` without the note-writer contract,
   so the frontmatter did not match the schema the rest of the harness reads.

So this hook is that missing gate, and only that. It engages when
`STUDY_SURFACE` marks a prompt-less surface and stays silent everywhere else,
because on an interactive surface the prompt already does this job and a second
gate would only get in the user's way.

Why the knowledge root is read-only here
----------------------------------------
The first version of this guard let a prompt-less surface write into `vault/`
as long as the note satisfied the note-writer contract. A conforming
frontmatter block is not the same thing as a note worth keeping: the contract
is checkable, but whether a claim is verified, whether the note duplicates one
that already exists, and whether `index.md`, `log.md`, and `hot.md` moved with
it are judgment calls, and on this surface nobody was there to make them. So
the knowledge root is now closed to writing entirely and the surface answers
questions instead. `_workspace/` and the temp directory stay open because
reading is not free of side effects — the semantic index `vault-search` reads
lives there and refreshes itself as notes change.

Contract
--------
Reads a PreToolUse payload on stdin, prints nothing when the call is allowed,
and prints a deny decision when it is not. Exit status stays 0 either way: a
crashing guard must not look like a blocked tool.

Two CLIs, two dialects. Antigravity (`agy`, what the bot actually runs) sends
`toolCall.name` with PascalCase args and requires an explicit
`{"decision": "deny"}`; Claude Code sends `tool_name` with snake_case input and
takes `permissionDecision`. Silence means "not my business" in both — verified
against a live `agy` session, where a hook that printed nothing left the tool
call untouched.

Registration differs too, and neither is tracked here: Antigravity reads
`~/.gemini/config/hooks.json` (its project-local `.agents/hooks.json` was not
picked up by CLI 1.1.7), while Claude Code reads `.claude/settings.json`. The
`study-install` skill records how to register this script.

Limits
------
A shell tool cannot be fully constrained by pattern matching — `python3 -c
"open(...)"` writes a file without ever naming a redirect. The load-bearing
check is the path check on the file-writing tools, which is exact; the shell
patterns catch the specific sweeps and redirects observed above, not every
conceivable bypass.
"""

import json
import os
import re
import sys

# Surfaces that run with no human approving tool calls. Anything not listed
# here keeps its permission prompt and is left alone.
GUARDED_SURFACES = {"telegram"}

# Directories macOS protects with a TCC consent prompt. Touching one from a
# background process raises a dialog the user cannot connect to anything they
# asked for.
PROTECTED_SUBPATHS = (
    "Library/Reminders",
    "Library/Calendars",
    "Library/Mail",
    "Library/Messages",
    "Library/Safari",
    "Library/Cookies",
    "Library/Application Support/AddressBook",
    "Library/Application Support/CallHistoryDB",
    "Library/Application Support/com.apple.TCC",
    "Library/Photos",
    "Pictures/Photos Library",
)

# A recursive walker given the home directory itself. Bounded by `[^|;&]*` so a
# later command in the same line is judged on its own.
SWEEP_COMMAND = re.compile(r"(?:^|[|;&]|\$\()\s*(find|fd|du|mdfind)\b([^|;&)]*)")
HOME_ROOT = re.compile(r"(?:^|\s)(?:~|\$HOME|\$\{HOME\})/?(?=\s|$)|(?:^|\s)/Users/[^/\s]+/?(?=\s|$)")

# Shell writes. `&1`-style duplications and /dev targets are not file writes.
REDIRECT = re.compile(r">>?\s*([^\s;&|<>()]+)")
TEE_TARGET = re.compile(r"\btee\b\s+(?:-\S+\s+)*([^\s;&|<>()]+)")

# AppleScript reaching into a user-data app is the direct form of the same
# overreach the sweep caused by accident.
OSASCRIPT_APP = re.compile(
    r"tell\s+application\s+\"(Reminders|Calendar|Contacts|Notes|Mail|Messages|Photos)\"",
    re.IGNORECASE,
)


# Which CLI sent the payload. The two differ in every part of the contract
# except one: staying silent means "not my business" in both, which is what
# this guard does for the overwhelming majority of calls.
DIALECT_CLAUDE = "claude"
DIALECT_ANTIGRAVITY = "antigravity"


def emit_deny(reason, dialect):
    """Print a deny decision in the shape the calling CLI understands."""
    if dialect == DIALECT_ANTIGRAVITY:
        # Antigravity: decision is required and the vocabulary is
        # allow/deny/ask/force_ask. "block" is not a value it knows.
        payload = {"decision": "deny", "reason": reason}
    else:
        payload = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            },
            # The older Claude shape is still honored, and study-wrapup.sh
            # already relies on it for the Stop event.
            "decision": "block",
            "reason": reason,
        }
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")
    sys.exit(0)


def study_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def resolve(path, cwd):
    """Absolute, symlink-free form of a path that need not exist yet."""
    if not os.path.isabs(path):
        path = os.path.join(cwd, path)
    return os.path.realpath(path)


def is_within(path, parent):
    if not parent:
        return False
    parent = os.path.realpath(parent)
    return path == parent or path.startswith(parent + os.sep)


def writable_roots(root):
    """Where a prompt-less surface may write.

    Scratch space only. `_workspace/` holds the semantic index and any proposal
    the surface wants to leave behind, and the temp directory is where working
    files belong. Two places are deliberately absent: the knowledge root, which
    this surface reads and never changes, and the harness repository, because
    changing tracked harness files is metaskill's job and needs a human at the
    prompt.
    """
    roots = [os.path.realpath(os.path.join(root, "_workspace"))]
    for temp in ("/tmp", os.environ.get("TMPDIR", "")):
        if temp:
            roots.append(os.path.realpath(temp))
    return [r for r in roots if r]


def check_write(path_value, cwd, root, dialect):
    if not path_value:
        return
    resolved = resolve(path_value, cwd)
    if any(is_within(resolved, allowed) for allowed in writable_roots(root)):
        return

    vault = os.path.realpath(os.path.join(root, "vault"))
    if is_within(resolved, vault):
        emit_deny(
            "This surface is read-only: it answers from the knowledge base and does not change "
            "it. %s is inside the knowledge root. Whether a note is worth keeping, whether it "
            "duplicates one that exists, and whether index.md, log.md, and hot.md move with it "
            "are judgment calls that need a person at the prompt, so write it from an "
            "interactive session through the note-writer skill instead. Searching, reading, and "
            "explaining are all available here." % resolved,
            dialect,
        )

    emit_deny(
        "This surface runs without a permission prompt and is read-only apart from scratch "
        "space (_workspace/ and the temp directory). %s is outside both. Changes to the "
        "knowledge root or the harness repository need an interactive session." % resolved,
        dialect,
    )


def check_bash(command, cwd, root, dialect):
    if not command:
        return

    for protected in PROTECTED_SUBPATHS:
        if protected in command:
            emit_deny(
                "This command reads %s, which macOS protects behind a privacy consent prompt. "
                "On a background surface that dialog names the bot process and the user cannot "
                "connect it to anything they asked for. Study material lives in vault/; read "
                "REGISTRY.md for the knowledge root instead of searching the home directory."
                % protected,
                dialect,
            )

    if OSASCRIPT_APP.search(command):
        emit_deny(
            "This command drives a personal-data app through AppleScript, which is outside "
            "what a study surface does. Keep the work inside vault/.",
            dialect,
        )

    for match in SWEEP_COMMAND.finditer(command):
        if HOME_ROOT.search(match.group(2)):
            emit_deny(
                "This command walks the home directory itself, which crosses macOS-protected "
                "folders such as ~/Library/Reminders and raises a privacy prompt attributed to "
                "the bot process. The knowledge root is already recorded in REGISTRY.md and "
                "linked as vault/, so no search is needed to find it.",
                dialect,
            )

    roots = writable_roots(root)
    targets = [m.group(1) for m in REDIRECT.finditer(command)]
    targets += [m.group(1) for m in TEE_TARGET.finditer(command)]
    for target in targets:
        if target.startswith("&") or target.startswith("/dev/"):
            continue
        resolved = resolve(target, cwd)
        if not any(is_within(resolved, allowed) for allowed in roots):
            emit_deny(
                "This command writes to %s. This surface is read-only apart from scratch space "
                "(_workspace/ and the temp directory); the knowledge root is read here and "
                "changed from an interactive session." % resolved,
                dialect,
            )


def read_call(payload):
    """Normalize the two CLI payload shapes into (dialect, tool, args).

    Antigravity sends protojson camelCase — `toolCall.name` with PascalCase
    argument keys — while Claude Code sends `tool_name` with snake_case input.
    Everything downstream works on the normalized triple.
    """
    call = payload.get("toolCall")
    if isinstance(call, dict):
        args = call.get("args")
        return DIALECT_ANTIGRAVITY, call.get("name", ""), args if isinstance(args, dict) else {}

    args = payload.get("tool_input")
    return DIALECT_CLAUDE, payload.get("tool_name", ""), args if isinstance(args, dict) else {}


# Tool names that change a file, per CLI, mapped to the argument key holding
# the path. Only the path matters: a read-only surface is judged on where a
# call would land, never on what it would put there.
WRITE_TOOLS = {
    DIALECT_ANTIGRAVITY: {
        "write_to_file": "TargetFile",
        "create_file": "TargetFile",
        "file_change": "TargetFile",
        "edit_notebook": "TargetFile",
        "delete_file": "TargetFile",
        "delete_directory": "DirectoryPath",
    },
    DIALECT_CLAUDE: {
        "Write": "file_path",
        "Edit": "file_path",
        "MultiEdit": "file_path",
        "NotebookEdit": "notebook_path",
    },
}
SHELL_TOOLS = {
    DIALECT_ANTIGRAVITY: ("run_command", "CommandLine"),
    DIALECT_CLAUDE: ("Bash", "command"),
}


def main():
    if os.environ.get("STUDY_SURFACE", "").strip() not in GUARDED_SURFACES:
        return

    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        # A guard that cannot read its input must not block the session; the
        # permission-less surface is no worse off than before the hook existed.
        return
    if not isinstance(payload, dict):
        return

    dialect, tool, args = read_call(payload)
    root = study_root()

    shell_tool, command_key = SHELL_TOOLS[dialect]
    if tool == shell_tool:
        # Antigravity carries the shell's own working directory in the call.
        cwd = args.get("Cwd") or payload.get("cwd") or root
        check_bash(args.get(command_key, ""), cwd, root, dialect)
        return

    path_key = WRITE_TOOLS[dialect].get(tool)
    if path_key:
        check_write(args.get(path_key, ""), payload.get("cwd") or root, root, dialect)


if __name__ == "__main__":
    main()
