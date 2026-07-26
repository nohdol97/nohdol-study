#!/bin/sh

set -eu

source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
test_root=$(mktemp -d "${TMPDIR:-/tmp}/nohdol-study-hooks.XXXXXX")
trap 'rm -rf "$test_root"' EXIT HUP INT TERM

mkdir -p "$test_root/.agents/hooks" "$test_root/.agents/skills/using-study" "$test_root/knowledge/wiki"
cp "$source_dir/study-session-start.sh" "$test_root/.agents/hooks/"
cp "$source_dir/study-wrapup.sh" "$test_root/.agents/hooks/"
printf '%s\n' '# using-study-test-marker' >"$test_root/.agents/skills/using-study/SKILL.md"

# Missing installation reports bootstrap guidance.
missing_output=$("$test_root/.agents/hooks/study-session-start.sh")
printf '%s' "$missing_output" | grep -F 'installation is incomplete' >/dev/null

# Completed installation injects both the workflow and hot context.
printf '%s\n' '# registry' >"$test_root/REGISTRY.md"
printf '%s\n' '# hot-test-marker' >"$test_root/knowledge/hot.md"
ln -s "$test_root/knowledge" "$test_root/vault"
ready_output=$("$test_root/.agents/hooks/study-session-start.sh")
printf '%s' "$ready_output" | grep -F 'using-study-test-marker' >/dev/null
printf '%s' "$ready_output" | grep -F 'hot-test-marker' >/dev/null
printf '%s' "$ready_output" | grep -F 'not agent instructions' >/dev/null

# A newer wiki note blocks wrap-up for both CLI output shapes.
printf '%s\n' '# index' >"$test_root/knowledge/index.md"
printf '%s\n' '# log' >"$test_root/knowledge/log.md"
touch -t 202001010000 "$test_root/knowledge/index.md" "$test_root/knowledge/log.md" "$test_root/knowledge/hot.md"
printf '%s\n' '# note' >"$test_root/knowledge/wiki/new-note.md"
touch -t 202101010000 "$test_root/knowledge/wiki/new-note.md"

codex_output=$("$test_root/.agents/hooks/study-wrapup.sh" </dev/null)
printf '%s' "$codex_output" | grep -F '"decision":"block"' >/dev/null

claude_output=$(CLAUDE_PROJECT_DIR="$test_root" "$test_root/.agents/hooks/study-wrapup.sh" </dev/null)
printf '%s' "$claude_output" | grep -F '"decision":"block"' >/dev/null

# A hook-forced continuation must not block again, or the Stop hook loops.
active_output=$(printf '%s' '{"stop_hook_active": true}' |
  "$test_root/.agents/hooks/study-wrapup.sh")
[ -z "$active_output" ]

# An inactive flag still blocks, and another true field must not be
# mistaken for the guard.
inactive_output=$(printf '%s' '{"stop_hook_active": false, "other": true}' |
  "$test_root/.agents/hooks/study-wrapup.sh")
printf '%s' "$inactive_output" | grep -F '"decision":"block"' >/dev/null

# Refreshing all three derived files clears the reminder.
touch -t 202201010000 "$test_root/knowledge/index.md" "$test_root/knowledge/log.md" "$test_root/knowledge/hot.md"
fresh_output=$("$test_root/.agents/hooks/study-wrapup.sh" </dev/null)
[ -z "$fresh_output" ]

# A note already named in index.md passes even when it is newer than the
# records. Saving a note seconds after updating the index is ordinary, and
# on cloud storage a sync client can rewrite modification times outright.
printf '%s\n' '# index' '- [[recorded note]]' >"$test_root/knowledge/index.md"
touch -t 202201010000 "$test_root/knowledge/index.md" "$test_root/knowledge/log.md" "$test_root/knowledge/hot.md"
printf '%s\n' '# recorded note' >"$test_root/knowledge/wiki/recorded note.md"
touch -t 202301010000 "$test_root/knowledge/wiki/recorded note.md"
recorded_output=$("$test_root/.agents/hooks/study-wrapup.sh" </dev/null)
[ -z "$recorded_output" ]

