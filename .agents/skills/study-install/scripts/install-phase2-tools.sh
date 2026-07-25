#!/bin/sh

set -u

mode=check
if [ "${1:-}" = "--install" ]; then
  mode=install
  shift
elif [ "${1:-}" = "--check" ]; then
  shift
fi
[ "$#" -eq 0 ] || {
  printf 'Usage: install-phase2-tools.sh [--check|--install]\n' >&2
  exit 2
}

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
failed=0

has_watch() {
  for watch_root in \
    "${HOME:-/nonexistent}/.agents/skills/watch" \
    "${HOME:-/nonexistent}/.claude/skills/watch" \
    "${HOME:-/nonexistent}/.codex/skills/watch" \
    "${HOME:-/nonexistent}/.gemini/skills/watch"; do
    [ -f "$watch_root/SKILL.md" ] && return 0
  done
  return 1
}

status_line() {
  label=$1
  command_name=$2
  if command -v "$command_name" >/dev/null 2>&1; then
    printf '%-14s available\n' "$label"
  else
    printf '%-14s missing\n' "$label"
  fi
}

if [ "$mode" = check ]; then
  status_line defuddle defuddle
  status_line paper-search paper-search
  status_line yt-dlp yt-dlp
  status_line ffmpeg ffmpeg
  if has_watch; then
    printf '%-14s available\n' watch
  else
    printf '%-14s missing\n' watch
  fi
  exit 0
fi

# A package manager can exit 0 while its bin directory stays off PATH, so
# every install is judged by observing the tool afterwards, never by the
# installer's exit status alone.
if ! command -v defuddle >/dev/null 2>&1; then
  if ! command -v npm >/dev/null 2>&1; then
    printf 'phase2 tools: npm is required for defuddle\n' >&2
    failed=1
  else
    npm install -g defuddle || true
    if ! command -v defuddle >/dev/null 2>&1; then
      printf 'phase2 tools: defuddle is not on PATH after install\n' >&2
      failed=1
    fi
  fi
fi

for media_tool in yt-dlp ffmpeg; do
  if ! command -v "$media_tool" >/dev/null 2>&1; then
    if [ "$(uname -s)" = Darwin ] && command -v brew >/dev/null 2>&1; then
      brew install "$media_tool" || true
      if ! command -v "$media_tool" >/dev/null 2>&1; then
        printf 'phase2 tools: %s is not on PATH after install\n' "$media_tool" >&2
        failed=1
      fi
    else
      printf 'phase2 tools: install %s with the system package manager\n' "$media_tool" >&2
      failed=1
    fi
  fi
done

if ! command -v paper-search >/dev/null 2>&1; then
  if ! command -v uv >/dev/null 2>&1; then
    printf 'phase2 tools: uv is required for paper-search\n' >&2
    failed=1
  else
    uv tool install git+https://github.com/openags/paper-search-mcp.git || true
    if ! command -v paper-search >/dev/null 2>&1; then
      printf 'phase2 tools: paper-search is not on PATH after install\n' >&2
      failed=1
    fi
  fi
fi

if ! has_watch; then
  if ! command -v npx >/dev/null 2>&1; then
    printf 'phase2 tools: npx is required for watch\n' >&2
    failed=1
  else
    npx -y skills add bradautomates/claude-video -g \
      --skill watch --agent claude-code codex gemini-cli -y || true
    if ! has_watch; then
      printf 'phase2 tools: watch skill was not found after install\n' >&2
      failed=1
    fi
  fi
fi

watch_download=
for watch_root in \
  "${HOME:-/nonexistent}/.agents/skills/watch" \
  "${HOME:-/nonexistent}/.claude/skills/watch" \
  "${HOME:-/nonexistent}/.codex/skills/watch" \
  "${HOME:-/nonexistent}/.gemini/skills/watch"; do
  if [ -f "$watch_root/scripts/download.py" ]; then
    watch_download="$watch_root/scripts/download.py"
    break
  fi
done

if [ -n "$watch_download" ]; then
  if ! python3 "$script_dir/patch-watch-korean.py" "$watch_download"; then
    failed=1
  fi
else
  printf 'phase2 tools: watch installed but download.py was not found\n' >&2
  failed=1
fi

"$0" --check
exit "$failed"
