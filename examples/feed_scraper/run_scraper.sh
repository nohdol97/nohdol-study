#!/bin/sh
#
# 피드 스크래퍼 실행 래퍼. launchd/cron이 이 파일을 부른다.
#
# 경로를 적지 않는다. 스크립트 자신의 위치에서 모두 유도하므로, 이 디렉터리를
# 통째로 옮기거나 다른 컴퓨터에 복사해도 그대로 돈다.

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
LOG="$SCRIPT_DIR/scraper.log"
MAX_BYTES=1048576   # 1MB

# 로그 로테이션. launchd에는 로테이션 기능이 없어 이 파일이 무한히 자란다.
# 실행 전에 옮기므로 다음 실행부터 새 파일에 쌓인다. 한 세대만 남긴다.
if [ -f "$LOG" ]; then
  SIZE=$(stat -f%z "$LOG" 2>/dev/null || echo 0)
  if [ "$SIZE" -gt "$MAX_BYTES" ]; then
    mv -f "$LOG" "$LOG.1"
  fi
fi

# 시스템 python은 PEP 668로 패키지 설치가 막혀 있고, 버전이 어긋나면 의존성이
# 함께 어긋난다. venv로 고정한다. 만드는 방법은 README에 있다.
VENV_PY="$SCRIPT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PY" ]; then
  echo "[$(date)] venv python not found at $VENV_PY"
  echo "  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

exec "$VENV_PY" "$SCRIPT_DIR/scrape.py"
