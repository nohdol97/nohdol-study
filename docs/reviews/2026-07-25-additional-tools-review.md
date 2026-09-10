# nohdol-study Review of additional tool introduction

> Historical review: the candidate decisions and machine observations below are dated 2026-07-25. The [completed pilot](2026-07-25-phase2c-pilot-status.md) subsequently rejected basic-memory under the non-modifying corpus requirement; PaperQA2 was not run. This is not an installation recommendation or current capability inventory.

- Date: 2026-07-25
- Scope: local retrieval, paper RAG, agent memory/graph, Obsidian skill·API,
  spaced repetition, diagram
- Judgment criteria: nohdol-study's actual learning utility, Markdown source-of-truth preservation,
  Evidence tracking, installation portability, external transmission, operational complexity

## conclusion

| candidate | verdict | next action |
|---|---|---|
| basic-memory | Phase 2c limited pilot adoption | Index the designated corpus with a read/search focus and compare the original hash and search quality |
| PaperQA2 | Conditional adoption | Used after provider/transmission approval in in-depth query of user-specified paper bundle |
| kepano/obsidian-skills | 4 types adopted | Introduced project-local with exact pin for markdown, bases, json-canvas, and obsidian-cli |
| spaced-repetition | Phase 3 adoption | Recall Markdown format designed to be plug-in compatible |
| D2·Mermaid·JSON Canvas·matplotlib | adopted | Implementation of `diagram` skill as a router for each purpose |
| Graphiti | hold | Reexamine when temporal fact/history queries require repetition |
| Mem0 | hold | Reconsideration when personalized agent memory becomes an explicit request |
| Cognee | hold | Reexamine when multiple data memory pipeline and agent trace memory becomes necessary |
| Kuzu | Excluding new introductions | Review only maintained candidates instead of archived DB |
| Obsidian Local REST API/MCP | Hold default route | Only when there is a live-app/remote client request that is not possible with the official CLI. |

## 1. basic-memory — small limited pilot

Basic Memory keeps the Markdown file as the original and SQLite as the derived index.
Use it. Provides search and note inquiry in CLI and file changes with watcher
You can synchronize. This structure is “Markdown original, DB derivative” by nohdol-study
It fits the principle.

The previous “after 100 curated notes” condition included the exact amount of time the tool becomes useful.
There is no evidence. Instead of counting notes, judge by the following small experiment.

1. Only the vault subpath specified by the user is targeted.
2. Compare the Markdown path and SHA-256 set before and after execution.
3. In Pilot, original change functions such as `bm format`, automatic write, and reset are available.
   Place it outside the wrapper allowlist.
4. Currently `knowledge-graph`, Understand with pre-made facts, relationships, and denial questions
   Anything, basic-memory precision, source tracking, latency, noise
   Compare.
5. If the results do not improve, you should be able to completely withdraw by clearing the SQLite index.
   Do it.

Basic Memory is AGPL-3.0, so copy and modify the upstream code to this repository.
Instead of deploying, it is called using a separately installed tool.

Evidence:

