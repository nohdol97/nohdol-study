# nohdol-study 방향 검토 — 공부 하네스 설계 제안

- 날짜: 2026-07-25 / 상태: **Phase 1·2 구현, Phase 2b 범위 확정·미구현** (Phase 2c·3 대기)
- 목적: 코드뿐 아니라 로봇·physical AI 등 다양한 분야의 지식 축적·공부를 돕는 하네스. Obsidian 연동 + 그래프 활용, Claude Code·Codex 양쪽 동작, 심링크 기반 이식.
- 분석 대상: claude-obsidian(AgriciDaniel) · superpowers(obra) · Understand-Anything(Egonex-AI) · claude-video(bradautomates) · defuddle(kepano) · context7 + 추가 후보 리서치
- 판정 기준: 다른 저장소의 채택·기각 결론을 승계하지 않고, 이 프로젝트의
  목표인 **다양한 분야 학습·근거 검증·지식 축적**에 실제 도움이 되는지만
  평가한다.

## 1. 핵심 발견 — 두 저장소가 같은 패턴으로 수렴한다

claude-obsidian과 Understand-Anything(/understand-knowledge)은 독립적으로 **Karpathy LLM 위키 패턴**에 수렴했다:

```
raw/          # 불변 원문 (논문 PDF·트랜스크립트·클리핑 원본 — 절대 수정 금지)
wiki/         # LLM이 생성·관리하는 지식 페이지 ([[위키링크]] 마크다운)
index.md      # 마스터 인덱스 (카테고리 카탈로그)
log.md        # append-only 연대기
hot.md        # ~500토큰 핫 캐시 (세션 시작 시 로드)
```

이것이 nohdol-study 지식 저장소의 기본 형태가 되어야 한다. 근거:
- **Obsidian 네이티브**: `[[위키링크]]` + flat YAML frontmatter = Obsidian 그래프 뷰가 공짜로 따라옴.
- **도구 중립**: 파일 직접 조작(Read/Write/Grep)만으로 Claude·Codex 모두 동작 — MCP·REST API·서버 불필요.
- **그래프는 파생물**: 위키링크가 원본 그래프이고, JSON/SQLite 인덱스는
  언제든 재생성 가능한 파생물이다. **Markdown이 source of truth이고 DB는
  파생 인덱스**라는 원칙을 이 프로젝트 자체의 기준으로 둔다.

**별도 그래프 서버(Neo4j 등)는 현재 기본 의존성으로 도입하지 않는다.**
그래프 연산은 ①위키링크와 현재 결정적 parser, ②Phase 2b의 Understand
Anything typed graph를 기본 계층으로 사용한다. basic-memory의 SQLite
인덱스는 이 원칙을 깨지 않는 로컬 검색 계층이므로 작은 범위의 파일럿으로
실측한다. Kuzu는 저장소가 2025-10 아카이브되어 신규 의존성에서 제외한다.

## 2. 골격 — nohdol-study 구조

검증된 구조를 그대로 가져온다:

```
nohdol-study/
├── AGENTS.md              # 단일 원본 (영어 — 모델-read 표면, ADR 030 원칙 동일)
├── AGENTS.ko.md           # 한글 다이제스트 뷰
├── CLAUDE.md              # @AGENTS.md 임포트 + Claude 전용 앵커
├── REGISTRY.md            # 미추적 — 설치처별 (vault 경로·분야 레지스트리·프로필)
├── .agents/               # 단일 원본: skills/ hooks/ (+ 필요 시 agents/)
├── .claude/               # 심링크 계층 (agents→../.agents/agents, skills→../.agents/skills) + settings.json
├── .codex/                # Codex 병행 계층 (config.toml 인라인 훅 + 필요 시 agents/*.toml 어댑터)
├── docs/                  # README(MOC) + adr/ + proposals/ + specs/
├── vault/                 # 미추적 심링크 → 실제 Obsidian vault (하단 §3)
└── _workspace/            # 미추적 세션 산출물
```

- **study-install 스킬**: 심링크 검증 → 지식 루트·프로필·동기화 방식
  인터뷰 → vault 심링크 생성 → REGISTRY.md 생성. Phase 1은 무의존으로
  두고 도구 상태만 보고한다. defuddle·논문·영상 도구의 실제 설치는 해당
  Phase 2 파이프라인 채택 시 추가한다.
