#!/usr/bin/env python3
"""Regression tests for study-note-check.

Run: python3 .agents/hooks/study-note-check_test.py

Two failure directions matter and both are pinned here. A miss puts a broken
note into the vault, which is the defect this hook exists to stop. A false
positive is worse in a different way: a hook that fires on ordinary writes
gets disabled, and then it stops catching anything. The scraper rewriting its
generated listings on every run is the exact case that trained an earlier
reminder away, so it is fixed as a passing case.

The real checkers are used, not stubs. What is being tested is that the hook
routes a written file to them and reports the result, and a stub would let a
wiring mistake through.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REAL_ROOT = HERE.parent.parent

failures: list[str] = []


def check(name: str, got, want) -> None:
    if got == want:
        print(f"  ok   {name}")
        return
    failures.append(name)
    print(f"  FAIL {name}\n       got={got!r}\n       want={want!r}")


def build_root() -> Path:
    """Build a temp harness whose vault is a symlink, as in a real install."""
    base = Path(tempfile.mkdtemp(prefix="study-note-check."))
    root = base / "harness"
    (root / ".agents" / "hooks").mkdir(parents=True)
    (root / "knowledge" / "wiki").mkdir(parents=True)
    (root / "knowledge" / "raw").mkdir(parents=True)
    # The knowledge root is reached through a symlink on every real
    # installation, which is what makes path comparison in the hook nontrivial.
    (root / "vault").symlink_to(root / "knowledge")
    shutil.copy(HERE / "study-note-check.py", root / ".agents" / "hooks" / "study-note-check.py")
    # The checkers themselves are shared, so the temp root borrows the real
    # ones rather than copying a snapshot that could drift from them.
    (root / ".agents" / "skills").symlink_to(REAL_ROOT / ".agents" / "skills")
    return root


def run(root: Path, path: Path, tool: str = "Write") -> tuple[int, str]:
    payload = {"tool_name": tool, "tool_input": {"file_path": str(path)}, "cwd": str(root)}
    result = subprocess.run(
        [sys.executable, str(root / ".agents" / "hooks" / "study-note-check.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stderr


def note(root: Path, name: str, frontmatter: str, body: str = "본문") -> Path:
    path = root / "knowledge" / "wiki" / f"{name}.md"
    path.write_text(f"---\n{frontmatter}\n---\n\n# {name}\n\n{body}\n", encoding="utf-8")
    return path


GOOD = "\n".join(
    [
        "type: concept",
        "status: seed",
        "created: 2026-07-31",
        "updated: 2026-07-31",
        "related: []",
        "sources: []",
        "verification: unverified",
        "checked: 2026-07-31",
    ]
)


def main() -> int:
    root = build_root()

    print("passes cleanly")
    code, _ = run(root, note(root, "정상", GOOD))
    check("a contract-clean note is silent", code, 0)

    good_mermaid = "```mermaid\nflowchart TD\n  A[시작] --> B[끝]\n```"
    code, _ = run(root, note(root, "정상 다이어그램", GOOD, good_mermaid))
    check("a valid mermaid block passes", code, 0)

    print("\ncatches what only shows up in Obsidian")
    broken_label = "```mermaid\nflowchart TD\n  A[1. 첫 단계] --> B[끝]\n```"
    code, err = run(root, note(root, "깨진 라벨", GOOD, broken_label))
    check("an ordered-list label is caught", code, 2)
    check("the label finding names markdown", "markdown" in err.lower(), True)

    code, err = run(root, note(root, "필드 누락", "type: concept\nstatus: seed"))
    check("missing contract fields are caught", code, 2)
    check("the missing field is named", "'created'" in err, True)

    code, err = run(root, note(root, "잘못된 상태", GOOD.replace("status: seed", "status: 완성")))
    check("an unknown status is caught", code, 2)

    print("\ncatches source anchors that do not resolve")
    code, err = run(root, note(root, "없는 출처", GOOD.replace("sources: []", "sources:\n  - raw/없는파일.md")))
    check("an unresolvable source path is caught", code, 2)
    check("the finding names the path", "raw/없는파일.md" in err, True)

    (root / "knowledge" / "raw" / "있는파일.md").write_text("원문", encoding="utf-8")
    code, _ = run(root, note(root, "있는 출처", GOOD.replace("sources: []", "sources:\n  - raw/있는파일.md")))
    check("a resolvable source path passes", code, 0)

    code, _ = run(root, note(root, "URL 출처", GOOD.replace("sources: []", "sources:\n  - https://example.org/a")))
    check("a URL source is not treated as a path", code, 0)

    # `_workspace/` is git-ignored and sits outside the knowledge root, so a
    # citation into it names a file nothing preserves. Eleven notes in the real
    # vault did exactly this.
    code, err = run(root, note(root, "워크스페이스 출처", GOOD.replace("sources: []", "sources:\n  - _workspace/x/run.py")))
    check("a _workspace citation is caught", code, 2)
    check("the finding points at raw/", "raw/" in err, True)

    print("\nstays out of the way")
    generated = "type: index\nstatus: seed\ncreated: 2026-07-31\nupdated: 2026-07-31"
    code, _ = run(root, note(root, "생성된 목록", generated, broken_label))
    check("a generated listing is skipped", code, 0)

    outside = root / "_workspace" / "메모.md"
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_text("---\ntype: x\n---\n\n" + broken_label, encoding="utf-8")
    code, _ = run(root, outside)
    check("a file outside the vault is ignored", code, 0)

    code, _ = run(root, note(root, "배시 무관", GOOD), tool="Bash")
    check("a non-write tool is ignored", code, 0)

    missing = root / "knowledge" / "wiki" / "없는노트.md"
    code, _ = run(root, missing)
    check("a path that is not a file is ignored", code, 0)

    # index.md and log.md are navigation records with their own shapes; the
    # note contract is not written for them, but a diagram in one still has to
    # render.
    index = root / "knowledge" / "index.md"
    index.write_text("# index\n\n" + broken_label, encoding="utf-8")
    code, err = run(root, index)
    check("index.md is diagram-checked", code, 2)
    check("index.md is not contract-checked", "missing frontmatter field" not in err, True)

    shutil.rmtree(root.parent, ignore_errors=True)

    print()
    if failures:
        print(f"{len(failures)} failure(s): {', '.join(failures)}")
        return 1
    print("all study-note-check tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
