# 피드 스크래퍼 가이드 (Feed Scraper)

RSS 소스를 연결된 vault로 자동 수집하는 도구다. 레퍼런스 구현은
[`examples/feed_scraper/`](../../examples/feed_scraper/)에 있고, 실제 실행은
비추적 영역인 `_workspace/feed_scraper/`에서 한다.

## 왜 이 구조인가

수집 도구는 **코드는 모든 컴퓨터에서 같고, 무엇을 수집할지는 컴퓨터마다 다르다.**
이 둘을 한 파일에 두면 다른 기계에 옮길 때마다 코드를 고쳐야 하고, 고친 내용이
하네스에 커밋되면 개인 선택이 추적 파일에 섞인다.

그래서 셋으로 나눴다.

| 무엇 | 어디 | 추적 |
|---|---|---|
| 엔진과 소스 카탈로그 | `examples/feed_scraper/scrape.py` | O |
| 이 컴퓨터의 선택 | `_workspace/feed_scraper/sources.local.toml` | X |
| 자격 증명·수집 상태 | `_workspace/feed_scraper/{.env,data/}` | X |

카탈로그에 있어도 `enabled`에 없으면 수집되지 않는다. 노트북에서는 로봇 소스만,
데스크톱에서는 GeekNews까지 — 같은 코드로 다르게 돌릴 수 있다.

### 코드를 고쳤으면 사본으로 복사한다

이 구조의 대가는 **엔진이 두 곳에 있다**는 것이다. 도는 것은 언제나 `_workspace/`
사본이므로, `examples/`의 추적본을 고치고 복사하지 않으면 낡은 코드가 계속 돈다.
2026-08-03에 실제로 그 일이 있었다 — 산출물을 `raw/`와 `wiki/` 두 층으로 가른
변경이 사본에 오지 않아 하루치 수집분이 통째로 `wiki/`에 쌓였고, 그동안 로그는
정상이라고 말하고 있었다.

```bash
cp -p examples/feed_scraper/scrape.py _workspace/feed_scraper/scrape.py
```

복사를 잊어도 조용히 지나가지 않는다. `run_scraper.sh`가 실행할 때마다
`scrape.py`·`run_scraper.sh`·`requirements.txt`의 SHA-256을 추적본과 대조하고,
어긋나면 로그 맨 앞에 파일 이름과 고치는 명령을 남긴다. 어긋나도 **멈추지는
않는다** — 낡은 코드로 도는 것이 수집이 끊기는 것보다 낫다는 판단이다. 사본
쪽을 먼저 고친 경우도 있으므로 복사 방향은 사람이 정한다.

`README.md`와 `sources.local.example.toml`은 대조하지 않는다. 갈라져도 수집
결과가 달라지지 않는데 경고만 잦아지면 경고 자체를 읽지 않게 된다. 사본만 떼어
다른 곳에 두면(`examples/`가 보이지 않으면) 검사는 조용히 건너뛴다.

## 두 가지 파이프라인

| 파이프라인 | 하는 일 | 외부 API | 산출물 |
|---|---|---|---|
| `feed` | 제목과 링크만 쌓는다 | 없음 | 소스별 목록 문서 1개 |
| `geeknews` | 점수 채점 → 기준 통과분 요약·분류 | Gemini | 날짜별 원본 + 월 인덱스 + 주제 문서 7종 |

### 산출물이 두 층에 나뉘는 이유

기준은 하나다 — **사람의 판단이 들어갔는가.**

| 산출물 | 위치 | 만든 주체 |
|---|---|---|
| 날짜별 원본 | `vault/raw/geeknews/<연월>/<날짜>.md` | 자동 |
| 월 인덱스 | `vault/raw/geeknews/<연월> 인덱스.md` | 자동 |
| 주제 문서 7종 | `vault/wiki/GeekNews/` | 분류는 자동, **무엇을 남기고 어느 원자 노트로 잇는지는 사람** |
| `feed` 소스별 목록 | `vault/wiki/<카탈로그의 path>` | 자동 |

