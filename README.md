# nohdol-study — AI 에이전트 기반 휴대용 공부 하네스

`nohdol-study`는 Claude Code, Codex, 그리고 Gemini Antigravity CLI가 동일한 파일 규약으로 사용하는 **휴대용 AI 스터디 하네스(Portable Study Harness)**다. 
수집한 원문은 `raw/`, 검증해 정리한 원자적 지식은 `wiki/`에 두며 **Markdown과 위키링크(`[[ ]]`)를 유일한 단일 원본(Single Source of Truth)**으로 삼는다.

> 💡 **설계 철학**: 하네스 저장소 자체는 지식 파일을 추적하지 않는다. 컴퓨터마다 다른 지식 저장소 경로는 실제 지식 루트를 가리키는 미추적 심링크(`vault/`)와 로컬 레지스트리(`REGISTRY.md`)를 통해 안전하게 연결된다.

---

## 🌟 제공 기능 및 학습 환경 (Features)

### 1. 🏗️ Phase 1: 기본 지식 하네스
- **이식성 높은 설치**: 설치처(개인/사내 프로필, 동기화 방식)별 지식 디렉터리 선택 및 안전한 부트스트랩
- **표준화된 구조**: `raw/` (불변 소스), `wiki/` (원자적 노트), `index.md` (지도), `log.md` (연대기), `hot.md` (세션 컨텍스트)
- **노트 계약 (Note Contract)**: Flat YAML 프론트매터, 위키링크, 주장별 출처 및 검증 상태(`unverified` ~ `primary-confirmed`) 엄격 집행
- **쓰기 시점 게이트 (`PostToolUse`)**: 노트를 저장하는 순간 다이어그램 렌더 실패·프론트매터 계약 위반·해석되지 않는 `sources:` 경로를 검사해 같은 턴에서 고치게 한다. 스킬을 거치지 않은 작성자에게도 파일 기준으로 적용된다
- **마무리 게이트 (`Stop`)**: 이번 세션에 쓴 노트가 기록됐는지, **무엇이 그 노트를 가리키는지**, 새로 건 링크가 실제로 해석되는지 확인한다. 도달 가능성 판정은 `vault-gardening`과 같은 정의를 쓴다
- **유출 게이트 (`PreToolUse`)**: 노트북 셀에 지식 루트 경로·위키링크·노트 프론트매터가 섞이면 막는다. 승인 프롬프트는 "이 도구를 실행할까"를 묻지 **페이로드에 노트가 들어 있는지**를 묻지 않기 때문에, 이 게이트만 대화형 세션에서도 켜져 있다. 공개 데이터셋에서 실측한 수치는 vault 자료가 아니므로 통과한다

### 2. 🔍 Phase 2: 다중 매체 수집 및 지식 그래프
- **웹 문서 캡처 (`defuddle`)**: 광고·내비게이션을 제거한 깨끗한 마크다운 불변 캡처
- **학술 논문 탐색 (`paper-search`)**: arXiv·DOI 기반 논문 검색, PDF 다운로드 및 출판 메타데이터 검증
- **영상 심층 학습 (`study-video`)**: 한국어·영어 자막 우선의 Transcript-first 학습. 영상 다운로드는 화면이 답해야 할 질문이 있을 때만
- **결정적 지식 그래프 (`knowledge-graph`)**: `article`·`topic`·`source` 타입의 결정적 JSON 그래프 생성 및 모델 추론 근거 검증
- **의미 검색 (`vault-search`)**: 노트가 쓴 단어를 몰라도 **의미로** 찾는다. 임베딩은 루프백 서버에서만 계산하고(그 외 엔드포인트는 스크립트가 거부), 인덱스는 동기화 밖 `_workspace/`에 둔다. 검색할 때 바뀐 노트만 자동으로 다시 임베딩하므로 재빌드를 기억할 필요가 없다. 결과는 근거가 아니라 **후보 목록**이다
- **대량 문서화 큐 (`ingest` 배치 모드)**: 진행률을 체크박스가 아니라 **노트가 그 파일을 실제로 인용하는지**로 계산해, 세션이 끊겨도 노트에서 재개된다

