#!/usr/bin/env python3
"""Regression tests for the ingest batch queue.

Run: python3 .agents/skills/ingest/scripts/queue_test.py
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unicodedata

SCRIPT = Path(__file__).resolve().with_name("queue.py")

failures: list[str] = []


def check(name: str, got, want) -> None:
    if got == want:
        print(f"  ok   {name}")
        return
    failures.append(name)
    print(f"  FAIL {name}\n       got={got!r}\n       want={want!r}")


def run(vault: Path, raw: str, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--vault", str(vault), "--raw", raw, *extra],
        capture_output=True,
        text=True,
    )


def build(root: Path) -> Path:
    vault = root / "knowledge"
    (vault / "wiki").mkdir(parents=True)
    (vault / "raw" / "batch").mkdir(parents=True)
    return vault


def note(vault: Path, title: str, sources: list[str]) -> None:
    lines = ["---", "type: concept", "status: seed", "created: 2026-07-31",
             "updated: 2026-07-31", "related: []", "sources:"]
    lines += [f"  - {source}" for source in sources]
    lines += ["verification: unverified", "---", "", f"# {title}", ""]
    (vault / "wiki" / f"{title}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="ingest-queue."))
    vault = build(root)
    batch = vault / "raw" / "batch"
    for name in ("a.md", "b.md", "c.md"):
        (batch / name).write_text("원문", encoding="utf-8")

    print("counts coverage from what the notes cite")
    result = run(vault, "raw/batch")
    check("nothing cited yet", "0/3" in result.stdout, True)
    check("waiting lists every file", result.stdout.count("- raw/batch/"), 3)

    note(vault, "첫 노트", ["raw/batch/a.md", "https://example.org/x"])
    result = run(vault, "raw/batch")
    check("a cited source is counted", "1/3" in result.stdout, True)
    check("a URL is not counted as a capture", "example.org" not in result.stdout, True)

    note(vault, "둘째 노트", ["raw/batch/b.md", "raw/batch/c.md"])
    result = run(vault, "raw/batch")
    check("all cited", "3/3" in result.stdout, True)
    check("nothing waiting", "Nothing waiting." in result.stdout, True)

    # macOS returns decomposed Unicode from the filesystem while a note is
    # written composed. Comparing the two as raw strings reported six cited
    # course files as uncited in the real vault.
    print("\nmatches across Unicode normalization forms")
    korean = (batch / unicodedata.normalize("NFD", "효율화.md"))
    korean.write_text("원문", encoding="utf-8")
    note(vault, "한글 노트", [unicodedata.normalize("NFC", "raw/batch/효율화.md")])
    result = run(vault, "raw/batch")
    check("a composed citation matches a decomposed filename", "4/4" in result.stdout, True)

    print("\nreports rather than guesses")
    result = run(vault, "raw/없는곳")
    check("a missing capture directory exits 2", result.returncode, 2)
    check("the error names the directory", "not found" in result.stderr, True)

    (vault / "raw" / "empty").mkdir()
    result = run(vault, "raw/empty")
    check("an empty capture directory is not an error", result.returncode, 0)

    result = run(vault, "raw/batch", "--ext", ".txt")
    check("an extension filter with no match is silent", "no files" in result.stdout, True)

    # A truncated list must say so. A batch that silently showed the first N
    # would read as "this is all of it" and leave the tail unworked.
    for index in range(5):
        (batch / f"extra{index}.md").write_text("원문", encoding="utf-8")
    result = run(vault, "raw/batch", "--limit", "2")
    check("the limit truncates the list", result.stdout.count("- raw/batch/"), 2)
    check("the truncation is stated", "3 more" in result.stdout, True)
    check("the total is still honest", "4/9" in result.stdout, True)

    print()
    if failures:
        print(f"{len(failures)} failure(s): {', '.join(failures)}")
        return 1
    print("all ingest queue tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