- **이 저장소가 추적하는 것은 하네스뿐** — 설치처마다 달라지는 지식
  파일(vault)은 미추적으로 두어 이식성을 확보한다.

## 3. Vault 전략 (결정됨)

- 설치처마다 `study-install`에서 지식 루트를 선택한다. Obsidian이 없는
  컴퓨터도 일반 디렉터리를 지식 루트로 사용할 수 있다.
- 이 컴퓨터는 Google Drive가 동기화하는 기존 Obsidian vault 루트를 그대로
  사용하며 `vault/` 미추적 심링크로 연결한다. 기존 노트에 새 규약을 일괄
  소급하지 않고, `raw/`·`wiki/` 아래 새 지식부터 규약을 적용한다.
- 지식 저장소의 Git 추적 여부는 설치처별 정책이다. 하네스 저장소에는
  절대 포함하지 않고 설치기가 vault Git을 자동 초기화하지 않는다.

## 4. 저장소별 도입 판정

| 대상 | 판정 | 근거 요약 |
|---|---|---|
| **claude-obsidian** | **규약만 이식** (통설치 기각) | 아키텍처 청사진으로 최적: hot.md 핫 캐시+훅, raw/wiki 분리, flat YAML 스키마(type/status/created/related/sources — status: seed→developing→mature→evergreen), 인덱스 위계, ingest 체크리스트, 멀티 에이전트 심링크 배선. 기각 사유: 유지보수 2개월 정지(마지막 push 2026-05-28)·1인 프로젝트·마케팅 콘텐츠 혼입·서드파티 플러그인 번들. MIT라 규약·스크립트 발췌 자유 |
| **superpowers** | **패턴만 이식** (통설치 기각) | 14개 스킬 전부 코딩용, 공부 스킬 0개. 이식할 패턴: ①SessionStart 부트스트랩(`using-study` 메타 스킬 주입 — "새 지식 접하면 노트 스킬 체크, 질문받으면 기존 노트 검색 먼저") ②SDO description 규칙("Use when + 트리거만, 워크플로 요약 금지") ③도구 중립 본문 + 도구 매핑 분리 ④writing-skills의 TDD식 스킬 검증 ⑤brainstorming의 소크라테스식 구조 → "학습 대화" 스킬로 개조 |
| **Understand-Anything** | **9개 스킬 전체 채택 — Phase 2b 통합** | 코드 저장소, 비즈니스 도메인, 설계 변경, Figma, Markdown 지식 베이스는 모두 nohdol-study가 공부할 수 있는 자료다. `/understand`, `-chat`, `-dashboard`, `-diff`, `-domain`, `-explain`, `-figma`, `-knowledge`, `-onboard`를 모두 제공한다. 단, upstream installer의 main 추적·전역 심링크와 현재 monorepo dependency 상태는 그대로 수용하지 않는다. exact commit으로 project-local 설치하고, 그래프 답변은 반드시 원문을 다시 열어 확인하며, dashboard와 Figma 외부 호출은 명시 실행으로 제한한다. |
| **claude-video** | **채택 — 인식 계층 + 상위 스킬** | `/watch`는 인식만 하고 영구 노트를 안 남긴다 — study가 채울 빈자리. `study-video` 스킬(2-pass): ①`--detail transcript`로 저비용 전체 파악 → ②중요 구간만 `--start/--end`+`--timestamps` 큐 프레임 → ③frontmatter+타임스탬프 링크+핵심 프레임을 vault attachments로 복사한 노트 생성. **한국어 자막 패치 필수**: download.py의 `--sub-langs "en.*"` 하드코딩 → `"ko.*,en.*"` (미패치 시 한국어 강의가 유료 Whisper로 빠짐). Whisper 오디오 외부 전송은 nohdol-study의 명시 승인 규칙을 따른다. |
| **defuddle** | **채택** (harness 스킬 이식 + 확장) | CLI가 본체 통합(defuddle-cli는 아카이브). `defuddle parse <URL> --md -f -o vault/...` 한 줄로 frontmatter 달린 Obsidian-ready 노트. 콜아웃·수식(MathML→LaTeX)·코드 블록이 Obsidian 문법으로 정규화 — 기술 아티클에 유리. **이식 시 수정 1건**: 기존 SKILL.md 25행의 `-p`(단일 속성 추출, name 인자 필수)는 오류 — 메타데이터 포함 마크다운은 `-f`가 정답. 웹 클리핑→ingest 파이프라인의 입구로 확장 |
| **context7** | **채택** (harness 스킬 그대로 이식) | 공부 중 라이브러리·프레임워크 문서 조회는 study에서도 동일 니즈. 폴백(WebFetch/WebSearch) 설계 완성돼 있어 수정 불요. MCP 등록은 user 스코프라 이미 전역 |

