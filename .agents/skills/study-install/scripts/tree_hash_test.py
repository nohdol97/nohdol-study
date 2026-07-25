#!/usr/bin/env python3

import os
from pathlib import Path
import subprocess
import sys
import tempfile


SCRIPT = Path(__file__).with_name("tree_hash.py")


def run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def make_tree(root: Path) -> None:
    (root / "nested").mkdir(parents=True)
    (root / "a.txt").write_text("alpha\n", encoding="utf-8")
    (root / "nested" / "b.txt").write_text("beta\n", encoding="utf-8")
    (root / "nested" / "run.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (root / "nested" / "run.sh").chmod(0o755)


with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    first = root / "first"
    second = root / "second"
    make_tree(first)
    make_tree(second)

    result = run(str(first))
    assert result.returncode == 0, result.stderr
    digest = result.stdout.strip()
    assert len(digest) == 64, digest

    # The same content in a different directory hashes the same.
    assert run(str(second)).stdout.strip() == digest

    # Repeating the walk is stable.
    assert run(str(first)).stdout.strip() == digest

    # --expect passes on a match and fails on a mismatch.
    assert run(str(first), "--expect", digest).returncode == 0
    mismatch = run(str(first), "--expect", "0" * 64)
    assert mismatch.returncode == 1
    assert "mismatch" in mismatch.stderr

    # Content, the executable bit, and file names each change the hash.
    (second / "nested" / "b.txt").write_text("changed\n", encoding="utf-8")
    assert run(str(second)).stdout.strip() != digest

    third = root / "third"
    make_tree(third)
    (third / "nested" / "run.sh").chmod(0o644)
    assert run(str(third)).stdout.strip() != digest

    fourth = root / "fourth"
    make_tree(fourth)
    (fourth / "a.txt").rename(fourth / "renamed.txt")
    assert run(str(fourth)).stdout.strip() != digest

    # A symlink is recorded by its target, not by following it.
    fifth = root / "fifth"
    make_tree(fifth)
    os.symlink("a.txt", fifth / "link.txt")
    with_link = run(str(fifth)).stdout.strip()
    assert with_link != digest

    sixth = root / "sixth"
    make_tree(sixth)
    os.symlink("nested/b.txt", sixth / "link.txt")
    assert run(str(sixth)).stdout.strip() != with_link

    # Build artifacts and dependency cache directories are ignored.
    seventh = root / "seventh"
    make_tree(seventh)
    (seventh / "node_modules").mkdir()
    (seventh / "node_modules" / "package.json").write_text("{}", encoding="utf-8")
    (seventh / "dist").mkdir()
    (seventh / "dist" / "bundle.js").write_text("console.log(1)", encoding="utf-8")
    (seventh / "test.tsbuildinfo").write_text("data", encoding="utf-8")
    (seventh / "debug.log").write_text("log", encoding="utf-8")
    assert run(str(seventh)).stdout.strip() == digest

    # A missing directory is an argument error, not a hash.
    assert run(str(root / "absent")).returncode == 2

print("tree hash tests: PASS")
