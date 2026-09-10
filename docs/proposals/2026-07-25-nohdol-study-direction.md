# nohdol-study direction review — study harness design proposal

> Historical design proposal: implementation-state labels and local observations below reflect the proposal date. Phase 2b and Phase 3 were subsequently implemented; NotebookLM export was withdrawn and basic-memory was not adopted. Consult the [current documentation map](../README.md) and operating rules instead of treating the old priority table as pending work.

- Date: 2026-07-25 / Status: **Phase 1·2 implemented, Phase 2b scope confirmed/not implemented** (Phase 2c·3 awaiting)
- Purpose: A harness that helps accumulate and study knowledge in various fields such as robots and physical AI as well as codes. Obsidian integration + graph utilization, operation of both Claude Code and Codex, symlink-based porting.
- Analysis targets: claude-obsidian (AgriciDaniel) · superpowers (obra) · Understand-Anything (Egonex-AI) · claude-video (bradautomates) · defuddle (kepano) · context7 + additional candidate research
- Judgment criteria: Without inheriting the acceptance/rejection conclusions of other repositories, the
  It is actually helpful for the goal of **learning in various fields, verifying evidence, and accumulating knowledge**.
  Evaluate.

## 1. Key discovery — two repositories converge on the same pattern

claude-obsidian and Understand-Anything(/understand-knowledge) independently converged on the **Karpathy LLM wiki pattern**:

```
raw/ # Immutable original text (paper PDF, transcript, clipping original — absolutely prohibited)
wiki/ # Knowledge page created and managed by LLM ([[위키링크]] Markdown)
index.md # master index (category catalog)
log.md #append-only chronology
hot.md # ~500 tokens hot cache (loaded at session start)
```

This should be the basic form of the nohdol-study knowledge repository. evidence:
- **Obsidian Native**: `[[위키링크]]` + flat YAML frontmatter = Obsidian graph view comes for free.
- **Tool Neutral**: Both Claude and Codex work with just direct file manipulation (Read/Write/Grep) — No MCP, REST API, or server required.
- **Graph is derivative**: Wikilink is the original graph, JSON/SQLite index is
  It is a derivative that can be regenerated at any time. Markdown is the source of truth and DB is
  The principle of derived index is set as the standard for this project itself.

**Separate graph servers (Neo4j, etc.) are not currently introduced as basic dependencies.**
Graph operations are performed using ① Wikilink and the current deterministic parser, and ② Understand Phase 2b.
It uses Anything typed graph as the base layer. SQLite on basic-memory
The index is a local search layer that does not break this principle, so it can be piloted with a small scope.
Take actual measurements. Kuzu excludes new dependencies as the repository is archived in 2025-10.

## 2. Skeleton — nohdol-study structure

Import the verified structure as is:

```
nohdol-study/
├── AGENTS.md # single original (English — model-read surface, same ADR 030 principle)
├── AGENTS.ko.md # Korean digest view
├── CLAUDE.md # @AGENTS.md import + Claude-specific anchor
├── REGISTRY.md # Untracked — By installation location (vault path/field registry/profile)
├── .agents/ # single source: skills/ hooks/ (+ agents/ if necessary)
├── .claude/ # Symlink layer (agents→../.agents/agents, skills→../.agents/skills) + settings.json
├── .codex/ # Codex parallel layer (config.toml inline hook + agents/*.toml adapter if necessary)
├── docs/                  # README(MOC) + adr/ + proposals/ + specs/
├── vault/ # Untracked symlink → Actual Obsidian vault (§3 below)
└── _workspace/ # Untracked session output
```

- **study-install skill**: Simlink verification → knowledge root·profile·synchronization method
  Interview → Create vault symlink → Create REGISTRY.md. Phase 1 is non-dependent
  It only reports the status of the tool. The actual installation of defuddle, thesis, and video tools is
  Added when adopting the Phase 2 pipeline.
- **All this repository tracks is harness** — knowledge that varies depending on where you install it
  The file (vault) is left untracked to ensure portability.

