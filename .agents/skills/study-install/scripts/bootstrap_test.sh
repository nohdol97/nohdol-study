#!/bin/sh

set -eu

source_script=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)/bootstrap.sh
test_root=$(mktemp -d "${TMPDIR:-/tmp}/nohdol-study-bootstrap.XXXXXX")
trap 'rm -rf "$test_root"' EXIT HUP INT TERM

make_harness() {
  harness=$1
  mkdir -p "$harness/.agents/skills/study-install/scripts" \
    "$harness/.agents/skills/notebooklm-export/scripts"
  cp "$source_script" "$harness/.agents/skills/study-install/scripts/bootstrap.sh"
  chmod +x "$harness/.agents/skills/study-install/scripts/bootstrap.sh"
  printf '%s\n' '#!/bin/sh' >"$harness/.agents/skills/notebooklm-export/scripts/export.sh"
  chmod +x "$harness/.agents/skills/notebooklm-export/scripts/export.sh"
}

canonical_dir() {
  CDPATH= cd -- "$1" && pwd -P
}

assert_file_contains() {
  file=$1
  expected=$2
  grep -F "$expected" "$file" >/dev/null || {
    printf 'FAIL: %s does not contain %s\n' "$file" "$expected" >&2
    exit 1
  }
}

# New plain-directory installation.
harness_one="$test_root/harness-one"
vault_one="$test_root/vault-one"
make_harness "$harness_one"
"$harness_one/.agents/skills/study-install/scripts/bootstrap.sh" \
  --vault "$vault_one" --profile personal --sync local --notebooklm consumer >/dev/null

[ "$(readlink "$harness_one/vault")" = "$(canonical_dir "$vault_one")" ]
[ -d "$vault_one/raw" ]
[ -d "$vault_one/wiki" ]
[ -f "$vault_one/index.md" ]
[ -f "$vault_one/log.md" ]
[ -f "$vault_one/hot.md" ]
assert_file_contains "$harness_one/REGISTRY.md" "Obsidian metadata: absent"
assert_file_contains "$harness_one/REGISTRY.md" "NotebookLM: consumer"
assert_file_contains "$harness_one/REGISTRY.md" \
  "NotebookLM workflow: snapshot-export-ready-account-unverified"

# Re-running preserves existing files.
printf '\nPRESERVE-ME\n' >>"$vault_one/index.md"
"$harness_one/.agents/skills/study-install/scripts/bootstrap.sh" \
  --vault "$vault_one" --profile corporate --sync other >/dev/null
assert_file_contains "$vault_one/index.md" "PRESERVE-ME"
assert_file_contains "$harness_one/REGISTRY.md" "profile: corporate"
assert_file_contains "$harness_one/REGISTRY.md" "sync: other"
# An omitted policy flag keeps the recorded choice instead of resetting it.
assert_file_contains "$harness_one/REGISTRY.md" "NotebookLM: consumer"
"$harness_one/.agents/skills/study-install/scripts/bootstrap.sh" \
  --vault "$vault_one" --profile corporate >/dev/null
assert_file_contains "$harness_one/REGISTRY.md" "NotebookLM: consumer"
assert_file_contains "$harness_one/REGISTRY.md" "sync: other"
# An explicit flag still changes the recorded choice.
"$harness_one/.agents/skills/study-install/scripts/bootstrap.sh" \
  --vault "$vault_one" --profile corporate --notebooklm off >/dev/null
assert_file_contains "$harness_one/REGISTRY.md" "NotebookLM: off"

# Existing Obsidian metadata is detected.
harness_two="$test_root/harness-two"
vault_two="$test_root/vault-two"
make_harness "$harness_two"
mkdir -p "$vault_two/.obsidian"
"$harness_two/.agents/skills/study-install/scripts/bootstrap.sh" \
  --vault "$vault_two" --profile corporate --sync obsidian-sync >/dev/null
assert_file_contains "$harness_two/REGISTRY.md" "Obsidian metadata: detected"
assert_file_contains "$harness_two/REGISTRY.md" "profile: corporate"

# A knowledge root inside the harness is rejected.
harness_three="$test_root/harness-three"
make_harness "$harness_three"
if "$harness_three/.agents/skills/study-install/scripts/bootstrap.sh" \
  --vault "$harness_three/knowledge" --profile personal >/dev/null 2>&1; then
  printf 'FAIL: internal knowledge root was accepted\n' >&2
  exit 1
fi
[ ! -e "$harness_three/knowledge" ]

# A real vault path at the link location is never replaced.
harness_four="$test_root/harness-four"
make_harness "$harness_four"
mkdir -p "$harness_four/vault"
if "$harness_four/.agents/skills/study-install/scripts/bootstrap.sh" \
  --vault "$test_root/vault-four" --profile personal >/dev/null 2>&1; then
  printf 'FAIL: real vault directory was replaced\n' >&2
  exit 1
fi

# A conflicting symlink requires explicit replacement.
harness_five="$test_root/harness-five"
make_harness "$harness_five"
mkdir -p "$test_root/vault-five-a" "$test_root/vault-five-b"
ln -s "$test_root/vault-five-a" "$harness_five/vault"
if "$harness_five/.agents/skills/study-install/scripts/bootstrap.sh" \
  --vault "$test_root/vault-five-b" --profile personal >/dev/null 2>&1; then
  printf 'FAIL: conflicting vault symlink changed without confirmation flag\n' >&2
  exit 1
fi
"$harness_five/.agents/skills/study-install/scripts/bootstrap.sh" \
  --vault "$test_root/vault-five-b" --profile personal --replace-link >/dev/null
[ "$(readlink "$harness_five/vault")" = "$(canonical_dir "$test_root/vault-five-b")" ]

# Existing incompatible baseline filenames are preserved and rejected.
harness_six="$test_root/harness-six"
vault_six="$test_root/vault-six"
make_harness "$harness_six"
mkdir -p "$vault_six"
printf '%s\n' '# Existing unrelated index' >"$vault_six/index.md"
if "$harness_six/.agents/skills/study-install/scripts/bootstrap.sh" \
  --vault "$vault_six" --profile personal >/dev/null 2>&1; then
  printf 'FAIL: incompatible existing index was accepted\n' >&2
  exit 1
fi
assert_file_contains "$vault_six/index.md" "Existing unrelated index"
[ ! -e "$harness_six/vault" ]

printf 'bootstrap tests: PASS\n'
