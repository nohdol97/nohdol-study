# Databricks first, Snowflake second: compare the same promises

Learning a managed platform is more useful after you can state what the pipeline must guarantee. Reimplement the same dataset, quality rules, recovery cases, and access tests. The goal is to explain architectural tradeoffs using comparable evidence.

## Terms introduced in this chapter

| Term | Meaning | Why it matters / when to use it |
|---|---|---|
| Managed compute | Processing capacity whose provisioning and operation are partly delegated to a provider | Delegate part of infrastructure operation while retaining responsibility for workload correctness and cost. |
| Unity Catalog | Databricks' governance and discovery layer for supported assets | Coordinate asset discovery and access governance across supported Databricks workloads. |
| Lakeflow | Databricks' family of ingestion, pipeline, and job capabilities | Coordinate ingestion, transformations, and jobs within Databricks' data-engineering tooling. |
| Dynamic table | A Snowflake query-defined table maintained through refreshes | Maintain a query-defined analytical result through managed refresh behavior with explicit freshness requirements. |
| DMF | Snowflake Data Metric Function, used to measure data properties | Measure data properties repeatedly so quality expectations can be evaluated on recorded results. |
| Warehouse | In Snowflake, a compute resource used for supported workloads | Assign and size Snowflake compute for a workload while managing concurrency and spending. |

## Understand the model first

1. Preserve the input fixtures and their expected outcomes outside a platform-specific implementation.
2. Map ingestion, transformations, publication, quality, lineage, permissions, and telemetry to platform capabilities.
3. Implement the pipeline in a disposable development environment.
4. Run the same failure and access tests as the local design.
5. Compare correctness, recovery, operational effort, performance, and cost separately.

This chapter is a guided cloud exercise, not an executed deployment of a data platform. It requires an account with the relevant capabilities, a spending limit, a disposable schema/catalog, and permission to create and remove only the lab's resources. The deployed deliverable of this course is the documentation site.

## Databricks: deepen Spark, Delta, and governance

Study the separation of workspace operations, compute, storage, and catalog permissions. Identify who owns storage locations, which identity performs a job, how code is versioned, and where event logs and query history are retained. Do not treat notebook state as the only record of a production transformation.

Build raw, accepted, and daily-revenue tables. Preserve source event IDs and ingestion timestamps in raw data. Resolve valid event versions and quarantine defects before publication. In Lakeflow Spark Declarative Pipelines, expectations can retain invalid rows while collecting metrics, drop invalid rows, or fail an update according to the selected policy. Choose based on the consumer contract: dropping an invalid revenue row changes completeness, even if it makes the accepted table pass a range check.

Unity Catalog lineage provides recorded relationships for supported operations, with documented coverage and permission limits. Reference registered tables where column-level coverage requires them, and test the integrations actually used. For example, the reviewed documentation distinguishes supported table-name references from path-based cases where column lineage is not captured. A visible graph is not proof that every external script or file export is represented.

Use Lakeflow Jobs for workflow operations where appropriate. Record code revision, runtime version, input/output identifiers, retries, and repair outcomes. Add MLflow for model or AI evaluation workflows when the project reaches those stages. Keep evaluation results connected to the exact corpus and application bundle.

## Databricks exercise

Create a development pipeline from the capstone fixtures and run it under a dedicated identity. Introduce a null key, an unknown currency, and a late correction. Compare retain, drop, and fail policies in separate runs, recording eligible input, quarantined output, published rows, and business totals. Restart a failed run and verify that repair does not double-count accepted events.

Inspect lineage for the registered tables and a deliberately unsupported or externally executed step. Record the coverage difference. Test a consumer identity with a restricted view or policy and an unauthorized identity against the underlying table. Finally inspect compute usage, remove lab schedules/resources, and verify that no lab compute continues running.

## Snowflake: compare storage, compute, and managed refresh

Snowflake SQL and Snowpark offer different ways to express processing; learn the execution and data-movement behavior before assuming a PySpark program transfers unchanged. Native Snowflake tables and Iceberg integrations also have different management and interoperability responsibilities.

Dynamic tables materialize a query and maintain results using a target lag and supported refresh behavior. Treat the target as scheduling intent to measure, not a guaranteed end-to-end business deadline. Streams and tasks provide a different way to express change-driven and procedural workflows. Openflow belongs in an ingestion comparison when a supported connector matches the source; it is not an interchangeable name for every streaming processor.

Snowflake data quality checks use DMFs and expectations. The reviewed documentation marks Data Quality Monitoring as an Enterprise Edition feature. Check the account edition, supported objects, permissions, scheduling, and charges before adopting it. A measured null count and its expectation do not repair source data or define a consumer fallback automatically.

