# Source review, extensions, and implementation boundaries

Reviewed on **2026-09-10**. This course uses the user-selected shared conversation as a curriculum brief. It does not use the conversation's AI-generated claims, citation handles, or assumptions about personal experience as independent evidence.

## What the shared conversation contributed

The conversation proposed a sequence from SQL/Python through Parquet, Iceberg/Delta, Spark, Kafka, dbt, data quality, OpenTelemetry, lineage/governance, Databricks, Snowflake, AI-ready data, and AI observability. It also recommended one evolving project and particular depth in Spark, OpenTelemetry, and data reliability. These ideas are preserved in the [roadmap](00-roadmap.md) and [capstone](15-capstone.md).

The conversation contains different suggested calendars and career predictions. This course consolidates the calendar into an adjustable twelve-month example and removes predictions presented as guarantees. Existing experience should be demonstrated with the exercises, not inferred from the shared conversation.

## Detailed coverage of the shared curriculum

The first version compressed many of these topics into lists or overview paragraphs. The expanded course gives them separate mechanism explanations, worked examples, and failure boundaries within the existing chapter routes.

| Source topic group | Detailed coverage and example |
|---|---|
| JOIN, window functions, recursive CTE, grouping sets, EXPLAIN, indexes/isolation | [Foundations](02-sql-python-foundations.md): multiplicity, ROWS/RANGE output, recursive termination, subtotals/nulls and plan interpretation |
| Typing/dataclass, iterator/generator, context manager, async, multiprocessing, serialization, profiling, pytest, logging, packaging | [Foundations](02-sql-python-foundations.md): runtime validation fixture and separate runtime/testing sections; Linux/Git execution evidence |
| Row group, column chunk, page, encoding/compression, statistics, pruning, object storage | [Parquet](03-parquet-object-storage.md): file anatomy, four elimination steps, equal-data 1-versus-13 candidate-group experiment |
| Snapshot, manifest list/manifest, metadata JSON, ACID, isolation, evolution, time travel, compaction/small files | [Tables](04-table-formats.md): metadata walk, supported inspection SQL, concurrent writers, delete representations and retention |
| Driver/executors, jobs/stages/tasks, logical/physical plan, Catalyst/Tungsten, partition/shuffle, joins, skew/spill/AQE/UI | [Spark](05-spark-performance.md): execution mechanics, join comparison, controlled settings experiment and causal UI diagnosis |
| Assignment/rebalance/offset/lag, ISR/replication/acks, producer idempotence/transactions, delivery/ordering/backpressure | [Streaming](06-kafka-cdc-streaming.md): replica failure arithmetic, contiguous progress, transaction boundaries and per-partition diagnosis |
| Structured Streaming, late/out-of-order events, checkpoints, CDC, Flink | [Streaming](06-kafka-cdc-streaming.md): micro-batches, output modes, watermark/state lifetime, snapshot/WAL and recovery cases |
| Fact/dimension/star, SCD 1/2, raw/staging/intermediate/mart | [Modeling](07-modeling-orchestration.md): grain and additivity, runnable historical/current attribution and boundary failure |
| dbt model/ref/source/test/macro/incremental/snapshot/documentation/contract; Airflow/Dagster | [Modeling](07-modeling-orchestration.md): replacement model and macro, change-detection limits, snapshot semantics and interval/asset operations |
| Completeness, accuracy, consistency, uniqueness, validity, freshness; GX/Soda; dataset SLO | [Quality](08-quality-contracts-slos.md): independently calculated dimensions, publication state machine, ownership and missing-evidence rules |
| OTel resource/span/trace/context/baggage/metric/attribute/cardinality/sampling; Collector pipeline | [OTel](09-opentelemetry.md): real SDK propagation fixture, links/temporality, head/tail policies and bounded queue math |
| Counter/gauge/histogram/summary, rate/increase/histogram_quantile, Grafana/Loki/Tempo/Jaeger | [Telemetry backends](10-metrics-logs-traces.md): resets, percentile calculation, stream parsing, trace correlation and alert lifecycle |
| Job/run/dataset/facets, catalog/column lineage; RBAC/ABAC/PII/masking/RLS/column security/audit | [Governance](11-lineage-governance.md): cycle-safe impact fixture, entity/column identity, policy enforcement and derivatives |
| Databricks architecture, Spark/Delta/Unity Catalog/Lakeflow/Jobs/quality/MLflow/serving | [Cloud platforms](12-cloud-platforms.md): development bronze/silver/gold code, expectation policies, Auto Loader, repair and artifact promotion |
| Snowflake SQL/Snowpark, Streams/Tasks, dynamic tables, Openflow, Horizon/lineage/DMF, Cortex | [Cloud platforms](12-cloud-platforms.md): stream/MERGE transaction fixture, refresh modes, compute, governance and AI responsibilities |
| Embedding/vector/hybrid/reranking, RAG/chunking/filtering, semantic layer/ontology/graph, MCP/tools/agents | [AI data](13-ai-ready-data-evaluation.md): cosine/ANN, runnable rank fusion, versioned retrieval and bounded tool execution |
| Prompt/response/token/cost/model/retrieval/tool/agent-step/evaluation; OTel/Langfuse/MLflow | [AI evaluation](13-ai-ready-data-evaluation.md): per-layer metrics, judged versus factual evidence, trace bundles and release gates |
| Docker/Kubernetes/Terraform, reliability, recovery, cost and self-service platform | [Operations](14-platform-operations.md): resource/identity boundaries, promotion bundles, replay-budget arithmetic and dataset registration |

