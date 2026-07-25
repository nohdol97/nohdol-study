---
name: understand-diff
description: Overlay a set of changes onto the existing Understand Anything graph to show which components, dependents, and layers a diff reaches. Use for 변경 영향 범위, 이 수정 뭘 건드려, and reviewing an unfamiliar diff before reading every file. Do NOT treat the overlay as a completed impact analysis, and do NOT use it when the graph predates the changes without saying so.
---

# understand-diff — Change impact overlay

## Why

A diff shows what changed; it does not show what depends on the change. The
graph supplies the dependents so the review starts at the right blast radius.

## Before running

Read `../understand/references/adapter-contract.md`.

Runtime tier: **graph consumer**. Needs a graph from `understand`.

Freshness matters more here than anywhere else. The graph is a snapshot of a
past state, so the very edits you are analyzing are the edits it does not know
about. Report the graph's base commit against the diff's base, and treat a gap
as a limit on the answer rather than a detail.

## Procedure

1. Establish the diff scope and the graph's base version, and state both.
2. Overlay the changed files to list touched components and their dependents.
3. Open the changed files and the dependents that matter. Reachability in a
   graph is not evidence that behavior breaks.
4. Report impact in three groups: confirmed by reading, suspected and unread,
   and outside what the graph covers.
5. Never present the overlay alone as a review verdict.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Blast radius | Changed files only | Dependents surfaced from the graph |
| Snapshot risk | Stale graph passes unnoticed | Base versions compared and reported |
| Verdict | Reachability read as impact | Confirmed, suspected, and uncovered kept apart |
