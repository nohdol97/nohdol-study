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

index_path="$vault_root/index.md"
log_path="$vault_root/log.md"
hot_path="$vault_root/hot.md"

message=""

for tracked_cache in "$index_path" "$log_path" "$hot_path"; do
  if [ ! -f "$tracked_cache" ]; then
    message='The knowledge root is missing index.md, log.md, or hot.md. Create the missing file before finishing.'
    break
  fi
done

# Which notes count as unrecorded.
#
# The earlier check compared modification times alone, which produced two
# false alarms often enough to train the reminder away. A note saved seconds
# after the index was updated looked newer even though it was already listed,
# and the feed scraper rewrites its collection documents every morning, so any
# automated run made the hook fire. Both are answered by asking what the files
# say rather than when they were touched.
#
# Timestamps still bound the search: a note older than both records was either
# handled long ago or is a known gap that vault-gardening reports, and walking
# the whole curated layer on every Stop would be slow on cloud storage.
if [ -z "$message" ]; then
  older_cache="$index_path"
  [ "$log_path" -ot "$older_cache" ] && older_cache="$log_path"

  unrecorded=""
  # `find -newer` output is newline-separated; note titles contain spaces, so
  # only the line break can separate them.
  candidates=$(find "$vault_root/wiki" -type f -name '*.md' -newer "$older_cache" 2>/dev/null || true)
  saved_ifs=$IFS
  IFS='
'
  for note in $candidates; do
    # Generated listings are skipped. `index` is a month archive index and `moc`
    # is a topic or per-source queue; the scraper rewrites both every run, and
    # neither is something index.md is meant to name item by item. Hand-written
    # maps use `topic` or `source`, so they are still checked. A dated capture
    # is `article`, so it is matched by its tag instead.
    if head -n 20 "$note" | grep -qE '^type: (index|moc)$'; then
      continue
    fi
    if head -n 20 "$note" | grep -qE '^  - (feed|daily-scrap)$'; then
      continue
    fi
    title=$(basename "$note" .md)
    if grep -qF "$title" "$index_path" || grep -qF "$title" "$log_path"; then
      continue
    fi
    unrecorded=$title
    break
  done
  IFS=$saved_ifs

  if [ -n "$unrecorded" ]; then
    message="Curated note \"$unrecorded\" is not recorded in index.md or log.md. Update the index, append the log, and refresh the compact hot cache before finishing."
  fi
fi

# hot.md carries no note list, so registration cannot be checked the same way.
# log.md is append-only and gains a dated row per knowledge change, so a hot
# cache whose `updated:` predates the newest log entry is behind by its own
# record. Comparing two dates written into the files keeps this independent of
# a sync client rewriting modification times.
if [ -z "$message" ]; then
  newest_log_date=$(grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' "$log_path" 2>/dev/null | sort | tail -n 1 || true)
  hot_updated=$(grep -m 1 -oE '^updated: [0-9]{4}-[0-9]{2}-[0-9]{2}' "$hot_path" 2>/dev/null | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' || true)
  if [ -n "$newest_log_date" ] && [ -n "$hot_updated" ]; then
    # String order matches chronological order for ISO dates.
    if [ "$newest_log_date" \> "$hot_updated" ]; then
      message="hot.md is dated $hot_updated but log.md records knowledge through $newest_log_date. Refresh the compact hot cache before finishing."
    fi
  fi
fi

[ -n "$message" ] || exit 0

# Claude Code and Codex share the Stop-hook contract: decision "block"
# with a reason returns one more turn to the agent. Codex treats
# "continue": false as a plain stop, which would drop the instruction, so
# both CLIs get the same shape. Escape the reason so a later wording
# change cannot emit invalid JSON.
escaped=$(printf '%s' "$message" | sed 's/\\/\\\\/g; s/"/\\"/g')
printf '{"decision":"block","reason":"%s"}\n' "$escaped"
