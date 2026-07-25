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
2. 저장소의 공식 레퍼런스 템플릿(`examples/telegram_bot/`)을 로컬 작업 디렉터리로 복사한 뒤, 토큰만 주입하여 봇을 임시 실행한다:
   ```bash
   # 공식 템플릿 복사 (최초 1회)
   mkdir -p _workspace/telegram_bot
   cp -p examples/telegram_bot/* _workspace/telegram_bot/

   # 임시 실행
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

# 백그라운드 상시 구동 (nohup 활용)
nohup ./_workspace/telegram_bot/run_bot.sh > _workspace/telegram_bot/bot.log 2>&1 &
```

#### 💡 [고급] 맥(macOS) 부팅 시 자동 시작 (`launchd` LaunchAgent 등록)
매번 컴퓨터 재부팅 시 터미널 명령어를 입력하지 않고 **맥이 부팅되자마자 알아서 백그라운드 구동되도록** 하려면, macOS 공식 부팅 서비스 관리자인 `launchd`를 활용할 수 있다.
보안 계율(RULE 5)에 따라 비밀 토큰은 프로젝트 및 `_workspace/` 내부에 절대 저장하지 않으므로, 사용자 계정 전용 경로인 `~/Library/LaunchAgents/com.nohdol.telegrambot.plist`에 아래와 같이 환경변수 주입 설정을 생성하고 등록한다:

```bash
# 1. launchctl 등록 및 실행
launchctl load -w ~/Library/LaunchAgents/com.nohdol.telegrambot.plist

# 2. 구동 상태 확인 (PID 출력 확인)
launchctl list | grep telegrambot
```
* **이점**: 재부팅 후에도 자동 구동되며, 예기치 못한 예외로 프로세스가 종료되더라도 macOS가 즉시(`KeepAlive`) 재구동시킨다.

## 4. 텔레그램 메뉴 및 명령어 사용법

봇 구동 시 텔레그램 채팅창 좌측 하단에 공식 **`[Menu]` (메뉴)** 버튼이 자동 등록된다.

| 명령어 | 메뉴 설명 | 주요 기능 및 인라인 버튼 |
|---|---|---|
| **`/skill`** | 🧩 핵심 공부 스킬 선택 | • `[ 🧠 소크라테스 문답 (study-session) ]`<br>• `[ 🃏 복습 플래시카드 (recall) ]`<br>• `[ 📄 논문 탐색·검증 (paper-search) ]`<br>• `[ 🌿 vault 드리프트 점검 (vault-gardening) ]`<br>• `[ 🔄 스킬 해제 (일반 자유 대화) ]` |
| **`/model`** | 🤖 AI 모델 선택 | • `[ 🤖 Gemini 3.1 Pro ]` (최상위 심층 학습/추론/아키텍처 분석)<br>• `[ ⚡ Gemini 2.5 Flash ]` (초고속 일상 메모/요약)<br>• `[ 🔄 기본값 ]` (초기화) |
| **`/effort`** | 🧠 추론 강도 선택 | • `[ 🔥 High ]` (가장 깊은 사고 및 엄격한 출처 검증 - 권장)<br>• `[ ⚖️ Medium ]` (균형 잡힌 속도와 지능)<br>• `[ ⚡ Low ]` (빠른 즉답) |
| **`/cancel`** | ⏹ 실행 중인 작업 취소 | 진행 중인 CLI 프로세스를 종료하고 부분 출력이 있으면 함께 반환. 진행 메시지의 `[ ⏹ 취소 ]` 버튼과 동일 |
| **`/status`** | ⚙️ 상태 확인 | 현재 작동 중인 모델, 추론 강도, 활성 스킬, **실행 중인 작업 유무**, Vault 연결 경로, CLI 엔진, Git 상태 출력 |
| **`/new`** | 🔄 새 대화 시작 | 이전 세션 기억을 초기화하고 새로운 대화 시작 |
| **`/help`** | 📚 도움말 | 사용법 및 소크라테스식 학습 프롬프트 예시 안내 |

