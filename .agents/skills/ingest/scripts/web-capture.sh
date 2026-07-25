#!/bin/sh

set -eu

fail() {
  printf 'web-capture: %s\n' "$*" >&2
  exit 1
}

[ "$#" -eq 2 ] || fail "usage: web-capture.sh URL ASCII_SLUG"
source_url=$1
slug=$2

case "$source_url" in
  http://*|https://*) ;;
  *) fail "URL must start with http:// or https://" ;;
esac
# grep matches per line, so a slug whose first line is clean would pass
# even with an embedded newline. case tests the whole value at once.
case "$slug" in
  ''|[!A-Za-z0-9]*|*[!A-Za-z0-9._-]*)
    fail "slug must be ASCII letters, numbers, dot, underscore, or hyphen" ;;
esac
command -v defuddle >/dev/null 2>&1 || fail "defuddle is not installed"

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
study_root=$(CDPATH= cd -- "$script_dir/../../../.." && pwd -P)
[ -L "$study_root/vault" ] || fail "vault is not connected; run study-install"

target_dir="$study_root/vault/raw/web"
target="$target_dir/$(date +%F)-$slug.md"
mkdir -p "$target_dir"
[ ! -e "$target" ] && [ ! -L "$target" ] ||
  fail "capture already exists: $target"

temporary=$(mktemp "$target.tmp.XXXXXX")
trap 'rm -f "$temporary"' EXIT HUP INT TERM
defuddle parse "$source_url" --md -f -o "$temporary"
[ -s "$temporary" ] || fail "defuddle returned an empty document"
sed -n '1p' "$temporary" | grep -Fx -- '---' >/dev/null 2>&1 ||
  fail "defuddle output is missing frontmatter"
[ ! -e "$target" ] && [ ! -L "$target" ] ||
  fail "capture appeared concurrently: $target"
mv "$temporary" "$target"
trap - EXIT HUP INT TERM

printf '%s\n' "$target"
