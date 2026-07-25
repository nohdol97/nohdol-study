#!/bin/sh
#
# Decide whether the optional NotebookLM CLI bridge may be installed.
#
# This script only reads release metadata. It never installs anything, never
# authenticates, and never sends vault content anywhere. Its whole job is to
# answer one question before any of that becomes possible: does the latest
# stable release contain the audited download-redirect fix?
#
# Unlike the source-pin tag check, this one fails closed when it cannot reach
# the API. That check guarded against tampering while a tree hash still
# decided the outcome; this one guards against installing a release with a
# known unfixed vulnerability, and "I could not tell" is not permission.

set -u

REPO=teng-lin/notebooklm-py
# docs/reviews/2026-07-25-notebooklm-understand-anything-security.md, finding
# N3: the download path follows redirects without re-validating each hop
# against the host allowlist until this commit.
FIX_COMMIT=0a6e28a0522b3542695e6666054e88060ef3de48
API=${NOHDOL_STUDY_NOTEBOOKLM_API:-https://api.github.com}

note() { printf 'notebooklm-bridge: %s\n' "$*" >&2; }

blocked() {
  note "$*"
  printf 'verdict     blocked\n'
  exit 1
}

command -v curl >/dev/null 2>&1 || blocked "curl is required to audit the release"
command -v python3 >/dev/null 2>&1 || blocked "python3 is required to read the release metadata"

# Observation only: whether the CLI happens to be present already. Its
# presence does not grant permission, and its absence is not a failure.
if command -v notebooklm >/dev/null 2>&1; then
  installed=$(notebooklm --version 2>/dev/null | head -n 1)
  printf '%-12s %s\n' cli "present (${installed:-version unknown})"
else
  printf '%-12s %s\n' cli "absent"
fi

releases=$(curl -fsSL "$API/repos/$REPO/releases?per_page=30" 2>/dev/null) ||
  blocked "release list could not be fetched; cannot confirm the fix is shipped"

stable=$(printf '%s' "$releases" | python3 -c '
import json, sys

try:
    releases = json.load(sys.stdin)
except ValueError:
    sys.exit(1)
if not isinstance(releases, list):
    sys.exit(1)
for release in releases:
    if release.get("prerelease") or release.get("draft"):
        continue
    tag = (release.get("tag_name") or "").strip()
    if tag:
        print(tag)
        break
' 2>/dev/null) || blocked "release metadata could not be read"

[ -n "$stable" ] || blocked "no stable release found; pre-releases are not eligible"
printf '%-12s %s\n' "stable" "$stable"

comparison=$(curl -fsSL "$API/repos/$REPO/compare/$FIX_COMMIT...$stable" 2>/dev/null) ||
  blocked "could not compare $stable against the audited fix"

status=$(printf '%s' "$comparison" | python3 -c '
import json, sys

try:
    print((json.load(sys.stdin).get("status") or "").strip())
except ValueError:
    pass
' 2>/dev/null)

case "$status" in
  ahead|identical) ;;
  behind|diverged)
    blocked "stable release $stable does not contain the download-redirect fix ($status)"
    ;;
  *)
    blocked "comparison against the audited fix was inconclusive"
    ;;
esac

printf '%-12s %s\n' "fix" "present in $stable"
cat <<'EOF'
verdict     release gate passed

The release gate is only the first of the conditions in ADR 003. Before any
install, a dependency audit of the exact browser and cookie extras must also
come back clean, and authentication remains a separate step the user runs
against a profile they name. Nothing here authorizes a transfer.
EOF
exit 0
