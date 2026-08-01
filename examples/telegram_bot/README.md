# 모바일 텔레그램 스터디 브리지 레퍼런스 구현 (Telegram Bot Reference Implementation)

이 디렉터리는 `nohdol-study` 하네스를 스마트폰 텔레그램(Telegram)과 연동하는 **공식 파이썬 봇 브리지(`bot.py`)와 실행 스크립트(`run_bot.sh`)의 레퍼런스 템플릿**이다.

**이 브리지는 읽기 전용이다.** 볼트를 검색·조회·설명하고 문답하지만 노트를 쓰거나 고치거나 지우지 않으며, 그 경계는 안내문이 아니라 `.agents/hooks/study-tool-guard.py`가 강제한다. 이유는 [docs/guides/mobile-telegram-bot.md](../../docs/guides/mobile-telegram-bot.md) 2절에 있다.

## 🚀 사용 가이드 (3초 적용법)

1. **로컬 작업 공간(`_workspace/`)으로 복사**:
   보안 계율(RULE 5) 및 `.gitignore` 정책에 따라 가상환경(`.venv`)과 실행 로그는 비추적 영역인 `_workspace/`에서 구동해야 한다. 아래 명령어로 레퍼런스 스크립트를 작업 공간에 복사한다:
   ```bash
   mkdir -p _workspace/telegram_bot
   cp -p examples/telegram_bot/* _workspace/telegram_bot/
   ```

2. **환경변수 주입 및 실행**:
   ```bash
   export TELEGRAM_BOT_TOKEN="발급받은_토큰"
   export TELEGRAM_ALLOWED_CHAT_ID="내_CHAT_ID_숫자"

   # 백그라운드 실행
   nohup ./_workspace/telegram_bot/run_bot.sh > _workspace/telegram_bot/bot.log 2>&1 &
   ```

## 📖 핵심 문서 및 아키텍처 안내
- **상세 세팅 및 렌더링 원리 가이드**: [docs/guides/mobile-telegram-bot.md](../../docs/guides/mobile-telegram-bot.md)
- **주요 특징**:
  - `MessageEntity` 기반 100% 무결점 서식 분리 전송 (백슬래시 `\`, 별표 `*` 깨짐 원천 차단)
  - `file://`, `vscode://` 등 로컬 파일 링크 프로토콜 자동 사전 정제 방어
  - 4,000자 초과 대용량 응답의 안전한 코드 청크(Chunk) 분할 전송
  - 좌측 하단 `[Menu]` 버튼을 통한 스킬(`/skill`), 모델(`/model`), 추론 강도(`/effort`) 즉시 전환
  - `/skill`은 대화를 고정하고 싶은 조회 스킬만 노출한다(`vault-search`, `study-session`, `vault-gardening`). 나머지 조회 스킬은 요청 문구로 자동 라우팅된다
  - **기본 스킬은 `vault-search`**다. 강제 사전 검색이 아니라 스킬로 둔 이유는 모델이 건너뛸 수 있어야 하기 때문이다 — 임베딩 검색은 `"고마워"`에도 결과를 돌려주므로 매 턴 주입하면 무관한 발췌가 항상 붙는다. 해제는 "고른 적 없음"과 구분되는 별도 상태로 저장한다
  - 매 요청에 읽기 전용 표면임을 프롬프트로 알린다. 훅만으로도 쓰기는 막히지만, 모델이 노트를 시도했다가 거부당하는 왕복은 폰에서 몇 분짜리 `생각 중...`으로 보인다
  - 승인 프롬프트 없이 도는 표면이므로 `STUDY_SURFACE=telegram`을 주입해 `.agents/hooks/study-tool-guard.py` 게이트를 켠다. 지식 루트는 읽기 전용이고 쓰기는 `_workspace/`와 임시 디렉터리로만 열리며, 홈 디렉터리 스윕이 차단된다. **등록은 저장소가 아니라 CLI 전역 설정에서 하며**, 절차는 `study-install` 6단계에 있다
