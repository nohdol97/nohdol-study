# Mobile Telegram Study Bridge (Telegram Bot Bridge) Guide

This is an official linking guide that links the `nohdol-study` harness with the smartphone Telegram so that you can search, search, and analyze the Obsidian knowledge vault (`vault/`) on your mobile phone anytime, anywhere and learn through Socratic questions and answers.

**This bridge is read-only.** It does not write, edit or delete notes, does not store data in `raw/`, and does not update `index.md`·`log.md`·`hot.md`. The reason why it was placed that way is in verse 2.

## 1. Architecture and principles

```text
[📱 Smartphone (Telegram)]
       ↕ (message and inline button controls)
[💻 Mac Background Bot (`_workspace/telegram_bot/run_bot.sh`)]
       ↕ (asynchronous CLI call: agy / gemini)
[🤖 AI Model (Gemini 3.1 Pro / 2.5 Flash)]
       ↕ (Search notes, collate evidence — read only, no write)
[📁 Knowledge Repository (where `vault/` symlink points)]
       ↕ (Google Drive real-time synchronization)
[📱 Smartphone (check original notes in Obsidian app)]
```

- **How ​​it works**: Messages sent via Telegram are received by an asynchronous Python bot engine running on a Mac, run a local CLI (`agy` or `gemini`) in the background, and split the generated responses into chunks and send them.
- **Continuity Guaranteed**: The conversation context (`--continue` / `--resume latest`) is automatically maintained, enabling seamless Deep Dive learning on smartphones.

## 2. Compliance with security and harness policy (AGENTS.md Rule 5)

This bridge is designed to strictly comply with harness safety rules.

