# ADR 003 — Understand Anything 전체 스킬과 선택적 학습 연동을 project-local로 채택

- 날짜: 2026-07-25
- 상태: 활성
- 대상: Understand Anything, kepano/obsidian-skills, notebooklm-py,
  지식 그래프, 소비자 NotebookLM

## 맥락

nohdol-study는 코드, 비즈니스 도메인, 변경 이력, 설계, 일반 지식 문서를
모두 공부하는 프로젝트다. Understand Anything의 코드·도메인·설명·질의·
온보딩·diff·dashboard·Figma·knowledge 기능은 각각 이 학습 과정에 쓸
수 있다. 다른 프로젝트에서 내려진 도입 판정은 이 결정의 근거가 아니다.

다만 upstream installer는 main branch를 갱신하고 전역 skill 이름을
심링크하며, v2.9.0 전체 monorepo lock에는 감사 시 high 취약점이 남아 있다.
따라서 “스킬을 모두 채택한다”와 “upstream installer를 그대로 실행한다”를
구분해야 한다.

개인용 NotebookLM은 공식 consumer API가 없지만 `notebooklm-py`는 비공식
내부 API를 이용한 CLI를 제공한다. 사용자는 웹 UI를 통한 반복 작업을 원하지
않으며, 기존 `notebooklm-export`는 전송 범위와 버전을 고정한 packet을 이미
만든다.

## 결정

### Understand Anything

- upstream의 9개 스킬 `understand`, `understand-chat`,
  `understand-dashboard`, `understand-diff`, `understand-domain`,
  `understand-explain`, `understand-figma`, `understand-knowledge`,
  `understand-onboard`를 모두 채택한다.
- exact release/commit을 미추적 project-local 도구 디렉터리에 두고 이
  저장소의 adapter skill로 노출한다. upstream의 main-pulling installer와
  `~/.agents/skills` 전역 심링크는 사용하지 않는다.
- Node 22+·pnpm 10+ 상태를 검사하고 필요한 package만 exact lock으로
  설치·감사한다. 해결되지 않은 high 취약점은 자동 설치를 차단한다.
- 코드 저장소의 `.ua/`는 실행 전 ignore/write 범위를 확인한 뒤 파생물로
  허용한다. vault 분석 결과는
  `_workspace/understand-anything/`로 리디렉션한다. Markdown과 source
  code가 원본이고 그래프는 삭제 가능한 파생물이다.
- dashboard는 자동으로 열지 않으며 사용자가 요청할 때만 localhost에서
  실행한다. CLI·JSON 탐색은 독립적으로 가능해야 한다.
- Figma는 별도 opt-in이다. token을 저장소·vault에 저장하지 않고
  `api.figma.com`으로 전달할 file key와 목적을 사용자가 승인한 때만
  실행한다.
- chat·explain·domain·onboard·diff가 만든 설명은 graph-derived navigation
  자료다. 확정 답변은 관련 source file을 다시 열어 검증한다.
- upstream v2.9.0의 결정적 parser, typed knowledge schema, 보수적
  article-analyzer를 지식 모드 adapter의 기준으로 사용한다.
- explicit 링크·frontmatter·backlink는 결정적 층, entity·claim·암묵 edge는
  모델 추론 층으로 분리한다.
- 모델 추론 층의 모든 항목은 source path, evidence anchor, extractor,
  confidence, verification 상태를 가져야 한다. `verified` 승격은 원문 대조
  뒤에만 가능하다.
- 최종 JSON에는 노트 전문이나 parser가 잘라 넣은 본문 사본을 보존하지
  않는다.

### Obsidian skills

- `kepano/obsidian-skills`의 `obsidian-markdown`, `obsidian-bases`,
  `json-canvas`, `obsidian-cli`를 exact commit으로 project-local 도입한다.
- upstream `defuddle` skill은 현재 nohdol-study의 불변 capture·evidence
  규칙보다 좁으므로 중복 설치하지 않는다.
- 공식 Obsidian CLI는 Obsidian 1.12.7+ 설치본과 실행 중인 앱이 있을 때만
  available로 기록한다. Obsidian이 없는 설치처에서는 나머지 파일 형식
  skill이 계속 동작한다.

### NotebookLM

- `notebooklm-export` packet 뒤에 붙는 선택적 CLI bridge로
  `notebooklm-py`를 채택한다. vault 전체 동기화는 하지 않는다.
- 안정 릴리스가 보안 수정 commit `0a6e28a0522b3542695e6666054e88060ef3de48`
  이후 코드를 포함하는지 검증한다. 그렇지 않으면 자동 설치하지 않는다.
  정확 commit 설치를 허용하려면 별도 lock·hash·회귀 검증을 먼저 만든다.
- 설치는 CLI에 필요한 최소 extra만 사용한다. MCP/server, headless
  master-token, browser impersonation transport는 기본 금지한다.
- 브라우저 cookie import는 사용자가 정확한 로컬 브라우저 profile과
  NotebookLM 전송을 명시 승인한 한 번의 인증 작업에서만 사용한다.
  `study-install`이 자동 실행하지 않는다.
- `storage_state.json`은 bearer credential이다. 저장소·vault 밖의 전용
  profile에 두고 POSIX에서 파일 `0600`, 디렉터리 `0700`을 확인한다.
- upload는 `_workspace/notebooklm/`의 export packet만 대상으로 한다.
  `vault/` 심링크 직접 업로드와 `--follow-symlinks`, `--allow-internal`은
  금지한다.
- notebook 생성, source upload, generate, download는 실행 전 대상·전송
  범위·출력 경로를 보여주고 승인받는다. public share, 사용자 초대, delete,
  logout은 별도 중요 작업으로 취급한다.
- NotebookLM 답변·퀴즈·그림은 파생 학습 자료이며 지식 근거가 아니다.

## 채택하지 않은 설치 방식과 기본 경로

- **Understand Anything upstream installer 그대로 실행**: 스킬 내용이
  아니라 main 자동 갱신·전역 덮어쓰기·재현되지 않는 의존성 범위를
  채택하지 않는다.
- **dashboard 자동 실행**: 스킬은 채택하지만 브라우저를 자동으로 열지는
  않는다.
- **Figma 상시 연결**: 스킬은 채택하지만 token과 외부 API 전송은 실행별
  opt-in이다.
- **NotebookLM 브라우저 UI 자동화**: 로그인 안정성·재현성·사용자 선호에
  맞지 않는다.
- **NotebookLM master token**: upstream도 full-account,
  infostealer-grade credential로 경고한다. 개인 기본 설치에 과도하다.
- **NotebookLM MCP/server**: 초기 CLI 사용에 불필요한 네트워크·의존성
  표면을 늘린다.

## 결과

학습 skill은 모두 사용할 수 있게 하되 설치와 실행 권한은 좁고 재현
가능하게 유지한다. 보안 게이트가 통과하지 않거나 계정·앱 연결이 없으면
기존 결정적 graph, Markdown 파일 skill, 수동 NotebookLM export는 계속
독립적으로 동작한다.
