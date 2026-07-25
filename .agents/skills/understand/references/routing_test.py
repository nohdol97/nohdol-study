#!/usr/bin/env python3
"""Check that the single understand skill still routes to every pinned mode.

One skill covers nine upstream entry points, so nothing but this file connects
a mode name to the upstream workflow behind it. If a mode is dropped from the
routing table or the pin stops shipping one, the skill would quietly send the
agent to read a file that is not there and improvise from the gap.

The upstream checkout is optional: when the pin is not installed, the checks
that need it are reported as skipped rather than silently passing.
"""

from __future__ import annotations

from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
SKILLS = HERE.parents[1]
STUDY_ROOT = SKILLS.parents[1]
UPSTREAM = (
    STUDY_ROOT
    / ".tools/understand-anything/understand-anything-plugin/skills"
)
SKILL = SKILLS / "understand" / "SKILL.md"
CONTRACT = HERE / "adapter-contract.md"
MODES = HERE / "modes.md"

EXPECTED_MODES = [
    "understand",
    "understand-chat",
    "understand-dashboard",
    "understand-diff",
    "understand-domain",
    "understand-explain",
    "understand-figma",
    "understand-knowledge",
    "understand-onboard",
]

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


for path, label in [(SKILL, "SKILL.md"), (CONTRACT, "the contract"), (MODES, "modes.md")]:
    check(path.is_file(), f"{label} is missing")

skill_text = SKILL.read_text(encoding="utf-8") if SKILL.is_file() else ""
contract_text = CONTRACT.read_text(encoding="utf-8") if CONTRACT.is_file() else ""
modes_text = MODES.read_text(encoding="utf-8") if MODES.is_file() else ""

check(
    "references/adapter-contract.md" in skill_text,
    "the skill does not send the reader to the shared contract",
)
check(
    "references/modes.md" in skill_text,
    "the skill does not send the reader to the mode detail",
)

# The contract carries the boundaries every mode depends on.
for required in [
    "install-phase2b-tools.sh --check",
    "_workspace/understand-anything/",
    "not evidence",
    "loopback",
    "api.figma.com",
]:
    check(required in contract_text, f"the contract no longer states: {required}")

# Every mode must be routable from the skill and documented in the detail file.
for mode in EXPECTED_MODES:
    check(mode in skill_text, f"{mode}: not reachable from the routing table")
    check(f"## `{mode}`" in modes_text, f"{mode}: has no section in modes.md")

# Consolidating to one skill must not leave the old per-mode skills behind.
stray = sorted(
    path.name
    for path in SKILLS.iterdir()
    if path.is_dir() and path.name.startswith("understand-")
)
check(not stray, f"per-mode skill directories should be gone: {stray}")

if UPSTREAM.is_dir():
    upstream_skills = {path.name for path in UPSTREAM.iterdir() if path.is_dir()}
    missing = sorted(set(EXPECTED_MODES) - upstream_skills)
    check(not missing, f"modes name upstream skills that do not exist: {missing}")
    uncovered = sorted(upstream_skills - set(EXPECTED_MODES))
    check(not uncovered, f"the pin ships upstream skills with no mode: {uncovered}")
    # The one mode that runs without a dependency install must keep the
    # scripts it depends on.
    for script in ["parse-knowledge-base.py", "merge-knowledge-graph.py"]:
        check(
            (UPSTREAM / "understand-knowledge" / script).is_file(),
            f"understand-knowledge: the pinned {script} is gone",
        )
    upstream_state = "checked against the installed pin"
else:
    upstream_state = "skipped: the understand-anything pin is not installed"

if failures:
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    raise SystemExit(1)

print(f"understand routing tests: PASS ({upstream_state})")
