# 데이터·관측성 엔지니어링: 이벤트에서 신뢰할 수 있는 AI까지

데이터의 출처, 결과를 신뢰할 근거, 실패 지점, 영향을 받는 대상, 복구 방법을 설명하는 능력을 기른다. 하나의 시스템을 발전시키며 분산 데이터 처리, 텔레메트리, 데이터 신뢰성, 거버넌스, AI를 연결하는 과정이다.

## 처음 보는 사람을 위한 출발점

HTTP 200을 반환하지만 어제 매출을 보여 주는 주문 대시보드를 생각해 보자. API는 가용하지만 데이터 제품은 실패하고 있다. 같은 테이블을 사용하는 AI 도우미라면 빠른 모델이 오래된 답을 자신 있게 내놓는다. 두 상황을 진단하려면 개별 도구를 넘어 데이터의 흐름을 따라가야 한다.

| 처음 만나는 말 | 학습용 쉬운 뜻 | 왜 필요한가요 · 언제 쓰나요 |
|---|---|---|
| 데이터 제품(data product) | 사용자, 의미, 담당자, 전달 약속이 정의된 데이터셋 | 데이터셋의 의미·소유자·전달에 관해 소비자가 의지할 약속을 제공한다. |
| 파이프라인(pipeline) | 데이터를 수집·변환·검증·공개하는 단계들 | 수집부터 공개까지를 실패·출력을 확인할 수 있는 단계로 조직한다. |
| 관측성(observability) | 시스템 내부 동작을 설명하는 데 도움이 되는 근거 | 실행 중인 시스템 내부의 근거로 장애와 동작 변화를 설명한다. |
| 데이터 신뢰성(data reliability) | 합의한 시간과 복구 범위 안에서 필요한 정확성·완전성을 갖춘 데이터를 전달하는 것 | 품질·전달 검사를 데이터 소비자가 실제로 필요로 하는 조건에 맞춘다. |
| 계보(lineage) | 입력, 처리 실행, 출력 사이의 관계 기록 | 데이터 변경·실행 실패 때 상위 입력과 하위 영향을 찾는다. |
| SLI / SLO | 측정한 결과 / 그 결과에 대해 합의한 목표 | 소비자에게 한 서비스 약속을 측정 가능한 결과와 합의한 목표로 표현한다. |

셸 명령 실행, 작은 Python 프로그램 읽기, 기본 SQL 작성 능력이 필요하다. 처음이라면 첫 달을 기초 장에 쓴다. Kafka 경험은 도움이 되지만 특정 회사, 직책, 운영 경험을 전제하지 않는다.

## 앞으로 발전시킬 시스템

```mermaid
flowchart LR
  S[Synthetic orders and CDC] --> K[Kafka]
  K --> P[Spark processing]
  P --> L[Parquet and Iceberg or Delta]
  L --> D[dbt models and quality gates]
  D --> R[Authorized retrieval and AI]
  P -. run and dataset identity .-> O[Telemetry and lineage]
  D -. quality outcomes .-> O
  R -. request and evaluation evidence .-> O
  O --> I[Impact analysis and recovery]
```

화살표는 미리 설치된 연동이 아니라 교육 과정의 설계다. 각 연결에는 호환되는 커넥터, 식별자 대응, 실패 시험이 필요하다.

## 학습 순서

| 단계 | 장 | 관찰 가능한 결과 |
|---|---|---|
| 1 | [스택 선택](../../../docs/guides/data-observability/01-stack-and-architecture.md) | 각 구성 요소의 필요성과 미룬 대안을 설명한다. |
| 2 | [SQL·Python·실행](../../../docs/guides/data-observability/02-sql-python-foundations.md) | 중복·NULL·조인 상황에서도 올바른 합계를 계산한다. |
| 3 | [Parquet와 오브젝트 스토리지](../../../docs/guides/data-observability/03-parquet-object-storage.md) | 읽은 바이트, 파일 배치, 읽기 제외(pruning)를 설명한다. |
| 4 | [Iceberg와 Delta](../../../docs/guides/data-observability/04-table-formats.md) | 커밋한 테이블 버전을 파일과 복구 경계까지 추적한다. |
| 5 | [Spark 내부 동작](../../../docs/guides/data-observability/05-spark-performance.md) | 실행 계획과 태스크 분포로 느린 단계를 진단한다. |
| 6 | [Kafka·CDC·스트리밍](../../../docs/guides/data-observability/06-kafka-cdc-streaming.md) | 이중 집계하거나 늦은 이벤트를 숨기지 않고 재생을 복구한다. |
| 7 | [모델링·dbt·오케스트레이션](../../../docs/guides/data-observability/07-modeling-orchestration.md) | 한 구간을 재처리하고 공개된 데이터 마트를 대사한다. |
| 8 | [품질·계약·데이터 SLO](../../../docs/guides/data-observability/08-quality-contracts-slos.md) | 잘못된 공개를 차단하고 관측 누락을 탐지한다. |
| 9 | [OpenTelemetry](../../../docs/guides/data-observability/09-opentelemetry.md) | 파이프라인 실행을 트레이스·로그·차원이 제한된 지표로 연결한다. |
| 10 | [Prometheus·Grafana·텔레메트리 운영](../../../docs/guides/data-observability/10-metrics-logs-traces.md) | 데이터셋 이상과 텔레메트리 장애를 따로 조사한다. |
| 11 | [계보·카탈로그·거버넌스](../../../docs/guides/data-observability/11-lineage-governance.md) | 영향받는 사용자를 찾고 실행 시 접근 권한을 강제한다. |
| 12 | [Databricks와 Snowflake](../../../docs/guides/data-observability/12-cloud-platforms.md) | 같은 계약을 다시 구현하고 측정한 동작을 비교한다. |
| 13 | [AI용 데이터와 평가](../../../docs/guides/data-observability/13-ai-ready-data-evaluation.md) | 답을 권한이 있는 출처 버전까지 추적하고 평가한다. |
| 14 | [플랫폼 운영](../../../docs/guides/data-observability/14-platform-operations.md) | 복원·릴리스 롤백·비용 귀속을 시연한다. |
| 15 | [종합 프로젝트와 장애 훈련](../../../docs/guides/data-observability/15-capstone.md) | 복구 근거를 갖춘 재현 가능한 포트폴리오를 만든다. |
| 참고 | [출처 검토와 범위](../../../docs/guides/data-observability/16-source-review.md) | 공유 대화와 기술적 근거를 구분한다. |

