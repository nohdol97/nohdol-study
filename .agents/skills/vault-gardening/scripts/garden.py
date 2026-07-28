#!/usr/bin/env python3
"""Report what has drifted in a knowledge root.

A vault degrades quietly. Frontmatter loses a field, a note stops being
reachable from the index, the hot cache grows past the budget that made it
cheap, a link points at a note that was renamed. None of that breaks anything
today, which is exactly why it accumulates.

This reports; it never edits. Deciding that an orphan should be linked, or
that a note is stale, is a judgment about knowledge, and the point of the
report is to put those decisions in front of a person.

Usage: garden.py --vault PATH [--hot-budget BYTES] [--index-link-budget N]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys


GRAPH_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "knowledge-graph" / "scripts" / "build_graph.py"
)
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REQUIRED_FIELDS = ["type", "status", "created", "updated"]
STATUS_VALUES = {"seed", "developing", "mature", "evergreen"}
VERIFICATION_VALUES = {
    "unverified", "source-backed", "primary-confirmed", "cross-checked",
    "contested",
}
# hot.md is loaded at the start of every session, so its cost is paid whether
# or not it is used. The budget is the reason it stays worth loading.
DEFAULT_HOT_BUDGET = 2000
# index.md is an entry point, not a listing. It should link the hub note for a
# topic and let the hub carry that topic's atomic notes, so its size tracks the
# number of topics rather than the number of notes. Once it links more notes
# than this, it has started to grow with the vault and stops being scannable.
DEFAULT_INDEX_LINK_BUDGET = 15
WIKILINK = re.compile(r"\[\[([^\]|#]+)")


def build_graph(wiki: Path) -> dict:
    output = wiki.parent / ".garden-graph.json"
    result = subprocess.run(
        [sys.executable, str(GRAPH_SCRIPT), "--wiki", str(wiki), "--output", str(output)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or "graph build failed")
    try:
        return json.loads(output.read_text(encoding="utf-8"))
    finally:
        output.unlink(missing_ok=True)


def check_frontmatter(graph: dict) -> list[str]:
    findings: list[str] = []
    for node in graph["nodes"]:
        if node["type"] != "article":
            continue
        frontmatter = node.get("frontmatter") or {}
        path = node["path"]
        for field in REQUIRED_FIELDS:
            value = frontmatter.get(field)
            if value in (None, "", []):
                findings.append(f"{path}: missing frontmatter field {field!r}")
        status = frontmatter.get("status")
        if status and status not in STATUS_VALUES:
            findings.append(f"{path}: status {status!r} is not one of {sorted(STATUS_VALUES)}")
        verification = frontmatter.get("verification")
        if verification and verification not in VERIFICATION_VALUES:
            findings.append(
                f"{path}: verification {verification!r} is not a recognized state"
            )
        for field in ("created", "updated", "checked"):
            value = frontmatter.get(field)
            if value and not ISO_DATE.match(str(value)):
                findings.append(f"{path}: {field} {value!r} is not an ISO date")
        created = str(frontmatter.get("created") or "")
        updated = str(frontmatter.get("updated") or "")
        if ISO_DATE.match(created) and ISO_DATE.match(updated) and updated < created:
            findings.append(f"{path}: updated {updated} precedes created {created}")
        # A note asserting it was cross-checked without recording when is a
        # claim nobody can re-examine.
        if verification in {"primary-confirmed", "cross-checked"} and not frontmatter.get("checked"):
            findings.append(
                f"{path}: verification {verification!r} without a 'checked' date"
            )
    return findings


def index_content(text: str) -> str:
    """Return index.md with its fenced blocks and code spans removed.

    The rule is borrowed from the graph builder rather than written again here.
    Two readings of what counts as a link drift apart, and then the budget
    reports links the graph never recorded.
    """
    spec = importlib.util.spec_from_file_location("study_build_graph", GRAPH_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.content_without_fences(text)


def check_index_shape(index: Path, budget: int) -> list[str]:
    """Report an index that has become a listing instead of an entry point.

    An index that names every note grows with the vault, which is exactly what
    an entry point must not do. The fix is never to delete knowledge: it is to
    give the topic a hub note and let the hub carry its atomic notes.
    """
    if not index.is_file():
        return []
    # A wikilink shown inside a fence or a code span is an example of the
    # syntax, not navigation, and a code span carries its line ending inside it.
    # The graph builder already draws that line, so the budget is counted
    # against the same text the graph reads rather than a second reading of it.
    text = index_content(index.read_text(encoding="utf-8"))
    # Embeds are assets, not navigation, so they do not count against the budget.
    targets = {
        match.group(1).strip()
        for match in WIKILINK.finditer(text)
        if not text[: match.start()].endswith("!")
    }
    if len(targets) <= budget:
        return []
    return [
        f"index.md links {len(targets)} notes, over the {budget} budget; it is an "
        "entry point, so give a topic one hub note and let the hub list that "
        "topic's atomic notes"
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, required=True)
    parser.add_argument("--hot-budget", type=int, default=DEFAULT_HOT_BUDGET)
    parser.add_argument(
        "--index-link-budget", type=int, default=DEFAULT_INDEX_LINK_BUDGET
    )
    args = parser.parse_args()

    vault = args.vault
    wiki = vault / "wiki"
    if not wiki.is_dir():
        print(f"vault-gardening: wiki directory not found: {wiki}", file=sys.stderr)
        return 2

    try:
        graph = build_graph(wiki)
    except (OSError, ValueError) as exc:
        print(f"vault-gardening: {exc}", file=sys.stderr)
        return 1

    sections: list[tuple[str, list[str]]] = []

    broken = [
        f"{item['target']} (referenced by {', '.join(item['referenced_by'])})"
        for item in graph["missing_targets"]
    ]
    sections.append(("links pointing at nothing", broken))

    # What makes a note reachable is that something points AT it — a backlink,
    # or a category in the index. Its own outgoing links say nothing about
    # whether anyone can find it.
    #
    # The earlier check reported `graph["orphans"]`, which requires a note to
    # have no links AND no backlinks. That let the worst case through: a note
    # citing six others while nobody cites it is invisible in the vault yet
    # counts as connected. One shipped exactly that way, reachable only from
    # the index's "recent" list, which keeps five entries and drops the rest.
    # Being listed there is not a category edge, so it is correctly not
    # counted here.
    categorized = {
        edge["from"] for edge in graph["edges"] if edge["type"] == "categorized_under"
    }
    unreachable = sorted(
        node["title"]
        for node in graph["nodes"]
        if node.get("type") == "article"
        and not node.get("backlinks")
        and node["id"] not in categorized
    )
    sections.append(("notes nothing points to", unreachable))

    sections.append(("frontmatter that breaks the note contract", check_frontmatter(graph)))

    missing_sources = [
        f"{node['reference']} (cited but not present)"
        for node in graph["nodes"]
        if node["type"] == "source" and node.get("kind") == "file" and not node.get("present")
    ]
    sections.append(("cited sources that are not in raw/", missing_sources))

    derived: list[str] = []
    for name in ("index.md", "log.md", "hot.md"):
        if not (vault / name).is_file():
            derived.append(f"{name} is missing")
    hot = vault / "hot.md"
    if hot.is_file():
        size = hot.stat().st_size
        if size > args.hot_budget:
            derived.append(
                f"hot.md is {size} bytes, over the {args.hot_budget} budget; "
                "it is loaded every session, so trim it to what a session needs"
            )
    derived.extend(check_index_shape(vault / "index.md", args.index_link_budget))
    sections.append(("session context", derived))

    total = sum(len(items) for _, items in sections)
    print(f"vault-gardening: {graph['counts']['article']} note(s), {total} finding(s)")
    for title, items in sections:
        print(f"\n## {title} ({len(items)})")
        if not items:
            print("- none")
            continue
        for item in items:
            print(f"- {item}")

    print(
        "\nNothing was changed. Each finding is a decision about knowledge: link "
        "an orphan only where a real relationship exists, and never add a link "
        "just to empty this list."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
