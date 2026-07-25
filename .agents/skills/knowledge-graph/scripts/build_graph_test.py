#!/usr/bin/env python3

import json
from pathlib import Path
import subprocess
import sys
import tempfile


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

print("knowledge graph tests: PASS")
