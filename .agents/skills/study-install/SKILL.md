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

Explain that Obsidian is optional. When it is absent, prefer creating a plain Obsidian-compatible directory over blocking installation. Do not install Obsidian unless the user separately requests it.

Vault version control is installation-specific. Observe and record whether Git exists, but never run `git init`, add a remote, or change sync configuration unless the user explicitly asks in a separate action.

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
  --sync local
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

For Phase 2b, run `scripts/install-phase2b-tools.sh --check`. It observes Node,
pnpm, Obsidian, and each pinned source tree without reaching the network and
without writing anything. Run it again with `--install` only when the user
asked for Phase 2b setup. That path downloads each pinned upstream commit,
recomputes the tree hash from `.tools/PINS.md`, and places the tree only when
the hash matches.

- It writes nothing outside the tool root, links nothing into a global skill
  directory, and never touches the vault.
- It installs source trees only. No upstream installer runs, no Node
  dependency is installed, and nothing in the tree is executed.
- It fails closed on a hash mismatch, an unmet runtime, a malformed or
  unparsable pin, and a missing `python3`. A checkout that no longer matches
  its pin is reported rather than overwritten, because overwriting would
  destroy whatever produced the difference.
- A tag pin is also checked against the upstream ref, and a tag that moved
  blocks the install. This check is a tamper signal, not the integrity
  mechanism: when the API is unreachable or rate-limited it reports and
  continues, because the download is addressed by commit and the tree hash is
  what actually gates placement.
- A pin whose runtime is unmet is skipped with a non-zero exit while other
  pins still install. Report the partial state instead of retrying.
- Obsidian absence is recorded as `unavailable` and is never a failure. The
  Markdown, Bases, and Canvas formats do not need the app; only the official
  CLI does.

Adopting these skills as project skills is Phase 2b-B and 2b-D. Phase 2b-A ends
once the verified trees are in place and `REGISTRY.md` records what was
observed.

Optional local automations live under `examples/` as reference implementations.
Mention them, install none by default, and set one up only when the user asks:

- `examples/feed_scraper/` — collects RSS sources into the vault. Which sources
  run is a per-machine choice, so the catalogue is tracked in `scrape.py` while
  the selection lives in an untracked `sources.local.toml`. Copy the directory
  to `_workspace/feed_scraper/`, create the venv, copy
  `sources.local.example.toml`, and enable only the sources this machine wants.
  A source using the `geeknews` pipeline additionally needs a `.env` API key;
  `feed` sources need none. See `docs/guides/feed-scraper.md`.
- `examples/telegram_bot/` — mobile bridge. See
  `docs/guides/mobile-telegram-bot.md`.

Record in `REGISTRY.md` which automations this installation actually runs, since
that differs per machine and nothing in the tracked harness can state it.

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
| Optional services | Assumed available | Tool status observed and recorded |
| Reinstallation | Manual, stateful setup | Idempotent bootstrap and explicit replacement |
