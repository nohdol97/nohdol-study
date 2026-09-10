# Handover work for next session — after Phase 2b

> Archived handoff: completed steps and proposed prompts below record the 2026-07-25 session. They are not an active backlog. Start from [current operating rules](../../AGENTS.md), the local registry, and the [documentation map](../README.md); NotebookLM was later withdrawn by ADR 004.

- Date written: 2026-07-25
- Reference branch: `main`
- Current status: Complete Phase 1·2·2b and Phase 3 implementation. What remains is Phase 2c
  There's only the pilot and the "remaining content work" below.
- **All planned implementations have been completed.** All remaining outstanding, including Phase 2c, are not judgments.
  Waiting for user decision — basic-memory will accept compensation for index modifying notes.
  PaperQA2 has a paper corpus and provider. Details
  [2c status](../reviews/2026-07-25-phase2c-pilot-status.md).
- Next starting point: There is no set next implementation. In fact, by accumulating data and using it,
  This is the finding stage, and the "Remaining Content Tasks" below are the only actual tasks waiting.
- Original decision:
  - [Direction suggestion](../proposals/2026-07-25-nohdol-study-direction.md)
  - [ADR 003](../adr/003-cli-learning-integrations.md)
  - [Phase 2b specifications](../specs/2026-07-25-phase2b-cli-learning-integrations.md)
  - [External linkage security review](../reviews/2026-07-25-notebooklm-understand-anything-security.md)
  - [More Tools Review](../reviews/2026-07-25-additional-tools-review.md)

## Procedure for starting a new session

1. `AGENTS.md`, untracked `REGISTRY.md`, this document, ADR 003, Phase 2b specification
   read
2. The reference state is `git status --short --branch` and `git pull --ff-only`.
   Confirm. Any user changes are preserved.
3. Check the baseline before implementation with the command below.

```sh
.agents/hooks/hooks_test.sh
python3 .agents/skills/knowledge-graph/scripts/build_graph_test.py
python3 .agents/skills/study-install/scripts/patch-watch-korean_test.py
.agents/skills/ingest/scripts/web-capture_test.sh
.agents/skills/study-install/scripts/bootstrap_test.sh
.agents/skills/study-install/scripts/install-phase2-tools_test.sh
python3 .agents/skills/metaskill/scripts/verify_harness.py
```

4. Re-establish local capabilities with the existing script corresponding to `study-install --check`.
   Observe. Without hardcoding the installation path, account, and version status in the tracking document.
   Only `REGISTRY.md` is updated.
5. The basis is to complete one set of tasks below in one session.

## Completed — Phase 2b-A (2026-07-25)

The tree hash is created by receiving the upstream exact commit to `.tools/` (untracked, only `PINS.md` is tracked).
We implemented an installer that deploys only when there is a match. `install-phase2b-tools.sh --check` is
Just observe without a network and download only `--install`. hash mismatch/unsatisfied
runtime·parse not possible pin·`python3` absence·existing checkout mismatch is fail-closed;
Moved tags are also blocked, but if the API is not reached, it is reported before proceeding (the integrity gateway is the tree
hash). The test covers the download path offline using a curl stub.

`high 취약점 fail-closed` is outside the scope of this step — there are no dependencies here.
Do not install. 2b-B also chose not to install it (executing the runtime gate).
(Moved to the point in time) The audit gate is implemented at the point when the dependency installation is actually approved.

The installer does not reference the global skill directory or vault path at all. of test
An immutable assertion is a regression canary that preserves that fact, not one that actively detects violations.
It's not a device.

Ground truth: `obsidian-skills` is deployed, `understand-anything` is pnpm 10+
Unplaced due to absence (designed fail-closed). The original plan below is recorded.

### Original plan — Phase 2b-A

project-local exact-pin installation for Understand Anything and Obsidian skills
Implement the base first. At this stage, NotebookLM authentication/upload, Figma API,
Dashboard execution and vault semantic analysis are not performed.

### scope of implementation

- Select or create an external tool root for each installation location, but do not track it in Git.
- Understand Anything and the exact release/commit of `kepano/obsidian-skills`,
  Record the source URL, license, and source hash.
- Upstream `main` automatic pull, `curl | bash`, `~/.agents/skills` global symlink
  do not use
- Paths `--check` and explicit `--install-phase2b-tools` to `study-install`
  Separate. check does not install.
- Observe Node 22+ and pnpm 10+, and perform exact lock and audit before installing dependencies.
  Demand results.
- The entire installation should not fail without Obsidian. The official CLI conditions are
  If not met, record only `unavailable`.
- Test that existing global skills and vault do not change in case of failure, rerun, or partial installation
  Add.

### Completion criteria

