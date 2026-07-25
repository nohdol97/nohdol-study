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
  STUDY_ROOT               : Path to nohdol-study root (default: "/Users/nohdol/nohdol-study").
"""

import os
import sys
import re
import asyncio
import logging
import subprocess
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

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_CHAT_ID = os.environ.get("TELEGRAM_ALLOWED_CHAT_ID", "").strip()
STUDY_CLI = os.environ.get("STUDY_CLI_CMD", "agy").strip()
STUDY_ROOT = os.environ.get("STUDY_ROOT", "/Users/nohdol/nohdol-study").strip()

# Per-chat session state
user_fresh_session = {}
user_current_model = {}      # e.g., {chat_id: "gemini-3.1-pro-preview"}
user_current_effort = {}     # e.g., {chat_id: "high"}
user_current_skill = {}      # e.g., {chat_id: "study-session"}
user_current_understand = {} # e.g., {chat_id: "understand-explain"}

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
    """Register Telegram [Menu] commands automatically on startup."""
    commands = [
        BotCommand("skill", "🧩 공부 스킬 선택 (소크라테스 문답, 복습, 노트화)"),
        BotCommand("understand", "🔬 Understand 심층 분석 (구조, 위치, 설명)"),
        BotCommand("status", "⚙️ 로컬 하네스 및 현재 모델/스킬 상태 확인"),
        BotCommand("model", "🤖 AI 모델 선택 (Pro ↔ Flash 버튼)"),
        BotCommand("effort", "🧠 추론 강도 선택 (High/Med/Low 버튼)"),
        BotCommand("new", "🔄 새 대화 시작 (이전 기억 초기화)"),
        BotCommand("help", "📚 도움말 및 사용 가이드"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Telegram [Menu] commands registered successfully.")

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
        f"📌 화면 좌측 하단의 *[Menu] (메뉴)* 버튼을 누르시면 모델 선택뿐만 아니라 */skill* 및 */understand* 명령어로 원하는 전문 AI 스킬을 버튼 원클릭으로 활성화할 수 있습니다!\n\n"
        f"이제 편하게 질문하거나 학습할 내용을 입력해 보세요!",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await unauthorized_reply(update)
        return

    await update.message.reply_text(
        "📚 *도움말 및 사용 가이드*\n\n"
        "이 봇은 메시지를 보낼 때마다 Mac의 `nohdol-study` 하네스에서 AI를 백그라운드로 실행합니다.\n\n"
        "✨ *핵심 버튼 메뉴 활용법*:\n"
        "• */skill* : 소크라테스식 문답(`study-session`), 복습 플래시카드(`recall`), 원자적 노트 저장(`note-writer`), 지식 그래프 점검(`knowledge-graph`) 중 원하는 모드를 터치로 켜고 끄기\n"
        "• */understand* : Understand Anything의 아키텍처 파악, 기능 위치 탐색, 개념 심층 설명, 온보딩 학습 가이드를 터치로 선택\n\n"
        "🎯 좌측 하단 *[Menu]* 버튼을 통해 모델 변경, 추론 강도 변경, 대화 초기화를 직관적으로 진행할 수 있습니다.",
        parse_mode="Markdown"
    )

async def skill_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await unauthorized_reply(update)
        return

    chat_id = update.effective_chat.id
    curr_skill = user_current_skill.get(chat_id, "일반 자유 대화 (기본값)")

    keyboard = [
        [InlineKeyboardButton("🧠 소크라테스 문답 학습 (study-session)", callback_data="skill|study-session")],
        [InlineKeyboardButton("🃏 복습 플래시카드 퀴즈 (recall)", callback_data="skill|recall")],
        [InlineKeyboardButton("📝 원자적 노트 보존 저장 (note-writer)", callback_data="skill|note-writer")],
        [InlineKeyboardButton("🕸️ 지식 그래프 및 고아 노트 점검 (knowledge-graph)", callback_data="skill|knowledge-graph")],
        [InlineKeyboardButton("🔄 스킬 해제 (일반 자유 대화로 복귀)", callback_data="skill|reset")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🧩 *핵심 공부 스킬 선택 메뉴*\n\n"
        f"• *현재 활성 스킬*: `{curr_skill}`\n\n"
        f"원하시는 스킬을 선택하면 다음 메시지부터 해당 스킬 규칙이 우선 적용됩니다:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def understand_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await unauthorized_reply(update)
        return

    chat_id = update.effective_chat.id
    curr_mode = user_current_understand.get(chat_id, "없음 (기본값)")

    keyboard = [
        [InlineKeyboardButton("🔍 구조/아키텍처 파악 (understand)", callback_data="under|understand")],
        [InlineKeyboardButton("💬 기능/코드 위치 찾기 (-chat)", callback_data="under|understand-chat")],
        [InlineKeyboardButton("📖 개념/흐름 깊이 설명 (-explain)", callback_data="under|understand-explain")],
        [InlineKeyboardButton("🗺️ 온보딩 학습 가이드 (-onboard)", callback_data="under|understand-onboard")],
        [InlineKeyboardButton("🕸️ 지식 베이스 분석 (-knowledge)", callback_data="under|understand-knowledge")],
        [InlineKeyboardButton("❌ Understand 모드 해제", callback_data="under|reset")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🔬 *Understand Anything 심층 분석 모드 선택*\n\n"
        f"• *현재 활성 모드*: `{curr_mode}`\n\n"
        f"원하시는 분석 모드를 선택하세요:",
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

    elif data.startswith("effort|"):
        choice = data.split("|")[1]
        if choice in ["low", "medium", "high"]:
            user_current_effort[chat_id] = choice
            await query.edit_message_text(f"✅ 추론 강도가 변경되었습니다!\n\n🧠 *`{choice.upper()}`*", parse_mode="Markdown")

    elif data.startswith("skill|"):
        choice = data.split("|")[1]
        if choice == "reset":
            user_current_skill.pop(chat_id, None)
            await query.edit_message_text("✅ 활성 스킬을 해제하고 *일반 자유 대화 모드*로 복귀했습니다.", parse_mode="Markdown")
        else:
            user_current_skill[chat_id] = choice
            user_current_understand.pop(chat_id, None)  # 상호 배타적 적용
            await query.edit_message_text(f"✅ 스킬이 활성화되었습니다!\n\n🧩 *`{choice}`*\n\n이제 질문이나 학습할 내용을 입력하시면 해당 스킬을 우선 적용하여 답변합니다.", parse_mode="Markdown")

    elif data.startswith("under|"):
        choice = data.split("|")[1]
        if choice == "reset":
            user_current_understand.pop(chat_id, None)
            await query.edit_message_text("✅ Understand 분석 모드를 해제했습니다.", parse_mode="Markdown")
        else:
            user_current_understand[chat_id] = choice
            user_current_skill.pop(chat_id, None)  # 상호 배타적 적용
            await query.edit_message_text(f"✅ Understand 분석 모드가 활성화되었습니다!\n\n🔬 *`{choice}`*\n\n분석할 대상(개념, 파일, 기능)이나 질문을 입력해 주세요.", parse_mode="Markdown")

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
    curr_skill = user_current_skill.get(chat_id, "일반 (해제됨)")
    curr_under = user_current_understand.get(chat_id, "없음 (해제됨)")

    await update.message.reply_text(
        f"⚙️ *로컬 스터디 하네스 및 챗봇 상태*\n\n"
        f"🤖 *AI 모델*: `{curr_model}`\n"
        f"🧠 *추론 강도*: `{curr_effort}`\n"
        f"🧩 *활성 스킬*: `{curr_skill}`\n"
        f"🔬 *Understand 모드*: `{curr_under}`\n"
        f"📁 *Vault 연결*: `{vault_link}`\n"
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
    
    status_msg = await update.message.reply_text("⏳ *생각 중...* (Mac에서 스터디 하네스 구동 중)", parse_mode="Markdown")

    is_fresh = user_fresh_session.pop(chat_id, False)
    
    cmd = [STUDY_CLI]
    
    model_pref = user_current_model.get(chat_id)
    effort_pref = user_current_effort.get(chat_id)
    active_skill = user_current_skill.get(chat_id)
    active_under = user_current_understand.get(chat_id)

    # 문자열 프롬프트 접두사에 활성 스킬/모드 명시적 주입
    prompt_text = user_text
    if active_skill:
        prompt_text = f"[{active_skill} 스킬 활성화 및 규칙 우선 적용] {user_text}"
    elif active_under:
        prompt_text = f"[{active_under} 스킬 모드 활성화 및 규칙 우선 적용] {user_text}"

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

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=STUDY_ROOT,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ.copy()
        )
        stdout, stderr = await process.communicate()
        out_text = stdout.decode("utf-8", errors="replace").strip()
        err_text = stderr.decode("utf-8", errors="replace").strip()
    except Exception as e:
        await status_msg.edit_text(f"❌ *실행 중 오류 발생*:\n`{e}`", parse_mode="Markdown")
        return

    try:
        await status_msg.delete()
    except Exception:
        pass

    final_reply = out_text
    if not final_reply and err_text:
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
    app.add_handler(CommandHandler("understand", understand_command))
    app.add_handler(CommandHandler("new", new_command))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
