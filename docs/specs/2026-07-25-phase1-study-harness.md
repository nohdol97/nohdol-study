# nohdol-study Phase 1 construction specifications

- Date: 2026-07-25
- Status: Implemented
- Related suggestions: [2026-07-25-nohdol-study-direction](../proposals/2026-07-25-nohdol-study-direction.md)

## background

Study subjects and storage locations vary from computer to computer. The harness repository only tracks public conventions and tool wiring; the actual knowledge should be stored in an external directory chosen by the installer. Obsidian is useful, but its core file-based features need to work on computers that don't have it installed.

## Goal

- Provides a re-runable installer that securely connects existing or new knowledge directories.
- Separate original text, organizing notes, index, log, and hot cache.
- Claude Code and Codex use the same skills and session context.
- Existing vault data is not automatically changed or included in harness Git.

## non-goal

- Batch migration of legacy materials, including 245 existing notes
- Automatic installation of Obsidian, CLI, and plugins
- Implementation of web/thesis/video ingest
- Introducing basic-memory or separate graph indexes
- Initialize vault Git repository

## Requirements

### R1. Separate installation location

`REGISTRY.md`, `vault`, and `_workspace/` are excluded from Git. The absolute installation path or profile is not recorded in the trace file.

### R2. Select knowledge root

The installer supports existing or new directories passed as absolute paths. The selected path can be any of the existing Obsidian vault, its subdirectories, or a general directory.

### R3. Safe initialization

The installer creates `raw/`, `wiki/`, `index.md`, `log.md`, and `hot.md` only if they do not exist. Even if you rerun it using the same path, the existing file contents will not change. If there are incompatible legacy files with the same name, they are preserved and stopped. Designating the inside of the harness repository as the knowledge root is rejected before creating the directory.

### R4. Connection conflict handling

If `vault` is a symlink pointing to the same path, it is maintained. Any other symlink will be rejected without explicit `--replace-link`. If it is an actual file or directory, it is always rejected and not automatically deleted.

### R5. install registry

The installer records the profile, knowledge root, whether Obsidian metadata was found, synchronization method, whether vault Git was found, and tool status in `REGISTRY.md`. This file is local and can be recreated.

### R6. tool independence

The Phase 1 installer uses only macOS `/bin/sh` and standard utilities. Obsidian·Python·Node·jq are not required dependencies.

### R7. knowledge protocol

`raw/` The original text is treated as immutable. `wiki/` notes use flat YAML frontmatter and wiki links. `log.md` is append-only, and `hot.md` is a derived cache of less than 3,000 bytes (about 900 tokens based on mixed Korean characters). Since the gate is measured in bytes, it is reproduced regardless of the tokenizer.

### R8. Start session

The SessionStart hook in Claude Code and Codex calls a common script. If installation is not completed, installation guidance is provided, and upon completion, the `using-study` rule and `hot.md` are provided as context. `hot.md` Specifies that the contents are data and are not treated as instructions.

### R9. Consistency before termination

If the `wiki/` change is newer than `index.md`, `log.md`, or `hot.md`, the Stop hook requires three files to be updated. If it is up to date, it passes without output.

### R10. Document/Language

Model-read operational assets and user-facing repository documentation, including READMEs, ADRs, specifications, and changelogs, are written in English. Chat follows the user's language. Functional Korean trigger aliases and language-specific examples are preserved.

### R11. Claim Unit Accuracy

Key facts in knowledge answers and notes are verified on a per-claim basis. Priority is given to primary sources, and independent evidence and counterevidence are sought for high-risk, controversial, unfamiliar, and timely claims. Distinguish between facts, inferences, and hypotheses, and record verification status and confirmation date. AI output and NotebookLM summaries are not counted as independent evidence.

## Completion criteria

- Installer regression testing ensures that new installs, reruns are preserved, existing Obsidians are detected, internal paths are rejected, connection conflicts are rejected, and incompatible files are preserved or rejected.
- Hook regression tests check non-installed/installed session output and stale/fresh termination decisions.
- All shell files pass `sh -n`.
- JSON is parsed, and TOML is parsed and verified in an environment with Python 3.11+ `tomllib`.
- In the actual installation location, `vault` points to the selected path and the initial five items are created.
- `REGISTRY.md`, `vault`, and `_workspace/` do not appear in `git status`.
- `AGENTS.md` always requires evidence verification, and `note-writer`'s essential references and note schema include verification status, confirmation date, and evidence by claim.

## Unverified range

Actual new session hook injection in Claude Code and Codex requires opening a new session in each CLI and confirming it after trust approval. Automated testing verifies configuration formats and common script output.