> [!NOTE]
> `/skill`에는 **대화를 그 모드로 고정하고 싶은 스킬만** 둔다. `note-writer`, `ingest`,
> `knowledge-graph`, `understand`, `diagram` 등 나머지는 하네스가 요청 문구를 보고
> 자동으로 고르므로 버튼이 필요 없다 — "기록해", "깨진 링크 찾아줘", "이 코드베이스 파악해줘"처럼
> 하고 싶은 것을 그냥 쓰면 된다. 버튼을 늘리면 자동 라우팅이 고를 것을 사람이 먼저 고정해
> 오히려 잘못된 스킬에 갇힌다.
>
> `study-video`도 마찬가지로 자동 라우팅된다. **영상 URL만 붙여넣어도 2-pass 분석이 시작된다.**
> 스킬 설명의 `explicitly selected`가 가리키는 것은 스킬이 아니라 *영상*이다 — 사용자가 특정 영상을
> 앞에 놓아야 동작하고, 스스로 영상을 찾아 나서지 않는다는 뜻이다.
>
> 대신 안쪽에 게이트가 있다: 자막을 우선 쓰고 `--no-whisper`를 **항상** 붙이므로 오디오는 그 영상에
> 대한 별도 승인 없이 외부 전사 서비스로 나가지 않으며, 프레임은 트랜스크립트로 고른 타임스탬프만
> 뽑는다.
>
> **영상 길이는 제약이 아니다.** 비용은 재생 시간이 아니라 트랜스크립트 분량과 고른 타임스탬프 수에
> 비례한다. 실측(102분 강의): 1-pass는 자막만 받아 2.3MB, 정리된 트랜스크립트 27k 토큰, 프레임 12장
> 248KB. 전체 샘플링이었다면 수백 장이 나왔을 자리다. 실제로 조심할 것은 셋뿐이다 —
> **자막 없는 영상**(Whisper 폴백이 필요해지고 오디오가 외부로 나간다), **모바일 대기 시간**(2-pass가
> 원본을 내려받으므로 봇이 수 분간 "생각 중" 상태), 그리고 지금 돌리고 싶지 않은 링크를 그냥
> 붙여넣는 것(그럴 땐 "나중에 볼 거야"처럼 의도를 같이 적는다).

### ⏳ 오래 걸리는 작업

모바일에서 가장 답답한 것은 응답이 아니라 **살아 있는지 모르는 것**이다. 그래서:

- 진행 메시지가 **5초마다 경과 시간으로 갱신**된다. `editMessageText`는 텔레그램에서 무음이므로
  **알림·소리·뱃지가 발생하지 않는다.** 화면을 열어두면 숫자가 올라가고, 닫아두면 조용하다.
  진짜 알림은 완료된 답변 하나뿐이다.
- 타이핑 표시는 텔레그램이 약 5초 뒤 지우므로 4초마다 갱신해 유지한다.
- 진행 메시지에 `[ ⏹ 취소 ]` 버튼이 붙는다. `/cancel` 도 같다. 취소하면 부분 출력이 있으면 함께 온다.
- `STUDY_RUN_TIMEOUT`(기본 1200초 = 20분)을 넘기면 자동 중단하고 알린다. 예전에는 CLI가 멈추면
  그 메시지가 영원히 `생각 중...` 이었고 **폰에서는 손쓸 방법이 없었다.**
- 앞 작업이 도는 중에 메시지를 보내면 막지는 않되, 두 실행이 같은 세션 이력을 공유해 답변이 섞일 수
  있다고 한 줄 알린다.

### ♻️ 재시작과 상태 유지

launchd `KeepAlive`가 봇을 스스로 되살리므로 재시작은 예고 없이 일어난다. 모델·추론 강도·활성 스킬은
`bot_state.json`에 저장되어 복원되고, **스킬이 켜져 있었다면 복원 사실을 한 번 알린다.**

