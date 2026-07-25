# 모바일 텔레그램 스터디 브리지 (Telegram Bot Bridge) 가이드

`nohdol-study` 하네스를 스마트폰 텔레그램(Telegram)과 완벽히 연동하여, 언제 어디서든 모바일로 AI와 소크라테스식 학습을 진행하고 Obsidian 지식 볼트(`vault/`)를 조회·분석·기록할 수 있는 공식 연동 가이드다.

## 1. 아키텍처 및 원리

```text
[📱 스마트폰 (Telegram)] 
       ↕ (메시지 및 인라인 버튼 제어)
[💻 Mac 백그라운드 봇 (`_workspace/telegram_bot/run_bot.sh`)]
       ↕ (비동기 CLI 호출: agy / gemini)
[🤖 AI 모델 (Gemini 3.1 Pro / 2.5 Flash)]
       ↕ (노트 검색, 근거 대조, 작성 및 정합성 관리)
[📁 지식 저장소 (`/Users/nohdol/.../Obsidian Vault`)]
       ↕ (Google Drive 실시간 동기화)
[📱 스마트폰 (Obsidian 앱에서 방금 생성된 마크다운 노트 확인!)]
```

- **핵심 작동 방식**: 텔레그램으로 보낸 메시지를 Mac에서 구동 중인 비동기 파이썬 봇 엔진이 수신하여 로컬 CLI(`agy` 또는 `gemini`)를 백그라운드로 실행하고, 생성된 답변을 청크로 분할해 전송한다.
- **연속성 보장**: 대화 문맥(`--continue` / `--resume latest`)이 자동으로 유지되어 스마트폰에서도 끊김 없이 딥다이브 학습이 가능하다.

## 2. 보안 및 하네스 정책 준수 (AGENTS.md Rule 5)

이 브리지는 하네스 안전 규칙을 엄격히 준수하도록 설계되었다.

1. **자격증명 비추적 격리 (No Committed Secrets)**:
   - 텔레그램 봇 토큰이나 API 키를 Git 저장소나 `vault/` 내부의 파일에 절대 기재하지 않는다.
   - 모든 시크릿은 실행 시 환경 변수(`TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_CHAT_ID`)로만 주입된다.
   - 실행 가상환경(`.venv`) 및 로그 파일은 Git 비추적 디렉터리(`_workspace/telegram_bot/`) 내부에 격리된다.

2. **화이트리스트 차단 기능 (Chat ID Whitelisting)**:
   - 외부 텔레그램 메신저 특성상 누구나 봇에게 접근할 수 있는 위험을 방지하기 위해, 사용자 본인의 텔레그램 Chat ID(`TELEGRAM_ALLOWED_CHAT_ID`)를 설정한다.
   - 허용되지 않은 Chat ID에서 온 메시지는 **🚨 접근 권한이 없습니다** 안내와 함께 100% 차단된다.

## 3. 빠른 세팅 및 실행 가이드 (5분 컷)

### 1단계: 텔레그램 봇 토큰 발급
1. 텔레그램 앱에서 **`@BotFather`**를 검색해 대화를 시작한다.
2. `/newbot` 명령어를 전송하고 봇 이름과 사용자명(끝이 `_bot`으로 끝나야 함)을 지정한다.
3. 발급된 **HTTP API Token**(예: `123456789:ABCdefGHI...`)을 복사한다.

### 2단계: 내 Chat ID 알아내기 (최초 1회)
1. 텔레그램에서 생성한 봇에게 아무 메시지나 보낸다 (예: `/start` 또는 `안녕`).
2. Mac 터미널에서 토큰만 주입하여 봇을 임시 실행한다:
   ```bash
   TELEGRAM_BOT_TOKEN="발급받은토큰" ./_workspace/telegram_bot/run_bot.sh
   ```
3. 봇이 텔레그램으로 **"🚨 접근 권한이 없습니다. 당신의 Chat ID: `12345678`"** 라고 내 ID 숫자를 알려주면 해당 번호를 복사하고 터미널에서 `Ctrl+C`로 종료한다.

### 3단계: 완벽한 보안 모드로 실전 구동
터미널에서 내 Chat ID까지 주입하여 봇을 가동한다:

```bash
export TELEGRAM_BOT_TOKEN="발급받은토큰"
export TELEGRAM_ALLOWED_CHAT_ID="내_CHAT_ID_숫자"

# CLI 엔진을 gemini로 변경하려면 아래 주석 해제 (기본값: agy)
# export STUDY_CLI_CMD="gemini"

# 백그라운드 상시 구동 (nohup 활용 추천)
nohup ./_workspace/telegram_bot/run_bot.sh > _workspace/telegram_bot/bot.log 2>&1 &
```

## 4. 텔레그램 메뉴 및 명령어 사용법

봇 구동 시 텔레그램 채팅창 좌측 하단에 공식 **`[Menu]` (메뉴)** 버튼이 자동 등록된다.

