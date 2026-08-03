#!/usr/bin/env python3

from pathlib import Path
import subprocess
import sys
import tempfile


SCRIPT = Path(__file__).with_name("garden.py")


def run(vault: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--vault", str(vault), *extra],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )


def build(root: Path) -> Path:
    vault = root / "vault"
    (vault / "wiki").mkdir(parents=True)
    (vault / "raw").mkdir()
    (vault / "index.md").write_text("# Index\n\n## Topics\n", encoding="utf-8")
    (vault / "log.md").write_text("# Log\n", encoding="utf-8")
    (vault / "hot.md").write_text("# Hot\n", encoding="utf-8")
    return vault


HEALTHY = """---
type: concept
status: mature
created: 2026-07-01
updated: 2026-07-02
verification: source-backed
---
# Healthy

Body.
"""


with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    vault = build(root)
    (vault / "wiki" / "healthy.md").write_text(HEALTHY, encoding="utf-8")
    (vault / "index.md").write_text(
        "# Index\n\n## Topics\n\n- Things\n  - [[Healthy]]\n", encoding="utf-8"
    )

    result = run(vault)
    assert result.returncode == 0, result.stderr
    assert "1 note(s), 0 finding(s)" in result.stdout, result.stdout
    # It reports and never edits.
    assert "Nothing was changed" in result.stdout
    assert not (vault / ".garden-graph.json").exists(), "the temporary graph was left behind"

    # A note the index groups is filed, not lost, even with no wikilinks.
    assert "notes nothing points to (0)" in result.stdout

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    vault = build(root)
    (vault / "wiki" / "broken.md").write_text(
        """---
type: concept
status: unusual
created: 2026-07-02
updated: 07/01/2026
verification: probably
---
# Broken

Points at [[Nowhere]].
""",
        encoding="utf-8",
    )
    (vault / "wiki" / "bare.md").write_text("# Bare\n", encoding="utf-8")
    (vault / "wiki" / "backwards.md").write_text(
        """---
type: concept
status: seed
created: 2026-07-10
updated: 2026-07-01
verification: cross-checked
---
# Backwards
""",
        encoding="utf-8",
    )
    (vault / "wiki" / "sourced.md").write_text(
        """---
type: concept
status: seed
created: 2026-07-01
updated: 2026-07-01
sources:
  - "raw/present.md"
  - "raw/absent.md"
  - "https://example.org/page"
---
# Sourced
""",
        encoding="utf-8",
    )
    (vault / "raw" / "present.md").write_text("here\n", encoding="utf-8")

    result = run(vault)
    assert result.returncode == 0, result.stderr
    out = result.stdout

    # A link with no target is reported with who pointed at it.
    assert "Nowhere (referenced by Broken)" in out, out
    # A note nothing points to is surfaced.
    assert "- Bare" in out, out
    # Broken sends a link out. That says nothing about whether anyone can find
    # it, so it must be reported too — this is the case the old "no link and no
    # category" rule let through.
    assert "- Broken" in out, out
    # Contract violations are named per note and field.
    assert "status 'unusual' is not one of" in out
    assert "verification 'probably' is not a recognized state" in out
    assert "updated '07/01/2026' is not an ISO date" in out
    assert "missing frontmatter field 'type'" in out
    assert "updated 2026-07-01 precedes created 2026-07-10" in out
    # Claiming a cross-check without recording when makes it unreviewable.
    assert "verification 'cross-checked' without a 'checked' date" in out
    # A cited file that is not in raw/ is reported; a URL is not a local file.
    assert "raw/absent.md (cited but not present)" in out
    assert "raw/present.md" not in out.split("cited sources")[1].split("##")[0]
    assert "example.org" not in out

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    vault = build(root)
    (vault / "wiki" / "healthy.md").write_text(HEALTHY, encoding="utf-8")

    # The hot cache is loaded every session, so its budget is enforced.
    (vault / "hot.md").write_text("x" * 4000, encoding="utf-8")
    result = run(vault)
    assert "over the 3000 budget" in result.stdout, result.stdout
    result = run(vault, "--hot-budget", "8000")
    assert "budget" not in result.stdout.split("session context")[1]

    # The default is enforced at its actual value, not merely somewhere below
    # the oversized case above: a cache one byte under budget passes and one
    # byte over is reported. Without this the constant could drift and only the
    # 4000-byte case would notice.
    (vault / "hot.md").write_text("x" * 3000, encoding="utf-8")
    assert "budget" not in run(vault).stdout.split("session context")[1]
    (vault / "hot.md").write_text("x" * 3001, encoding="utf-8")
    assert "over the 3000 budget" in run(vault).stdout

    # Korean prose is counted in bytes like everything else. A Hangul syllable
    # is 3 UTF-8 bytes, so 1000 of them sit exactly at the budget and 1001 do
    # not - the gate must not silently measure characters instead.
    (vault / "hot.md").write_text("가" * 1000, encoding="utf-8")
    assert "budget" not in run(vault).stdout.split("session context")[1]
    (vault / "hot.md").write_text("가" * 1001, encoding="utf-8")
    assert "over the 3000 budget" in run(vault).stdout

    # A missing derived file is a finding, not a crash.
    (vault / "log.md").unlink()
    result = run(vault)
    assert result.returncode == 0
    assert "log.md is missing" in result.stdout

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    vault = build(root)
    (vault / "wiki" / "healthy.md").write_text(HEALTHY, encoding="utf-8")

    # An index that names every note grows with the vault, which is what an
    # entry point must not do. Under the budget it is left alone.
    listing = "# Index\n\n## Topics\n\n" + "".join(
        f"- [[Note {n}]]\n" for n in range(12)
    )
    (vault / "index.md").write_text(listing, encoding="utf-8")
    result = run(vault)
    assert "over the 15 budget" not in result.stdout, result.stdout

    # Past the budget it is reported, and the advice is to add a hub, never to
    # drop knowledge.
    listing = "# Index\n\n## Topics\n\n" + "".join(
        f"- [[Note {n}]]\n" for n in range(30)
    )
    (vault / "index.md").write_text(listing, encoding="utf-8")
    result = run(vault)
    assert "index.md links 30 notes, over the 15 budget" in result.stdout, result.stdout
    assert "hub note" in result.stdout

    # The budget is configurable for a vault with genuinely many topics.
    result = run(vault, "--index-link-budget", "50")
    assert "over the 50 budget" not in result.stdout

    # Links shown as syntax are not navigation. A code span keeps its line
    # ending inside it, so the one written across a break must not count either
    # - otherwise an index explaining the link syntax reports itself as bloated.
    demo = (
        "# Index\n\n## Topics\n\n- Things\n  - [[Healthy]]\n\n"
        "Write `[[Example]]` to link. Long form: `[[Example\n"
        "Note|alias]]` also works.\n\n"
        "```md\n" + "".join(f"- [[Fenced {n}]]\n" for n in range(20)) + "```\n"
    )
    (vault / "index.md").write_text(demo, encoding="utf-8")
    result = run(vault, "--index-link-budget", "1")
    assert "over the 1 budget" not in result.stdout, result.stdout

    # Repeating one hub is navigation, not listing: distinct targets are counted.
    (vault / "index.md").write_text(
        "# Index\n\n## Topics\n\n" + "- [[Hub]]\n" * 30, encoding="utf-8"
    )
    result = run(vault)
    assert "over the 15 budget" not in result.stdout, result.stdout

    # Embedded assets are not navigation and must not consume the budget.
    embeds = "# Index\n\n" + "".join(
        f"![[assets/topic/frame-{n}.jpg]]\n" for n in range(30)
    )
    (vault / "index.md").write_text(embeds, encoding="utf-8")
    result = run(vault)
    assert "over the 15 budget" not in result.stdout, result.stdout

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    vault = build(root)
    # Unrelated content beside the curated layer is common in a real vault and
    # must not be walked or reported.
    legacy = vault / "Legacy Project"
    (legacy / "deep").mkdir(parents=True)
    (legacy / "deep" / "old.md").write_text("# Old\n\nSee [[Nothing Here]].\n", encoding="utf-8")
    (vault / "wiki" / "healthy.md").write_text(HEALTHY, encoding="utf-8")
    (vault / "index.md").write_text(
        "# Index\n\n## Topics\n\n- Things\n  - [[Healthy]]\n", encoding="utf-8"
    )

    result = run(vault)
    assert result.returncode == 0, result.stderr
    assert "1 note(s)" in result.stdout, result.stdout
    assert "Nothing Here" not in result.stdout, "legacy content was scanned"
    assert "Old" not in result.stdout

    # A missing wiki directory is an argument error, not an empty success.
    result = run(root / "absent-vault")
    assert result.returncode == 2
    assert "wiki directory not found" in result.stderr

# Reachability is decided by what points AT a note, and by nothing else. The
# three notes below separate the ways that can happen.
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    vault = build(root)

    def note(title: str, body: str) -> str:
        return (
            "---\ntype: concept\nstatus: seed\ncreated: 2026-07-01\n"
            f"updated: 2026-07-01\nverification: source-backed\n---\n# {title}\n\n{body}\n"
        )

    # Cites two notes; nobody cites it, and the index does not file it.
    (vault / "wiki" / "loud.md").write_text(
        note("Loud", "Points at [[Quiet]] and [[Filed]]."), encoding="utf-8"
    )
    # Cites nobody, but Loud points at it.
    (vault / "wiki" / "quiet.md").write_text(note("Quiet", "Body."), encoding="utf-8")
    # Cited and filed under a topic.
    (vault / "wiki" / "filed.md").write_text(note("Filed", "Body."), encoding="utf-8")
    (vault / "index.md").write_text(
        "# Index\n\n## Topics\n\n- Things\n  - [[Filed]]\n", encoding="utf-8"
    )

    out = run(vault).stdout
    section = out.split("notes nothing points to")[1].split("##")[0]
    assert "- Loud" in section, section
    # An inbound link is enough; a category is not required.
    assert "- Quiet" not in section, section
    # A category is enough; an inbound link is not required.
    assert "- Filed" not in section, section

print("vault gardening tests: PASS")