날짜별 원본은 하루치에 서로 무관한 글이 여러 개 들어가는 불변 캡처이고, 월 인덱스는 그 폴더를 훑어 만든 링크 목록일 뿐이다. 둘 다 큐레이션 판단이 하나도 없으므로 `raw/`에 쌓는다. `wiki/`에 두면 원자 노트를 세는 모든 지표 — 고아 노트, `status` 분포, 지식 그래프 — 가 수집량에 휩쓸린다. 실제로 2026-08-02 이전에는 `wiki/` 305개 노트 중 177개가 이 캡처였고 `status: seed`의 61%가 여기서 나왔다.

`wiki/GeekNews/`에는 주제 문서만 남는다. 그래서 하위 디렉터리를 두지 않는다 — 한 종류만 있는 폴더에 `주제/`를 한 겹 더 파면 경로만 길어진다.

Obsidian은 wikilink를 vault 전체에서 이름으로 풀기 때문에 층이 갈려도 링크는 그대로 걸린다. 인덱스의 `[[2026-08-01]]`도, 허브의 `[[2026.8 인덱스]]`도 마찬가지다.

> 월 인덱스 목록을 담은 `GeekNews 큐레이션 허브`의 표는 **손으로 관리한다.** 스크래퍼는 인덱스를 만들지만 허브 표에 행을 추가하지 않으므로, 달이 바뀌면 새 인덱스를 아무도 가리키지 않는다.

### `feed`가 요약하지 않는 이유

본문을 읽지 않으므로 API 호출이 0이다. **소스를 몇 개 붙이든 무료 티어 한도와
무관하다.** 요약을 붙이면 소스마다 한도를 나눠 써야 하고, 그 요약은 검증되지
않은 생성물이라 근거로 쓸 수도 없다. 읽을지 말지는 제목으로 충분히 정해진다.

### `geeknews`가 요약하는 이유

GeekNews는 투표 점수가 있어 "무엇이 읽을 만한가"를 사이트가 이미 재고 있다.
5P 게이트를 통과한 하루 8~12건만 남으므로 요약 비용이 감당된다. 주제 분류까지
같은 호출에서 받아 주제 문서로 흘려보낸다.

## 설치

```bash
mkdir -p _workspace/feed_scraper
cp -p examples/feed_scraper/* _workspace/feed_scraper/
cd _workspace/feed_scraper

python3 -m venv .venv                      # Python 3.11+ (tomllib)
.venv/bin/pip install -r requirements.txt

cp sources.local.example.toml sources.local.toml
$EDITOR sources.local.toml                 # 켤 소스 고르기

echo 'GEMINI_API_KEY=...' > .env           # geeknews를 켰을 때만
./run_scraper.sh
```

vault 경로는 적지 않는다. 스크립트가 위로 올라가며 `vault` 심링크를 가진
하네스 루트를 찾는다. 표준 배치를 벗어난 곳에서 돌릴 때만
`sources.local.toml`에 `study_root`를 적는다.

## 자동 실행 (macOS launchd)

```bash
launchctl load -w ~/Library/LaunchAgents/com.user.study.feedscraper.plist
launchctl list | grep feedscraper
```

`ProgramArguments`가 `_workspace/feed_scraper/run_scraper.sh`를 가리키면 된다.
래퍼가 자신의 위치에서 로그·venv 경로를 유도하므로 plist에는 그 한 줄만 있으면
충분하다.

### 실행 시각

`geeknews`를 켰다면 시각이 의미를 갖는다. Gemini 일일 한도(RPD)는 **태평양
자정**에 리셋되고, PDT 기준 **KST 16:00**이다. 06시·08시 실행은 태평양 기준
같은 날이라 한도를 공유하고, KST 17시 이후 실행은 다음 날 할당을 받는다.

`feed` 소스만 쓴다면 호출이 없으므로 시각은 아무래도 좋다. 피드 창이 4일
이상인 소스들이라 하루 한 번으로 충분하다.

## 소스 추가

