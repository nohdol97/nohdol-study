# docs/ — Decision, specification, proposal, guide

This directory is a MOC (Map of Content) that connects nohdol-study's decisions and implementation standards. The single source for current operating rules is [AGENTS.md](../AGENTS.md).

## Guides

| guide | Target | substance |
|---|---|---|
| [Public learning guide](../docs-site/README.md) | English DevOps and AIOps gateway on GitHub Pages | Two learning paths, 20 topics, and 77 articles; prerequisites and follow-up reading across backend engineering, AI Specialist, and AI Transformation; search, Markdown reader, and Pages deployment |
| [Workspace Portal](../examples/workspace_portal/README.md) | Dynamic HTML site for users from `_workspace` | `_workspace/sites/<slug>/` path and explicit manifest, single server root, portal initialization/registration/inspection |
| [Mobile Telegram Study Bridge](guides/mobile-telegram-bot.md) | Smartphone Telegram ↔ Mac harness integration (read only) | Inquiry/question-and-answer surface that only reads the knowledge root, mobile Socratic learning, inline button control, MessageEntity-based flawless format rendering and local URL purification, automatic startup when launchd boots, AGENTS.md security whitelist compliance |
| [Feed Scraper](guides/feed-scraper.md) | RSS source → vault automatic collection | Separation of catalog (tracking) and selection by computer (non-tracking), `feed` stacks only titles and links, API call 0, `geeknews` summarizes/classifies after score gate, marker-based duplication prevention, launchd automatically runs |

## ADR

| ADR | date | situation | title |
|---|---|---|---|
| [009](adr/009-public-docs-root-learning-paths.md) | 2026-09-03 | active | The public document root divides the DevOps·AIOps learning area and places topics exactly in one area. |
| [008](adr/008-public-docs-gateway.md) | 2026-09-03 | Partial replacement (→009) | Learning documents by subject are deployed to GitHub Pages through an explicit catalog. |
| [001](adr/001-initial-study-harness.md) | 2026-07-25 | active | File-based study harness Phase 1 structure |
| [002](adr/002-phase2-derived-workflows.md) | 2026-07-25 | active | Phase 2 Collection·NotebookLM·Graph Derivation Workflow |
| [003](adr/003-cli-learning-integrations.md) | 2026-07-25 | Partial replacement (→004) | Project-local adoption of Understand Anything full skills and optional learning linkage |
| [004](adr/004-remove-notebooklm-export.md) | 2026-07-25 | active | Remove NotebookLM export skill — 0 cases, 763 lines Invalid compared to maintenance cost |
| [005](adr/005-egress-guard-for-external-runtimes.md) | 2026-08-01 | active | External runtime leak gate as a separate hook — the approval prompt does not ask for payload content |
| [006](adr/006-archify-explicit-use-outside-vault.md) | 2026-08-09 | active | archify is an explicit call only, output is `_workspace/` — CLI has no SVG output so notes cannot be embedded |
| [007](adr/007-single-workspace-site-portal.md) | 2026-08-16 | active | Dynamic sites for users open from a single portal, `_workspace` |

## specs

| specs | situation | Target |
|---|---|---|
| [2026-09-03-aiops-public-learning-path](specs/2026-09-03-aiops-public-learning-path.md) | implemented | AI Specialist 5 modules, AI Transformation 4 pillars → Signal/evidence-based diagnosis → 5 topics/20 documents of approved automatic recovery and DevOps cross-link/execution safety contract |
| [2026-09-03-infra-specialist-public-learning-path](specs/2026-09-03-infra-specialist-public-learning-path.md) | implemented | 57 document paths connecting Kubernetes and 14 DevOps topics, backend 6 axes, traffic control reinforcement and terminology → normal observation → failure/recovery → operation judgment contract |
| [2026-09-03-public-docs-gateway](specs/2026-09-03-public-docs-gateway.md) | implemented | Early Kubernetes 11 training documents, search/document viewer, and visibility gates on scalable topic gateways |
| [2026-07-25-phase1-study-harness](specs/2026-07-25-phase1-study-harness.md) | implemented | Installer, knowledge structure, common skills, session hooks |
| [2026-07-25-phase2-ingest-notebooklm-graph](specs/2026-07-25-phase2-ingest-notebooklm-graph.md) | implemented | Web/paper/video ingest, NotebookLM export, graph-based parser |
| [2026-07-25-phase2b-cli-learning-integrations](specs/2026-07-25-phase2b-cli-learning-integrations.md) | 2b-A~2b-D implemented, 2b-E withdrawn as ADR 004 | Understand Anything 9 types, Obsidian 4 types, NotebookLM CLI bridge |
| [2026-08-16-workspace-site-portal](specs/2026-08-16-workspace-site-portal.md) | implemented | `_workspace` single portal, site manifest, registration/verification tool |

## proposal

| proposal | result | substance |
|---|---|---|
| [2026-07-25-nohdol-study-direction](proposals/2026-07-25-nohdol-study-direction.md) | Phase 1·2 implementation, Phase 2b scope confirmed | Original Markdown, all Understand Anything skills, and optional integration with Obsidian and NotebookLM |

## examine

| examine | verdict |
|---|---|
| [2026-07-25-phase2c-pilot-status](reviews/2026-07-25-phase2c-pilot-status.md) | PaperQA2 not available, basic-memory not adopted | The index does not meet the read-only premise by modifying the note frontmatter. Search is valid, no external transfer |
| [NotebookLM CLI·Understand Anything Security Review](reviews/2026-07-25-notebooklm-understand-anything-security.md) | Notebooklm-py conditionally adopted, v0.7.3 installation pending, Understand Anything 9 types project-local safety adapter adopted |
| [Review of additional tool introduction](reviews/2026-07-25-additional-tools-review.md) | basic-memory limited pilot, PaperQA2 conditional, Obsidian 4 types adopted; memory server series pending |

## handover work

| taking over | start task |
|---|---|
| [2026-07-25 Next Session](handoffs/2026-07-25-next-session.md) | Phase 2b-A project-local exact-pin installed base |

## Change history

- [harness change history](harness-changelog.md)
