#!/usr/bin/env python3
"""Semantic search over the curated notes, computed locally.

What this is, and what it is not.

It is a derived index. Every vector in it is reproducible from the Markdown by
rebuilding, nothing here is authoritative, and deleting the index loses no
knowledge. It answers "which notes are about this" when you do not know the
words the note used — the gap keyword search leaves.

It is not evidence. A result is a pointer with a similarity score, and a score
says two passages sit near each other in an embedding space, not that either
one is true. Open the note and read the passage before using it in an answer.
The same rule the knowledge graph carries applies here for the same reason.

Everything runs against a loopback embedding server. The vault holds career
material and private notes, so a non-loopback endpoint is refused outright
rather than left to configuration.

Usage:
  semantic.py build  --vault PATH [--endpoint URL] [--model NAME]
  semantic.py query  --vault PATH "질문" [--limit N]
  semantic.py status --vault PATH
"""

from __future__ import annotations

import argparse
import array
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_ENDPOINT = "http://127.0.0.1:11434"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1", "[::1]"}

# Preference order when no model is named. Multilingual first: these notes are
# Korean, and an English-centred model retrieves them badly enough to make the
# search not worth running — measured at 2 of 8 known-answer questions in the
# top ten, against a note the vault definitely contains.
PREFERRED_MODELS = ("bge-m3", "snowflake-arctic-embed2", "nomic-embed-text")

# nomic-embed-text trains at 2048 tokens. Korean runs roughly one token per
# character or worse, so the cap is set in characters well under that rather
# than guessing a token count. Overlap keeps a claim that straddles a boundary
# findable from either side.
CHUNK_CHARS = 900
CHUNK_OVERLAP = 150

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)


def fail(message: str) -> None:
    print(f"vault-search: {message}", file=sys.stderr)
    raise SystemExit(2)


def check_loopback(endpoint: str) -> None:
    host = urllib.parse.urlparse(endpoint).hostname or ""
    if host not in LOOPBACK_HOSTS:
        fail(
            f"endpoint {endpoint!r} is not loopback. This index is built from "
            "private notes and must not be sent to another host."
        )


