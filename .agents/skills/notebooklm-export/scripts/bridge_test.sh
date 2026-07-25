#!/bin/sh
#
# The release gate is exercised against a stubbed API so the verdict is
# decided by the test rather than by whatever upstream published today. The
# packet verifier needs no network at all.

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
gate="$script_dir/bridge-gate.sh"
verify="$script_dir/verify-packet.sh"
export_script="$script_dir/export.sh"

test_root=$(mktemp -d "${TMPDIR:-/tmp}/nohdol-study-bridge.XXXXXX")
trap 'rm -rf "$test_root"' EXIT HUP INT TERM

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

sha256_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    sha256sum "$1" | awk '{print $1}'
  fi
}

# --- release gate -----------------------------------------------------------

stub_bin="$test_root/stub-bin"
mkdir -p "$stub_bin"

# The stub answers the two endpoints the gate reads from files the test
# controls, and fails any request it was not set up for.
cat >"$stub_bin/curl" <<STUB
#!/bin/sh
for argument in "\$@"; do
  case "\$argument" in
    *"/releases?"*)
      cat "$test_root/releases.json" 2>/dev/null || exit 22
      exit 0
      ;;
    *"/compare/"*)
      cat "$test_root/compare.json" 2>/dev/null || exit 22
      exit 0
      ;;
  esac
done
exit 22
STUB
chmod +x "$stub_bin/curl"

run_gate() { PATH="$stub_bin:$PATH" sh "$gate"; }

# A stable release that contains the fix passes.
printf '[{"tag_name": "v9.9.9", "prerelease": false, "draft": false}]\n' \
  >"$test_root/releases.json"
printf '{"status": "ahead"}\n' >"$test_root/compare.json"
output=$(run_gate) || fail "the gate blocked a fixed stable release"
printf '%s' "$output" | grep -q 'release gate passed' ||
  fail "the passing verdict was not reported"
printf '%s' "$output" | grep -q 'stable       v9.9.9' ||
  fail "the audited release was not named"
# Passing the release gate is not permission to install.
printf '%s' "$output" | grep -q 'dependency audit' ||
  fail "the remaining conditions were not stated"

# A stable release that predates the fix is blocked.
printf '{"status": "diverged"}\n' >"$test_root/compare.json"
if run_gate >"$test_root/out" 2>&1; then
  fail "the gate passed a release without the fix"
fi
grep -q 'does not contain the download-redirect fix' "$test_root/out" ||
  fail "the blocking reason was not explained"
grep -q 'verdict     blocked' "$test_root/out" || fail "no blocked verdict"

printf '{"status": "behind"}\n' >"$test_root/compare.json"
if run_gate >/dev/null 2>&1; then fail "a behind release was accepted"; fi

# Pre-releases are not eligible, even when they carry the fix.
printf '[{"tag_name": "v9.9.9rc1", "prerelease": true, "draft": false}]\n' \
  >"$test_root/releases.json"
printf '{"status": "ahead"}\n' >"$test_root/compare.json"
if run_gate >"$test_root/out" 2>&1; then
  fail "a pre-release satisfied the gate"
fi
grep -q 'no stable release found' "$test_root/out" ||
  fail "the pre-release exclusion was not explained"

# An unreachable API blocks rather than assuming the best.
rm -f "$test_root/releases.json"
if run_gate >"$test_root/out" 2>&1; then
  fail "the gate passed without reaching the API"
fi
grep -q 'cannot confirm' "$test_root/out" || fail "the offline reason was not explained"

# An inconclusive comparison also blocks.
printf '[{"tag_name": "v9.9.9", "prerelease": false, "draft": false}]\n' \
  >"$test_root/releases.json"
printf '{"nothing": true}\n' >"$test_root/compare.json"
if run_gate >"$test_root/out" 2>&1; then
  fail "an inconclusive comparison was treated as a pass"
fi
grep -q 'inconclusive' "$test_root/out" || fail "the inconclusive reason was not explained"

# --- packet verification ----------------------------------------------------

vault="$test_root/vault"
mkdir -p "$vault/wiki" "$vault/raw"
cat >"$vault/wiki/note.md" <<'EOF'
---
type: concept
verification: cross-checked
checked: 2026-07-25
---
# Note

Body.
EOF
printf 'source bytes\n' >"$vault/raw/source.md"

packet_root="$test_root/packets"
mkdir -p "$packet_root"
packet=$(cd "$test_root" && NOTEBOOKLM_EXPORT_ROOT="$packet_root" sh "$export_script" \
  --name sample "$vault/wiki/note.md" "$vault/raw/source.md" 2>/dev/null | tail -n 1) ||
  packet=""
