---
name: understand-chat
description: Answer a question about an analyzed codebase by querying the existing Understand Anything graph for candidate files and then confirming the answer in those files. Use for 코드베이스 질문, 이 기능 어디 있어, 어느 파일 봐야 해, and locating behavior in an unfamiliar repository. Do NOT use it to answer from the graph alone, for a repository with no graph yet (run understand first), or for questions about the curated notes of this vault.
---

# understand-chat — Graph-guided code questions

## Why

Finding where a behavior lives is a search problem; deciding what it does is a
reading problem. This uses the graph for the first and the file for the second.

## Before running

Read `../understand/references/adapter-contract.md`.

Runtime tier: **graph consumer**. It needs a graph produced earlier by
`understand`. Without one, say so and either run that skill or search the code
directly; do not answer from memory of the repository.

## Procedure

1. Query only the part of the graph the question needs. Do not load a whole
   graph file into context.
2. Collect the candidate files and symbols it points to.
3. **Open those files and read them.** The answer is finished only after this.
   State the file and line the conclusion rests on.
4. When the graph and the file disagree, follow the file and report the graph
   as stale.
5. If reading shows the candidates were wrong, say the graph misled you rather
   than shaping the answer to match it.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Locating behavior | Broad search or guesswork | Graph narrows candidates first |
| Answer basis | Generated summary | File and line confirmed by reading |
| Stale graph | Silently wrong answer | Disagreement reported, file wins |
