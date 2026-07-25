# nohdol-study 추가 도구 도입 검토

- 날짜: 2026-07-25
- 범위: local retrieval, 논문 RAG, agent memory/graph, Obsidian skill·API,
  spaced repetition, diagram
- 판정 기준: nohdol-study의 실제 학습 효용, Markdown source-of-truth 보존,
  근거 추적, 설치처 이식성, 외부 전송, 운영 복잡도

## 결론

| 후보 | 판정 | 다음 행동 |
|---|---|---|
| basic-memory | Phase 2c 제한 파일럿 채택 | 지정 corpus를 read/search 중심으로 index하고 원본 hash·검색 품질 비교 |
| PaperQA2 | 조건부 채택 | 사용자가 지정한 논문 묶음의 심층 질의에서 provider·전송 승인 후 사용 |
| kepano/obsidian-skills | 4종 채택 | markdown, bases, json-canvas, obsidian-cli를 exact pin으로 project-local 도입 |
| spaced-repetition | Phase 3 채택 | recall Markdown 포맷을 플러그인 호환으로 설계 |
| D2·Mermaid·JSON Canvas·matplotlib | 채택 | `diagram` skill의 용도별 router로 구현 |
| Graphiti | 보류 | temporal fact/history 질의가 반복 요구가 되면 재검토 |
| Mem0 | 보류 | 개인화 agent memory가 명시 요구가 되면 재검토 |
| Cognee | 보류 | 다중 데이터 memory pipeline과 agent trace 기억이 필요해지면 재검토 |
| Kuzu | 신규 도입 제외 | 아카이브된 DB 대신 유지보수되는 후보만 검토 |
| Obsidian Local REST API/MCP | 기본 경로 보류 | 공식 CLI로 불가능한 live-app/원격 client 요구가 있을 때만 |

## 1. basic-memory — 작은 제한 파일럿

Basic Memory는 Markdown 파일을 원본으로 유지하고 SQLite를 파생 index로
사용한다. CLI에서 검색·노트 조회를 제공하고 watcher로 파일 변경을
동기화할 수 있다. 이 구조는 nohdol-study의 “Markdown 원본, DB 파생물”
원칙과 맞는다.

이전의 “curated note 100개 이후” 조건에는 도구가 유용해지는 정확한
근거가 없다. 노트 수 대신 다음의 작은 실험으로 판단한다.

1. 사용자가 지정한 vault 하위 경로만 대상으로 한다.
2. 실행 전후 Markdown path와 SHA-256 집합을 비교한다.
3. 파일럿에서는 `bm format`, 자동 write, reset 같은 원본 변경 기능을
   wrapper allowlist 밖에 둔다.
4. 미리 만든 사실·관계·부정 질문으로 현재 `knowledge-graph`, Understand
   Anything, basic-memory의 precision, source 추적, latency, noise를
   비교한다.
5. 결과가 낫지 않으면 SQLite index를 지우는 것으로 완전히 철회할 수 있어야
   한다.

Basic Memory는 AGPL-3.0이므로 upstream 코드를 이 저장소에 복사·수정해
배포하지 않고 별도 설치한 도구로 호출한다.

근거:

