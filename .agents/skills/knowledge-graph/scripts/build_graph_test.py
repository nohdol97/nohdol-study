#!/usr/bin/env python3

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unicodedata


SCRIPT = Path(__file__).with_name("build_graph.py")


def run(wiki: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--wiki", str(wiki), "--output", str(output)],
        check=False,
        capture_output=True,
        text=True,
    )


with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    wiki = root / "wiki"
    wiki.mkdir()
    (wiki / "alpha.md").write_text(
        """---
type: concept
status: seed
related:
  - "[[Beta]]"
---
# Alpha

See [[Beta|the second note]], [[Missing#Section]], and [[Beta]].

```md
[[Hidden]]
```
""",
        encoding="utf-8",
    )
    (wiki / "beta.md").write_text("# Beta\n", encoding="utf-8")
    (wiki / "orphan.md").write_text("# Orphan\n", encoding="utf-8")

    first = root / "first.json"
    second = root / "second.json"
    result = run(wiki, first)
    assert result.returncode == 0, result.stderr
    assert run(wiki, second).returncode == 0
    assert first.read_bytes() == second.read_bytes()

    graph = json.loads(first.read_text(encoding="utf-8"))
    assert graph["node_count"] == 3
    nodes = {node["title"]: node for node in graph["nodes"]}
    assert nodes["Alpha"]["links"] == ["Beta"]
    assert nodes["Alpha"]["missing_links"] == ["Missing"]
    assert nodes["Beta"]["backlinks"] == ["Alpha"]
    assert graph["missing_targets"] == [
        {"target": "Missing", "referenced_by": ["Alpha"]}
    ]
    assert graph["orphans"] == ["Orphan"]
    assert all(item["target"] != "Hidden" for item in graph["missing_targets"])
    assert nodes["Alpha"]["frontmatter"]["related"] == ["[[Beta]]"]

    (wiki / "duplicate.md").write_text("# beta\n", encoding="utf-8")
    duplicate = run(wiki, root / "duplicate.json")
    assert duplicate.returncode != 0
    assert "duplicate note title" in duplicate.stderr
    assert not (root / "duplicate.json").exists()

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    wiki = root / "wiki"
    (wiki / "nested").mkdir(parents=True)

    # Filename and H1 differ, so Obsidian resolves the filename while this
    # graph names the note by its heading. Both spellings must resolve.
    (wiki / "rt2-paper.md").write_text(
        "# Robotic Transformer 2\n", encoding="utf-8"
    )
    # A Korean filename stored decomposed, linked from a composed body.
    decomposed = unicodedata.normalize("NFD", "피지컬 AI")
    (wiki / f"{decomposed}.md").write_text("# 피지컬 AI 개요\n", encoding="utf-8")
    # One filename owned by two notes stays ambiguous instead of guessing.
    (wiki / "shared.md").write_text("# Shared One\n", encoding="utf-8")
    (wiki / "nested" / "shared.md").write_text("# Shared Two\n", encoding="utf-8")
    (wiki / "hub.md").write_text(
        """# Hub

Filename link [[rt2-paper]] and title link [[Robotic Transformer 2]].
Composed Korean link [[피지컬 AI]].
Case variants [[RT2-Paper]] and [[rt2-paper]] are one edge.
Ambiguous [[shared]] cannot resolve.

Inline `[[NotALink]]` is code, not a link.
""",
        encoding="utf-8",
    )

    output = root / "graph.json"
    result = run(wiki, output)
    assert result.returncode == 0, result.stderr
    graph = json.loads(output.read_text(encoding="utf-8"))
    nodes = {node["title"]: node for node in graph["nodes"]}

    assert nodes["Hub"]["links"] == ["Robotic Transformer 2", "피지컬 AI 개요"]
    assert nodes["Robotic Transformer 2"]["backlinks"] == ["Hub"]
    assert nodes["피지컬 AI 개요"]["backlinks"] == ["Hub"]
    assert nodes["Hub"]["missing_links"] == ["shared"]
    missing = {item["target"] for item in graph["missing_targets"]}
    assert missing == {"shared"}, missing
    assert "Shared One" in nodes and "Shared Two" in nodes

print("knowledge graph tests: PASS")
