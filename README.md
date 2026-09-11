# nohdol-study — AI agent-based portable study harness

`nohdol-study` is a **portable AI study harness** that gives Claude Code, Codex, and Gemini Antigravity CLI a shared file contract. Captured sources live in `raw/`, verified atomic notes live in `wiki/`, and **Markdown and wikilinks (`[[ ]]`) are the source of truth**.

> 💡 **Design philosophy**: The harness repository itself does not track knowledge files. The knowledge repository path, which is different for each computer, is securely connected through an untracked symlink (`vault/`) and a local registry (`REGISTRY.md`) that point to the actual knowledge root.

---

## 🌟 Provided features and learning environment (Features)

### 1. 🏗️ Phase 1: Basic knowledge harness
- **Highly portable installation**: Select knowledge directory by installation location (personal/company profile, synchronization method) and secure bootstrapping
- **Standardized structure**: `raw/` (immutable source), `wiki/` (atomic note), `index.md` (map), `log.md` (chronology), `hot.md` (session context)
- **Note Contract**: Flat YAML front matter, wiki link, strict enforcement of source and verification status for each claim (`unverified`, `source-backed`, `primary-confirmed`, `cross-checked`, or `contested`)
- **Write point gate (`PostToolUse`)**: At the moment of saving a note, diagram render failure, Frontmatter contract violation, and uninterpreted `sources:` path are checked and corrected in the same turn. Applies on a file basis even to authors who have not gone through the skill
- **Finish Gate (`Stop`)**: Checks whether the notes written in this session have been recorded, **what points to those notes**, and whether the newly entered link is actually interpreted. The reachability judgment uses the same definition as `vault-gardening`.
- **Egress gate (`PreToolUse`)**: Blocks notebook cells containing knowledge-root paths, wikilinks, or note frontmatter. An approval prompt asks whether to run a tool; it does not inspect whether the payload contains notes. This gate therefore also runs in interactive sessions. Measurements from public datasets are allowed because they are not vault material.

### 2. 🔍 Phase 2: Multi-media collection and knowledge graph
- **Web Document Capture (`defuddle`)**: Clean Markdown immutable capture without advertisements and navigation.
- **Academic Paper Search (`paper-search`)**: arXiv·DOI-based paper search, PDF download, and publication metadata verification
- **Deep video learning (`study-video`)**: Transcript-first learning with Korean and English subtitles first. Video downloads only occur when the screen has questions to answer.
- **Deterministic Knowledge Graph (`knowledge-graph`)**: Generate deterministic JSON graph of type `article`·`topic`·`source` and verify model inference evidence
- **Meaning Search (`vault-search`)**: Search **by meaning** even if you do not know the word written in the note. Embeddings are calculated only on the loopback server (other endpoints are rejected by the script), and the index is placed outside of synchronization at `_workspace/`. When you search, only changed notes are automatically re-embedded, so you don't have to remember to rebuild. The result is not evidence, but a **candidate list**
- **Bulk Documentation Queue (`ingest` batch mode)**: Progress is calculated by **whether the note actually cites the file** rather than a checkbox, so even if the session is interrupted, it is resumed in the note.

### 3. 🧠 Phase 2b: Code/domain analysis and Obsidian integration
- **Understand Anything 9-Mode Routing (`understand`)**: Know your codebase architecture, explore feature locations, explain concepts, onboarding guide, scope of change impact, domain analysis, dashboard viewer.
- **Obsidian format and CLI integration (`obsidian`)**: Markdown extension, Bases (`.base`), JSON Canvas (`.canvas`) creation and internal routing of Obsidian CLI (4 modes)
- **Interactive diagram for presentation (`archify`)**: **Only when explicitly called** Creates a standalone HTML diagram with a pinned CLI. Since Obsidian cannot embed and the knowledge root is synchronized, the output is placed only in `_workspace/`, and the diagrams to be included in the notes are handled by `diagram` (Mermaid/D2).
- **Source and execution gates**: External tool trees are checked against `.tools/PINS.md`. Dependency installation and optional external transfers require their explicit workflow gates; a source hash does not prove runtime isolation.

### 4. 🖥️Local Dynamic Site Portal
- **Single entry point**: Place the HTML learning site you use repeatedly in `_workspace/sites/<slug>/` and search and access it in `_workspace/index.html`
- **One server**: `python3 examples/workspace_portal/portal.py serve` provides the entirety of `_workspace` once
- **Explicit exposure**: Hide knowledge graph and temporary analysis and register only sites viewed by users to `sites.json`

