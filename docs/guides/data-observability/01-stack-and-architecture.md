# Choose a stack by responsibility

Suppose the sales team needs new orders in its report within ten minutes. The report must also pass data checks and be reproducible later.

Write down those requirements before choosing tools. Then assign a component to each job: collecting changes, storing data, calculating results, and checking delivery.

## Terms introduced in this chapter

| Term | Meaning | Why it matters / when to use it |
|---|---|---|
| Storage format | The rules for storing data inside a file. Parquet is one example. | Choose a file representation that fits analytical access, compression, and interoperability needs. **Concrete situation (illustrative):** A query needs two fields from a wide dataset. → Compare candidate file formats under that access pattern. → Measure bytes read, decoding work, and output correctness. |
| Table format | The rules and metadata that identify which files belong to a committed table version. | Define which files form one accepted table state when readers and writers operate concurrently. **Concrete situation (illustrative):** Writers add files while readers need a consistent table. → Use the table format's committed-state protocol. → Verify readers resolve one valid version, not a directory guess. |
| Compute engine | Software that runs queries or transformations to calculate results from data. | Execute the required transformations while measuring the work caused by the chosen plan. **Concrete situation (illustrative):** A transformation scans data but spends most time on redistribution. → Inspect the compute engine's plan. → Compare a revised plan under equivalent result checks. |
| Control plane | The part of a platform that defines what runs, when it runs, and which permissions it uses. | Separate definitions and policies that direct work from the data-moving execution itself. **Concrete situation (illustrative):** A job definition exists but its schedule or permission is wrong. → Inspect control-plane metadata and policy. → Verify the intended execution is authorized and scheduled. |
| Data plane | The workers and storage that actually read, move, and transform the data. | Locate the throughput, failure, and access boundaries where data is actually processed. **Concrete situation (illustrative):** Scheduling succeeds while actual data transfer stalls. → Inspect data-plane readers, workers, and storage. → Locate the measured throughput or access bottleneck. |

## Understand the model first

1. A producer emits an event with a stable identity and a schema version.
2. Ingestion preserves enough information to replay it.
3. Processing creates validated output and commits a table version.
4. A publication gate exposes that version to consumers.
5. Telemetry and lineage explain what happened without becoming the data's source of truth.

The catalog tells a reader which table exists and how to find it. Object storage holds the files. An engine reads the table metadata to choose the files for a query. A dashboard renders observations from backends; it does not repair the table or enforce its contract.

## A default learning stack and deliberate alternatives

The choices below are teaching recommendations. They are not rankings or claims that every combination is compatible.

| Responsibility | Start with | Add or compare when the problem requires it |
|---|---|---|
| Local correctness | Python, SQLite; DuckDB for analytical files | PostgreSQL for concurrent transactions and CDC |
| Durable files | Parquet and a local directory, then S3 or equivalent object storage | Cloud-specific IAM, request cost, lifecycle and recovery behavior |
| Analytical tables | Iceberg **or** Delta Lake | Compare the second format after implementing commit and maintenance workflows |
| Distributed processing | Spark SQL / PySpark | Flink for a deliberate study of continuous event-time processing and state |
| Transport | Kafka | Debezium and Kafka Connect for database change capture |
| Schema compatibility | A schema registry with Avro, Protobuf, or JSON Schema | Compatibility and semantic migration tests across producer/consumer versions |
| Interactive lake queries | DuckDB locally | Trino when independent distributed SQL access is needed |
| Modeling | dbt with one supported adapter | A semantic layer when several consumers need identical metric definitions |
| Scheduling | Airflow **or** Dagster | Compare time-interval workflows with asset-oriented definitions |
| Quality | SQL assertions and dbt tests | Great Expectations or Soda when richer checks and reporting justify another service |
| Lineage and discovery | OpenLineage events and a small searchable registry | Marquez as a lineage backend; DataHub or OpenMetadata for broader catalog evaluation |
| Instrumentation | OTel SDK and Collector | Agent/gateway tiers when routing, isolation, or capacity requires them |
| Telemetry storage | Prometheus, Loki, Tempo; Grafana for exploration | Jaeger as a trace alternative; Mimir or Thanos for metrics scale and retention; Pyroscope for profiles |
| Managed platform | Databricks after the fundamentals | Snowflake as the second implementation of the same contracts |
| AI operations | Authorized retrieval plus MLflow or Langfuse | Both only when their distinct workflow responsibilities are explicit |
| Delivery | Git, CI, containers | Terraform, Kubernetes, workload identity, policy and GitOps as operating needs grow |

Do not deploy all alternatives together. Start with a local file pipeline. Add a service when you can state which requirement cannot be met by the current system. Kafka, Spark, and a lakehouse already introduce substantial recovery and compatibility work.

