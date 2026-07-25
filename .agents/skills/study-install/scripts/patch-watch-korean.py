#!/usr/bin/env python3
"""Patch claude-video's caption preference to Korean, then English."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


OLD = '"--sub-langs", "en.*"'
NEW = '"--sub-langs", "ko.*,en.*"'
EXPECTED_CALLS = 2


def patch(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    old_count = text.count(OLD)
    new_count = text.count(NEW)

    if old_count == 0 and new_count == EXPECTED_CALLS:
        return "already-patched"
    if old_count != EXPECTED_CALLS or new_count != 0:
        raise ValueError(
            f"unexpected upstream shape: old={old_count}, patched={new_count}; "
            "review download.py before changing it"
        )

    patched = text.replace(OLD, NEW)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(patched, encoding="utf-8")
    temporary.replace(path)
    return "patched"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("download_py", type=Path)
    args = parser.parse_args()

    if not args.download_py.is_file():
        print(f"watch patch: missing file: {args.download_py}", file=sys.stderr)
        return 2

    try:
        result = patch(args.download_py)
    except (OSError, ValueError) as exc:
        print(f"watch patch: {exc}", file=sys.stderr)
        return 1

    print(f"watch patch: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
