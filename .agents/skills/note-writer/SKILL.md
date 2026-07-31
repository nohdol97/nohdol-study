---
name: note-writer
description: Create or revise durable study notes in the connected knowledge root while enforcing atomic scope, flat YAML frontmatter, wikilinks, evidence, uncertainty, and index/log/hot consistency. Use when the user asks to 기록, 정리, 노트화, 지식으로 저장, or when a study session produces reusable understanding.
---

# note-writer — Curated knowledge notes

Read `references/note-schema.md` and `references/evidence-check.md` before writing.

## Why

Durable notes become future evidence for reasoning. Atomic scope, explicit
uncertainty, and traceable sources keep a polished synthesis from hardening into
false memory.

## Procedure

1. Verify installation (`REGISTRY.md` and `vault`).
2. Search `vault/wiki/` for an existing note that already represents the concept or claim. Search twice, because the two searches fail differently: `rg` finds the wording you guessed, and `vault-search` finds the concept when the existing note called it something else — which is exactly how a duplicate gets written.

   ```sh
   python3 .agents/skills/vault-search/scripts/semantic.py query --vault vault "노트로 쓰려는 개념을 한 문장으로"
   ```

   Open the top candidates before deciding. A ranked hit is a pointer, not a verdict that the concept is already covered, and an empty result is not proof that it is not — the index can be stale (`semantic.py status --vault vault`).
3. Choose between improving the existing note and creating one new atomic note. Do not create aliases merely because wording differs.
4. If a source must be retained, save an unchanged copy under `vault/raw/`. Never rewrite raw material.
5. Apply the mandatory evidence-check reference for material factual claims. Inspect the underlying primary or authoritative source rather than trusting a model summary or citation list.
6. Write the curated note under `vault/wiki/` using the schema. Preserve evidence boundaries: sourced statements, synthesis, inference, hypothesis, and open questions must be distinguishable.
7. Add meaningful `[[wikilinks]]` in both directions when updating related notes is safe and in scope.
8. Update `vault/index.md` as an entry point, not a listing. Follow
   `references/index-policy.md`: one hub note per topic, atomic notes reached
   through the hub, and recent-change lines capped because `log.md` is the record.
9. Add one concise row at the top of `vault/log.md` so the newest work reads
   first; never change or remove an entry already written.
10. Refresh `vault/hot.md` with only current focus, recent durable learning, open questions, and next actions. Keep it roughly 500 tokens or less.
11. Verify frontmatter, links, source paths, evidence status, and that no raw
    file changed unexpectedly. Then check the line layout, which nothing else
    catches because a hard-wrapped file renders correctly:

    ```sh
    python3 .agents/skills/note-writer/scripts/unwrap.py --vault vault
    ```

    It reports; `--write` applies. See "One line per paragraph" below.
12. When the note carries a diagram or an embedded asset, run the `diagram`
    check on it before finishing. A broken diagram renders as
    `Error parsing Mermaid diagram!`, or prints `Unsupported markdown: list`
    where a label should be, and the source still looks complete either way, so
    nothing else in this procedure catches it:

    ```sh
    python3 .agents/skills/diagram/scripts/check.py "vault/wiki/NOTE.md"
    ```

    In a `flowchart` or `graph`, quote every node label, edge label, and
    `subgraph` title, start no label with `1. `, `- `, or `# `, and break lines
    with `<br/>` rather than `\n` - see the `diagram` skill for why.

## One line per paragraph

**Write each paragraph, list item, and blockquote line as a single source line.
Do not wrap prose at a column.** A newline inside a paragraph renders as a
space, so the break says nothing a reader can see - but the writer pays for it
every time: editing one word reflows the whole block, the diff turns into
rewrapping noise that hides the real change, and Obsidian's editor rewraps to
the pane width anyway, so the file and the screen disagree.

A line break is content only where it is structure. Keep these on their own
lines: headings, list items, table rows, fenced code, frontmatter keys, and a
line ending in two spaces or a backslash, which is an explicit hard break.

Long lines are correct here. Wrap at the reader's window, not in the file.

```markdown
<!-- no -->
IMEC이 정리한 5대 난제 중 핵심은 비정상성이다.
"정상"은 하나가 아니며, 학습 시점의 정상이
테스트 시점에도 정상이라는 보장이 없다.

<!-- yes -->
IMEC이 정리한 5대 난제 중 핵심은 비정상성이다. "정상"은 하나가 아니며, 학습 시점의 정상이 테스트 시점에도 정상이라는 보장이 없다.
```

The same rule holds inside a blockquote (`> ` prose is one line per paragraph)
and inside a list item (a wrapped continuation belongs on the item's line).

## Quality gates

- One note has one central concept or claim.
- The title is specific enough to link without extra context.
- Every named source exists or has a valid URL.
- Every material factual claim maps to inspected evidence or is explicitly labeled unverified, inference, hypothesis, or contested.
- Unknowns remain unknown; no invented citation, quote, relationship, or confidence.
- Contradictions and gaps are explicit callouts, not smoothed away.
- Time-sensitive claims include a current `checked` date.
- Agreement between AI systems is not counted as independent corroboration.
- Existing legacy notes outside the curated layer stay untouched unless the user requests migration.
- Any diagram in the note passes the `diagram` check, so it renders as a picture rather than an error block.
- Each paragraph, list item, and blockquote line occupies one source line; `unwrap.py` reports nothing to join.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Scope | Topic dumps and duplicates | One central concept or claim |
| Confidence | Fluent prose hides uncertainty | Verification state and open gaps |
| Navigation | Isolated files | Wikilinks plus index/log/hot consistency |
| Line layout | Prose hard-wrapped, so every edit reflows a block | One line per paragraph; diffs show the change |
