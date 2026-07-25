---
name: understand-explain
description: Explain a concept, flow, or component of an analyzed codebase source-first, using the Understand Anything graph to select what to read and then teaching from the code itself. Use for 이 부분 설명해줘, 이 흐름 어떻게 동작해, and understanding a component well enough to change it. Do NOT use it to produce an explanation from the graph without opening the code, and do NOT use it for Markdown notes.
---

# understand-explain — Source-first explanation

## Why

An explanation the user cannot verify against the code teaches nothing durable.
The graph picks the reading path; the explanation comes from what the code
actually says.

This harness treats user comprehension as the goal, so the output is a reading
guide as much as a summary.

## Before running

Read `../understand/references/adapter-contract.md`.

Runtime tier: **graph consumer**. Needs a graph from `understand`. Without one,
explain from the code directly and say the graph was unavailable.

## Procedure

1. Use the graph to choose the smallest set of files that carries the concept.
2. Read them. Quote the signatures, conditions, and data shapes verbatim
   instead of paraphrasing them into something tidier.
3. Explain in dependency order: what it receives, what it decides, what it
   emits, and where the edges are.
4. Name what you did not read and what therefore stays unconfirmed.
5. Hand back the reading order so the user can follow the same path.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Explanation basis | Plausible summary | Quoted code the user can re-check |
| Scope honesty | Gaps invisible | Unread parts named as unconfirmed |
| User growth | Answer replaces reading | Reading order handed over |
