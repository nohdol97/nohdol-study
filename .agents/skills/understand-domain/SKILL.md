---
name: understand-domain
description: Derive the business domain view of an analyzed codebase - actors, workflows, and rules - from the Understand Anything graph, with each element traced to the code that implements it. Use for 도메인 파악, 비즈니스 로직 구조, 업무 흐름 분석, and learning what a system does rather than how it is built. Do NOT accept a domain element with no code reference, and do NOT use it for architecture or dependency questions.
---

# understand-domain — Business domain view

## Why

Reading a repository by module tells you how it is built; reading it by domain
tells you what it is for. The second is what makes the first memorable.

Domain naming is also where a model invents most freely, so every element here
must point at code.

## Before running

Read `../understand/references/adapter-contract.md`.

Runtime tier: **graph consumer**, plus `python3` for the bundled domain
extraction script.

## Procedure

1. Derive candidate actors, workflows, and rules from the graph.
2. Drop every candidate with no code reference. A plausible domain term that
   no file implements is invention, not analysis.
3. Open the implementing files for the elements you keep and confirm the
   behavior matches the name you gave it.
4. Separate what the code enforces from what a naming convention merely
   suggests, and say which is which.
5. Record open questions where the domain intent is not decidable from code -
   those belong to the user, not to a guess.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Domain model | Inferred from names | Each element traced to implementing code |
| Invention | Plausible terms slip in | Unreferenced candidates dropped |
| Certainty | Convention read as rule | Enforced and suggested reported apart |
