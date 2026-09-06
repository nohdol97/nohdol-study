# Mobile Telegram Study Bridge Reference Implementation (Telegram Bot Reference Implementation)

This directory is the reference template for the official Python bot bridge (`bot.py`) and execution script (`run_bot.sh`) that links `nohdol-study` harness with smartphone Telegram.

**This bridge is read-only.** It searches, queries, explains, and answers vaults, but does not write, edit, or delete notes, and its boundaries are enforced by `.agents/hooks/study-tool-guard.py`, not by instructions. The reason is in section 2 of [docs/guides/mobile-telegram-bot.md](../../docs/guides/mobile-telegram-bot.md).

## 🚀 Usage guide (3 second application method)

1. **Copy to local workspace (`_workspace/`)**:
   According to the security rule (RULE 5) and `.gitignore` policy, the virtual environment (`.venv`) and execution log must be run in the untracked area, `_workspace/`. Copy the reference script to your workspace with the command below:
   ```bash
   mkdir -p _workspace/telegram_bot
   cp -p examples/telegram_bot/* _workspace/telegram_bot/
   ```

2. **Environment variable injection and execution**:
   ```bash
   export TELEGRAM_BOT_TOKEN="발급받은_토큰"
   export TELEGRAM_ALLOWED_CHAT_ID="내_CHAT_ID_숫자"

   # background execution
   nohup ./_workspace/telegram_bot/run_bot.sh > _workspace/telegram_bot/bot.log 2>&1 &
   ```

## 📖 Core documentation and architecture guidance
- **Detailed settings and rendering principle guide**: [docs/guides/mobile-telegram-bot.md](../../docs/guides/mobile-telegram-bot.md)
- **Key Features**:
  - 100% flawless format separation and transmission based on `MessageEntity` (Breaking of backslash `\` and asterisk `*` at the source)
  - Local file link protocol automatic pre-purification defense, such as `file://`, `vscode://`, etc.
  - Secure code chunk split transmission of large responses exceeding 4,000 characters
  - Instantly switch skill (`/skill`), model (`/model`), and inference strength (`/effort`) through the `[Menu]` button at the bottom left.
  - `/skill` exposes only the inquiry skills for which you want to fix the conversation (`vault-search`, `study-session`, `vault-gardening`). The remaining inquiry skills are automatically routed to the request phrase.
  - **The basic skill is `vault-search`**. The reason it's a skill rather than a forced dictionary search is because the model needs to be able to skip it — the embedding search also returns results in `"고마워"`, so if you inject it every turn, you'll always end up with an irrelevant excerpt. Unchecked is stored in a separate state separate from “Never selected”.
  - A prompt informs each request that this is a read-only surface. The hook alone prevents writing, but the round trip where the model attempts to write a note and is rejected appears to be several minutes long `생각 중...` on the phone.
  - Since this is a spinning surface without an acknowledgment prompt, we inject `STUDY_SURFACE=telegram` to turn on the `.agents/hooks/study-tool-guard.py` gate. Knowledge root is read-only, writes are only open to `_workspace/` and temporary directories, and home directory sweeps are blocked. **Registration is done in CLI global settings, not in the repository**, and the procedure is in step 6 of `study-install`
