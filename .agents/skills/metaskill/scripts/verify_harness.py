#!/usr/bin/env python3
"""Verify nohdol-study harness navigation and skill integrity."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[4]
SKILLS = ROOT / ".agents" / "skills"


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def main() -> int:
    failures: list[str] = []
    skill_names: set[str] = set()

    for directory in sorted(path for path in SKILLS.iterdir() if path.is_dir()):
        skill_file = directory / "SKILL.md"
        if not skill_file.is_file():
            fail(f"skill directory lacks SKILL.md: {directory.name}", failures)
            continue
        skill_names.add(directory.name)
        text = skill_file.read_text(encoding="utf-8")
        lines = text.splitlines()
        if not lines or lines[0] != "---":
            fail(f"{directory.name}: frontmatter must start on line 1", failures)
            continue
        try:
            closing = lines[1:].index("---") + 1
        except ValueError:
            fail(f"{directory.name}: frontmatter closing marker missing", failures)
            continue
        frontmatter = lines[1:closing]
        name_lines = [line.removeprefix("name:").strip() for line in frontmatter if line.startswith("name:")]
        descriptions = [
            line.removeprefix("description:").strip()
            for line in frontmatter
            if line.startswith("description:")
        ]
        if name_lines != [directory.name]:
            fail(f"{directory.name}: frontmatter name mismatch", failures)
        if len(descriptions) != 1 or not descriptions[0]:
            fail(f"{directory.name}: exactly one description is required", failures)
        elif len(descriptions[0].encode("utf-8")) > 1024:
            fail(f"{directory.name}: description exceeds 1024 bytes", failures)
        if len(lines) > 500:
            fail(f"{directory.name}: SKILL.md exceeds 500 lines", failures)
        if "## With / without" not in text:
            fail(f"{directory.name}: With / without section missing", failures)

    summary = (SKILLS / "README.ko.md").read_text(encoding="utf-8")
    summary_names = set(re.findall(r"^## ([a-z0-9-]+)\s*$", summary, re.MULTILINE))
    if summary_names != skill_names:
        fail(
            "skill README headings differ: "
            f"missing={sorted(skill_names - summary_names)}, "
            f"extra={sorted(summary_names - skill_names)}",
            failures,
        )

    agents = (ROOT / "AGENTS.md").read_bytes()
    digest = hashlib.sha256(agents).hexdigest()
    korean = (ROOT / "AGENTS.ko.md").read_text(encoding="utf-8")
    match = re.search(r"source-sha256: ([0-9a-f]{64})", korean)
    if not match or match.group(1) != digest:
        fail("AGENTS.ko.md source hash is stale", failures)

    moc = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    for category in ("adr", "specs", "proposals"):
        for document in sorted((ROOT / "docs" / category).glob("*.md")):
            relative = f"{category}/{document.name}"
            if relative not in moc:
                fail(f"docs MOC missing {relative}", failures)

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for required in ("REGISTRY.md", "vault", "_workspace/"):
        if required not in gitignore:
            fail(f".gitignore missing {required}", failures)

    for link, expected in (
        (ROOT / ".claude" / "skills", "../.agents/skills"),
        (ROOT / ".claude" / "agents", "../.agents/agents"),
    ):
        if not link.is_symlink() or str(link.readlink()) != expected:
            fail(f"bad symlink: {link.relative_to(ROOT)}", failures)

    if failures:
        for item in failures:
            print(f"FAIL: {item}", file=sys.stderr)
        return 1
    print(f"harness verification: PASS ({len(skill_names)} skills)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