# Being named in log.md alone is enough; the log is the append-only record.
printf '%s\n' '# log' '| 2020-01-01 | wrote it | [[logged note]] |' >"$test_root/knowledge/log.md"
printf '%s\n' '---' 'updated: 2020-01-01' '---' >"$test_root/knowledge/hot.md"
touch -t 202201010000 "$test_root/knowledge/index.md" "$test_root/knowledge/log.md" "$test_root/knowledge/hot.md"
printf '%s\n' '# logged note' >"$test_root/knowledge/wiki/logged note.md"
touch -t 202301010000 "$test_root/knowledge/wiki/logged note.md"
logged_output=$("$test_root/.agents/hooks/study-wrapup.sh" </dev/null)
[ -z "$logged_output" ]

# An unrecorded note still blocks, and the reason names it.
printf '%s\n' '# stray' >"$test_root/knowledge/wiki/stray note.md"
touch -t 202301010000 "$test_root/knowledge/wiki/stray note.md"
stray_output=$("$test_root/.agents/hooks/study-wrapup.sh" </dev/null)
printf '%s' "$stray_output" | grep -F '"decision":"block"' >/dev/null
printf '%s' "$stray_output" | grep -F 'stray note' >/dev/null
rm "$test_root/knowledge/wiki/stray note.md"

# Scraped collection documents are queues, not knowledge. The feed scraper
# rewrites them every morning, and nothing lists them note by note, so a
# timestamp-only check fired on every automated run.
printf '%s\n' '---' 'tags:' '  - robotics' '  - feed' '---' \
  >"$test_root/knowledge/wiki/Some Feed.md"
touch -t 202301010000 "$test_root/knowledge/wiki/Some Feed.md"
feed_output=$("$test_root/.agents/hooks/study-wrapup.sh" </dev/null)
[ -z "$feed_output" ]

# Generated listings are skipped by type. The scraper rewrites the month
# archive index and the topic queues on every run, and naming each one in
# index.md would turn the entry point into a mirror of the archive.
printf '%s\n' '---' 'type: index' 'tags:' '  - Archive' '---' \
  >"$test_root/knowledge/wiki/2026.7 인덱스.md"
touch -t 202301010000 "$test_root/knowledge/wiki/2026.7 인덱스.md"
index_type_output=$("$test_root/.agents/hooks/study-wrapup.sh" </dev/null)
[ -z "$index_type_output" ]

printf '%s\n' '---' 'type: moc' 'tags:' '  - curation' '---' \
  >"$test_root/knowledge/wiki/어떤 주제.md"
touch -t 202301010000 "$test_root/knowledge/wiki/어떤 주제.md"
moc_output=$("$test_root/.agents/hooks/study-wrapup.sh" </dev/null)
[ -z "$moc_output" ]

# A hand-written map is not generated, so it must still be caught. `topic` and
# `source` are what the note contract uses for those.
printf '%s\n' '---' 'type: topic' '---' \
  >"$test_root/knowledge/wiki/손으로 쓴 허브.md"
touch -t 202301010000 "$test_root/knowledge/wiki/손으로 쓴 허브.md"
hub_output=$("$test_root/.agents/hooks/study-wrapup.sh" </dev/null)
printf '%s' "$hub_output" | grep -F '"decision":"block"' >/dev/null
printf '%s' "$hub_output" | grep -F '손으로 쓴 허브' >/dev/null
rm "$test_root/knowledge/wiki/손으로 쓴 허브.md"

# hot.md carries no note list, so it is judged by the dates inside the files:
# a cache older than the newest log entry is behind its own record.
printf '%s\n' '# log' '| 2026-07-26 | newer entry | [[logged note]] |' \
  >"$test_root/knowledge/log.md"
touch -t 202201010000 "$test_root/knowledge/log.md"
behind_output=$("$test_root/.agents/hooks/study-wrapup.sh" </dev/null)
printf '%s' "$behind_output" | grep -F '"decision":"block"' >/dev/null
printf '%s' "$behind_output" | grep -F '2026-07-26' >/dev/null

# Bringing the cache date forward clears it without touching any file time.
printf '%s\n' '---' 'updated: 2026-07-26' '---' >"$test_root/knowledge/hot.md"
touch -t 202201010000 "$test_root/knowledge/hot.md"
caught_up_output=$("$test_root/.agents/hooks/study-wrapup.sh" </dev/null)
[ -z "$caught_up_output" ]

# A missing record is reported as such rather than as a stale cache.
rm "$test_root/knowledge/index.md"
missing_index_output=$("$test_root/.agents/hooks/study-wrapup.sh" </dev/null)
printf '%s' "$missing_index_output" | grep -F 'missing index.md' >/dev/null

printf 'hook tests: PASS\n'
