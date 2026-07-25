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

printf 'hook tests: PASS\n'
