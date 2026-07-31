# Curated note schema

Use this template:

```markdown
---
type: concept
status: seed
created: YYYY-MM-DD
updated: YYYY-MM-DD
related:
  - "[[Related note]]"
sources:
  - "raw/source-file.pdf"
  - "https://example.com/source"
verification: cross-checked
checked: YYYY-MM-DD
---

# Specific note title

## 핵심

Explain one concept or claim in the user's working language.

## 관계

- Builds on [[Foundation]]
- Contrasts with [[Alternative]]

## 검증

| 핵심 주장 | 구분 | 검증 상태 | 근거 | 반증·한계 | 확인일 |
|---|---|---|---|---|---|
| 구체적인 주장 | 사실 | cross-checked | [1차 출처](https://example.com/primary), [독립 출처](https://example.org/corroboration) | 적용 범위 | YYYY-MM-DD |

## 열린 질문

> [!question]
> What remains unresolved?

## 모순과 한계

> [!warning]
> Record conflicting evidence, scope limits, or uncertainty.

## 출처

- [Source title](https://example.com/source)
```

## Line layout

One source line per paragraph, per list item, and per blockquote line. Do not
wrap prose at a column: the break renders as a space, so it changes nothing a
reader sees while making every later edit reflow the block and every diff show
rewrapping instead of the change. Reserve a line break for structure - a
heading, a list item, a table row, fenced code, a frontmatter key, or an
explicit hard break written as two trailing spaces or a backslash. The
`note-writer` SKILL carries the check that finds violations.

## Field rules

The H1 must match the filename exactly. A title containing `/` cannot, because
the filesystem reads it as a path separator: write the filename, H1, and every
`[[wikilink]]` with a space instead (`Redis Pub Sub와 Streams 메시징`) and state
the real spelling in the first line of the body.

- `type`: one lowercase label. Prefer `concept`, `claim`, `method`, `topic`, `source`, or `question`; introduce another stable label only when these are misleading.
- `status`: `seed` for a first useful capture, `developing` for connected but incomplete understanding, `mature` for well-supported coverage, `evergreen` for stable and maintained knowledge.
- `created`: never change after creation.
- `updated`: change when meaning changes, not for whitespace-only edits.
- `related`: flat list. Every item should represent a real semantic relation.
- `sources`: flat list of exact URLs or vault-relative `raw/` paths. An empty list is valid for personal synthesis, but label the content as such.
- `verification`: use `unverified` when captured but unchecked, `source-backed` after inspecting a relevant source, `primary-confirmed` when an authoritative primary source directly establishes the claim, `cross-checked` when independent evidence corroborates it, and `contested` when credible evidence conflicts.
- `checked`: date when the evidence itself was last inspected. Refresh it for claims whose truth can change with versions, policy, price, law, personnel, or current events.

The note-level `verification` field summarizes the weakest material claim, not the strongest one. A note with one unresolved central claim cannot be marked `cross-checked`.

AI-generated text is not a source. NotebookLM inline citations, search snippets, and model-produced bibliographies are navigation aids until the linked source and supporting passage have been inspected.

Avoid nested frontmatter objects, generated IDs, database-only metadata, and plugin-specific fields in Phase 1.