## 3. Vault Strategy (Decided)

- Select the knowledge root from `study-install` for each installation location. Without Obsidian
  Computers can also use general directories as knowledge roots.
- This computer retains the existing Obsidian vault root synced by Google Drive.
  It is used and connected via `vault/` untracked symlink. Batch new rules into existing notes
  Instead of retroactively, the rules apply starting from new knowledge under `raw/`·`wiki/`.
- Whether or not to track Git in the knowledge repository is a policy for each installation location. In the harness repository
  Never include it and the installer will not automatically initialize vault Git.

## 4. Decision on adoption by repository

| Target | verdict | summary of evidence |
|---|---|---|
| **claude-obsidian** | **Porting only the rules** (General installation rejected) | Best as an architectural blueprint: hot.md hot cache+hooks, raw/wiki separation, flat YAML schema (type/status/created/related/sources — status: seed→developing→mature→evergreen), index hierarchy, ingest checklist, multi-agent symlink wiring. Reason for rejection: 2-month maintenance suspension (last push 2026-05-28), one-person project, mixing of marketing content, third-party plug-in bundle. MIT, so you can freely extract the rules and scripts |
| **superpowers** | **Pattern only ported** (general installation rejected) | All 14 skills are for coding, 0 study skills. Patterns to be ported: ①SessionStart bootstrap (`using-study` meta-skill injection — "Check note skills when encountering new knowledge, search existing notes first when asked") ②SDO description rule ("Use when + trigger only, do not summarize workflow") ③Separate tool-neutral body + tool mapping ④TDD-style skill verification of writing-skills ⑤Socratic structure of brainstorming → Modified with "Learning Conversation" skill |
| **Understand-Anything** | **Adoption of all 9 skills — Phase 2b integration** | Code repositories, business domains, design changes, Figma, and the Markdown knowledge base are all materials that nohdol-study can study. `/understand`, `-chat`, `-dashboard`, `-diff`, `-domain`, `-explain`, `-figma`, `-knowledge`, and `-onboard` are all provided. However, the main trace/global symlink of the upstream installer and the current monorepo dependency status are not accepted as is. Install project-local with an exact commit, be sure to check graph answers by re-opening the original text, and limit external calls to dashboard and Figma to explicit execution. |
| **claude-video** | **Adoption — Awareness Hierarchy + Top Skills** | `/watch` only recognizes and does not leave a permanent note — a void that study will fill. `study-video` Skill (2-pass): ①Understand the entire low-cost system with `--detail transcript` → ②Create only important sections with `--start/--end`+`--timestamps` cue frame → ③Create a note copying frontmatter+timestamp link+key frames to vault attachments. **Korean subtitle patch required**: Hard coding of `--sub-langs "en.*"` in download.py → `"ko.*,en.*"` (If not patched, Korean lectures will be omitted as paid Whisper). External transmission of Whisper audio follows nohdol-study's explicit permission rules. |
| **defuddle** | **Adoption** (harness skill port + expansion) | CLI integrated into the main body (defuddle-cli is an archive). `defuddle parse <URL> --md -f -o vault/...` Obsidian-ready notebook with single-line frontmatter. Callouts, formulas (MathML → LaTeX), and code blocks are normalized to Obsidian grammar — advantageous for technology articles. **1 fix during porting**: `-p` (single attribute extraction, name argument required) on line 25 of existing SKILL.md is error — `-f` is correct for markdown with metadata. Web clipping→expand to the ingestion of the ingest pipeline |
| **context7** | **Adoption** (Importation of harness skill as is) | Searching library/framework documents while studying is the same need in study. The fallback (WebFetch/WebSearch) design has been completed, so no modifications are required. MCP registration is already global within the user scope. |

### 4-1. Understand Anything Reexamination Conclusion

This project includes not only knowledge notes, but also code base, product domain, change history,
Figma design is also studied. Therefore, all 9 skills of upstream are
Valid.

