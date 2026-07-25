#!/bin/sh
#
# Place the Phase 2b external source pins under the untracked tool root.
#
# This installs source trees and builds local Node dependencies when authorized. It never runs upstream installers, never
# links into a global skill directory, and never touches the vault. Everything it writes lives under the tool root.

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
# Every integrity decision runs through python3. Without this gate a missing
# interpreter is indistinguishable from a hash mismatch, and the script would
# tell the user to delete a checkout that is actually intact.
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c '' >/dev/null 2>&1; then
  note "python3 is required to verify source hashes"
  exit 1
fi

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

# Records may be written with the surrounding pipes of a Markdown table. Those
# would otherwise leave the first field empty and make every pin look like a
# blank line to skip, so the installer would report success having installed
# nothing.
sed -n '/^<!-- pins:start -->$/,/^<!-- pins:end -->$/p' "$pins_file" |
  grep '|' | grep -v '^<!--' |
  sed 's/^[[:space:]]*|//; s/|[[:space:]]*$//' >"$pins"
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
  records=0
  while IFS='|' read -r name ref_kind ref repo commit expected license runtime; do
    name=$(trim "${name:-}")
    [ -n "$name" ] || continue
    records=$((records + 1))
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
  [ "$records" -gt 0 ] || {
    note "pin ledger has no usable records"
    exit 1
  }
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
  # placement. An unreachable API therefore reports and continues, which also
  # keeps an offline machine and an anonymous rate limit from blocking a
  # install whose integrity is already guaranteed by the hash.
  #
  # The commits endpoint is used rather than the tag ref because it resolves
  # an annotated tag to its commit; the ref endpoint would return the tag
  # object's own id and report a correct pin as moved.
  _repo=$1
  _ref=$2
  _commit=$3
  _resolved=$(curl -fsSL "https://api.github.com/repos/$_repo/commits/$_ref" 2>/dev/null |
    sed -n 's/^[[:space:]]*"sha"[[:space:]]*:[[:space:]]*"\([0-9a-f]\{40\}\)".*/\1/p' |
    head -n 1)
  if [ -z "$_resolved" ]; then
    note "could not verify tag $_ref for $_repo; continuing on the pinned commit"
    return 0
  fi
  [ "$_resolved" = "$_commit" ] && return 0
  note "tag $_ref for $_repo moved to $_resolved, expected $_commit"
  return 1
}

records=0
while IFS='|' read -r name ref_kind ref repo commit expected license runtime; do
  name=$(trim "${name:-}")
  [ -n "$name" ] || continue
  records=$((records + 1))
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
    # Placing source executes nothing, and one tree can hold tools with very
    # different needs, so withholding the whole tree would also withhold the
    # parts that run on their own. The requirement is reported here and
    # enforced by the adapter that actually runs something.
    note "$name: runtime $runtime unmet (node ${node_version:-missing}, pnpm ${pnpm_version:-missing}); placing source, dependent tools stay unavailable"
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

[ "$records" -gt 0 ] || {
  note "pin ledger has no usable records"
  exit 1
}

if [ "$mode" = install ] && [ "$node_ok" -eq 1 ] && [ "$pnpm_ok" -eq 1 ] && [ -f "$tools_root/understand-anything/package.json" ]; then
  note "installing and building understand-anything NPM dependencies (user authorized)..."
  (cd "$tools_root/understand-anything" && pnpm install --no-frozen-lockfile && pnpm -r build) || {
    note "understand-anything NPM dependency build failed"
    failed=1
  }
fi

printf '\n'
"$0" --check
exit "$failed"
