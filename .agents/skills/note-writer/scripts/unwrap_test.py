#!/usr/bin/env python3
"""Regression tests for unwrap.

Run: python3 .agents/skills/note-writer/scripts/unwrap_test.py

This script rewrites notes in place with --write, so the failure that matters
is not "a paragraph stayed wrapped" but "a line break that WAS structure got
joined." Every construct whose meaning lives in the newline is pinned here:
joining one of them silently corrupts a note, and the note still looks
plausible afterwards.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile

SCRIPT = Path(__file__).resolve().with_name("unwrap.py")

spec = importlib.util.spec_from_file_location("unwrap_mod", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

failures: list[str] = []


def check(name: str, got, want) -> None:
    if got == want:
        print(f"  ok   {name}")
        return
    failures.append(name)
    print(f"  FAIL {name}\n       got={got!r}\n       want={want!r}")


def joined(text: str) -> str:
    """unwrap() returns (text, count); the tests care about the text."""
    result = mod.unwrap(text)
    return result[0] if isinstance(result, tuple) else result


def unchanged(name: str, text: str) -> None:
    check(name, joined(text), text)


def main() -> int:
    print("joins what carries no meaning")
    check(
        "a wrapped paragraph becomes one line",
        joined("한 문단인데\n두 줄로 접혀 있다.\n"),
        "한 문단인데 두 줄로 접혀 있다.\n",
    )
    check(
        "a blank line still separates paragraphs",
        joined("첫 문단\n이어짐.\n\n둘째 문단\n이어짐.\n"),
        "첫 문단 이어짐.\n\n둘째 문단 이어짐.\n",
    )

    print("\nleaves the newline alone where it is the structure")
    unchanged("frontmatter", "---\ntype: concept\nstatus: seed\n---\n\n본문\n")
    unchanged("fenced code", "```python\nx = 1\ny = 2\n```\n")
    unchanged("tilde fence", "~~~\na\nb\n~~~\n")
    unchanged("a table", "| 가 | 나 |\n|---|---|\n| 1 | 2 |\n")
    unchanged("headings", "# 제목\n\n## 소제목\n")
    unchanged("list items", "- 첫째\n- 둘째\n- 셋째\n")
    unchanged("numbered list", "1. 첫째\n2. 둘째\n")
    unchanged("thematic break", "본문\n\n---\n\n다음\n")
    unchanged("indented code", "    x = 1\n    y = 2\n")
    unchanged("footnote definitions", "[^1]: 첫 각주\n[^2]: 둘째 각주\n")

    # Two trailing spaces and a trailing backslash are the two ways Markdown
    # spells an explicit line break inside a paragraph. Joining either changes
    # what the reader sees, which is the one thing this script promises not to
    # do.
    check(
        "a two-space hard break survives",
        joined("첫 줄  \n둘째 줄\n"),
        "첫 줄  \n둘째 줄\n",
    )
    check(
        "a backslash hard break survives",
        joined("첫 줄\\\n둘째 줄\n"),
        "첫 줄\\\n둘째 줄\n",
    )

    # A paragraph line immediately before a list must not swallow the list.
    check(
        "prose before a list keeps its break",
        joined("다음과 같다:\n- 첫째\n"),
        "다음과 같다:\n- 첫째\n",
    )

    print("\nreports before it writes")
    root = Path(tempfile.mkdtemp(prefix="unwrap."))
    wiki = root / "wiki"
    wiki.mkdir(parents=True)
    note = wiki / "샘플.md"
    original = "# 샘플\n\n한 문단인데\n접혀 있다.\n"
    note.write_text(original, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--vault", str(root)],
        capture_output=True, text=True,
    )
    check("a report leaves the file alone", note.read_text(encoding="utf-8"), original)
    check("the report names the note", "샘플" in result.stdout, True)

    subprocess.run(
        [sys.executable, str(SCRIPT), "--vault", str(root), "--write"],
        capture_output=True, text=True,
    )
    check(
        "--write applies the join",
        note.read_text(encoding="utf-8"),
        "# 샘플\n\n한 문단인데 접혀 있다.\n",
    )

    second = subprocess.run(
        [sys.executable, str(SCRIPT), "--vault", str(root)],
        capture_output=True, text=True,
    )
    check("a second pass finds nothing", "샘플" in second.stdout, False)

    print()
    if failures:
        print(f"{len(failures)} failure(s): {', '.join(failures)}")
        return 1
    print("all unwrap tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
