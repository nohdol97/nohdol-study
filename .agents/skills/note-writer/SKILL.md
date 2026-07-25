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
2. Search `vault/wiki/` for an existing note that already represents the concept or claim.
3. Choose between improving the existing note and creating one new atomic note. Do not create aliases merely because wording differs.
4. If a source must be retained, save an unchanged copy under `vault/raw/`. Never rewrite raw material.
5. Apply the mandatory evidence-check reference for material factual claims. Inspect the underlying primary or authoritative source rather than trusting a model summary or citation list.
6. Write the curated note under `vault/wiki/` using the schema. Preserve evidence boundaries: sourced statements, synthesis, inference, hypothesis, and open questions must be distinguishable.
7. Add meaningful `[[wikilinks]]` in both directions when updating related notes is safe and in scope.
8. Update `vault/index.md` as an entry point, not a listing. Follow
   `references/index-policy.md`: one hub note per topic, atomic notes reached
   through the hub, and recent-change lines capped because `log.md` is the record.
9. Append one concise row or bullet to `vault/log.md`; never reorder or rewrite history.
10. Refresh `vault/hot.md` with only current focus, recent durable learning, open questions, and next actions. Keep it roughly 500 tokens or less.
11. Verify frontmatter, links, source paths, evidence status, and that no raw file changed unexpectedly.
12. When the note carries a diagram or an embedded asset, run the `diagram`
    check on it before finishing. A broken diagram renders as
    `Error parsing Mermaid diagram!` and the source still looks complete, so
    nothing else in this procedure catches it:

    ```sh
    python3 .agents/skills/diagram/scripts/check.py "vault/wiki/NOTE.md"
    ```

    In a `flowchart` or `graph`, quote every node label, edge label, and
    `subgraph` title - see the `diagram` skill for why bare labels fail.

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

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Scope | Topic dumps and duplicates | One central concept or claim |
| Confidence | Fluent prose hides uncertainty | Verification state and open gaps |
| Navigation | Isolated files | Wikilinks plus index/log/hot consistency |