### 4-1. Understand Anything 재검토 결론

이 프로젝트는 지식 노트만이 아니라 코드베이스·제품 도메인·변경 이력·
Figma 설계까지 학습 대상으로 삼는다. 그러므로 upstream의 9개 스킬은 모두
유효하다.

| 스킬 | nohdol-study에서의 용도 | 실행 경계 |
|---|---|---|
| `understand` | 공부할 코드 저장소를 구조·흐름·개념 그래프로 변환 | Node 22+·pnpm 10+ 준비와 dependency audit 후 실행 |
| `understand-chat` | 그래프를 탐색해 질문의 관련 원문 위치 찾기 | 답변 전 해당 source file을 직접 읽음 |
| `understand-dashboard` | 큰 그래프를 로컬 시각화 | 자동 실행하지 않고 사용자가 요청할 때만 localhost viewer 실행 |
| `understand-diff` | 코드 변경이 개념·흐름에 미친 영향 학습 | diff overlay는 파생물이며 원문 판단을 대체하지 않음 |
| `understand-domain` | 코드에서 사용자·비즈니스 흐름 학습 | 추론한 흐름은 코드 근거와 대조 |
| `understand-explain` | 특정 개념·흐름을 source-first로 깊게 설명 | 그래프 요약만으로 확정하지 않음 |
| `understand-figma` | Figma 설계를 제품·코드 학습과 연결 | `FIGMA_TOKEN`과 `api.figma.com` 전송을 명시 승인한 때만 |
| `understand-knowledge` | `raw/`·`wiki/`의 claim·source·topic 연결 탐색 | semantic edge에 evidence·confidence·verification 추가 |
| `understand-onboard` | 낯선 저장소의 학습 순서와 walkthrough 생성 | 생성 문서는 파생 학습 자료로 표시 |

“전체 스킬 채택”과 “upstream installer 그대로 실행”은 같은 결정이 아니다.
installer는 main branch를 pull하고 `~/.agents/skills`의 동일 이름을
`ln -sfn`으로 교체한다. nohdol-study는 exact release/commit을 미추적
project-local 도구 경로에 설치하고, 이 프로젝트가 노출할 9개 skill adapter를
통해 실행한다. 이로써 설치처마다 버전을 재현하면서 다른 프로젝트의 전역
skill을 덮지 않는다.

지식 모드는 추가로 다음을 보완한다.

- explicit wikilink 그래프는 결정적으로 재생성한다.
- 암묵 claim과 edge에는 원문 파일·근거 구간·추출 방식·confidence·
  verification 상태를 남긴다.
- vault를 분석할 때 파생물은 미추적 `_workspace/`로 리디렉션하고 최종
  그래프에 노트 전문을 복제하지 않는다.
- 코드 프로젝트를 분석할 때는 대상 저장소의 `.ua/`를 쓸 수 있지만 실행 전
  ignore 상태와 쓰기 범위를 확인한다.

현재 upstream v2.9.0 knowledge parser 테스트는 `8 passed, 1 skipped`였지만,
이 컴퓨터의 `wiki/`는 문서가 1개라 upstream의 `md_count >= 3` 탐지에서
실패한다. 또한 v2.9.0 전체 production lock 감사에는 high 10건을 포함한
21건이 있어 Node 기반 스킬을 지금 바로 설치하지 않는다. Phase 2b는
project-local pin, 필요한 package만의 exact lock, audit, 출력 경계 어댑터를
완료한 뒤 9개를 활성화한다.

## 5. 추가 도입 후보 (직접 리서치)