if [ -z "$packet" ] || [ ! -d "$packet" ]; then
  # The exporter resolves its own output root; fall back to building a packet
  # by hand so the verifier is still covered.
  packet="$packet_root/manual"
  mkdir -p "$packet/sources/wiki" "$packet/sources/raw"
  cp "$vault/wiki/note.md" "$packet/sources/wiki/note.md"
  cp "$vault/raw/source.md" "$packet/sources/raw/source.md"
  {
    printf '# NotebookLM source manifest — manual\n\n'
    printf '| File | SHA-256 | Verification | Checked |\n|---|---|---|---|\n'
    printf '| `wiki/note.md` | `%s` | cross-checked | 2026-07-25 |\n' \
      "$(sha256_file "$packet/sources/wiki/note.md")"
    printf '| `raw/source.md` | `%s` | source | n/a |\n' \
      "$(sha256_file "$packet/sources/raw/source.md")"
  } >"$packet/00-manifest.md"
fi

sh "$verify" "$packet" >/dev/null || fail "a freshly built packet did not verify"

# Content edited after export is caught.
work="$test_root/edited"
cp -R "$packet" "$work"
printf 'tampered\n' >>"$work/sources/raw/source.md"
if sh "$verify" "$work" >"$test_root/out" 2>&1; then
  fail "an edited file passed verification"
fi
grep -q 'content changed since export' "$test_root/out" ||
  fail "the content change was not explained"

# A file the manifest never listed cannot ride along.
work="$test_root/extra"
cp -R "$packet" "$work"
printf 'unreviewed\n' >"$work/sources/stowaway.md"
if sh "$verify" "$work" >"$test_root/out" 2>&1; then
  fail "an unlisted file passed verification"
fi
grep -q 'not listed in the manifest' "$test_root/out" ||
  fail "the unlisted file was not named"

# A symlink is refused rather than followed.
work="$test_root/linked"
cp -R "$packet" "$work"
ln -s /etc/hosts "$work/sources/link.md"
if sh "$verify" "$work" >"$test_root/out" 2>&1; then
  fail "a packet containing a symlink passed"
fi
grep -q 'symlink' "$test_root/out" || fail "the symlink was not reported"

# A listed file replaced by a symlink is refused as a symlink, and its target
# is never read: reporting a content change would mean the verifier followed
# the link out of the packet.
work="$test_root/listed-link"
cp -R "$packet" "$work"
printf 'content from outside the packet\n' >"$test_root/outside.md"
rm "$work/sources/raw/source.md"
ln -s "$test_root/outside.md" "$work/sources/raw/source.md"
if sh "$verify" "$work" >"$test_root/out" 2>&1; then
  fail "a listed symlink passed verification"
fi
grep -q 'listed file is a symlink: raw/source.md' "$test_root/out" ||
  fail "the listed symlink was not named"
if grep -q 'content changed since export: raw/source.md' "$test_root/out"; then
  fail "the verifier read through the symlink instead of refusing it"
fi

# A missing file is caught.
work="$test_root/missing"
cp -R "$packet" "$work"
rm "$work/sources/wiki/note.md"
if sh "$verify" "$work" >"$test_root/out" 2>&1; then
  fail "a packet missing a listed file passed"
fi
grep -q 'listed file is missing' "$test_root/out" || fail "the missing file was not named"

# An unverified note is refused at upload time, not only at export time.
work="$test_root/unverified"
cp -R "$packet" "$work"
sed 's/cross-checked/unverified/' "$work/00-manifest.md" >"$work/00-manifest.md.new"
mv "$work/00-manifest.md.new" "$work/00-manifest.md"
if sh "$verify" "$work" >"$test_root/out" 2>&1; then
  fail "an unverified note passed verification"
fi
grep -q 'unverified note in packet' "$test_root/out" ||
  fail "the unverified note was not named"

# An entry beside the reviewed set is surfaced without failing the packet.
work="$test_root/sibling"
cp -R "$packet" "$work"
mkdir -p "$work/upload"
printf 'flattened copy\n' >"$work/upload/01-note.md"
sh "$verify" "$work" >"$test_root/out" 2>&1 ||
  fail "a sibling directory should not fail the packet"
grep -q 'not part of the reviewed set' "$test_root/out" ||
  fail "the sibling directory was not surfaced"

# A manifest with no rows is an error, never an empty success.
work="$test_root/norows"
cp -R "$packet" "$work"
printf '# empty manifest\n' >"$work/00-manifest.md"
if sh "$verify" "$work" >"$test_root/out" 2>&1; then
  fail "a manifest with no rows passed"
fi
grep -q 'lists no files' "$test_root/out" || fail "the empty manifest was not explained"

printf 'notebooklm bridge tests: PASS\n'
