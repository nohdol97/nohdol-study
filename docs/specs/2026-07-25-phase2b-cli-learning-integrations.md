# nohdol-study Phase 2b — project-local learning integration specifications

- Date: 2026-07-25
- Status: R1~R10·R16 implemented. **R11~R15 (NotebookLM bridge) withdrawn with [ADR 004](../adr/004-remove-notebooklm-export.md)** — The export skill itself has been removed
- Related Decision: [ADR 003](../adr/003-cli-learning-integrations.md)
- Security Review: [NotebookLM·Understand Anything](../reviews/2026-07-25-notebooklm-understand-anything-security.md)

## Goal

- All 9 skills of Understand Anything for code, domain, design, and knowledge learning
  It can be used, but meets the accuracy, output, and external transmission boundaries of nohdol-study.
- Obsidian Markdown, Bases, JSON Canvas, and official CLI skills to project-local
  Provides.
- Verified NotebookLM export packet to consumer NotebookLM without web UI
  Provides an optional CLI path to deliver and retrieve learning materials.
- Any integration requires Markdown source, portability, and external transfer approval rules.
  Do not weaken it.

## non-goal

- Installation that automatically pulls upstream main or overwrites user global skills
- Auto-launch dashboard or auto-discovery of Figma token
- Claims to be the official API of consumer NotebookLM or always synchronized
- Upload all vaults
- Automatically confirms claims and relationships inferred by the model
- NotebookLM public share/collaborator invitation automation
- headless master token, MCP/server, browser impersonation transport

## R1. External skill source pin

Understand Anything and kepano/obsidian-skills are upstream release/commit,
Record the license, original path, and source hash. Untracked project-local tool
Install it in the path and expose it through nohdol-study adapter. `curl | bash`,
Upstream main automatic pull, `~/.agents/skills` global link is not used.
Maintain upstream fixtures and account for local changes with patch lists and tests.

## R2. Understand Anything overall skill routing

All of the following 9 entry points are provided.

| entry point | Required action |
|---|---|
| `understand` | Generate code graph/tour |
| `understand-chat` | Recheck the source after exploring the graph |
| `understand-dashboard` | localhost viewer only when explicitly requested |
| `understand-diff` | Create change overlay on base graph |
| `understand-domain` | Actor·workflow·rule analysis with code evidence |
| `understand-explain` | source-first concept/flow explanation |
| `understand-figma` | Only approved Figma files are analyzed using external API |
| `understand-knowledge` | Markdown typed knowledge graph |
| `understand-onboard` | Learning sequence/walkthrough with source link |

If the graph consumer did not directly open the relevant source file when generating the answer,
Do not process it as complete.

9 are provided by one `understand` skill through internal routing (user decision)
2026-07-25). The requirement is to provide an entry point, not the number of skills, and to establish a common boundary.
This is because if you repeat it nine times, it will be out of sync.

## R3. Node dependency gate

`study-install --check` observes Node 22+ and pnpm 10+. Upon installation
Only the packages that are actually needed are locked with an exact lock and production dependencies are secured.
Thank you. Unresolved high vulnerabilities or lock mismatches require automatic installation.
Block it. Monorepo full install is not the default path.

## R4. Output and external execution boundaries

- Code repository `.ua/`: Check target root, ignore status, and expected output before execution.
  It is displayed and used only within the relevant repository.
- vault: redirect to `_workspace/understand-anything/` and add `.ua/` to vault
  don't make
- dashboard: Does not open automatically. Binds only to loopback when requested.
- Figma: Do not record tokens in repo·vault. file key and
  `api.figma.com` transmission is approved on a per-execution basis.
- intermediate cleanup: do not recursive delete without an explicit target guard
  No.

## R5. nohdol-study format detection

Recognizes `index.md`·`log.md`·`raw/` and `wiki//*.md` of the knowledge root.
If there is more than one `wiki/`, a valid derived graph is created rather than an empty graph.
Existing Obsidian legacy directories will not be scanned unless explicitly put in scope.
No.

## R6. deterministic explicit graph

Article, topic, source and explicit wikilink·backlink·category·missing·orphan
Create the same bytes from the same input. Code fence not a link, duplicate title,
Regression test path alias and Korean file name.

