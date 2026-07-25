---
name: understand-onboard
description: Produce a dependency-ordered learning path through an analyzed codebase, with source links and checkpoints, from the Understand Anything graph. Use for 온보딩 가이드, 어디부터 봐야 해, 학습 순서, and entering a new repository or handing one to someone else. Do NOT use it as a substitute for reading the code, and do NOT emit a walkthrough whose steps you have not opened.
---

# understand-onboard — Learning path through a repository

## Why

Entering a repository fails on ordering more than on volume. This turns the
dependency structure into a sequence: what to read first so the next file makes
sense.

## Before running

Read `../understand/references/adapter-contract.md`.

Runtime tier: **graph consumer**. Needs a graph from `understand`.

## Procedure

1. Take the dependency order from the graph and cut it to a path a person can
   actually finish.
2. Open each step's entry file before writing that step. A walkthrough that
   points at code nobody opened is where stale graphs do the most damage.
3. For each step record why it comes here, the file to open, and what the
   reader should be able to explain afterwards.
4. Mark the boundaries where the path stops and what remains unexplored.
5. When the path is worth keeping, hand it to `note-writer` with the commit or
   version it was derived from, so a later reader knows when it was true.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Ordering | Alphabetical or arbitrary entry | Dependency order a reader can follow |
| Step validity | Steps generated from a snapshot | Entry file opened before the step is written |
| Durability | Advice expires silently | Path recorded with its source version |
