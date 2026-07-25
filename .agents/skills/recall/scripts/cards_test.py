#!/usr/bin/env python3

from pathlib import Path
import subprocess
import sys
import tempfile


SCRIPT = Path(__file__).with_name("cards.py")


def run(wiki: Path, *files: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--wiki", str(wiki), *(str(f) for f in files)],
        check=False,
        capture_output=True,
        text=True,
    )


NOTE = """---
type: concept
status: mature
---
# Physical AI

## Safety

A physical mistake causes harm in the world, so testing under real conditions
matters more than it does for software.

## Feedback

The loop closes when the result is sensed again.
"""


with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    wiki = root / "wiki"
    wiki.mkdir()
    (wiki / "note.md").write_text(NOTE, encoding="utf-8")

    def write(name: str, text: str) -> Path:
        path = root / name
        path.write_text(text, encoding="utf-8")
        return path

    # Cards that resolve pass, including a heading anchor, a literal-phrase
    # anchor, and a card carrying review scheduling.
    good = write(
        "good.md",
        """# Cards — Physical AI

Why does a physical mistake matter more than a software one?
?
It causes harm in the world rather than a wrong screen.
<!-- from: note.md#Safety -->

What closes the loop?
?
Sensing the result again.
<!-- from: note.md#The loop closes when the result is sensed again --> <!--SR:!2026-08-01,3,270-->
""",
    )
    result = run(wiki, good)
    assert result.returncode == 0, result.stderr
    assert "2 card(s) traceable" in result.stdout, result.stdout

    # A card with no provenance cannot be re-examined and is refused.
    result = run(wiki, write("bare.md", "Question?\n?\nAnswer.\n"))
    assert result.returncode == 1
    assert "no provenance comment" in result.stderr

    # Provenance naming a note that is not in the wiki is refused.
    result = run(
        wiki,
        write("gone.md", "Q?\n?\nA.\n<!-- from: missing.md#Safety -->\n"),
    )
    assert result.returncode == 1
    assert "not in the wiki: missing.md" in result.stderr

    # An anchor that resolves nowhere is refused rather than accepted weakly:
    # this is the check that stops a card inventing what the note said.
    result = run(
        wiki,
        write("invented.md", "Q?\n?\nA.\n<!-- from: note.md#Nowhere In The Note -->\n"),
    )
    assert result.returncode == 1
    assert "anchor does not resolve" in result.stderr

    result = run(wiki, write("noanchor.md", "Q?\n?\nA.\n<!-- from: note.md -->\n"))
    assert result.returncode == 1
    assert "no anchor" in result.stderr

    # An empty side is refused; a card needs both halves.
    result = run(wiki, write("noanswer.md", "Q?\n?\n<!-- from: note.md#Safety -->\n"))
    assert result.returncode == 1
    assert "no answer" in result.stderr

    result = run(wiki, write("noquestion.md", "?\nA.\n<!-- from: note.md#Safety -->\n"))
    assert result.returncode == 1
    assert "no question" in result.stderr

    # A file with no cards is an error, not an empty success.
    result = run(wiki, write("empty.md", "# Just a heading\n"))
    assert result.returncode == 1
    assert "contains no cards" in result.stderr

    result = run(wiki, root / "absent.md")
    assert result.returncode == 1
    assert "not a file" in result.stderr

    # Frontmatter on the card file does not become a card.
    result = run(
        wiki,
        write(
            "withfm.md",
            """---
type: cards
status: developing
---
Q?
?
A.
<!-- from: note.md#Safety -->
""",
        ),
    )
    assert result.returncode == 0, result.stderr
    assert "1 card(s)" in result.stdout

    # A missing wiki directory is an argument error.
    result = run(root / "nowhere", good)
    assert result.returncode == 2
    assert "wiki directory not found" in result.stderr

print("recall card tests: PASS")
