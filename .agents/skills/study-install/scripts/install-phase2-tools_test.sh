#!/bin/sh

set -eu

source_script=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)/install-phase2-tools.sh
test_root=$(mktemp -d "${TMPDIR:-/tmp}/nohdol-study-phase2-tools.XXXXXX")
trap 'rm -rf "$test_root"' EXIT HUP INT TERM

mkdir -p "$test_root/home"

if env HOME="$test_root/home" PATH="/usr/bin:/bin" \
  "$source_script" --install >"$test_root/stdout" 2>"$test_root/stderr"; then
  printf 'FAIL: missing tool installation unexpectedly succeeded\n' >&2
  exit 1
fi

# A failure in the first source route must not prevent later checks.
grep -F 'npm is required for defuddle' "$test_root/stderr" >/dev/null
grep -F 'install yt-dlp with the system package manager' "$test_root/stderr" >/dev/null
grep -F 'uv is required for paper-search' "$test_root/stderr" >/dev/null
grep -F 'npx is required for watch' "$test_root/stderr" >/dev/null
grep -F 'watch installed but download.py was not found' "$test_root/stderr" >/dev/null
grep -F 'defuddle' "$test_root/stdout" >/dev/null
grep -F 'paper-search' "$test_root/stdout" >/dev/null
grep -F 'watch' "$test_root/stdout" >/dev/null

printf 'phase2 tool installer tests: PASS\n'