Horizon Catalog is the governance/discovery context to investigate for lineage, classification, access, and policies. Cortex belongs later, when evaluating AI functions or serving against an already governed dataset. Compare those capabilities against requirements and current account availability rather than treating product names as exact equivalents.

## Databricks architecture: identities and execution boundaries

Separate the workspace's code/job configuration, the compute executing a task, the data locations, and Unity Catalog's registered objects and permissions. A notebook user and the scheduled job's run-as identity can have different rights. Test the scheduled identity's ability to read the bronze source, write silver/gold, and access its checkpoint or managed storage. An interactive success under an administrator's identity is a poor production test.

Unity Catalog uses a catalog/schema/object hierarchy for supported assets. Managed tables and external tables assign different storage-lifecycle responsibilities. A storage credential/external location is a controlled bridge to cloud storage; it does not mean every notebook should receive a raw storage secret. Registered table references also allow supported governance and lineage integrations to observe more than an arbitrary path read.

SQL warehouses serve SQL workloads, while other supported compute choices execute jobs and interactive Spark workloads. Choose by workload, runtime/library requirements, isolation, startup delay, and measured concurrency. The provider managing the machines does not decide the order grain, retry identity, or consumer deadline for you.

## Lakeflow pipeline lab: bronze, silver, gold, and expectations

Run this only in a disposable Databricks schema named `study_lab` under an existing development catalog. Configure a Lakeflow Spark Declarative Pipelines development pipeline to publish to that same catalog/schema, using a runtime that supports `pyspark.pipelines` and Databricks expectations. This example uses a batch materialized view so the four input rows are easy to inspect. It is a managed-platform exercise, not a locally executed result.

First run this SQL once in the selected catalog, using a fresh schema:

```sql
CREATE SCHEMA study_lab;
CREATE TABLE study_lab.orders_bronze (
  event_id STRING, amount_cents BIGINT, currency STRING
) USING DELTA;
INSERT INTO study_lab.orders_bronze VALUES
  ('e1',100,'USD'),('e2',250,'USD'),
  (NULL,50,'USD'),('e4',70,'UNKNOWN');
SELECT COUNT(*) AS raw_rows FROM study_lab.orders_bronze;
```

Add this Python source file to the development pipeline. The functions return DataFrames; the pipeline builds the dependency graph and executes it. Do not send notifications or perform imperative external writes inside dataset-definition functions, which can be evaluated during planning.

```python
from pyspark import pipelines as dp
from pyspark.sql import functions as F

@dp.materialized_view(name='orders_silver')
@dp.expect_or_drop(
    'valid_order',
    "event_id IS NOT NULL AND amount_cents >= 0 AND currency = 'USD'"
)
def orders_silver():
    return spark.read.table('study_lab.orders_bronze')

@dp.materialized_view(name='orders_gold')
def orders_gold():
    return (spark.read.table('study_lab.orders_silver')
            .groupBy('currency')
            .agg(F.count('*').alias('event_count'),
                 F.sum('amount_cents').alias('total_cents')))
```

After a successful update, inspect these results and the pipeline's quality/event evidence:

```sql
SELECT COUNT(*) AS accepted_rows FROM study_lab.orders_silver;
SELECT currency,event_count,total_cents FROM study_lab.orders_gold;
```

Expected logical result:

```text
bronze raw_rows=4
silver accepted_rows=2
gold currency=USD event_count=2 total_cents=350
valid_order violations=2, with drop policy recorded
```

The drop policy is appropriate only for this teaching comparison. It does not establish completeness against the producer, and it does not deduplicate event IDs. Add the capstone's conflict, version, and expected-input checks before treating it as a revenue product. Retain raw defects for investigation.

In separate development runs, replace `expect_or_drop` with `expect` to retain invalid rows while reporting violations, then with `expect_or_fail` to fail the violating flow. Record the update outcome and inspect which prior outputs remain visible. Failure of one flow is not a universal transaction across every dataset and flow in a pipeline. Never interpret “failed update” as proof that no other output changed.

### Auto Loader and streaming tables

Auto Loader discovers new files in supported object storage and maintains progress. A `cloudFiles` streaming read plus a streaming table fits incremental file ingestion; schema inference/evolution and rescued-data behavior need explicit configuration and inspection. File discovery progress does not establish business-event uniqueness: two files can contain the same event. Preserve source path, ingestion time, schema information, and event identity in bronze.

For CDC, map source keys, sequencing, updates, and deletes to the supported AUTO CDC workflow when it meets the contract. Do not treat a file's arrival time as the authoritative order of business updates. A late correction needs its source sequence and a target-history policy.

## Jobs, repair, Delta maintenance, and MLflow serving

Lakeflow Jobs orchestrates task dependencies, parameters, schedules, and retry/repair workflows. Pass a stable business interval and source snapshot explicitly. Repair runs can rerun unsuccessful and dependent work under supported behavior; earlier successful side effects still exist. Reconcile output/run identities before issuing an additional publication or external effect.

