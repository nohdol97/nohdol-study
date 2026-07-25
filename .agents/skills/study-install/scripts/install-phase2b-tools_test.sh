#!/bin/sh
#
# The installer is exercised without reaching the network for any assertion
# that must hold on every machine. The one download case points at a pin that
# cannot resolve, so it fails the same way online and offline.

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
installer="$script_dir/install-phase2b-tools.sh"
tree_hash="$script_dir/tree_hash.py"

test_root=$(mktemp -d "${TMPDIR:-/tmp}/nohdol-study-phase2b.XXXXXX")
trap 'rm -rf "$test_root"' EXIT HUP INT TERM

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

# Stub runtimes so the gate is decided by the test, not by this machine.
stub_bin="$test_root/stub-bin"
mkdir -p "$stub_bin"
write_stub() {
  printf '#!/bin/sh\nprintf "%%s\\n" "%s"\n' "$2" >"$stub_bin/$1"
  chmod +x "$stub_bin/$1"
}

# A global skill root and a vault stand in for everything the installer must
# never touch.
home_root="$test_root/home"
mkdir -p "$home_root/.agents/skills/watch" "$home_root/.claude/skills"
printf 'global watch skill\n' >"$home_root/.agents/skills/watch/SKILL.md"
vault_root="$test_root/vault/wiki"
mkdir -p "$vault_root"
printf '# Note\n' >"$vault_root/note.md"

untouched_before=$(python3 "$tree_hash" "$home_root")
vault_before=$(python3 "$tree_hash" "$test_root/vault")

assert_untouched() {
  [ "$(python3 "$tree_hash" "$home_root")" = "$untouched_before" ] ||
    fail "global skill directory changed during $1"
  [ "$(python3 "$tree_hash" "$test_root/vault")" = "$vault_before" ] ||
    fail "vault changed during $1"
}

new_tools_root() {
  root="$test_root/$1"
  mkdir -p "$root"
  printf '%s' "$root"
}

write_pins() {
  root=$1
  shift
  {
    printf '<!-- pins:start -->\n```text\n'
    for record in "$@"; do
      printf '%s\n' "$record"
    done
    printf '```\n<!-- pins:end -->\n'
  } >"$root/PINS.md"
}

run_installer() {
  root=$1
  shift
  NOHDOL_STUDY_TOOLS_ROOT="$root" HOME="$home_root" \
    PATH="$stub_bin:$PATH" "$installer" "$@"
}

# 1. check reports an absent pin and installs nothing.
root_a=$(new_tools_root tools-a)
write_pins "$root_a" \
  'sample | commit | main | example/sample | abc123 | '"$(printf '0%.0s' $(seq 64))"' | MIT | none'
output=$(run_installer "$root_a" --check)
printf '%s' "$output" | grep -q 'sample .*absent' || fail "check did not report absent"
[ ! -d "$root_a/sample" ] || fail "check created a checkout"
assert_untouched "check"

# 2. An already-correct checkout is left alone and needs no network.
root_b=$(new_tools_root tools-b)
mkdir -p "$root_b/sample/nested"
printf 'content\n' >"$root_b/sample/nested/file.txt"
digest=$(python3 "$tree_hash" "$root_b/sample")
write_pins "$root_b" \
  "sample | commit | main | example/sample | abc123 | $digest | MIT | none"
run_installer "$root_b" --check | grep -q 'sample .*ready' ||
  fail "an unchanged checkout was not reported ready"
output=$(run_installer "$root_b" --install)
printf '%s' "$output" | grep -q 'ready (unchanged)' ||
  fail "install did not treat a matching checkout as complete"
[ "$(python3 "$tree_hash" "$root_b/sample")" = "$digest" ] ||
  fail "install modified a matching checkout"
assert_untouched "idempotent install"

# 3. A checkout that no longer matches its pin is reported, never overwritten.
root_c=$(new_tools_root tools-c)
mkdir -p "$root_c/sample"
printf 'local edit\n' >"$root_c/sample/file.txt"
write_pins "$root_c" \
  'sample | commit | main | example/sample | abc123 | '"$(printf 'a%.0s' $(seq 64))"' | MIT | none'
run_installer "$root_c" --check | grep -q 'hash-mismatch' ||
  fail "a diverged checkout was not reported"
if run_installer "$root_c" --install >"$test_root/out-c" 2>&1; then
  fail "install succeeded despite a hash conflict"
fi
grep -q 'does not match the pin' "$test_root/out-c" ||
  fail "the hash conflict was not explained"
grep -q 'local edit' "$root_c/sample/file.txt" ||
  fail "install overwrote a diverged checkout"
assert_untouched "hash conflict"

# 4. An unmet runtime fails closed before any download.
root_d=$(new_tools_root tools-d)
write_stub node v18.0.0
write_stub pnpm 9.0.0
write_pins "$root_d" \
  'needs-node | commit | main | example/sample | abc123 | '"$(printf '0%.0s' $(seq 64))"' | MIT | node22-pnpm10'
if run_installer "$root_d" --install >"$test_root/out-d" 2>&1; then
  fail "install succeeded with an unmet runtime"
fi
grep -q 'runtime node22-pnpm10 is not satisfied' "$test_root/out-d" ||
  fail "the runtime gate was not explained"
[ ! -d "$root_d/needs-node" ] || fail "an unrunnable checkout was placed"
assert_untouched "runtime gate"

# 5. A satisfied runtime passes the gate and then fails on the download.
write_stub node v22.1.0
write_stub pnpm 10.2.0
root_e=$(new_tools_root tools-e)
write_pins "$root_e" \
  'unreachable | commit | main | nohdol-study/does-not-exist | abc123 | '"$(printf '0%.0s' $(seq 64))"' | MIT | node22-pnpm10'
if run_installer "$root_e" --install >"$test_root/out-e" 2>&1; then
  fail "install succeeded for an unreachable pin"
fi
if grep -q 'is not satisfied' "$test_root/out-e"; then
  fail "the runtime gate rejected a satisfied runtime"
fi
grep -q 'download failed' "$test_root/out-e" ||
  fail "the download failure was not reported"
[ ! -d "$root_e/unreachable" ] || fail "a failed download left a checkout"
if find "$root_e" -maxdepth 1 -name '.staging.*' | grep -q .; then
  fail "a failed download left staging files"
fi
assert_untouched "download failure"

# 6. A malformed pin is rejected without touching the tool root.
root_f=$(new_tools_root tools-f)
write_pins "$root_f" \
  'sample | commit | main | example/sample | abc123 | tooshort | MIT | none'
if run_installer "$root_f" --install >"$test_root/out-f" 2>&1; then
  fail "install accepted a malformed tree hash"
fi
grep -q '64 hex characters' "$test_root/out-f" ||
  fail "the malformed pin was not explained"
assert_untouched "malformed pin"

# 7. The tracked ledger of this repository parses and reports every pin.
real_output=$("$installer" --check)
printf '%s' "$real_output" | grep -q 'understand-anything' ||
  fail "the tracked ledger did not report understand-anything"
printf '%s' "$real_output" | grep -q 'obsidian-skills' ||
  fail "the tracked ledger did not report obsidian-skills"

printf 'phase2b installer tests: PASS\n'