이게 중요한 이유는 `study-session` 때문이다. 예전에는 재시작 시 스킬 플래그가 조용히 사라져,
사용자는 소크라테스식 문답을 계속 하는데 봇은 어느 순간부터 평범하게 답하고 있었다. 그걸 알 방법이
없었다. 참고로 **대화 이력 자체는 원래 안 날아간다** — 봇이 CLI를 `--continue`(또는 `--resume latest`)로
부르므로 문답 기록은 맥의 CLI 세션에 남는다. 유실되던 것은 스킬 접두사 주입뿐이었다.

> `bot_state.json`에는 chat ID가 들어가므로 `.gitignore` 대상이다. 커밋하지 않는다.

### 💡 모바일 딥다이브 활용 팁
- **과거 노트 검색 및 종합**: *"내가 예전에 적어둔 피지컬 AI 노트에서 감지(Sensor) 부분만 요약해줘"*
- **지식 연결고리 발견**: *"내 노트들 중에 서로 연관이 깊은데 위키링크로 안 엮인 고아 노트가 있어?"*
- **복습 과외 (`recall`)**: *"내 볼트 `wiki/`의 노트들을 바탕으로 오늘 풀 수 있는 퀴즈 5문제 내줘"*
- **외부 웹/논문 캡처**: *"이 논문 다운받아서 노트화해 줘 [arXiv/URL]"*

## 5. 마크다운 렌더링 및 메시지 분할 아키텍처 (Telegram MessageEntity 기반)

AI CLI(`agy` 또는 `gemini`)가 출력하는 풍부한 마크다운(GitHub Flavored Markdown: `# 제목`, `**굵은 글씨**`, 표, 코드 블록 등)을 텔레그램 채팅창에서 깨짐 없이 깔끔하게 렌더링하기 위해 다음과 같은 포맷팅 엔진과 방어 로직이 내장되어 있다.

1. **`telegramify-markdown` 및 `MessageEntity` 기반 구문 변환**:
   - 텔레그램 Bot API의 `parse_mode="MarkdownV2"`는 문자열 기반 파싱을 수행하므로 이스케이프 기호(`.`, `-`, `(` 등)가 조금만 어긋나도 오류를 내거나 화면에 백슬래시(`\`), 별표(`*`), 백틱(`` ` ``)을 그대로 노출하는 한계가 있다.
   - 이를 원천 차단하기 위해 `bot.py`는 `telegramify_markdown.telegramify()`를 호출하여 마크다운 기호가 전혀 없는 100% 순수 텍스트(`item.text`)와 스타일 속성 객체 배열(`MessageEntity`)을 분리 생성한다. 이로써 텍스트 자체에 백슬래시나 별표가 전혀 포함되지 않아 깨짐이나 노출을 완벽하게 방지한다.
2. **코드 블록 보호 및 안전한 4,000자 분할**:
   - `telegramify()` 호출 시 `max_message_length=4000`, `min_file_lines=999999` 파라미터를 지정하여 코드 블록이 파일 첨부로 변환되는 것을 막고, 텔레그램 전송 제한 길이를 초과하지 않도록 안전하게 분할한다.
3. **로컬 파일 링크(`file://`, `vscode://`) 프로토콜 정제 방어**:
   - AI CLI 모델이 응답 중 로컬 경로(`[CLAUDE.md](file:///...)`)를 마크다운 링크로 출력할 경우, 텔레그램 Bot API는 미지원 프로토콜(`BadRequest: Entity url ... is invalid: unsupported url protocol`)로 간주하여 전송을 차단하고 예외를 발생시킨다.
   - 이를 방지하기 위해 마크다운 변환 전 전처리 단계에서 정규식(`re.sub`)을 통해 웹 URL(`http://`, `https://`, `tg://` 등)을 제외한 모든 로컬 프로토콜 링크를 인라인 코드 formatting(예: `` `CLAUDE.md` ``)으로 변환하여 API 거부를 100% 방지한다.
