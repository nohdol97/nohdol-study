# nohdol-study

Claude Code와 Codex가 같은 파일 규약으로 사용하는 공부 하네스다. 원문은
`raw/`, 검증해 정리한 지식은 `wiki/`에 두며 Markdown과 위키링크가 유일한
원본이다. Obsidian은 그래프·편집 UI를 제공하는 선택 사항이다.

하네스 저장소는 지식 파일을 추적하지 않는다. 컴퓨터마다 다른 지식 경로,
동기화 방식, NotebookLM 모드와 도구 상태는 미추적 `REGISTRY.md`에만 남고,
`vault/`는 실제 지식 루트를 가리키는 미추적 심링크다.

## 제공 범위

Phase 1:

- 설치처별 지식 디렉터리 선택과 안전한 재설치
- `raw/`, `wiki/`, `index.md`, `log.md`, `hot.md` 구조
- Claude Code·Codex 공용 스킬과 세션 훅
- 원자적 노트, flat YAML, 위키링크, 주장별 근거·불확실성 규약

Phase 2:

- 공개 웹 문서의 defuddle 불변 캡처
- 공개 학술 소스의 논문 검색·PDF 보존·검증 노트화
- 한국어·영어 자막 우선의 transcript-first 영상 학습
- 검증 파일만 묶는 NotebookLM 학습 패킷
- article·topic·source 타입의 결정적 JSON 그래프와 근거 검증형 추론 계층

Phase 2b-A(외부 소스 pin), 2b-B(Understand Anything adapter 9종),
2b-C(typed 지식 그래프)는 구현됐다.

- **구현됨(2b-A)** — 미추적 `.tools/` 루트에 upstream 정확 commit을 내려받아
  tree hash가 일치할 때만 배치하는 설치기. 전역 스킬 디렉터리와 vault는
  건드리지 않고, 소스만 놓을 뿐 의존성 설치나 코드 실행은 하지 않는다.
- **구현됨(2b-B)** — `understand` 스킬 하나가 9개 entry point(그래프 생성·
  위치 찾기·설명·온보딩·변경 영향·도메인·지식 베이스·dashboard·Figma)를
  내부 라우팅한다. 공통 경계는
  `.agents/skills/understand/references/adapter-contract.md` 하나가
  운반한다 — 그래프는 탐색 수단이지 근거가 아니며 사실 답변은 소스 파일
  확인 뒤에만 완료하고, vault 분석 산출물은 `_workspace/`로 돌리며,
  dashboard와 Figma는 실행별 명시 요청·승인 대상이다. mode별 절차는
  `references/modes.md`에 있다.
- **구현됨(2b-C)** — article·topic·source 타입 그래프. 노트가 1개여도
  주제 분류와 인용 출처로 유효한 그래프가 나오고, 노트 본문은 그래프에
  담기지 않는다. 모델이 추론한 entity·claim은 `--semantic`으로만 들어오며
  인용 노트에서 근거 앵커가 해석되지 않으면 버려진다.
- **남음** — Obsidian Markdown·Bases·JSON Canvas·공식 CLI 스킬 4종(2b-D),
  검증 export packet만 올리는 선택적 NotebookLM CLI bridge(2b-E)

mode마다 런타임 계층이 다르다. `understand-knowledge`만 `python3`로 바로
돌고, 그래프 소비형 5종은 먼저 만들어진 그래프를 필요로 하며,
`understand`·`understand-figma`·`understand-dashboard`는 빌드된 의존성이
필요해 별도 승인 전까지 `unavailable`로 보고한다.

웹 dashboard는 스킬로 제공하되 자동으로 열지 않고 사용자가 요청할 때만
localhost에서 실행한다. Figma와 NotebookLM 외부 전송도 실행별 승인
대상이다. Phase 2c에서는 basic-memory를 지정 corpus의 read/search 제한
파일럿으로 비교하고 PaperQA2를 논문 심층 질의에 조건부 사용한다.

## 설치

Claude Code나 Codex에서 다음과 같이 요청한다.

```text
study-install로 이 컴퓨터에 하네스를 설치해줘.
```

설치 과정은 지식 루트, `personal`/`corporate` 프로필, 동기화 라벨,
NotebookLM `off`/`consumer`/`enterprise` 모드를 선택한다. 기존 Obsidian
vault, 새 Obsidian 호환 디렉터리, 일반 디렉터리 모두 가능하다.

직접 초기화할 수도 있다.

```sh
.agents/skills/study-install/scripts/bootstrap.sh \
  --vault "/absolute/path/to/knowledge" \
  --profile personal \
  --sync google-drive \
  --notebooklm consumer
```

Phase 2 도구는 상태 확인과 설치를 분리한다.

```sh
.agents/skills/study-install/scripts/install-phase2-tools.sh --check
.agents/skills/study-install/scripts/install-phase2-tools.sh --install
```

Phase 2b 외부 소스도 같은 방식으로 나뉜다. `--check`는 네트워크에 접근하지
않고 Node·pnpm·Obsidian과 각 pin 상태만 관찰한다.

```sh
.agents/skills/study-install/scripts/install-phase2b-tools.sh --check
.agents/skills/study-install/scripts/install-phase2b-tools.sh --install
```