### 3. 🧠 Phase 2b: 코드·도메인 분석 및 Obsidian 연동
- **Understand Anything 9개 모드 라우팅 (`understand`)**: 코드베이스 아키텍처 파악, 기능 위치 탐색, 개념 설명, 온보딩 가이드, 변경 영향 범위, 도메인 분석, 대시보드 뷰어
- **Obsidian 형식 및 CLI 연동 (`obsidian`)**: 마크다운 확장, Bases(`.base`), JSON Canvas(`.canvas`) 작성 및 Obsidian CLI (4개 모드) 내부 라우팅
- **발표용 인터랙티브 다이어그램 (`archify`)**: **명시 호출 시에만** pin된 CLI로 단독 실행 HTML 다이어그램을 만든다. Obsidian이 임베드할 수 없고 지식 루트는 동기화되므로 산출물은 `_workspace/`에만 두며, 노트에 들어갈 다이어그램은 `diagram`(Mermaid/D2)이 그대로 담당한다
- **안전한 격리 런타임**: 외부 도구 트리는 `.tools/PINS.md`의 tree hash를 검증하여 배치하며, 승인 없는 의존성 설치 및 외부 전송을 철저히 차단

### 4. 📱 모바일 텔레그램 스터디 브리지 (Telegram Bot Bridge)
- **이동 중 읽기 전용 학습**: 스마트폰 텔레그램 메신저로 언제 어디서든 기존 지식 볼트를 검색·조회·설명하고 소크라테스식 문답을 진행하며, 노트 작성·수정·삭제는 하지 않음
- **클라우드 실시간 동기화**: Mac에서 생성·수정된 노트는 Google Drive를 통해 스마트폰 Obsidian 앱에 즉시 동기화
- **인라인 버튼 및 메뉴 제어**: 좌측 하단 `[Menu]` 버튼과 터치 버튼으로 AI 모델(`Gemini 3.1 Pro` ↔ `2.5 Flash`) 및 추론 강도(`High/Med/Low`) 즉시 전환
- **무결점 서식 렌더링 (`MessageEntity`)**: 마크다운 기호(`\`, `*`, `` ` ``) 노출 없이 스타일 속성 배열만 분리 전송하고 로컬 경로(`file://`)를 정제하는 방어 아키텍처 탑재
- **맥 OS 부팅 시 자동 구동 (`launchd`)**: 재부팅 후에도 명령어 입력 없이 상시 구동되며 프로세스 종료 시 자동 복구(`KeepAlive`)
- **AGENTS.md Rule 5 보안 경계**: 환경 변수 주입, Chat ID 화이트리스트, `STUDY_SURFACE=telegram` 도구 게이트로 vault 쓰기·삭제와 홈 디렉터리 스윕을 차단

---

## 🚀 빠른 시작 (Quick Start)

### 1단계: 하네스 설치 및 Vault 연결
AI CLI(Claude Code, Codex, Gemini CLI 등)에서 다음과 같이 요청하거나 셸 스크립트를 직접 실행한다:

```sh
# CLI 대화창에서 요청 시
"study-install로 이 컴퓨터에 하네스를 설치하고 vault를 연결해 줘."

# 직접 부트스트랩 실행 시
./.agents/skills/study-install/scripts/bootstrap.sh \
  --vault "/absolute/path/to/my-obsidian-vault" \
  --profile personal \
  --sync google-drive
```

### 2단계: 모바일 텔레그램 스터디 봇 구동 (선택 사항)
폰에서 볼트를 **검색·조회·문답**하는 읽기 전용 브리지다. 노트 작성·수정·삭제는 하지 않으며, 그 경계는 안내문이 아니라 `.agents/hooks/study-tool-guard.py`가 강제한다. 텔레그램의 `@BotFather`에게서 봇 토큰을 발급받은 후, Mac 터미널에서 아래 명령어로 봇을 백그라운드에 구동한다:

```bash
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHI..."
export TELEGRAM_ALLOWED_CHAT_ID="내_CHAT_ID_숫자"

# 봇 상시 가동 (nohup 방식)
nohup ./_workspace/telegram_bot/run_bot.sh > _workspace/telegram_bot/bot.log 2>&1 &

# 또는 맥 부팅 시 자동 시작 (launchd 방식 - 추천)
launchctl load -w ~/Library/LaunchAgents/com.nohdol.telegrambot.plist
```
> 📖 **상세 세팅 및 자동 시작 가이드**: [모바일 텔레그램 스터디 브리지 가이드](docs/guides/mobile-telegram-bot.md) 참조

