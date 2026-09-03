# ADR 009 — 공개 문서 루트는 학습 영역을 나누고 주제는 영역에 정확히 하나만 속한다

- 날짜: 2026-09-03
- 상태: 활성
- 대상: `docs-site/catalog.json`, `docs-site/build.mjs`, `docs-site/src/`
- 관련 스펙: [Public Docs Gateway](../specs/2026-09-03-public-docs-gateway.md), [DevOps 공개 학습 경로](../specs/2026-09-03-infra-specialist-public-learning-path.md), [AIOps 공개 학습 경로](../specs/2026-09-03-aiops-public-learning-path.md)
- 부분 대체: [ADR 008](008-public-docs-gateway.md)의 첫 화면에서 모든 topic을 직접 나열하는 구조

## 맥락

공개 사이트는 Kubernetes에서 시작해 당시 `Infra Specialist`로 부르던 13개 topic으로 확장됐다. 이제 이 학습 영역의 이름은 인프라뿐 아니라 백엔드 운영과 배포 수명주기를 포함하는 `DevOps`다. 그러나 공개 `docs-site`는 DevOps 전용 제품이 아니다. AIOps를 추가하면서 모든 topic을 같은 평면에 놓으면 학습 영역과 선수 관계가 섞이고, 이후 다른 영역이 추가될 때 첫 화면이 topic 목록으로 다시 비대해진다.

개인 `vault/`에는 인프라·AIOps에 참고할 검증 노트가 있지만 공개 범위가 아니다. 구조와 주제 선택에는 활용할 수 있어도 자동 게시하거나 경로를 카탈로그에 넣어서는 안 된다.

## 결정

카탈로그에 `paths` 계층을 추가하고 루트는 학습 영역 카드만 보여 준다. 현재 영역은 `infra`와 `aiops` 두 개다. 각 영역이 명시적인 `topicIds` 순서를 소유하고, 모든 topic은 정확히 한 영역에 속해야 한다.

- `#path=<id>`는 영역의 topic 순서와 공통 학습 사다리를 보여 준다.
- `#topic=<id>`와 `#doc=<id>`의 기존 직접 링크는 유지한다.
- 빌드는 없는 topic 참조, 두 영역에 중복 배치된 topic, 어느 영역에도 속하지 않은 topic을 거부한다.
- 검색은 모든 영역의 공개 문서를 대상으로 하며 결과에 영역과 topic을 함께 표시한다.
- topic 간 선수·후속 관계는 Markdown 상대 링크로 연결하고 빌드 시 document route로 변환한다.
- 공개 범위는 계속 명시적 catalog와 Git 추적 Markdown으로 제한한다. `vault/`, `REGISTRY.md`, `_workspace/`를 자동 발견하거나 공개하지 않는다.

## 현재 콘텐츠 경계

DevOps는 기존 13개 topic에 `트래픽 제어와 서비스 복원력`, `운영 가능한 백엔드 엔지니어링`을 추가해 15개 topic·57개 문서가 된다. 백엔드 topic은 vault의 81개 노트를 자동 공개하지 않고 여섯 축(API 계약, 불변식·transaction, 동시성·용량, 분산 workflow, cache·성능, 호환 배포)으로 재구성해 기존 network·PostgreSQL·messaging·security·traffic·AIOps 문서로 연결한다.

AIOps는 `AI Specialist 핵심 모델과 응용`, `AI Transformation 운영 플랫폼`, `신호와 운영 토폴로지`, `이상 탐지와 근거 기반 진단`, `승인된 자동 복구와 운영 학습` 5개 topic·20개 문서다. AI Specialist의 다섯 교육 모듈과 AI Transformation의 네 운영 필러를 빠짐없이 상위 장으로 옮기되 개인 강의 원문·vault 문장을 게시하지 않는다. 모델·검색·GPU·MLOps·에이전트 실행 결과가 incident evidence와 평가 dataset 사이를 오가도록 연결하고, 진단과 조치 문서는 DevOps의 traffic·GitOps·security·reliability·backend 문서로 돌아간다. 세 vault 영역의 개별 항목이 큰 축 아래에서 사라지지 않도록 각 roadmap은 전체 내용 연결표를 갖고, build test는 각 표의 경계 항목을 검사한다.

## 결과

- 루트 크기는 topic 수가 아니라 학습 영역 수를 따른다.
- DevOps와 AIOps가 독립 진입점을 가지면서 내부 문서 링크로 지식을 공유한다.
- 새로운 영역은 path 한 개와 완결된 topic 묶음으로 추가할 수 있다.
- 기존 URL fragment의 topic·document 직접 링크는 깨지지 않는다.
- catalog 검증이 영역 배치 누락과 중복을 CI에서 막는다.
