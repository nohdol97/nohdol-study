#!/usr/bin/env python3
"""Check that the understand-* adapters stay aligned with the pinned upstream.

An adapter that names an upstream skill which no longer exists would send the
agent to read a missing file and improvise from there, so the mapping is
verified rather than assumed. The upstream checkout is optional: when the pin
is not installed, the tests that need it are reported as skipped instead of
silently passing.
"""

from __future__ import annotations

from pathlib import Path
import sys


SKILLS = Path(__file__).resolve().parents[2]
STUDY_ROOT = SKILLS.parents[1]
UPSTREAM = (
    STUDY_ROOT
    / ".tools/understand-anything/understand-anything-plugin/skills"
)
CONTRACT = Path(__file__).with_name("adapter-contract.md")

ADAPTERS = [
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


check(CONTRACT.is_file(), "the shared adapter contract is missing")
contract_text = CONTRACT.read_text(encoding="utf-8") if CONTRACT.is_file() else ""

# The contract carries the boundaries every adapter depends on. Losing one of
# these silently would leave the adapters pointing at nothing.
for required in [
    "install-phase2b-tools.sh --check",
    "_workspace/understand-anything/",
    "not evidence",
    "loopback",
    "api.figma.com",
]:
    check(required in contract_text, f"the contract no longer states: {required}")

for name in ADAPTERS:
    skill = SKILLS / name / "SKILL.md"
    check(skill.is_file(), f"{name}: SKILL.md is missing")
    if not skill.is_file():
        continue
    text = skill.read_text(encoding="utf-8")
    check(
        "adapter-contract.md" in text,
        f"{name}: does not send the reader to the shared contract",
    )
    check(
        "Runtime tier" in text,
        f"{name}: does not state which runtime tier it needs",
    )

# No adapter may exist without an upstream skill behind it.
adapter_dirs = {
    path.name
    for path in SKILLS.iterdir()
    if path.is_dir() and path.name.startswith("understand")
}
check(
    adapter_dirs == set(ADAPTERS),
    f"adapter directories drifted from the expected set: {sorted(adapter_dirs)}",
)

if UPSTREAM.is_dir():
    upstream_skills = {path.name for path in UPSTREAM.iterdir() if path.is_dir()}
    missing = sorted(set(ADAPTERS) - upstream_skills)
    check(not missing, f"adapters name upstream skills that do not exist: {missing}")
    uncovered = sorted(upstream_skills - set(ADAPTERS))
    check(
        not uncovered,
        f"the pin ships upstream skills with no adapter: {uncovered}",
    )
    # The one adapter that runs without a dependency install must keep the
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

print(f"understand adapter tests: PASS ({upstream_state})")
