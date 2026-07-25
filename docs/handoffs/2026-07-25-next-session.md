# 다음 세션 작업 인계 — Phase 2b 이후

- 작성일: 2026-07-25
- 기준 브랜치: `main`
- 현재 상태: Phase 1·2·2b 전체와 Phase 3 구현 완료. 남은 것은 Phase 2c
  파일럿과, 아래 "남은 콘텐츠 작업"뿐이다.
- **계획된 구현은 모두 끝났다.** Phase 2c까지 포함해 남은 미결은 판정이 아니라
  사용자 결정 대기다 — basic-memory는 색인이 노트를 수정한다는 대가를 받아들일지,
  PaperQA2는 논문 corpus와 provider를 갖출지. 상세는
  [2c 현황](../reviews/2026-07-25-phase2c-pilot-status.md).
- 다음 시작점: 정해진 다음 구현은 없다. 실제로 자료를 쌓아 쓰면서 부족한 곳을
  찾는 단계이고, 아래 "남은 콘텐츠 작업"이 유일하게 대기 중인 실제 작업이다.
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
.agents/skills/study-install/scripts/bootstrap_test.sh
.agents/skills/study-install/scripts/install-phase2-tools_test.sh
python3 .agents/skills/metaskill/scripts/verify_harness.py
```

4. `study-install --check`에 해당하는 기존 스크립트로 로컬 capability를 다시
   관찰한다. 추적 문서에 설치 경로·계정·버전 상태를 하드코딩하지 않고
   `REGISTRY.md`만 갱신한다.
5. 한 세션에서 아래 작업 묶음 하나를 완료하는 것을 기본으로 한다.

## 완료됨 — Phase 2b-A (2026-07-25)

`.tools/`(미추적, `PINS.md`만 추적)에 upstream 정확 commit을 받아 tree hash가
일치할 때만 배치하는 설치기를 구현했다. `install-phase2b-tools.sh --check`는
네트워크 없이 관측만 하고, `--install`만 내려받는다. hash 불일치·미충족
runtime·파싱 불가 pin·`python3` 부재·기존 체크아웃 불일치는 fail-closed이고,
이동한 tag도 막되 API 미도달 시에는 보고 후 진행한다(무결성 관문은 tree
hash다). 테스트는 curl 스텁으로 다운로드 경로까지 오프라인 커버한다.

`high 취약점 fail-closed`는 이 단계 범위 밖이다 — 여기서는 의존성을 아예
설치하지 않는다. 2b-B에서도 설치하지 않기로 했으므로(런타임 게이트를 실행
시점으로 옮김) 감사 게이트는 의존성 설치가 실제로 승인되는 시점에 구현한다.

설치기는 전역 스킬 디렉터리와 vault 경로를 아예 참조하지 않는다. 테스트의
불변 단언은 그 사실을 지키는 회귀 카나리이지, 위반을 능동적으로 탐지하는
장치가 아니다.

실측 상태: `obsidian-skills`는 배치 완료, `understand-anything`은 pnpm 10+
부재로 미배치(설계된 fail-closed). 아래 원래 계획은 기록으로 남긴다.

### 원래 계획 — Phase 2b-A

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

### 완료됨 — Phase 2b-B (2026-07-25)

9개 adapter를 project skill로 노출했다. 공통 경계는
`.agents/skills/understand/references/adapter-contract.md` 하나가 운반한다.

조사에서 드러난 사실 하나가 2b-A의 설계를 고치게 했다: 한 pin 안에 런타임이
세 계층으로 갈려 있다. `understand-knowledge`의 파서는 Python 표준
라이브러리만 쓰고, 그래프 소비형 5종은 기존 그래프만 있으면 되며,
`understand`·`understand-figma`·`understand-dashboard`만 빌드된 의존성을
요구한다. 소스 배치는 아무것도 실행하지 않으므로 런타임 게이트를 설치
시점에서 실행 시점(adapter)으로 옮겼다. 그 결과 두 pin 모두 배치됐고,
의존성 없이 도는 `understand-knowledge` 경로가 열렸다.

미해결로 남은 것: `understand-knowledge`는 상류 파서를 그대로 부르므로
출력이 아직 이 하네스 스키마가 아니다(2b-C 대상). 현재 vault는 wiki 노트가
1개라 상류 파서의 입력 조건(`index.md` + Markdown 여러 개)에 미달한다.

### 원래 계획 — Phase 2b-B

`understand`, `understand-chat`, `understand-dashboard`, `understand-diff`,
`understand-domain`, `understand-explain`, `understand-figma`,
`understand-knowledge`, `understand-onboard`를 모두 project skill로 노출한다.

- chat·domain·explain·onboard·diff는 관련 source file을 다시 읽은 뒤에만
  사실 답변을 완료한다.
- dashboard는 사용자 요청 시에만 loopback으로 실행한다.
- Figma는 token·file key·`api.figma.com` 전송을 실행별 승인받는다.
- 코드 프로젝트 `.ua/`는 target·ignore·write 범위를 확인한다.
- vault 분석은 `_workspace/understand-anything/`로 리디렉션한다.

### 완료됨 — Phase 2b-C (2026-07-25)

결정적 계층을 article·topic·source 타입으로 확장했다. topic은 `index.md`의
분류에서(위키링크 없이 하위에 링크를 가진 최상위 항목만 — 최근 갱신 목록은
분류로 오해되지 않는다), source는 노트 frontmatter의 `sources`에서 나오며
`raw/` 경로는 실재 여부까지 기록한다. 그 결과 노트가 1개인 현재 vault에서도
1 article·1 topic·5 source·6 edge가 나온다(이전엔 고아 노드 1개뿐).

추론 계층은 `--semantic`으로만 들어온다. record마다 `source_path`·
`evidence_anchor`·`extractor`·`confidence`·`verification`이 필수이고, 앵커를
인용 노트 안에서 실제로 해석해 실패하면 **버린다**. 노트 본문은 그래프에
담기지 않고 근거는 앵커와 excerpt hash로만 남으므로, 노트 안의 지시문 같은
문장이 그래프를 타고 흐르지 않는다.

### 원래 계획 — Phase 2b-C

- 현재 결정적 wikilink graph를 article/entity/topic/claim/source schema로
  확장한다.
- `wiki/` 문서가 1개여도 유효한 graph를 만든다.
- 최종 graph에서 노트 본문 사본을 제거한다.
- semantic enrichment는 opt-in으로 분리한다.
- inferred claim·edge에 source path, evidence anchor, extractor, confidence,
  verification을 강제한다.
- prompt-like note fixture와 vault 원본 hash 불변 테스트를 추가한다.

### 완료됨 — Phase 2b-D (2026-07-25)

`obsidian` 스킬 하나가 `obsidian-markdown`·`obsidian-bases`·`json-canvas`·
`obsidian-cli` 4개 mode를 내부 라우팅한다(2b-B와 같은 방침). 앞의 셋은
Obsidian 없이 동작하고 CLI만 앱 실행을 요구해 없으면 `unavailable`이다.
상류 `defuddle`는 채택하지 않았고, 라우팅 테스트가 그 결정을 고정한다.

`scripts/validate.py`가 만든 파일을 검증한다 — 캔버스는 JSON Canvas 1.0(노드
타입·좌표·id 중복·엣지가 실제 노드를 가리키는지), Markdown은 미닫힘·빈
위키링크와 미지의 콜아웃 타입, `.base`는 로드 실패를 부르는 구조 오류.
콜아웃 목록은 pin된 참조에서 읽어 상류와 동기화된다. 각 검사는 뮤테이션으로
유효성을 확인했고, 실제 vault 파일 4개에도 통과한다.

한계로 남긴 것: 무의존 원칙상 `.base`는 YAML 검증이 아니라 구조 사전
점검이다. 스킬 문서와 한글 안내가 이를 "명백히 깨지지는 않았다"로 보고하라고
명시한다.

### 원래 계획 — Phase 2b-D

`obsidian-markdown`, `obsidian-bases`, `json-canvas`, `obsidian-cli`를
project-local skill로 제공한다. 기존 nohdol-study `defuddle`는 유지한다.

- Markdown/Bases/Canvas는 Obsidian 앱 없이 생성·검증 가능해야 한다.
- CLI는 공식 요구 조건이 충족된 설치처에서만 available이다.
- `.base`와 `.canvas` fixture, wikilink·embed·callout 회귀 테스트를 둔다.

### 완료됨 — Phase 2b-E (2026-07-25)

재감사 결과 **게이트가 차단 판정**이라 CLI 설치·인증·전송을 열지 않았다.
코드로 직접 확인한 사실: 최신 안정 릴리스는 `v0.7.3`이고 그 트리에
`_redirect_guard.py`가 없으며(HTTP 404) `downloads.py`가 hop 재검증 없이
`follow_redirects=True`를 쓴다. 수정은 `v0.8.0` 프리릴리스에만 있다.

구현한 것은 판정을 결정적으로 재현하는 `bridge-gate.sh`(릴리스 메타데이터만
읽고 설치·인증·전송 없음, 프리릴리스 제외, API 미도달 시 fail-closed)와,
게이트와 무관하게 **수동 업로드에도 당장 쓸모 있는** `verify-packet.sh`다.
후자는 packet을 자기 manifest와 다시 대조한다 — 해시 재계산, 심링크는 따라
읽지 않고 거부, manifest에 없는 파일 거부, `unverified` 노트 거부. 규약 밖
형제 디렉터리(`upload/` 같은)는 실패가 아니라 경고로 드러낸다.


### 원래 계획 — Phase 2b-E

현재 안정 릴리스가 redirect 수정과 안전한 exact dependency set을
충족하는지 다시 감사한 후 진행한다. 충족하지 않으면 installer와 wrapper
테스트만 구현하고 실제 인증·전송은 계속 차단한다.

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

### 완료됨 — Phase 3 (2026-07-25)

네 스킬 모두 구현했다. 판정 가능한 부분은 전부 스크립트로 옮겨 규칙이
말로만 남지 않게 했다.

- `diagram` — Mermaid 기본, `check.py`가 노드를 세어 약 15개 초과면 D2→SVG
  승급을 권고한다(승급 기준이 감이 아니라 계수). 미지의 Mermaid 타입·불균형
  괄호·없는 임베드 에셋·빈 SVG도 잡는다. Mermaid 파서는 JS라 **사전 점검일
  뿐**이며 렌더링 확인은 사람이 한다.
- `study-session` — 스크립트 없음. 한 질문씩, 유창한 재진술을 이해로 인정하지
  않기, 채점 못 할 질문 금지, 사용자가 언제든 멈출 수 있음.
- `vault-gardening` — `garden.py`가 5개 절로 보고하고 **아무것도 고치지
  않는다**. 큐레이션 계층만 훑는다(구현 중 실측: 지식 루트에 레거시
  디렉터리가 많아 전체 순회는 클라우드에서 멈춘다).
- `recall` — 카드마다 `<!-- from: 노트.md#앵커 -->`가 필수이고, `cards.py`가
  지식 그래프와 **같은 앵커 규칙**(importlib로 로드해 드리프트 방지)으로
  해석해 실패하면 거부한다.