| skill | Use in nohdol-study | execution boundary |
|---|---|---|
| `understand` | Convert code repositories to be studied into structure, flow, and concept graphs | Node 22+·pnpm 10+ preparation and execution after dependency audit |
| `understand-chat` | Navigate the graph to find the relevant source text for your question | Before answering, read the source file directly. |
| `understand-dashboard` | Local visualization of large graphs | Run localhost viewer only when requested by the user instead of running it automatically |
| `understand-diff` | Learn about the impact of code changes on concept and flow | The diff overlay is derivative and does not replace the judgment of the original text. |
| `understand-domain` | Learn user and business flows from code | The inferred flow is compared with the code evidence. |
| `understand-explain` | In-depth explanation of specific concepts and flows in a source-first manner | Graph summary alone is not conclusive |
| `understand-figma` | Connect Figma design with product and code learning | Only when explicitly approved to transfer `FIGMA_TOKEN` and `api.figma.com` |
| `understand-knowledge` | Explore claim·source·topic connection of `raw/`·`wiki/` | Add evidence·confidence·verification to semantic edge |
| `understand-onboard` | Learning sequence and walkthrough generation for unfamiliar repositories | Generated documents are marked as derived learning material |

“Adopt the entire skill” and “run the upstream installer as is” are not the same decision.
The installer clones or pulls the main branch and places multiple items under `~/.agents/skills` and other locations.
Replace with `ln -sfn`. nohdol-study does not track exact release/commit
Install it in the project-local tool path and install the 9 skill adapters that this project will expose.
Run through. This allows the version to be reproduced in each installation location while maintaining the global status of other projects.
It does not cover skill.

Knowledge Mode additionally complements:

- An explicit wikilink graph is regenerated deterministically.
- Implicit claims and edges include original text file, evidence section, extraction method, confidence, and
  Leave a verification status.
- When analyzing the vault, the derivatives are redirected to the untracked `_workspace/` and the final
  Do not duplicate the full text of your notes in the graph.
- When analyzing a code project, you can use `.ua/` in the target repository, but before running
  Check the ignore status and writing range.

The current upstream v2.9.0 knowledge parser test was `8 passed, 1 skipped`,
This computer's `wiki/` has only one document, so it is detected in upstream's `md_count >= 3` detection.
It fails. Additionally, the v2.9.0 full production lock audit included high 10 cases.
There are 21 cases, so do not install Node-based skills right now. Phase 2b is
project-local pin, exact lock, audit, and output boundary adapter for only the required package
After completion, activate 9.

## 5. Additional introduction candidates (direct research)

