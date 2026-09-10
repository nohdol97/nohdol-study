# Source review, extensions, and implementation boundaries

Reviewed on **2026-09-10**. This course uses the user-selected shared conversation as a curriculum brief. It does not use the conversation's AI-generated claims, citation handles, or assumptions about personal experience as independent evidence.

## What the shared conversation contributed

The conversation proposed a sequence from SQL/Python through Parquet, Iceberg/Delta, Spark, Kafka, dbt, data quality, OpenTelemetry, lineage/governance, Databricks, Snowflake, AI-ready data, and AI observability. It also recommended one evolving project and particular depth in Spark, OpenTelemetry, and data reliability. These ideas are preserved in the [roadmap](00-roadmap.md) and [capstone](15-capstone.md).

The conversation contains different suggested calendars and career predictions. This course consolidates the calendar into an adjustable twelve-month example and removes predictions presented as guarantees. Existing experience should be demonstrated with the exercises, not inferred from the shared conversation.

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

## Corrections to overly broad interpretations

Kafka or Spark does not make every external effect exactly once. A schema contract does not prove business quality. One fresh row does not establish completeness. Automatic lineage has coverage limits. A catalog tag is not an access check. Time travel depends on retained metadata and data. A model's evaluation score does not independently establish the truth of its answer.

These distinctions guide the failure exercises throughout the course. They are part of the engineering model rather than reasons to avoid implementation.

## Explain it in your own words

Choose one factual mechanism, one curriculum recommendation, and one local fixture from this course. Explain what evidence would support each and why the shared AI conversation cannot substitute for that evidence. Return to the [roadmap](00-roadmap.md) to plan your next implementation step.

<!-- source: https://chatgpt.com/share/6aa266f6-db88-83ee-a8d7-3e7aa8e0821d?ogimg=plain | checked: 2026-09-10 | user-selected curriculum brief, successfully read from its public share payload -->