## 각 스택 안의 동작 원리를 학습하기

각 기술 장은 아래 세부 원리를 구분해 다룬다. 한 절을 읽고 예제를 계산하거나 실행한 뒤 실패 사례를 설명하고 다음으로 넘어간다. 출처 목록은 공유 대화의 세부 주제와 각 장을 연결한다. 이름만 알아보는 것으로는 부족하다.

| 학습 단위 | 세부 내용 |
|---|---|
| [SQL과 Python](../../../docs/guides/data-observability/02-sql-python-foundations.md) | 조인 행 증폭, 윈도 프레임, 재귀 CTE, 그룹 집합, 실행 계획·격리 수준, 검증·제너레이터·비동기·프로세스·메모리·테스트 |
| [파일 배치](../../../docs/guides/data-observability/03-parquet-object-storage.md) | 행 그룹·청크·페이지, 인코딩과 압축, 읽기 제외 계층, 정렬·교차 배치 실험, 파티션·파일 경계 |
| [테이블 프로토콜](../../../docs/guides/data-observability/04-table-formats.md) | Iceberg 메타데이터 추적, Delta 로그·버전 읽기, 낙관적 충돌, 진화, 삭제, 압축 병합·보존 |
| [Spark 실행](../../../docs/guides/data-observability/05-spark-performance.md) | Catalyst·Tungsten, driver·job·stage·task, shuffle·파티션 제어, 세 가지 조인, 메모리·spill·skew, AQE·UI 진단 |
| [스트리밍 시스템](../../../docs/guides/data-observability/06-kafka-cdc-streaming.md) | 복제본·ISR·acks, 멱등성·트랜잭션, 할당·재균형·오프셋, CDC, 출력 모드, 워터마크·상태, Flink·역압 |
| [모델과 스케줄링](../../../docs/guides/data-observability/07-modeling-orchestration.md) | 사실·차원 테이블의 행 단위, Type 1/2 이력, ref·source·매크로, 증분 교체, 스냅샷·테스트·계약, Airflow·Dagster·과거 구간 재처리 |
| [데이터 신뢰성](../../../docs/guides/data-observability/08-quality-contracts-slos.md) | 여섯 품질 차원, 측정 가능한 분모, 공개 상태 머신, 검사 도구, SLO 소진·근거 누락 |
| [OpenTelemetry](../../../docs/guides/data-observability/09-opentelemetry.md) | 리소스·스코프·span, 컨텍스트·baggage·link, 실제 SDK 전파, 지표 계측기·시간 집계 방식, head/tail 샘플링·Collector 큐 |
| [텔레메트리 백엔드](../../../docs/guides/data-observability/10-metrics-logs-traces.md) | 카운터 초기화, rate·increase, 히스토그램 계산, 카디널리티, LogQL, 트레이스 검색, Grafana 연계·알림 수명 주기 |
| [거버넌스](../../../docs/guides/data-observability/11-lineage-governance.md) | 데이터셋·작업·실행·facet, 열 계보, 순환에 안전한 영향 추적, RBAC·ABAC, 행·열 정책 강제, 분류·감사 |
| [Databricks와 Snowflake](../../../docs/guides/data-observability/12-cloud-platforms.md) | 실행 환경을 명시한 파이프라인 예제, expectations, Auto Loader, Jobs·MLflow, Streams·MERGE, Tasks, 동적 갱신, Snowpark, DMF·Horizon·Cortex |
| [AI 데이터와 평가](../../../docs/guides/data-observability/13-ai-ready-data-evaluation.md) | 코사인·ANN, 하이브리드 결합·재순위화, 청크·인덱스 버전, 의미 계층·온톨로지·그래프, MCP·도구·에이전트, 계층별 평가 |
| [플랫폼 전달](../../../docs/guides/data-observability/14-platform-operations.md) | 런타임·신원 경계, 릴리스 묶음, 용량·재생 계산, 복구, 단위 경제성, 데이터셋 등록 |

