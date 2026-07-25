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
| 2026-07-25 | Phase 2b-B — Understand Anything adapter 9종 | `understand`·`understand-chat`·`-dashboard`·`-diff`·`-domain`·`-explain`·`-figma`·`-knowledge`·`-onboard`, 공통 `adapter-contract.md`, adapter 정합 테스트, AGENTS·CLAUDE·README·한글 안내·MOC·스펙 | 상류 스킬을 그대로 열지 않고 이 하네스의 경계(그래프는 근거 아님·산출물 격리·실행별 승인) 안에서 노출하기 위해. 조사 결과 한 pin 안에 런타임이 세 계층으로 갈려 있어, 배치는 아무것도 실행하지 않으므로 게이트를 설치 시점에서 실행 시점으로 옮김 — 이로써 의존성 없이 도는 `understand-knowledge`가 열림 |
| 2026-07-25 | Phase 2b-A — 외부 소스 exact-pin 설치 기반 | `.tools/PINS.md`, `install-phase2b-tools.sh`, `tree_hash.py`, `study-install`, `.gitignore`, README·한글 안내·MOC·REGISTRY | upstream 전역 installer 없이 정확한 commit만 재현 가능하게 배치하기 위해, 아카이브 바이트가 아니라 트리 내용으로 신원을 고정하고 hash·tag·runtime·pin 형식을 모두 fail-closed로 막음 |
| 2026-07-25 | 독립 리뷰 지적 반영 — 훅 정지 계약, 링크 해석, 설치 관측, 스킬 경계 | `study-wrapup`, `build_graph`, `web-capture`, `bootstrap`, `install-phase2-tools`, `defuddle`·`context7`·`paper-search`·`notebooklm-export`·`knowledge-graph`·`ingest`·`metaskill` 스킬, AGENTS | Stop 훅이 강제 continuation에서 무한 차단되던 경로를 막고, 파일명·NFC 링크 해석과 설치 성공 관측을 실제 동작에 맞추며, 이식 과정에서 빠진 폴백·경계·주입 방어를 복원 |