- The same source hash comes out with the same pin and input.
- Fail-closed due to incorrect hash, moved tag, high vulnerability, insufficient runtime
  Do it.
- The path/hash of `~/.agents/skills` and vault Markdown before and after installation are the same.
- The install destination status remains only in `REGISTRY.md`, and the Git trace file does not contain any path or account information.
  There is no information.
- The focused test and overall metaskill verification pass.
- Update related README, Korean skill map, MOC, and changelog in the same commit.

## Follow-up sequence

### Completed — Phase 2b-B (2026-07-25)

Nine adapters were exposed as project skills. The common border is
`.agents/skills/understand/references/adapter-contract.md` carries one.

One finding revealed in the investigation led to a change in 2b-A's design: the runtime was contained within one pin.
It is divided into three tiers. The parser of `understand-knowledge` is a Python standard
Only libraries are used, and the five types of graph consumption require only existing graphs.
Only `understand`·`understand-figma`·`understand-dashboard` has built dependencies.
I demand it. The source batch doesn't run anything, so it installs a runtime gate
Moved from point of view to execution point (adapter). As a result, both pins were placed,
The `understand-knowledge` path that runs without dependencies has been opened.

What remains unresolved: `understand-knowledge` calls the upstream parser verbatim.
The output is not yet in this harness schema (for 2b-C). Currently the vault has a wiki note.
Since there is only one, it does not meet the input conditions of the upstream parser (`index.md` + multiple Markdown).

### Original plan — Phase 2b-B

`understand`, `understand-chat`, `understand-dashboard`, `understand-diff`,
`understand-domain`, `understand-explain`, `understand-figma`,
Both `understand-knowledge` and `understand-onboard` are exposed as project skills.

- chat·domain·explain·onboard·diff only occurs after rereading the related source file.
  Actually complete the answer.
- The dashboard runs in loopback only when the user requests it.
- Figma receives approval for token·file key·`api.figma.com` transfer on a per-execution basis.
- Code project `.ua/` checks the target·ignore·write range.
- Vault analysis redirects to `_workspace/understand-anything/`.

### Completed — Phase 2b-C (2026-07-25)

