#!/bin/sh

set -eu

usage() {
  cat <<'EOF'
Usage:
  bootstrap.sh --vault ABSOLUTE_PATH --profile personal|corporate \
    [--sync local|google-drive|obsidian-sync|other] \
    [--notebooklm off|consumer|enterprise] [--replace-link]

The selected path may be an existing Obsidian vault or a plain directory.
Existing knowledge files are never overwritten.
EOF
}

fail() {
  printf 'study-install: %s\n' "$*" >&2
  exit 1
}

command_status() {
  if command -v "$1" >/dev/null 2>&1; then
    printf 'available'
  else
    printf 'missing'
  fi
}

obsidian_status() {
  if command -v obsidian >/dev/null 2>&1; then
    printf 'cli-available'
  elif [ -d /Applications/Obsidian.app ] || [ -d "${HOME:-/nonexistent}/Applications/Obsidian.app" ]; then
    printf 'app-installed'
  elif [ "$obsidian_metadata" = detected ]; then
    printf 'metadata-detected'
  else
    printf 'missing-optional'
  fi
}

watch_status() {
  for watch_root in \
    "${HOME:-/nonexistent}/.agents/skills/watch" \
    "${HOME:-/nonexistent}/.claude/skills/watch" \
    "${HOME:-/nonexistent}/.codex/skills/watch" \
    "${HOME:-/nonexistent}/.gemini/skills/watch"; do
    if [ -f "$watch_root/SKILL.md" ]; then
      printf 'available'
      return
    fi
  done
  printf 'missing'
}

prospective_directory() {
  prospective_input=$1
  prospective_probe=$prospective_input
  prospective_suffix=

  while [ ! -d "$prospective_probe" ]; do
    prospective_leaf=${prospective_probe##*/}
    [ -n "$prospective_leaf" ] || fail "cannot resolve knowledge root: $prospective_input"
    prospective_suffix="/$prospective_leaf$prospective_suffix"
    prospective_parent=${prospective_probe%/*}
    [ -n "$prospective_parent" ] || prospective_parent=/
    [ "$prospective_parent" != "$prospective_probe" ] ||
      fail "cannot resolve knowledge root: $prospective_input"
    prospective_probe=$prospective_parent
  done

  prospective_base=$(CDPATH= cd -- "$prospective_probe" && pwd -P)
  printf '%s%s' "$prospective_base" "$prospective_suffix"
}

write_if_missing() {
  destination=$1
  if [ -e "$destination" ] || [ -L "$destination" ]; then
    return 0
  fi

  temporary="${destination}.tmp.$$"
  trap 'rm -f "$temporary"' EXIT HUP INT TERM
  cat >"$temporary"
  if [ -e "$destination" ] || [ -L "$destination" ]; then
    rm -f "$temporary"
  else
    mv "$temporary" "$destination"
  fi
  trap - EXIT HUP INT TERM
}

write_generated() {
  destination=$1
  temporary="${destination}.tmp.$$"
  trap 'rm -f "$temporary"' EXIT HUP INT TERM
  cat >"$temporary"
  mv "$temporary" "$destination"
  trap - EXIT HUP INT TERM
}

vault_input=
profile=
sync_method=local
notebooklm_mode=off
replace_link=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --vault)
      [ "$#" -ge 2 ] || fail "--vault requires a path"
      vault_input=$2
      shift 2
      ;;
    --profile)
      [ "$#" -ge 2 ] || fail "--profile requires personal or corporate"
      profile=$2
      shift 2
      ;;
    --sync)
      [ "$#" -ge 2 ] || fail "--sync requires a value"
      sync_method=$2
      shift 2
      ;;
    --notebooklm)
      [ "$#" -ge 2 ] || fail "--notebooklm requires a value"
      notebooklm_mode=$2
      shift 2
      ;;
    --replace-link)
      replace_link=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

[ -n "$vault_input" ] || fail "--vault is required"
[ -n "$profile" ] || fail "--profile is required"

case "$profile" in
  personal|corporate) ;;
  *) fail "--profile must be personal or corporate" ;;
esac

case "$sync_method" in
  local|google-drive|obsidian-sync|other) ;;
  *) fail "--sync must be local, google-drive, obsidian-sync, or other" ;;
esac

case "$notebooklm_mode" in
  off|consumer|enterprise) ;;
  *) fail "--notebooklm must be off, consumer, or enterprise" ;;
esac

case "$vault_input" in
  /*) ;;
  *) fail "--vault must be an absolute path" ;;
esac

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
study_root=$(CDPATH= cd -- "$script_dir/../../../.." && pwd -P)

case "$notebooklm_mode" in
  off)
    notebooklm_workflow=disabled
    ;;
  consumer)
    if [ -x "$study_root/.agents/skills/notebooklm-export/scripts/export.sh" ]; then
      notebooklm_workflow=snapshot-export-ready-account-unverified
    else
      notebooklm_workflow=missing-export-script
    fi
    ;;
  enterprise)
    if command -v gcloud >/dev/null 2>&1; then
      notebooklm_workflow=gcloud-available-project-auth-unverified
    else
      notebooklm_workflow=gcloud-missing
    fi
    ;;
esac

while [ "$vault_input" != "/" ] && [ "${vault_input%/}" != "$vault_input" ]; do
  vault_input=${vault_input%/}
done

case "$vault_input" in
  */../*|*/..|*/./*|*/.) fail "--vault must not contain . or .. path segments" ;;
esac

prospective_vault=$(prospective_directory "$vault_input")
case "$prospective_vault/" in
  "$study_root/"|"$study_root/"*) fail "knowledge root must be outside the harness repository" ;;
esac

mkdir -p "$vault_input"
vault_path=$(CDPATH= cd -- "$vault_input" && pwd -P)

case "$vault_path/" in
  "$study_root/"|"$study_root/"*) fail "knowledge root must be outside the harness repository" ;;