Delta maintenance addresses file layout and retained history. Compaction and data skipping improve selected workloads but must be measured against write/compute cost. Vacuum/retention decisions determine how far time travel and replay can reach. A job checkpoint and a table's Delta log protect different state; back up or reconstruct both according to the recovery contract.

MLflow tracks model/application runs, artifacts, traces, and evaluation records through supported integrations. Tie a registered model or AI application version to its training/corpus snapshot, parameters, and evaluation suite. Model serving exposes the selected artifact through a controlled runtime/endpoint. Deploying the artifact requires compatibility, authorization, latency/capacity, and rollback checks as well as an offline score. A successful model registration is not a serving rollout.

## Snowflake architecture: SQL, micro-partitions, and warehouses

For native tables, Snowflake stores data in managed columnar micro-partitions and uses metadata to prune work. A warehouse supplies compute; scaling its size and scaling concurrency solve different problems. Inspect query profile, partitions scanned, bytes, spill, queuing, and cache state before increasing compute. Repeating a cached query can obscure the cost of its first execution.

Snowpark expresses operations that execute in Snowflake through its supported APIs. Building a DataFrame expression is distinct from materializing a local result; `collect()` brings results to the client. Python procedures/UDFs add runtime and package constraints. Rewriting a PySpark script's method names is not enough to preserve plan behavior, supported functions, or data movement.

## Streams and Tasks: change position versus execution schedule

A Snowflake stream tracks a change position for a source table; it is not a Kafka broker or an independent complete copy of the table. Querying a stream does not advance its offset. Consuming it in a committed DML transaction advances the position under Snowflake's rules. Use separate streams when independent consumers need independent progress, and monitor staleness against source change-retention limits.

This manual change-application lab needs a fresh disposable Snowflake schema and an already authorized warehouse. It creates two tables and a stream, not a schedule. Execute the statements in order. Metadata action fields distinguish inserted/deleted row images and update pairs.

```sql
CREATE TABLE study_source (event_id STRING, amount_cents NUMBER(18,0));
CREATE TABLE study_target (event_id STRING, amount_cents NUMBER(18,0));
CREATE STREAM study_changes ON TABLE study_source;
INSERT INTO study_source VALUES ('e1',100),('e2',250);

BEGIN;
MERGE INTO study_target t USING (
  SELECT event_id,amount_cents FROM study_changes
  WHERE METADATA$ACTION='INSERT'
) s ON t.event_id=s.event_id
WHEN MATCHED THEN UPDATE SET amount_cents=s.amount_cents
WHEN NOT MATCHED THEN INSERT (event_id,amount_cents)
VALUES (s.event_id,s.amount_cents);
COMMIT;

SELECT COUNT(*),SUM(amount_cents) FROM study_target;
SELECT COUNT(*) AS pending_changes FROM study_changes;

UPDATE study_source SET amount_cents=120 WHERE event_id='e1';
SELECT event_id,METADATA$ACTION,METADATA$ISUPDATE FROM study_changes;
```

Expected first result is `(2,350)`, with zero pending changes after commit. The subsequent update exposes its change representation; rerunning the same MERGE transaction gives `(2,370)`, then another identical invocation stays `(2,370)`. This fixture assumes one current source row per event ID and handles inserts/updates. It deliberately does not implement source deletes: add a transactionally coordinated delete branch and a deletion fixture before extending that contract. Multiple source matches need deterministic reconciliation before MERGE.

A task runs SQL or a procedure under a schedule or supported trigger. A task graph describes dependencies; resume/suspend, privileges, overlap/retry behavior, and compute selection are operational responsibilities. Wrap the proven transaction in a procedure before scheduling it, and retain the source/target outcome identity. Scheduling a task cannot repair an ambiguous MERGE or recover changes after a stream becomes stale.

## Dynamic tables versus procedural change application

A dynamic table declares a query result to maintain. Snowflake chooses or uses a supported refresh mode and computes refreshes toward the configured target lag. An incremental refresh updates affected parts when the query is eligible; a full refresh recomputes the result. Inspect actual refresh mode, history, upstream dependencies, and cost. `TARGET_LAG` is an intended freshness relationship, not a guarantee that a failed source load arrives by a business deadline.

Choose a dynamic table when the desired result is naturally a supported declarative query and managed refresh fits. Choose streams/tasks when explicit procedural behavior, side effects, or transaction sequencing are required. They are not interchangeable syntax for exactly the same operational contract. A simple `SELECT COUNT(*)` preview does not reveal refresh eligibility for a larger query containing joins, UDFs, or unsupported constructs.

## DMF, Horizon, Openflow, and Cortex responsibilities

