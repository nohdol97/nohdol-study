#!/bin/sh

set -eu

source_script=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)/web-capture.sh
test_root=$(mktemp -d "${TMPDIR:-/tmp}/nohdol-study-web.XXXXXX")
trap 'rm -rf "$test_root"' EXIT HUP INT TERM

harness="$test_root/harness"
knowledge="$test_root/knowledge"
fake_bin="$test_root/bin"
mkdir -p "$harness/.agents/skills/ingest/scripts" "$knowledge" "$fake_bin"
cp "$source_script" "$harness/.agents/skills/ingest/scripts/web-capture.sh"
chmod +x "$harness/.agents/skills/ingest/scripts/web-capture.sh"
ln -s "$knowledge" "$harness/vault"

cat >"$fake_bin/defuddle" <<'EOF'
#!/bin/sh
output=
seen_frontmatter=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    -o|--output) output=$2; shift 2 ;;
    -f|--frontmatter) seen_frontmatter=1; shift ;;
    *) shift ;;
  esac
done
[ "$seen_frontmatter" -eq 1 ] || exit 9
cat >"$output" <<'DOC'
---
title: Captured
source: https://example.com/article
---
# Captured
DOC
EOF
chmod +x "$fake_bin/defuddle"

target=$(PATH="$fake_bin:$PATH" \
  "$harness/.agents/skills/ingest/scripts/web-capture.sh" \
  https://example.com/article article)
[ -f "$target" ]
grep -F '# Captured' "$target" >/dev/null

if PATH="$fake_bin:$PATH" \
  "$harness/.agents/skills/ingest/scripts/web-capture.sh" \
  https://example.com/article article >/dev/null 2>&1; then
  printf 'FAIL: existing capture was overwritten\n' >&2
  exit 1
fi
grep -F '# Captured' "$target" >/dev/null

printf 'web capture tests: PASS\n'
