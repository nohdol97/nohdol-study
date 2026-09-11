# 출처 검토·확장·구현 경계

검토일은 **2026-09-10**이다. 사용자가 선택한 공유 대화를 교육 과정 요구로 사용했으며 AI 주장, 인용 핸들, 개인 경험 가정을 독립 근거로 쓰지 않는다.

## 공유 대화에서 가져온 내용

공유 대화는 SQL/Python→Parquet→Iceberg/Delta→Spark→Kafka→dbt→품질→OTel→계보·거버넌스→Databricks→Snowflake→AI용 데이터·관측성을 제안했다. 발전하는 프로젝트 하나와 Spark·OTel·신뢰성 심화를 권했다. [로드맵](../../../docs/guides/data-observability/00-roadmap.md)과 [종합 프로젝트](../../../docs/guides/data-observability/15-capstone.md)에 반영했다.

대화에는 서로 다른 일정·진로 예측이 있다. 조정 가능한 12개월 예시로 통합하고 보장처럼 제시된 예측을 제거했다. 경험은 대화에서 추론하지 말고 실습으로 보여 줘야 한다.

## 공유 교육 과정의 세부 대응

첫 버전은 많은 주제를 목록·개요로 압축했다. 확장 과정은 기존 장 경로 안에서 개별 원리·계산 예제·실패 경계를 설명한다.

| 소스 주제군 | 세부 내용과 예제 |
|---|---|
| JOIN·윈도·재귀 CTE·그룹 집합·EXPLAIN·인덱스·격리 | [기초](../../../docs/guides/data-observability/02-sql-python-foundations.md): 행 증폭, ROWS/RANGE 출력, 재귀 종료, 소계·NULL·계획 해석 |
| 타입·dataclass·반복자·제너레이터·컨텍스트 관리자·비동기·다중 프로세스·직렬화·프로파일·pytest·로그·패키징 | [기초](../../../docs/guides/data-observability/02-sql-python-foundations.md): 런타임 검증 예제와 실행·테스트 절, Linux·Git 근거 |
| 행 그룹·열 청크·페이지·인코딩·압축·통계·읽기 제외·오브젝트 저장소 | [Parquet](../../../docs/guides/data-observability/03-parquet-object-storage.md): 파일 구조, 네 제거 단계, 같은 데이터의 후보 그룹 1 대 13 실험 |
| 스냅샷·매니페스트 목록·매니페스트·메타데이터 JSON·ACID·격리·진화·과거 조회·병합·작은 파일 | [테이블](../../../docs/guides/data-observability/04-table-formats.md): 메타데이터 추적, 지원 SQL, 동시 작성자, 삭제 표현·보존 |
| driver·executor·job·stage·task·논리·물리 계획·Catalyst·Tungsten·파티션·shuffle·join·skew·spill·AQE·UI | [Spark](../../../docs/guides/data-observability/05-spark-performance.md): 실행 원리, 조인 비교, 통제 설정 실험·인과 UI 진단 |
| 할당·재균형·오프셋·지연·ISR·복제·acks·생산자 멱등성·트랜잭션·전달·순서·역압 | [스트리밍](../../../docs/guides/data-observability/06-kafka-cdc-streaming.md): 복제본 실패 계산, 연속 진척, 트랜잭션 경계·파티션 진단 |
| Structured Streaming·늦은 이벤트·순서 뒤바뀜·체크포인트·CDC·Flink | [스트리밍](../../../docs/guides/data-observability/06-kafka-cdc-streaming.md): 마이크로 배치, 출력 모드, 워터마크·상태 수명, 스냅샷·WAL·복구 |
| 사실·차원·스타·SCD 1/2·raw·staging·intermediate·mart | [모델링](../../../docs/guides/data-observability/07-modeling-orchestration.md): 행 단위·가산성, 실행 가능한 과거·현재 귀속과 경계 실패 |
| dbt model·ref·source·test·macro·incremental·snapshot·문서·계약, Airflow·Dagster | [모델링](../../../docs/guides/data-observability/07-modeling-orchestration.md): 교체 모델·매크로, 변경 탐지 한계, 스냅샷 의미·구간·자산 운영 |
| 완전성·정확성·일관성·유일성·유효성·신선도, GX·Soda·데이터 SLO | [품질](../../../docs/guides/data-observability/08-quality-contracts-slos.md): 독립 계산, 공개 상태 머신, 담당자·근거 누락 규칙 |
| OTel resource·span·trace·context·baggage·metric·attribute·카디널리티·샘플링·Collector | [OTel](../../../docs/guides/data-observability/09-opentelemetry.md): 실제 SDK 전파, link·temporality, head/tail·유한 큐 계산 |
| Counter·gauge·histogram·summary·rate·increase·histogram_quantile·Grafana·Loki·Tempo·Jaeger | [텔레메트리 백엔드](../../../docs/guides/data-observability/10-metrics-logs-traces.md): 초기화, 백분위 계산, 스트림 파싱, 추적 연계·알림 수명 |
| Job·run·dataset·facet·카탈로그·열 계보·RBAC·ABAC·PII·마스킹·RLS·열 보안·감사 | [거버넌스](../../../docs/guides/data-observability/11-lineage-governance.md): 순환 안전 영향 예제, 개체·열 ID, 정책 강제·파생물 |
| Databricks 구조·Spark·Delta·Unity Catalog·Lakeflow·Jobs·품질·MLflow·제공 | [클라우드](../../../docs/guides/data-observability/12-cloud-platforms.md): 개발 bronze/silver/gold 코드, expectation 정책, Auto Loader, 복구·산출물 승격 |
| Snowflake SQL·Snowpark·Streams·Tasks·동적 테이블·Openflow·Horizon·계보·DMF·Cortex | [클라우드](../../../docs/guides/data-observability/12-cloud-platforms.md): stream/MERGE 트랜잭션 예제, 갱신 모드, 계산·거버넌스·AI 책임 |
| 임베딩·벡터·하이브리드·재순위화·RAG·청크·필터·의미 계층·온톨로지·그래프·MCP·도구·에이전트 | [AI 데이터](../../../docs/guides/data-observability/13-ai-ready-data-evaluation.md): 코사인·ANN, 실행 순위 결합, 버전 검색·제한 도구 실행 |
| 프롬프트·응답·토큰·비용·모델·검색·도구·에이전트 단계·평가, OTel·Langfuse·MLflow | [AI 평가](../../../docs/guides/data-observability/13-ai-ready-data-evaluation.md): 계층 지표, 평가와 사실 근거, trace 묶음·배포 관문 |
| Docker·Kubernetes·Terraform·신뢰성·복구·비용·셀프서비스 | [운영](../../../docs/guides/data-observability/14-platform-operations.md): 자원·신원 경계, 승격 묶음, 재생 예산·등록 |

