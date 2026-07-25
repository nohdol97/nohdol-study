# Phase 2c 파일럿 — 전제 조건 실측과 현재 판정

- 날짜: 2026-07-25
- 대상: basic-memory(basicmachines-co), PaperQA2(Future-House)
- 관련: [ADR 003](../adr/003-cli-learning-integrations.md),
  [추가 도구 검토](2026-07-25-additional-tools-review.md),
  [작업 인계](../handoffs/2026-07-25-next-session.md)
- 판정: **PaperQA2 = 실행 불가(전제 미충족)**, **basic-memory = 파일럿 완료, 읽기 전용 조건 불충족으로 미채택**

## 왜 이 문서가 있나

Phase 2c는 두 도구를 "사용자가 지정한 corpus·provider가 있을 때만" 돌리기로
한 제한 파일럿이다. 진행 요청을 받고 전제를 실측한 결과 지금은 둘 다 돌릴 수
없어서, 무엇이 없어서 못 도는지와 무엇을 미리 만들어 뒀는지를 남긴다.

## 실측 (2026-07-25)

| 항목 | 관측값 |
|---|---|
| `basic-memory` CLI | 미설치 (`uv`는 있어 설치는 가능) |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` | 셋 다 미설정 |
| `vault/wiki` (큐레이션 계층) | 노트 1개 |
| `vault/raw/papers` | PDF 1개 |
| 지식 루트의 레거시 Markdown | `GeekNews` 169, `공부` 30, `AX` 18, `도서` 9, `경제` 2 |
| `~/study` (하네스 밖 레거시) | 881개 |

## PaperQA2 — 실행 불가

두 겹으로 막힌다.

1. **provider 부재.** PaperQA2는 LLM과 임베딩 provider를 요구하는데 키가 하나도
   없다. 키가 생기더라도 논문 본문이 외부 모델로 나가므로 AGENTS 5절에 따라
   실행별 명시 승인이 먼저다.
2. **corpus 부재.** 보존된 논문이 1편이라 "심층 질의" 비교가 성립하지 않는다.

따라서 설치하지 않았고, 설치 절차도 만들지 않았다. 만들면 돌릴 수 없는 도구의
사용법을 검증 없이 적어 두는 셈이다.

재검토 trigger: 사용자가 논문 corpus를 모으고 provider를 지정하며 외부 전송을
승인할 때.

## basic-memory — 파일럿 실행 결과 (미채택)

사용자가 corpus로 `vault/공부`를 지정해 실행했다. **원본이 아니라 scratch
사본에서 돌렸고**, 그 판단이 결과를 갈랐다(아래 B2).

### 실행 조건

원본 `vault/공부`는 md 30개를 포함해 총 194개 파일이고, md 중 frontmatter는
4개, 위키링크는 4개뿐이다. 즉 이 하네스의 노트 계약을 따르지 않은 레거시
corpus다. 파일럿 후 원본을 재확인한 결과 `permalink` 삽입 0건, frontmatter
여전히 4개로 **완전히 무오염**이다.

### B1. 설치 이식성 — 3회 시도

`uv tool install basic-memory`가 만든 venv의 Python 3.12.4가
`sqlite3.enable_load_extension`을 지원하지 않아 프로젝트 등록조차 실패했다
(`'sqlite3.Connection' object has no attribute 'enable_load_extension'`).
Python 3.11은 버전 요구를 못 맞추고(0.14.0b1 프리릴리스만 해당),
`--python /opt/homebrew/bin/python3`(3.14.6)을 명시해 재설치한 뒤에야 동작했다.
설치처의 Python 빌드에 따라 갈리는 의존이며, 기준선은 표준 라이브러리만 쓴다.

### B2. 색인이 노트를 수정한다 — 결정적 사유

`reindex`(103초, 190 entity)가 **마크다운 30개를 전부 수정**했다. 각 파일 앞에
frontmatter를 새로 써넣는다:

```yaml
---
title: 명령어
type: note
permalink: study-pilot/docker/myeongryeongeo
---
```

한글 제목이 로마자 permalink로 변환된다. 검색은 색인을 전제하고 색인은 쓰기를
수반하므로, **검색을 쓰면서 원본을 안 건드리는 모드가 없다.** 이는 이 파일럿의
전제("자동 write 금지, 원본 hash 확인")를 구조적으로 충족할 수 없다는 뜻이다.

원본에 바로 돌렸다면 Google Drive의 개인 노트 30개가 수정됐을 것이다.

### B3. 외부 전송은 없다 — 확인

임베딩은 로컬 `fastembed`/`bge-small-en-v1.5`이고 `cloud_api_key: None`이다.
AGENTS 5절 위반은 없었다. 다만 **영어 모델을 한국어 corpus에 쓴다**는 점은
검색 품질의 한계로 남는다.

### B4. 검색은 실제로 쓸모 있다

사전에 작성한 질문으로 관련 문서를 찾아낸다: `GitOps` →
`04-ci-cd-gitops`(score 0.845), `MSA` → `msa-communication`, `FastAPI` →
`fast-api`. 폴더가 다른 동명 파일도 namespace가 붙은 permalink로 구분한다.

버그 하나: 응답의 `total` 필드가 `results`에 10건이 있어도 `0`이다. 수치를
그대로 믿으면 안 된다.

### B5. 기준선은 이 corpus에서 아예 실패한다

결정적 그래프는 `Docker/명령어.md`와 `Kubernetes/명령어.md`의 **중복 제목으로
하드 실패**해 그래프를 만들지 못한다. 하나를 지우고 재실행하면 29개 노트에서
엣지 6개, **깨진 링크 52개, 고아 23개**가 나온다(0.19초).

이는 기준선의 결함이 아니라 **적용 범위**다. 위키링크와 frontmatter로 큐레이션된
`wiki/`를 위해 만들어졌고, 그 규약을 따르지 않는 레거시 노트에서는 구조를 찾을
것이 없다. 반대로 basic-memory는 그런 corpus에서 검색을 제공한다.

### 판정

**둘은 경쟁 관계가 아니다.** 기준선은 큐레이션된 노트의 구조를 결정적으로
측정하고, basic-memory는 큐레이션되지 않은 더미에서 검색을 제공한다.

지금 채택하지 않는 이유는 검색 품질이 아니라 **소유권**이다. basic-memory는
노트의 frontmatter를 자기 것으로 삼는다. 그 대가를 치를지는 사용자의 결정이지
숨길 사항이 아니다 — 치르기로 한다면 레거시 노트 검색 도구로 유효하다.

### 재검토 trigger

- 사용자가 "레거시 노트를 검색하고 싶고 frontmatter가 바뀌어도 좋다"고 결정할 때.
  그 경우 대상은 `wiki/`가 아니라 레거시 디렉터리로 한정한다.
- basic-memory가 원본을 수정하지 않는 읽기 전용 색인 모드를 제공할 때.

## 미리 만든 것 — 파일럿 하네스

corpus가 정해지면 바로 돌릴 수 있도록, corpus와 무관하게 유효한 부분을 먼저
구현했다: `.agents/skills/knowledge-graph/scripts/pilot.py`.

- 실행 전후로 corpus의 모든 Markdown을 SHA-256으로 스냅샷하고, **하나라도
  추가·삭제·수정되면 후보를 실격**시킨다. 후보가 무엇을 보고했든 무관하다.
- `write`·`format`·`reset`·`sync` 같은 세그먼트를 가진 명령은 **실행 전에**
  거부한다. 하이픈 단위로 보므로 `write-note`는 잡히고 `format` 안의 `rm`에는
  오탐하지 않는다.
- 결정적 기준선(노드·엣지·누락·고아·런타임)을 측정해 같은 표에 놓는다.
- **후보 명령은 인자로 받는다.** 설치해서 help를 읽어보지 않은 CLI의 명령줄을
  기억으로 적지 않는다 — 이 하네스가 다른 곳에서 금지하는 바로 그 미검증
  주장이기 때문이다.

각 불변식은 뮤테이션으로 실효성을 확인했다(변경 감지·사전 차단·추가/삭제
감지·임시 산출물 정리).

## 설치 상태

`basic-memory` 0.22.1이 이 머신에 설치돼 있다(`uv tool`, Homebrew Python 3.14).
파일럿 프로젝트 등록은 해제했고 기본 프로젝트는 `main`으로 되돌렸다. 채택하지
않았으므로 하네스는 이 도구를 호출하지 않는다. 필요 없으면
`uv tool uninstall basic-memory`로 제거해도 무방하다.

## 변경 이력

| 날짜 | 변경 내용 | 사유 |
|---|---|---|
| 2026-07-25 | 전제 실측·판정 기록, 파일럿 하네스 구현 | Phase 2c 진행 요청 — 두 도구 모두 전제 미충족으로 실행 불가임을 확인하고, corpus와 무관하게 유효한 안전 장치를 먼저 구현 |
| 2026-07-25 | basic-memory 파일럿 실행·미채택 판정 | 사용자가 `vault/공부`를 corpus로 지정. scratch 사본에서 실행한 결과 색인이 마크다운 30개를 전부 수정함을 확인 — 읽기 전용 전제를 구조적으로 충족 불가. 검색 자체는 유효하고 외부 전송은 없음 |