### 3단계: 피드 스크래퍼 구동 (선택 사항)
RSS 소스를 vault로 자동 수집한다. **어느 소스를 켤지는 컴퓨터마다 다르므로**, 코드(카탈로그)는 추적하고 선택은 비추적 설정 파일에 둔다:

```bash
mkdir -p _workspace/feed_scraper
cp -p examples/feed_scraper/* _workspace/feed_scraper/
cd _workspace/feed_scraper

python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp sources.local.example.toml sources.local.toml   # 켤 소스 고르기

./run_scraper.sh
```
`feed` 소스(제목·링크만 수집)는 외부 API를 쓰지 않으므로 키가 필요 없다. `geeknews`만 Gemini 키를 `.env`에 넣어야 한다.

> 📖 **소스 추가 및 운영 가이드**: [피드 스크래퍼 가이드](docs/guides/feed-scraper.md) 참조

---

## 🧩 스킬 구성 (Skills Map)

모든 스킬은 `.agents/skills/` 디렉터리에 위치하며, 세부 사용법과 경계는 [한글 스킬 안내(.agents/skills/README.ko.md)](.agents/skills/README.ko.md)에서 확인할 수 있다.

```text
.agents/skills/
├── archify/             # 명시 호출 전용 단독 HTML 인터랙티브 다이어그램 (vault 밖)
├── context7/            # 최신 버전 라이브러리 공식 문서 조회
├── defuddle/            # 공개 웹 페이지 본문 마크다운 추출
├── diagram/             # 구조별 다이어그램 도구 선택 (Mermaid / D2 / Canvas)
├── ingest/              # 웹·논문·영상 매체별 수집 및 노트화 라우팅
├── knowledge-graph/     # 결정적 지식 그래프 재생성 및 근거 검증
├── metaskill/           # 하네스 규칙·스킬·설치기·스펙 자체 개선
├── note-writer/         # 원자적 검증 노트 작성, 프론트매터·index 정책 집행
├── obsidian/            # Obsidian 문법·캔버스·Bases 검증 및 CLI 제어
├── paper-search/        # 공개 논문 탐색·다운로드·메타데이터 검증
├── recall/              # 출처 추적 가능한 간격 반복 복습 카드 제작
├── study-install/       # 설치처 부트스트랩 및 로컬 환경 검사
├── study-session/       # 물어서 가르치는 소크라테스식 학습 대화
├── study-video/         # 자막 우선 영상 학습, 프레임 확인은 조건부
├── understand/          # Understand Anything 9개 모드 내부 라우팅
├── using-study/         # 지식 우선 세션 운영 및 세션 컨텍스트 관리
├── vault-gardening/     # 지식 루트 드리프트·고아/깨진 링크·index 비대화 점검
└── vault-search/        # 로컬 임베딩으로 curated 노트를 의미 검색
```

---

## 📚 문서 지도 (Documentation Architecture)

이 프로젝트의 세부 아키텍처 결정(ADR), 단계별 구현 스펙(Specs), 보안 검토 보고서는 모두 `docs/` 디렉터리에 체계적으로 정리되어 있다.

- **[문서 지도 (docs/README.md)](docs/README.md)**: 전체 ADR, 스펙, 제안 문서의 MOC(Map of Content)
- **[모바일 텔레그램 연동 가이드](docs/guides/mobile-telegram-bot.md)**: 스마트폰 ↔ Mac 하네스 브리지 구축 가이드 (읽기 전용 — 조회·문답만)
- **[피드 스크래퍼 가이드](docs/guides/feed-scraper.md)**: RSS 소스 자동 수집, 컴퓨터별 소스 선택, 신규 소스 추가 절차
- **[하네스 변경 이력 (Changelog)](docs/harness-changelog.md)**: Phase 1 ~ Phase 2b 기능 업데이트 및 아키텍처 변경 기록
- **운영 규칙 원본**: [AGENTS.md](AGENTS.md) (모든 AI 에이전트 및 CLI가 세션 시작 시 우선 준수하는 불변 규칙)
