# docs/ — 결정·스펙·제안 지도

이 디렉터리는 nohdol-study의 결정과 구현 기준을 연결하는 MOC(Map of Content)다. 현재 운영 규칙의 단일 원본은 [AGENTS.md](../AGENTS.md)다.

## ADR

| ADR | 날짜 | 상태 | 제목 |
|---|---|---|---|
| [001](adr/001-initial-study-harness.md) | 2026-07-25 | 활성 | 파일 기반 공부 하네스 Phase 1 구조 |
| [002](adr/002-phase2-derived-workflows.md) | 2026-07-25 | 활성 | Phase 2 수집·NotebookLM·그래프 파생 워크플로 |
| [003](adr/003-cli-learning-integrations.md) | 2026-07-25 | 활성 | Understand Anything 전체 스킬과 선택적 학습 연동의 project-local 채택 |

## 스펙

| 스펙 | 상태 | 대상 |
|---|---|---|
| [2026-07-25-phase1-study-harness](specs/2026-07-25-phase1-study-harness.md) | 구현됨 | 설치기, 지식 구조, 공용 스킬, 세션 훅 |
| [2026-07-25-phase2-ingest-notebooklm-graph](specs/2026-07-25-phase2-ingest-notebooklm-graph.md) | 구현됨 | 웹·논문·영상 ingest, NotebookLM export, 그래프 기준 파서 |
| [2026-07-25-phase2b-cli-learning-integrations](specs/2026-07-25-phase2b-cli-learning-integrations.md) | 2b-A~2b-C 구현, 2b-D·2b-E 미구현 | Understand Anything 9종, Obsidian 4종, NotebookLM CLI bridge |

## 제안

| 제안 | 결과 | 요지 |
|---|---|---|
| [2026-07-25-nohdol-study-direction](proposals/2026-07-25-nohdol-study-direction.md) | Phase 1·2 구현, Phase 2b 범위 확정 | Markdown 원본, Understand Anything 전체 스킬, Obsidian·NotebookLM 선택 연동 |

## 검토

| 검토 | 판정 |
|---|---|
| [NotebookLM CLI·Understand Anything 보안 검토](reviews/2026-07-25-notebooklm-understand-anything-security.md) | notebooklm-py 조건부 채택·v0.7.3 설치 보류, Understand Anything 9종 project-local 안전 어댑터 채택 |
| [추가 도구 도입 검토](reviews/2026-07-25-additional-tools-review.md) | basic-memory 제한 파일럿, PaperQA2 조건부, Obsidian 4종 채택; memory server 계열 보류 |

## 작업 인계

| 인계 | 시작 작업 |
|---|---|
| [2026-07-25 다음 세션](handoffs/2026-07-25-next-session.md) | Phase 2b-A project-local exact-pin 설치 기반 |

## 변경 이력

- [하네스 변경 이력](harness-changelog.md)