## Architecture boundaries

```mermaid
flowchart TB
  C[Contracts and ownership] --> E[Execution and publication]
  A[Access policy] --> E
  E --> T[Versioned tables]
  E --> R[Run receipts]
  E --> O[Telemetry backends]
  R --> L[Lineage and catalog]
  T --> Q[Authorized consumers]
  L -. discovery and impact .-> Q
```

Keep business events and telemetry logically separate even when both use Kafka. Business-event retention protects replay. Telemetry retention supports diagnosis under a different volume and privacy policy. A telemetry overload should not silently consume all capacity needed for order processing.

## A reviewable selection record

Write a short decision before adding distributed compute: current daily bytes, peak rate, file count, query patterns, latency target, acceptable recovery time, and machine budget. Run the same correctness fixtures before and after the migration. If the distributed version is slower on a laptop, that is an observation, not proof that the engine is unsuitable at scale.

Maintain a compatibility manifest containing engine version, connector coordinates, Java/Python versions, table protocol/features, OTel distribution, SDK versions, and dbt adapter. Pin a tested set in the project lockfiles. A set of independently current versions is not necessarily a working set.

## Follow one event through five different identities

An event identity, source position, processing run, table snapshot, and trace ID answer different questions. Treating them as interchangeable makes replay and incident analysis ambiguous. For the orders project, carry enough references to make the following chain explicit:

| Reference | Example | Question it answers |
|---|---|---|
| Business identity/version | `e1`, source sequence `2` | Which logical change is this? |
| Transport position | topic orders, partition 0, offset 91 | Where can ingestion resume/replay? |
| Logical interval and attempt | September 10, attempt run-8 | Which slice and execution produced the candidate? |
| Input/output version | source snapshot A, accepted snapshot B | Which exact state was read and published? |
| Trace/span context | trace T, consume span S | Which operations participated in this execution? |

The same e1 can be delivered at two offsets after a producer-side replay. Two attempts can process the same logical interval. A snapshot can combine many input partitions and runs; one trace need not encompass its entire lifetime. The business reconciliation gate uses event/version identities, while the recovery mechanism also needs source positions and committed output references.

## Compare two concrete implementations

For a daily 100 MB report, a scheduled Python/DuckDB transformation can read a versioned input, write a candidate Parquet file, validate counts/totals, and publish a manifest. Its failure boundary is the candidate-to-published transition. Keep yesterday's approved manifest available while labeling its age if today's candidate fails. A distributed cluster adds little value unless a measured requirement justifies its startup and operating work.

For continuously arriving events, Kafka gives the processor a retained log, Spark maintains bounded processing progress/state, and an Iceberg/Delta sink defines committed table visibility. A mart builder then publishes a consumer definition, and OTel/OpenLineage provide execution and derivation evidence. Every additional boundary adds a failure to test: broker acknowledgement, source progress, sink commit, mart approval, and observation delivery.

If Spark crashes after the table commit but before its progress is recorded, sink reconciliation must tolerate replay. If dbt succeeds but the publication gate fails, the consumer should not accidentally read the unapproved candidate. If telemetry export stops, the independent publication ledger still establishes business outcomes while monitoring reports incomplete coverage. These are architecture requirements you can test before choosing a managed product.

## Exercise and interpretation

Draw two designs: a daily 100 MB report and a continuously updated stream with a five-minute freshness target. Assign storage, processing, scheduling, contract checking, and telemetry to each. Explain every additional process in the second design. Then add a one-hour downstream outage and show where the backlog lives, how long it survives, and who owns recovery.

## Example results

Illustrative design review, not a running platform.

```text
daily 100 MB report: versioned files + scheduled transform + publication checks
five-minute stream: retained log + checkpointed processing + freshness checks
100 events/s paused for one hour: backlog = 360000
recovery 300/s minus incoming 100/s: net drain = 200/s
estimated drain time = 1800 seconds
```

The estimate assumes sustained rates and sufficient retention. A diagram without a backlog owner or retention bound fails the review.

## Explain it in your own words

Why can OpenLineage and OpenTelemetry coexist without one replacing the other? A lineage event describes data derivation; a span records an operation. Linking their run identities makes them useful together. Neither grants permission to read a dataset.

Continue with [foundations](02-sql-python-foundations.md).

<!-- source: https://openlineage.io/docs/spec/object-model/ | checked: 2026-09-10 | dataset/job/run responsibilities -->
<!-- source: https://opentelemetry.io/docs/collector/configuration/ | checked: 2026-09-10 | Collector component responsibilities; stack choices are curriculum synthesis -->
