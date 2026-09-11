# docs/ — Decision, specification, proposal, guide

This directory is a MOC (Map of Content) that connects nohdol-study's decisions and implementation standards. The single source for current operating rules is [AGENTS.md](../AGENTS.md).

## Guides

| guide | Target | substance |
|---|---|---|
| [Public learning guide](../docs-site/README.md) | English DevOps, AIOps, and Data & Observability gateway on GitHub Pages | Three learning paths, 21 topics, and 94 articles; prerequisites and follow-up reading across backend engineering, AI Specialist, and AI Transformation; search, Markdown reader, and Pages deployment |
| [Data & Observability Engineering](guides/data-observability/00-roadmap.md) | Data and observability specialization | Seventeen English chapters covering distributed data, quality, telemetry, lineage, managed platforms, AI evaluation, and a reproducible capstone |
| [Workspace Portal](../examples/workspace_portal/README.md) | Dynamic HTML site for users from `_workspace` | `_workspace/sites/<slug>/` path and explicit manifest, single server root, portal initialization/registration/inspection |
| [Mobile Telegram Study Bridge](guides/mobile-telegram-bot.md) | Smartphone Telegram ↔ Mac harness integration (read only) | Inquiry/question-and-answer surface that only reads the knowledge root, mobile Socratic learning, inline button control, MessageEntity rendering and local-link normalization, automatic startup when launchd boots, AGENTS.md security whitelist compliance |
| [Feed Scraper](guides/feed-scraper.md) | RSS source → vault automatic collection | Separation of catalog (tracking) and selection by computer (non-tracking), `feed` stacks only titles and links, no model calls; RSS requests remain, `geeknews` summarizes/classifies after score gate, marker-based duplication prevention, launchd automatically runs |

## ADR

| ADR | date | situation | title |
|---|---|---|---|
| [009](adr/009-public-docs-root-learning-paths.md) | 2026-09-03 | active | The public document root divides DevOps, AIOps, and Data & Observability and places topics exactly in one area. |
| [008](adr/008-public-docs-gateway.md) | 2026-09-03 | Partial replacement (→009) | Learning documents by subject are deployed to GitHub Pages through an explicit catalog. |
| [001](adr/001-initial-study-harness.md) | 2026-07-25 | active | File-based study harness Phase 1 structure |
| [002](adr/002-phase2-derived-workflows.md) | 2026-07-25 | Partially superseded by ADR 004 | Ingest and graph remain active; NotebookLM withdrawn |
| [003](adr/003-cli-learning-integrations.md) | 2026-07-25 | Partial replacement (→004) | Project-local adoption of Understand Anything full skills and optional learning linkage |
| [004](adr/004-remove-notebooklm-export.md) | 2026-07-25 | active | Remove NotebookLM export skill — 0 cases, 763 lines Invalid compared to maintenance cost |
| [005](adr/005-egress-guard-for-external-runtimes.md) | 2026-08-01 | active | External runtime leak gate as a separate hook — the approval prompt does not ask for payload content |
| [006](adr/006-archify-explicit-use-outside-vault.md) | 2026-08-09 | active | archify is an explicit call only, output is `_workspace/` — CLI has no SVG output so notes cannot be embedded |
| [007](adr/007-single-workspace-site-portal.md) | 2026-08-16 | active | Dynamic sites for users open from a single portal, `_workspace` |

## specs

| specs | situation | Target |
|---|---|---|
| [Documentation language switch](specs/2026-09-11-document-language-switch.md) | implemented; extended | Korean/English interface and persistence; article scope extended by bilingual reading |
| [Bilingual reading and terminology](specs/2026-09-11-bilingual-reading.md) | implemented | All 94 paired articles, three reading modes, bilingual search, terminology, and translation publication gates |
| [Data course technical depth](specs/2026-09-10-data-course-depth.md) | implemented | Per-mechanism explanations, source coverage map, worked examples, local SDK/SQL/dbt verification, and managed-platform exercises |
| [Documentation review specification](specs/2026-09-10-documentation-review.md) | implemented | Whole-catalog review, labeled results, regression checks, and historical status clarification |
| [2026-09-10-data-observability-learning-path](specs/2026-09-10-data-observability-learning-path.md) | implemented | Seventeen source-reviewed chapters in docs/, third public path, executable fixtures, browser checks, and Pages deployment |
| [2026-09-03-aiops-public-learning-path](specs/2026-09-03-aiops-public-learning-path.md) | implemented | AI Specialist 5 modules, AI Transformation 4 pillars → Signal/evidence-based diagnosis → 5 topics/20 documents of approved automatic recovery and DevOps cross-link/execution safety contract |
| [2026-09-03-infra-specialist-public-learning-path](specs/2026-09-03-infra-specialist-public-learning-path.md) | implemented | 57 document paths connecting Kubernetes and 14 DevOps topics, backend 6 axes, traffic control reinforcement and terminology → normal observation → failure/recovery → operation judgment contract |
| [2026-09-03-public-docs-gateway](specs/2026-09-03-public-docs-gateway.md) | implemented | Early Kubernetes 11 training documents, search/document viewer, and visibility gates on scalable topic gateways |
| [2026-07-25-phase1-study-harness](specs/2026-07-25-phase1-study-harness.md) | implemented | Installer, knowledge structure, common skills, session hooks |
| [2026-07-25-phase2-ingest-notebooklm-graph](specs/2026-07-25-phase2-ingest-notebooklm-graph.md) | Implemented; NotebookLM withdrawn by ADR 004 | Web/paper/video ingest and graph parser |
| [2026-07-25-phase2b-cli-learning-integrations](specs/2026-07-25-phase2b-cli-learning-integrations.md) | 2b-A~2b-D implemented, 2b-E withdrawn as ADR 004 | Understand Anything 9 types, Obsidian 4 types, NotebookLM CLI bridge |
| [2026-08-16-workspace-site-portal](specs/2026-08-16-workspace-site-portal.md) | implemented | `_workspace` single portal, site manifest, registration/verification tool |

## proposal

| proposal | result | substance |
|---|---|---|
| [2026-07-25-nohdol-study-direction](proposals/2026-07-25-nohdol-study-direction.md) | Historical proposal; follow current ADRs and skills | Original Markdown, all Understand Anything skills, and optional integration with Obsidian and NotebookLM |

## Reviews

| Review | Verdict |
|---|---|
| [Full documentation review](reviews/2026-09-10-full-documentation-review.md) | All 94 learning documents and supporting docs; corrections, result examples, and verification limits |
| [2026-07-25-phase2c-pilot-status](reviews/2026-07-25-phase2c-pilot-status.md) | PaperQA2 not available, basic-memory not adopted | The index does not meet the read-only premise by modifying the note frontmatter. Search is valid, no external transfer |
| [NotebookLM CLI·Understand Anything Security Review](reviews/2026-07-25-notebooklm-understand-anything-security.md) | Historical exact-version audit; NotebookLM subsequently withdrawn by ADR 004 |
| [Review of additional tool introduction](reviews/2026-07-25-additional-tools-review.md) | Historical candidate review; subsequent pilot rejected basic-memory and did not run PaperQA2 |

## handover work

| taking over | start task |
|---|---|
| [2026-07-25 Next Session](handoffs/2026-07-25-next-session.md) | Archived receipt, not an active implementation queue |

## Change history

- [harness change history](harness-changelog.md)