- [Technical information](https://docs.basicmemory.com/reference/technical-information)
- [CLI reference](https://docs.basicmemory.com/reference/cli-reference/)
- [Local CLI basics](https://docs.basicmemory.com/local/cli-basics)
- [GitHub repository](https://github.com/basicmachines-co/basic-memory)

## 2. PaperQA2 — 논문 심층 질의용

PaperQA2는 PDF와 text corpus에서 답을 구성하고 citation을 붙이는 논문 RAG
도구다. 일상적인 한 편 ingest는 현재 `paper-search`와 `note-writer`로
충분하지만, 여러 논문의 방법·결과·한계를 반복 비교할 때는 보완 가치가
있다.

기본 설정은 외부 model·embedding provider를 사용할 수 있다. 실행 전 corpus,
provider, 외부 전송 여부를 보여주고 승인받는다. 답의 citation은 해당 PDF
원문에서 다시 확인하며 PaperQA 답변 자체를 verified note의 근거로 쓰지
않는다.

근거:

- [FutureHouse PaperQA2](https://github.com/Future-House/paper-qa)

## 3. Obsidian skills와 API

`kepano/obsidian-skills`의 다음 4개는 파일 기반 학습에 직접 도움이 되므로
채택한다.

- `obsidian-markdown`: Obsidian wikilink, embed, callout, properties 작성
- `obsidian-bases`: `.base` YAML view·filter·formula 작성
- `json-canvas`: 공개 JSON Canvas 1.0 형식의 지식 맵 작성
- `obsidian-cli`: 공식 CLI를 통한 검색·파일·property·command 작업

upstream `defuddle` skill은 현재 nohdol-study의 immutable capture,
evidence, authenticated-source 금지 경계보다 단순하므로 교체하지 않는다.
4개 skill은 사용자 전역 위치가 아니라 exact commit의 project-local
source로 설치한다.

공식 Obsidian CLI는 Obsidian 1.12 installer와 실행 중인 앱이 필요하다.
2026-07-25 이 Mac의 `/Applications/Obsidian.app`은 1.10.6이므로 현재는
CLI만 `unavailable`이며, Markdown/Bases/Canvas skill에는 영향이 없다.

Local REST API 플러그인은 API key와 self-signed HTTPS 또는 loopback HTTP,
실행 중인 Obsidian을 요구하고 파일 변경·command 실행까지 노출한다. 공식
CLI가 충족하지 못하는 remote client 또는 live app metadata 요구가 없으므로
기본 경로에는 넣지 않는다.

근거:

- [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills)
- [Obsidian CLI help](https://obsidian.md/help/cli)
- [Obsidian Bases syntax](https://obsidian.md/help/bases/syntax)
- [JSON Canvas 1.0](https://jsoncanvas.org/spec/1.0/)
- [Obsidian Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api)

## 4. Graphiti·Mem0·Cognee·Kuzu

세 memory/graph 도구는 기능상 사용할 수 없어서가 아니라 현재 요구보다
운영 계층이 크기 때문에 보류한다.

- Graphiti는 temporal knowledge graph에 적합하지만 Neo4j, FalkorDB 또는
  Neptune 같은 graph backend와 LLM provider가 필요하다.
- Mem0 open source는 LLM, embedder, vector store를 조합하는 agent memory다.
- Cognee는 vector, graph, relational 계층과 model 설정을 묶은 memory
  pipeline이며 agent interaction까지 capture할 수 있다.

현재 nohdol-study의 핵심은 사용자가 소유한 Markdown과 주장별 근거다.
상시 agent memory가 추가되면 “왜 기억됐는가”와 삭제·동기화·외부 전송
정책까지 별도 운영해야 한다. temporal fact history, 개인화 agent memory,
다중 데이터/trace memory가 실제 반복 요구가 될 때 각각 재검토한다.

Kuzu는 공식 저장소가 2025-10 아카이브되어 신규 DB 선택지에서 제외한다.
이는 파일 형식이나 기존 데이터 사용 금지가 아니라 새 핵심 의존성으로
선택하지 않는다는 뜻이다.

근거:

- [Graphiti](https://github.com/getzep/graphiti)
- [Mem0 open-source overview](https://docs.mem0.ai/open-source/overview)
- [Cognee installation](https://docs.cognee.ai/getting-started/installation)
- [Kuzu repository](https://github.com/kuzudb/kuzu)

## 5. 복습과 다이어그램

`obsidian-spaced-repetition`은 질문/답, cloze, note review를 Markdown 안에
보존할 수 있어 Phase 3 `recall` 출력 대상으로 적합하다. plugin 설치는
Obsidian 사용 설치처의 선택 사항이며 복습 schedule은 하네스 Git에 넣지
않는다.

다이어그램은 하나의 도구로 통일하지 않는다.

- Mermaid: Obsidian 안에서 바로 렌더되는 기본 text diagram
- D2: 큰 architecture를 CLI에서 SVG로 렌더
- JSON Canvas: vault note를 연결하는 지식 맵
- matplotlib: 좌표·궤적·3D처럼 수치 정확성이 필요한 SVG

D2는 브라우저 없이 text를 SVG로 만들 수 있지만 현재 이 Mac에는 설치돼
있지 않다. `diagram` skill을 구현하면서 optional dependency로 설치한다.

근거:

- [Obsidian Spaced Repetition](https://github.com/st3v3nmw/obsidian-spaced-repetition)
- [D2 installation](https://d2lang.com/tour/install/)
- [D2 FAQ](https://d2lang.com/tour/faq/)
- [Mermaid](https://github.com/mermaid-js/mermaid)
