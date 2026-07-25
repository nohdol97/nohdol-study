# nohdol-study Phase 2b — project-local 학습 연동 스펙

- 날짜: 2026-07-25
- 상태: R1~R10·R16 구현. **R11~R15(NotebookLM bridge)는 [ADR 004](../adr/004-remove-notebooklm-export.md)로 철회** — export 스킬 자체가 제거됐다
- 관련 결정: [ADR 003](../adr/003-cli-learning-integrations.md)
- 보안 검토: [NotebookLM·Understand Anything](../reviews/2026-07-25-notebooklm-understand-anything-security.md)

## 목표

- Understand Anything의 9개 스킬을 코드·도메인·설계·지식 학습에 모두
  사용할 수 있게 하되 nohdol-study의 정확성·출력·외부 전송 경계에 맞춘다.
- Obsidian Markdown·Bases·JSON Canvas·공식 CLI skill을 project-local로
  제공한다.
- 검증된 NotebookLM export packet을 웹 UI 없이 consumer NotebookLM에
  전달하고 학습 자료를 회수할 수 있는 선택적 CLI 경로를 제공한다.
- 어느 연동도 Markdown 원본, 설치처 이식성, 외부 전송 승인 규칙을
  약화하지 않게 한다.

## 비목표

- upstream main을 자동 pull하거나 사용자 전역 skill을 덮어쓰는 설치
- dashboard 자동 실행 또는 Figma token 자동 탐색
- consumer NotebookLM의 공식 API 또는 상시 동기화라고 주장
- vault 전체 업로드
- 모델이 추론한 claim·관계를 자동으로 사실 확정
- NotebookLM public share·협업자 초대 자동화
- headless master token, MCP/server, browser impersonation transport

## R1. 외부 skill source pin

Understand Anything과 kepano/obsidian-skills는 upstream release/commit,
license, 원본 경로와 source hash를 기록한다. 미추적 project-local 도구
경로에 설치하고 nohdol-study adapter를 통해 노출한다. `curl | bash`,
upstream main 자동 pull, `~/.agents/skills` 전역 link는 사용하지 않는다.
upstream fixture를 유지하고 로컬 변경은 patch 목록과 테스트로 설명한다.

## R2. Understand Anything 전체 skill routing

다음 9개 entry point를 모두 제공한다.

| entry point | 필수 동작 |
|---|---|
| `understand` | 코드 graph·tour 생성 |
| `understand-chat` | graph 탐색 후 source 재확인 |
| `understand-dashboard` | 명시 요청 시에만 localhost viewer |
| `understand-diff` | 기준 graph에 변경 overlay 생성 |
| `understand-domain` | 코드 근거가 있는 actor·workflow·rule 분석 |
| `understand-explain` | source-first 개념·flow 설명 |
| `understand-figma` | 승인된 Figma file만 외부 API로 분석 |
| `understand-knowledge` | Markdown typed knowledge graph |
| `understand-onboard` | source 링크가 있는 학습 순서·walkthrough |

graph consumer가 답을 생성할 때 관련 source file을 직접 열지 않았다면
완료로 처리하지 않는다.

9개는 `understand` 스킬 하나가 내부 라우팅으로 제공한다(사용자 결정
2026-07-25). 요구는 entry point 제공이지 스킬 개수가 아니며, 공통 경계를
아홉 번 반복하면 서로 어긋나기 때문이다.

## R3. Node dependency gate

`study-install --check`는 Node 22+와 pnpm 10+를 관찰한다. 설치 시
실제로 필요한 package만 exact lock으로 고정하고 production dependency를
감사한다. 해결되지 않은 high 취약점이나 lock 불일치는 자동 설치를
차단한다. monorepo 전체 install은 기본 경로가 아니다.

## R4. 출력과 외부 실행 경계

- 코드 저장소 `.ua/`: 실행 전 target root, ignore 상태, 예상 산출물을
  보여주고 해당 저장소 안에서만 쓴다.
- vault: `_workspace/understand-anything/`로 리디렉션하고 vault에 `.ua/`를
  만들지 않는다.
- dashboard: 자동 open하지 않는다. 요청 시 loopback에만 bind한다.
- Figma: token을 repo·vault에 기록하지 않는다. file key와
  `api.figma.com` 전송을 실행별 승인받는다.
- intermediate cleanup: 명시적 target guard 없이 recursive delete하지
  않는다.

## R5. nohdol-study 형식 탐지

지식 루트의 `index.md`·`log.md`·`raw/`와 `wiki/**/*.md`를 인식한다.
`wiki/`가 1개 이상이면 빈 그래프가 아닌 유효한 파생 graph를 만들며,
기존 Obsidian 레거시 디렉터리는 명시적으로 범위에 넣지 않는 한 스캔하지
않는다.

## R6. 결정적 explicit graph

article, topic, source와 explicit wikilink·backlink·category·missing·orphan을
동일 입력에서 동일 바이트로 만든다. 코드 fence 안 링크, 중복 제목,
경로 alias와 한글 파일명을 회귀 테스트한다.

## R7. 파생물 격리

