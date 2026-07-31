#!/bin/sh
# Install the local embedding server used by vault-search and AgentsView search.
#
# Why this script exists rather than `brew services start ollama`.
#
# Homebrew's ollama service sets OLLAMA_FLASH_ATTENTION=1 and
# OLLAMA_KV_CACHE_TYPE=q8_0, which reach llama-server as `--flash-attn on
# --cache-type-k q8_0 --cache-type-v q8_0`. Those shrink the KV cache of a
# generative model. An embedding model is an encoder and has no such cache: the
# Homebrew-managed server answered /api/version and then hung before
# ggml_metal_init, so no model ever loaded, while a hand-started `ollama serve`
# loaded the same model in under a second. This installs a LaunchAgent that
# sets no tuning variables, which is the whole difference.
#
# Usage: install-embedding.sh --check | --install [--model NAME]

set -eu

MODEL=""
MODE="check"
LABEL="com.nohdol.ollama"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
ENDPOINT="http://127.0.0.1:11434"

while [ $# -gt 0 ]; do
  case "$1" in
    --check) MODE="check" ;;
    --install) MODE="install" ;;
    --model) shift; MODEL="${1:-}" ;;
    *) printf 'unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
  shift
done

os=$(uname -s)
arch=$(uname -m)
if [ "$os" = "Darwin" ]; then
  ram_bytes=$(sysctl -n hw.memsize 2>/dev/null || echo 0)
else
  # Linux: MemTotal is in kB.
  ram_bytes=$(awk '/MemTotal/ {print $2 * 1024; exit}' /proc/meminfo 2>/dev/null || echo 0)
fi
ram_gb=$((ram_bytes / 1073741824))

# Model choice.
#
# The knowledge base is Korean, and that decides more than size does.
# nomic-embed-text is English-centred; a multilingual model retrieves Korean
# notes noticeably better, which is the entire job here. bge-m3 is the
# multilingual default and needs roughly 1.5 GB resident. Below 8 GB of system
# memory that is no longer a safe resident cost next to an editor and a
# browser, so the smaller English-centred model is used and its weakness is
# reported rather than hidden.
if [ -z "$MODEL" ]; then
  if [ "$ram_gb" -ge 8 ]; then
    MODEL="bge-m3"
  else
    MODEL="nomic-embed-text"
  fi
fi

printf 'machine: %s %s, %s GB RAM\n' "$os" "$arch" "$ram_gb"
printf 'model:   %s\n' "$MODEL"
if [ "$ram_gb" -lt 8 ]; then
  printf 'note:    under 8 GB, so an English-centred model is chosen; Korean recall will be weaker\n'
fi

have_ollama=no
command -v ollama >/dev/null 2>&1 && have_ollama=yes
agent_loaded=no
launchctl list 2>/dev/null | grep -q "$LABEL" && agent_loaded=yes
serving=no
curl -sS --max-time 5 "$ENDPOINT/api/version" >/dev/null 2>&1 && serving=yes

printf 'ollama:    %s\n' "$have_ollama"
printf 'launchagent: %s\n' "$agent_loaded"
printf 'serving:   %s\n' "$serving"

if [ "$MODE" = "check" ]; then
  if [ "$serving" = yes ]; then
    printf '\nReady. Semantic search over the vault is available.\n'
  else
    printf '\nNot installed. Run with --install to set it up. This is optional:\n'
    printf 'every other skill works without it, and vault-search reports its absence\n'
    printf 'rather than silently falling back to a worse search.\n'
  fi
  exit 0
fi

if [ "$os" != "Darwin" ]; then
  printf '\n--install currently automates macOS only. On Linux, install ollama, run it on\n'
  printf 'loopback, and pull %s; vault-search needs nothing else.\n' "$MODEL"
  exit 1
fi

if [ "$have_ollama" = no ]; then
  command -v brew >/dev/null 2>&1 || {
    printf 'Homebrew is required to install ollama automatically.\n' >&2
    exit 1
  }
  printf '\ninstalling ollama...\n'
  brew install ollama
fi

# Homebrew's own service must stay off: two servers cannot hold port 11434, and
# its environment is the reason this script exists.
brew services stop ollama >/dev/null 2>&1 || true

printf 'writing %s\n' "$PLIST"
mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
cat >"$PLIST" <<PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(command -v ollama || echo /opt/homebrew/bin/ollama)</string>
        <string>serve</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>HOME</key>
        <string>$HOME</string>
        <key>OLLAMA_HOST</key>
        <string>127.0.0.1:11434</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/ollama.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/ollama.log</string>
</dict>
</plist>
PLIST_EOF

launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"

printf 'waiting for the server...\n'
i=0
while [ "$i" -lt 30 ]; do
  curl -sS --max-time 5 "$ENDPOINT/api/version" >/dev/null 2>&1 && break
  i=$((i + 1))
  sleep 1
done
curl -sS --max-time 5 "$ENDPOINT/api/version" >/dev/null 2>&1 || {
  printf 'server did not come up; see %s/Library/Logs/ollama.log\n' "$HOME" >&2
  exit 1
}

printf 'pulling %s...\n' "$MODEL"
ollama pull "$MODEL"

# Prove a model actually loads. The failure this script was written for passed
# every check except this one, so checking anything less would miss it again.
printf 'verifying an embedding...\n'
body=$(printf '{"model":"%s","input":"설치 확인"}' "$MODEL")
if curl -sS --max-time 300 "$ENDPOINT/api/embed" \
    -H 'Content-Type: application/json' -d "$body" | grep -q '"embeddings"'; then
  printf '\nReady. Record the model in REGISTRY.md and build the index:\n'
  printf '  python3 .agents/skills/vault-search/scripts/semantic.py build --vault vault\n'
else
  printf 'the server is up but no embedding came back; see %s/Library/Logs/ollama.log\n' "$HOME" >&2
  exit 1
fi
