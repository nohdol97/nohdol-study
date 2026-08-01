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
- `d2`: renders a diagram that has outgrown Mermaid, for the `diagram` skill
- a local embedding server: semantic search over the notes, for `vault-search`
- `colab-mcp`: agent access to Google Colab runtimes (GPU practice) — profile-gated external transmission, see below

Missing optional tools are not installation failures.

#### Local embedding server

```sh
sh scripts/install-embedding.sh --check      # report only
sh scripts/install-embedding.sh --install    # ollama, a LaunchAgent, and a model
```

The script sizes the model from installed memory and says which it picked.
Report the choice and let the user override with `--model`; the trade-off is
worth stating plainly, because it is about the knowledge base rather than the
hardware.

The notes here are Korean, and an English-centred embedding model retrieves
them badly. Measured over eight questions whose answering note was known,
`nomic-embed-text` put the right note in the top ten **twice out of eight**
(MRR 0.067) — for "에이전트가 낸 결과를 배포 전에 자동으로 막는 방법" it ranked a
GeekNews item about customer churn above the note that answers it, matching on
the shared verb 막다 rather than on meaning. So a multilingual model is the
default wherever it fits in memory, and the smaller English-centred one is a
fallback whose weakness is reported rather than hidden.

Never install this through `brew services`. Its plist forces
`OLLAMA_KV_CACHE_TYPE=q8_0`, which an encoder model has no cache for, and the
server then answers `/api/version` while no model ever loads — a failure that
looks like a hardware limit and is not. The script's own LaunchAgent sets no
tuning variables, and it verifies by requesting an actual embedding rather than
by checking that a port is open.

#### Colab MCP server (profile-gated, external transmission)

Google's official MCP server ([googlecolab/colab-mcp](https://github.com/googlecolab/colab-mcp)) lets the agent CLI create notebooks and run code on Colab runtimes, including the free T4 GPU — useful when practice work exceeds local memory. Everything it runs executes on Google's servers, so it is optional third-party transmission under the `AGENTS.md` §5 rule, not an ordinary local tool.

- `corporate` profile: do not offer, install, or register it. Record `blocked-by-profile` in `REGISTRY.md` so a later session does not re-litigate the question.
- `personal` profile: ask the user explicitly during this step. Never install it by default, and record the decision either way.

```sh
claude mcp list 2>/dev/null | grep -i colab                                        # observe only
claude mcp add --scope user colab-mcp -- uvx "git+https://github.com/googlecolab/colab-mcp"   # only after explicit opt-in
```

Requires `uv`. The first use triggers an OAuth browser approval for Colab/Drive scopes, and the tools appear from the next CLI session, not the current one — say so instead of claiming live verification. Vault content does not go through this server; it exists to run practice code on public data and models.

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
- `examples/telegram_bot/` — read-only mobile bridge: it searches, reads, and
  explains the vault but never writes to it. See
  `docs/guides/mobile-telegram-bot.md`.

Record in `REGISTRY.md` which automations this installation actually runs, since
that differs per machine and nothing in the tracked harness can state it.

### 6. Register the guard for prompt-less surfaces

Only needed when this installation drives the harness from a surface with no
human approving tool calls, such as the Telegram bot in `examples/`. Everywhere
else the permission prompt is already the gate and this step is skipped.

`.agents/hooks/study-tool-guard.py` is that gate: it makes the knowledge root
read-only, confines writing to `_workspace/` and the temp directory, and refuses
home-directory sweeps that trip macOS privacy prompts. It acts only when the
surface sets `STUDY_SURFACE=telegram`, so registering it cannot disturb
interactive sessions.

Registration is per CLI and is not tracked here, because it names an absolute
installation path:

- Claude Code reads the tracked `.claude/settings.json`, where the hook is
  already registered under `PreToolUse`. Nothing to do.
- Antigravity (`agy`) reads `~/.gemini/config/hooks.json`. Its project-local
  `.agents/hooks.json` was **not** loaded by CLI 1.1.7 — the log line
  `Loaded hooks.json from ~/.gemini/config/hooks.json` names the only file it
  read — so add a named hook there, merging with any existing entry rather than
  replacing the file:

```json
"study-tool-guard": {
  "PreToolUse": [
    {
      "matcher": "write_to_file|create_file|file_change|edit_notebook|delete_file|delete_directory|run_command",
      "hooks": [
        { "type": "command", "command": "/ABSOLUTE/PATH/nohdol-study/.agents/hooks/study-tool-guard.py", "timeout": 15 }
      ]
    }
  ]
}
```

Verify with a live run rather than by reading the file back, because a hook that
is present but unregistered fails silently:

```sh
STUDY_SURFACE=telegram agy --dangerously-skip-permissions \
  -p "Create the file ~/guard-probe.md containing 'probe'. Quote any error."

STUDY_SURFACE=telegram agy --dangerously-skip-permissions \
  -p "Create the file vault/wiki/guard-probe.md containing 'probe'. Quote any error."
```

Both writes must be refused and no file may appear. The second probe is the one
worth running twice, because a guard that still allows the vault looks healthy
on the first probe while leaving the knowledge root open.

### 6b. Egress guard — only when a notebook MCP server is registered

`.agents/hooks/study-egress-guard.py` keeps vault material out of an external
notebook runtime. Unlike the tool guard it runs on every surface, because the
permission prompt asks whether to run a tool and never whether the payload
carries the user's notes. It is already registered for Claude Code in the
tracked `.claude/settings.json` and for Codex in `.codex/config.toml`, so this
step is only about confirming it fires.

There is nothing to install when no notebook server is registered — the guard
matches `mcp__colab-mcp__*` and stays silent otherwise. When one is registered,
confirm the guard is live before the first real cell:

```sh
printf '%s' '{"tool_name":"mcp__colab-mcp__add_code_cell","tool_input":{"code":"p = \"vault/wiki/a.md\""}}' \
  | .agents/hooks/study-egress-guard.py
```

A deny payload must come back. Silence means the guard is not doing its job, and
silence is also what an unregistered hook looks like from inside a session, so
check the CLI's own hook listing rather than assuming.

Codex support for `PreToolUse` has not been observed in a live session; Claude
Code is the verified path.

### 7. Verify

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
