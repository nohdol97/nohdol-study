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

# 4. An unmet runtime is reported, not enforced at install time. Placing
# source executes nothing, and one tree can hold tools with different needs,
# so the requirement is carried to the adapter that runs something.
root_d=$(new_tools_root tools-d)
write_stub node v18.0.0
write_stub pnpm 9.0.0
write_pins "$root_d" \
  'needs-node | commit | main | example/sample | abc123 | '"$(printf '0%.0s' $(seq 64))"' | MIT | node22-pnpm10'
run_installer "$root_d" --check | grep -q 'runtime node22-pnpm10 unmet' ||
  fail "check did not report the unmet runtime"
run_installer "$root_d" --install >"$test_root/out-d" 2>&1 || true
grep -q 'runtime node22-pnpm10 unmet' "$test_root/out-d" ||
  fail "install did not report the unmet runtime"
if grep -q 'is not satisfied' "$test_root/out-d"; then
  fail "an unmet runtime still blocked placement"
fi
assert_untouched "runtime report"

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

# 7. Records wrapped in Markdown table pipes still parse. Without this the
# leading pipe empties the first field and every pin is skipped as blank,
# so the installer would report success having installed nothing.
root_g=$(new_tools_root tools-g)
mkdir -p "$root_g/sample"
printf 'content\n' >"$root_g/sample/file.txt"
digest=$(python3 "$tree_hash" "$root_g/sample")
write_pins "$root_g" \
  "| sample | commit | main | example/sample | abc123 | $digest | MIT | none |"
run_installer "$root_g" --check | grep -q 'sample .*ready' ||
  fail "a table-formatted record was not parsed"

# A ledger with no record at all is an error.
root_h=$(new_tools_root tools-h)
printf '<!-- pins:start -->\n```text\n```\n<!-- pins:end -->\n' >"$root_h/PINS.md"
if run_installer "$root_h" --install >"$test_root/out-h" 2>&1; then
  fail "install reported success for an empty ledger"
fi

# So is a ledger whose lines survive extraction but carry no usable name.
# Skipping those silently would install nothing and still report success.
root_h2=$(new_tools_root tools-h2)
write_pins "$root_h2" '  |  |  |  |  |  |  |  '
if run_installer "$root_h2" --install >"$test_root/out-h2" 2>&1; then
  fail "install reported success for a ledger with no usable record"
fi
grep -q 'no usable records' "$test_root/out-h2" ||
  fail "the unusable ledger was not explained"
if run_installer "$root_h2" --check >"$test_root/out-h3" 2>&1; then
  fail "check reported success for a ledger with no usable record"
fi

# The remaining cases need a download. A stub curl keeps them offline: the
# archive comes from a local fixture and the tag lookup returns a chosen sha.
fixture="$test_root/fixture"
mkdir -p "$fixture/root/nested"
printf 'pinned content\n' >"$fixture/root/nested/file.txt"
tar -czf "$fixture/source.tar.gz" -C "$fixture" root
mkdir -p "$fixture/expected"
tar -xzf "$fixture/source.tar.gz" -C "$fixture/expected" --strip-components=1
fixture_digest=$(python3 "$tree_hash" "$fixture/expected")

cat >"$stub_bin/curl" <<STUB
#!/bin/sh
# Serve the tag lookup from a file and every download from the fixture.
target=
for argument in "\$@"; do
  case "\$argument" in
    *api.github.com*)
      cat "$test_root/tag-response.json" 2>/dev/null || exit 22
      exit 0
      ;;
  esac
done
previous=
for argument in "\$@"; do
  [ "\$previous" = "-o" ] && target=\$argument
  previous=\$argument
done
[ -n "\$target" ] || exit 22
cp "$fixture/source.tar.gz" "\$target"
STUB
chmod +x "$stub_bin/curl"

# 8. A download whose tree hash differs from the pin installs nothing.
root_i=$(new_tools_root tools-i)
write_pins "$root_i" \
  'sample | commit | main | example/sample | abc123 | '"$(printf 'b%.0s' $(seq 64))"' | MIT | none'
if run_installer "$root_i" --install >"$test_root/out-i" 2>&1; then
  fail "install accepted a tree whose hash differs from the pin"
