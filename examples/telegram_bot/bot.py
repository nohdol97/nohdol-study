#!/usr/bin/env python3
"""
nohdol-study Telegram Bot Bridge
--------------------------------
Connects Telegram messages to the local study harness CLI (agy or gemini).
Never commit tokens or credentials; configure via environment variables.

Environment Variables:
  TELEGRAM_BOT_TOKEN       : Required. Telegram Bot API token from @BotFather.
  TELEGRAM_ALLOWED_CHAT_ID : Optional but recommended. If set, only this chat ID can use the bot.
  STUDY_CLI_CMD            : CLI command to run (default: "agy", can be "gemini").
  STUDY_ROOT               : Path to nohdol-study root. Found automatically when unset.
  STUDY_RUN_TIMEOUT        : Optional. Seconds before a run is abandoned (default: 1200).
"""

import os
import sys
import re
import json
import time
import asyncio
import logging
import subprocess
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, MessageEntity
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("NohdolStudyBot")

# 텔레그램 API는 토큰을 URL 경로에 담는데(`/bot<TOKEN>/getUpdates`), httpx는
# 요청 URL을 그대로 INFO로 남긴다. 폴링이 몇 초마다 도므로 로그 파일이
# 토큰 사본으로 채워지고, 그 파일을 누군가에게 보내는 순간 토큰이 함께 나간다.
# 레벨을 올려 정상 요청 로그를 막는다.
logging.getLogger("httpx").setLevel(logging.WARNING)