| 후보 | 판정 | 요약 |
|---|---|---|
| **basic-memory** (basicmachines-co) | **채택 — Phase 2c 제한 파일럿** | Markdown을 source of truth로 두고 SQLite를 재생성 가능한 로컬 인덱스로 사용하며 CLI 검색을 제공한다. 100노트라는 임의 게이트는 제거한다. 기존 vault의 명시된 작은 범위에서 read/search 중심으로 시험하고 원본 hash·검색 정확도·지연·노이즈를 현재 parser/UA와 비교한다. `bm format`, 자동 write/reset은 파일럿에서 금지한다. AGPL-3.0이므로 코드를 저장소에 vendor하지 않는다. |
| **paper-search-mcp** (openags) | **채택** | arXiv 등 다중 소스 논문 검색·다운로드·텍스트 추출, **MCP·CLI·Skills 3중 인터페이스** — 도구 중립. 로봇·physical AI 공부의 논문 파이프라인 입구: 검색/다운로드(CLI) → raw/ 저장 → 노트화 스킬. **가드레일 필수**: 논문 텍스트는 데이터로만 취급(prompt injection 방어 — Understand-Anything의 "untrusted data" 명시 패턴 차용) |
| **spaced repetition** | **채택(경량, Phase 3)** | 노트에서 플래시카드 후보를 지정 포맷 마크다운으로 추출하는 스킬 + obsidian-spaced-repetition 플러그인(vault 내 FSRS, 플레인 파일) 또는 Obsidian_to_Anki CLI 중 택일. Anki MCP는 대화형 리뷰 수요가 생기면 |
| **PaperQA2** | **조건부 채택 — 논문 심층 질의** | PDF/text 묶음에 인용이 있는 RAG를 제공한다. `raw/papers`의 특정 corpus를 깊게 비교할 때만 사용하고, 기본 OpenAI 모델·embedding으로 원문을 보낼 수 있으므로 provider와 전송 범위를 승인받는다. NotebookLM보다 재현 가능한 로컬 index가 필요한 경우의 보완재다. |
| **kepano/obsidian-skills** | **4종 채택** | `obsidian-markdown`, `obsidian-bases`, `json-canvas`, `obsidian-cli`를 project-local로 도입한다. upstream `defuddle`은 현재 nohdol-study 스킬보다 근거·불변 캡처 규칙이 약해 중복 도입하지 않는다. 공식 Obsidian CLI는 앱 1.12.7+와 실행 중인 앱이 필요하며, 이 Mac의 1.10.6에서는 아직 사용할 수 없다. |
| **Graphiti** | **보류 — temporal graph 수요 시 재검토** | 시간에 따른 entity/fact 변화와 agent memory에는 강하지만 Neo4j/FalkorDB/Neptune와 LLM provider가 필요하다. 학습 노트에서 시간축 지식 질의가 반복될 때만 파일럿한다. |
| **Mem0** | **보류 — 개인화 agent memory 수요 시 재검토** | LLM·embedder·vector store를 조합하는 agent memory 계층이다. 지금 필요한 문서 학습·근거 추적보다 운영 계층이 크다. |
| **Cognee** | **보류 — 다중 데이터 memory pipeline 수요 시 재검토** | vector·graph·relational 계층과 모델 설정을 함께 운영한다. 현재 파일 기반 학습에는 과하고, 프롬프트·tool trace까지 기억할 명시 요구가 생기면 다시 본다. |
| **Kuzu** | **신규 도입 제외** | 공식 저장소가 2025-10 아카이브되어 유지보수되는 새 의존성으로 선택하지 않는다. |
| **Obsidian Local REST API/MCP** | **기본 경로 보류** | 앱 상주, API key, self-signed HTTPS 또는 loopback HTTP가 필요하고 노트 쓰기·명령 실행 표면이 넓다. 공식 Obsidian CLI가 충족하지 못하는 live-app/원격 client 요구가 생길 때만 재검토한다. |

세부 근거와 재검토 조건은
[추가 도구 검토](../reviews/2026-07-25-additional-tools-review.md)에 기록한다.

## 5-1. 다이어그램·그림 도구 (2026-07-25 추가 검증)

