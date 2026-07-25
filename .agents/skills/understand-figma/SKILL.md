---
name: understand-figma
description: Analyze an approved Figma file through the Understand Anything design pipeline to extract screens, components, and tokens for design study. Use only when the user names a specific Figma file and approves sending it to api.figma.com for that run. Do NOT search for or reuse a stored token, do NOT write a token into this repository or the vault, and do NOT analyze a file the user has not named in this turn.
---

# understand-figma — Approved design file analysis

## Why

Design files carry structure worth studying alongside code. They are also
someone's private workspace, so every run here is a deliberate external
transmission rather than a capability that sits switched on.

## Before running

Read `../understand/references/adapter-contract.md`.

Runtime tier: **built package**. The Figma scripts import
`@understand-anything/core`, which needs Node 22+, pnpm 10+, and a build. That
install is blocked until separately authorized (ADR 003); report unavailable
rather than installing.

## Procedure

1. Confirm the user named the file in this turn. Never infer a file key from
   context or history.
2. State plainly what leaves the machine: the file key, that content is
   fetched from `api.figma.com`, and what the analysis will keep. Get approval
   before the first request.
3. The token comes from the environment for that run only. Do not search for
   one, do not copy it anywhere, and do not record it in this repository, the
   vault, or `REGISTRY.md`.
4. Write output to `_workspace/understand-anything/`, never into the vault.
5. Approval covers this run and this file. A later file or a later session
   needs a new approval.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Transmission | Design content sent as a side effect | File key and destination approved per run |
| Credentials | Token discovered and reused | Environment only for the run, never stored |
| Scope | Approval treated as standing | Approval bound to one file and one run |
