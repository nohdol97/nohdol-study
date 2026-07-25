#!/bin/sh
#
# Place the Phase 2b external source pins under the untracked tool root.
#
# This installs source trees only. It never runs upstream installers, never
# links into a global skill directory, never touches the vault, and never
# installs Node dependencies. Everything it writes lives under the tool root.

set -u

usage() {
  printf 'Usage: install-phase2b-tools.sh [--check|--install]\n' >&2
}

mode=check
if [ "${1:-}" = "--install" ]; then
  mode=install
  shift
elif [ "${1:-}" = "--check" ]; then
  shift
fi
[ "$#" -eq 0 ] || {
  usage
  exit 2
}

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
study_root=$(CDPATH= cd -- "$script_dir/../../../.." && pwd -P)
# The override exists for the test harness. Real installs use the repository
# tool root so the checkouts stay with the harness they belong to.
tools_root=${NOHDOL_STUDY_TOOLS_ROOT:-$study_root/.tools}
pins_file="$tools_root/PINS.md"
tree_hash_script="$script_dir/tree_hash.py"

failed=0
note() { printf 'phase2b: %s\n' "$*" >&2; }

[ -f "$pins_file" ] || {
  note "pin ledger not found: $pins_file"
  exit 1
}
[ -f "$tree_hash_script" ] || {
  note "tree hash helper not found: $tree_hash_script"
  exit 1
}

# --- runtime observation ---------------------------------------------------

leading_integer() {
  printf '%s' "${1#v}" | sed -n 's/^\([0-9][0-9]*\).*/\1/p'
}

at_least() {
  observed=$1
  required=$2
  [ -n "$observed" ] || return 1
  [ "$observed" -ge "$required" ] 2>/dev/null || return 1
  return 0
}

node_version=
command -v node >/dev/null 2>&1 && node_version=$(node --version 2>/dev/null)
pnpm_version=
command -v pnpm >/dev/null 2>&1 && pnpm_version=$(pnpm --version 2>/dev/null)

node_ok=0
at_least "$(leading_integer "${node_version:-}")" 22 && node_ok=1
pnpm_ok=0
at_least "$(leading_integer "${pnpm_version:-}")" 10 && pnpm_ok=1

# Obsidian is optional on purpose. Its absence limits the official CLI skill
# and nothing else, so it is reported and never treated as a failure.
obsidian_state=unavailable
if command -v obsidian >/dev/null 2>&1; then
  obsidian_state=cli-available
elif [ -d /Applications/Obsidian.app ]; then
  obsidian_state=app-only
fi

runtime_report() {
  printf '%-22s %s\n' node "${node_version:-missing} (need v22+)"
  printf '%-22s %s\n' pnpm "${pnpm_version:-missing} (need 10+)"
  printf '%-22s %s\n' obsidian "$obsidian_state"
}

# --- pin ledger ------------------------------------------------------------

pins=$(mktemp "${TMPDIR:-/tmp}/phase2b-pins.XXXXXX") || exit 1
staging=
cleanup() {
  rm -f "$pins"
  [ -z "$staging" ] || rm -rf "$staging"
}
trap cleanup EXIT HUP INT TERM

sed -n '/^<!-- pins:start -->$/,/^<!-- pins:end -->$/p' "$pins_file" |
  grep '|' | grep -v '^<!--' >"$pins"
[ -s "$pins" ] || {
  note "pin ledger has no records"
  exit 1
}

trim() { printf '%s' "$1" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//'; }

runtime_satisfied() {
  case "$1" in
    none) return 0 ;;
    node22-pnpm10)
      [ "$node_ok" -eq 1 ] && [ "$pnpm_ok" -eq 1 ] && return 0
      return 1
      ;;
    *) return 1 ;;
  esac
}

# --- check mode ------------------------------------------------------------

if [ "$mode" = check ]; then
  runtime_report
  while IFS='|' read -r name ref_kind ref repo commit expected license runtime; do
    name=$(trim "${name:-}")
    [ -n "$name" ] || continue
    expected=$(trim "${expected:-}")
    runtime=$(trim "${runtime:-}")
    target="$tools_root/$name"
    if [ ! -d "$target" ]; then
      state=absent
    elif python3 "$tree_hash_script" "$target" --expect "$expected" >/dev/null 2>&1; then
      state=ready
    else
      state=hash-mismatch
    fi
    if runtime_satisfied "$runtime"; then
      printf '%-22s %s\n' "$name" "$state"
    else
      printf '%-22s %s (runtime %s unmet)\n' "$name" "$state" "$runtime"
    fi
  done <"$pins"
  exit 0