- [Technical information](https://docs.basicmemory.com/reference/technical-information)
- [CLI reference](https://docs.basicmemory.com/reference/cli-reference/)
- [Local CLI basics](https://docs.basicmemory.com/local/cli-basics)
- [GitHub repository](https://github.com/basicmachines-co/basic-memory)

## 2. PaperQA2 — for in-depth questioning of papers

PaperQA2 is a paper RAG that constructs answers from PDF and text corpus and adds citations.
It's a tool. The routine meanwhile ingest is currently `paper-search` and `note-writer`.
Sufficient, but has complementary value when repeatedly comparing methods, results, and limitations of multiple papers.
there is.

The default setting is to use an external model·embedding provider. Corpus before execution,
Provider, shows whether external transmission is available and is approved. The answer's citation is in the PDF
Check the original text again and use the PaperQA answer itself as evidence in the verified note.
No.

Evidence:

- [FutureHouse PaperQA2](https://github.com/Future-House/paper-qa)

## 3. Obsidian skills and API

The next four of `kepano/obsidian-skills` directly help with file-based learning, so
adopt.

- `obsidian-markdown`: Create Obsidian wikilink, embed, callout, properties
- `obsidian-bases`: Create `.base` YAML view·filter·formula
- `json-canvas`: Creating knowledge maps in open JSON Canvas 1.0 format.
- `obsidian-cli`: Search·file·property·command operations via official CLI

The upstream `defuddle` skill is currently nohdol-study's immutable capture,
evidence, authenticated-source It is simpler than the prohibition boundary, so it is not replaced.
The 4 skills are not user-global, but project-local in the exact commit.
Install from source.

The official Obsidian CLI requires the Obsidian 1.12 installer and a running app.
2026-07-25 `/Applications/Obsidian.app` on this Mac is 1.10.6, so currently
Only CLI is `unavailable` and has no effect on Markdown/Bases/Canvas skills.

The Local REST API plugin uses an API key and self-signed HTTPS or loopback HTTP,
It requests Obsidian to be running and even exposes file changes and command execution. official
Because there are no remote client or live app metadata needs that the CLI cannot meet.
Do not put it in the default path.

Evidence:

- [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills)
- [Obsidian CLI help](https://obsidian.md/help/cli)
- [Obsidian Bases syntax](https://obsidian.md/help/bases/syntax)
- [JSON Canvas 1.0](https://jsoncanvas.org/spec/1.0/)
- [Obsidian Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api)

## 4. Graphiti·Mem0·Cognee·Kuzu

It's not that the three memory/graph tools are functionally unusable, but because they are faster than current needs.
It is held back because the operational layer is large.

- Graphiti is suitable for temporal knowledge graphs, but Neo4j, FalkorDB or
  A graph backend and LLM provider such as Neptune are required.
- Mem0 open source is an agent memory that combines LLM, embedder, and vector store.
- Cognee is a memory that bundles vector, graph, relational layers and model settings.
  It is a pipeline and can even capture agent interactions.

Currently, the core of nohdol-study is user-owned Markdown and evidence for each claim.
When permanent agent memory is added, “Why was it remembered?” and deletion, synchronization, and external transfer
Even policies must be operated separately. temporal fact history, personalized agent memory,
Multiple data/trace memories are re-examined individually when actual repetition is required.

Kuzu is excluded from the new DB selection as the official repository is archived in 2025-10.
This is not a ban on file types or existing data, but rather a new core dependency.
It means not choosing.

Evidence:

- [Graphiti](https://github.com/getzep/graphiti)
- [Mem0 open-source overview](https://docs.mem0.ai/open-source/overview)
- [Cognee installation](https://docs.cognee.ai/getting-started/installation)
- [Kuzu repository](https://github.com/kuzudb/kuzu)

## 5. Review and diagram

`obsidian-spaced-repetition` contains questions/answers, clozes, and note reviews in Markdown.
Because it can be preserved, it is suitable for Phase 3 `recall` output. Plugin installation is
It is optional for the installation location using Obsidian, and the review schedule is not included in harness Git.
No.

Diagrams are not unified as a single tool.

- Mermaid: A basic text diagram that renders directly within Obsidian.
- D2: Rendering large architectures from CLI to SVG
- JSON Canvas: Knowledge map linking vault notes
- matplotlib: SVG that requires numerical accuracy such as coordinates, trajectory, and 3D

D2 can convert text to SVG without a browser, but it is currently installed on this Mac.
There is not. Installs as an optional dependency while implementing the `diagram` skill.

Evidence:

- [Obsidian Spaced Repetition](https://github.com/st3v3nmw/obsidian-spaced-repetition)
- [D2 installation](https://d2lang.com/tour/install/)
- [D2 FAQ](https://d2lang.com/tour/faq/)
- [Mermaid](https://github.com/mermaid-js/mermaid)
