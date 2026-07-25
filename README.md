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
- 위키링크·백링크·누락·고아 노트의 결정적 JSON 그래프

Phase 2b-A(외부 소스 pin 설치 기반)는 구현됐고, 그 위의 스킬 노출은 아직
남아 있다.

- **구현됨** — 미추적 `.tools/` 루트에 upstream 정확 commit을 내려받아
  tree hash가 일치할 때만 배치하는 설치기. 전역 스킬 디렉터리와 vault는
  건드리지 않고, 소스만 놓을 뿐 의존성 설치나 코드 실행은 하지 않는다.
- **남음** — Understand Anything의 코드·도메인·diff·온보딩·설명·질의·
  dashboard·Figma·지식 9개 스킬 노출(2b-B), typed 지식 그래프(2b-C),
  Obsidian Markdown·Bases·JSON Canvas·공식 CLI 스킬 4종(2b-D), 검증 export
  packet만 올리는 선택적 NotebookLM CLI bridge(2b-E)

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
├── knowledge-graph/     # 결정적 위키링크 그래프와 링크 품질
├── metaskill/           # 하네스·스킬·규칙 개선
├── note-writer/         # 원자적 검증 노트 작성
├── notebooklm-export/   # 검증된 주제별 NotebookLM 패킷
├── paper-search/        # 공개 논문 검색·다운로드·검증
├── study-install/       # 설치처 bootstrap과 도구 점검
├── study-video/         # transcript-first 2-pass 영상 학습
└── using-study/         # 지식 우선 세션 운영
```

Phase 2b는 Understand Anything 9개를 모두 채택한다. upstream의 main-pulling
전역 installer는 쓰지 않고, 필요한 source와 dependency를 project-local로
고정·감사한다. `knowledge-graph`는 article/entity/topic/claim/source
schema와 근거가 있는 암묵 관계를 추가할 예정이다.

사용 시점·금지 경계·핵심 절차는
[한글 스킬 안내](.agents/skills/README.ko.md)에 정리되어 있다.

## 의존성

- 필수: POSIX 셸과 Claude Code 또는 Codex 중 하나
- 선택 UI: Obsidian
- Phase 2 웹: `defuddle`
- Phase 2 논문: `paper-search`
- Phase 2 영상: `yt-dlp`, `ffmpeg`, 전역 `watch` 스킬
- 그래프 기준 파서: Python 표준 라이브러리
- Phase 2b 코드·그래프: Node 22+, pnpm 10+ (정확 dependency audit 통과 후)
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
