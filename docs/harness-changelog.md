# nohdol-study 하네스 변경 이력

| 날짜 | 변경 내용 | 대상 | 이유 |
|---|---|---|---|
| 2026-07-25 | Phase 1 파일 기반 공부 하네스 구축 | 저장소 골격, 설치기, 스킬, 훅, 문서 | 설치처별 vault와 Claude Code·Codex를 연결하면서 지식과 하네스를 분리 |
| 2026-07-25 | 주장 단위 근거 검증 규율 추가 후 상시 규칙으로 통합 | AGENTS, `note-writer` 필수 참조, 노트 스키마 | 선택 스킬 활성화 누락 없이 잘못된 정보의 확정 지식화를 방지 |
| 2026-07-25 | Phase 2 ingest·NotebookLM·그래프 기준 구현 | 웹 capture, 논문·영상 스킬, 검증 export, 결정적 그래프, 설치 도구 | 다양한 자료를 원문 보존·검증 경계를 유지하며 학습 자산으로 전환 |
| 2026-07-25 | metaskill 규칙 도입과 스킬 문서 보강 | `metaskill`, 루트 README, 한글 스킬 안내, 기존 스킬 | 하네스 변경과 사용자용 라우팅 문서가 함께 검증·동기화되도록 함 |
| 2026-07-25 | direction 전체 재검토와 Phase 2b 범위 수정 | Understand Anything 9개 스킬, Obsidian 4개 스킬, NotebookLM CLI, ADR 003, 보안 검토, 실행 스펙 | 다른 프로젝트의 판정 대신 nohdol-study의 코드·도메인·설계·지식 학습 목적만으로 평가하고 project-local 설치 경계를 명문화 |
| 2026-07-25 | 추가 도구 후보 재검토 | basic-memory, PaperQA2, Graphiti, Mem0, Cognee, Kuzu, Obsidian REST/MCP, SR, diagram | 임의 100노트 게이트를 제거하고 실제 효용·source-of-truth·외부 전송·운영 비용에 따라 채택과 재검토 조건을 구분 |
| 2026-07-25 | 다음 세션 작업 인계와 Phase 경계 정합 수정 | Phase 2b-A~E, Phase 2c·3, Physical AI 이미지, AGENTS 한글 뷰, `knowledge-graph` | 새 세션이 설치처 정보나 외부 전송 경계를 추측하지 않고 바로 이어서 구현하도록 하고 남아 있던 basic-memory 100노트 규칙을 현재 결정과 일치시킴 |