문서·노트 작성 시 아키텍처 다이어그램/그림 생성 도구. 판단 기준: Obsidian 렌더링 여부 > LLM 텍스트 생성 적합성 > CLI 이식성.

| 용도 | 도구 | 판정 근거 |
|---|---|---|
| **기본** (플로우·시퀀스·상태도·일반 구조도) | **Mermaid** (코드 펜스) | Obsidian 네이티브 렌더링(2026-07 릴리스에서 v11.13.0 번들 — mindmap·timeline·C4·architecture-beta까지), **의존성 0**(뷰어 내장 렌더링이라 바이너리 불필요), LLM 생성 최적, GitHub·Claude Code·Codex 무차별 동작 |
| **복잡한 아키텍처** (로봇 SW 스택 등 노드 15개+/중첩 3단+) | **D2 + ELK → SVG 임베드** | Go 단일 바이너리(MPL-2.0, 24.8k★ 활발), ELK 레이아웃이 Mermaid가 무너지는 규모에서 품질 확보, sketch 모드. 공식 Obsidian 플러그인은 방치 상태라 **`d2 in.d2 out.svg` → `![[...]]` 임베드** 파이프라인으로 사용. CLI가 문법 오류를 즉시 리턴해 에이전트 자가 수정 루프에 적합 |
| **지식 맵** (개념 관계도) | **JSON Canvas (.canvas)** | Obsidian 네이티브 무한 캔버스, 오픈 스펙 1.0(MIT), 순수 JSON이며 vault note file node를 직접 참조할 수 있다. 채택한 `json-canvas` 스킬에 겹침 방지 그리드와 읽기 순서를 명문화한다. |
| **수학/기하 그림** (궤적·좌표계·변환·3D 기구학) | **matplotlib → SVG 임베드** (간단 도식은 SVG 직접 생성 폴백, 수식은 MathJax) | 정확한 좌표·곡선·3D는 스크립트 렌더링만 신뢰 가능. Python 스크립트 생성 → SVG 저장 → 임베드 |

**도입하지 않을 것**: PlantUML(JVM+Graphviz 이중 런타임 — 이식성 정면 위배), draw.io(GUI 본질, headless export가 Electron/xvfb로 과중), Excalidraw 직접 JSON 생성(좌표 명시 JSON이라 가이드 없는 LLM 생성물 품질 낮음 + Obsidian 플러그인이 1인 프로젝트로 지속성 경고등 — 손그림 감성이 필요하면 mermaid-to-excalidraw 변환 경로), Graphviz 단독(D2 ELK가 상위 호환), manim(정적 노트에 과잉), tldraw(관망).

**운영 규칙**: ①그림 산출물은 노트 옆 `assets/` 하위 SVG로 통일,
②Mermaid→D2 승급 기준을 `diagram` 스킬에 명문화, ③채택한 Obsidian
스킬 4종은 exact commit의 project-local 설치로 제공하고 전역 skill을
덮어쓰지 않는다.

## 5-2. NotebookLM CLI 재검토

웹 UI 자동화는 계속 비목표다. 대신 `notebooklm-py`의 CLI를
`notebooklm-export` 뒤에 붙이는 **선택적 consumer bridge**를 Phase 2b로
채택한다. 이 경로는 notebook 생성, source upload, 질의, 퀴즈·플래시카드·
인포그래픽 생성과 다운로드를 CLI에서 수행할 수 있다.

보안 검토 결과 현재 안정 릴리스 v0.7.3을 즉시 자동 설치하는 것은
보류한다. 저장소 최신 코드에는 들어간 다운로드 redirect 매-hop 검증이
v0.7.3 태그에는 없고, 릴리스의 lock에는 취약한 `click 8.3.1`이 있다.
최신 허용 범위로 다시 해석한 browser/cookies 의존성은 감사 시 알려진
취약점이 없었지만, 비공식 Google 내부 API·bearer cookie·계정 제한 위험은
남는다. 세부 판정과 설치 게이트는
[보안 검토](../reviews/2026-07-25-notebooklm-understand-anything-security.md)와
[ADR 003](../adr/003-cli-learning-integrations.md)을 따른다.

## 6. 스킬 로스터