1. **No Committed Secrets**:
   - Never write Telegram bot tokens or API keys in Git repositories or files inside `vault/`.
   - All secrets are only injected into environment variables (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_CHAT_ID`) when running.
   - The execution virtual environment (`.venv`) and log files are isolated inside the Git untracked directory (`_workspace/telegram_bot/`).

2. **Whitelist blocking function (Chat ID Whitelisting)**:
   - To prevent the risk of anyone being able to access bots due to the nature of the external Telegram messenger, set your own Telegram Chat ID (`TELEGRAM_ALLOWED_CHAT_ID`).
   - Messages from unauthorized Chat IDs are 100% blocked with the message **🚨 You do not have access permission**.

3. **Tool Gate (PreToolUse Guard) — Knowledge root is read-only**:
   - This bot launches the CLI as `--dangerously-skip-permissions`. This is because there is no one at the keyboard to approve it, so **there is no gate blocking the tool call.** In fact, the one word "document it" spread to `find ~ -maxdepth 3`, which touched `~/Library/Reminders`, and macOS popped up "python3.11 is trying to access reminders." The reason the dialog points to a bot rather than CLI is because TCC attributes the permission request to the **responsible process** that launched the child.
   - `.agents/hooks/study-tool-guard.py` fills that position. It wakes up when it sees `STUDY_SURFACE=telegram` injected by the bot, and does not participate in other sessions.
     - **`vault/` rejects all writing, editing, and deleting below.** It is the same whether it is `wiki/` note, `raw/` capture, or `index.md`·`log.md`·`hot.md`.
     - The only places open for writing are `_workspace/` and the temporary directory. Reading is not without side effects — the semantic index that `vault-search` reads is there and updates itself when the note changes — so when this scratch space is closed, the search itself stops. The harness repository is still excluded, and changes to the trace file are a matter of human sessions with `metaskill`.
     - Blocks home directory sweeps, access to TCC protected folders, and privacy app AppleScript.
   - **Why is it a complete block rather than a contract check?** In the first edition, writing `wiki/` was passed if the note-writer contract (8 frontmatter fields, `status`, `verification`, ISO date, H1 and file name matching) was satisfied. However, **A front matter with the correct format and a note with value to leave are not the same thing.** A contract can be viewed by a machine, but it is a judgment whether the claim has been verified, whether it does not overlap with an existing note, and whether `index`·`log`·`hot` moved together, and there is no one on this surface to judge. So I closed the knowledge root and the only thing left to do was answer the question. Contract enforcement has not gone away — notes taken during an interactive session are checked the moment the `PostToolUse` hook `.agents/hooks/study-note-check.py` is saved.
   - The bot prefaces each request with a prompt indicating that it is a read-only surface. The hook alone prevents writing, but the hook can be rejected only after the model **decides to call**, so on the phone, the round trip only appears as `생각 중...`, lasting several minutes. If you let us know in advance, the time will be changed to the answer.
   - **Registration is CLI-specific and not tracked in the repository.** `agy` (Antigravity CLI), as the bot calls it, only reads the global `~/.gemini/config/hooks.json` — the project-local `.agents/hooks.json` was not loaded in 1.1.7. The registration procedure and verification commands are in skill level 6 of `study-install`.
   - Shell commands cannot be completely confined by patterns alone (bypasses such as `python3 -c "open(...)"`). The real line of defense is the writer's path inspection, while shell inspection is the secondary line that catches sweeps and redirects that are actually observed.

## 3. Quick setup and execution guide (5 minute cut)

### Step 1: Issue Telegram bot token
1. Search **`@BotFather`** in the Telegram app to start a conversation.
2. Send the command `/newbot` and specify the bot name and username (which must end with `_bot`).
3. Copy the issued **HTTP API Token** (example: `123456789:ABCdefGHI...`).

### Step 2: Find out your Chat ID (first time)
1. Send any message to the bot created in Telegram (e.g. `/start` or `안녕`).
2. Copy the official reference template from the repository (`examples/telegram_bot/`) to your local working directory and temporarily run the bot by injecting only the token:
   ```bash
   # Copy the official template (first time)
   mkdir -p _workspace/telegram_bot
   cp -p examples/telegram_bot/* _workspace/telegram_bot/

   # temporary execution
   TELEGRAM_BOT_TOKEN="발급받은토큰" ./_workspace/telegram_bot/run_bot.sh
   ```
3. When the bot tells you your ID number via Telegram, **"🚨 You do not have access permission. Your Chat ID: `12345678`"**, copy that number and exit with `Ctrl+C` in the terminal.

### Step 3: Run in full security mode
Run the bot by injecting your Chat ID in the terminal:

```bash
export TELEGRAM_BOT_TOKEN="발급받은토큰"
export TELEGRAM_ALLOWED_CHAT_ID="내_CHAT_ID_숫자"

# Uncomment below to change CLI engine to gemini (default: agy)
# export STUDY_CLI_CMD="gemini"

# Always running in the background (using nohup)
nohup ./_workspace/telegram_bot/run_bot.sh > _workspace/telegram_bot/bot.log 2>&1 &
```

#### 💡 [Advanced] Automatic startup when booting Mac (macOS) (Register `launchd` LaunchAgent)
If you want **your Mac to automatically run in the background as soon as it boots** without entering a terminal command every time you reboot your computer, you can use `launchd`, the official macOS boot service manager.
According to the security rule (RULE 5), the secret token is never stored inside the project and `_workspace/`, so create and register the environment variable injection setting in `~/Library/LaunchAgents/com.nohdol.telegrambot.plist`, a path dedicated to the user account, as follows:

```bash
# 1. Register and run launchctl
launchctl load -w ~/Library/LaunchAgents/com.nohdol.telegrambot.plist

# 2. Check driving status (check PID output)
launchctl list | grep telegrambot
```
* **Advantage**: It runs automatically even after rebooting, and even if the process terminates due to an unexpected exception, macOS restarts it immediately (`KeepAlive`).

## 4. How to use Telegram menus and commands

When running the bot, the official **`[Menu]` (Menu)** button is automatically registered at the bottom left of the Telegram chat window.

| command | Menu Description | Key features and inline buttons |
|---|---|---|
| **`/skill`** | 🧩 Select inquiry skill | • `[ 🔎 의미 기반 노트 검색 (vault-search) — 기본 ]`<br>• `[ 🧠 소크라테스 문답 (study-session) ]`<br>• `[ 🌿 vault 드리프트 점검 (vault-gardening) ]`<br>• `[ 🔄 스킬 해제 (일반 자유 대화) ]` |
| **`/model`** | 🤖 AI model selection | • `[ 🤖 Gemini 3.1 Pro ]` (Top-level deep learning/inference/architectural analysis)<br>• `[ ⚡ Gemini 2.5 Flash ]` (Super-fast daily notes/summaries)<br>• `[ 🔄 기본값 ]` (Initialization) |
| **`/effort`** | 🧠 Choose your inference strength | • `[ 🔥 High ]` (Deepest thinking and rigorous source verification - recommended)<br>• `[ ⚖️ Medium ]` (Balanced speed and intelligence)<br>• `[ ⚡ Low ]` (Quick immediate answers) |
| **`/cancel`** | ⏹ Cancel a running task | Terminates any ongoing CLI process and returns any partial output. Same as `[ ⏹ 취소 ]` button in progress message |
| **`/status`** | ⚙️ Check status | Current running model, inference strength, active skills, **running tasks**, Vault connection path (read-only), CLI engine, Git status output |
| **`/new`** | 🔄Start a new conversation | Reset previous session memories and start a new conversation |
| **`/help`** | 📚Help | Instructions for use and example Socratic learning prompts |

### 🔎 The basic skill is `vault-search`

A chat where nothing is selected goes to `vault-search`. Almost all of the language that comes to this surface is **questions about things already in the vault**, and the harness rule of "look for existing notes before answering" is prose and can be skipped. Leaving it as default changes it from memory to state.

**There is one reason it is a skill rather than a forced dictionary search — the model must be able to skip it.** Embedding searches return results no matter what you put in them. In actual measurements, `"고마워"` raises GeekNews' "It's okay to fall behind, thank you!" to 0.453, and `"아까 그거 다시 설명해줘"` raises "Retry-now Autonomous Loop Agent" to 0.535 (when it's really relevant, it's 0.61 to 0.62). The last one is especially bad, because it is an irrelevant note inserted into a follow-up question whose answer is already in the conversation history. If a bot pushes the result into the prompt at every turn, that taint will always stick, and worse, it creates **the temptation to quote an excerpt before opening the note** — `vault-search`'s contract is that the result is just a pointer, the same rule that applies to knowledge graphs.

**Cost is not an issue.** Since it is a local embedding, there are no external calls, and if there is no drift, one query takes **about 1 second**. The first query right after five notes are changed takes **about 44 seconds** to rebedding, and this value gets smaller the more often you run it — this is because the drift is dispersed and resolved.

`/skill` → If you press Turn Off, even the default settings will be turned off. Internally we store "never picked" and "directly turned off" as different states, otherwise the turn off will only persist for one next message and the default will be turned back on.

> [!NOTE]
> In `/skill`, place **only the inquiry skill that you want to fix the conversation to that mode**. `knowledge-graph`(Backlink·Orphan
> Note inquiry) and `understand` (identification of code base/knowledge base) are automatically performed by Harness after looking at the request text.
> You don't need a button because you choose — whatever you want to do, like "find broken links" or "figure out this code base".
> Just use it. If you increase the number of buttons, the automatic routing will choose the wrong skill instead of fixing it first.
> Trapped.
>
> `note-writer`·`ingest`·`recall`·`paper-search`·`study-video`·`diagram` do not spin on this surface.
>  It is a skill that leaves all results in `vault/`, and the knowledge root is read-only, so the hook does not allow writing.
> I refuse. The reason for removing it from the button is the same — you can turn it on, but the worst mode is that it gets blocked at the last step.
>
> So, when you send the message “Write it down,” the bot replies by organizing what to write, where to write it, and with what front matter.
> Read it on your phone and finish with `note-writer` in an interactive session on your Mac. The same applies to papers, videos, and web materials —
> Instead of throwing out a link and saying "I'll look at this later," what you get in response now is the material.
> It includes explanations and relationships with existing notes.

### ⏳ A task that takes a long time

The most frustrating thing about mobile is not the response, but **not knowing if something is alive**. so:

- Progress messages are **updated with elapsed time every 5 seconds**. `editMessageText` is silent on Telegram, so
  **Notifications, sounds, and badges do not occur.** When the screen is open, the number goes up, and when it is closed, it is quiet.
  The only real notification is one completed response.
- The typing mark is maintained by being updated every 4 seconds because Telegram erases it after about 5 seconds.
- The `[ ⏹ 취소 ]` button is attached to the progress message. `/cancel` is the same. If you cancel, partial output, if any, will come with it.
- If it exceeds `STUDY_RUN_TIMEOUT` (default 1200 seconds = 20 minutes), it automatically stops and notifies. In the past, if the CLI stopped
  The message was forever `생각 중...` and **there was no way to do anything about it on the phone.**
- Sending a message while the previous task is running will not prevent it, but the responses may be mixed if the two executions share the same session history.
  Let them know that you have it.

### ♻️ Restart and maintain state

Since launchd `KeepAlive` revives the bot on its own, the restart occurs without warning. Model, inference strength, and active skills are
It is saved and restored in `bot_state.json`, and **if the skill is turned on, the restoration is notified once**.

The reason this is important is because `study-session`. In the past, when restarting, the skill flag quietly disappeared,
The user continued to answer Socratic questions, but at some point the bot began answering normally. There's no way to know that
There wasn't. For reference, **the conversation history itself is not originally lost** — the bot sets the CLI to `--continue` (or `--resume latest`).
Because it is called, the question and answer record remains in the Mac's CLI session. All that was lost was skill prefix injection.

> Since `bot_state.json` contains a chat ID, it is the target of `.gitignore`. Don't commit.

### 💡 Tips for using mobile Deep Dive

These are all **read-only** usages. There is nothing left in the bolt, so you can bite as much as you like while moving.

- **Search and synthesis of past notes**: *"Summarize only the sensor part of the physical AI notes I wrote down before"*
- **Semantic-based duplicate check (`vault-search`)**: *"Have you already sorted this out? — Automatic blocking before agent output deployment"* (Find even if you don't remember the word)
- **Discover knowledge links**: *"Among my notes, are there orphan notes that are closely related to each other but are not connected by wiki links?"*
- **Socratic Questions and Answers (`study-session`)**: *"Ask me why HBM4 bandwidth is like that"* — Just check understanding without making notes
- **Take the answer and finish it on your Mac**: *"Just show me a draft of what this will look like if I organize it into a note"*

## 5. Markdown rendering and message segmentation architecture (based on Telegram MessageEntity)

The following formatting engine and defense logic are built-in to render rich markdown (GitHub Flavored Markdown: `# 제목`, `**굵은 글씨**`, tables, code blocks, etc.) output by AI CLI (`agy` or `gemini`) cleanly and without corruption in the Telegram chat window.

1. **Syntax conversion based on `telegramify-markdown` and `MessageEntity`**:
   - `parse_mode="MarkdownV2"` of Telegram Bot API performs string-based parsing, so even if the escape symbols (`.`, `-`, `(`, etc.) are slightly out of sync, an error is generated or the screen displays backslash (`\`), asterisk (`*`, etc.) There is a limit to exposing backticks (`` ` ``) as is.
   - To block this at the source, `bot.py` calls `telegramify_markdown.telegramify()` and creates 100% pure text (`item.text`) with no markdown symbols and an array of style attribute objects (`MessageEntity`) separately. As a result, the text itself does not contain any backslashes or asterisks, completely preventing it from being broken or exposed.
2. **Code block protection and secure 4,000 character split**:
   - When calling `telegramify()`, specify the `max_message_length=4000` and `min_file_lines=999999` parameters to prevent the code block from being converted to a file attachment, and safely divide it so as not to exceed the Telegram transmission limit length.
3. **Local file link (`file://`, `vscode://`) protocol purification defense**:
   - If the AI ​​CLI model outputs the local path (`[CLAUDE.md](file:///...)`) as a markdown link during the response, Telegram Bot API considers it to be an unsupported protocol (`BadRequest: Entity url ... is invalid: unsupported url protocol`), blocks transmission, and raises an exception.
   - To prevent this, all local protocol links except web URLs (`http://`, `https://`, `tg://`, etc.) are converted to inline code formatting (e.g. `` `CLAUDE.md` ``) through regular expressions (`re.sub`) in the preprocessing stage before Markdown conversion to 100% prevent API rejection.
4. **Double asterisk (`**`) notation correction and plaintext fallback protection:
   - In guidance messages (`/start`, `/help`, callback buttons, etc.) that use Telegram's general markdown (`parse_mode="Markdown"`), a single asterisk (`*굵은 글씨*`), a Telegram grammar, is applied instead of `**굵은 글씨**` to prevent parsing errors.
   - If entity transmission fails due to an unexpected special symbol, it automatically switches to plain text mode to prevent message loss and transmits the output results to the end.
5. **Always-on automatic management of dependencies**:
   - When `./_workspace/telegram_bot/run_bot.sh` is executed, if `telegramify-markdown` is not found in the virtual environment (`.venv`), it is configured to be automatically mounted as `uv pip install` immediately.

## 6. Troubleshooting & Maintenance FAQ (Troubleshooting & Maintenance)

### Q1. When the bot becomes unresponsive or the error `409 Conflict` is logged
- **Cause**: Telegram Bot API prohibits two or more processes from simultaneously polling `getUpdates` with the same token. This occurs when manual execution (`nohup`) and automatic startup (`launchd`) overlap or when two or more background processes are running.
- **Solution**:
  ```bash
  # 1. Force stop all bot processes
  ps aux | grep "[b]ot.py" | awk '{print $2}' | xargs kill -9 2>/dev/null || true

  # 2. Resume normal single operation with launchd
  launchctl load -w ~/Library/LaunchAgents/com.nohdol.telegrambot.plist
  ```

### Q2. When you want to check the bot operation status and real-time logs
- **Check driving status**:
  ```bash
  launchctl list | grep telegrambot
  # or
  ps aux | grep "[b]ot.py"
  ```
- **View real-time execution log**:
  ```bash
  tail -f _workspace/telegram_bot/bot.log
  ```

### Q3. When you want to pause the bot or stop it completely
- If registered as `launchd`, it will be revived immediately even if killed with the regular `kill` command (`KeepAlive`), so you must execute the service unload command as follows:
  ```bash
  # Pausing and unloading services
  launchctl unload -w ~/Library/LaunchAgents/com.nohdol.telegrambot.plist
  ```

## 7. Appendix: LLM one-click implementation and official template guide (Reference Implementation Appendix)

Although the specifications in this document alone can enable the AI ​​model to generate bot code, **an official reference script (`examples/telegram_bot/`) is provided in the repository itself** so that you can immediately apply the most authentic and verified code.

1. **Official Reference File Configuration (`examples/telegram_bot/`)**:
   - `bot.py`: Asynchronous bridge core logic based on `python-telegram-bot` and `telegramify-markdown` (100% equipped with purification defense and `MessageEntity` conversion)
   - `run_bot.sh`: Execution bootstrapper that automatically creates a virtual environment (`.venv`) and ensures dependency loading.
2. **Prompt Tips When Using LLM**:
   - When you ask the AI ​​CLI to launch a bot from another person or session, you only need to request one sentence:
   > *"Copy the bot reference template from `examples/telegram_bot/` in this repository to `_workspace/telegram_bot/` and run it in the background with my token (`...`) and Chat ID (`...`)."*
