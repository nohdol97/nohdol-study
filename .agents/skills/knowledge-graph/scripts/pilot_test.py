#!/usr/bin/env python3

from pathlib import Path
import subprocess
import sys
import tempfile


SCRIPT = Path(__file__).with_name("pilot.py")


def run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )


def build(root: Path) -> Path:
    corpus = root / "wiki"
    corpus.mkdir(parents=True)
    (corpus / "alpha.md").write_text(
        "---\ntype: concept\nstatus: seed\n---\n# Alpha\n\nSee [[Beta]].\n",
        encoding="utf-8",
    )
    (corpus / "beta.md").write_text(
        "---\ntype: concept\nstatus: seed\n---\n# Beta\n", encoding="utf-8"
    )
    return corpus


with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    corpus = build(root)

    # The baseline runs on its own and reports what it measured.
    result = run("--corpus", str(corpus))
    assert result.returncode == 0, result.stderr
    assert "Files measured: 2" in result.stdout, result.stdout
    assert "articles: 2" in result.stdout
    assert "unchanged: all 2 file(s)" in result.stdout
    assert "not run: no candidate command was given" in result.stdout
    # The temporary graph is not left in the vault.
    assert not (root / ".pilot-graph.json").exists()

    # A read-only candidate is timed and reported.
    reader = root / "reader.py"
    reader.write_text("print('two results')\n", encoding="utf-8")
    result = run(
        "--corpus", str(corpus),
        "--candidate", f"{sys.executable} {reader}",
        "--label", "stub index",
    )
    assert result.returncode == 0, result.stderr
    assert "## stub index" in result.stdout
    assert "result: exit 0" in result.stdout
    assert "two results" in result.stdout

    # A candidate that fails is reported without being hidden.
    failer = root / "failer.py"
    failer.write_text("raise SystemExit(3)\n", encoding="utf-8")
    result = run("--corpus", str(corpus), "--candidate", f"{sys.executable} {failer}")
    assert result.returncode == 0, result.stderr
    assert "result: exit 3" in result.stdout, result.stdout

    # A candidate that changes the corpus disqualifies itself, whatever it
    # reported. This is the invariant the pilot exists to enforce.
    writer = root / "writer.py"
    writer.write_text(
        "from pathlib import Path\n"
        f"path = Path({str(corpus / 'alpha.md')!r})\n"
        "path.write_text(path.read_text(encoding='utf-8') + 'appended\\n', encoding='utf-8')\n"
        "print('indexed 2 notes')\n",
        encoding="utf-8",
    )
    result = run(
        "--corpus", str(corpus),
        "--candidate", f"{sys.executable} {writer}",
    )
    assert result.returncode == 1, result.stdout
    assert "modified: alpha.md" in result.stdout
    assert "disqualified" in result.stdout

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    corpus = build(root)

    # A candidate that adds or removes a file is caught too.
    adder = root / "adder.py"
    adder.write_text(
        f"from pathlib import Path\nPath({str(corpus / 'new.md')!r}).write_text('# New\\n')\n",
        encoding="utf-8",
    )
    result = run("--corpus", str(corpus), "--candidate", f"{sys.executable} {adder}")
    assert result.returncode == 1
    assert "added: new.md" in result.stdout

    (corpus / "new.md").unlink()
    remover = root / "remover.py"
    remover.write_text(
        f"from pathlib import Path\nPath({str(corpus / 'beta.md')!r}).unlink()\n",
        encoding="utf-8",
    )
    result = run("--corpus", str(corpus), "--candidate", f"{sys.executable} {remover}")
    assert result.returncode == 1
    assert "removed: beta.md" in result.stdout

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    corpus = build(root)

    # A command that could write is refused before it runs, not judged after.
    for dangerous in [
        "basic-memory tool write-note --title x",
        "some-index format ./notes",
        "tool reset",
        "indexer sync --force",
    ]:
        result = run("--corpus", str(corpus), "--candidate", dangerous)
        assert result.returncode == 2, f"{dangerous}: {result.stdout}"
        assert "read-only" in result.stderr, result.stderr

    # Argument errors are reported rather than guessed around.
    result = run("--corpus", str(root / "absent"))
    assert result.returncode == 2
    assert "corpus directory not found" in result.stderr

    empty = root / "empty"
    empty.mkdir()
    result = run("--corpus", str(empty))
    assert result.returncode == 2
    assert "no Markdown files" in result.stderr

    result = run("--corpus", str(corpus), "--candidate", "'unclosed")
    assert result.returncode == 2
    assert "could not be parsed" in result.stderr

print("pilot tests: PASS")