fi

# --- install mode ----------------------------------------------------------

command -v curl >/dev/null 2>&1 || {
  note "curl is required to download pinned sources"
  exit 1
}

mkdir -p "$tools_root" || exit 1

tag_still_points_at() {
  # Verifying the tag is a tamper signal, not the integrity mechanism: the
  # download is addressed by commit and the tree hash is what actually gates
  # placement. An unreachable API therefore reports and continues.
  repo=$1
  ref=$2
  commit=$3
  api="https://api.github.com/repos/$repo/git/ref/tags/$ref"
  resolved=$(curl -fsSL "$api" 2>/dev/null |
    sed -n 's/.*"sha"[[:space:]]*:[[:space:]]*"\([0-9a-f]\{40\}\)".*/\1/p' |
    head -n 1)
  if [ -z "$resolved" ]; then
    note "could not verify tag $ref for $repo; continuing on the pinned commit"
    return 0
  fi
  [ "$resolved" = "$commit" ] && return 0
  note "tag $ref for $repo moved to $resolved, expected $commit"
  return 1
}

while IFS='|' read -r name ref_kind ref repo commit expected license runtime; do
  name=$(trim "${name:-}")
  [ -n "$name" ] || continue
  ref_kind=$(trim "${ref_kind:-}")
  ref=$(trim "${ref:-}")
  repo=$(trim "${repo:-}")
  commit=$(trim "${commit:-}")
  expected=$(trim "${expected:-}")
  runtime=$(trim "${runtime:-}")

  case "$name" in
    */*|.|..|'') note "invalid pin name: $name"; failed=1; continue ;;
  esac
  case "$commit" in
    [0-9a-f][0-9a-f]*) ;;
    *) note "$name: commit must be a hex object id"; failed=1; continue ;;
  esac
  [ ${#expected} -eq 64 ] || {
    note "$name: tree hash must be 64 hex characters"
    failed=1
    continue
  }

  target="$tools_root/$name"

  if [ -d "$target" ]; then
    if python3 "$tree_hash_script" "$target" --expect "$expected" >/dev/null 2>&1; then
      printf '%-22s ready (unchanged)\n' "$name"
      continue
    fi
    # Overwriting here would destroy whatever local state produced the
    # difference, so the conflict is reported and left for a human.
    note "$name: existing checkout does not match the pin; remove $target to reinstall"
    failed=1
    continue
  fi

  if ! runtime_satisfied "$runtime"; then
    note "$name: runtime $runtime is not satisfied (node ${node_version:-missing}, pnpm ${pnpm_version:-missing})"
    failed=1
    continue
  fi

  if [ "$ref_kind" = tag ] && ! tag_still_points_at "$repo" "$ref" "$commit"; then
    failed=1
    continue
  fi

  staging=$(mktemp -d "$tools_root/.staging.XXXXXX") || {
    failed=1
    continue
  }
  archive="$staging/source.tar.gz"
  extracted="$staging/tree"
  mkdir -p "$extracted"

  if ! curl -fsSL -o "$archive" "https://codeload.github.com/$repo/tar.gz/$commit"; then
    note "$name: download failed for $repo@$commit"
    rm -rf "$staging"
    staging=
    failed=1
    continue
  fi
  if ! tar -xzf "$archive" -C "$extracted" --strip-components=1; then
    note "$name: archive could not be extracted"
    rm -rf "$staging"
    staging=
    failed=1
    continue
  fi
  if ! python3 "$tree_hash_script" "$extracted" --expect "$expected" >/dev/null; then
    note "$name: source hash does not match the pin; nothing was installed"
    rm -rf "$staging"
    staging=
    failed=1
    continue
  fi

  mv "$extracted" "$target" || {
    note "$name: could not place the verified tree"
    rm -rf "$staging"
    staging=
    failed=1
    continue
  }
  rm -rf "$staging"
  staging=
  printf '%-22s installed (%s@%s)\n' "$name" "$ref" "$commit"
done <"$pins"

printf '\n'
"$0" --check
exit "$failed"