`scrape.py`의 `SOURCES`에 항목을 더하고, `sources.local.toml`의 `enabled`에
키를 적는다. 더하기 전에 두 가지를 실측한다.

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
    'hub': "로봇과 피지컬 AI 정보 소스",
    'window_days': 14,
},
```

재는 방법과 탈락한 후보(arXiv cs.RO, hnrss 등)는 vault의
`[[로봇과 피지컬 AI 정보 소스]]` 노트에 있다.

### 주제 전용이 아닌 피드 거르기

`title_filter`를 주면 제목에 그 낱말 중 하나가 있는 항목만 받는다. Hugging
Face 블로그처럼 관심 주제가 일부인 피드에 쓴다 — 실측에서 831건 중 로봇 관련은
23건(2.8%)이라, 거르지 않으면 나머지가 목록을 덮는다.

```python
'title_filter': ["robot", "lerobot", "embodied", "manipulat"],
```

본문이 아니라 제목만 검사한다. 본문까지 보면 주제가 스쳐 지나간 글이 대거
걸리고, 정작 찾던 글은 제목에 그 말이 있다는 것이 GeekNews 관심어에서 이미
확인된 바다. 대신 **낱말 목록이 곧 재현율**이므로, 놓치는 글이 있다고 느껴지면
목록을 넓히되 그만큼 다른 주제가 섞여 든다.

## 현재 카탈로그

| 키 | 소스 | 파이프라인 | 일평균 | 피드 창 |
|---|---|---|---|---|
| `geeknews` | GeekNews | `geeknews` | 8~12(게이트 후) | 33시간 |
| `ieee-robotics` | IEEE Spectrum Robotics | `feed` | 0.4 | 67일 |
| `the-robot-report` | The Robot Report | `feed` | 3.7 | 4.1일 |
| `ros-discourse` | ROS Discourse | `feed` | 6.7 | 4.5일 |
| `robohub` | Robohub | `feed` | 0.4 | 191일 |
| `nvidia-robotics` | NVIDIA Robotics | `feed` | 0.2 | 118일 |
| `huggingface-robotics` | Hugging Face (로봇) | `feed` | 0.35 중 2.8% | 넓음 |

일평균과 창은 2026-07-26 실측이다. 발행 주기가 바뀌면 함께 바뀐다.

## 중복과 재실행

모든 항목은 마커를 달고 저장된다 — `feed`는 `<!-- src:키:링크 -->`,
`geeknews`는 `<!-- gn:topic_id -->`. 하루에 몇 번을 돌려도 같은 글이 두 번
들어가지 않으므로, 실패한 실행은 그냥 다시 돌리면 된다.

`geeknews`는 추가로 점수를 `data/pending/`에 캐시한다. 요약이 429로 막혀
중단되어도 다음 실행이 점수를 다시 묻지 않고 요약만 이어서 한다.

## 문제 해결

| 증상 | 원인 | 조치 |
|---|---|---|
| `설정이 없습니다` | `sources.local.toml` 미생성 | example을 복사 |
| `켜진 소스가 없습니다` | `enabled`가 비었거나 전부 주석 | 키를 적는다 |
| `카탈로그에 없는 소스` | `enabled`의 오타 | 카탈로그 키와 대조 |
| `venv python not found` | 가상환경 미생성 | 위 설치 절차 |
| `GEMINI_API_KEY가 없어 건너뜁니다` | `.env` 없음 | 키를 넣거나 `geeknews`를 끈다 |
| 특정 소스만 0건 | 피드 URL 변경 또는 창 밖 | 해당 RSS를 직접 열어 확인 |

## 산출물이 지식이 아니라는 점

수집된 목록은 **읽을 것을 고르는 대기열**이지 지식이 아니다. `feed` 문서의
각 줄은 발행된 제목일 뿐이고, `geeknews`의 한 줄 요약은 검증되지 않은 AI
생성물이다. 두 경우 모두 주장의 근거로 쓸 수 없다. 읽고 이해한 것은
`note-writer`로 원자적 노트에 적고, 그 노트가 증거를 갖는다.