## R7. Derivative isolation

The output root is injected into `_workspace/understand-anything/` of the harness.
Do not create `.ua/`·`.understand-anything/` in the vault. vault before and after execution
The Markdown path and SHA-256 set must be the same.

## R8. Minimize text

Intermediate analysis input is sent to memory or untracked temporary files only to the extent necessary.
Use it. The final graph does not include a copy of the note body, but rather the source path,
Only heading/block anchor and short evidence excerpt hash are left.

## R9. semantic enrichment

The semantic stage is a separate opt-in. The main text of the note is treated as untrusted data.
Do not execute commands, policies, or prompts within it. The new entity·claim·edge has
`source_path`, `evidence_anchor`, `extractor`, `confidence`,
`verification` is required. Items without evidence are discarded and inferred and
Verified is counted separately.

## R10. Obsidian skills

`obsidian-markdown`, `obsidian-bases`, `json-canvas`, `obsidian-cli`
Exposed as project-local skill. upstream defuddle is not installed but existing
nohdol-study maintains defuddle. Markdown/Bases/Canvas without Obsidian app
It must be usable for file format creation and verification. CLI app installer 1.12.7+
and running app conditions, and report to `unavailable` if not met.
Doesn't cause the entire installation to fail.

## R11. NotebookLM release gate

The installer ensures that the latest stable release includes audited security fixes and required features.
inspect. Correct version of browser/cookies minimum dependency set is `pip-audit`
And do not install it if it has a high or higher vulnerability or if the lock is not reproduced.

## R12. NotebookLM Certification

Authentication is not an automatic step for `study-install`. To a dedicated profile selected by the user
Run it once and check whether the storage path is outside the storage/vault and the POSIX permission.
inspect. Printing/logging/copying master-token and auth JSON is prohibited.

## R13. Packet-only upload

The bridge re-creates the manifest and hash of the packet created by `notebooklm-export`.
Verify. Only files specified in the packet are uploaded, and symlinks and paths outside the range are uploaded.
I refuse. Before sending, please enter the notebook name, file list, total size, and Google transfer facts.
It shows.

## R14. External change approval

Show the user the execution plan for each create, upload, generate, and download
Get approved. General learning about public share, collaborator change, delete, and logout
It is not called in the flow and must be separately explicitly requested.

## R15. Product recovery and verification

The results of quiz, flashcard, infographic, mind map, report, and Q&A are
Save it in `_workspace/notebooklm/<topic>/artifacts/`. Notebook in manifest
ID, source IDs, artifact ID/type, creation time, source packet hash used
leave it When imported into the vault, it is compared with the original source and given a new verification status.

## R16. Installation location status

`study-install --check` is `notebooklm` CLI, audit version, auth file existence and
Understand Anything 9 adapter·Node/pnpm·Obsidian skill·Official CLI preparation
Observe the status and record it in `REGISTRY.md`.
Account validity is written as `unverified` if network verification has not actually been performed.

## Completion criteria

- Both the upstream knowledge parser fixture and the existing graph regression pass.
- Understand Anything 9 entry points use project-local pins
  Does not change user global skills and settings.
- The chat/explain/domain/onboard/diff fixture in the code graph redirects the source.
  Do not complete a factual response without a reading record.
- The dashboard is not opened before an explicit request and does not bind to addresses other than loopback.
- Figma fixture operates in the absence of token, absence of approval, and unauthorized host, respectively.
  fail-closed.
- A graph is also created from one `wiki/` in the current vault, and the original hash does not change.
- There is no copy of `knowledgeMeta.content` or note text in the final graph.
- In fixtures containing prompt-like statements, semantic output does not execute the command.
  Reject claims without evidence.
- NotebookLM installer rejects vulnerable and unfixed releases and provides secure exact
  Only dependency sets are allowed.
- Files outside the packet, symlink, hash mismatch, unverified note, upload without approval
  Each refuses.
- Authentication files, account identifiers, and notebook IDs are not stored in Git trace files or vaults.
- Even without the Obsidian app, the markdown/bases/canvas skill works and only the CLI
  Report as unavailable.
- Full metaskill verification and document link checking pass.
