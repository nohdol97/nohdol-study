#!/bin/sh
#
# 실행 래퍼의 어긋남 검사 테스트.
#
# 래퍼는 마지막에 스크래퍼를 exec하므로, 검사만 떼어 보려면 venv가 없는 상태를
# 쓴다 — 검사는 venv 확인보다 앞에 있고, venv가 없으면 그 뒤에서 멈춘다. 그래서
# 여기서는 네트워크도 vault도 건드리지 않고 검사 부분만 실행된다.

set -eu

source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
test_root=$(mktemp -d "${TMPDIR:-/tmp}/nohdol-study-scraper.XXXXXX")
trap 'rm -rf "$test_root"' EXIT HUP INT TERM

upstream="$test_root/examples/feed_scraper"
runtime="$test_root/_workspace/feed_scraper"
mkdir -p "$upstream" "$runtime"

# 추적본 자리에는 지금 고친 래퍼가 그대로 들어간다. 사본에도 같은 것을 두어
# 어긋나지 않은 상태에서 시작한다.
for name in run_scraper.sh scrape.py requirements.txt; do
  if [ -f "$source_dir/$name" ]; then
    cp "$source_dir/$name" "$upstream/$name"
  else
    printf '%s\n' "# $name" >"$upstream/$name"
  fi
  cp "$upstream/$name" "$runtime/$name"
done
chmod +x "$upstream/run_scraper.sh" "$runtime/run_scraper.sh"

run_wrapper() {
  # venv가 없어 종료 코드가 1이다. 검사 출력만 보므로 그것을 실패로 다루지 않는다.
  "$1/run_scraper.sh" 2>&1 || true
}

# 파일 이름만 찾으면 뒤따르는 venv 안내의 `pip install -r requirements.txt`가
# 걸린다. 어긋남 보고는 이름 뒤에 해시를 붙인 줄이므로 그 형태로 좁힌다.
reported() {
  printf '%s' "$2" | grep -E "^ +$1  사본 " >/dev/null
}

# 사본이 추적본과 같으면 아무 말도 하지 않는다. 매 실행 뜨는 경고는 읽히지 않는다.
same_output=$(run_wrapper "$runtime")
if printf '%s' "$same_output" | grep -F '어긋난 파일' >/dev/null; then
  printf 'FAIL: 동일한 사본인데 어긋남을 보고했다\n' >&2
  exit 1
fi
# 검사를 지나 venv 확인까지 갔는지 확인한다. 검사가 조용한 것과 검사가 아예 돌지
# 않은 것을 구분하지 못하면, 이 테스트는 아무것도 지키지 않는다.
printf '%s' "$same_output" | grep -F 'venv python not found' >/dev/null

# 엔진이 뒤처지면 파일 이름을 지목한다. 2026-08-03 사고가 정확히 이 상태였다.
printf '%s\n' '# upstream changed' >>"$upstream/scrape.py"
drift_output=$(run_wrapper "$runtime")
printf '%s' "$drift_output" | grep -F '어긋난 파일' >/dev/null
reported 'scrape\.py' "$drift_output"
# 고치는 명령이 함께 나와야 한다. 어긋났다는 사실만으로는 아침 로그에서 넘어간다.
printf '%s' "$drift_output" | grep -F 'cp -p' >/dev/null
# 손대지 않은 파일까지 싸잡아 보고하지 않는다.
if reported 'requirements\.txt' "$drift_output"; then
  printf 'FAIL: 동일한 requirements.txt를 어긋남으로 보고했다\n' >&2
  exit 1
fi

# 어긋나도 멈추지 않는다. 낡은 코드로 도는 것이 수집이 끊기는 것보다 낫다는
# 판단이므로, 검사가 조용히 실행을 막기 시작하면 그 판단이 뒤집힌 것이다.
printf '%s' "$drift_output" | grep -F 'venv python not found' >/dev/null

# 복사해 맞추면 경고가 사라진다.
cp "$upstream/scrape.py" "$runtime/scrape.py"
fixed_output=$(run_wrapper "$runtime")
if printf '%s' "$fixed_output" | grep -F '어긋난 파일' >/dev/null; then
  printf 'FAIL: 맞춘 뒤에도 어긋남을 보고했다\n' >&2
  exit 1
fi

# 래퍼 자신이 뒤처지는 것도 잡는다. 사본을 손으로 고쳐 온 이력이 있으면 엔진보다
# 이쪽이 먼저 갈라진다.
printf '%s\n' '# upstream wrapper changed' >>"$upstream/run_scraper.sh"
wrapper_output=$(run_wrapper "$runtime")
reported 'run_scraper\.sh' "$wrapper_output"
cp "$upstream/run_scraper.sh" "$runtime/run_scraper.sh"
chmod +x "$runtime/run_scraper.sh"

# 추적본이 없는 곳에 사본만 떼어 두면 검사를 건너뛴다. 그 배치를 지원한다고
# 적어 두었으므로, 경고가 뜨면 안내와 코드가 어긋난 것이다.
lone="$test_root/lone"
mkdir -p "$lone"
cp "$runtime/run_scraper.sh" "$lone/run_scraper.sh"
chmod +x "$lone/run_scraper.sh"
lone_output=$(run_wrapper "$lone")
if printf '%s' "$lone_output" | grep -F '어긋난 파일' >/dev/null; then
  printf 'FAIL: 추적본이 없는데 어긋남을 보고했다\n' >&2
  exit 1
fi
printf '%s' "$lone_output" | grep -F 'venv python not found' >/dev/null

# 추적본 자리에서 직접 돌리면 자기 자신과 비교하게 된다. 언제나 같으므로 조용해야
# 하지만, 경로가 같다는 것을 확인하지 않으면 무의미한 비교가 매번 돈다.
upstream_output=$(run_wrapper "$upstream")
if printf '%s' "$upstream_output" | grep -F '어긋난 파일' >/dev/null; then
  printf 'FAIL: 추적본 자리에서 자기 자신을 어긋남으로 보고했다\n' >&2
  exit 1
fi

printf 'run_scraper tests: PASS\n'
