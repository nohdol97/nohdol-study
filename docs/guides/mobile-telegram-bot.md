# Mobile Telegram study bridge guide

The [reference bridge](../../examples/telegram_bot/README.md) forwards a permitted Telegram conversation to a local agent CLI and returns its answer. It is an optional remote access surface. Repository files do not establish whether a particular machine has installed or enabled it; installation state belongs in `REGISTRY.md`.

## Access and data boundaries

The intended mode is read-only knowledge search, explanation, and study questions. The bot sets `STUDY_SURFACE=telegram`; `study-install` must register `study-tool-guard.py` for the selected CLI before a prompt-less session is used. A notice in the prompt is not enforcement. The targeted guard does not constitute a general operating-system sandbox or proof that every external transfer is safe.

**Set `TELEGRAM_ALLOWED_CHAT_ID` before startup. The current reference implementation allows every chat when this variable is empty.** Its whitelist compares the chat ID; do not use a group chat unless every member is intended to have the resulting access. Configure a private permitted chat and verify rejection from another chat before exposing knowledge.

Answers travel through Telegram, and the selected model provider may also receive source material. Read-only filesystem access does not remove this transmission. Obtain explicit authorization for the intended non-public content and destinations before enabling it; corporate installations forbid optional third-party transmission by default. This guide does not authorize transferring vault content.

## First-time setup

The template uses Python, `uv`, and an already configured supported agent CLI. The launcher defaults to `agy`; select the installed CLI through `STUDY_CLI_CMD` after checking its supported flags. Model menu aliases are template values, not a guarantee of current provider availability.

Copy only into a new destination:

```bash
test ! -e _workspace/telegram_bot || exit 1
mkdir -p _workspace/telegram_bot
cp -p examples/telegram_bot/* _workspace/telegram_bot/
```

The launcher creates a virtual environment and installs `python-telegram-bot` and `telegramify-markdown` when its dependency check fails. This involves network access and is part of explicit setup, not a dependency-free ordinary study action. Review/pin the dependency set for your installation before unattended use.

Obtain the token directly from BotFather. Inject these variables through a credential manager or protected launcher outside the harness, vault, and workspace:

| Variable | Meaning |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Secret bot credential; never print or paste it into chat/history |
| `TELEGRAM_ALLOWED_CHAT_ID` | Required operational restriction for this deployment |
| `STUDY_ROOT` | Installation's harness root; normally discovered by the launcher |
| `STUDY_CLI_CMD` | CLI executable; default `agy` |

After explicit setup, transmission authorization, and hook registration, validate presence without displaying values and run in the foreground first:

```bash
: "${TELEGRAM_BOT_TOKEN:?Inject the bot token externally}"
: "${TELEGRAM_ALLOWED_CHAT_ID:?Set the permitted private chat ID}"
./_workspace/telegram_bot/run_bot.sh
```

Stop the foreground process with Ctrl-C. Updating an existing installation requires comparing the reference and runtime copies and preserving its local conversation state.

## Example results and acceptance

Illustrative outcomes, not a claim that a live bot was tested during documentation review:

```text
permitted private chat, /start: welcome/menu response
different chat, /start: access denied
permitted chat, existing-note question: answer with source references
request to write a vault note: refused by the registered tool guard
missing CLI executable: process-launch error; no study answer
```

Run these checks in a fresh session with harmless synthetic content before any non-public question. A working welcome menu proves Telegram connectivity only; it does not verify CLI authentication, source retrieval, hook enforcement, or safe transmission. Preserve failures as failures.

## Conversation controls

| Command | Function |
|---|---|
| `/skill` | Choose vault-search, study-session, vault-gardening, or clear the preference |
| `/model` | Choose among the template's configured model aliases |
| `/effort` | Select the effort passed to the selected CLI |
| `/status` | Inspect bridge session preferences and task state |
| `/cancel` | Request cancellation of the active task |
| `/new` | Start the next task without continuing the prior conversation |

The default skill is `vault-search`. A skill preference guides the agent; it does not replace source verification. CLI `--continue` behavior can select a previous local session, so verify isolation from unrelated interactive work and use a dedicated CLI profile where supported. Canceling the local process does not necessarily undo an external side effect.

## Rendering and diagnostics

The bridge converts Markdown into text plus Telegram MessageEntity ranges and normalizes unsupported local links. This reduces escaping failures, but does not guarantee perfect rendering for every input. Check long responses, code blocks, Unicode, and links with the reference tests and a synthetic live message.

Bot API request URLs can contain the credential. Do not publish full HTTP debug logs, environment dumps, launchd plists, or CLI session output. The existing logging filters reduce known exposure paths; they do not make arbitrary logs safe to share.

## Optional launchd operation

Create a machine-specific user LaunchAgent only after the foreground checks pass. It needs an owned label, absolute launcher path, usable CLI PATH, credential injection, log handling, and an intentional restart policy. Secrets must stay outside tracked files, vault, and workspace. This repository does not provision a complete personal plist.

Use the exact label of that installation when starting, stopping, or diagnosing it. Never kill every process matching `bot.py`, and do not launch a second foreground/nohup copy while the LaunchAgent is polling the same token. Stop only the owned job before updating its files.

Keep one bridge instance per token. A polling conflict can indicate a second instance, while an authorization error can indicate an invalid token; neither is fixed by broad process termination.

## Verification and retirement

Run the reference bot tests listed in `examples/telegram_bot/` and the harness verifier before deployment. Static tests do not establish live CLI hook trust: repeat the fresh-session allow/deny checks after changing CLI configuration.

To retire the bridge, stop/unload its owned job, verify that its process has exited, and revoke the bot credential if access should end permanently. Local preferences and conversation records may contain sensitive information; preserve or remove them according to the installation policy.
