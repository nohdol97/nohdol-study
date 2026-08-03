# 피드 스크래퍼 레퍼런스 구현 (Feed Scraper)

RSS 소스를 연결된 vault로 자동 수집하는 스크립트다. 이 디렉터리는 **레퍼런스**이고,
실제 실행은 비추적 영역인 `_workspace/feed_scraper/`에서 한다.

전체 배경과 운영 지침은 [docs/guides/feed-scraper.md](../../docs/guides/feed-scraper.md)에 있다.

## 두 가지 파이프라인

| 파이프라인 | 하는 일 | 외부 API |
|---|---|---|
| `feed` | 제목과 링크만 소스별 목록 문서에 쌓는다 | 없음 |
| `geeknews` | 점수를 채점해 기준 통과분만 요약·분류한다 | Gemini |

`feed`는 본문을 읽지 않으므로 API 호출이 0이다. **소스를 몇 개 붙이든 무료 티어
한도와 무관하다.** 읽을지 말지는 제목을 보고 사람이 정한다.

## 설치

```bash
# 1. 작업 공간으로 복사
mkdir -p _workspace/feed_scraper
cp -p examples/feed_scraper/* _workspace/feed_scraper/
cd _workspace/feed_scraper

# 2. 가상환경 (Python 3.11+ — 설정 파싱에 tomllib을 쓴다)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. 켤 소스 고르기
cp sources.local.example.toml sources.local.toml
$EDITOR sources.local.toml

# 4. (geeknews를 켰다면) API 키
echo 'GEMINI_API_KEY=...' > .env

# 5. 실행
./run_scraper.sh
```

`sources.local.toml`과 `.env`, `.venv`, `data/`, `scraper.log`는 모두 추적되지
않는다. 설치별 선택과 자격 증명이기 때문이다.

## 소스를 켜고 끄기

`scrape.py`의 `SOURCES`가 **카탈로그**이고, `sources.local.toml`의 `enabled`가
**선택**이다. 카탈로그에 있어도 `enabled`에 없으면 수집되지 않는다. 컴퓨터마다
관심사가 다르므로 둘을 나눴다.

```toml
enabled = ["ieee-robotics", "the-robot-report"]
```

## 소스 추가하기

`scrape.py`의 `SOURCES`에 항목 하나를 더한다. 그 전에 두 가지를 실측한다.

1. **`published_parsed` 유무** — 없으면 날짜를 적을 수 없어 건너뛴다
2. **피드 창** — 가장 오래된 항목부터 최신까지의 시간 폭. `window_days`를
   그보다 넉넉히 잡아야 하루 한 번 실행에서도 놓치지 않는다

```python
'my-source': {
    'name': "My Source",
    'pipeline': 'feed',
    'rss': "https://example.com/feed.xml",
    'path': "Robotics/My Source.md",     # vault/wiki/ 기준 상대 경로
    'tags': ["robotics", "feed"],
    'hub': "로봇과 피지컬 AI 정보 소스",   # 이 문서의 related가 가리킬 허브
    'window_days': 14,
    # 선택: 주제 전용이 아닌 피드는 제목으로 거른다.
    # 'title_filter': ["robot", "lerobot", "embodied"],
},
```

재는 방법과 탈락한 후보는 vault의 `[[로봇과 피지컬 AI 정보 소스]]`에 있다.

## 자동 실행 (macOS)

`launchd` 사용자 에이전트를 쓴다. `ProgramArguments`가
`_workspace/feed_scraper/run_scraper.sh`를 가리키게 하면 된다.

`geeknews`를 켰다면 실행 시각이 의미를 갖는다 — Gemini 일일 한도는 **태평양
자정**(PDT 기준 KST 16:00)에 리셋되므로, KST 17시 이후 실행은 그 이전 실행과
다른 할당을 받는다. `feed` 소스만 쓴다면 호출이 없어 시각은 아무래도 좋다.

## 테스트

```sh
python3 examples/feed_scraper/scrape_test.py   # 엔진
sh examples/feed_scraper/run_scraper_test.sh   # 실행 래퍼의 어긋남 검사
```

래퍼 테스트는 venv 없는 임시 디렉터리에서 돌므로 네트워크도 vault도 건드리지
않는다.

## 중복과 재실행

모든 항목은 끝에 마커를 달고 저장된다(`<!-- src:키:링크 -->`, GeekNews는
`<!-- gn:id -->`). 하루에 몇 번을 돌려도 같은 글이 두 번 들어가지 않으므로,
실행 실패 후 그냥 다시 돌리면 된다.