| 스킬 | 역할 | 원천 |
|---|---|---|
| `study-install` | 신규 머신 부트스트랩 (심링크·도구·vault·REGISTRY) | 자체 |
| `using-study` | 세션 부트스트랩 메타 스킬 (훅 주입) | superpowers 패턴 |
| `ingest` | 소스 유형 라우팅 (웹→defuddle, 논문→paper-search, 영상→study-video) → raw/ 저장 → 노트 생성 → 인덱스·log·hot 갱신 체크리스트 | claude-obsidian ingest 규약 |
| `note-writer` | 노트 규약 집행 (frontmatter 스키마·위키링크·원자성·contradiction/gap 콜아웃) | claude-obsidian WIKI.md 상당 — study의 doc-writer |
| `study-session` | 소크라테스식 학습 대화 (한 질문씩·이해 확인 게이트·결과 노트화) | superpowers brainstorming 개조 |
| `study-video` | 강의 영상 → 노트 2-pass 파이프라인 | claude-video 상위 스킬 |
| `defuddle` / `context7` | 웹 본문 추출 / 라이브러리 문서 | 외부 도구를 nohdol-study 규칙에 맞게 통합 |
| `understand-*` 9종 | 코드·도메인·diff·온보딩·설명·질의·dashboard·Figma·지식 그래프 학습 | Understand Anything project-local adapter |
| `knowledge-graph` | explicit 결정적 그래프 구현됨; UA knowledge graph의 정확성·품질 기준 | Understand Anything knowledge + 기존 기준 parser |
| `notebooklm-export` | 검증 snapshot 구현됨; 선택적 CLI upload/generate/download bridge는 Phase 2b 확장 | 자체 export + notebooklm-py |
| `obsidian-markdown` / `obsidian-bases` / `json-canvas` / `obsidian-cli` | Obsidian 문법·동적 뷰·캔버스·공식 CLI 사용 | kepano/obsidian-skills project-local pin |
| `diagram` | 문서·노트 다이어그램 생성 (Mermaid 기본, 노드 15개+/중첩 3단+ → D2→SVG, 지식 맵 → JSON Canvas, 수학 그림 → matplotlib→SVG — §5-1 승급 규칙) | 신규 |
| `vault-gardening` | 주기적 인덱스·링크 정합·고아 노트 점검 | 신규 |
| `recall` (Phase 3) | 플래시카드 추출·복습 | SR 경량 경로 |

훅은 Claude `settings.json`과 Codex `config.toml` 인라인 설정을 병행한다.
SessionStart에 hot.md 로드 + using-study를 주입하고, Stop/wrapup에 hot.md
갱신을 유도한다.

## 7. 단계별 로드맵

1. **Phase 1 — 골격 (완료)**: 디렉토리·심링크·AGENTS.md·docs MOC·study-install·note-writer(규약)·vault 연결.
2. **Phase 2 — ingest 3종 + 기준 그래프 (완료)**: defuddle·paper-search·study-video, 검증 NotebookLM export, explicit wikilink 결정적 그래프.
3. **Phase 2b — project-local 학습 연동 (채택·미구현)**: Understand Anything 9개 스킬, Obsidian 스킬 4개, NotebookLM CLI bridge. dashboard는 명시 실행만 허용하고 Figma·NotebookLM 전송은 승인 경계를 둔다.
4. **Phase 2c — 검색·논문 심층 파일럿**: basic-memory를 작은 read/search 범위에서 비교하고, PaperQA2는 사용자가 지정한 논문 corpus에만 조건부 실행한다.
5. **Phase 3 — 학습 루프 (미구현)**: `diagram` → `study-session` → `vault-gardening` → `recall` 순으로 구현하고 boundary score는 그 뒤에 검토한다.

### 7-1. 남은 작업과 우선순위

