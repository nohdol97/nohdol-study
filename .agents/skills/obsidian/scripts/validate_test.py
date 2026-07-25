#!/usr/bin/env python3

from pathlib import Path
import subprocess
import sys
import tempfile


SCRIPT = Path(__file__).with_name("validate.py")


def run(*paths: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *(str(path) for path in paths)],
        check=False,
        capture_output=True,
        text=True,
    )


def write(root: Path, name: str, text: str) -> Path:
    path = root / name
    path.write_text(text, encoding="utf-8")
    return path


VALID_CANVAS = """{
  "nodes": [
    {"id": "6f0ad84f44ce9c17", "type": "text", "text": "Root", "x": 0, "y": 0,
     "width": 260, "height": 80},
    {"id": "9c17c9d2b4a1e330", "type": "file", "file": "wiki/note.md", "x": 400,
     "y": 0, "width": 260, "height": 80},
    {"id": "aa11bb22cc33dd44", "type": "group", "label": "Cluster", "x": -40,
     "y": -40, "width": 800, "height": 200}
  ],
  "edges": [
    {"id": "e1", "fromNode": "6f0ad84f44ce9c17", "toNode": "9c17c9d2b4a1e330",
     "fromSide": "right", "toSide": "left"}
  ]
}
"""

VALID_BASE = """filters:
  and:
    - 'status != "done"'
formulas:
  age: 'now() - file.ctime'
views:
  - type: table
    name: Open items
    order:
      - file.name
  - type: cards
    name: Gallery
"""

VALID_MARKDOWN = """---
type: concept
---
# Note

Links to [[Other Note]] and embeds ![[diagram.png]].
A heading link [[Other Note#Section]] and an alias [[Other Note|alias]].

> [!warning] Careful
> Body text.

> [!faq]- Folded
> Hidden.

```md
[[Unclosed example in a fence
> [!not-a-real-type]
```

Inline `[[Unclosed in code` stays out of it.
"""


with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)

    # Valid files of each kind pass together.
    canvas = write(root, "board.canvas", VALID_CANVAS)
    base = write(root, "items.base", VALID_BASE)
    markdown = write(root, "note.md", VALID_MARKDOWN)
    result = run(canvas, base, markdown)
    assert result.returncode == 0, result.stderr
    assert "3 file(s) valid" in result.stdout
    # The callout list should come from the pin when it is installed.
    pin = (
        Path(__file__).resolve().parents[4]
        / ".tools/obsidian-skills/skills/obsidian-markdown/references/CALLOUTS.md"
    )
    expected_source = "pinned reference" if pin.is_file() else "built-in list"
    assert expected_source in result.stdout, result.stdout

    # Canvas: an edge pointing at a node that does not exist.
    broken = write(
        root,
        "dangling.canvas",
        """{
  "nodes": [{"id": "a", "type": "text", "text": "x", "x": 0, "y": 0,
             "width": 10, "height": 10}],
  "edges": [{"id": "e", "fromNode": "a", "toNode": "ghost"}]
}
""",
    )
    result = run(broken)
    assert result.returncode == 1
    assert "toNode 'ghost' is not a node" in result.stderr

    # Canvas: duplicate node ids, a bad type, and non-integer geometry.
    result = run(
        write(
            root,
            "bad-nodes.canvas",
            """{
  "nodes": [
    {"id": "a", "type": "text", "text": "x", "x": 0, "y": 0, "width": 10,
     "height": 10},
    {"id": "a", "type": "sticky", "x": "0", "y": 0, "width": 10, "height": 10}
  ]
}
""",
        )
    )
    assert result.returncode == 1
    assert "duplicate id 'a'" in result.stderr
    assert "type must be one of" in result.stderr
    assert "x must be an integer" in result.stderr

    # Canvas: a file node without its file, and invalid JSON.
    result = run(
        write(
            root,
            "no-file.canvas",
            '{"nodes": [{"id": "a", "type": "file", "x": 0, "y": 0,'
            ' "width": 10, "height": 10}]}',
        )
    )
    assert result.returncode == 1
    assert "requires 'file'" in result.stderr

    result = run(write(root, "broken.canvas", "{not json"))
    assert result.returncode == 1
    assert "not valid JSON" in result.stderr

    # Base: missing views, a tab indent, an unknown top-level key, and a view
    # with no name.
    result = run(write(root, "no-views.base", "filters:\n  and: []\n"))
    assert result.returncode == 1
    assert "needs a 'views' section" in result.stderr

    result = run(write(root, "tabbed.base", "views:\n\t- type: table\n"))
    assert result.returncode == 1
    assert "indent with spaces" in result.stderr

    result = run(write(root, "unknown.base", "wibble:\n  a: b\nviews:\n  - type: table\n    name: X\n"))
    assert result.returncode == 1
    assert "unknown top-level key 'wibble'" in result.stderr

    result = run(write(root, "nameless.base", "views:\n  - type: table\n"))
    assert result.returncode == 1
    assert "missing 'name'" in result.stderr

    result = run(write(root, "empty.base", "\n\n"))
    assert result.returncode == 1
    assert "file is empty" in result.stderr

    # Markdown: an unclosed wikilink outside a fence is caught, and the same
    # shape inside a fence or inline code is not.
    result = run(write(root, "unclosed.md", "Text [[Note\n"))
    assert result.returncode == 1
    assert "not closed" in result.stderr

    result = run(write(root, "empty-link.md", "Text [[]] here\n"))
    assert result.returncode == 1
    assert "empty target" in result.stderr

    result = run(write(root, "embed.md", "![[]]\n"))
    assert result.returncode == 1
    assert "empty target" in result.stderr

    # Callouts: an unknown type and a missing type.
    result = run(write(root, "callout.md", "> [!definitely-not-real] Title\n> body\n"))
    assert result.returncode == 1
    assert "unknown callout type 'definitely-not-real'" in result.stderr

    result = run(write(root, "typeless.md", "> [!] Title\n"))
    assert result.returncode == 1
    assert "callout has no type" in result.stderr

    # An alias documented in the pinned reference is accepted.
    result = run(write(root, "alias.md", "> [!tldr] Summary\n> body\n"))
    assert result.returncode == 0, result.stderr

    # A directory or unsupported extension is reported, not silently skipped.
    result = run(root / "missing.md")
    assert result.returncode == 1
    assert "not a file" in result.stderr

    result = run(write(root, "note.txt", "text"))
    assert result.returncode == 1
    assert "unsupported file type" in result.stderr

print("obsidian validator tests: PASS")
