#!/usr/bin/env python3

from pathlib import Path
import subprocess
import sys
import tempfile


SCRIPT = Path(__file__).with_name("check.py")


def run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def write(root: Path, name: str, text: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)

    # A small, well-formed diagram passes and is counted.
    good = write(
        root,
        "good.md",
        """# Note

```mermaid
flowchart LR
  A[Sensor] --> B{Decide}
  B -->|yes| C[Actuate]
  B -->|no| D[Ask a human]
```

```mermaid
sequenceDiagram
  Robot->>Human: may I proceed?
  Human-->>Robot: yes
```
""",
    )
    result = run(str(good))
    assert result.returncode == 0, result.stderr
    assert "2 mermaid block(s) checked" in result.stdout, result.stdout
    assert result.stderr == "", result.stderr

    # A non-mermaid fence is not a diagram and is left alone, including one
    # that would otherwise look unbalanced.
    result = run(
        str(
            write(
                root,
                "code.md",
                "```python\nvalue = data[0\n```\n\nText with `[[inline]]`.\n",
            )
        )
    )
    assert result.returncode == 0, result.stderr
    assert "0 mermaid block(s)" in result.stdout

    # An unknown diagram type is caught before it renders as an error block.
    result = run(str(write(root, "type.md", "```mermaid\nflowkart LR\n  A --> B\n```\n")))
    assert result.returncode == 1
    assert "unknown mermaid diagram type 'flowkart'" in result.stderr

    # Every bundled type is accepted.
    for kind in ["mindmap", "timeline", "erDiagram", "quadrantChart", "C4Context",
                 "architecture-beta", "kanban", "stateDiagram-v2"]:
        result = run(str(write(root, f"kind-{kind}.md", f"```mermaid\n{kind}\n```\n")))
        assert result.returncode == 0, f"{kind}: {result.stderr}"

    # Unbalanced delimiters are caught; a bracket inside a quoted label is not
    # mistaken for one.
    result = run(str(write(root, "unbalanced.md", "```mermaid\nflowchart LR\n  A[Sensor --> B[Act]\n```\n")))
    assert result.returncode == 1
    assert "unbalanced square bracket" in result.stderr

    result = run(
        str(
            write(
                root,
                "quoted.md",
                '```mermaid\nflowchart LR\n  A["a [bracket] inside"] --> B[Ok]\n```\n',
            )
        )
    )
    assert result.returncode == 0, result.stderr

    # An empty mermaid block is reported rather than silently counted.
    result = run(str(write(root, "empty.md", "```mermaid\n\n```\n")))
    assert result.returncode == 1
    assert "mermaid block is empty" in result.stderr

    # Node counting drives the escalation hint. Two nodes with wordy labels
    # must stay two: the labels here hold far more words than the threshold,
    # so counting them would trip the hint.
    small = write(
        root,
        "small.md",
        """```mermaid
flowchart LR
  A[One two three four five six seven eight nine ten eleven twelve] -->
    B[thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty]
```
""",
    )
    result = run(str(small))
    assert result.returncode == 0, result.stderr
    assert "render this one with D2" not in result.stderr, result.stderr

    nodes = "\n".join(f"  n{index} --> n{index + 1}" for index in range(1, 18))
    big = write(root, "big.md", f"```mermaid\ngraph TD\n{nodes}\n```\n")
    result = run(str(big))
    # The hint is advice, not a failure: the note still renders.
    assert result.returncode == 0, result.stderr
    assert "render this one with D2" in result.stderr
    assert "over the 15" in result.stderr

    # The threshold is adjustable, and raising it silences the hint.
    result = run("--max-nodes", "40", str(big))
    assert result.returncode == 0
    assert "render this one with D2" not in result.stderr

    # A missing embedded asset is caught, and one that exists is not.
    write(root, "assets/diagram.svg", "<svg><rect width='1' height='1'/></svg>")
    result = run(str(write(root, "embed-ok.md", "![[assets/diagram.svg]]\n")))
    assert result.returncode == 0, result.stderr

    result = run(str(write(root, "embed-missing.md", "![[assets/gone.svg]]\n")))
    assert result.returncode == 1
    assert "embedded asset not found: assets/gone.svg" in result.stderr

    # A wikilink to a note is not an asset reference.
    result = run(str(write(root, "note-link.md", "See [[Another Note]] and ![[Another Note]].\n")))
    assert result.returncode == 0, result.stderr

    # An SVG that a failed render left empty is caught.
    result = run(str(write(root, "empty.svg", "<svg xmlns='http://www.w3.org/2000/svg'></svg>")))
    assert result.returncode == 1
    assert "no drawable elements" in result.stderr

    result = run(str(write(root, "not.svg", "<html>nope</html>")))
    assert result.returncode == 1
    assert "does not contain an <svg> element" in result.stderr

    result = run(str(write(root, "real.svg", "<svg><path d='M0 0'/></svg>")))
    assert result.returncode == 0, result.stderr

    # Unsupported input is reported, not silently skipped.
    result = run(str(write(root, "notes.txt", "text")))
    assert result.returncode == 1
    assert "unsupported file type" in result.stderr

    result = run(str(root / "absent.md"))
    assert result.returncode == 1
    assert "not a file" in result.stderr

print("diagram check tests: PASS")