pin 원장은 추적되는 `.tools/PINS.md` 하나뿐이고 나머지 `.tools/` 내용은
미추적이다. `--install`은 원장의 정확한 commit을 받아 tree hash를 다시
계산하고, 일치할 때만 트리를 배치한다. hash 불일치, 미충족 runtime, 파싱되지
않는 pin, `python3` 부재는 모두 설치를 중단시킨다. 이미 있는 체크아웃이
원장과 다르면 덮어쓰지 않고 보고한다. tag pin은 upstream ref와도 대조해
이동한 tag를 막지만, 이는 무결성 장치가 아니라 변조 신호다 — API에 닿지
못하면 보고만 하고 진행한다. 다운로드가 commit 주소로 이뤄지고 실제 관문은
tree hash이기 때문이다. Obsidian이 없어도 설치는 실패하지 않으며 공식 CLI만
`unavailable`이 된다.

설치기는 vault에 Git을 초기화하거나 기존 노트를 변경하지 않는다. API 키와
NotebookLM 로그인도 만들거나 저장하지 않는다.

## NotebookLM 경계

개인용 `consumer` 모드는 공식 상시 동기화가 아니라 검증된 주제별
스냅샷이다.

```sh
.agents/skills/notebooklm-export/scripts/export.sh \
  --name topic-slug \
  vault/wiki/relevant-note.md \
  vault/raw/relevant-source.pdf
```

결과의 `00-manifest.md`에는 원본 상대경로, SHA-256, 검증 상태, 확인일이
기록된다. 퀴즈·플래시카드·인포그래픽·마인드맵·답변은 학습용 파생물이며,
다시 지식으로 저장하려면 인용된 원문을 직접 확인해야 한다.

현재 수동 업로드 경로는 구현돼 있다. 웹 UI 없이 사용하는 선택적
`notebooklm-py` bridge는 보안 게이트를 통과한 릴리스만 설치하도록 Phase
2b에서 구현한다. bearer cookie, public share, vault 전체 upload, master
token, MCP/server는 기본 경로에서 허용하지 않는다.

`enterprise`는 공식 API 후보지만 별도 Google Cloud 프로젝트·라이선스·API
활성화·사용자 인증이 필요하다. `study-install`은 준비 상태만 관찰하고
자격증명을 저장하지 않는다.

## 스킬 구성

```text
.agents/skills/
├── context7/            # 현재 버전 라이브러리 공식 문서
├── defuddle/            # 공개 웹 본문 정리
├── ingest/              # 웹·논문·영상 소스 라우팅
├── knowledge-graph/     # article·topic·source 타입 그래프와 근거 검증
├── metaskill/           # 하네스·스킬·규칙 개선
├── note-writer/         # 원자적 검증 노트 작성
├── notebooklm-export/   # 검증된 주제별 NotebookLM 패킷
├── paper-search/        # 공개 논문 검색·다운로드·검증
├── study-install/       # 설치처 bootstrap과 도구 점검
├── study-video/         # transcript-first 2-pass 영상 학습
├── understand/          # Understand Anything 9개 mode 내부 라우팅
└── using-study/         # 지식 우선 세션 운영
```

Understand Anything 9개 entry point는 `understand` 스킬 하나가 내부 라우팅으로
모두 제공한다. upstream의 main-pulling
전역 installer는 쓰지 않고, source를 project-local로 고정·검증해 두고
dependency 설치는 감사 통과 전까지 막는다. `knowledge-graph`는 이제
article/topic/source schema와 근거가 있는 암묵 관계를 갖췄다.

사용 시점·금지 경계·핵심 절차는
[한글 스킬 안내](.agents/skills/README.ko.md)에 정리되어 있다.

## 의존성

- 필수: POSIX 셸과 Claude Code 또는 Codex 중 하나
- 선택 UI: Obsidian
- Phase 2 웹: `defuddle`
- Phase 2 논문: `paper-search`
- Phase 2 영상: `yt-dlp`, `ffmpeg`, 전역 `watch` 스킬
- 그래프 기준 파서: Python 표준 라이브러리
- Phase 2b `understand-knowledge`: Python 표준 라이브러리만 (지금 동작)
- Phase 2b `understand`·`understand-figma`·`understand-dashboard`: Node 22+,
  pnpm 10+와 빌드된 core (정확 dependency audit 통과 후 — 그전까지 unavailable)
- 선택 Obsidian CLI: Obsidian 1.12.7+ 설치본과 실행 중인 앱

`watch`의 Whisper 경로는 Groq 또는 OpenAI로 오디오를 전송할 수 있으므로
기본 공부 워크플로는 항상 `--no-whisper`를 사용한다. 사용자가 해당 영상의
외부 전사를 명시 승인한 경우에만 활성화한다.

## 문서

- [방향 제안](docs/proposals/2026-07-25-nohdol-study-direction.md)
- [Phase 1 스펙](docs/specs/2026-07-25-phase1-study-harness.md)
- [Phase 2 스펙](docs/specs/2026-07-25-phase2-ingest-notebooklm-graph.md)
- [Phase 2b 스펙](docs/specs/2026-07-25-phase2b-cli-learning-integrations.md)
- [초기 구조 ADR](docs/adr/001-initial-study-harness.md)
- [Phase 2 파생 도구 ADR](docs/adr/002-phase2-derived-workflows.md)
- [CLI 학습 연동 ADR](docs/adr/003-cli-learning-integrations.md)
- [외부 연동 보안 검토](docs/reviews/2026-07-25-notebooklm-understand-anything-security.md)
- [추가 도구 도입 검토](docs/reviews/2026-07-25-additional-tools-review.md)
- [다음 세션 작업 인계](docs/handoffs/2026-07-25-next-session.md)
- [문서 지도](docs/README.md)