| candidate | verdict | summation |
|---|---|---|
| **basic-memory** (basicmachines-co) | **Adoption — Phase 2c limited pilot** | It uses Markdown as the source of truth, uses SQLite as a reproducible local index, and provides CLI search. The arbitrary gate of 100 notes is removed. Tests focus on read/search in the specified small range of the existing vault and compares the original hash, search accuracy, delay, and noise with the current parser/UA. `bm format`, automatic write/reset is prohibited in pilot. Since it is AGPL-3.0, the code is not vendored to the repository. |
| **paper-search-mcp** (openags) | **Adoption** | Search, download, and text extract multi-source papers such as arXiv, **MCP·CLI·Skills triple interface** — Tool neutral. Entry to the thesis pipeline for robot/physical AI study: Search/download (CLI) → raw/save → note-making skills. **Guardrail required**: Paper text is treated only as data (prompt injection defense — borrowing the “untrusted data” explicit pattern from Understand-Anything) |
| **spaced repetition** | **Adopted (lightweight, Phase 3)** | Skill to extract flashcard candidates from notes into specified format markdown + choice of obsidian-spaced-repetition plugin (FSRS, plain file in vault) or Obsidian_to_Anki CLI. Anki MCP develops interactive reviews when demand arises. |
| **PaperQA2** | **Conditional acceptance — In-depth paper inquiry** | Provides RAG with citations in PDF/text bundle. It is used only for deep comparison of a specific corpus of `raw/papers`, and the original text can be sent using the basic OpenAI model and embedding, so the provider and transmission range are approved. It is a complementary product when a local index that is more reproducible than NotebookLM is needed. |
| **kepano/obsidian-skills** | **4 types adopted** | `obsidian-markdown`, `obsidian-bases`, `json-canvas`, and `obsidian-cli` are introduced as project-local. Upstream `defuddle` has weaker evidence and immutable capture rules than the current nohdol-study skill, so it is not introduced in duplicate. The official Obsidian CLI requires App 1.12.7+ and the app running, and is not yet available in 1.10.6 on this Mac. |
| **Graphiti** | **Pending — temporal graph to be reviewed on demand** | It is strong in entity/fact changes over time and agent memory, but requires Neo4j/FalkorDB/Neptune and LLM provider. Pilot only when the time-axis knowledge query is repeated in the learning notes. |
| **Mem0** | **Pending — Personalized agent memory to be reviewed on demand** | It is an agent memory layer that combines LLM, embedder, and vector store. The operational layer is larger than the document learning/evidence tracking that is needed now. |
| **Cognee** | **Pending — Multi-data memory pipeline to be reconsidered on demand** | Vector·graph·relational layers and model settings are operated together. It is excessive for the current file-based learning, and I will look at it again if there is an explicit need to remember prompts and tool traces. |
| **Kuzu** | **Excluding new introductions** | The official repositories are archived 2025-10 and do not select new dependencies as maintained. |
| **Obsidian Local REST API/MCP** | **Hold default route** | It requires app residency, API key, self-signed HTTPS or loopback HTTP, and has a large surface for writing notes and executing commands. Reexamined only when live-app/remote client needs arise that the official Obsidian CLI cannot meet. |

Detailed evidence and reexamination conditions
[Record additional tools review](../reviews/2026-07-25-additional-tools-review.md).

## 5-1. Diagram/picture tool (additional verification on 2026-07-25)

Architecture diagram/picture creation tool when writing documents and notes. Judgment criteria: Obsidian rendering > LLM text generation suitability > CLI portability.

| use | equipment | Judgment evidence |
|---|---|---|
| **Basic** (flow, sequence, state diagram, general structure diagram) | **Mermaid** (Code Fence) | Obsidian native rendering (v11.13.0 bundle from 2026-07 release — mindmap·timeline·C4·architecture-beta), **dependency 0** (viewer built-in rendering, so no binary required), LLM generation optimal, GitHub·Claude Code·Codex brute-force operation |
| **Complex architecture** (15 nodes including robot SW stack+/3 layers of overlap+) | **D2 + ELK → SVG Embed** | Go single binary (MPL-2.0, 24.8k★ active), ELK layout ensures quality at scale where Mermaid falls apart, sketch mode. The official Obsidian plugin is in neglected condition, so it is used as **`d2 in.d2 out.svg` → `![[...]]` embed** pipeline. CLI returns syntax errors immediately, making it ideal for agent self-correction loops |
| **Knowledge Map** (Concept Relationship Map) | **JSON Canvas (.canvas)** | Obsidian native infinite canvas, open specification 1.0 (MIT), pure JSON and can directly reference vault note file nodes. The anti-overlapping grid and reading order are specified in the adopted `json-canvas` skill. |
| **Math/Geometry Drawing** (trajectory, coordinate system, transformation, 3D kinematics) | **matplotlib → SVG embed** (fallback to direct SVG creation for simple schematics, MathJax for formulas) | Accurate coordinates, curves, and 3D can only be trusted with script rendering. Create Python script → Save SVG → Embed |

**Not to be introduced**: PlantUML (JVM+Graphviz dual runtime — a direct violation of portability), draw.io (GUI essence, headless export to Electron/xvfb is heavy), Excalidraw direct JSON generation (coordinate-specified JSON, so unguided LLM output is low quality + persistence warning lights for projects with 1 Obsidian plugin — mermaid-to-excalidraw conversion path if you need a hand-drawn feel), Graphviz standalone (upwards compatible with D2 ELK), manim (overkill for static notes), tldraw (wait and see).

