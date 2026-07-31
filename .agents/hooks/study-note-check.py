#!/usr/bin/env python3
"""Check a curated note at the moment it is written.

Why this runs as a hook rather than as a step in a skill.

The checkers this calls are good — the Mermaid label check was cross-checked
against Obsidian's bundled renderer over 235 real labels with no false
positive and no miss. What they lacked was a caller. Every invocation was
prose in a SKILL.md ("run this before finishing"), and prose compliance is
probabilistic. Three separate sessions opened with the user reporting a broken
note they found in Obsidian: a Mermaid parse error, an `Unsupported markdown:
list` label, and inline formatting split across a line break. By then the file
was already written and synced, and diagnosing it cost a whole session each.

A hook removes the choice. The note is checked because it was written, not
because an agent remembered, which also covers writers that never went through
`note-writer` at all — the retired Telegram bot wrote notes that broke the
frontmatter contract precisely because it bypassed the skill.

Scope is deliberately narrow: only the file just written, and only the
questions answerable from that file. Reachability and backlinks need the whole
graph and stay in `vault-gardening` and the Stop hook, because building a
graph over a cloud-synced vault on every edit would make writing unusable.

Contract: exit 2 with findings on stderr asks the agent to fix them in the
same turn. Exit 1 reports that the check itself failed, which is a problem
with this hook and must not block the note. Exit 0 is silent.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


HOOKS_DIR = Path(__file__).resolve().parent
STUDY_ROOT = HOOKS_DIR.parent.parent
SKILLS = STUDY_ROOT / ".agents" / "skills"
GARDEN_SCRIPT = SKILLS / "vault-gardening" / "scripts" / "garden.py"
GRAPH_SCRIPT = SKILLS / "knowledge-graph" / "scripts" / "build_graph.py"
DIAGRAM_SCRIPT = SKILLS / "diagram" / "scripts" / "check.py"

# Generated listings are rewritten wholesale by the feed scraper on every run.
# They are not hand-authored knowledge and the note contract was never written
# for them, so checking them would fire on every automated run and train the
# reminder away — the same failure the Stop hook already had to correct.
GENERATED_TYPES = {"index", "moc"}
GENERATED_TAGS = {"feed", "daily-scrap"}


def load(script: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def written_path(payload: dict) -> Path | None:
    """Return the file a write-shaped tool call touched, if there is one."""
    if payload.get("tool_name") not in {"Write", "Edit", "MultiEdit", "NotebookEdit"}:
        return None
    raw = (payload.get("tool_input") or {}).get("file_path")
    if not raw:
        return None
    return Path(str(raw))


def is_generated(frontmatter: dict) -> bool:
    if str(frontmatter.get("type") or "") in GENERATED_TYPES:
        return True
    tags = frontmatter.get("tags")
    if isinstance(tags, list) and {str(tag) for tag in tags} & GENERATED_TAGS:
        return True
    return False


def check(path: Path) -> list[str]:
    """Return findings for one written note, or an empty list."""
    if path.suffix.lower() not in {".md", ".markdown"}:
        return []

    vault = STUDY_ROOT / "vault"
    if not vault.is_dir():
        return []
    # `vault` is a symlink into cloud storage, so both sides are resolved
    # before comparing. A tool call reports the path the agent used, which is
    # the symlink route, while `path.resolve()` yields the storage route.
    try:
        root = vault.resolve()
        target = path.resolve()
        relative = target.relative_to(root)
    except (OSError, ValueError):
        return []
    if not target.is_file():
        return []

    graph = load(GRAPH_SCRIPT, "study_build_graph")
    garden = load(GARDEN_SCRIPT, "study_garden")

    text = target.read_text(encoding="utf-8", errors="replace")
    frontmatter, _ = graph.split_frontmatter(text)
    if is_generated(frontmatter):
        return []

    label = str(relative)
    findings: list[str] = []

    # The note contract governs curated notes. `index.md`, `log.md`, and
    # `hot.md` are navigation records with their own shapes, so they are
    # checked for diagrams and source anchors but not against the contract.
    if relative.parts and relative.parts[0] == "wiki":
        findings.extend(garden.note_contract_findings(label, frontmatter))
    findings.extend(garden.source_anchor_findings(label, frontmatter, root))

    result = subprocess.run(
        [sys.executable, str(DIAGRAM_SCRIPT), str(target)],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        for line in result.stderr.splitlines():
            line = line.strip()
            # `check.py` prefixes advice and problems alike; only a non-zero
            # exit means something is actually broken, and the advice lines
            # explain it, so both are worth passing through.
            if line:
                findings.append(line.replace(str(target), label))

    return findings


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    path = written_path(payload)
    if path is None:
        return 0

    try:
        findings = check(path)
    except Exception as exc:  # noqa: BLE001 - a broken check must not block a write
        print(f"study-note-check: check failed: {exc}", file=sys.stderr)
        return 1

    if not findings:
        return 0

    print(
        "study-note-check: this note was saved with problems that do not show "
        "up in the source, only in Obsidian. Fix them now, in this turn.",
        file=sys.stderr,
    )
    for finding in findings:
        print(f"  - {finding}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