출력 루트는 하네스의 `_workspace/understand-anything/`로 주입한다.
vault에 `.ua/`·`.understand-anything/`을 만들지 않는다. 실행 전후 vault
Markdown의 경로와 SHA-256 집합이 동일해야 한다.

## R8. 본문 최소화

중간 분석 입력은 필요한 범위에서만 메모리 또는 미추적 임시 파일로
사용한다. 최종 graph에는 노트 본문 사본을 포함하지 않고 source path,
heading/block anchor, 짧은 evidence excerpt hash만 남긴다.

## R9. semantic enrichment

semantic 단계는 별도 opt-in이다. 노트 본문은 untrusted data로 취급하고
그 안의 명령·정책·prompt를 실행하지 않는다. 새 entity·claim·edge에는
`source_path`, `evidence_anchor`, `extractor`, `confidence`,
`verification`이 필수다. evidence가 없는 항목은 버리고, inferred와
verified를 별도 집계한다.

## R10. Obsidian skills

`obsidian-markdown`, `obsidian-bases`, `json-canvas`, `obsidian-cli`를
project-local skill로 노출한다. upstream defuddle는 설치하지 않고 기존
nohdol-study defuddle를 유지한다. Markdown/Bases/Canvas는 Obsidian 앱 없이
파일 형식 생성·검증에 사용할 수 있어야 한다. CLI는 앱 installer 1.12.7+
및 실행 중인 앱 조건을 확인하고, 충족하지 않으면 `unavailable`로 보고하되
설치 전체를 실패시키지 않는다.

## R11. NotebookLM release gate

설치기는 최신 안정 릴리스가 감사한 보안 수정과 요구 기능을 포함하는지
검사한다. 정확 버전의 browser/cookies 최소 dependency set을 `pip-audit`
하고 high 이상 취약점이 있거나 lock이 재현되지 않으면 설치하지 않는다.

## R12. NotebookLM 인증

인증은 `study-install`의 자동 단계가 아니다. 사용자가 선택한 전용 profile에
대해 한 번 실행하고, 저장 경로가 저장소·vault 밖인지와 POSIX permission을
검사한다. master-token과 auth JSON 출력·로그·복사는 금지한다.

## R13. Packet-only upload

bridge는 `notebooklm-export`가 만든 packet의 manifest와 hash를 다시
검증한다. packet 안의 명시된 파일만 upload하며 symlink와 범위 밖 path를
거부한다. 전송 전에 notebook 이름, 파일 목록, 총 크기, Google 전송 사실을
보여준다.

## R14. 외부 변경 승인

create, upload, generate, download 각각의 실행 계획을 사용자에게 보여주고
승인받는다. public share, collaborator 변경, delete, logout은 일반 학습
흐름에서 호출하지 않으며 별도 명시 요청이 있어야 한다.

## R15. 생성물 회수와 검증

quiz, flashcard, infographic, mind map, report, Q&A 결과는
`_workspace/notebooklm/<topic>/artifacts/`에 저장한다. manifest에는 notebook
ID, source IDs, artifact ID/type, 생성 시각, 사용한 source packet hash를
남긴다. vault로 들여올 때는 원 출처와 대조하고 검증 상태를 새로 부여한다.

## R16. 설치처 상태

`study-install --check`는 `notebooklm` CLI, 감사 버전, auth 파일 존재 여부와
Understand Anything 9개 adapter·Node/pnpm·Obsidian skill·공식 CLI 준비
상태를 관찰해 `REGISTRY.md`에 기록한다.
계정 유효성은 네트워크 검증을 실제 실행하지 않았다면 `unverified`로 쓴다.

## 완료 기준

- upstream knowledge parser fixture와 기존 graph 회귀가 모두 통과한다.
- Understand Anything 9개 entry point가 project-local pin을 사용하고
  사용자 전역 skill과 설정을 변경하지 않는다.
- code graph의 chat/explain/domain/onboard/diff fixture는 source를 다시
  읽은 기록 없이 사실 답변을 완료하지 않는다.
- dashboard는 명시 요청 전 열리지 않고 loopback 외 주소에 bind하지 않는다.
- Figma fixture는 token 부재·승인 부재·허용되지 않은 host에서 각각
  fail-closed 한다.
- 현재 vault의 1개 `wiki/`에서도 graph를 만들고 원본 hash가 변하지 않는다.
- 최종 graph에 `knowledgeMeta.content`나 노트 본문 사본이 없다.
- prompt-like 문장이 든 fixture에서 semantic 출력이 명령을 실행하지 않고
  evidence 없는 claim을 거부한다.
- NotebookLM installer는 취약·미수정 릴리스를 거부하고 안전한 exact
  dependency set만 허용한다.
- packet 밖 파일, symlink, hash 불일치, 미검증 note, 승인 없는 upload를
  각각 거부한다.
- 인증 파일·계정 식별자·notebook ID가 Git 추적 파일이나 vault에 남지 않는다.
- Obsidian 앱이 없어도 markdown/bases/canvas skill은 동작하고 CLI만
  unavailable로 보고한다.
- 전체 metaskill 검증과 문서 링크 검사가 통과한다.
