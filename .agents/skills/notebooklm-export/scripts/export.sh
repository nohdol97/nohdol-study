#!/bin/sh

set -eu

fail() {
  printf 'notebooklm-export: %s\n' "$*" >&2
  exit 1
}

sha256_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    fail "shasum or sha256sum is required"
  fi
}

name=
output=
include_unverified=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --name)
      [ "$#" -ge 2 ] || fail "--name requires an ASCII slug"
      name=$2
      shift 2
      ;;
    --output)
      [ "$#" -ge 2 ] || fail "--output requires an absolute path"
      output=$2
      shift 2
      ;;
    --include-unverified)
      include_unverified=1
      shift
      ;;
    --)
      shift
      break
      ;;
    -*)
      fail "unknown option: $1"
      ;;
    *)
      break
      ;;
  esac
done

[ -n "$name" ] || fail "--name is required"
# grep matches per line, so a name whose first line is clean would pass even
# with an embedded newline. case tests the whole value at once.
case "$name" in
  ''|[!A-Za-z0-9]*|*[!A-Za-z0-9._-]*) fail "--name must be an ASCII slug" ;;
esac
[ "$#" -gt 0 ] || fail "select at least one vault file"

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
study_root=$(CDPATH= cd -- "$script_dir/../../../.." && pwd -P)
[ -L "$study_root/vault" ] || fail "vault is not connected; run study-install"
vault_root=$(CDPATH= cd -- "$study_root/vault" && pwd -P)

if [ -z "$output" ]; then
  timestamp=$(date +%Y%m%d-%H%M%S)
  output="$study_root/_workspace/notebooklm/$name-$timestamp"
else
  case "$output" in
    /*) ;;
    *) fail "--output must be absolute" ;;
  esac
fi

[ ! -e "$output" ] && [ ! -L "$output" ] ||
  fail "output already exists: $output"

for selected_file in "$@"; do
  [ -f "$selected_file" ] || fail "not a file: $selected_file"
  [ ! -L "$selected_file" ] || fail "symlinked sources are not accepted: $selected_file"
  selected_dir=$(CDPATH= cd -- "$(dirname -- "$selected_file")" && pwd -P)
  selected_abs="$selected_dir/$(basename -- "$selected_file")"
  case "$selected_abs" in
    "$vault_root"/*) ;;
    *) fail "source is outside the connected vault: $selected_file" ;;
  esac

  relative=${selected_abs#"$vault_root/"}
  case "$relative" in
    wiki/*.md)
      verification=$(sed -n 's/^verification:[[:space:]]*//p' "$selected_abs" | sed -n '1p')
      case "$verification" in
        source-backed|primary-confirmed|cross-checked|contested) ;;
        *)
          [ "$include_unverified" -eq 1 ] ||
            fail "$relative is missing an acceptable verification state"
          ;;
      esac
      ;;
  esac
done

mkdir -p "$output/sources"
generated_at=$(date '+%Y-%m-%dT%H:%M:%S%z')
manifest="$output/00-manifest.md"

cat >"$manifest" <<EOF
# NotebookLM source manifest — $name

- generated: $generated_at
- mode: evidence-preserving snapshot
- source of truth: connected nohdol-study vault

> Upload this manifest with the files under \`sources/\`. NotebookLM output is
> derived study material, not verified evidence. Follow citations back to these
> sources before retaining any generated claim.

| File | SHA-256 | Verification | Checked |
|---|---|---|---|
EOF

for selected_file in "$@"; do
  selected_dir=$(CDPATH= cd -- "$(dirname -- "$selected_file")" && pwd -P)
  selected_abs="$selected_dir/$(basename -- "$selected_file")"
  relative=${selected_abs#"$vault_root/"}
  destination="$output/sources/$relative"
  mkdir -p "$(dirname -- "$destination")"
  cp -p "$selected_abs" "$destination"

  verification=source
  checked='n/a'
  case "$relative" in
    *.md)
      found_verification=$(sed -n 's/^verification:[[:space:]]*//p' "$selected_abs" | sed -n '1p')
      found_checked=$(sed -n 's/^checked:[[:space:]]*//p' "$selected_abs" | sed -n '1p')
      [ -z "$found_verification" ] || verification=$found_verification
      [ -z "$found_checked" ] || checked=$found_checked
      ;;
  esac

  escaped_relative=$(printf '%s' "$relative" | sed 's/|/\\|/g')
  printf '| `%s` | `%s` | %s | %s |\n' \
    "$escaped_relative" "$(sha256_file "$selected_abs")" "$verification" "$checked" >>"$manifest"
done

printf '%s\n' "$output"