## 추가한 심화 내용

| 확장 | 이유 | 학습 위치 |
|---|---|---|
| DuckDB·계획·독립 정확성 예제 | 장비 하나에서 초기 결과 검토 | 기초·Parquet |
| Debezium·소스 WAL·스키마 레지스트리 | 운영 DB·스키마 진화를 재생에 연결 | Kafka·스트리밍 |
| Flink·Trino 비교 | 연속 상태 처리와 독립 분석 질의 구분 | 스택·스트리밍·테이블 |
| Collector 유실·카디널리티·관측 범위 | 관측성 자체도 실패하는 시스템으로 취급 | OTel·지표 |
| 누락 구간 SLO 분모 | 실행·검사가 없는데 녹색인 화면 방지 | 품질·계약 |
| 명시 계보 범위·허용·거부 검사 | 발견·영향 후보·강제 구분 | 계보·거버넌스 |
| 복원·보존·백필 동시성·단위 비용 | 정확성을 실제 운영에 연결 | 플랫폼 운영 |
| 검색 인가·보류 평가 | 사용 가능하고 허용된 소스 버전에 AI 연결 | AI용 데이터 |

## 근거 표현 방식

기술 장마다 Markdown 주석에 출처 URL·검토일을 보존한다. 공개 렌더러는 주석을 제거하고 이 목록은 읽을 수 있는 일차 출처 링크를 제공한다. 제품 동작이라고 명시하지 않은 설명·예제·그림·임계값·선택 조언은 독립적인 학습 종합이다.

출처 검토는 인용 원리를 확인하며 모든 제품의 보편적 호환 배포를 검증하지 않는다. `latest`·`stable`·`current` 링크는 바뀐다. 구현 전 엔진·커넥터·프로토콜·SDK·백엔드 정확 버전과 해당 문서를 기록한다. 일부는 로컬 실행 예제, 나머지는 준비 환경이 필요한 설정 조각·안내 실습으로 표시한다.

## 일차 출처 목록

