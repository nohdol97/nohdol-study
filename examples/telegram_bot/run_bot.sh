#!/bin/sh
#
# Helper script to launch the nohdol-study Telegram Bot using the local virtualenv.
# Usage:
#   export TELEGRAM_BOT_TOKEN="your_token_here"
#   export TELEGRAM_ALLOWED_CHAT_ID="your_chat_id_here"  # optional but strongly recommended
#   ./run_bot.sh

set -e

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
study_root=$(CDPATH= cd -- "$script_dir/../.." && pwd -P)
venv_python="$script_dir/.venv/bin/python"

if [ ! -f "$venv_python" ] || ! "$venv_python" -c "import telegramify_markdown" >/dev/null 2>&1; then
  printf 'Virtual environment or dependencies missing. Installing dependencies...\n' >&2
  mkdir -p "$script_dir/.venv"
  uv venv "$script_dir/.venv"
  uv pip install -p "$venv_python" python-telegram-bot telegramify-markdown
fi

export STUDY_ROOT="${STUDY_ROOT:-$study_root}"
export STUDY_CLI_CMD="${STUDY_CLI_CMD:-agy}"

exec "$venv_python" "$script_dir/bot.py" "$@"
