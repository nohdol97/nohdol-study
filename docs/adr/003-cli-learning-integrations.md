# ADR 003 — Understand Anything Full skill and optional learning linkage adopted as project-local

- Date: 2026-07-25
- Status: Active
- Target: Understand Anything, kepano/obsidian-skills, notebooklm-py,
  Knowledge Graph, Consumer NotebookLM

## context

nohdol-study provides code, business domain, change history, design, and general knowledge documents.
This is a project for everyone to study. Understand Anything's code, domain, description, query, and
Onboarding, diff, dashboard, Figma, and knowledge functions are each used in this learning process.
You can. Adoption decisions made in other projects are not evidence of this decision.

However, the upstream installer updates the main branch and changes the global skill name to
It is symlinked, and the v2.9.0 entire monorepo lock still has a high vulnerability during auditing.
Therefore, “adopt all skills” and “run the upstream installer as is”
must be distinguished.

NotebookLM for personal use does not have an official consumer API, but `notebooklm-py` is unofficial.
Provides CLI using internal API. Users do not want to do repetitive tasks through the web UI.
Also, the existing `notebooklm-export` already has a packet with fixed transmission range and version.
make it

## decision

### Understand Anything

- Upstream’s 9 skills `understand`, `understand-chat`,
  `understand-dashboard`, `understand-diff`, `understand-domain`,
  `understand-explain`, `understand-figma`, `understand-knowledge`,
  All adopt `understand-onboard`.
- Place exact release/commit in the untracked project-local tools directory and use this
  It is exposed as an adapter skill in the repository. upstream main-pulling installer and
  `~/.agents/skills` Global symlink is not used.
- Check the status of Node 22+·pnpm 10+ and lock only necessary packages with exact lock.
  Installation, thank you. Unresolved high vulnerabilities block automatic installation.
- `.ua/` in the code repository checks the ignore/write range before execution and then converts it to a derivative.
  Allowed. The vault analysis results are
  Redirect to `_workspace/understand-anything/`. Markdown and source
  The code is the original and the graph is a deletable derivative.
- The dashboard does not open automatically and only opens on localhost when the user requests it.
  Run. CLI·JSON navigation must be possible independently.
- Figma is a separate opt-in. Without storing the token in the storage/vault
  Only when the user approves the file key and purpose to be delivered to `api.figma.com`
  Run.
- The explanation created by chat·explain·domain·onboard·diff is graph-derived navigation.
  It's data. Confirmed answers are verified by reopening the relevant source file.
- deterministic parser, typed knowledge schema, conservative in upstream v2.9.0
  Use article-analyzer as the standard for the knowledge mode adapter.
- The explicit link, frontmatter, and backlink are the deterministic layer, and the entity, claim, and implicit edge are the
  Separate into model inference layers.
- All items in the model inference layer are source path, evidence anchor, extractor,
  Must have confidence and verification status. `verified` promotion is compared to the original text
  This is only possible afterward.
- The final JSON does not retain the full notes or a copy of the text cut by the parser.
  No.

### Obsidian skills

- `kepano/obsidian-skills`, `obsidian-markdown`, `obsidian-bases`,
  `json-canvas` and `obsidian-cli` are introduced project-locally as exact commits.
- Upstream `defuddle` skill is currently nohdol-study's unchangeable capture·evidence
  It is narrower than the rule, so do not install duplicates.
- The official Obsidian CLI only works if you have Obsidian 1.12.7+ installed and the app running.
  Record as available. For installations without Obsidian, the remaining file format
  The skill continues to operate.

### NotebookLM

- With an optional CLI bridge attached after the `notebooklm-export` packet
  Adopt `notebooklm-py`. The entire vault is not synchronized.
- Stable release fixes security commit `0a6e28a0522b3542695e6666054e88060ef3de48`
  Afterwards, verify that the code is included. Otherwise, it will not be installed automatically.
  To allow accurate commit installation, create separate lock, hash, and regression verification first.
- Installation uses only the minimum extra required for CLI. MCP/server, headless
  Master-token and browser impersonation transport are prohibited by default.
- Browser cookie import allows the user to enter the correct local browser profile and
  It is used only in one authentication operation where NotebookLM transmission is explicitly approved.
  `study-install` does not run automatically.
- `storage_state.json` is the bearer credential. Dedicated outside of storage/vault
  profile and check file `0600` and directory `0700` in POSIX.
- Upload only targets the export packet of `_workspace/notebooklm/`.
  `vault/` symlink direct upload and `--follow-symlinks`, `--allow-internal`
  It is prohibited.
- Notebook creation, source upload, generate, and download are targeted and transferred before execution.
  Show the scope and output path and receive approval. public share, user invitation, delete,
  Logout is treated as a separate important task.
- NotebookLM answers, quizzes, and pictures are derived learning materials and are not knowledge evidence.

## Installation method and default path not adopted

- **Run Understand Anything upstream installer as is**: The skill content is
  In addition, main auto-update, global overwriting, and non-reproducible dependency scope are
  do not adopt
- **Auto-launch dashboard**: Adopts the skill, but does not automatically open the browser.
  No.
- **Figma Always Connected**: Skills are adopted, but token and external API transmission are performed on a per-execution basis.
  It is opt-in.
- **NotebookLM Browser UI Automation**: Improve login reliability, reproducibility, and user preferences.
  It doesn't fit.
- **NotebookLM master token**: upstream also full-account,
  Alert with infostealer-grade credential. It is excessive for a personal basic installation.
- **NotebookLM MCP/server**: Network/dependency unnecessary for initial CLI use
  Increase the surface.

## result

All learning skills can be used, but installation and execution rights are narrow and reproducible.
Keep it possible. If the security gate does not pass or there is no account/app connection,
Existing deterministic graph, Markdown file skills, and manual NotebookLM export will continue
Operates independently.
