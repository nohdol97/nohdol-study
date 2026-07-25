---
name: understand
description: Build or incrementally refresh the Understand Anything code graph for a source repository, producing file, symbol, dependency, and architecture layers plus a dependency-ordered tour. Use when the user wants to map an unfamiliar codebase, 코드베이스 파악, 구조 분석, 아키텍처 파악, or 코드 그래프 생성. Do NOT use for Markdown knowledge notes (that is understand-knowledge), for the curated wikilink graph of this vault (that is knowledge-graph), or as a substitute for reading the code before answering.
---

# understand — Code graph generation

## Why

A large unfamiliar repository is hard to enter file by file. This builds a
structural map that says where to look first. It is the entry point that
produces the graph the other adapters read.

The map is a starting point for reading, not a replacement for it. The harness
goal is the user understanding the code, so the graph exists to shorten the
search, never to answer in the code's place.

## Before running

Read `references/adapter-contract.md`. It carries the preflight, the runtime
tiers, the output rules, and the evidence rule for every adapter.

Runtime tier: **built package**. Nearly every bundled script imports
`@understand-anything/core` or `graphology`, so this needs Node 22+, pnpm 10+,
and a built core package. That dependency install is blocked until separately
authorized (ADR 003). When it is unavailable, say so and offer the alternatives
below instead of installing anything.

Alternatives while unavailable: read the code directly with the harness search
tools, or use `knowledge-graph` for the curated notes of this vault.

## Procedure

1. Run the preflight. Confirm the pin is `ready` and the runtime tier is met.
2. State the target repository root, whether `.ua/` is ignored there, and what
   the run will write. Get confirmation before the first write.
3. Follow the upstream `understand/SKILL.md` phases within those boundaries.
4. Report what the graph covers and what it omits, including any ignore rules
   that excluded part of the tree.
5. Treat the result as navigation. Any claim you carry forward gets confirmed
   in the source file first.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Entry into a large repository | File-by-file guessing | Structural map that ranks where to read first |
| Cost visibility | Analysis starts and bills silently | Target, writes, and ignores stated before the run |
| Trust | Generated summary reads as fact | Graph is navigation; the file decides |