The deterministic hierarchy was extended to article·topic·source types. The topic is `index.md`
In categories (only top-level items with links below, without wikilinks — the list of recent updates is
(It is not misunderstood as a classification), the source comes from `sources` of the note frontmatter
The `raw/` path even records whether it exists or not. As a result, even in the current vault with 1 note,
1 article, 1 topic, 5 sources, 6 edges appear (previously there was only 1 orphan node).

The inference layer comes only as `--semantic`. For each record, `source_path`·
`evidence_anchor`·`extractor`·`confidence`·`verification` are required, and anchor
If the actual interpretation within the quote note fails, it is **discarded**. The text of the note is in the graph.
Since it is not included and only the anchor and excerpt hash remain as evidence, such as instructions in the note
Sentences do not flow along the graph.

### Original plan — Phase 2b-C

- Current deterministic wikilink graph into article/entity/topic/claim/source schema
  expand
- Even if there is only one `wiki/` document, a valid graph is created.
- Removes a copy of the note body from the final graph.
- Semantic enrichment is separated into opt-in.
- source path, evidence anchor, extractor, confidence, inferred claim·edge,
  Force verification.
- Add prompt-like note fixture and vault original hash immutability test.

### Completed — Phase 2b-D (2026-07-25)

One skill `obsidian` is `obsidian-markdown`·`obsidian-bases`·`json-canvas`·
`obsidian-cli` 4 modes are internally routed (same policy as 2b-B). The first three are
If it operates without Obsidian and only requires CLI to run the app, it is `unavailable`.
The upstream `defuddle` was not adopted, and the routing test fixes the decision.

Verify the file created by `scripts/validate.py` — the canvas is JSON Canvas 1.0 (node
(type, coordinates, id duplication, edge points to actual node), Markdown is non-closed, empty
Wikilink and unknown callout type, `.base`, are structural errors that cause load failure.
The callout list is read from the pinned reference and synchronized upstream. Each test is a mutation.
Validation was confirmed, and the four actual vault files also passed.

Limitations: Due to the principle of no dependency, `.base` is not a YAML verification, but a structure dictionary
It's an inspection. The skill documentation and Korean instructions report this as "not clearly broken".
Specify.

### Original plan — Phase 2b-D

`obsidian-markdown`, `obsidian-bases`, `json-canvas`, `obsidian-cli`
Provided as project-local skill. The existing nohdol-study `defuddle` is maintained.

- Markdown/Bases/Canvas must be able to be created and verified without the Obsidian app.
- CLI is only available in installations that meet the official requirements.
- `.base` and `.canvas` fixtures, wikilink·embed·callout regression test.

### Completed — Phase 2b-E (2026-07-25)

As a result of the re-audit, **gate was determined to be blocked**, so CLI installation, authentication, and transmission were not opened.
What I saw directly with the code: The latest stable release is `v0.7.3` and in that tree
`_redirect_guard.py` does not exist (HTTP 404) and `downloads.py` fails without hop revalidation.
Write `follow_redirects=True`. The fix is ​​only in the `v0.8.0` prerelease.

The implementation is `bridge-gate.sh` (release metadata only), which definitively reproduces the judgment.
No reading, installation, authentication, or transmission, excluding pre-releases, fail-closed if API is not reached) and,
Regardless of the gate, it is **`verify-packet.sh`, which is immediately useful for manual upload.**
The latter matches the packet against its manifest — recalculating the hash, and symlinking accordingly.
Reject without reading, reject file not in manifest, reject `unverified` note. outside the rules
Sibling directories (such as `upload/`) are exposed as warnings rather than failures.


### Original plan — Phase 2b-E

The current stable release includes a redirect fix and a safe exact dependency set.
Proceed after auditing again to see if the requirements are met. If not met, installer and wrapper
Only tests are implemented and actual authentication and transmission are continuously blocked.

  Check `0700`/`0600`.
- create/upload/generate/download shows the execution plan and Google transfer scope.
  Afterwards, it is approved.
- Change master token, MCP/server, impersonation, public share, collaborator,
  delete is not allowed in the default path.

### Phase 2c — Limited Pilot

1. Basic-memory is compared based on read/search in the corpus specified by the user.
   `bm format`, automatic write and reset are prohibited and the original hash is checked.
2. PaperQA2 runs only when there is a paper corpus and provider specified by the user.
   External model·embedding transmission is approved and the citation is re-verified in the original PDF.

### Completed — Phase 3 (2026-07-25)

All four skills have been implemented. All parts that can be judged are transferred to a script and the rules are established.
I made sure it didn't just remain in words.

- `diagram` — Mermaid default, if `check.py` counts nodes and exceeds about 15, D2→SVG
  A promotion is recommended (the promotion criteria is coefficient, not intuition). Unknown Mermaid Type/Imbalance
  It also catches embedded assets without parentheses and empty SVGs. Mermaid parser is JS Prior inspection date
  It is only and the rendering is checked by a person.
- `study-session` — No script. One question at a time, fluent restatement counts as understanding
  No, no questions that cannot be graded, users can stop at any time.
- `vault-gardening` — `garden.py` reports in 5 clauses and does not fix anything
  Doesn’t. Only scans the curation layer (actual measurement during implementation: legacy in knowledge root)
  (There are many directories, so the entire traversal stops in the cloud).
- `recall` — `<!-- from: 노트.md#앵커 -->` is required for each card, and `cards.py` is required for each card.
  With **same anchor rules** as the knowledge graph (load with importlib to avoid drift)
  If the interpretation fails, it is rejected.

Each test was validated by mutation.

## Completed — Content Operations (2026-07-25)

`피지컬 AI - 12살을 위한 안내서` was completed with two pictures. Approved Image
Since there was no generation path, I used **Mermaid diagram** instead of the generated image — Detection–Judgment–
Action–feedback cycle (flowchart) and three roles in paper robot experiment (sequenceDiagram).

This choice actually suited the requirements. Because a diagram depicts the structure itself,
There is no room for contradiction with the text description, Obsidian renders it directly, and the source is in the notes.
It can be repaired, and there are no external services or product source issues.

The 「About the picture」 callout clearly stated that **the picture is not evidence but a summary of the text**.
Both `diagram`·`obsidian` tests and `vault-gardening` passed, and index·log·hot also passed.
Updated.

If you need a generated image (e.g. an illustration of a cleaning robot scene), the user must approve the path.
Do it. In that case, only the scene description is sent, and the provenance and creation date are recorded in the note.

## Pending candidates and reexamination trigger

- Graphiti: When temporal fact/history queries are repeated
- Mem0: When personalized agent memory is an explicit request
- Cognee: When multiple data/agent trace memory is needed
- Obsidian REST/MCP: live-app/remote-client cannot be resolved with official CLI
  When a demand arises
- Kuzu: Archived so not revisited with new core dependencies

## Request to be sent to new session

```text
Please read docs/handoffs/2026-07-25-next-session.md and proceed from Phase 2b-D.
Check AGENTS.md and REGISTRY.md first, and do not use the upstream global installer.
If an ambiguous design changes the actual storage location or security boundary, please notify me prior to implementation.
Ask questions, and organize tests, documentation, and commits together when completed.
```
