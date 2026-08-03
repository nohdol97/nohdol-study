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

# 추적본과 어긋났는지 본다.
#
# 도는 것은 언제나 이 사본이다. 저장소의 추적본을 고쳐도 여기로 복사하지 않으면
# 낡은 코드가 계속 도는데, 그 실패는 조용하다 — 2026-08-03에 실제로 일어났다.
# 산출물을 `raw/`와 `wiki/` 두 층으로 가른 변경이 사본에 오지 않아 하루치
# 수집분이 통째로 `wiki/`에 쌓였고, 잘못된 자리에 파일이 생긴 것을 사람이 눈으로
# 보고서야 알았다. 그 사이 로그는 정상이라고 말하고 있었다.
#
# 사본만 떼어 다른 곳에서 돌리는 것도 지원해야 하므로, 추적본이 보이지 않으면
# 검사를 건너뛴다. 어긋남을 찾아도 멈추지 않는다 — 낡은 코드라도 수집이 끊기는
# 것보다는 낫고, 무엇을 해야 하는지는 로그 맨 앞에 남는다.
UPSTREAM=$(CDPATH= cd -- "$SCRIPT_DIR/../../examples/feed_scraper" 2>/dev/null && pwd -P) || UPSTREAM=""

# 실행 동작을 정하는 파일만 본다. README와 예시 설정은 갈라져도 수집 결과가
# 달라지지 않으므로, 자주 뜨는 경고로 경고 자체를 무시하게 만들 이유가 없다.
SYNCED="scrape.py run_scraper.sh requirements.txt"

if [ -n "$UPSTREAM" ] && [ "$UPSTREAM" != "$SCRIPT_DIR" ] \
   && command -v shasum >/dev/null 2>&1; then
  DRIFTED=""
  for name in $SYNCED; do
    if [ -f "$UPSTREAM/$name" ] && [ -f "$SCRIPT_DIR/$name" ]; then
      MINE=$(shasum -a 256 <"$SCRIPT_DIR/$name" | cut -d' ' -f1)
      THEIRS=$(shasum -a 256 <"$UPSTREAM/$name" | cut -d' ' -f1)
      if [ "$MINE" != "$THEIRS" ]; then
        DRIFTED="$DRIFTED $name"
      fi
    fi
  done

  if [ -n "$DRIFTED" ]; then
    echo "[$(date)] ⚠️  추적본과 어긋난 파일:$DRIFTED"
    echo "    도는 것은 이 사본이므로, 저장소 쪽 변경은 복사하기 전까지 반영되지 않습니다."
    for name in $DRIFTED; do
      MINE=$(shasum -a 256 <"$SCRIPT_DIR/$name" | cut -c1-8)
      THEIRS=$(shasum -a 256 <"$UPSTREAM/$name" | cut -c1-8)
      echo "      $name  사본 $MINE / 추적본 $THEIRS"
    done
    echo "    사본이 낡았다면 추적본을 복사하세요:"
    echo "      cp -p $UPSTREAM/<파일> $SCRIPT_DIR/<파일>"
    echo "    사본 쪽을 먼저 고친 것이라면 반대로 복사한 뒤 저장소에 커밋하세요."
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
