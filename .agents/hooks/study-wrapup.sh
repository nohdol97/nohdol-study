#!/bin/sh

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
study_root=$(CDPATH= cd -- "$script_dir/../.." && pwd -P)
vault_root="$study_root/vault"

# A Stop hook that blocks while the agent is already in a hook-forced
# continuation loops forever. Both Claude Code and Codex set
# stop_hook_active on the stdin payload for that state, so read it first
# and stay silent. Reading is skipped on a terminal so the hook stays
# runnable by hand.
if [ ! -t 0 ]; then
  payload=$(cat 2>/dev/null || true)
  case "$(printf '%s' "$payload" | tr -d ' \t\n')" in
    *'"stop_hook_active":true'*) exit 0 ;;
  esac
fi

[ -L "$vault_root" ] || exit 0
[ -d "$vault_root/wiki" ] || exit 0

stale=0
for tracked_cache in index.md log.md hot.md; do
  cache_path="$vault_root/$tracked_cache"
  if [ ! -f "$cache_path" ]; then
    stale=1
    break
  fi
  if find "$vault_root/wiki" -type f -name '*.md' -newer "$cache_path" -print -quit | grep . >/dev/null 2>&1; then
    stale=1
    break
  fi
done

[ "$stale" -eq 1 ] || exit 0

message='Curated wiki knowledge is newer than index.md, log.md, or hot.md. Before finishing, update the index, append the log, and refresh the compact hot cache.'

# Claude Code and Codex share the Stop-hook contract: decision "block"
# with a reason returns one more turn to the agent. Codex treats
# "continue": false as a plain stop, which would drop the instruction, so
# both CLIs get the same shape. Escape the reason so a later wording
# change cannot emit invalid JSON.
escaped=$(printf '%s' "$message" | sed 's/\\/\\\\/g; s/"/\\"/g')
printf '{"decision":"block","reason":"%s"}\n' "$escaped"
