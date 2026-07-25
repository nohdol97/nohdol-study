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

if ! command -v defuddle >/dev/null 2>&1; then
  if ! command -v npm >/dev/null 2>&1; then
    printf 'phase2 tools: npm is required for defuddle\n' >&2
    failed=1
  elif ! npm install -g defuddle &&
    ! command -v defuddle >/dev/null 2>&1; then
    printf 'phase2 tools: failed to install defuddle\n' >&2
    failed=1
  fi
fi

for media_tool in yt-dlp ffmpeg; do
  if ! command -v "$media_tool" >/dev/null 2>&1; then
    if [ "$(uname -s)" = Darwin ] && command -v brew >/dev/null 2>&1; then
      if ! brew install "$media_tool"; then
        command -v "$media_tool" >/dev/null 2>&1 || {
          printf 'phase2 tools: failed to install %s\n' "$media_tool" >&2
          failed=1
        }
        if command -v "$media_tool" >/dev/null 2>&1; then
          printf 'phase2 tools: %s is available despite package-manager warnings\n' \
            "$media_tool" >&2
        fi
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
  elif ! uv tool install git+https://github.com/openags/paper-search-mcp.git &&
    ! command -v paper-search >/dev/null 2>&1; then
    printf 'phase2 tools: failed to install paper-search\n' >&2
    failed=1
  fi
fi

if ! has_watch; then
  if ! command -v npx >/dev/null 2>&1; then
    printf 'phase2 tools: npx is required for watch\n' >&2
    failed=1
  elif ! npx -y skills add bradautomates/claude-video -g \
    --skill watch --agent claude-code codex gemini-cli -y; then
    printf 'phase2 tools: failed to install watch\n' >&2
    failed=1
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