4. **이중 별표(`**`) 표기 교정 및 평문 폴백(Fallback) 방어**:
   - 텔레그램 일반 마크다운(`parse_mode="Markdown"`)을 쓰는 안내 메시지(`/start`, `/help`, 콜백 버튼 등)에서는 `**굵은 글씨**` 대신 텔레그램 문법인 단일 별표(`*굵은 글씨*`)를 적용해 파싱 오류를 원천 차단한다.
   - 만약 예기치 못한 특수 기호로 인해 엔티티 전송이 실패할 경우, 메시지 유실을 막기 위해 평문(Plain text) 모드로 자동 전환되어 출력 결과를 끝까지 전송한다.
5. **의존성 상시 자동 관리**:
   - `./_workspace/telegram_bot/run_bot.sh` 실행 시 가상환경(`.venv`) 내에 `telegramify-markdown`이 없으면 `uv pip install`로 즉시 자동 탑재되도록 구성되어 있다.

## 6. 트러블슈팅 및 운영 FAQ (Troubleshooting & Maintenance)

### Q1. 봇이 응답하지 않거나 `409 Conflict` 오류가 로그에 찍힐 때
- **원인**: 텔레그램 Bot API는 동일한 토큰으로 2개 이상의 프로세스가 동시에 `getUpdates` 폴링을 수행하는 것을 금지한다. 수동 실행(`nohup`)과 자동 시작(`launchd`)이 중복되었거나 백그라운드 프로세스가 2개 이상 떠 있을 때 발생한다.
- **해결 방안**:
  ```bash
  # 1. 모든 봇 프로세스 강제 종료
  ps aux | grep "[b]ot.py" | awk '{print $2}' | xargs kill -9 2>/dev/null || true

  # 2. launchd로 정상 단일 구동 재개
  launchctl load -w ~/Library/LaunchAgents/com.nohdol.telegrambot.plist
  ```

### Q2. 봇 구동 상태 및 실시간 로그를 확인하고 싶을 때
- **구동 상태 확인**:
  ```bash
  launchctl list | grep telegrambot
  # 또는
  ps aux | grep "[b]ot.py"
  ```
- **실시간 실행 로그 조회**:
  ```bash
  tail -f _workspace/telegram_bot/bot.log
  ```

### Q3. 봇을 일시 정지하거나 완전히 중단시키고 싶을 때
- `launchd`에 등록된 경우 일반 `kill` 명령어로 죽여도 즉시 다시 살아나므로(`KeepAlive`), 아래와 같이 서비스 언로드(Unload) 명령을 실행해야 한다:
  ```bash
  # 서비스 일시 정지 및 언로드
  launchctl unload -w ~/Library/LaunchAgents/com.nohdol.telegrambot.plist
  ```

## 7. 부록: LLM 원클릭 구현 및 공식 템플릿 안내 (Reference Implementation Appendix)

이 문서의 스펙만으로도 AI 모델이 봇 코드를 생성할 수 있지만, 가장 확실하고 검증된 코드를 즉시 적용할 수 있도록 **저장소 자체에 공식 레퍼런스 스크립트(`examples/telegram_bot/`)를 제공**한다.

1. **공식 레퍼런스 파일 구성 (`examples/telegram_bot/`)**:
   - `bot.py`: `python-telegram-bot` 및 `telegramify-markdown` 기반 비동기 브리지 핵심 로직 (정제 방어 및 `MessageEntity` 변환 100% 탑재)
   - `run_bot.sh`: 가상환경(`.venv`) 자동 생성 및 의존성 탑재를 보장하는 실행 부트스트래퍼
2. **LLM 활용 시 프롬프트 팁**:
   - 다른 사람이나 다른 세션에서 AI CLI에게 봇을 띄워달라고 할 때는 아래 한 문장만 요청하면 된다:
   > *"이 저장소의 `examples/telegram_bot/`에 있는 봇 레퍼런스 템플릿을 `_workspace/telegram_bot/`으로 복사하고, 내 토큰(`...`)과 Chat ID(`...`)로 백그라운드 구동해 줘."*