| 우선순위 | 작업 | 완료 기준 |
|---|---|---|
| P0 | Understand Anything 9개 전체 채택·보안 경계 문서화 | direction·ADR·보안 검토·실행 스펙이 동일한 판정을 말한다 |
| P1 | UA와 Obsidian 스킬의 project-local exact-pin installer 구현 | upstream main 자동 pull·전역 symlink 없이 source commit·license·hash·도구 상태를 REGISTRY에 기록 |
| P1 | UA Node dependency를 필요한 package 단위로 고정·감사 | Node 22+·pnpm 10+ 확인, high 취약점 0 또는 위험별 명시 승인, 설치 전후 전역 skill 불변 |
| P1 | 9개 UA skill adapter와 실행 라우팅 추가 | 각 upstream skill을 호출할 수 있고 source-first·출력·dashboard·Figma 경계 테스트 통과 |
| P1 | `knowledge-graph`를 upstream knowledge schema 기반으로 확장 | 현재 1개 `wiki/`도 탐지, 출력 경로 주입, 결정적 explicit graph, 본문 미포함, upstream fixture+로컬 회귀 통과 |
| P1 | semantic enrichment를 별도 opt-in 단계로 추가 | entity/claim/암묵 edge마다 evidence anchor·confidence·verification·extractor가 있고 prompt injection 문구를 데이터로만 처리 |
| P1 | 현재 vault에서 Understand Anything 파생 그래프를 실제 생성 | 원본 Markdown byte/hash 불변, `_workspace/`에만 산출, missing/orphan/typed 관계 보고 |
| P1 | `notebooklm-py` 안전 릴리스 게이트와 CLI wrapper 구현 | redirect fix 포함 릴리스 또는 감사한 정확 commit 고정, 취약 의존성 0, base+필요 최소 extra만 설치 |
| P1 | NotebookLM consumer bridge를 export packet 뒤에 연결 | vault 심링크 직접 업로드 금지, packet manifest 확인, 전송 승인 후 create/upload/generate/download, 결과 `_workspace/` 저장 |
| P1 | NotebookLM 인증·변경 보호 | 전용 profile, 0600/0700 확인, master-token·MCP/server·impersonate 금지, public share/delete/외부 전송 명시 승인 |
| P1 | Obsidian 스킬 4종 도입 | markdown/bases/canvas 형식 검증, CLI는 앱 1.12.7+일 때만 available로 표시 |
| P2 | basic-memory 제한 파일럿 | 지정 경로만 index, 원본 hash 불변, write/format/reset 없이 검색 fixture로 parser·UA와 비교 |
| P2 | PaperQA2 on-demand wrapper | 지정 corpus·provider·외부 전송을 확인하고 인용 결과를 원 PDF와 재검증 |
| P2 | `diagram` 스킬 구현 | Mermaid 기본, 이미지/SVG provenance, Physical AI 문서 그림 경로를 브라우저 없이 재현 |
| P2 | `study-session` 구현 | 한 질문씩 이해 확인, 오답·불확실성 보존, 결과 노트 선택 저장 |
| P2 | `vault-gardening` 구현 | index/log/hot·깨진 링크·고아·중복 제목을 비파괴적으로 점검 |
| P3 | `recall`과 spaced repetition 구현 | 원문 근거로 답을 검증할 수 있는 카드만 생성, 스케줄 데이터는 설치처 로컬 |
| 게이트 | Graphiti·Mem0·Cognee 재검토 | temporal graph·agent personalization·다중 데이터 memory 중 하나가 실제 반복 요구가 될 때 |
| 게이트 | Obsidian REST/MCP 재검토 | 공식 CLI로 해결할 수 없는 live-app 또는 원격 client 요구가 생길 때 |

### 7-2. 기존 direction 전 항목 구현 대조

