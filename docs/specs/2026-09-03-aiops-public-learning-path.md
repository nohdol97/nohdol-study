# AIOps 공개 학습 경로 스펙

- 날짜: 2026-09-03
- 상태: 구현됨
- 관련 결정: [ADR 009](../adr/009-public-docs-root-learning-paths.md)
- 선수 구현: [Public Docs Gateway](2026-09-03-public-docs-gateway.md), [DevOps 공개 학습 경로](2026-09-03-infra-specialist-public-learning-path.md)

## 목표

- 공개 문서 루트에서 DevOps와 별도의 AIOps 학습 영역을 제공한다.
- AI Specialist의 모델·응용 전체 지도와 AI Transformation의 운영 플랫폼 전체 지도를 선수 경로로 제공하고 `모델·검색·에이전트 → 배포 bundle → 운영 증거 계약 → 탐지·상관·진단 → 승인된 조치 → 사후 학습` 폐루프로 가르친다.
- 기존 DevOps의 Observability/SRE·Kubernetes·GitOps·Security·Traffic·Reliability 문서를 선수·후속 링크로 재사용해 중복을 피한다.
- AI가 만든 후보와 실제 evidence, 사람의 승인과 상태 변경 권한, 명령 성공과 사용자 결과 회복을 구분한다.

## 비목표

- 개인 `vault/` 노트의 자동 게시나 문장 복제
- 특정 observability·AIOps vendor 제품의 전체 reference
- 모델 accuracy 하나로 root cause나 remediation 권한을 확정하는 설계
- 운영 credential이 필요한 live 변경 실습
- 사람 없는 완전 자율 운영을 현재 완료 상태로 주장하는 일

## 공개 구조

| 순서 | topic ID | 공개 제목 | 책임 |
|---|---|---|---|
| A01 | `ai-specialist-core` | AI Specialist 핵심 모델과 응용 | LLM·Vision/생성·On-device·시계열/추천·RAG/GraphRAG/NL2SQL/MCP의 입력·모델·평가·target 계약 |
| A02 | `ai-transformation-platform` | AI Transformation 운영 플랫폼 | GPU·분산 학습·LLM serving, MLOps/LLMOps, AI DevOps/FinOps, enterprise agent·identity·sandbox·durable operation |
| A03 | `aiops-foundations` | AIOps 신호와 운영 토폴로지 | metric·log·trace·event·change와 service·deployment·resource 관계를 incident bundle로 연결 |
| A04 | `aiops-diagnosis` | 이상 탐지와 근거 기반 장애 진단 | symptom rule, anomaly candidate, alert grouping, evidence retrieval, RCA category와 abstain을 단계별 평가 |
| A05 | `aiops-remediation` | 승인된 자동 복구와 운영 학습 | recommend·approve-to-run·auto-run 등급, operation 상태 머신, idempotency·abort·rollback·outcome verification |

운영 폐루프 3개 topic은 `00-roadmap.md`, `01-*` 개념 장, `02-*` 안내형 실습 장의 3개 문서를 가진다. 범위가 넓은 두 허브는 roadmap과 모듈·필러별 장을 둔다. AI Specialist는 roadmap 포함 6개, AI Transformation은 roadmap 포함 5개로 전체 5개 topic·20개 문서다.

## 연결 계약

- A01은 5개 AI Specialist 모듈을 모두 포함하고 model·retrieval 결과를 A02의 bundle·평가 단위와 A03의 evidence 입력으로 연결한다.
- A02는 4개 AI Transformation 필러를 모두 포함하고 Kubernetes·GitOps·security·backend를 기반으로 model·prompt·index·tool·policy·runtime을 versioned bundle로 만든다.
- A03은 Infra의 `observability-sre`, Kubernetes 관측 장과 GitOps change revision, A01·A02의 model·bundle ID를 선수로 연결한다.
- A04는 A03 incident bundle을 입력으로 받고 traffic retry·overflow와 deployment cohort를 원인 후보 예시로 연결한다.
- A05는 A04 진단 후보를 받되 실행 권한은 별도 gate로 분리하고, Infra의 backend·traffic·GitOps·security·reliability 문서로 action·identity·rollback·SLO를 연결한다.
- 모든 상대 링크는 build 결과에서 `#doc=<id>` 내부 route로 해석되어야 한다.

## 설명과 근거 계약

- material fact는 OpenTelemetry·Prometheus·Kubernetes·Gateway API 같은 공식 문서 또는 원 논문에서 확인하고 source comment에 URL·확인일·version을 남긴다.
- private vault는 주제 발견과 기존 지식 탐색에만 사용하고 공개 source로 인용하지 않는다.
- anomaly score는 incident나 root cause가 아니며, 시간 상관은 인과가 아니다.
- LLM 설명은 evidence ID, 후보 category, 반증·누락과 abstain을 갖는 출력 계약 뒤에 둔다.
- 자동화는 진단 confidence와 분리된 target·scope·precondition·approval·abort·rollback·verification 계약을 가진다.

## 실습 안전 계약

- 실습은 합성 JSON·YAML만 사용하는 Local 또는 Plan only 등급이다.
- 실제 cluster·cloud·ticket·monitoring state를 변경하지 않는다.
- 임시 파일을 만들면 정확한 `/tmp/aiops-incident-lab` target과 cleanup을 명시한다.
- dry-run이 검증하는 API·구조 범위와 검증하지 못하는 사용자 결과·외부 dependency를 구분한다.
- 결과 불명 operation은 blind retry하지 않고 실제 상태 reconciliation으로 전이한다.

## 구현 완료 기준

- catalog 루트에는 `infra`, `aiops` 두 path가 있고 모든 topic은 정확히 하나에 배치된다.
- AIOps 5개 topic·20개 문서가 Git 추적 상태이며 검색·직접 URL로 접근된다.
- AI Specialist roadmap은 49개 노트의 LLM·효율화·Vision·생성·On-device·시계열·추천·RAG·구조 질의/MCP 항목을, AI Transformation roadmap은 허브와 49개 하위 노트의 infrastructure·serving·MLOps/LLMOps·DevOps/FinOps·enterprise agent·edge 항목을 빠짐없이 공개 장에 배치한다.
- 각 topic은 관계·상태를 보여 주는 Mermaid와 JSON·YAML·shell 중 하나의 검토 가능한 예시를 가진다.
- 각 roadmap은 처음 보는 사람의 문제 상황, 쉬운 용어 표, 학습 순서, 완료 기준, 확인 문제와 운영 판단을 가진다.
- 각 상세 장은 용어 또는 준비 조건을 먼저 설명하고 결과가 증명하는 범위와 남은 불확실성을 구분한다.
- AIOps와 DevOps 사이의 대표 교차 링크를 build test가 확인한다.
- source comment는 공개 HTML에서 제거되고 private path는 계속 거부된다.
- 데스크톱·모바일에서 path → topic → document 탐색이 잘리지 않는다.
