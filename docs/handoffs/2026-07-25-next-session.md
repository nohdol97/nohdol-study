# 다음 세션 작업 인계 — Phase 2b 이후

- 작성일: 2026-07-25
- 기준 브랜치: `main`
- 현재 상태: Phase 1·2 구현 완료, Phase 2b·2c·3 미구현
- 결정 원본:
  - [방향 제안](../proposals/2026-07-25-nohdol-study-direction.md)
  - [ADR 003](../adr/003-cli-learning-integrations.md)
  - [Phase 2b 스펙](../specs/2026-07-25-phase2b-cli-learning-integrations.md)
  - [외부 연동 보안 검토](../reviews/2026-07-25-notebooklm-understand-anything-security.md)
  - [추가 도구 검토](../reviews/2026-07-25-additional-tools-review.md)

## 새 세션 시작 절차

1. `AGENTS.md`, 미추적 `REGISTRY.md`, 이 문서, ADR 003, Phase 2b 스펙을
   읽는다.
2. `git status --short --branch`와 `git pull --ff-only`로 기준 상태를
   확인한다. 사용자 변경이 있으면 보존한다.
3. 아래 명령으로 구현 전 기준선을 확인한다.

```sh
.agents/hooks/hooks_test.sh
python3 .agents/skills/knowledge-graph/scripts/build_graph_test.py
python3 .agents/skills/study-install/scripts/patch-watch-korean_test.py
.agents/skills/ingest/scripts/web-capture_test.sh
.agents/skills/notebooklm-export/scripts/export_test.sh
.agents/skills/study-install/scripts/bootstrap_test.sh
.agents/skills/study-install/scripts/install-phase2-tools_test.sh
python3 .agents/skills/metaskill/scripts/verify_harness.py
```

4. `study-install --check`에 해당하는 기존 스크립트로 로컬 capability를 다시
   관찰한다. 추적 문서에 설치 경로·계정·버전 상태를 하드코딩하지 않고
   `REGISTRY.md`만 갱신한다.
5. 한 세션에서 아래 작업 묶음 하나를 완료하는 것을 기본으로 한다.

## 다음에 가장 먼저 할 일 — Phase 2b-A

Understand Anything과 Obsidian skill을 위한 **project-local exact-pin 설치
기반**을 먼저 구현한다. 이 단계에서는 NotebookLM 인증·업로드, Figma API,
dashboard 실행, vault semantic 분석을 하지 않는다.

### 구현 범위

- 설치처별 외부 도구 root를 선택하거나 생성하되 Git에 추적하지 않는다.
- Understand Anything과 `kepano/obsidian-skills`의 정확한 release/commit,
  source URL, license, source hash를 기록한다.
- upstream `main` 자동 pull, `curl | bash`, `~/.agents/skills` 전역 심링크를
  사용하지 않는다.
- `study-install`에 `--check`와 명시적 `--install-phase2b-tools` 경로를
  분리한다. check는 설치하지 않는다.
- Node 22+와 pnpm 10+를 관찰하고, dependency 설치 전 exact lock과 audit
  결과를 요구한다.
- Obsidian이 없어도 설치 전체가 실패하지 않아야 한다. 공식 CLI 조건이
  충족되지 않으면 `unavailable`로만 기록한다.
- 실패·재실행·부분 설치에서 기존 전역 skill과 vault가 바뀌지 않는 테스트를
  추가한다.

### 완료 기준

- 같은 pin과 입력으로 같은 source hash가 나온다.
- 잘못된 hash, 이동한 tag, high 취약점, 불충분한 runtime에서 fail-closed
  한다.
- 설치 전후 `~/.agents/skills`와 vault Markdown의 path/hash가 같다.
- 설치처 상태는 `REGISTRY.md`에만 남고 Git 추적 파일에는 경로나 계정
  정보가 없다.
- focused test와 전체 metaskill 검증이 통과한다.
- 관련 README, 한글 skill 지도, MOC, changelog를 같은 커밋에서 갱신한다.

## 후속 작업 순서

### Phase 2b-B — Understand Anything 9개 adapter

`understand`, `understand-chat`, `understand-dashboard`, `understand-diff`,
`understand-domain`, `understand-explain`, `understand-figma`,
`understand-knowledge`, `understand-onboard`를 모두 project skill로 노출한다.

- chat·domain·explain·onboard·diff는 관련 source file을 다시 읽은 뒤에만
  사실 답변을 완료한다.
- dashboard는 사용자 요청 시에만 loopback으로 실행한다.
- Figma는 token·file key·`api.figma.com` 전송을 실행별 승인받는다.
- 코드 프로젝트 `.ua/`는 target·ignore·write 범위를 확인한다.
- vault 분석은 `_workspace/understand-anything/`로 리디렉션한다.

