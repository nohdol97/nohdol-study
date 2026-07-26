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

    # A parenthesis inside an unquoted label is balanced, so the delimiter
    # count above cannot see it, but Mermaid refuses to parse the diagram.
    # These cases were confirmed against Mermaid's own parser.
    result = run(str(write(root, "paren-label.md", "```mermaid\nflowchart LR\n  A[Span 1 (25ms)] --> B[ok]\n```\n")))
    assert result.returncode == 1
    assert "unquoted label 'Span 1 (25ms' holds a parenthesis" in result.stderr, result.stderr

    result = run(str(write(root, "paren-quoted.md", '```mermaid\nflowchart LR\n  A["Span 1 (25ms)"] --> B[ok]\n```\n')))
    assert result.returncode == 0, result.stderr

    # The shapes that stack delimiters are not labels holding a parenthesis.
    for shape in ["A[(store)]", "A((circle))", "A[[Some Note]]", "A{{hex}}"]:
        result = run(str(write(root, f"shape-{shape[1:3]}.md", f"```mermaid\nflowchart LR\n  {shape} --> B[ok]\n```\n")))
        assert result.returncode == 0, f"{shape}: {result.stderr}"

    # An edge label follows the same rule.
    result = run(str(write(root, "paren-edge.md", "```mermaid\nflowchart LR\n  A -->|Repl (a/b)| B\n```\n")))
    assert result.returncode == 1
    assert "unquoted label 'Repl (a/b)' holds a parenthesis" in result.stderr, result.stderr

    result = run(str(write(root, "paren-edge-ok.md", '```mermaid\nflowchart LR\n  A -->|"Repl (a/b)"| B\n```\n')))
    assert result.returncode == 0, result.stderr

    # So does a subgraph title, which has no brackets to make the rule obvious.
    result = run(str(write(root, "paren-subgraph.md", "```mermaid\nflowchart LR\n  subgraph Ray AIR (Runtime)\n    A[x]\n  end\n```\n")))
    assert result.returncode == 1
    assert "subgraph title holds a parenthesis" in result.stderr

    result = run(str(write(root, "paren-subgraph-ok.md", '```mermaid\nflowchart LR\n  subgraph RAY["Ray AIR (Runtime)"]\n    A[x]\n  end\n```\n')))
    assert result.returncode == 0, result.stderr

    # A double quote inside an unquoted label ends the statement too.
    result = run(str(write(root, "quote-label.md", '```mermaid\nflowchart LR\n  A[say "hi"] --> B[ok]\n```\n')))
    assert result.returncode == 1
    assert "holds a double quote" in result.stderr

    # Characters Mermaid does accept unquoted must not be reported. Each of
    # these parses; flagging them would push notes toward pointless quoting.
    for label in ["Security & Guard", "req #1029", "100% dup", "cost $0.0012",
                  "Span 1: input", "a/b", "a + b", "a<br>b", "a, b", "TTFT 410ms"]:
        result = run(str(write(root, "safe.md", f"```mermaid\nflowchart LR\n  A[{label}] --> B[ok]\n```\n")))
        assert result.returncode == 0, f"{label}: {result.stderr}"

    # A subgraph title needs no quotes for a space, an ampersand, a number, or
    # Korean text - only for a parenthesis.
    for title in ["Client Layer", "Security & Guard Layer", "4 · App Layer", "클라이언트 계층"]:
        result = run(str(write(root, "safe-sub.md", f"```mermaid\nflowchart LR\n  subgraph {title}\n    A[x]\n  end\n```\n")))
        assert result.returncode == 0, f"{title}: {result.stderr}"

    # A label Mermaid parses but cannot render as markdown. Quoting does not
    # help: the label text is handed to a markdown lexer either way, and the
    # reader gets "Unsupported markdown: list" where the label should be.
    # Every case here was confirmed against Obsidian's bundled markdown handler.
    for label, kind in [("1. 루프 & 하네스", "list"), ("1) 루프", "list"),
                        ("01. 루프", "list"), ("- 항목", "list"),
                        ("* 항목", "list"), ("+ 항목", "list"),
                        ("# 제목", "heading"), ("> 인용", "blockquote"),
                        ("2026. 07. 26 기준", "list")]:
        result = run(str(write(root, "md-label.md", f'```mermaid\nflowchart LR\n  A["{label}"] --> B[ok]\n```\n')))
        assert result.returncode == 1, f"{label}: {result.stdout}"
        assert f'"Unsupported markdown: {kind}"' in result.stderr, f"{label}: {result.stderr}"

    # Written without quotes the label still fails, whichever rule sees it first.
    result = run(str(write(root, "md-label-bare.md", "```mermaid\nflowchart LR\n  A[1. 루프] --> B[ok]\n```\n")))
    assert result.returncode == 1
    assert "Unsupported markdown: list" in result.stderr, result.stderr

    # An edge label and a subgraph title go through the same renderer.
    result = run(str(write(root, "md-edge.md", '```mermaid\nflowchart LR\n  A -->|"1. 전달"| B\n```\n')))
    assert result.returncode == 1
    assert "Unsupported markdown: list" in result.stderr, result.stderr

    result = run(str(write(root, "md-sub.md", '```mermaid\nflowchart LR\n  subgraph L1["1. Hardware Layer"]\n    A[x]\n  end\n```\n')))
    assert result.returncode == 1
    assert "Unsupported markdown: list" in result.stderr, result.stderr

    result = run(str(write(root, "md-sub-bare.md", "```mermaid\nflowchart LR\n  subgraph 1. Hardware Layer\n    A[x]\n  end\n```\n")))
    assert result.returncode == 1
    assert "Unsupported markdown: list" in result.stderr, result.stderr

    # A line after <br/> starts a markdown block in the SVG-label renderer.
    result = run(str(write(root, "md-break.md", '```mermaid\nflowchart LR\n  A["제목<br/>- 항목"] --> B[ok]\n```\n')))
    assert result.returncode == 1
    assert "Unsupported markdown: list" in result.stderr, result.stderr

    # A markdown label treats \n as two characters, not a line break.
    result = run(str(write(root, "md-newline.md", '```mermaid\nflowchart LR\n  A["창발성\\n임계점 돌파"] --> B[ok]\n```\n')))
    assert result.returncode == 1
    assert "holds a literal \\n" in result.stderr, result.stderr

    result = run(str(write(root, "md-newline-ok.md", '```mermaid\nflowchart LR\n  A["창발성<br/>임계점 돌파"] --> B[ok]\n```\n')))
    assert result.returncode == 0, result.stderr

    # Text that carries no markdown meaning must not be reported: a numbered
    # label written the safe way, a decimal, a leading arrow, a bare hyphen, a
    # heading mark inside the text, and an underscore in an identifier.
    for label in ["1 · 루프", "① 루프", "STEP 1: 루프", "3.5B 파라미터", "-1 오프셋",
                  "->  다음 단계", "req #1029 검토", "a_b_c 식별자",
                  "가중치 2 * 3", "구간 A - B"]:
        result = run(str(write(root, "md-safe.md", f'```mermaid\nflowchart LR\n  A["{label}"] --> B[ok]\n```\n')))
        assert result.returncode == 0, f"{label}: {result.stderr}"

    # A style or click line carries strings that are never rendered as a label.
    for statement in ['click A "https://example.com/a-b" _blank', "style A fill:#f9f"]:
        result = run(str(write(root, "md-nonlabel.md", f"```mermaid\nflowchart LR\n  A[x] --> B[y]\n  {statement}\n```\n")))
        assert result.returncode == 0, f"{statement}: {result.stderr}"

    # The markdown rules belong to the node-shaped types. A sequenceDiagram
    # message is drawn by a different code path that keeps \n as a line break.
    result = run(str(write(root, "md-seq.md", "```mermaid\nsequenceDiagram\n  A->>B: 1. 준비\\n2. 실행\n```\n")))
    assert result.returncode == 0, result.stderr

    # A sequenceDiagram takes a parenthesis unquoted, so the rule must not
    # reach it.
    result = run(
        str(
            write(
                root,
                "seq-paren.md",
                "```mermaid\nsequenceDiagram\n  participant K as Kubeflow (CT)\n  K->>K: step (detail)\n```\n",
            )
        )
    )
    assert result.returncode == 0, result.stderr

    # A subgraph title is not a node id: referencing it reads well and does not
    # parse.
    result = run(
        str(
            write(
                root,
                "spaced-id.md",
                "```mermaid\nflowchart LR\n  subgraph One Layer\n    A[x]\n  end\n"
                "  subgraph Two Layer\n    B[y]\n  end\n  One Layer --> Two Layer\n```\n",
            )
        )
    )
    assert result.returncode == 1
    assert "uses a node id containing a space" in result.stderr

    # Link forms that do parse must survive that rule: chained edges, labelled
    # edges, an ampersand node list, and a link carrying its own text.
    for statement in ["A[x] --> B[y] --> C[z]", "A -->|route| B", "A & B --> C",
                      "A -. 할인 .-> B", "A == weight ==> B", "A -- note --> B", "A <--> B",
                      "A --- B", "A -.-> B", "A[x]:::cls --> B"]:
        result = run(str(write(root, "safe-link.md", f"```mermaid\nflowchart LR\n  {statement}\n```\n")))
        assert result.returncode == 0, f"{statement}: {result.stderr}"

    # Declaration lines hold two words legitimately and are not edges.
    for statement in ["direction TB", "style A fill:#f9f", "classDef cls fill:#eee",
                      "class A cls", "linkStyle 0 stroke:#333"]:
        result = run(str(write(root, "safe-decl.md", f"```mermaid\nflowchart LR\n  A[x] --> B[y]\n  {statement}\n```\n")))
        assert result.returncode == 0, f"{statement}: {result.stderr}"

    # A subgraph left unclosed - a mistyped end reads as an ordinary line and
    # the diagram fails far from where it was written.
    result = run(
        str(
            write(
                root,
                "unclosed.md",
                "```mermaid\nflowchart LR\n  subgraph S\n    A[x]\n  </end\n```\n",
            )
        )
    )
    assert result.returncode == 1
    assert "1 subgraph and 0 end" in result.stderr

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