## Added depth

| Extension | Reason | Where to study |
|---|---|---|
| DuckDB, query plans, independent correctness fixtures | Make early results inspectable on one machine | Foundations and Parquet |
| Debezium, source WAL, schema registry | Connect operational databases and schema evolution to replay | Kafka and streaming |
| Flink and Trino comparison | Separate continuous state processing from independent analytical query access | Stack, streaming, and tables |
| Collector loss, cardinality, telemetry coverage | Treat observability as a system that can itself fail | OTel and metrics |
| Missing-interval SLO denominators | Avoid green dashboards when jobs or checkers never ran | Quality and contracts |
| Explicit lineage coverage and allow/deny checks | Separate discovery, impact candidates, and enforcement | Lineage and governance |
| Restore, retention, backfill concurrency, unit cost | Connect correctness to realistic operations | Platform operations |
| Retrieval authorization and held-out evaluations | Keep AI grounded in usable, permitted source versions | AI-ready data |

## How evidence is represented

Each technical chapter retains source URLs and the review date in Markdown comments. The public renderer removes these metadata comments, while this source register provides readable primary-source links. Explanations, fixtures, diagrams, thresholds, and selection advice are independent teaching synthesis unless explicitly described as a product behavior.

The source review verifies the cited mechanisms, not a universally compatible deployment of all named products. Mutable `latest`, `stable`, and `current` links can change. Before implementation, record exact engine, connector, protocol, SDK, and backend versions and use their corresponding documentation. Some examples are executable local fixtures; others are explicitly labeled configuration fragments or guided exercises requiring a prepared environment.

## Primary-source register

