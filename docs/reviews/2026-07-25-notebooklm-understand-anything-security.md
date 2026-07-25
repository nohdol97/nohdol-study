# NotebookLM CLI·Understand Anything 보안 검토

- 날짜: 2026-07-25
- 검토 범위:
  - `teng-lin/notebooklm-py` 안정 릴리스 `v0.7.3`
    (`a6c54417058bd5e43e0162dd93a390308d2f99f6`)과 main
    (`45fd4258e608fbb9685496f26cfcea48810c44ee`)
  - `Egonex-AI/Understand-Anything` 안정 릴리스 `v2.9.0`
    (`f08763d11d0202a8a8f52b5dedda6d1b2e2ebac8`)과
    `/understand-knowledge`
- 판정:
  - NotebookLM: **조건부 채택, 현재 v0.7.3 자동 설치 보류**
  - Understand Anything: **9개 스킬 전체 채택, upstream 전역 installer는
    사용하지 않고 project-local 안전 어댑터 필요**

## 확인 방법

- 릴리스·commit·보안 정책·설치 문서 확인
- 인증 저장, path validation, source upload, download redirect, 공유·삭제
  확인 코드 검토
- `notebooklm-py`의 frozen lock과 현재 허용 범위 dependency를 각각
  `pip-audit`로 검사
- Understand Anything v2.9.0의 installer, 9개 skill, parser, merge,
  analyzer, dashboard·Figma 경계, lock을 검토
- upstream knowledge parser 테스트 실행: `8 passed, 1 skipped`
- 현재 vault에 upstream parser 실행: `md_count=1`이라 의도대로 실패,
  원본 변경 없음

## NotebookLM 발견 사항

### N1. 비공식 내부 API — 높음, 수용 필요

Google이 문서화하지 않은 consumer NotebookLM RPC를 사용한다. API가 예고
없이 깨지거나 비정상 사용으로 rate limit·계정 제한이 생길 수 있다. 공식
consumer API나 Google의 보안 보증으로 표현하면 안 된다.

### N2. 인증 파일은 bearer credential — 높음, 완화 가능

`storage_state.json`을 가진 사람은 NotebookLM 범위에서 사용자를 가장할 수
있다. 코드는 POSIX profile 디렉터리 `0700`, credential 파일 `0600`, atomic
write를 구현한다. 그러나 파일 암호화는 아니므로 저장소·vault·Google Drive
밖의 전용 profile에 두어야 한다.

browser-cookie import는 Chrome/Firefox의 기존 Google cookie 저장소를 읽는다.
macOS Chrome은 Keychain 접근을 요구할 수 있다. 자동 설치·자동 refresh로
실행하지 않고 사용자가 정확한 browser profile을 승인한 한 번의 인증
작업으로 제한한다.

master-token 구현은 upstream 코드도 “full-account, durable,
infostealer-grade”라고 경고한다. 개인 기본 경로에서는 금지한다.

### N3. v0.7.3 download redirect 방어 누락 — 높음, 설치 차단

v0.7.3은 초기 URL의 HTTPS와 Google host를 검사하지만
`follow_redirects=True` 뒤의 각 hop을 다시 검사하지 않는다. 수정 commit
`0a6e28a0522b3542695e6666054e88060ef3de48`은 main에는 있으나 검토한
v0.7.3 tag에는 없다. 공격자가 영향을 주는 Google redirect가 임의 host를
가리키면 그 응답 byte가 지정 output path에 기록될 수 있다. cookie는 domain
scoped라 비-Google host로 전송되지 않는다는 upstream 분석과 별개로,
artifact download를 쓰는 이번 요구에는 릴리스 게이트가 필요하다.

### N4. dependency 상태 — 중간

- v0.7.3 frozen lock의 `click 8.3.1`에서
  `PYSEC-2026-2132` 1건을 확인했다. 그대로 재현 설치하면 안 된다.
- v0.7.3의 허용 범위를 2026-07-25 현재 다시 해석한 browser set과 cookies
  set은 각각 `pip-audit`에서 알려진 취약점 0건이었다.
- “현재 취약점 0건”은 미래 안전을 보장하지 않는다. 실제 설치 직전에 exact
  lock을 다시 만들고 감사해야 한다.

### N5. 좋은 기본 방어 — 확인

- profile path traversal 방지와 atomic credential write
- CLI file upload의 symlink 기본 거부
- localhost·private·link-local source URL 기본 거부
- artifact download의 Google host allowlist와 main의 per-hop guard
- delete의 confirmation 및 MCP의 two-step confirmation
- download 임시 파일과 실패 시 정리

### N6. upstream skill의 자율성은 과함 — 중간

upstream skill은 notebook 생성과 source add를 확인 없이 자동 실행하도록
허용한다. nohdol-study에서는 둘 다 외부 state 변경이며, source add는 Google
전송이므로 자동 규칙을 가져오지 않는다. public sharing은 v0.7.3 CLI에서
별도 확인 없이 활성화할 수 있어 wrapper allowlist 밖에 둔다.

### N7. 안전한 사용 형태

- 기존 `notebooklm-export` packet만 upload
- vault가 symlink이므로 `vault/...`를 직접 넘기지 않음
- `--follow-symlinks`, `--allow-internal`, master-token, MCP/server,
  impersonate extra 금지
- 외부 전송과 mutation을 실행 전 승인
- 생성물은 `_workspace/`에 회수하고 독립 근거로 사용하지 않음

## Understand Anything 발견 사항

### U1. 9개 스킬 모두 nohdol-study 학습 범위에 해당 — 채택