| 영역 | 재검토 결과 | 후속 |
|---|---|---|
| §1 raw/wiki/index/log/hot | 채택·구현됨 | 현 구조 유지, JSON은 계속 파생물 |
| §2 하네스 골격 | 채택·구현됨 | `.agents` 단일 원본과 미추적 vault/REGISTRY 유지 |
| §3 vault 전략 | 기존 “새 vault 권고”가 사용자 결정과 불일치해 수정됨 | 설치처별 선택, 이 Mac은 기존 Google Drive vault root 사용 |
| §4 claude-obsidian | 규약만 이식 완료 | 전체 plugin 설치 계획 없음 |
| §4 superpowers | SessionStart·SDO·metaskill 패턴 이식 완료 | `study-session`만 Phase 3 미구현 |
| §4 Understand Anything | 9개 스킬 전체 채택 | Phase 2b project-local 설치·어댑터·감사 필요 |
| §4 claude-video | `study-video`와 한국어 자막 patch 구현됨 | 실제 지정 영상별 end-to-end만 실행 |
| §4 defuddle/context7 | 스킬 구현됨 | 설치처별 실행 파일·연결 상태만 관찰 |
| §5 paper-search | 스킬과 ingest route 구현됨 | 실제 논문은 사용자 지정 시 수집 |
| §5 basic-memory | 100노트 게이트 제거, 제한 파일럿 채택 | Phase 2c read/search 비교 필요 |
| §5 PaperQA2 | 조건부 채택 | 지정 논문 corpus가 있을 때만 실행 |
| §5 Obsidian skills | 4종 채택 | project-local 설치; 이 Mac은 앱 update 전 CLI unavailable |
| §5 memory/graph servers | 현 요구에는 보류 | 명시된 재검토 trigger가 생길 때만 |
| §5 spaced repetition | 채택만 됨 | `recall` Phase 3 미구현 |
| §5-1 diagram | 도구 판정만 있음 | `diagram` 스킬과 provenance 규칙 미구현 |
| §6 스킬 로스터 | 11개 현재 스킬은 구현됨 | `study-session`, `diagram`, `vault-gardening`, `recall` 미구현 |
| §7 로드맵 | Phase 1·2 완료 | Phase 2b → Phase 3 순으로 수정 |
| NotebookLM | 검증 packet export만 구현됨 | CLI bridge는 보안 게이트 뒤 Phase 2b에서 구현 |

## 8. 사용자 결정

1. **vault 위치·관계**: 설치처마다 `study-install`에서 정확한 지식 루트를 선택한다. 기존 Obsidian vault 루트·하위 폴더·일반 디렉터리를 모두 지원한다.
2. **vault git 추적**: 설치처별 정책이다. 하네스 Git에는 절대 포함하지 않고, 설치기는 vault Git을 자동 초기화하지 않는다.
3. **basic-memory 도입 방식**: 노트 수가 아니라 지정 corpus와 사전 정의한
   검색 질문으로 제한 파일럿한다. 원본 변경 명령은 허용하지 않는다.
4. **사내/개인 프로필**: 설치처별 `REGISTRY.md`에 기록한다. 사내 프로필은 선택적 제3자 전송을 기본 금지한다.

## 변경 이력

| 날짜 | 변경 내용 | 사유 |
|---|---|---|
| 2026-07-25 | 최초 작성 — 5개 저장소 + 추가 후보 병렬 분석 종합 | 사용자 방향 검토 요청 |
| 2026-07-25 | §5-1 다이어그램·그림 도구 검증 추가 + `diagram` 스킬 로스터 반영 | 사용자 요청 — 문서 작성 시 아키텍처·그림 도구 필요 |
| 2026-07-25 | Phase 1 채택·구현 — 설치처별 지식 루트 선택, Obsidian 선택 의존성, vault Git 정책 미추적 확정 | 사용자 답변 반영 |
| 2026-07-25 | 주장 단위 근거 검증을 AGENTS 상시 규칙과 note-writer 필수 참조로 추가 | 사용자 요구 — 선택 스킬보다 항상 적용되는 정확성 규율이 적합 |
| 2026-07-25 | Phase 2 웹·논문·영상 ingest, NotebookLM 검증 snapshot, 결정적 그래프 기준 구현 | 사용자 요청 — NotebookLM 연동 검사와 Phase 2 진행 |
| 2026-07-25 | metaskill 규칙과 상세 한글 스킬 안내 도입 | 사용자 요청 — 스킬 설명·README가 빈약해지는 문제 방지 |
| 2026-07-25 | 전체 재검토 — Understand Anything 9개 스킬 전체 채택, NotebookLM CLI 조건부 채택, Phase 2b 작업 목록 추가 | 다른 프로젝트의 판정이 아니라 nohdol-study의 코드·도메인·설계·지식 학습 목적만으로 재평가 |
| 2026-07-25 | 추가 후보 재검토 — Obsidian 4종·basic-memory·PaperQA2 채택 범위 확정, memory server 계열 재검토 조건 명시 | 임의 노트 수 게이트를 제거하고 source-of-truth·외부 전송·운영 복잡도로 판단 |
