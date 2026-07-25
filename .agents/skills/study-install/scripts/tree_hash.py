#!/usr/bin/env python3
"""Deterministic content hash for an extracted third-party source tree.

A release archive is not a stable identity: the same commit can be
repackaged with different compression or timestamps, and a tarball digest
would then fail for a tree whose files never changed. This walks the
extracted tree instead and hashes what actually matters - the relative
path, the kind of entry, the executable bit, and the file bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import sys


def entries(root: Path) -> list[tuple[str, str]]:
    """Return sorted (relative path, record) pairs for every tracked entry."""
    collected: list[tuple[str, str]] = []
    for directory, subdirectories, filenames in os.walk(root, followlinks=False):
        # Sorting here only makes the walk predictable; the final sort below
        # is what guarantees the hash is order-independent.
        subdirectories.sort()
        for name in sorted(filenames) + sorted(subdirectories):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                collected.append((relative, f"link {os.readlink(path)}"))
            elif path.is_file():
                mode = "x" if os.access(path, os.X_OK) else "-"
                content = hashlib.sha256(path.read_bytes()).hexdigest()
                collected.append((relative, f"file {mode} {content}"))
    collected.sort()
    return collected


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for relative, record in entries(root):
        digest.update(f"{record}  {relative}\n".encode("utf-8"))
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument(
        "--expect",
        help="fail when the computed hash differs from this value",
    )
    args = parser.parse_args()

    if not args.root.is_dir():
        print(f"tree-hash: not a directory: {args.root}", file=sys.stderr)
        return 2

    computed = tree_hash(args.root)
    if args.expect and computed != args.expect:
        print(
            f"tree-hash: mismatch for {args.root}\n"
            f"  expected {args.expect}\n"
            f"  actual   {computed}",
            file=sys.stderr,
        )
        return 1
    print(computed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