| Area | Primary sources | Review focus |
|---|---|---|
| Local foundations | [Python SQLite](https://docs.python.org/3/library/sqlite3.html), [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html) | Local execution and estimated versus observed query work |
| Files | [Parquet file format](https://parquet.apache.org/docs/file-format/), [DuckDB Parquet](https://duckdb.org/docs/current/data/parquet/overview) | Row groups, column chunks, pages and reader operations |
| Table state | [Iceberg specification](https://iceberg.apache.org/spec/), [Iceberg evolution](https://iceberg.apache.org/docs/latest/evolution/), [Delta concurrency](https://docs.delta.io/concurrency-control/) | Metadata hierarchy, evolution, optimistic commit validation |
| Spark | [Cluster overview](https://spark.apache.org/docs/latest/cluster-overview.html), [SQL tuning](https://spark.apache.org/docs/latest/sql-performance-tuning.html), [Structured Streaming](https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html) | Executors, plans, shuffle/AQE, sink-dependent guarantees and recovery |
| Streaming and CDC | [Kafka 4.1 design](https://kafka.apache.org/41/design/design/), [Debezium PostgreSQL](https://debezium.io/documentation/reference/stable/connectors/postgresql.html), [Flink time](https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/time/) | Ordering/transactions, source retention and event-time progress |
| Query access | [Trino Iceberg connector](https://trino.io/docs/current/connector/iceberg.html) | Engine/connector compatibility must be checked for the chosen table features |
| Modeling and scheduling | [dbt tests](https://docs.getdbt.com/docs/build/data-tests), [dbt contracts](https://docs.getdbt.com/docs/mesh/govern/model-contracts), [Airflow backfill](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/backfill.html) | Data checks versus shape/constraints; historical interval reprocessing |
| Service objectives | [Google SRE: implementing SLOs](https://sre.google/workbook/implementing-slos/), [alerting on SLOs](https://sre.google/workbook/alerting-on-slos/) | Consumer outcomes, explicit populations and budget burn |
| Instrumentation | [Collector configuration](https://opentelemetry.io/docs/collector/configuration/), [Collector resilience](https://opentelemetry.io/docs/collector/resiliency/), [context propagation](https://opentelemetry.io/docs/concepts/context-propagation/) | Enabled components, bounded queues, context and baggage |
| Metrics and logs | [Prometheus histograms](https://prometheus.io/docs/practices/histograms/), [PromQL functions](https://prometheus.io/docs/prometheus/latest/querying/functions/), [Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/), [Loki labels](https://grafana.com/docs/loki/latest/get-started/labels/) | Quantile aggregation, counter functions, routing and cardinality |
| Lineage | [OpenLineage model](https://openlineage.io/docs/spec/object-model/), [event schema](https://openlineage.io/spec/2-0-2/OpenLineage.json) | Dataset, job, run, facets and event structure |
| Databricks | [Pipeline expectations](https://docs.databricks.com/aws/en/ldp/expectations), [Unity Catalog lineage](https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-lineage) | Retain/drop/fail policies and coverage/permission limitations |
| Snowflake | [Data quality](https://docs.snowflake.com/en/user-guide/data-quality-intro), [dynamic tables](https://docs.snowflake.com/en/user-guide/dynamic-tables/overview) | DMFs, expectations, edition requirements and target-lag behavior |
| AI evidence | [MLflow tracing](https://mlflow.org/docs/latest/genai/tracing/), [Langfuse observability](https://langfuse.com/docs/observability/overview), [OTel GenAI conventions repository](https://github.com/open-telemetry/semantic-conventions-genai) | Trace/evaluation responsibilities and convention-version drift |

## Additional primary sources for the detailed sections

The detailed sources were reviewed on 2026-09-10, with the historical optimizer and metrics data-model references checked on 2026-09-11. Versioned URLs scope the teaching example; mutable URLs require version checks before implementation.

| Mechanism | Primary references |
|---|---|
| SQL and Python runtime | [PostgreSQL windows](https://www.postgresql.org/docs/current/tutorial-window.html), [recursive CTEs](https://www.postgresql.org/docs/current/queries-with.html), [isolation](https://www.postgresql.org/docs/current/transaction-iso.html), [asyncio tasks](https://docs.python.org/3/library/asyncio-task.html), [allocation tracing](https://docs.python.org/3/library/tracemalloc.html) |
| Files and table inspection | [Parquet encodings](https://parquet.apache.org/docs/file-format/data-pages/encodings/), [Iceberg Spark queries](https://iceberg.apache.org/docs/latest/spark-queries/), [Delta batch/version reads](https://docs.delta.io/delta-batch/) |
| Spark execution | [Spark 4.0.1 SQL tuning](https://spark.apache.org/docs/4.0.1/sql-performance-tuning.html), [memory tuning](https://spark.apache.org/docs/4.0.1/tuning.html), [UI](https://spark.apache.org/docs/4.0.1/web-ui.html), [EXPLAIN](https://spark.apache.org/docs/4.0.1/sql-ref-syntax-qry-explain.html) |
| Streaming | [Kafka 4.1 producer](https://kafka.apache.org/41/configuration/producer-configs/), [consumer](https://kafka.apache.org/41/configuration/consumer-configs/), [Spark 4.0.1 state/streaming](https://spark.apache.org/docs/4.0.1/streaming/apis-on-dataframes-and-datasets.html), [Flink state/checkpoints](https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/stateful-stream-processing/) |
| Modeling and checks | [dbt incremental](https://docs.getdbt.com/docs/build/incremental-models), [snapshots](https://docs.getdbt.com/docs/build/snapshots), [macros](https://docs.getdbt.com/docs/build/jinja-macros), [Dagster assets](https://docs.dagster.io/guides/build/assets), [GX Core](https://docs.greatexpectations.io/docs/core/introduction/), [SodaCL](https://docs.soda.io/soda-cl/soda-cl-overview.html) |
| Instrumentation and queries | [Python SDK](https://opentelemetry.io/docs/languages/python/instrumentation/), [propagation](https://opentelemetry.io/docs/languages/python/propagation/), [sampling](https://opentelemetry.io/docs/concepts/sampling/), [LogQL](https://grafana.com/docs/loki/latest/query/log_queries/), [TraceQL](https://grafana.com/docs/tempo/latest/traceql/) |
| Access enforcement | [PostgreSQL row policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html), [Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/) |
| Databricks implementation | [Pipeline Python](https://docs.databricks.com/aws/en/ldp/developer/python-dev), [Auto Loader](https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/), [job repair](https://docs.databricks.com/aws/en/jobs/repair-job-failures) |
| Snowflake implementation | [Streams](https://docs.snowflake.com/en/user-guide/streams-intro), [Tasks](https://docs.snowflake.com/en/user-guide/tasks-intro), [refresh modes](https://docs.snowflake.com/en/user-guide/dynamic-tables/refresh-modes), [micro-partitions](https://docs.snowflake.com/en/user-guide/tables-clustering-micropartitions), [Snowpark DataFrames](https://docs.snowflake.com/en/developer-guide/snowpark/python/working-with-dataframes) |
| AI retrieval and tools | [pgvector](https://github.com/pgvector/pgvector), [RRF](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion), [MCP tools, 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) |
| Design background and metric semantics | [Catalyst design](https://www.databricks.com/blog/2015/04/13/deep-dive-into-spark-sqls-catalyst-optimizer.html), [Tungsten design](https://www.databricks.com/blog/2015/04/28/project-tungsten-bringing-spark-closer-to-bare-metal.html) (historical rationale, not current benchmarks), [OTel metric data model](https://opentelemetry.io/docs/specs/otel/metrics/data-model/) |

## Corrections to overly broad interpretations

Kafka or Spark does not make every external effect exactly once. A schema contract does not prove business quality. One fresh row does not establish completeness. Automatic lineage has coverage limits. A catalog tag is not an access check. Time travel depends on retained metadata and data. A model's evaluation score does not independently establish the truth of its answer.

These distinctions guide the failure exercises throughout the course. They are part of the engineering model rather than reasons to avoid implementation.

## Explain it in your own words

Choose one factual mechanism, one curriculum recommendation, and one local fixture from this course. Explain what evidence would support each and why the shared AI conversation cannot substitute for that evidence. Return to the [roadmap](00-roadmap.md) to plan your next implementation step.

<!-- source: https://chatgpt.com/share/6aa266f6-db88-83ee-a8d7-3e7aa8e0821d?ogimg=plain | checked: 2026-09-10 | user-selected curriculum brief, successfully read from its public share payload -->
