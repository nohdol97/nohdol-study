#!/bin/sh

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
study_root=$(CDPATH= cd -- "$script_dir/../.." && pwd -P)
vault_root="$study_root/vault"

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

if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
  printf '{"decision":"block","reason":"%s"}\n' "$message"
else
  printf '{"continue":false,"stopReason":"%s"}\n' "$message"
fi