각 검사는 뮤테이션으로 유효성을 확인했다.

## 완료됨 — 콘텐츠 작업 (2026-07-25)

`피지컬 AI - 12살을 위한 안내서`에 그림 두 개를 넣어 완성했다. 승인된 이미지
생성 경로가 없어 생성 이미지 대신 **Mermaid 다이어그램**을 썼다 — 감지–판단–
행동–피드백 순환(flowchart)과 종이 로봇 실험의 세 역할(sequenceDiagram).

이 선택이 오히려 요구사항에 맞았다. 다이어그램은 그 구조 자체를 그리므로
본문 설명과 모순될 여지가 없고, Obsidian이 바로 렌더링하며, 소스가 노트 안에
남아 고칠 수 있고, 외부 서비스도 생성물 출처 문제도 없다.

「그림에 대하여」 콜아웃으로 **그림이 근거가 아니라 본문 요약임**을 명시했다.
`diagram`·`obsidian` 검사와 `vault-gardening` 모두 통과하고, index·log·hot도
갱신했다.

생성 이미지(예: 청소 로봇 장면 삽화)가 필요하면 사용자가 경로를 승인해야
한다. 그 경우에도 장면 설명만 전송하고, provenance와 생성일을 노트에 기록한다.

## 보류 중인 후보와 재검토 trigger

- Graphiti: temporal fact/history 질의가 반복될 때
- Mem0: 개인화 agent memory가 명시 요구가 될 때
- Cognee: 다중 데이터·agent trace memory가 필요할 때
- Obsidian REST/MCP: 공식 CLI로 해결할 수 없는 live-app/remote-client
  요구가 생길 때
- Kuzu: 아카이브 상태이므로 신규 핵심 의존성으로 재검토하지 않음

## 새 세션에 전달할 요청문

```text
docs/handoffs/2026-07-25-next-session.md를 읽고 Phase 2b-D부터 진행해줘.
AGENTS.md와 REGISTRY.md를 먼저 확인하고, upstream 전역 installer는 쓰지 마.
모호한 설계가 실제 저장 위치나 보안 경계를 바꾼다면 구현 전에 나에게
질문하고, 완료되면 테스트·문서·커밋을 함께 정리해줘.
```
