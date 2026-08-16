# docs/ — 결정·스펙·제안·가이드 지도

이 디렉터리는 nohdol-study의 결정과 구현 기준을 연결하는 MOC(Map of Content)다. 현재 운영 규칙의 단일 원본은 [AGENTS.md](../AGENTS.md)다.

## 가이드 (Guides)

| 가이드 | 대상 | 요지 |
|---|---|---|
| [Workspace Portal](../examples/workspace_portal/README.md) | `_workspace`의 사용자용 다이내믹 HTML 사이트 | `_workspace/sites/<slug>/` 경로와 명시적 manifest, 단일 server root, portal 초기화·등록·검사 |
| [모바일 텔레그램 스터디 브리지](guides/mobile-telegram-bot.md) | 스마트폰 텔레그램 ↔ Mac 하네스 연동 (읽기 전용) | 지식 루트를 읽기만 하는 조회·문답 표면, 모바일 소크라테스 학습, 인라인 버튼 제어, MessageEntity 기반 무결점 서식 렌더링 및 로컬 URL 정제, launchd 부팅 시 자동 시작, AGENTS.md 보안 화이트리스트 준수 |
| [피드 스크래퍼](guides/feed-scraper.md) | RSS 소스 → vault 자동 수집 | 카탈로그(추적)와 컴퓨터별 선택(비추적) 분리, `feed`는 제목·링크만 쌓아 API 호출 0, `geeknews`는 점수 게이트 후 요약·분류, 마커 기반 중복 방지, launchd 자동 실행 |

## ADR

| ADR | 날짜 | 상태 | 제목 |
|---|---|---|---|
| [001](adr/001-initial-study-harness.md) | 2026-07-25 | 활성 | 파일 기반 공부 하네스 Phase 1 구조 |
| [002](adr/002-phase2-derived-workflows.md) | 2026-07-25 | 활성 | Phase 2 수집·NotebookLM·그래프 파생 워크플로 |
| [003](adr/003-cli-learning-integrations.md) | 2026-07-25 | 부분 대체(→004) | Understand Anything 전체 스킬과 선택적 학습 연동의 project-local 채택 |
| [004](adr/004-remove-notebooklm-export.md) | 2026-07-25 | 활성 | NotebookLM export 스킬 제거 — 회수 0건, 763줄 유지 비용 대비 무효 |
| [005](adr/005-egress-guard-for-external-runtimes.md) | 2026-08-01 | 활성 | 외부 런타임 유출 게이트를 별도 훅으로 — 승인 프롬프트는 페이로드 내용을 묻지 않는다 |
| [006](adr/006-archify-explicit-use-outside-vault.md) | 2026-08-09 | 활성 | archify는 명시 호출 전용, 산출물은 `_workspace/` — CLI에 SVG 출력이 없어 노트가 임베드할 수 없다 |
| [007](adr/007-single-workspace-site-portal.md) | 2026-08-16 | 활성 | 사용자용 다이내믹 사이트는 `_workspace` 단일 포털에서 연다 |

## 스펙

| 스펙 | 상태 | 대상 |
|---|---|---|
| [2026-07-25-phase1-study-harness](specs/2026-07-25-phase1-study-harness.md) | 구현됨 | 설치기, 지식 구조, 공용 스킬, 세션 훅 |
| [2026-07-25-phase2-ingest-notebooklm-graph](specs/2026-07-25-phase2-ingest-notebooklm-graph.md) | 구현됨 | 웹·논문·영상 ingest, NotebookLM export, 그래프 기준 파서 |
| [2026-07-25-phase2b-cli-learning-integrations](specs/2026-07-25-phase2b-cli-learning-integrations.md) | 2b-A~2b-D 구현, 2b-E는 ADR 004로 철회 | Understand Anything 9종, Obsidian 4종, NotebookLM CLI bridge |
| [2026-08-16-workspace-site-portal](specs/2026-08-16-workspace-site-portal.md) | 구현됨 | `_workspace` 단일 portal, site manifest, 등록·검증 도구 |

## 제안

| 제안 | 결과 | 요지 |
|---|---|---|
| [2026-07-25-nohdol-study-direction](proposals/2026-07-25-nohdol-study-direction.md) | Phase 1·2 구현, Phase 2b 범위 확정 | Markdown 원본, Understand Anything 전체 스킬, Obsidian·NotebookLM 선택 연동 |

## 검토

| 검토 | 판정 |
|---|---|
| [2026-07-25-phase2c-pilot-status](reviews/2026-07-25-phase2c-pilot-status.md) | PaperQA2 불가·basic-memory 미채택 | 색인이 노트 frontmatter를 수정해 읽기 전용 전제를 충족 못 함. 검색은 유효, 외부 전송 없음 |
| [NotebookLM CLI·Understand Anything 보안 검토](reviews/2026-07-25-notebooklm-understand-anything-security.md) | notebooklm-py 조건부 채택·v0.7.3 설치 보류, Understand Anything 9종 project-local 안전 어댑터 채택 |
| [추가 도구 도입 검토](reviews/2026-07-25-additional-tools-review.md) | basic-memory 제한 파일럿, PaperQA2 조건부, Obsidian 4종 채택; memory server 계열 보류 |

## 작업 인계

| 인계 | 시작 작업 |
|---|---|
| [2026-07-25 다음 세션](handoffs/2026-07-25-next-session.md) | Phase 2b-A project-local exact-pin 설치 기반 |

## 변경 이력

- [하네스 변경 이력](harness-changelog.md)
