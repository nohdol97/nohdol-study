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

# Whether the notes written this session were recorded, and whether anything
# points at them.
#
# Both questions used to be answered here with `grep`, and the reachability one
# was answered wrongly: a title found anywhere in index.md counted, including
# under the capped "recent updates" list, so a note passed at write time and
# went unreachable once five newer notes pushed it out. `vault-gardening` was
# corrected to judge by inbound links; this hook was not, and the two
# definitions disagreed until now. The judgment moved to a helper that calls
# the same `garden.unreachable_notes`, because a rule written twice in this
# repository has drifted every time.
#
# An earlier version of the record check compared modification times alone,
# which produced two false alarms often enough to train the reminder away. A
# note saved seconds after the index was updated looked newer even though it
# was already listed, and the feed scraper rewrites its collection documents
# every morning, so any automated run made the hook fire. The helper keeps the
# answer to "what do the files say" and uses timestamps only to bound where it
# looks.
if [ -z "$message" ]; then
  # A helper that fails must not block finishing, so its exit status is
  # ignored and only what it printed is used.
  message=$(python3 "$script_dir/study-note-record.py" --vault "$vault_root" 2>/dev/null | head -n 1 || true)
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