바로 로컬에서 학습하려면 SQL·모델링·품질·지표·계보·검색 장의 표시된 Python 예제를 실행한다. 가상 입력과 정확한 예상 출력을 사용한다. 로컬 의존성을 사용할 수 있으면 DuckDB/dbt와 메모리 내 OTel SDK 실습도 추가한다. Spark, 테이블 엔진, 관리형 플랫폼 실습에는 별도 사전 조건과 예상 결과를 명시한다. 사용자 인프라에서 실행됐다고 가정하지 않는다.

## 12개월 실행 계획

주당 약 8~10시간 집중 학습을 가정한 계획 예시이며 전문성을 보장하지 않는다. 입증한 결과에 따라 진도를 정한다. Kafka나 관측성 경험이 있으면 장별 실습부터 시도하고 절약한 시간을 Spark 내부 동작과 데이터 정확성에 쓴다.

| 월 | 주요 초점 | 완료 산출물 |
|---|---|---|
| 1 | SQL·Python·Linux·Git, 작은 스크립트 계측 | 정확성 예제와 재현 가능한 실행 매니페스트 |
| 2 | Parquet·오브젝트 스토리지·테이블 형식 하나 | 파일 배치 벤치마크와 스냅샷 복구 기록 |
| 3–4 | Spark SQL·shuffle·skew·상태·장애 진단 | 변경 전후 계획과 측정으로 설명한 성능 |
| 5 | Kafka·CDC·이벤트 시간·재생 | 커밋 출력 대사를 포함한 실패 행렬 |
| 6 | dbt·오케스트레이션·데이터 계약 | 명시적 품질 검사를 통과해야 공개되는 마트 |
| 7–8 | OTel·Prometheus·Grafana·트레이스·로그 | 종단 간 사고 및 텔레메트리 유실 훈련 |
| 9 | OpenLineage·카탈로그·접근 정책 | 영향 그래프, 담당자 대응, 허용·거부 검사 |
| 10–11 | Databricks 구현과 운영 | 동등한 출력·권한·복구·비용 보고서 |
| 12 | AI 데이터 전달과 평가 | 버전이 있는 검색 자료 집합과 평가된 답변 트레이스 |
| 후속 | Snowflake 비교, 필요 시 Flink·Trino | 같은 워크로드에 대한 아키텍처 비교 |

기본 계측은 첫 달에 시작하고 7~8월에 심화한다. 마지막까지 근거 수집을 미루면 앞선 성능 실험을 해석하기 어렵다.

매주 원리 하나를 읽고 설명하고, 기능 한 부분을 구현하고, 실패 하나를 주입한 뒤 근거가 입증하는 내용을 기록한다. 마지막 학습 시간은 정리와 이전 가정 재검토에 남겨 둔다.

## 완료

이벤트 경로를 소스 오프셋에서 테이블 스냅샷, 마트, 검색 인덱스, 답까지 재구성할 수 있어야 한다. 서비스 정상과 데이터셋 정상을 구분하고 재생 정확성을 시연하며 계보로 영향받는 담당자를 찾고 시험한 절차로 복구할 수 있어야 한다. 포트폴리오에는 화면 캡처뿐 아니라 측정값과 한계도 포함한다.

## 처음 이해했는지 확인

1. API가 정상이고 소비자 지연이 0이어도 데이터는 틀릴 수 있는가? 변환·공개·소스 누락 사례를 설명해 보자.
2. trace ID로 재현 가능한 테이블 버전을 식별할 수 없는 이유는 무엇인가? 트레이스는 실행을 식별하며, 입력 스냅샷과 처리 리비전은 읽은 것과 수행한 일을 식별한다.
3. 다른 클라우드를 비교하기 전에 하나를 깊이 배우는 이유는 무엇인가? 비교가 의미 있으려면 구체적인 워크로드와 실패 계약이 필요하다.

## 운영 판단으로 확장하기

구성 요소를 추가할 때마다 해결하는 문제, 새로 생기는 실패, 담당자, 채택 전에 필요한 근거를 말해 본다. 전문성이란 제약 안에서 결정을 내리고 그 근거를 설명하는 능력이며 읽기 목록 완주는 준비일 뿐이다.

사전 학습은 기존 [PostgreSQL 로드맵](../../content/postgresql/00-roadmap.md), [관측성과 SRE 로드맵](../../content/observability-sre/00-roadmap.md), [AI 플랫폼 수명 주기](../../content/ai-transformation-platform/02-mlops-llmops-lifecycle.md)를 참고한다.

<!-- source: https://chatgpt.com/share/6aa266f6-db88-83ee-a8d7-3e7aa8e0821d?ogimg=plain | checked: 2026-09-10 | curriculum input only; not independent factual evidence -->