### 5. 🌐 GitHub Pages public documentation
[**Open the public document site directly →**](https://nohdol97.github.io/nohdol-study/)

- **Lab result examples**: Normal, failed, and recovered states carry expected or synthetic labels. See the [full documentation review](docs/reviews/2026-09-10-full-documentation-review.md) for corrections and verification limits.
- **Detailed stack mechanisms**: The [Data course](docs/guides/data-observability/00-roadmap.md) now teaches the shared curriculum's individual SQL, Spark, Kafka, dbt, OTel, governance, cloud, and AI mechanisms with worked examples. Seven local fixtures plus optional OTel/DuckDB/dbt checks reproduce results; the [depth specification](docs/specs/2026-09-10-data-course-depth.md) defines the coverage.
- **Three learning paths, 21 topics, 94 documents**: DevOps has 57 documents, AIOps has 20, and [Data & Observability](docs/guides/data-observability/00-roadmap.md) adds a 17-chapter English course from SQL and Parquet through Spark, Kafka, quality, OpenTelemetry, governance, cloud platforms, and AI evaluation. Internal links connect prerequisites and follow-up reading.
- **Connected backend and AIOps paths**: Backend follows API contracts → invariants and transactions → capacity → distributed workflows → caching and performance → compatible deployments. AIOps connects five AI Specialist modules and four AI Transformation pillars to incident evidence, diagnosis, and approved remediation.
- **Concept → execution → recovery**: Each new topic is explained starting with key terms and actual situations, and distinguishes between what the command results prove and what is not yet known. Local·Plan only·AWS optional Boundary, failure judgment, and cleanup are provided according to [spec ](docs/specs/2026-09-03-infra-specialist-public-learning-path.md)
- **Convert links to internal documents**: Rather than linking user-specified official pages to external links, evolve them into self-contained explanations with relationship/sequence diagrams, executable YAML/`kubectl` examples, failure examples, and recovery flows.
- **Integrated search and reading screen**: Title/summary/text search, URL direct link, responsive Markdown viewer and dark mode provided
- **Korean/English interface**: Header buttons switch menus, path and topic introductions, search labels, and diagram controls, with a saved preference. Document text and code remain in English. See the [language-switch specification](docs/specs/2026-09-11-document-language-switch.md).
- **Public scope gate**: Only build Git tracking Markdown specified in `docs-site/catalog.json`, reject `vault/`·`REGISTRY.md`·`_workspace/`
- **Pages artifact deployment**: Deploy only `docs-site/dist/` tested by GitHub Actions without committing the artifact.
- **Direct delivery**: General changes that have passed verification are pushed to `origin/main` without waiting for separate approval and confirmed through Pages deployment.

### 6. 📱 Mobile Telegram Study Bridge (Telegram Bot Bridge)
- **Read-only learning on the go**: Search, query, and explain existing knowledge vaults anytime, anywhere using the smartphone Telegram messenger and conduct Socratic questions and answers, but do not write, edit, or delete notes.
- **Cloud real-time synchronization**: Synchronization depends on the selected client and platform; verify arrival and conflicts on each device
- **Inline buttons and menu controls**: Instantly switch between AI models (`Gemini 3.1 Pro` ↔ `2.5 Flash`) and inference strengths (`High/Med/Low`) with the bottom left `[Menu]` button and touch buttons.
- **Structured message rendering (`MessageEntity`)**: Equipped with a defense architecture that separates and transmits style attribute arrays without exposing markdown symbols (`\`, `*`, `` ` ``) and refines local paths (`file://`)
- **Optional launchd operation**: A separately configured user LaunchAgent can start the bridge and restart it under the selected policy; verify the local installation before relying on unattended operation.
- **AGENTS.md Rule 5 security perimeter**: Environment variable injection, Chat ID whitelist, `STUDY_SURFACE=telegram` tool gate blocks vault writes/deletes and home directory sweeps

---

## 🚀 Quick Start

### Local Dynamic Site Portal

```sh
python3 examples/workspace_portal/portal.py init
python3 examples/workspace_portal/portal.py check
python3 examples/workspace_portal/portal.py serve
```

If you open `http://127.0.0.1:4173/` in your browser, you can access all registered sites. To register a new site, follow [Workspace Portal Guide](examples/workspace_portal/README.md).

### GitHub Pages public documentation

```sh
cd docs-site
npm ci
npm test
npm run build
npm run preview
```

Open `http://127.0.0.1:4174/` in your browser. The DevOps, AIOps, and Data & Observability learning paths, method of reflecting official sources as internal documents, and Page settings follow [Public Learning Guide Guide](docs-site/README.md).

### Step 1: Install harness and connect Vault
Make the following request in AI CLI (Claude Code, Codex, Gemini CLI, etc.) or run the shell script directly:

```sh
# When requested in the CLI dialog
"study-install로 이 컴퓨터에 하네스를 설치하고 vault를 연결해 줘."

# When running bootstrap directly
./.agents/skills/study-install/scripts/bootstrap.sh \
  --vault "/absolute/path/to/my-obsidian-vault" \
  --profile personal \
  --sync google-drive
```

### Step 2: Optional mobile bridge

Follow the [Telegram bridge guide](docs/guides/mobile-telegram-bot.md) for transmission approval, externally injected credentials, the required allowed private chat, and fresh-session hook verification. The current template allows all chats if `TELEGRAM_ALLOWED_CHAT_ID` is empty. Model menus and launchd setup are installation-specific.

### Step 3: Optional feed collection

Follow the [feed scraper guide](docs/guides/feed-scraper.md) for first-time setup, source selection, result examples, and scheduling. Collection writes to the knowledge root; generated lists remain a reading queue. Feed-only mode makes RSS requests but no model calls. Inject model credentials externally; never store them in a workspace `.env`.

---

## 🧩Skills Map (Skills Map)

All skills are located in the `.agents/skills/` directory, and detailed usage instructions and boundaries can be found in [Skill guide (.agents/skills/README.ko.md)](.agents/skills/README.ko.md).

```text
.agents/skills/
├── archify/ # Standalone HTML interactive diagram for explicit calls only (out of vault)
├── context7/ # Check the official documentation of the latest version of the library
├── defuddle/ # Extract public web page body markdown
├── diagram/ # Select diagram tool by structure (Mermaid / D2 / Canvas)
├── ingest/ # Collection and note-making routing by web, paper, and video media
├── knowledge-graph/ # Deterministic knowledge graph regeneration and evidence verification
├── metaskill/ # harness Self-improvement of rules, skills, installers, and specifications
├── note-writer/ # Write atomic verification note, enforce frontmatter/index policy
├── obsidian/ # Obsidian Grammar, Canvas, Bases verification and CLI control
├── paper-search/ # Open paper search/download/metadata verification
├── recall/ # Create spaced repetition review cards with source traceability
├── study-install/ # Check installation destination bootstrap and local environment
├── study-session/ # Socratic learning dialogue that teaches by asking questions
├── study-video/ # Video study with subtitles first, frame confirmation is conditional
├── understand/ # Understand Anything 9 modes internal routing
├── using-study/ # Knowledge-first session operation and session context management
├── vault-gardening/ # Check for knowledge root drift, orphans/broken links, and index hyperactivity
└── vault-search/ # Semantic search of curated notes with local embedding
```

---

## 📚 Documentation Architecture

This project's detailed architecture decisions (ADRs), step-by-step implementation specifications (Specs), and security review reports are all systematically organized in the `docs/` directory.

- **[Document Map (docs/README.md)](docs/README.md)**: Map of Content (MOC) of entire ADR, specification, and proposal documents.
- **[Open Learning Guide](docs-site/README.md)**: three paths, 21 topics, 94 documents, internal links between areas, beginner learning ladder and GitHub Pages deployment method
- **[DevOps Open Learning Path Specification](docs/specs/2026-09-03-infra-specialist-public-learning-path.md)**: Scope and verification agreement of 15 topics and 57 documents, from Linux, network, AWS to backend, traffic, operations, data, and Karpenter.
- **[Data & Observability course](docs/guides/data-observability/00-roadmap.md)**: Seventeen English chapters, a twelve-month plan, stack tradeoffs, runnable correctness fixtures, failure drills, and a single evolving platform project.
- **[AIOps Open Learning Path Specification](docs/specs/2026-09-03-aiops-public-learning-path.md)**: AI Specialist·AI Transformation Linkage and safety contract of 5 topics and 20 documents from the entire map to signals, diagnosis, and approved automatic recovery
- **[Mobile Telegram integration guide](docs/guides/mobile-telegram-bot.md)**: Guide to building a smartphone ↔ Mac harness bridge (read only — inquiry/Q&A only)
- **[Feed Scraper Guide](docs/guides/feed-scraper.md)**: Automatic collection of RSS sources, selection of sources by computer, procedure for adding new sources
- **[harness change history (Changelog)](docs/harness-changelog.md)**: Phase 1 ~ Phase 2b feature updates and architecture change records
- **Operating rules source**: [AGENTS.md](AGENTS.md) (Current shared rules to read at session start)
