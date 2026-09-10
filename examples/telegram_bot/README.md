# Mobile Telegram study bridge reference

The Python bot and launcher connect Telegram to a local agent CLI. Runtime copies belong under `_workspace/telegram_bot/`; follow the [full guide](../../docs/guides/mobile-telegram-bot.md) for setup and example results.

The intended surface is read-only. Register the shared `study-tool-guard.py` through `study-install` for the selected CLI and verify it in a fresh session. The bot sets `STUDY_SURFACE=telegram`; that environment marker alone does not register a hook.

**An empty `TELEGRAM_ALLOWED_CHAT_ID` currently permits all chats.** Set a private allowed chat explicitly and test a rejected chat. Inject `TELEGRAM_BOT_TOKEN` externally; never save it in this repository, the vault, workspace, or shell history.

Sending answers through Telegram and source material to a selected provider requires the installation's transmission authorization. Read-only access is not a confidentiality guarantee.

The launcher defaults to `agy` and can download virtual-environment dependencies when missing. Model/effort aliases must be checked against the installed CLI. Markdown conversion uses MessageEntity ranges and local-link normalization; unusual formatting still needs testing.

The default skill is `vault-search`; `/skill`, `/model`, `/effort`, `/status`, `/cancel`, and `/new` control the conversation. Copying scripts is not evidence that authentication, hook trust, session isolation, or unattended operation works.