| 명령어 | 메뉴 설명 | 주요 기능 및 인라인 버튼 |
|---|---|---|
| **`/skill`** | 🧩 핵심 공부 스킬 선택 | • `[ 🧠 소크라테스 문답 (study-session) ]`<br>• `[ 🃏 복습 플래시카드 (recall) ]`<br>• `[ 📝 원자적 노트 저장 (note-writer) ]`<br>• `[ 🕸️ 지식 그래프 점검 (knowledge-graph) ]`<br>• `[ 🔄 스킬 해제 (일반 자유 대화) ]` |
| **`/understand`** | 🔬 Understand 심층 분석 | • `[ 🔍 구조/아키텍처 파악 (understand) ]`<br>• `[ 💬 기능/코드 위치 찾기 (-chat) ]`<br>• `[ 📖 개념/흐름 깊이 설명 (-explain) ]`<br>• `[ 🗺️ 온보딩 학습 가이드 (-onboard) ]`<br>• `[ 🕸️ 지식 베이스 분석 (-knowledge) ]`<br>• `[ ❌ Understand 모드 해제 ]` |
| **`/model`** | 🤖 AI 모델 선택 | • `[ 🤖 Gemini 3.1 Pro ]` (최상위 심층 학습/추론/아키텍처 분석)<br>• `[ ⚡ Gemini 2.5 Flash ]` (초고속 일상 메모/요약)<br>• `[ 🔄 기본값 ]` (초기화) |
| **`/effort`** | 🧠 추론 강도 선택 | • `[ 🔥 High ]` (가장 깊은 사고 및 엄격한 출처 검증 - 권장)<br>• `[ ⚖️ Medium ]` (균형 잡힌 속도와 지능)<br>• `[ ⚡ Low ]` (빠른 즉답) |
| **`/status`** | ⚙️ 상태 확인 | 현재 작동 중인 모델, 추론 강도, 활성 스킬, Vault 연결 경로, CLI 엔진, Git 상태 출력 |
| **`/new`** | 🔄 새 대화 시작 | 이전 세션 기억을 초기화하고 새로운 대화 시작 |
| **`/help`** | 📚 도움말 | 사용법 및 소크라테스식 학습 프롬프트 예시 안내 |

### 💡 모바일 딥다이브 활용 팁
- **과거 노트 검색 및 종합**: *"내가 예전에 적어둔 피지컬 AI 노트에서 감지(Sensor) 부분만 요약해줘"*
- **지식 연결고리 발견**: *"내 노트들 중에 서로 연관이 깊은데 위키링크로 안 엮인 고아 노트가 있어?"*
- **복습 과외 (`recall`)**: *"내 볼트 `wiki/`의 노트들을 바탕으로 오늘 풀 수 있는 퀴즈 5문제 내줘"*
- **외부 웹/논문 캡처**: *"이 논문 다운받아서 노트화해 줘 [arXiv/URL]"*

## 5. 마크다운 렌더링 및 메시지 분할 아키텍처 (Telegram MarkdownV2)

AI CLI(`agy` 또는 `gemini`)가 출력하는 풍부한 마크다운(GitHub Flavored Markdown: `# 제목`, `**굵은 글씨**`, 표, 코드 블록 등)을 텔레그램 채팅창에서 깨짐 없이 깔끔하게 렌더링하기 위해 다음과 같은 포맷팅 엔진과 방어 로직이 내장되어 있다.

1. **`telegramify-markdown` 기반 자동 구문 변환**:
   - 텔레그램 Bot API(`MarkdownV2`)는 일반 마크다운과 달리 특수문자(`.`, `-`, `(`, `)`, `~`, `>` 등)의 엄격한 이스케이프를 요구한다.
   - `bot.py`는 CLI 응답 수신 시 `telegramify_markdown.markdownify()`를 호출하여 표준 마크다운을 텔레그램 호환 구문으로 자동 이스케이프 및 변환한다.
2. **코드 블록 보호 및 안전한 4,000자 분할 (`split_markdownv2`)**:
   - 텔레그램 1회 전송 제한 길이(4,096 UTF-16 단위)를 초과하는 긴 AI 응답을 단순 문자열 끊기로 분할할 경우 코드 블록(```)이나 마크다운 태그가 중간에 절단되어 API 오류(`BadRequest: can't parse entities`)가 발생한다.
   - `telegramify_markdown.split_markdownv2(mdv2_text, max_utf16_len=4000)`를 사용해 마크다운 태그와 코드 블록 경계를 보존하면서 안전하게 메시지 청크를 분할한다.
3. **이중 별표(`**`) 표기 교정 및 평문 폴백(Fallback) 방어**:
   - 텔레그램 일반 마크다운(`parse_mode="Markdown"`)을 쓰는 안내 메시지(`/start`, `/help`, 콜백 버튼 등)에서는 `**굵은 글씨**` 대신 텔레그램 문법인 단일 별표(`*굵은 글씨*`)를 적용해 파싱 오류를 원천 차단한다.
   - 만약 예기치 못한 특수 기호로 인해 `MarkdownV2` 전송이 실패할 경우, 메시지 유실을 막기 위해 평문(Plain text) 모드로 자동 전환되어 출력 결과를 끝까지 전송한다.
4. **의존성 상시 자동 관리**:
   - `./_workspace/telegram_bot/run_bot.sh` 실행 시 가상환경(`.venv`) 내에 `telegramify-markdown`이 없으면 `uv pip install`로 즉시 자동 탑재되도록 구성되어 있다.