**Operating Rules**: ①Image output is unified as `assets/` sub-SVG next to the note,
②Mermaid→D2 promotion criteria were stipulated in the `diagram` skill, ③Obsidian adopted it
Four types of skills are provided through project-local installation of exact commit, and global skills are provided by
Do not overwrite.

## 5-2. NotebookLM CLI revisited

Web UI automation continues to be a non-goal. Instead, use the CLI of `notebooklm-py`
**Optional consumer bridge** attached after `notebooklm-export` to Phase 2b
adopt. This path includes notebook creation, source upload, queries, quizzes, flashcards, etc.
Infographic creation and downloading can be done from CLI.

As a result of our security review, immediate automatic installation of the current stable release v0.7.3 is prohibited.
put on hold Repository latest code contains download redirect every-hop verification
It is not in the v0.7.3 tag, and there is a vulnerable `click 8.3.1` in the release lock.
browser/cookies dependencies re-interpreted with the latest acceptable ranges are known to be
There were no vulnerabilities, but the risks of unofficial Google internal API, bearer cookie, and account restrictions were
It remains. Detailed judgment and installation gate
[Security Review](../reviews/2026-07-25-notebooklm-understand-anything-security.md) and
[Following ADR 003](../adr/003-cli-learning-integrations.md).

## 6. Skill Roster

| skill | role | source |
|---|---|---|
| `study-install` | New machine bootstrap (symlink·tool·vault·REGISTRY) | itself |
| `using-study` | Session Bootstrap Metaskill (Hook Injection) | superpowers pattern |
| `ingest` | Source type routing (web → defuddle, paper → paper-search, video → study-video) → raw/ storage → note creation → index·log·hot update checklist | claude-obsidian ingest protocol |
| `note-writer` | Note convention enforcement (frontmatter schema, wikilink, atomicity, contradiction/gap callout) | claude-obsidian WIKI.md equivalent — study's doc-writer |
| `study-session` | Socratic learning dialogue (one question at a time, comprehension check gate, result notes) | superpowers brainstorming mods |
| `study-video` | Lecture video → Note 2-pass pipeline | claude-video top skills |
| `defuddle` / `context7` | Web body extract/library document | Integrate external tools into nohdol-study rules |
| `understand-*` 9 types | Code·Domain·diff·Onboarding·Explanation·Query·dashboard·Figma·Knowledge graph learning | Understand Anything project-local adapter |
| `knowledge-graph` | explicit deterministic graph implemented; Accuracy and quality standards for UA knowledge graph | Understand Anything knowledge + existing standard parser |
| `notebooklm-export` | Verification snapshot implemented; Optional CLI upload/generate/download bridge extends Phase 2b | self export + notebooklm-py |
| `obsidian-markdown` / `obsidian-bases` / `json-canvas` / `obsidian-cli` | Use Obsidian syntax, dynamic views, canvas, and official CLI | kepano/obsidian-skills project-local pin |
| `diagram` | Document/note diagram creation (Mermaid basic, 15 nodes+/nested 3 levels+ → D2→SVG, knowledge map → JSON Canvas, math figure → matplotlib→SVG — §5-1 promotion rules) | new |
| `vault-gardening` | Periodic index/link matching/orphan note inspection | new |
| `recall` (Phase 3) | Extract and review flashcards | SR lightweight path |

The hook uses Claude `settings.json` and Codex `config.toml` inline settings in parallel.
Load hot.md in SessionStart + inject using-study, hot.md in Stop/wrapup
Induce renewal.

## 7. Step-by-step roadmap