| 영역 | 일차 출처 | 검토 초점 |
|---|---|---|
| 로컬 기초 | [Python SQLite](https://docs.python.org/3/library/sqlite3.html), [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html) | 로컬 실행과 예상·관측 쿼리 작업 |
| 파일 | [Parquet file format](https://parquet.apache.org/docs/file-format/), [DuckDB Parquet](https://duckdb.org/docs/current/data/parquet/overview) | 행 그룹·열 청크·페이지·리더 연산 |
| 테이블 상태 | [Iceberg specification](https://iceberg.apache.org/spec/), [Iceberg evolution](https://iceberg.apache.org/docs/latest/evolution/), [Delta concurrency](https://docs.delta.io/concurrency-control/) | 메타데이터 계층·진화·낙관적 커밋 검증 |
| Spark | [Cluster overview](https://spark.apache.org/docs/latest/cluster-overview.html), [SQL tuning](https://spark.apache.org/docs/latest/sql-performance-tuning.html), [Structured Streaming](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) | 실행기·계획·shuffle/AQE·출력별 보장·복구 |
| 스트리밍·CDC | [Kafka 4.1 design](https://kafka.apache.org/41/design/design/), [Debezium PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html), [Flink time](https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/time/) | 순서·트랜잭션·소스 보존·이벤트 시간 진척 |
| 질의 접근 | [Trino Iceberg connector](https://trino.io/docs/current/connector/iceberg.html) | 선택 테이블 기능과 엔진·커넥터 호환성 |
| 모델링·스케줄 | [dbt tests](https://docs.getdbt.com/docs/build/data-tests), [dbt contracts](https://docs.getdbt.com/docs/mesh/govern/model-contracts), [Airflow backfill](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/backfill.html) | 데이터 검사와 형태·제약, 과거 구간 재처리 |
| 서비스 목표 | [Google SRE: implementing SLOs](https://sre.google/workbook/implementing-slos/), [alerting on SLOs](https://sre.google/workbook/alerting-on-slos/) | 사용자 결과·명시 모집단·예산 소진 |
| 계측 | [Collector configuration](https://opentelemetry.io/docs/collector/configuration/), [Collector resilience](https://opentelemetry.io/docs/collector/resiliency/), [context propagation](https://opentelemetry.io/docs/concepts/context-propagation/) | 활성 구성·유한 큐·컨텍스트·baggage |
| 지표·로그 | [Prometheus histograms](https://prometheus.io/docs/practices/histograms/), [PromQL functions](https://prometheus.io/docs/prometheus/latest/querying/functions/), [Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/), [Loki labels](https://grafana.com/docs/loki/latest/get-started/labels/) | 분위수 집계·카운터 함수·라우팅·카디널리티 |
| 계보 | [OpenLineage model](https://openlineage.io/docs/spec/object-model/), [event schema](https://openlineage.io/spec/2-0-2/OpenLineage.json) | dataset·job·run·facet·이벤트 구조 |
| Databricks | [Pipeline expectations](https://docs.databricks.com/aws/en/ldp/expectations), [Unity Catalog lineage](https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-lineage) | 유지·삭제·실패 정책과 범위·권한 한계 |
| Snowflake | [Data quality](https://docs.snowflake.com/en/user-guide/data-quality-intro), [dynamic tables](https://docs.snowflake.com/en/user-guide/dynamic-tables/overview) | DMF·expectation·에디션·target lag |
| AI 근거 | [MLflow tracing](https://mlflow.org/docs/latest/genai/tracing/), [Langfuse observability](https://langfuse.com/docs/observability/overview), [OTel GenAI conventions repository](https://github.com/open-telemetry/semantic-conventions-genai) | trace·평가 책임과 규약 버전 변화 |

## 세부 절의 추가 일차 출처

세부 출처는 2026-09-10, 과거 옵티마이저·지표 데이터 모델 참조는 2026-09-11에 검토했다. 버전 URL은 예제 범위를 정하며 가변 URL은 구현 전에 버전을 확인해야 한다.

| 동작 원리 | 일차 참조 |
|---|---|
| SQL·Python 런타임 | [PostgreSQL windows](https://www.postgresql.org/docs/current/tutorial-window.html), [recursive CTEs](https://www.postgresql.org/docs/current/queries-with.html), [isolation](https://www.postgresql.org/docs/current/transaction-iso.html), [asyncio tasks](https://docs.python.org/3/library/asyncio-task.html), [allocation tracing](https://docs.python.org/3/library/tracemalloc.html) |
| 파일·테이블 조사 | [Parquet encodings](https://parquet.apache.org/docs/file-format/data-pages/encodings/), [Iceberg Spark queries](https://iceberg.apache.org/docs/latest/spark-queries/), [Delta batch/version reads](https://docs.delta.io/delta-batch/) |
| Spark 실행 | [Spark 4.0.1 SQL tuning](https://spark.apache.org/docs/4.0.1/sql-performance-tuning.html), [memory tuning](https://spark.apache.org/docs/4.0.1/tuning.html), [UI](https://spark.apache.org/docs/4.0.1/web-ui.html), [EXPLAIN](https://spark.apache.org/docs/4.0.1/sql-ref-syntax-qry-explain.html) |
| 스트리밍 | [Kafka 4.1 producer](https://kafka.apache.org/41/configuration/producer-configs/), [consumer](https://kafka.apache.org/41/configuration/consumer-configs/), [Spark 4.0.1 state/streaming](https://spark.apache.org/docs/4.0.1/streaming/apis-on-dataframes-and-datasets.html), [Flink state/checkpoints](https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/stateful-stream-processing/) |
| 모델링·검사 | [dbt incremental](https://docs.getdbt.com/docs/build/incremental-models), [snapshots](https://docs.getdbt.com/docs/build/snapshots), [macros](https://docs.getdbt.com/docs/build/jinja-macros), [Dagster assets](https://docs.dagster.io/guides/build/assets), [GX Core](https://docs.greatexpectations.io/docs/core/introduction/), [SodaCL](https://docs.soda.io/soda-cl/soda-cl-overview.html) |
| 계측·질의 | [Python SDK](https://opentelemetry.io/docs/languages/python/instrumentation/), [propagation](https://opentelemetry.io/docs/languages/python/propagation/), [sampling](https://opentelemetry.io/docs/concepts/sampling/), [LogQL](https://grafana.com/docs/loki/latest/query/log_queries/), [TraceQL](https://grafana.com/docs/tempo/latest/traceql/) |
| 접근 강제 | [PostgreSQL row policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html), [Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/) |
| Databricks 구현 | [Pipeline Python](https://docs.databricks.com/aws/en/ldp/developer/python-dev), [Auto Loader](https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/), [job repair](https://docs.databricks.com/aws/en/jobs/repair-job-failures) |
| Snowflake 구현 | [Streams](https://docs.snowflake.com/en/user-guide/streams-intro), [Tasks](https://docs.snowflake.com/en/user-guide/tasks-intro), [refresh modes](https://docs.snowflake.com/en/user-guide/dynamic-tables/refresh-modes), [micro-partitions](https://docs.snowflake.com/en/user-guide/tables-clustering-micropartitions), [Snowpark DataFrames](https://docs.snowflake.com/en/developer-guide/snowpark/python/working-with-dataframes) |
| AI 검색·도구 | [pgvector](https://github.com/pgvector/pgvector), [RRF](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion), [MCP tools, 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) |
| 설계 배경·지표 의미 | [Catalyst design](https://www.databricks.com/blog/2015/04/13/deep-dive-into-spark-sqls-catalyst-optimizer.html), [Tungsten design](https://www.databricks.com/blog/2015/04/28/project-tungsten-bringing-spark-closer-to-bare-metal.html) (과거 설계 근거이며 현재 벤치마크가 아님), [OTel metric data model](https://opentelemetry.io/docs/specs/otel/metrics/data-model/) |

## 지나치게 넓은 해석 바로잡기

Kafka·Spark가 모든 외부 효과를 정확히 한 번 만들지는 않는다. 스키마 계약은 업무 품질을 입증하지 않는다. 새 행 하나는 완전성의 근거가 아니다. 자동 계보에는 범위 한계가 있다. 카탈로그 태그는 접근 검사가 아니다. 과거 조회에는 메타데이터·데이터 보존이 필요하다. 모델 평가 점수는 답의 진실성을 독립 입증하지 않는다.

이 구분은 구현을 피할 이유가 아니라 엔지니어링 모델의 일부이며 전 과정의 실패 실습을 이끈다.

## 스스로 설명해 보기

사실 원리 하나, 학습 권장 하나, 로컬 예제 하나를 골라 각각 필요한 근거와 공유 AI 대화가 이를 대신하지 못하는 이유를 설명한다. [로드맵](../../../docs/guides/data-observability/00-roadmap.md)에서 다음 구현을 계획한다.

<!-- source: https://chatgpt.com/share/6aa266f6-db88-83ee-a8d7-3e7aa8e0821d?ogimg=plain | checked: 2026-09-10 | user-selected curriculum brief, successfully read from its public share payload -->
