# ADR 009 — A public document root divides a study area and a topic belongs to exactly one area.

- Date: 2026-09-03
- Status: Active
- Target: `docs-site/catalog.json`, `docs-site/build.mjs`, `docs-site/src/`
- Related specs: [Public Docs Gateway](../specs/2026-09-03-public-docs-gateway.md), [DevOps Public Learning Path](../specs/2026-09-03-infra-specialist-public-learning-path.md), [AIOps Public Learning Path](../specs/2026-09-03-aiops-public-learning-path.md)
- Partial replacement: Structure that lists all topics directly on the first screen of [ADR 008](008-public-docs-gateway.md)

## context

The public site started with Kubernetes and expanded to 13 topics, then called `Infra Specialist`. This learning area is now named `DevOps`, which includes infrastructure as well as backend operations and deployment lifecycle. However, the public `docs-site` is not a dedicated DevOps product. When adding AIOps, putting all topics on the same plane mixes learning areas and prerequisite relationships, and then when other areas are added, the first screen becomes bloated again with a list of topics.

Personal `vault/` has verification notes for reference in infrastructure and AIOps, but it is not in the public domain. Although it can be used for structure and topic selection, it should not be auto-published or cataloged as a route.

## decision

Add layer `paths` to the catalog and root only shows study area cards. There are currently two areas: `infra` and `aiops`. Each area owns an explicit `topicIds` sequence, and every topic must belong to exactly one area.

- `#path=<id>` shows the topic order of the area and the common learning ladder.
- The existing direct link between `#topic=<id>` and `#doc=<id>` is maintained.
- Build rejects topics that do not exist, topics that are overlapped in two areas, and topics that do not belong to any area.
- The search targets public documents in all areas, and the area and topic are displayed together in the results.
- Prerequisite and follow-up relationships between topics are connected by Markdown relative links and converted to document routes when building.
- The scope of disclosure continues to be limited to explicit catalog and Git tracking Markdown. `vault/`, `REGISTRY.md`, and `_workspace/` are not automatically discovered or disclosed.

## Current content boundary

DevOps adds `트래픽 제어와 서비스 복원력` and `운영 가능한 백엔드 엔지니어링` to the existing 13 topics, resulting in 15 topics and 57 documents. The backend topic does not automatically disclose the vault's 81 notes, but reorganizes them along six axes (API contract, immutable/transaction, concurrency/capacity, distributed workflow, cache/performance, compatible deployment) and connects them to existing network·PostgreSQL·messaging·security·traffic·AIOps documents.

AIOps consists of 5 topics and 20 documents: `AI Specialist 핵심 모델과 응용`, `AI Transformation 운영 플랫폼`, `신호와 운영 토폴로지`, `이상 탐지와 근거 기반 진단`, and `승인된 자동 복구와 운영 학습`. All five training modules of AI Specialist and four operational pillars of AI Transformation are moved to the upper chapters without exception, but the original text of individual lectures and vault sentences are not posted. The model, search, GPU, MLOps, and agent execution results are connected to go back and forth between the incident evidence and the evaluation dataset, and the diagnosis and action documents return to the traffic, GitOps, security, reliability, and backend documents of DevOps. To ensure that individual items in the three vault areas do not disappear under the main axis, each roadmap has a full content linking table, and the build test checks the boundary items in each table.

## Extension: Data and Observability (2026-09-10)

The third `data-observability` path uses the same one-path-per-topic contract and preserves all existing routes. Its 17 selected chapters live under `docs/guides/data-observability/` at the user's request. The catalog already permits explicitly selected tracked Markdown there; unrelated docs and private files are not added. See the [acceptance specification](../specs/2026-09-10-data-observability-learning-path.md).

## result

- The root size follows the number of study areas, not the number of topics.
- DevOps and AIOps have independent entry points and share knowledge through internal documentation links.
- New areas can be added with a single path and a complete set of topics.
- Direct links to the topic/document of existing URL fragments are not broken.
- Catalog verification prevents area placement omission and duplication in CI.