1. **Phase 1 — Skeleton (complete)**: Directory·Symlink·AGENTS.md·docs MOC·study-install·note-writer(protocol)·vault connection.
2. **Phase 2 — 3 types of ingest + reference graph (complete)**: defuddle·paper-search·study-video, verification NotebookLM export, explicit wikilink deterministic graph.
3. **Phase 2b — project-local learning integration (adopted/not implemented)**: 9 Understand Anything skills, 4 Obsidian skills, NotebookLM CLI bridge. Dashboard only allows explicit execution, and Figma·NotebookLM transfer places an approval boundary.
4. **Phase 2c — Search/Paper In-Depth Pilot**: Basic-memory is compared in a small read/search range, and PaperQA2 is conditionally executed only on the user-specified paper corpus.
5. **Phase 3 — Learning loop (not implemented)**: Implement in the order `diagram` → `study-session` → `vault-gardening` → `recall`, and review the boundary score afterwards.

### 7-1. Remaining tasks and priorities

| priority | work | Completion criteria |
|---|---|---|
| P0 | Understand Anything Adopt all 9 and document security perimeter | direction·ADR·security review·execution specifications refer to the same decision |
| P1 | Project-local exact-pin installer implementation of UA and Obsidian skills | Automatic pull of upstream main·Record source commit·license·hash·tool status to REGISTRY without global symlink |
| P1 | Fix and audit UA Node dependency in required package units | Node 22+·pnpm 10+ confirmed, high vulnerability 0 or explicitly approved by risk, global skill unchanged before and after installation |
| P1 | Added 9 UA skill adapters and execution routing | Can call each upstream skill and pass source-first·output·dashboard·Figma boundary tests |
| P1 | Expand `knowledge-graph` based on upstream knowledge schema | Currently 1 `wiki/` is also detected, output path injection, deterministic explicit graph, body not included, upstream fixture + local regression pass. |
| P1 | Add semantic enrichment as a separate opt-in step | Each entity/claim/implicit edge has an evidence anchor·confidence·verification·extractor, and prompt injection phrases are processed only as data. |
| P1 | Actual creation of an Understand Anything derived graph from the current vault | Original Markdown byte/hash immutable, calculated only at `_workspace/`, reporting missing/orphan/typed relationships |
| P1 | `notebooklm-py` safe release gate and CLI wrapper implementation | Release with redirect fix or fixed audited exact commit, 0 vulnerable dependencies, install base+only minimum extra required |
| P1 | Connect the NotebookLM consumer bridge behind the export packet | Prohibit direct vault symlink upload, check packet manifest, create/upload/generate/download after approval for transmission, save result `_workspace/` |
| P1 | NotebookLM authentication/change protection | Dedicated profile, 0600/0700 confirmation, master-token·MCP/server·impersonate prohibited, public share/delete/external transmission explicitly approved |
| P1 | Introducing 4 types of Obsidian skills | markdown/bases/canvas format validation, CLI only shows as available for app 1.12.7+ |
| P2 | basic-memory limited pilot | Index only the specified path, immutable the original hash, search fixture without write/format/reset, compare with parser·UA |
| P2 | PaperQA2 on-demand wrapper | Check designated corpus·provider·external transmission and re-verify citation results with original PDF |
| P2 | `diagram` skill implementation | Reproduce Mermaid basics, image/SVG provenance, and Physical AI document picture paths without a browser. |
| P2 | `study-session` Implementation | Check understanding one question at a time, preserve incorrect answers/uncertainties, and save selection of result notes |
| P2 | `vault-gardening` Implementation | Non-destructively checks for index/log/hot, broken links, orphans, and duplicate titles |
| P3 | `recall` and spaced repetition implementation | Only cards that can verify answers with original text evidence are generated, and schedule data is local to the installation site. |
| gate | Graphiti·Mem0·Cognee revisited | When one of temporal graph·agent personalization·multiple data memories becomes an actual repetition request |
| gate | Obsidian REST/MCP revisited | When a live-app or remote client request arises that cannot be resolved with the official CLI |

### 7-2. Contrast implementation of all existing direction items