class RedactToken(logging.Filter):
    """로그 문자열에 남은 봇 토큰을 가린다.

    위의 레벨 조정이 정상 경로를 막지만, 예외 메시지나 다른 라이브러리를 통해
    URL이 다시 새어 나올 수 있다. 마지막 방어선이라 레벨과 함께 둔다.
    """

    def filter(self, record):
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            return True
        if isinstance(record.msg, str) and token in record.msg:
            record.msg = record.msg.replace(token, "<TOKEN>")
        if record.args:
            record.args = tuple(
                arg.replace(token, "<TOKEN>") if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True


# 로거가 아니라 핸들러에 붙인다. 로거에 붙이면 그 로거를 거치는 기록만 걸러지고,
# 다른 라이브러리가 자기 로거로 남기는 것은 그대로 나간다.
for _handler in logging.getLogger().handlers:
    _handler.addFilter(RedactToken())


def find_study_root():
    """`vault` 심링크를 가진 하네스 루트를 위로 올라가며 찾는다.

    설치 경로를 이 파일에 적지 않기 위해서다. 하네스는 vault를 심링크로 걸어
    두므로 그것을 찾으면 설치와 무관하게 루트를 얻는다. `examples/telegram_bot/`
    에서든 `_workspace/telegram_bot/`에서든 같은 깊이라 그대로 동작한다.
    """
    path = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        path = os.path.dirname(path)
        if os.path.islink(os.path.join(path, "vault")):
            return path
    return ""


BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_CHAT_ID = os.environ.get("TELEGRAM_ALLOWED_CHAT_ID", "").strip()
STUDY_CLI = os.environ.get("STUDY_CLI_CMD", "agy").strip()
STUDY_ROOT = (os.environ.get("STUDY_ROOT") or find_study_root()).strip()
RUN_TIMEOUT = int(os.environ.get("STUDY_RUN_TIMEOUT", "1200"))

# The status message is edited, never re-sent: editMessageText raises no
# notification, so a long run stays visible without buzzing the phone. The
# floor keeps a multi-minute run well under Telegram's edit rate limit.
PROGRESS_INTERVAL = 5
# Telegram clears a chat action after ~5s, so it needs refreshing or the
# typing indicator disappears while the CLI is still working.
CHAT_ACTION_INTERVAL = 4

# launchd restarts this bot on its own (KeepAlive), and an in-memory mode was
# lost silently: the user kept answering a Socratic session that had already
# reverted to plain chat. The CLI conversation itself survives via --continue,
# so only these selections need persisting.
STATE_FILE = Path(__file__).resolve().parent / "bot_state.json"

# Per-chat session state
user_fresh_session = {}
user_current_model = {}      # e.g., {chat_id: "gemini-3.1-pro-preview"}
user_current_effort = {}     # e.g., {chat_id: "high"}
user_current_skill = {}      # {chat_id: "study-session"}; "" means switched off on purpose
running_processes = {}       # e.g., {chat_id: asyncio subprocess}


def save_state():
    try:
        STATE_FILE.write_text(json.dumps({
            "model": {str(k): v for k, v in user_current_model.items()},
            "effort": {str(k): v for k, v in user_current_effort.items()},
            "skill": {str(k): v for k, v in user_current_skill.items()},
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        logger.warning(f"Could not persist bot state: {exc}")


def load_state() -> dict:
    """Restore selections and report which chats had a skill active."""
    if not STATE_FILE.is_file():
        return {}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning(f"Ignoring unreadable bot state: {exc}")
        return {}
    for key, target in (
        ("model", user_current_model),
        ("effort", user_current_effort),
        ("skill", user_current_skill),
    ):
        for chat_id, value in (data.get(key) or {}).items():
            try:
                target[int(chat_id)] = value
            except ValueError:
                continue
    # An empty value is a deliberate "off", not an active skill worth announcing.
    return {chat: skill for chat, skill in user_current_skill.items() if skill}


def active_skill_for(chat_id):
    """The skill in force for this chat, or None if it was switched off.

    Never chosen (no key) and switched off ("") have to stay distinguishable.
    If they collapse, `/skill` → 해제 lasts exactly one message before the
    default turns itself back on.
    """
    return user_current_skill.get(chat_id, DEFAULT_SKILL) or None


def skill_label(chat_id):
    """How the current selection reads in /skill and /status."""
    if chat_id not in user_current_skill:
        return f"{DEFAULT_SKILL} (기본값)"
    return user_current_skill[chat_id] or "일반 자유 대화 (직접 해제함)"


# This surface asks and answers; it does not write knowledge. The tool guard
# enforces that, but a hook can only refuse a call after the model has decided
# to make it, and on a phone that costs minutes of "생각 중..." while a note is
# attempted, denied, and retried. Saying so up front turns those round trips
# into an answer the user can act on.
# What a chat gets before it has chosen anything. Almost every message here is
# a question about what is already in the vault, and the harness rule that
# answers must start from existing notes is prose the model can skip. Making
# the search skill the resting state moves that from remembered to default.
# It stays a skill rather than a forced pre-query for one reason: the model can
# skip it. "고마워" and "아까 그거 다시 설명해줘" both return confident-looking
# hits (0.45 / 0.54) about nothing the user asked, and injecting those every
# turn would put excerpts in front of a model that is supposed to open the note
# before quoting it.
DEFAULT_SKILL = "vault-search"

READ_ONLY_PREAMBLE = (
    "[읽기 전용 표면(텔레그램). vault/ 아래에 쓰지 않는다 — 검색·읽기·설명·문답만 한다. "
    "노트 작성·수정·삭제, raw/ 캡처, index·log·hot 갱신은 맥의 대화형 세션에서 한다. "
    "기록 요청을 받으면 파일을 쓰려 하지 말고, 무엇을 어디에 적을지 정리해 답으로 보여준 뒤 "
    "맥에서 note-writer 로 마무리하도록 안내한다.]"
)


def format_elapsed(seconds: float) -> str:
    total = int(seconds)
    if total < 60:
        return f"{total}초"
    return f"{total // 60}분 {total % 60}초"

# Human readable model aliases
MODEL_ALIASES = {
    "pro": ("gemini-3.1-pro-preview", "Gemini 3.1 Pro (최상위 추론/학습 전용)"),
    "flash": ("gemini-2.5-flash", "Gemini 2.5 Flash (초고속 일상 메모/요약용)"),
}

def is_authorized(update: Update) -> bool:
    if not ALLOWED_CHAT_ID:
        return True
    chat_id = str(update.effective_chat.id)
    return chat_id == ALLOWED_CHAT_ID

async def unauthorized_reply(update: Update):
    chat_id = update.effective_chat.id
    logger.warning(f"Unauthorized access attempt from Chat ID: {chat_id}")
    await update.message.reply_text(
        f"🚨 접근 권한이 없습니다.\n"
        f"당신의 Chat ID: `{chat_id}`\n\n"
        f"본인이라면 실행 중인 환경 변수 `TELEGRAM_ALLOWED_CHAT_ID={chat_id}` 로 설정하고 봇을 재시작하세요.",
        parse_mode="Markdown"
    )

async def post_init(application: Application):
    """Register [Menu] commands and restore selections from the last run."""
    commands = [
        BotCommand("skill", "🧩 조회 스킬 선택 (의미 검색, 문답, vault 점검)"),
        BotCommand("cancel", "⏹ 실행 중인 작업 취소"),
        BotCommand("status", "⚙️ 로컬 하네스 및 현재 모델/스킬 상태 확인"),
        BotCommand("model", "🤖 AI 모델 선택 (Pro ↔ Flash 버튼)"),
        BotCommand("effort", "🧠 추론 강도 선택 (High/Med/Low 버튼)"),
        BotCommand("new", "🔄 새 대화 시작 (이전 기억 초기화)"),
        BotCommand("help", "📚 도움말 및 사용 가이드"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Telegram [Menu] commands registered successfully.")

    # launchd revives this process on its own. Silently dropping an active
    # mode is the failure worth avoiding: the user keeps answering a Socratic
    # session that already reverted to plain chat.
    restored = load_state()
    for chat_id, skill in restored.items():
        logger.info(f"Restored skill for chat {chat_id}: {skill}")
        try:
            await application.bot.send_message(
                chat_id,
                f"♻️ 봇이 재시작되었습니다.\n\n🧩 활성 스킬 *`{skill}`* 을 복원했습니다. "
                f"대화 이력은 CLI 쪽에 남아 있으므로 그대로 이어가시면 됩니다.",
                parse_mode="Markdown",
            )
        except Exception as exc:
            logger.warning(f"Could not notify chat {chat_id} about restart: {exc}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not is_authorized(update):
        await unauthorized_reply(update)
        return

    await update.message.reply_text(
        f"🎓 *nohdol-study 텔레그램 스터디 봇에 오신 것을 환영합니다!*\n\n"
        f"💡 *현재 연결 정보*:\n"
        f"• *Chat ID*: `{chat_id}`\n"
        f"• *CLI 엔진*: `{STUDY_CLI}`\n"
        f"• *스터디 하네스*: `{STUDY_ROOT}`\n\n"
        f"📌 화면 좌측 하단의 *[Menu] (메뉴)* 버튼을 누르시면 모델 선택과 */skill* 명령어로 명시적으로 켜야 하는 스킬을 원클릭으로 활성화할 수 있습니다!\n\n"
        f"🔒 *이 봇은 읽기 전용입니다.* 볼트를 검색하고 읽고 설명하고 문답하지만, 노트를 쓰거나 고치거나 지우지 않습니다. "
        f"기록은 맥의 대화형 세션에서 하세요.\n\n"
        f"🔎 기본 모드는 *`{DEFAULT_SKILL}`* 입니다 — 답하기 전에 볼트에서 먼저 찾으므로, "
        f"노트에 쓴 단어가 기억나지 않아도 됩니다. /skill 에서 바꾸거나 끌 수 있습니다.\n\n"
        f"이제 편하게 질문해 보세요!",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await unauthorized_reply(update)
        return

    await update.message.reply_text(
        "📚 *도움말 및 사용 가이드*\n\n"
        "이 봇은 메시지를 보낼 때마다 Mac의 `nohdol-study` 하네스에서 AI를 백그라운드로 실행합니다.\n\n"
        "🔒 *읽기 전용 봇입니다*: 볼트를 검색·조회·설명하고 문답하지만 노트를 쓰지 않습니다. "
        "\"기록해\"라고 하면 파일을 만드는 대신 *무엇을 어디에 적을지 정리해서* 답해 주므로, 맥에서 그대로 마무리하면 됩니다. "
        "쓰기는 하네스 훅이 실제로 막으므로 실수로 저장되는 일도 없습니다.\n\n"
        "🔎 *기본 모드는 `vault-search`*: 답하기 전에 볼트에서 의미로 먼저 찾습니다. 노트에 쓴 단어를 몰라도 되고, "
        "인사나 앞 대화 이어받기처럼 검색이 필요 없을 때는 건너뜁니다. 결과는 *어느 노트를 볼지 가리키는 포인터*이므로 "
        "봇은 그 노트를 열어 확인한 뒤 답합니다.\n\n"
        "✨ *핵심 버튼 메뉴 활용법*:\n"
        "• */skill* : 의미 기반 노트 검색(`vault-search`, 기본), 소크라테스식 문답(`study-session`), vault 점검(`vault-gardening`) 중 원하는 모드를 터치로 켜고 끄기\n"
        "• 지식 그래프 조회·코드베이스 파악 등 나머지 조회 스킬은 *그냥 말하면 자동으로 선택*됩니다. \"깨진 링크 찾아줘\", \"이거 이미 정리했나\"처럼 하고 싶은 것을 쓰세요\n\n"
        "⏳ *오래 걸리는 작업*: 진행 중에는 경과 시간이 5초마다 갱신됩니다(알림은 오지 않습니다). "
        "멈추고 싶으면 메시지의 *[⏹ 취소]* 버튼이나 */cancel* 을 쓰세요. 응답이 없으면 자동으로 중단됩니다.\n\n"
        "♻️ 모델·강도·스킬 선택은 저장되어 봇이 재시작되어도 유지됩니다.\n\n"
        "🎯 좌측 하단 *[Menu]* 버튼을 통해 모델 변경, 추론 강도 변경, 대화 초기화를 직관적으로 진행할 수 있습니다.",
        parse_mode="Markdown"
    )

async def skill_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await unauthorized_reply(update)
        return

    chat_id = update.effective_chat.id
    curr_skill = skill_label(chat_id)

    keyboard = [
        [InlineKeyboardButton("🔎 의미 기반 노트 검색 (vault-search) — 기본", callback_data="skill|vault-search")],
        [InlineKeyboardButton("🧠 소크라테스 문답 학습 (study-session)", callback_data="skill|study-session")],
        [InlineKeyboardButton("🌿 vault 드리프트 점검 (vault-gardening)", callback_data="skill|vault-gardening")],
        [InlineKeyboardButton("🔄 스킬 해제 (일반 자유 대화로 복귀)", callback_data="skill|reset")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🧩 *조회 스킬 선택 메뉴*\n\n"
        f"• *현재 활성 스킬*: `{curr_skill}`\n\n"
        f"원하시는 스킬을 선택하면 다음 메시지부터 해당 스킬 규칙이 우선 적용됩니다.\n\n"
        f"🔎 아무것도 고르지 않으면 `{DEFAULT_SKILL}` 로 동작합니다 — 답하기 전에 볼트에서 먼저 찾습니다. "
        f"단어가 기억나지 않아도 의미로 찾으며, 인사나 앞 대화 이어받기처럼 검색이 필요 없는 말에는 알아서 건너뜁니다.\n\n"
        f"⚠️ 이 봇은 *읽기 전용*이라 노트를 쓰지 않습니다. 그래서 카드 작성(`recall`)이나 "
        f"논문 저장(`paper-search`)처럼 vault에 파일을 남기는 스킬은 여기에 없습니다 — "
        f"맥의 대화형 세션에서 하세요.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await unauthorized_reply(update)
        return

    chat_id = update.effective_chat.id
    curr_model = user_current_model.get(chat_id, "Gemini 3.1 Pro (기본값)")

    keyboard = [
        [InlineKeyboardButton("🤖 Gemini 3.1 Pro (최상위 추론/학습)", callback_data="model|pro")],
        [InlineKeyboardButton("⚡ Gemini 2.5 Flash (초고속 일상/요약)", callback_data="model|flash")],
        [InlineKeyboardButton("🔄 기본값으로 초기화", callback_data="model|reset")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🤖 *AI 모델 선택 메뉴*\n\n"
        f"• *현재 적용 모델*: `{curr_model}`\n\n"
        f"원하시는 모델을 아래 버튼에서 선택하세요:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def effort_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await unauthorized_reply(update)
        return

    chat_id = update.effective_chat.id
    curr_effort = user_current_effort.get(chat_id, "high (기본값)")

    keyboard = [
        [InlineKeyboardButton("🔥 High (가장 깊은 사고 및 엄격한 검증 - 권장)", callback_data="effort|high")],
        [InlineKeyboardButton("⚖️ Medium (속도와 지능의 균형)", callback_data="effort|medium")],
        [InlineKeyboardButton("⚡ Low (빠른 일상 즉답)", callback_data="effort|low")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🧠 *추론 강도 (Reasoning Effort) 선택 메뉴*\n\n"
        f"• *현재 강도*: `{curr_effort}`\n\n"
        f"원하시는 추론 강도를 아래 버튼에서 선택하세요:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_authorized(update):
        return

    chat_id = query.message.chat.id
    data = query.data or ""

    if data.startswith("model|"):
        choice = data.split("|")[1]
        if choice == "reset":
            user_current_model.pop(chat_id, None)
            await query.edit_message_text("✅ AI 모델 설정을 *기본값 (Gemini 3.1 Pro)* 으로 초기화했습니다.", parse_mode="Markdown")
        elif choice in MODEL_ALIASES:
            model_id, desc = MODEL_ALIASES[choice]
            user_current_model[chat_id] = model_id
            await query.edit_message_text(f"✅ AI 모델이 변경되었습니다!\n\n🤖 *{desc}*\n(`{model_id}`)", parse_mode="Markdown")
        save_state()

    elif data.startswith("effort|"):
        choice = data.split("|")[1]
        if choice in ["low", "medium", "high"]:
            user_current_effort[chat_id] = choice
            await query.edit_message_text(f"✅ 추론 강도가 변경되었습니다!\n\n🧠 *`{choice.upper()}`*", parse_mode="Markdown")
            save_state()

    elif data.startswith("skill|"):
        choice = data.split("|")[1]
        if choice == "reset":
            # pop 이 아니라 빈 값이다. 지우면 "고른 적 없음"이 되어 다음 메시지에
            # 기본 스킬이 도로 켜지고, 해제 버튼이 아무 일도 안 한 것처럼 보인다.
            user_current_skill[chat_id] = ""
            await query.edit_message_text(
                f"✅ 활성 스킬을 해제하고 *일반 자유 대화 모드*로 복귀했습니다.\n\n"
                f"기본값 `{DEFAULT_SKILL}` 도 함께 꺼집니다. 다시 켜려면 /skill 에서 고르세요.",
                parse_mode="Markdown",
            )
        else:
            user_current_skill[chat_id] = choice
            await query.edit_message_text(f"✅ 스킬이 활성화되었습니다!\n\n🧩 *`{choice}`*\n\n이제 질문이나 학습할 내용을 입력하시면 해당 스킬을 우선 적용하여 답변합니다.", parse_mode="Markdown")
        save_state()

    elif data == "run|cancel":
        stop_running(chat_id)


def stop_running(chat_id) -> bool:
    """Kill this chat's run, if any. The run loop reports the cancellation."""
    process = running_processes.get(chat_id)
    if process is None or process.returncode is not None:
        return False
    try:
        process._study_cancelled = True
        process.kill()
    except ProcessLookupError:
        return False
    return True


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await unauthorized_reply(update)
        return
    if not stop_running(update.effective_chat.id):
        await update.message.reply_text("ℹ️ 지금 실행 중인 작업이 없습니다.")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await unauthorized_reply(update)
        return

    chat_id = update.effective_chat.id
    await update.message.reply_chat_action(action="typing")
    try:
        vault_link = subprocess.check_output(["readlink", "vault"], cwd=STUDY_ROOT, text=True).strip()
        git_status = subprocess.check_output(["git", "status", "--short"], cwd=STUDY_ROOT, text=True).strip()
        git_msg = "Clean (변경 사항 없음)" if not git_status else f"변경됨:\n{git_status}"
    except Exception as e:
        vault_link = f"확인 실패: {e}"
        git_msg = "Git 상태 확인 실패"

    curr_model = user_current_model.get(chat_id, "Gemini 3.1 Pro (기본값)")
    curr_effort = user_current_effort.get(chat_id, "high (기본값)")
    curr_skill = skill_label(chat_id)

    await update.message.reply_text(
        f"⚙️ *로컬 스터디 하네스 및 챗봇 상태*\n\n"
        f"🤖 *AI 모델*: `{curr_model}`\n"
        f"🧠 *추론 강도*: `{curr_effort}`\n"
        f"🧩 *활성 스킬*: `{curr_skill}`\n"
        f"⏳ *실행 중인 작업*: `{'있음 (/cancel 로 중단)' if running_processes.get(chat_id) is not None and running_processes[chat_id].returncode is None else '없음'}`\n"
        f"📁 *Vault 연결*: `{vault_link}` (읽기 전용)\n"
        f"🔧 *CLI 엔진*: `{STUDY_CLI}`\n"
        f"🌱 *Git 상태*: {git_msg}\n",
        parse_mode="Markdown"
    )

async def new_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await unauthorized_reply(update)
        return
    
    chat_id = update.effective_chat.id
    user_fresh_session[chat_id] = True
    await update.message.reply_text(
        "🔄 *대화 문맥 초기화 완료!*\n"
        "다음 메시지는 이전 대화 기록을 이어받지 않고 새로 시작합니다.",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await unauthorized_reply(update)
        return

    user_text = update.message.text
    if not user_text:
        return

    chat_id = update.effective_chat.id
    await update.message.reply_chat_action(action="typing")

    previous = running_processes.get(chat_id)
    if previous is not None and previous.returncode is None:
        await update.message.reply_text(
            "⚠️ 앞선 작업이 아직 실행 중입니다. 둘이 같은 세션 이력을 함께 쓰므로 "
            "답변이 섞일 수 있습니다. 앞 작업을 멈추려면 /cancel 을 보내세요."
        )

    status_msg = await update.message.reply_text("⏳ *생각 중...* (Mac에서 스터디 하네스 구동 중)", parse_mode="Markdown")

    is_fresh = user_fresh_session.pop(chat_id, False)
    
    cmd = [STUDY_CLI]
    
    model_pref = user_current_model.get(chat_id)
    effort_pref = user_current_effort.get(chat_id)
    active_skill = active_skill_for(chat_id)

    # 문자열 프롬프트 접두사에 표면 성격과 활성 스킬/모드 명시적 주입
    prefix = READ_ONLY_PREAMBLE
    if active_skill:
        prefix += f"[{active_skill} 스킬 활성화 및 규칙 우선 적용]"
    prompt_text = f"{prefix} {user_text}"

    if "gemini" in STUDY_CLI.lower():
        if not is_fresh:
            cmd.extend(["--resume", "latest"])
        if model_pref:
            cmd.extend(["--model", model_pref])
        cmd.extend(["-y", "-p", prompt_text])
    else:  # default to agy
        if not is_fresh:
            cmd.extend(["--continue"])
        if model_pref:
            cmd.extend(["--model", model_pref])
        if effort_pref:
            cmd.extend(["--effort", effort_pref])
        cmd.extend(["--dangerously-skip-permissions", "-p", prompt_text])

    logger.info(f"Executing for chat {chat_id}: {' '.join(cmd)}")

    # Nobody is at a keyboard here, so the CLI runs with permission prompts
    # off and nothing stands between a tool call and the filesystem. Marking
    # the surface lets the PreToolUse guard (.agents/hooks/study-tool-guard.py)
    # be that gate instead: the knowledge root is read-only, writing is confined
    # to scratch space, and the home directory is not swept. The preamble above
    # tells the model the same thing so it does not spend the run finding out.
    run_env = os.environ.copy()
    run_env["STUDY_SURFACE"] = "telegram"

    started = time.monotonic()
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=STUDY_ROOT,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=run_env
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ *실행 중 오류 발생*:\n`{e}`", parse_mode="Markdown")
        return

    running_processes[chat_id] = process
    cancel_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⏹ 취소", callback_data="run|cancel")]]
    )
    context_line = " · ".join(
        part for part in (
            f"🧩 {active_skill}" if active_skill else "",
            f"🤖 {model_pref.split('-')[0].title()}" if model_pref else "",
        ) if part
    )

    async def show_progress():
        """Keep the run visible without notifying: edits are silent in Telegram."""
        while True:
            await asyncio.sleep(PROGRESS_INTERVAL)
            elapsed = format_elapsed(time.monotonic() - started)
            body = f"⏳ *생각 중...* ({elapsed})"
            if context_line:
                body += f"\n{context_line}"
            try:
                await status_msg.edit_text(
                    body, parse_mode="Markdown", reply_markup=cancel_markup
                )
            except Exception:
                pass  # An unchanged-text or rate-limit error must not kill the run.

    async def keep_typing():
        while True:
            try:
                await update.message.reply_chat_action(action="typing")
            except Exception:
                pass
            await asyncio.sleep(CHAT_ACTION_INTERVAL)

    progress_task = asyncio.create_task(show_progress())
    typing_task = asyncio.create_task(keep_typing())
    timed_out = False
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=RUN_TIMEOUT)
    except asyncio.TimeoutError:
        timed_out = True
        process.kill()
        stdout, stderr = await process.communicate()
    finally:
        progress_task.cancel()
        typing_task.cancel()
        running_processes.pop(chat_id, None)

    out_text = stdout.decode("utf-8", errors="replace").strip()
    err_text = stderr.decode("utf-8", errors="replace").strip()
    elapsed_text = format_elapsed(time.monotonic() - started)
    cancelled = getattr(process, "_study_cancelled", False)

    try:
        await status_msg.delete()
    except Exception:
        pass

    final_reply = out_text
    if timed_out:
        header = f"⏱ *{format_elapsed(RUN_TIMEOUT)}을 넘겨 중단했습니다.*"
        final_reply = f"{header}\n\n{out_text}" if out_text else (
            f"{header} 출력이 없었습니다. 맥에서 `{STUDY_CLI}`가 멈춰 있는지 확인해 주세요."
        )
    elif cancelled:
        header = f"⏹ *취소했습니다.* ({elapsed_text} 경과)"
        final_reply = f"{header}\n\n{out_text}" if out_text else f"{header} 부분 출력은 없었습니다."
    elif not final_reply and err_text:
        final_reply = f"ℹ️ *출력 결과 없음 (stderr)*:\n{err_text}"
    elif not final_reply:
        final_reply = "✅ 작업이 백그라운드에서 완료되었습니다. (출력 메시지 없음)"

    # 텔레그램 Bot API는 file://, vscode://, cursor:// 등 웹(http/https/tg/mailto) 외 프로토콜을
    # 미지원 URL로 간주하여 400 BadRequest 예외를 일으키고 평문 폴백(백슬래시 노출)으로 이어지므로,
    # 변환 전 인라인 코드 formatting(`링크 텍스트`)으로 안전하게 사전 정제한다.
    final_reply = re.sub(r"\[([^\]]+)\]\((?!https?://|tg://|mailto:|ftp://)[^\)]+\)", r"`\1`", final_reply)

    sent_successfully = False
    try:
        import telegramify_markdown
        items = await telegramify_markdown.telegramify(final_reply, min_file_lines=999999, max_message_length=4000)
        for item in items:
            if hasattr(item, "text") and item.text:
                ptb_entities = [
                    MessageEntity(
                        type=e.type,
                        offset=e.offset,
                        length=e.length,
                        url=e.url,
                        language=e.language,
                        custom_emoji_id=getattr(e, "custom_emoji_id", None)
                    ) for e in item.entities
                ]
                await update.message.reply_text(item.text, entities=ptb_entities)
            elif hasattr(item, "file_data") and item.file_data:
                await update.message.reply_document(
                    document=item.file_data,
                    filename=item.file_name,
                    caption=getattr(item, "caption_text", ""),
                    caption_entities=[
                        MessageEntity(
                            type=e.type,
                            offset=e.offset,
                            length=e.length,
                            url=e.url,
                            language=e.language,
                            custom_emoji_id=getattr(e, "custom_emoji_id", None)
                        ) for e in getattr(item, "caption_entities", [])
                    ]
                )
        sent_successfully = True
    except Exception as e:
        logger.warning(f"Entity formatting/sending failed, falling back to plain text: {e}")

    if not sent_successfully:
        chunk_size = 4000
        for i in range(0, len(final_reply), chunk_size):
            chunk = final_reply[i:i+chunk_size]
            try:
                await update.message.reply_text(chunk)
            except Exception as e:
                await update.message.reply_text(f"⚠️ [출력 문자열]\n{chunk}")

def main():
    if not BOT_TOKEN:
        logger.error("Error: TELEGRAM_BOT_TOKEN environment variable is not set.")
        print("🚨 오류: TELEGRAM_BOT_TOKEN 환경 변수가 설정되지 않았습니다.", file=sys.stderr)
        print("실행 방법: TELEGRAM_BOT_TOKEN='당신의_토큰' ./run_bot.sh", file=sys.stderr)
        sys.exit(1)

    # 루트를 못 찾으면 CLI를 빈 cwd로 띄우게 되고, 그 실패는 봇이 답을 못 하는
    # 증상으로만 보여 원인을 찾기 어렵다. 여기서 멈추고 이유를 말한다.
    if not STUDY_ROOT or not os.path.isdir(STUDY_ROOT):
        logger.error("Study root not found: %r", STUDY_ROOT)
        print("🚨 오류: 하네스 루트를 찾지 못했습니다.", file=sys.stderr)
        print("  이 스크립트는 위로 올라가며 `vault` 심링크가 있는 디렉터리를 찾습니다.", file=sys.stderr)
        print("  표준 배치를 벗어났다면 STUDY_ROOT 환경 변수로 지정하세요.", file=sys.stderr)
        sys.exit(1)

    print(f"🚀 nohdol-study 텔레그램 봇 시작 중... (CLI: {STUDY_CLI}, Root: {STUDY_ROOT})")
    if ALLOWED_CHAT_ID:
        print(f"🔒 보안 모드: Chat ID [{ALLOWED_CHAT_ID}] 허용됨")
    else:
        print("⚠️ 주의: TELEGRAM_ALLOWED_CHAT_ID가 설정되지 않아 모든 Chat ID의 접근을 허용합니다.")

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("model", model_command))
    app.add_handler(CommandHandler("effort", effort_command))
    app.add_handler(CommandHandler("skill", skill_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("new", new_command))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