fi
grep -q 'source hash does not match' "$test_root/out-i" ||
  fail "the source hash mismatch was not explained"
[ ! -d "$root_i/sample" ] || fail "a mismatched tree was placed"
if find "$root_i" -maxdepth 1 -name '.staging.*' | grep -q .; then
  fail "a rejected download left staging files"
fi
assert_untouched "source hash mismatch"

# 9. A matching download is placed, and re-running changes nothing.
root_j=$(new_tools_root tools-j)
write_pins "$root_j" \
  "sample | commit | main | example/sample | abc123 | $fixture_digest | MIT | none"
run_installer "$root_j" --install >"$test_root/out-j" 2>&1 ||
  fail "install rejected a matching download"
grep -q 'sample .*installed' "$test_root/out-j" ||
  fail "the placement was not reported"
[ -f "$root_j/sample/nested/file.txt" ] || fail "the verified tree was not placed"
if find "$root_j" -maxdepth 1 -name '.staging.*' | grep -q .; then
  fail "a successful install left staging files"
fi
run_installer "$root_j" --install >"$test_root/out-j2" 2>&1 ||
  fail "the second install run failed"
grep -q 'ready (unchanged)' "$test_root/out-j2" ||
  fail "the second run did not recognize the existing tree"
assert_untouched "successful install"

# 10. A tag that no longer resolves to the pinned commit blocks the install.
root_k=$(new_tools_root tools-k)
printf '{\n  "sha": "%s"\n}\n' "$(printf 'c%.0s' $(seq 40))" \
  >"$test_root/tag-response.json"
write_pins "$root_k" \
  "sample | tag | v1.0.0 | example/sample | $(printf 'd%.0s' $(seq 40)) | $fixture_digest | MIT | none"
if run_installer "$root_k" --install >"$test_root/out-k" 2>&1; then
  fail "install accepted a moved tag"
fi
grep -q 'moved to' "$test_root/out-k" || fail "the moved tag was not explained"
[ ! -d "$root_k/sample" ] || fail "a moved tag still placed a tree"

# The same pin installs once the tag resolves to the pinned commit.
pinned_commit=$(printf 'd%.0s' $(seq 40))
printf '{\n  "sha": "%s"\n}\n' "$pinned_commit" >"$test_root/tag-response.json"
run_installer "$root_k" --install >"$test_root/out-k2" 2>&1 ||
  fail "install rejected a tag that still matches"
[ -f "$root_k/sample/nested/file.txt" ] || fail "the verified tree was not placed"
assert_untouched "tag verification"

rm -f "$stub_bin/curl"

# 11. Without a working python3 nothing can be verified. The installer must
# say so rather than let a failed check read as a hash mismatch, which would
# advise deleting an intact checkout.
root_l=$(new_tools_root tools-l)
mkdir -p "$root_l/sample"
printf 'content\n' >"$root_l/sample/file.txt"
intact_digest=$(python3 "$tree_hash" "$root_l/sample")
write_pins "$root_l" \
  "sample | commit | main | example/sample | abc123 | $intact_digest | MIT | none"
printf '#!/bin/sh\nexit 127\n' >"$stub_bin/python3"
chmod +x "$stub_bin/python3"
if run_installer "$root_l" --install >"$test_root/out-l" 2>&1; then
  fail "install continued without a usable python3"
fi
grep -q 'python3 is required' "$test_root/out-l" ||
  fail "the missing interpreter was not explained"
if grep -q 'remove' "$test_root/out-l"; then
  fail "an intact checkout was reported as a hash conflict"
fi
rm -f "$stub_bin/python3"
[ -f "$root_l/sample/file.txt" ] || fail "the intact checkout was disturbed"

# 12. The tracked ledger of this repository parses and reports every pin.
real_output=$("$installer" --check)
printf '%s' "$real_output" | grep -q 'understand-anything' ||
  fail "the tracked ledger did not report understand-anything"
printf '%s' "$real_output" | grep -q 'obsidian-skills' ||
  fail "the tracked ledger did not report obsidian-skills"

printf 'phase2b installer tests: PASS\n'
