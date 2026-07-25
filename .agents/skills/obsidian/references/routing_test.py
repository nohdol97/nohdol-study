#!/usr/bin/env python3
"""Check that the obsidian skill still routes to every pinned mode.

One skill covers four upstream file-format and CLI workflows, so nothing but
this connects a mode name to the upstream workflow behind it. A mode dropped
from the routing table, or one the pin stops shipping, would leave the agent
reading a path that is not there.

The upstream checkout is optional: when the pin is absent the checks that need
it are reported as skipped rather than silently passing.
"""

from __future__ import annotations

from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
SKILLS = HERE.parents[1]
STUDY_ROOT = SKILLS.parents[1]
UPSTREAM = STUDY_ROOT / ".tools/obsidian-skills/skills"
SKILL = SKILLS / "obsidian" / "SKILL.md"
MODES = HERE / "modes.md"

EXPECTED_MODES = [
    "json-canvas",
    "obsidian-bases",
    "obsidian-cli",
    "obsidian-markdown",
]
# Adopted deliberately against: this repository's own defuddle skill carries
# capture and evidence rules the upstream one lacks.
NOT_ADOPTED = ["defuddle"]

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


for path, label in [(SKILL, "SKILL.md"), (MODES, "modes.md")]:
    check(path.is_file(), f"{label} is missing")

skill_text = SKILL.read_text(encoding="utf-8") if SKILL.is_file() else ""
modes_text = MODES.read_text(encoding="utf-8") if MODES.is_file() else ""

check("references/modes.md" in skill_text, "the skill does not point at the mode detail")
check(
    "scripts/validate.py" in skill_text,
    "the skill does not require the files it writes to be validated",
)
for boundary in ["install-phase2b-tools.sh --check", "unavailable", "_workspace/"]:
    check(boundary in skill_text, f"the skill no longer states: {boundary}")

for mode in EXPECTED_MODES:
    check(mode in skill_text, f"{mode}: not reachable from the routing table")
    check(f"## `{mode}`" in modes_text, f"{mode}: has no section in modes.md")

for mode in NOT_ADOPTED:
    check(
        f"## `{mode}`" not in modes_text,
        f"{mode}: is documented as a mode but was deliberately not adopted",
    )

if UPSTREAM.is_dir():
    shipped = {path.name for path in UPSTREAM.iterdir() if path.is_dir()}
    missing = sorted(set(EXPECTED_MODES) - shipped)
    check(not missing, f"modes name upstream skills that do not exist: {missing}")
    unaccounted = sorted(shipped - set(EXPECTED_MODES) - set(NOT_ADOPTED))
    check(
        not unaccounted,
        f"the pin ships skills that are neither routed nor declined: {unaccounted}",
    )
    callouts = (
        UPSTREAM / "obsidian-markdown" / "references" / "CALLOUTS.md"
    )
    check(
        callouts.is_file(),
        "the pinned callout reference the validator reads is gone",
    )
    upstream_state = "checked against the installed pin"
else:
    upstream_state = "skipped: the obsidian-skills pin is not installed"

if failures:
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    raise SystemExit(1)

print(f"obsidian routing tests: PASS ({upstream_state})")
