#!/bin/sh
#
# Re-verify an export packet against its own manifest before it is uploaded.
#
# The manifest records what was true when the packet was built. Anything can
# happen to a directory between then and an upload - an edit, a stray file
# dropped in, a symlink pointing outside. This checks the packet still matches
# what the manifest claims, so what leaves the machine is exactly what was
# reviewed.
#
# Usage: verify-packet.sh PACKET_DIR

set -u

fail() {
  printf 'verify-packet: %s\n' "$*" >&2
  exit 1
}

problem() {
  printf 'verify-packet: %s\n' "$*" >&2
  problems=$((problems + 1))
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

[ "$#" -eq 1 ] || fail "usage: verify-packet.sh PACKET_DIR"
packet=$1
[ -d "$packet" ] || fail "not a directory: $packet"

manifest="$packet/00-manifest.md"
sources="$packet/sources"
[ -f "$manifest" ] || fail "manifest not found: $manifest"
[ -d "$sources" ] || fail "sources directory not found: $sources"

problems=0
listed=$(mktemp "${TMPDIR:-/tmp}/verify-packet.XXXXXX") || exit 1
trap 'rm -f "$listed"' EXIT HUP INT TERM

# A symlink anywhere in the packet can point outside it, so the packet is
# rejected rather than followed.
if find "$packet" -type l -print | grep -q .; then
  find "$packet" -type l -print | while IFS= read -r link; do
    printf 'verify-packet: symlink in packet: %s\n' "$link" >&2
  done
  problem "a packet may not contain symlinks"
fi

rows=0
while IFS='	' read -r relative expected verification; do
  [ -n "$relative" ] || continue
  rows=$((rows + 1))
  printf '%s\n' "$relative" >>"$listed"
  target="$sources/$relative"
  case "$relative" in
    /*|*..*) problem "manifest path escapes the packet: $relative"; continue ;;
  esac
  if [ -L "$target" ]; then
    problem "listed file is a symlink: $relative"
    continue
  fi
  if [ ! -f "$target" ]; then
    problem "listed file is missing: $relative"
    continue
  fi
  actual=$(sha256_file "$target")
  if [ "$actual" != "$expected" ]; then
    problem "content changed since export: $relative"
  fi
  case "$verification" in
    unverified)
      problem "unverified note in packet: $relative"
      ;;
  esac
done <<EOF
$(sed -n 's/^| `\(..*\)` | `\([0-9a-f]\{64\}\)` | \([^|]*\) |.*$/\1	\2	\3/p' "$manifest" |
  sed 's/[[:space:]]*$//')
EOF

[ "$rows" -gt 0 ] || fail "manifest lists no files; nothing to verify"

# A file sitting in sources/ that the manifest never listed would ride along
# unreviewed, so its presence fails the packet.
find "$sources" -type f -print | while IFS= read -r found; do
  relative=${found#"$sources/"}
  grep -Fxq "$relative" "$listed" ||
    printf 'verify-packet: file not listed in the manifest: %s\n' "$relative" >&2
done
extra=$(find "$sources" -type f -print | while IFS= read -r found; do
  relative=${found#"$sources/"}
  grep -Fxq "$relative" "$listed" || printf 'x'
done)
[ -z "$extra" ] || problem "the packet holds files the manifest does not list"

# An entry beside the manifest and sources/ is not part of the reviewed set.
# It does not break the manifest-to-sources guarantee, so it is surfaced for a
# human to judge rather than failing the packet - a flattened upload copy is a
# real need, but an undocumented one is how unreviewed content travels.
for entry in "$packet"/*; do
  [ -e "$entry" ] || continue
  case "${entry##*/}" in
    00-manifest.md|sources) ;;
    *)
      printf 'verify-packet: note: %s is not part of the reviewed set; record it in the manifest or leave it behind\n' \
        "${entry##*/}" >&2
      ;;
  esac
done

if [ "$problems" -gt 0 ]; then
  printf 'verify-packet: %s problem(s); do not upload this packet\n' "$problems" >&2
  exit 1
fi

printf 'verify-packet: %s file(s) match the manifest\n' "$rows"