| area | Result of review | follow up |
|---|---|---|
| §1 raw/wiki/index/log/hot | Adopted and implemented | Maintain current structure, JSON continues to be derivative |
| §2 harness skeleton | Adopted and implemented | `.agents` Maintain a single source and untracked vault/REGISTRY |
| §3 vault strategy | Existing “new vault recommendation” fixed due to inconsistency with user decision | Select installation location, this Mac uses existing Google Drive vault root |
| §4 claude-obsidian | Only protocols have been ported | No plans to install full plugin |
| §4 superpowers | SessionStart·SDO·metaskill pattern transplant completed | Phase 3 not implemented only for `study-session` |
| §4 Understand Anything | Adoption of all 9 skills | Phase 2b project-local installation/adapter/audit required |
| §4 claude-video | `study-video` and Korean subtitle patch implemented | Executes only end-to-end for each actual designated video |
| §4 defuddle/context7 | Skill implemented | Observe only executable files and connection status for each installation location |
| §5 paper-search | Skills and ingest route implemented | Actual papers are collected upon customization |
| §5 basic-memory | 100 knot gate removed, limited pilot adopted | Phase 2c read/search comparison required |
| §5 PaperQA2 | Conditional adoption | Run only when there is a designated paper corpus |
| §5 Obsidian skills | 4 types adopted | install project-local; This Mac's CLI is unavailable before app update |
| §5 memory/graph servers | On hold for current demands | Only when a specified reconsideration trigger occurs |
| §5 spaced repetition | Only adopted | `recall` Phase 3 not implemented |
| §5-1 diagram | Only tool judgment | `diagram` skill and provenance rules not implemented |
| §6 Skill Roster | 11 current skills implemented | `study-session`, `diagram`, `vault-gardening`, `recall` not implemented |
| §7 Roadmap | Phase 1·2 completed | Modified in the order of Phase 2b → Phase 3 |
| NotebookLM | Only verification packet export is implemented. | CLI bridge is implemented in Phase 2b behind the security gate |

## 8. User decision

1. **Vault location/relationship**: Select the correct knowledge root from `study-install` for each installation location. The existing Obsidian vault root, subfolders, and general directories are all supported.
2. **vault git tracking**: This is a policy for each installation location. It is never included in harness Git, and the installer does not automatically initialize vault Git.
3. **basic-memory introduction method**: not the number of notes, but a specified corpus and a predefined
   Pilot your search limited to questions. Orders to change the original are not permitted.
4. **Company/Personal Profile**: Recorded in `REGISTRY.md` for each installation location. Selective third-party transmission of internal profiles is prohibited by default.

## Change history

| date | Changes | reason |
|---|---|---|
| 2026-07-25 | First written — 5 repositories + parallel analysis synthesis of additional candidates | Request a user direction review |
| 2026-07-25 | §5-1 Diagram/picture tool verification added + `diagram` skill roster reflected | User Request — Architecture/illustration tools needed when writing documents |
| 2026-07-25 | Phase 1 adoption and implementation — Knowledge root selection for each installation location, Obsidian selection dependency, vault Git policy non-tracking confirmed | Reflecting user responses |
| 2026-07-25 | Addition of assertion unit evidence verification as AGENTS regular rule and note-writer required reference | User Needs — Accuracy discipline that is always applied is more appropriate than optional skills. |
| 2026-07-25 | Phase 2 Web/thesis/video ingest, NotebookLM verification snapshot, deterministic graph standard implementation | User request — NotebookLM linkage inspection and Phase 2 progress |
| 2026-07-25 | Introducing metaskill rules and detailed Korean skill guidance | User Request — Prevent skill description/README from being sparse |
| 2026-07-25 | Full review — Adopt all 9 Understand Anything skills, conditionally adopt NotebookLM CLI, add Phase 2b task list | Not a judgment for another project, but a re-evaluation solely for the purpose of learning the code, domain, design, and knowledge of nohdol-study |
| 2026-07-25 | Reexamination of additional candidates — Obsidian 4 types, basic-memory, PaperQA2 adoption scope confirmed, memory server series reexamination conditions specified | Remove arbitrary note count gate and judge based on source-of-truth, external transmission, and operational complexity |
