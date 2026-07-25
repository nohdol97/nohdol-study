---
name: study-install
description: Bootstrap nohdol-study on one machine by selecting a knowledge directory, connecting the local vault symlink, recording installation-only policy, and safely initializing missing knowledge files. Use when REGISTRY.md or vault is missing, or when the user says study-install, 공부 하네스 설치, 초기 설정, 지식 저장 위치 연결, or vault 연동.
---

# study-install — Installation-site bootstrap

## Purpose

The tracked repository is portable; the knowledge location and policy are not. This skill completes a local installation without committing the chosen path or modifying existing vault notes.

## Procedure

### 1. Inspect before changing anything

From the repository root, check:

- whether `REGISTRY.md` exists;
- whether `vault` is absent, a symlink, or a real file/directory;
- whether `.claude/skills` and `.claude/agents` are healthy symlinks;
- whether the proposed knowledge path exists and contains `.obsidian`;
- whether that path is already a Git work tree.

Do not infer the target from an unrelated historical path. Installation state differs by machine.

### 2. Resolve installation choices

If the user has not already provided them, ask one batched interview:

1. Exact knowledge-root path. It may be an existing Obsidian vault, a subdirectory in one, or a new/plain directory.
2. Profile: `personal` or `corporate`.
3. Sync label: `local`, `google-drive`, `obsidian-sync`, or `other`.
4. NotebookLM mode: `off`, `consumer`, or `enterprise`.

Explain that Obsidian is optional. When it is absent, prefer creating a plain Obsidian-compatible directory over blocking installation. Do not install Obsidian unless the user separately requests it.

Vault version control is installation-specific. Observe and record whether Git exists, but never run `git init`, add a remote, or change sync configuration unless the user explicitly asks in a separate action.

For NotebookLM:

- `consumer`: configure the local workflow as verified snapshot export and manual upload. Do not claim API sync or inspect browser login.
- `enterprise`: check for `gcloud` and report that project, location, license, and user authentication are still required. Never copy credentials into the repository.
- `off`: keep NotebookLM out of the workflow for this installation.

Connection checks are mode-specific. Consumer mode can verify the local export
workflow but cannot prove the user's NotebookLM login or a live notebook without
an explicit browser upload. Enterprise mode can verify `gcloud` presence but
must label project, license, API enablement, and authentication unverified until
observed.

### 3. Handle conflicts explicitly

- If `vault` already points to the selected path, keep it.
- If it is a symlink to another path, explain both targets and obtain confirmation before using `--replace-link`.
- If it is a real file or directory, stop. Never delete or move it automatically.
- Reject the repository root or any directory inside it as the knowledge root.
- If `index.md`, `log.md`, or `hot.md` already exists without the study frontmatter contract, stop and offer a dedicated subdirectory or an explicit migration. Never repurpose a same-named legacy file silently.

### 4. Bootstrap

Run:

```sh
.agents/skills/study-install/scripts/bootstrap.sh \
  --vault "/absolute/knowledge/path" \
  --profile personal \
  --sync local \
  --notebooklm consumer
```

Substitute the confirmed values. The script creates only missing items:

```text
raw/
wiki/
index.md
log.md
hot.md
```

It also writes the untracked local `REGISTRY.md` and makes `_workspace/`.

### 5. Report optional capabilities

Phase 1 requires no global tool beyond a POSIX shell and one supported agent CLI. For Phase 2, run `scripts/install-phase2-tools.sh --check`; if the user requested Phase 2 setup, run it again with `--install`. Report every skipped or failed item:

- Obsidian: optional graph/editor UI
- `defuddle`: Phase 2 web ingestion
- paper search tooling: Phase 2 paper ingestion
- `yt-dlp` and `ffmpeg`: Phase 2 video ingestion
- `d2`: optional later diagram rendering

Missing optional tools are not installation failures.

For `consumer`, also run
`../notebooklm-export/scripts/export_test.sh`. This verifies the local handoff
packet, not the Google account connection. For `enterprise`, run `gcloud auth
list` and relevant project/API checks only when the user has selected that mode
and authorized the account context.

### 6. Verify

Run:

```sh
readlink vault
test -d vault/raw
test -d vault/wiki
test -f vault/index.md
test -f vault/log.md
test -f vault/hot.md
git status --short
```

Confirm that:

- `vault` resolves to the selected directory;
- existing target content is still present;
- `REGISTRY.md`, `vault`, and `_workspace/` do not appear in Git status;
- baseline files contain valid flat YAML;
- `.claude/skills` and `.claude/agents` remain symlinks.

For Codex, explain that project config and exact hook definitions must be trusted through `/hooks`. For Claude Code, hooks apply on the next session. A live new-session smoke test remains unverified until the user opens one.

## With / without

| Metric | Without this skill | With this skill |
|---|---|---|
| Portability | Personal paths leak into Git | Local registry and ignored vault link |
| Existing vault safety | Initialization may overwrite names | Conflict gate and create-if-missing |
| Optional services | Assumed available | NotebookLM mode and tool status observed |
| Reinstallation | Manual, stateful setup | Idempotent bootstrap and explicit replacement |
