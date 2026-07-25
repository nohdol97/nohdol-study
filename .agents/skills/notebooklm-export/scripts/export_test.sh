#!/bin/sh

set -eu

source_script=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)/export.sh
test_root=$(mktemp -d "${TMPDIR:-/tmp}/nohdol-study-notebooklm.XXXXXX")
trap 'rm -rf "$test_root"' EXIT HUP INT TERM

harness="$test_root/harness"
knowledge="$test_root/knowledge"
mkdir -p "$harness/.agents/skills/notebooklm-export/scripts" \
  "$knowledge/wiki" "$knowledge/raw"
cp "$source_script" "$harness/.agents/skills/notebooklm-export/scripts/export.sh"
chmod +x "$harness/.agents/skills/notebooklm-export/scripts/export.sh"
ln -s "$knowledge" "$harness/vault"

cat >"$knowledge/wiki/verified.md" <<'EOF'
---
type: concept
verification: primary-confirmed
checked: 2026-07-25
---
# Verified
EOF
cat >"$knowledge/wiki/unverified.md" <<'EOF'
---
type: concept
verification: unverified
checked: 2026-07-25
---
# Unverified
EOF
printf '%s\n' 'primary source' >"$knowledge/raw/source.txt"

before=$(shasum -a 256 "$knowledge/wiki/verified.md" | awk '{print $1}')
output="$test_root/export"
"$harness/.agents/skills/notebooklm-export/scripts/export.sh" \
  --name robotics --output "$output" \
  "$knowledge/wiki/verified.md" "$knowledge/raw/source.txt" >/dev/null

[ -f "$output/00-manifest.md" ]
[ -f "$output/sources/wiki/verified.md" ]
[ -f "$output/sources/raw/source.txt" ]
grep -F 'primary-confirmed' "$output/00-manifest.md" >/dev/null
grep -F "$before" "$output/00-manifest.md" >/dev/null
after=$(shasum -a 256 "$knowledge/wiki/verified.md" | awk '{print $1}')
[ "$before" = "$after" ]

if "$harness/.agents/skills/notebooklm-export/scripts/export.sh" \
  --name unsafe --output "$test_root/unsafe" \
  "$knowledge/wiki/unverified.md" >/dev/null 2>&1; then
  printf 'FAIL: unverified note was exported\n' >&2
  exit 1
fi
[ ! -e "$test_root/unsafe" ]

printf 'notebooklm export tests: PASS\n'