`understand`·`chat`·`diff`·`domain`·`explain`·`onboard`는 코드와 제품
도메인을 공부하는 서로 다른 관점을 제공한다. `knowledge`는 Markdown 지식
베이스, `figma`는 설계, `dashboard`는 큰 그래프의 시각 탐색에 쓸 수 있다.
이 프로젝트는 지식 노트에만 한정되지 않으므로 9개를 모두 채택한다.

단, graph-derived 설명이 확정 근거는 아니다. chat·domain·explain·onboard·
diff의 답은 관련 source file을 다시 열어 대조해야 한다.

### U2. 전체 installer의 범위가 과함 — 높음

installer는 main branch를 clone/pull하고 `~/.agents/skills` 등에 여러
Understand Anything 스킬을 `ln -sfn`으로 연결한다. exact release pin이 없고
기존 이름 충돌을 덮을 수 있다. 문제는 스킬 범위가 아니라 설치 scope와
재현성이다. exact commit의 project-local checkout과 adapter를 사용한다.

### U3. knowledge parser 자체는 무의존·결정적 — 양호

parser와 merge는 Python 표준 라이브러리만 사용하고 shell command를
본문에서 실행하지 않는다. upstream parser 테스트도 통과했다. explicit
wikilink·backlink·category 기반은 현 기준 parser를 확장할 좋은 토대다.

### U4. 구현과 문서의 형식 지원 범위가 다름 — 중간

설계 문서는 Obsidian 등 여러 Markdown 형식 자동 탐지를 말하지만 v2.9.0의
실제 skill은 Karpathy pattern만 지원한다. `index.md`와 Markdown 3개 이상을
요구한다. 현재 nohdol-study vault는 `wiki/` 1개라 실패한다. “Obsidian
vault면 바로 작동”한다고 문서화하면 잘못된 정보다.

### U5. 본문 사본이 최종 graph에 남음 — 높음

parser는 각 article의 첫 3,000자를 `knowledgeMeta.content`에 넣고 merge가
이를 최종 graph까지 보존한다. `.ua/`가 Google Drive vault 안에 생기면
private note 일부가 불필요하게 중복·동기화된다. nohdol-study 어댑터는
출력을 `_workspace/`로 바꾸고 최종 graph에서 본문을 제거해야 한다.

### U6. 모델 추론의 근거 추적이 부족 — 높음

article-analyzer는 보수적 추출과 prompt-injection 무시를 명시하지만,
entity·claim·암묵 edge schema에는 source span, evidence anchor,
verification state가 없다. merge도 허용 type과 node 존재만 검사한다.
사용자가 중시하는 정확성을 충족하려면 근거 없는 claim을 버리고 inferred와
verified를 분리해야 한다.

### U7. dashboard·Figma·정리 삭제 경계 — 중간

skill은 완료 후 dashboard를 자동 실행하고 `.ua/intermediate`를 `rm -rf`로
정리한다. dashboard 기능 자체는 채택하되 자동 실행을 제거하고 사용자가
요청할 때만 loopback viewer를 연다. 중간물은 명시적 cleanup 또는 교체
가능한 temp directory로 관리한다.

Figma skill은 `FIGMA_TOKEN`과 `api.figma.com` 외부 호출이 필요하다. token은
저장소·vault에 저장하지 않고, 분석할 file key와 전송 목적을 실행별
승인받는다.

### U8. 전체 monorepo dependency audit — 높음, 전체 설치 차단 근거

v2.9.0 lock의 production audit에서 high 10건을 포함한 21건이 보고됐다.
여기에는 homepage/dashboard/build 계층 의존성이 섞여 있어 모든 스킬이
각 취약점에 도달한다는 뜻은 아니다. 하지만 그대로 `pnpm install`하기보다
실제 필요한 package만 exact lock으로 분리·감사해야 한다. 해결되지 않은
high 취약점이 있는 Node 경로는 자동 설치하지 않는다.

## 최종 게이트

| 항목 | 지금 허용 | 차단 조건 |
|---|---|---|
| 기존 결정적 `knowledge-graph` | 예 | 없음 |
| UA 9개 project-local adapter 개발 | 예 | main 자동 pull·전역 skill 덮어쓰기 |
| UA Node 기반 스킬 실사용 | dependency gate 뒤 | high 취약점·불일치 lock |
| UA semantic enrichment | 어댑터 이후 opt-in | evidence 없는 claim·prompt 실행 |
| UA dashboard | 명시 요청·loopback에서 | 자동 open·외부 bind |
| UA Figma | token·file 전송 승인 뒤 | token 저장·무승인 전송 |
| UA upstream installer | 아니오 | main 추적·전역 symlink |
| NotebookLM 수동 export | 예 | manifest/hash 불일치 |
| notebooklm-py 설치·실사용 | 아직 아니오 | 수정 미포함 릴리스, 취약 exact lock |
| browser-cookie 인증 | 설치 게이트 뒤 명시 승인 시 | 자동 실행, profile 불명, 권한 불량 |
| master-token/MCP/server/public share | 아니오 | 기본 경로에서 허용하지 않음 |

## 외부 근거

- NotebookLM CLI: <https://github.com/teng-lin/notebooklm-py>
- NotebookLM security policy:
  <https://github.com/teng-lin/notebooklm-py/blob/main/SECURITY.md>
- NotebookLM redirect fix:
  <https://github.com/teng-lin/notebooklm-py/pull/1532>
- Understand Anything:
  <https://github.com/Egonex-AI/Understand-Anything>
- Understand Anything v2.9.0:
  <https://github.com/Egonex-AI/Understand-Anything/releases/tag/v2.9.0>
