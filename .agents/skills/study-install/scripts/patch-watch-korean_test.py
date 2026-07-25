#!/usr/bin/env python3

from pathlib import Path
import subprocess
import sys
import tempfile


SCRIPT = Path(__file__).with_name("patch-watch-korean.py")


def run(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(path)],
        check=False,
        capture_output=True,
        text=True,
    )


with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    target = root / "download.py"
    target.write_text(
        'a = ["--sub-langs", "en.*"]\nb = ["--sub-langs", "en.*"]\n',
        encoding="utf-8",
    )

    first = run(target)
    assert first.returncode == 0, first.stderr
    assert target.read_text(encoding="utf-8").count('"ko.*,en.*"') == 2

    second = run(target)
    assert second.returncode == 0, second.stderr
    assert "already-patched" in second.stdout

    unexpected = root / "unexpected.py"
    unexpected.write_text('a = ["--sub-langs", "en.*"]\n', encoding="utf-8")
    failed = run(unexpected)
    assert failed.returncode != 0
    assert unexpected.read_text(encoding="utf-8").count('"en.*"') == 1

print("watch patch tests: PASS")
