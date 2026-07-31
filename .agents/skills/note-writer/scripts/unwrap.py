#!/usr/bin/env python3
"""Join hard-wrapped paragraph lines in Markdown notes.

A paragraph split across several source lines renders as one paragraph anyway,
so the breaks carry no meaning - but they make every later edit reflow the
whole block, and they hide diffs behind rewrapping noise. This joins those
lines back into one line per paragraph.

What it never touches, because the line break IS the structure:

  - YAML frontmatter
  - fenced code blocks (``` and ~~~) and indented code blocks
  - tables (any line starting with `|`)
  - headings, thematic breaks, and blank lines
  - list items and their wrapped continuations, which keep their own shape
  - a line ending in two spaces or a backslash: an explicit hard break
  - the line before a line that starts a new block (list, table, heading,
    fence, quote level change)

Report only by default. Pass --write to edit in place.

    python3 unwrap.py --vault vault            # report
    python3 unwrap.py --vault vault --write    # apply
"""

import argparse
import pathlib
import re
import sys

FENCE = re.compile(r"^\s{0,3}(```|~~~)")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s")
HR = re.compile(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$")
LIST = re.compile(r"^\s*([-*+]|\d+[.)])(\s|$)")
TABLE = re.compile(r"^\s*\|")
QUOTE = re.compile(r"^(\s*(?:>\s?)+)(.*)$")
INDENT_CODE = re.compile(r"^(\t| {4,})\S")
FOOTNOTE = re.compile(r"^\s*\[\^[^\]]+\]:")
DEF = re.compile(r"^\s*(:|\[[^\]]+\]:)")
# `코드: ...` / `제목: ...` — a short label then a colon. Written as prose but
# used as a list, so each one owns its line.
LABEL = re.compile(r"^\s*\**[^\s:：]([^:：\n]{0,28})\**[:：]\s")
# A line that is nothing but ONE bold span is a heading in disguise. The inner
# text must hold no `**`, or `**a** 이므로 **b**` would look like a heading too.
BOLD_ONLY = re.compile(r"^\s*\*\*(?:[^*]|\*(?!\*))+\*\*\s*$")


def quote_prefix(line):
    """Return (prefix, rest) for a blockquote line, else ('', line)."""
    m = QUOTE.match(line)
    if not m:
        return "", line
    return m.group(1), m.group(2)


def depth(prefix):
    return prefix.count(">")


def starts_block(line):
    """True if this line begins a construct whose first line must stay first."""
    body = quote_prefix(line)[1]
    s = body.strip()
    if not s:
        return True
    return bool(
        HEADING.match(body)
        or HR.match(body)
        or LIST.match(body)
        or TABLE.match(body)
        or FENCE.match(body)
        or FOOTNOTE.match(body)
        or DEF.match(body)
        or INDENT_CODE.match(body)
        or LABEL.match(body)
        or BOLD_ONLY.match(body)
    )


def absorbs_next(line):
    """A bold-only line is a heading in disguise: nothing folds into it."""
    return not BOLD_ONLY.match(quote_prefix(line)[1])


def is_plain_paragraph_line(line):
    """A line that is ordinary prose (possibly inside a blockquote)."""
    prefix, body = quote_prefix(line)
    if not body.strip():
        return False
    return not (
        HEADING.match(body)
        or HR.match(body)
        or LIST.match(body)
        or TABLE.match(body)
        or FENCE.match(body)
        or FOOTNOTE.match(body)
        or DEF.match(body)
        or INDENT_CODE.match(body)
    )


def join(a, b):
    """Join two prose lines. CJK needs no space; Latin does."""
    a = a.rstrip()
    b = b.lstrip()
    if not a:
        return b
    if not b:
        return a
    if a[-1].isspace() or b[0].isspace():
        return a + b
    return a + " " + b


def unwrap(text):
    lines = text.split("\n")
    out = []
    i = 0
    n = len(lines)
    joined = 0

    # frontmatter passes through untouched
    if lines and lines[0].strip() == "---":
        out.append(lines[0])
        i = 1
        while i < n and lines[i].strip() != "---":
            out.append(lines[i])
            i += 1
        if i < n:
            out.append(lines[i])
            i += 1

    in_fence = None
    while i < n:
        line = lines[i]
        body = quote_prefix(line)[1]

        if in_fence:
            out.append(line)
            if FENCE.match(body) and body.strip().startswith(in_fence):
                in_fence = None
            i += 1
            continue

        m = FENCE.match(body)
        if m:
            in_fence = m.group(1)
            out.append(line)
            i += 1
            continue

        # a list item absorbs its own wrapped continuations, which are indented
        # further than the marker and start no new construct
        if LIST.match(body) and not TABLE.match(body):
            prefix, cur = quote_prefix(line)
            d = depth(prefix)
            while i + 1 < n:
                if cur.endswith("  ") or cur.endswith("\\"):
                    break
                nxt = lines[i + 1]
                nprefix, nbody = quote_prefix(nxt)
                if depth(nprefix) != d or not nbody.strip():
                    break
                indent = len(nbody) - len(nbody.lstrip())
                if indent == 0 or starts_block(nxt) or FENCE.match(nbody):
                    break
                cur = join(cur, nbody)
                joined += 1
                i += 1
            out.append(prefix + cur if prefix else cur)
            i += 1
            continue

        if not is_plain_paragraph_line(line):
            out.append(line)
            i += 1
            continue

        # prose: absorb following prose lines at the same quote depth
        prefix, cur = quote_prefix(line)
        d = depth(prefix)
        while absorbs_next(line) and i + 1 < n:
            nxt = lines[i + 1]
            # an explicit hard break ends the join
            if cur.endswith("  ") or cur.endswith("\\"):
                break
            if not is_plain_paragraph_line(nxt):
                break
            if starts_block(nxt):
                break
            nprefix, nbody = quote_prefix(nxt)
            if depth(nprefix) != d:
                break
            cur = join(cur, nbody)
            joined += 1
            i += 1
        out.append(prefix + cur if prefix else cur)
        i += 1

    return "\n".join(out), joined


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--globs", nargs="*",
                    default=["wiki/**/*.md", "raw/**/*.md", "*.md"])
    args = ap.parse_args()

    root = pathlib.Path(args.vault)
    seen = set()
    total_files = total_joins = 0
    for g in args.globs:
        for p in sorted(root.glob(g)):
            if p in seen or not p.is_file():
                continue
            seen.add(p)
            src = p.read_text(encoding="utf-8")
            new, joined = unwrap(src)
            if joined == 0 or new == src:
                continue
            total_files += 1
            total_joins += joined
            print(f"{joined:5d}  {p.relative_to(root)}")
            if args.write:
                p.write_text(new, encoding="utf-8")

    verb = "joined" if args.write else "would join"
    print(f"\n{total_files} file(s), {verb} {total_joins} line break(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