def embed(texts: list[str], endpoint: str, model: str) -> list[list[float]]:
    request = urllib.request.Request(
        f"{endpoint.rstrip('/')}/api/embed",
        data=json.dumps({"model": model, "input": texts}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            payload = json.load(response)
    except urllib.error.URLError as exc:
        fail(
            f"embedding server unreachable at {endpoint} ({exc}). "
            "Start it with: launchctl kickstart gui/$(id -u)/com.nohdol.ollama"
        )
    vectors = payload.get("embeddings")
    if not isinstance(vectors, list) or len(vectors) != len(texts):
        fail(f"embedding server returned {len(vectors or [])} vectors for {len(texts)} inputs")
    return vectors


def installed_models(endpoint: str) -> list[str]:
    try:
        with urllib.request.urlopen(f"{endpoint.rstrip('/')}/api/tags", timeout=30) as response:
            payload = json.load(response)
    except (urllib.error.URLError, ValueError):
        return []
    return [str(item.get("name", "")).split(":")[0] for item in payload.get("models", [])]


def resolve_model(vault: Path, endpoint: str, requested: str | None) -> str:
    """Decide which model to embed with.

    Asking the server rather than hardcoding a default removes a mismatch that
    would otherwise be easy to hit: the installer sizes the model to the
    machine, so a fixed default here would name a model that was never pulled
    and fail at the first batch instead of at the first check.

    An existing index wins over preference, because vectors from two models are
    not comparable and silently switching would corrupt the index rather than
    improve it.
    """
    if requested:
        return requested
    index, _ = load_index(vault)
    if index.get("model"):
        return index["model"]
    available = installed_models(endpoint)
    for candidate in PREFERRED_MODELS:
        if candidate in available:
            return candidate
    fail(
        "no embedding model is installed. Run: "
        "sh .agents/skills/study-install/scripts/install-embedding.sh --install"
    )


def normalize(vector: list[float]) -> list[float]:
    """Scale to unit length so a dot product is the cosine similarity.

    Doing this once at build time turns every query into a plain dot product,
    which is what makes a pure-Python search over a few thousand chunks finish
    in well under a second without numpy.
    """
    length = math.sqrt(sum(value * value for value in vector))
    if length == 0:
        return vector
    return [value / length for value in vector]


def body_of(text: str) -> str:
    return FRONTMATTER.sub("", text, count=1)


def chunks_of(note: Path, wiki: Path) -> list[dict]:
    """Split one note into overlapping passages, each labelled by its heading.

    The heading travels with the passage into the embedding. A section called
    "열린 질문" under a note titled "P&T 22" means something the bare sentences
    under it do not, and a search for open questions should be able to find it.
    """
    text = note.read_text(encoding="utf-8", errors="replace")
    title = note.stem
    body = body_of(text)

    sections: list[tuple[str, list[str]]] = []
    heading = ""
    buffer: list[str] = []
    for line in body.splitlines():
        match = HEADING.match(line)
        if match:
            if buffer:
                sections.append((heading, buffer))
            heading = match.group(2).strip()
            buffer = []
            continue
        buffer.append(line)
    if buffer:
        sections.append((heading, buffer))

    result: list[dict] = []
    for section_heading, lines in sections:
        prose = "\n".join(lines).strip()
        if not prose:
            continue
        label = f"{title} › {section_heading}" if section_heading else title
        start = 0
        while start < len(prose):
            piece = prose[start : start + CHUNK_CHARS]
            result.append(
                {
                    "note": note.relative_to(wiki).as_posix(),
                    "title": title,
                    "heading": section_heading,
                    "text": f"{label}\n\n{piece}",
                    "excerpt": piece[:280].replace("\n", " ").strip(),
                }
            )
            if start + CHUNK_CHARS >= len(prose):
                break
            start += CHUNK_CHARS - CHUNK_OVERLAP
    return result


def store_paths(vault: Path) -> tuple[Path, Path]:
    # The index lives outside the knowledge root. It is derived, it is large,
    # and a cloud sync client has no reason to carry it between machines —
    # rebuilding is cheaper than syncing and always matches the local notes.
    root = vault.parent / "_workspace" / "vault-semantic"
    return root / "index.json", root / "vectors.f32"


def load_index(vault: Path) -> tuple[dict, array.array]:
    index_path, vectors_path = store_paths(vault)
    if not index_path.is_file() or not vectors_path.is_file():
        return {}, array.array("f")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    vectors = array.array("f")
    with vectors_path.open("rb") as handle:
        vectors.frombytes(handle.read())
    return index, vectors


def note_hash(note: Path) -> str:
    return hashlib.sha256(note.read_bytes()).hexdigest()[:16]


def scan(wiki: Path) -> dict[str, str]:
    return {
        path.relative_to(wiki).as_posix(): note_hash(path)
        for path in wiki.rglob("*.md")
        if path.is_file() and "assets" not in path.parts
    }


def drift(vault: Path, index: dict) -> tuple[list[str], list[str]]:
    """Notes added or edited, and notes removed, since the index was written."""
    wiki = vault / "wiki"
    recorded = index.get("notes", {})
    current = scan(wiki)
    changed = [name for name, digest in current.items() if recorded.get(name) != digest]
    removed = [name for name in recorded if name not in current]
    return changed, removed


def build_index(vault: Path, endpoint: str, model: str, quiet: bool = False) -> int:
    wiki = vault / "wiki"
    if not wiki.is_dir():
        fail(f"wiki directory not found: {wiki}")
    check_loopback(endpoint)

    def say(message: str) -> None:
        if not quiet:
            print(message, flush=True)

    notes = sorted(
        path for path in wiki.rglob("*.md")
        if path.is_file() and "assets" not in path.parts
    )
    current = {path.relative_to(wiki).as_posix(): note_hash(path) for path in notes}

    index, old_vectors = load_index(vault)
    reusable: dict[str, list[dict]] = {}
    # A model change invalidates everything: vectors from two models are not
    # comparable, so reuse is only safe within one model and width.
    if index.get("model") == model and index.get("dimension"):
        dimension = index["dimension"]
        old_hashes = index.get("notes", {})
        for position, chunk in enumerate(index.get("chunks", [])):
            name = chunk["note"]
            if old_hashes.get(name) == current.get(name):
                offset = position * dimension
                chunk = dict(chunk)
                chunk["_vector"] = old_vectors[offset : offset + dimension].tolist()
                reusable.setdefault(name, []).append(chunk)

    fresh = [name for name in current if name not in reusable]
    say(f"vault-search: {len(notes)} note(s), {len(fresh)} to embed, {len(reusable)} reused")

    chunks: list[dict] = []
    pending: list[dict] = []
    for path in notes:
        name = path.relative_to(wiki).as_posix()
        if name in reusable:
            chunks.extend(reusable[name])
        else:
            pending.extend(chunks_of(path, wiki))

    batch = 32
    for start in range(0, len(pending), batch):
        window = pending[start : start + batch]
        vectors = embed([item["text"] for item in window], endpoint, model)
        for item, vector in zip(window, vectors):
            item["_vector"] = normalize(vector)
        chunks.extend(window)
        say(f"progress: {min(start + batch, len(pending))}/{len(pending)} chunks")

    if not chunks:
        fail("nothing to index")

    dimension = len(chunks[0]["_vector"])
    flat = array.array("f")
    for chunk in chunks:
        if len(chunk["_vector"]) != dimension:
            fail(f"inconsistent embedding width in {chunk['note']}")
        flat.extend(chunk["_vector"])

    index_path, vectors_path = store_paths(vault)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    vectors_path.write_bytes(flat.tobytes())
    index_path.write_text(
        json.dumps(
            {
                "model": model,
                "dimension": dimension,
                "notes": current,
                "chunks": [
                    {key: chunk[key] for key in ("note", "title", "heading", "excerpt")}
                    for chunk in chunks
                ],
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    size = vectors_path.stat().st_size / 1048576
    say(f"vault-search: indexed {len(chunks)} chunk(s), {size:.1f} MB")
    return 0


def cmd_build(args) -> int:
    check_loopback(args.endpoint)
    model = resolve_model(args.vault, args.endpoint, args.model)
    return build_index(args.vault, args.endpoint, model)


def cmd_query(args) -> int:
    vault = args.vault
    check_loopback(args.endpoint)
    index, vectors = load_index(vault)
    if not index:
        fail("no index yet; run: semantic.py build --vault vault")

    # Catch up before searching, rather than asking a person to remember.
    #
    # A rebuild anyone has to trigger is a rebuild that silently stops
    # happening, and a stale index fails in the worst way available: it returns
    # plausible results that omit the note just written, which reads as "this
    # is not in the vault." Only changed notes are re-embedded, so the usual
    # cost after a writing session is a second or two, and zero when nothing
    # moved.
    if not args.no_refresh:
        changed, removed = drift(vault, index)
        if changed or removed:
            print(
                f"vault-search: {len(changed)} changed, {len(removed)} removed since "
                "the last build — re-embedding those first",
                file=sys.stderr,
            )
            build_index(vault, args.endpoint, index["model"], quiet=True)
            index, vectors = load_index(vault)

    dimension = index["dimension"]
    query_vector = normalize(embed([args.text], args.endpoint, index["model"])[0])

    scored: list[tuple[float, dict]] = []
    for position, chunk in enumerate(index["chunks"]):
        offset = position * dimension
        score = 0.0
        for axis in range(dimension):
            score += vectors[offset + axis] * query_vector[axis]
        scored.append((score, chunk))
    scored.sort(key=lambda item: -item[0])

    # One hit per note. Several chunks of the same long note crowding out every
    # other note is the usual way this kind of search stops being useful.
    seen: set[str] = set()
    shown = 0
    print(f'vault-search: "{args.text}"\n')
    for score, chunk in scored:
        if chunk["note"] in seen:
            continue
        seen.add(chunk["note"])
        location = f" › {chunk['heading']}" if chunk["heading"] else ""
        print(f"{score:.3f}  {chunk['note']}{location}")
        print(f"       {chunk['excerpt']}\n")
        shown += 1
        if shown >= args.limit:
            break

    print(
        "These are pointers ranked by embedding similarity, not evidence. Open "
        "the note and read the passage before using any of it in an answer."
    )
    return 0


def cmd_status(args) -> int:
    vault = args.vault
    index, _ = load_index(vault)
    if not index:
        print("vault-search: no index yet")
        return 0
    recorded = index.get("notes", {})
    changed, removed = drift(vault, index)
    print(
        f"vault-search: {len(index['chunks'])} chunk(s) from {len(recorded)} note(s), "
        f"model {index['model']}"
    )
    print(f"  changed since build: {len(changed)}")
    print(f"  removed since build: {len(removed)}")
    for name in (changed + removed)[:10]:
        print(f"  - {name}")
    if changed or removed:
        print("\nA query picks these up on its own; only changed notes are re-embedded.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "query", "status"):
        part = sub.add_parser(name)
        part.add_argument("--vault", type=Path, required=True)
        part.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
        if name == "build":
            part.add_argument("--model", default=None)
        if name == "query":
            part.add_argument("text")
            part.add_argument("--limit", type=int, default=8)
            part.add_argument(
                "--no-refresh",
                action="store_true",
                help="search the index as-is instead of re-embedding changed notes first",
            )
    args = parser.parse_args()
    return {"build": cmd_build, "query": cmd_query, "status": cmd_status}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