esac

for knowledge_dir in raw wiki; do
  if [ -L "$vault_path/$knowledge_dir" ] || { [ -e "$vault_path/$knowledge_dir" ] && [ ! -d "$vault_path/$knowledge_dir" ]; }; then
    fail "$vault_path/$knowledge_dir conflicts with the required knowledge directory"
  fi
done

for knowledge_file in index.md log.md hot.md; do
  candidate="$vault_path/$knowledge_file"
  if [ -L "$candidate" ] || { [ -e "$candidate" ] && [ ! -f "$candidate" ]; }; then
    fail "$candidate conflicts with the required knowledge file"
  fi
  if [ -f "$candidate" ]; then
    for required_field in type status created updated related sources; do
      grep -E "^${required_field}:" "$candidate" >/dev/null 2>&1 ||
        fail "$candidate is not a compatible nohdol-study file; choose a subdirectory or migrate it explicitly"
    done
  fi
done

vault_link="$study_root/vault"
if [ -L "$vault_link" ]; then
  current_target=$(readlink "$vault_link")
  if [ -d "$vault_link" ]; then
    current_path=$(CDPATH= cd -- "$vault_link" && pwd -P)
  else
    current_path=$current_target
  fi

  if [ "$current_path" != "$vault_path" ]; then
    [ "$replace_link" -eq 1 ] || fail "vault already points to $current_target; rerun with --replace-link after confirmation"
    rm "$vault_link"
    ln -s "$vault_path" "$vault_link"
  fi
elif [ -e "$vault_link" ]; then
  fail "$vault_link is a real file or directory; move it manually before installation"
else
  ln -s "$vault_path" "$vault_link"
fi

mkdir -p "$vault_path/raw" "$vault_path/wiki" "$study_root/_workspace"

today=$(date +%F)

write_if_missing "$vault_path/index.md" <<EOF
---
type: index
status: evergreen
created: $today
updated: $today
related: []
sources: []
---

# 지식 인덱스

## 주제

아직 등록된 주제가 없습니다.

## 최근 갱신

- $today — 공부 하네스 지식 구조 초기화
EOF

write_if_missing "$vault_path/log.md" <<EOF
---
type: log
status: evergreen
created: $today
updated: $today
related: []
sources: []
---

# 지식 로그

> 이 파일은 append-only입니다. 기존 기록을 고치거나 재정렬하지 않습니다.

| 날짜 | 변경 | 관련 노트 |
|---|---|---|
| $today | 공부 하네스 지식 구조 초기화 | [[index]] |
EOF

write_if_missing "$vault_path/hot.md" <<EOF
---
type: cache
status: developing
created: $today
updated: $today
related: []
sources: []
---

# Hot Context

## 현재 초점

- 아직 설정되지 않음

## 최근 배운 것

- 지식 구조를 초기화함

## 열린 질문

- 다음에 깊게 공부할 주제는 무엇인가?

## 다음 행동

- 첫 주제를 공부하고 \`wiki/\`에 원자적 노트를 작성한다.
EOF

if [ -d "$vault_path/.obsidian" ]; then
  obsidian_metadata=detected
else
  obsidian_metadata=absent
fi

if git -C "$vault_path" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  vault_git=detected
else
  vault_git=absent
fi

write_generated "$study_root/REGISTRY.md" <<EOF
# nohdol-study installation registry

> Installation-specific, generated, and intentionally untracked. Do not commit this file.

## Installation

- profile: $profile
- knowledge root: \`$vault_path\`
- vault link: \`vault -> $vault_path\`
- Obsidian metadata: $obsidian_metadata
- sync: $sync_method
- NotebookLM: $notebooklm_mode
- NotebookLM workflow: $notebooklm_workflow
- vault Git: $vault_git
- initialized: $today

## Local capabilities

| Capability | Status | Required |
|---|---|---|
| Claude Code | $(command_status claude) | one agent CLI |
| Codex | $(command_status codex) | one agent CLI |
| Obsidian | $(obsidian_status) | no |
| defuddle | $(command_status defuddle) | Phase 2 |
| paper-search | $(command_status paper-search) | Phase 2 papers |
| yt-dlp | $(command_status yt-dlp) | Phase 2 |
| ffmpeg | $(command_status ffmpeg) | Phase 2 |
| watch skill | $(watch_status) | Phase 2 video |
| gcloud | $(command_status gcloud) | NotebookLM Enterprise only |
| d2 | $(command_status d2) | later diagrams |

## Local policy

- Knowledge stays outside the harness Git repository.
- Existing vault content is not migrated or normalized automatically.
- Optional external processing requires the data policy in AGENTS.md.
- Vault version control and synchronization are managed separately for this installation.
- NotebookLM consumer mode uses explicit snapshot export; enterprise API credentials stay outside this repository.
EOF

printf 'study-install: connected %s\n' "$vault_path"
printf 'study-install: Obsidian metadata %s; vault Git %s; sync %s\n' "$obsidian_metadata" "$vault_git" "$sync_method"
printf 'study-install: NotebookLM %s\n' "$notebooklm_mode"
printf 'study-install: NotebookLM workflow %s\n' "$notebooklm_workflow"
