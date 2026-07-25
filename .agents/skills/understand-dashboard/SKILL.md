---
name: understand-dashboard
description: Start the Understand Anything graph viewer on loopback for visual exploration, only when the user explicitly asks for it. Use for 대시보드 열어줘, 그래프 시각화, 시각적으로 보고 싶어 about an already-analyzed repository. Do NOT start it as a follow-up to another skill, do NOT bind it to any address other than loopback, and do NOT use it to answer questions the agent should answer by reading files.
---

# understand-dashboard — Loopback graph viewer

## Why

A large graph is easier to explore visually than through queries. That value is
for the person looking at it; the agent still answers from files.

## Before running

Read `../understand/references/adapter-contract.md`.

Runtime tier: **built package**. The viewer needs Node 22+, pnpm 10+, a
dependency install, and a build. That install is blocked until separately
authorized (ADR 003), so on a machine without it this is unavailable. Report
that and offer CLI or JSON exploration of the same graph instead.

## Procedure

1. Confirm the user asked for the dashboard in this turn. Upstream opens it
   automatically at the end of an analysis; that behavior is not adopted.
2. Confirm the runtime tier. Never run a dependency install to satisfy it.
3. Bind to loopback only. Do not expose the port on another interface or
   through a tunnel.
4. Tell the user the URL and how to stop it, and stop it when the exploration
   is done.
5. Anything read off the dashboard is navigation. A claim taken from it is
   confirmed in the file before it goes anywhere.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Launch | Opens itself after analysis | Runs only on an explicit request |
| Exposure | Default bind may be reachable | Loopback only, stop instructions given |
| Availability | Silent failure or unplanned install | Unavailable reported with an alternative |