### Phase 2b-C — typed knowledge graph

- 현재 결정적 wikilink graph를 article/entity/topic/claim/source schema로
  확장한다.
- `wiki/` 문서가 1개여도 유효한 graph를 만든다.
- 최종 graph에서 노트 본문 사본을 제거한다.
- semantic enrichment는 opt-in으로 분리한다.
- inferred claim·edge에 source path, evidence anchor, extractor, confidence,
  verification을 강제한다.
- prompt-like note fixture와 vault 원본 hash 불변 테스트를 추가한다.

### Phase 2b-D — Obsidian skill 4종

`obsidian-markdown`, `obsidian-bases`, `json-canvas`, `obsidian-cli`를
project-local skill로 제공한다. 기존 nohdol-study `defuddle`는 유지한다.

- Markdown/Bases/Canvas는 Obsidian 앱 없이 생성·검증 가능해야 한다.
- CLI는 공식 요구 조건이 충족된 설치처에서만 available이다.
- `.base`와 `.canvas` fixture, wikilink·embed·callout 회귀 테스트를 둔다.

### Phase 2b-E — NotebookLM CLI bridge

현재 안정 릴리스가 redirect 수정과 안전한 exact dependency set을
충족하는지 다시 감사한 후 진행한다. 충족하지 않으면 installer와 wrapper
테스트만 구현하고 실제 인증·전송은 계속 차단한다.

- `notebooklm-export` packet manifest/hash를 재검증한다.
- packet 외 파일, symlink, vault 직접 경로, 미검증 note를 거부한다.
- 전용 credential profile은 저장소·vault·동기화 폴더 밖에 두고
  `0700`/`0600`을 확인한다.
- create/upload/generate/download는 실행 계획과 Google 전송 범위를 보여준
  뒤 승인받는다.
- master token, MCP/server, impersonation, public share, collaborator 변경,
  delete는 기본 경로에서 허용하지 않는다.

### Phase 2c — 제한 파일럿

1. basic-memory를 사용자가 지정한 corpus에서 read/search 중심으로 비교한다.
   `bm format`, 자동 write, reset은 금지하고 원본 hash를 확인한다.
2. PaperQA2는 사용자가 지정한 논문 corpus와 provider가 있을 때만 실행한다.
   외부 model·embedding 전송을 승인받고 citation을 원 PDF에서 재검증한다.

### Phase 3 — 학습 루프

다음 순서로 각각 별도 구현한다.

1. `diagram`: Mermaid 기본, D2→SVG, JSON Canvas, matplotlib→SVG
2. `study-session`: 소크라테스식 질문과 이해 확인
3. `vault-gardening`: 깨진 링크·고아·중복·index/log/hot 점검
4. `recall`: 근거 검증 가능한 Markdown 카드와 spaced repetition

## 남은 콘텐츠 작업

`피지컬 AI - 12살을 위한 안내서`의 본문과 근거 노트는 작성돼 있다.
사용자가 정한 방향대로 NotebookLM 이미지 생성은 사용하지 않고, Gemini
또는 사용자가 승인한 이미지 생성 경로로 어린이용 그림을 만든 뒤 다음을
완료한다.

- 생성 이미지라는 provenance와 생성일을 기록한다.
- 이미지가 사실 근거가 아니라 설명용임을 명시한다.
- vault의 note-local `assets/`에 저장하고 Obsidian embed를 추가한다.
- 문서의 감지–판단–행동–피드백 설명과 그림이 모순되지 않는지 확인한다.

이미지 생성 서비스로 note나 private source를 보낼 필요는 없다. 장면 설명만
전송한다.

## 보류 중인 후보와 재검토 trigger

- Graphiti: temporal fact/history 질의가 반복될 때
- Mem0: 개인화 agent memory가 명시 요구가 될 때
- Cognee: 다중 데이터·agent trace memory가 필요할 때
- Obsidian REST/MCP: 공식 CLI로 해결할 수 없는 live-app/remote-client
  요구가 생길 때
- Kuzu: 아카이브 상태이므로 신규 핵심 의존성으로 재검토하지 않음

## 새 세션에 전달할 요청문

```text
docs/handoffs/2026-07-25-next-session.md를 읽고 Phase 2b-A부터 진행해줘.
AGENTS.md와 REGISTRY.md를 먼저 확인하고, upstream 전역 installer는 쓰지 마.
모호한 설계가 실제 저장 위치나 보안 경계를 바꾼다면 구현 전에 나에게
질문하고, 완료되면 테스트·문서·커밋을 함께 정리해줘.
```
