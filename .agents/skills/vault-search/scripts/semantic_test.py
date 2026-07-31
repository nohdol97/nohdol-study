#!/usr/bin/env python3
"""Regression tests for vault-search.

Run: python3 .agents/skills/vault-search/scripts/semantic_test.py

No embedding server is needed. What is pinned here is everything that decides
what gets embedded and what gets compared — chunking, normalization, drift
detection, and the loopback refusal. The embedding call itself is one HTTP
request whose behavior belongs to the server, and stubbing it would only test
the stub.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

SCRIPT = Path(__file__).resolve().with_name("semantic.py")

spec = importlib.util.spec_from_file_location("semantic", SCRIPT)
semantic = importlib.util.module_from_spec(spec)
spec.loader.exec_module(semantic)

failures: list[str] = []


def check(name: str, got, want) -> None:
    if got == want:
        print(f"  ok   {name}")
        return
    failures.append(name)
    print(f"  FAIL {name}\n       got={got!r}\n       want={want!r}")


def note(wiki: Path, name: str, text: str) -> Path:
    path = wiki / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="vault-search."))
    vault = root / "knowledge"
    wiki = vault / "wiki"
    wiki.mkdir(parents=True)

    print("keeps notes on this machine")
    for endpoint in ("https://api.openai.com", "http://10.0.0.5:11434", "http://evil.test"):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "status", "--vault", str(vault), "--endpoint", endpoint],
            capture_output=True, text=True,
        )
        # `status` reads no server, so a refusal here would be theatre; the
        # refusal that matters is on the commands that would transmit text.
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "query", "--vault", str(vault), "x", "--endpoint", endpoint],
            capture_output=True, text=True,
        )
        check(f"{endpoint} is refused", result.returncode, 2)
        check(f"{endpoint} refusal says why", "not loopback" in result.stderr, True)

    for endpoint in ("http://127.0.0.1:11434", "http://localhost:11434"):
        try:
            semantic.check_loopback(endpoint)
            allowed = True
        except SystemExit:
            allowed = False
        check(f"{endpoint} is allowed", allowed, True)

    print("\nchunks by section, carrying the heading")
    body = "---\ntype: concept\n---\n\n# 제목\n\n첫 문단이다.\n\n## 열린 질문\n\n아직 모르는 것.\n"
    path = note(wiki, "샘플", body)
    chunks = semantic.chunks_of(path, wiki)
    check("frontmatter is not embedded", any("type: concept" in c["text"] for c in chunks), False)
    check("a section becomes a chunk", len(chunks), 2)
    check("the heading travels with the text", "열린 질문" in chunks[1]["text"], True)
    check("the note path is recorded", chunks[0]["note"], "샘플.md")

    long_note = note(wiki, "긴 노트", "# 긴 노트\n\n" + ("가나다라마바사아자차 " * 400))
    long_chunks = semantic.chunks_of(long_note, wiki)
    check("a long section is split", len(long_chunks) > 1, True)
    # Overlap exists so a sentence on a boundary stays findable from both sides.
    check(
        "consecutive chunks overlap",
        long_chunks[0]["text"][-60:] in long_chunks[1]["text"],
        True,
    )

    print("\nnormalizes so a dot product is a cosine")
    unit = semantic.normalize([3.0, 4.0])
    check("unit length", round(sum(v * v for v in unit), 6), 1.0)
    check("zero vector survives", semantic.normalize([0.0, 0.0]), [0.0, 0.0])

    print("\nnotices drift without a server")
    index = {"notes": {"샘플.md": semantic.note_hash(path), "사라진 노트.md": "deadbeef"}}
    changed, removed = semantic.drift(vault, index)
    check("an unchanged note is not reported", "샘플.md" in changed, False)
    check("a deleted note is reported", removed, ["사라진 노트.md"])
    check("a new note is reported", "긴 노트.md" in changed, True)

    path.write_text(body + "\n한 줄 더.\n", encoding="utf-8")
    changed, _ = semantic.drift(vault, index)
    check("an edited note is reported", "샘플.md" in changed, True)

    print("\nreports rather than guesses")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "status", "--vault", str(vault)],
        capture_output=True, text=True,
    )
    check("status without an index is not an error", result.returncode, 0)
    check("status says there is no index", "no index yet" in result.stdout, True)

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "query", "--vault", str(vault), "무엇이든"],
        capture_output=True, text=True,
    )
    check("query without an index exits 2", result.returncode, 2)
    check("query names the build command", "build --vault" in result.stderr, True)

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "build", "--vault", str(root / "없음")],
        capture_output=True, text=True,
    )
    check("a missing wiki exits 2", result.returncode, 2)

    print("\nkeeps the index out of the synced knowledge root")
    index_path, vectors_path = semantic.store_paths(vault)
    check("index sits under _workspace", "_workspace" in index_path.parts, True)
    check("index is outside the vault", "knowledge" in index_path.parts, False)
    check("vectors sit beside the index", vectors_path.parent, index_path.parent)

    print()
    if failures:
        print(f"{len(failures)} failure(s): {', '.join(failures)}")
        return 1
    print("all vault-search tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
