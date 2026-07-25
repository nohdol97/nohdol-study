---
name: understand
description: Analyze a codebase or Markdown knowledge base with the pinned Understand Anything toolchain, routing internally to graph build, question answering, explanation, onboarding path, diff impact, domain view, knowledge extraction, dashboard, or Figma. Use for 코드베이스 파악, 구조 분석, 아키텍처 파악, 이 기능 어디 있어, 어느 파일 봐야 해, 이 부분 설명해줘, 온보딩 가이드, 어디부터 봐야 해, 변경 영향 범위, 도메인 파악, 지식 베이스 분석, 대시보드, and Figma 분석. Do NOT use for the deterministic wikilink graph of this vault (that is knowledge-graph), do NOT finish a factual answer without opening the source file, and do NOT start the dashboard or send anything to Figma without an explicit request in this turn.
---

# understand — Understand Anything, routed

## Why

The pinned upstream ships nine entry points that differ in what they read and
what they cost, but they share one job: find the right thing to read in
something too large to read whole. Routing them from one skill keeps that
shared judgment in one place, so a boundary is stated once instead of nine
times and cannot drift between them.

The map is never the answer. This harness treats the user understanding the
material as the goal, so every mode shortens the search and none of them
replaces reading.

## Route

Pick the mode from what the user is trying to do, then follow that section of
`references/modes.md`.

| The user wants | Mode | Needs |
|---|---|---|
| a map of an unfamiliar repository | `understand` | built package |
| to find where a behavior lives | `understand-chat` | a graph |
| to understand a component well enough to change it | `understand-explain` | a graph |
| a reading order for entering the repository | `understand-onboard` | a graph |
| to know what a change reaches | `understand-diff` | a graph |
| what the system does, in business terms | `understand-domain` | a graph, `python3` |
| a typed view of a Markdown knowledge base | `understand-knowledge` | `python3` |
| to explore a large graph visually | `understand-dashboard` | built package |
| to analyze an approved Figma file | `understand-figma` | built package |

When the request is ambiguous, say which mode you chose and why before running
it. When it spans several, run the cheapest that answers it rather than
chaining modes by default.

## Before running

Read `references/adapter-contract.md`. It carries the preflight, the runtime
tiers, the output rules, and the evidence rule that apply to every mode.

In short: the pin must report `ready`; a graph is navigation and a factual
answer is confirmed in the source file before it is finished; vault analysis is
redirected to `_workspace/understand-anything/`; the dashboard and Figma run
only on an explicit request in this turn; and the built-package tier is automatically installed and built during `study-install` per user authorization (ADR 003 policy override).

When a mode's runtime is unmet, report it as unavailable and offer the
alternative in `references/modes.md`. Never simulate a tool's output, and never
install anything to make a mode run.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Entry into unfamiliar material | File-by-file guessing | Mode chosen for the actual question |
| Boundaries | Restated per entry point and drifting | Stated once, applied to every mode |
| Trust | Generated summary reads as fact | Graph is navigation; the file decides |
| Cost | Heaviest tool by default | Cheapest mode that answers, tiers reported |