A Data Metric Function measures a property, such as null count or freshness. An expectation evaluates the metric against an acceptable condition; scheduled monitoring adds execution/permission/cost requirements. For a valid key rule, a null-count metric of zero does not prove unique keys or complete source delivery. Check the account edition and current supported objects before scheduling DMFs; the reviewed Data Quality Monitoring feature requires Enterprise Edition.

Horizon groups governance/discovery capabilities such as policies, classification, and lineage. Test row access and masking under reader identities and inspect supported lineage coverage, just as in Unity Catalog. Openflow provides ingestion/integration through supported flows and connectors; assess its source checkpoint, error routing, and replay behavior for the selected connector. Cortex adds supported AI/search/inference capabilities, whose data access, freshness, evaluation, and cost need the same contract as another AI endpoint.

At cleanup, stop any lab tasks/pipelines/schedules, verify their state, and remove only the disposable lab resources. Record actual compute/billing evidence if you run these cloud exercises. No account was provisioned or billed to produce the expected results printed here.

## Comparison worksheet

| Requirement | Databricks investigation | Snowflake investigation |
|---|---|---|
| Transform and publish | Spark, Delta, Lakeflow pipelines | SQL/Snowpark, dynamic tables or tasks |
| Quality | Expectations, monitoring, custom checks | DMFs, expectations, custom checks |
| Lineage and access | Unity Catalog coverage and policy | Horizon lineage and policy coverage |
| Replay and repair | Source positions, checkpoints, job repair | Change retention, refresh/task behavior, historical reconstruction |
| AI lifecycle | MLflow and supported AI platform capabilities | Cortex and supported evaluation/serving capabilities |
| Economics | Compute/runtime, storage, transfer, orchestration | Warehouse/serverless usage, storage, transfer, refresh and checks |

A useful comparison records source size, query concurrency, cache state, runtime configuration, repeated measurements, output equality, recovery time, and a cost breakdown. Do not declare a winner from a single warm query or a trial-credit balance.

## Example results

Synthetic policy worksheet with two valid and two invalid rows; no managed-platform run is claimed.

```text
retain policy: 4 candidates with violations reported
drop policy: 2 valid candidates; 2 dropped rows recorded
fail policy: no approved new publication
retry after correction: business total unchanged by duplicate delivery
cleanup: no lab compute or schedule remains active
```

The invalid rows contain a null key and unknown currency. Whether old output stays visible depends on the selected publication contract. Record actual update identifiers, lineage gaps, access tests, and billing evidence before calling the cloud lab complete.

## Explain it in your own words

Which responsibilities move to the provider, and which still belong to your team? Explain why platform monitoring, business quality checks, access enforcement, and restoration each require distinct evidence. Defer Snowflake specialization until you can demonstrate the first platform's failure behavior.

Continue with [AI-ready data and evaluation](13-ai-ready-data-evaluation.md).

<!-- source: https://docs.databricks.com/aws/en/ldp/expectations | checked: 2026-09-10 | retain/drop/fail policies and limitations -->
<!-- source: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-lineage | checked: 2026-09-10 | lineage coverage and access -->
<!-- source: https://docs.snowflake.com/en/user-guide/data-quality-intro | checked: 2026-09-10 | DMFs, expectations, Enterprise requirement -->
<!-- source: https://docs.snowflake.com/en/user-guide/dynamic-tables/overview | checked: 2026-09-10 | maintained query results and target lag -->
<!-- source: https://docs.databricks.com/aws/en/ldp/developer/python-dev | checked: 2026-09-10 | pyspark.pipelines and materialized view development -->
<!-- source: https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/auto-loader/ | checked: 2026-09-10 | incremental file ingestion -->
<!-- source: https://docs.databricks.com/aws/en/jobs/repair-job-failures | checked: 2026-09-10 | job repair and retry scope -->
<!-- source: https://docs.snowflake.com/en/user-guide/streams-intro | checked: 2026-09-10 | offsets, change images and consumption -->
<!-- source: https://docs.snowflake.com/en/user-guide/tasks-intro | checked: 2026-09-10 | task execution responsibilities -->
<!-- source: https://docs.snowflake.com/en/user-guide/dynamic-tables/refresh-modes | checked: 2026-09-10 | incremental/full refresh -->
<!-- source: https://docs.snowflake.com/en/user-guide/tables-clustering-micropartitions | checked: 2026-09-10 | managed micro-partitions and pruning -->
<!-- source: https://docs.snowflake.com/en/developer-guide/snowpark/python/working-with-dataframes | checked: 2026-09-10 | lazy expressions and result materialization -->
<!-- source: https://docs.databricks.com/aws/en/data-governance/unity-catalog/ | checked: 2026-09-10 | registered objects and permissions -->
