# Databricks first, Snowflake second: compare the same promises

Learning a managed platform is more useful after you can state what the pipeline must guarantee. Reimplement the same dataset, quality rules, recovery cases, and access tests. The goal is to explain architectural tradeoffs using comparable evidence.

## Terms introduced in this chapter

| Term | Meaning |
|---|---|
| Managed compute | Processing capacity whose provisioning and operation are partly delegated to a provider |
| Unity Catalog | Databricks' governance and discovery layer for supported assets |
| Lakeflow | Databricks' family of ingestion, pipeline, and job capabilities |
| Dynamic table | A Snowflake query-defined table maintained through refreshes |
| DMF | Snowflake Data Metric Function, used to measure data properties |
| Warehouse | In Snowflake, a compute resource used for supported workloads |

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

## Explain it in your own words

Which responsibilities move to the provider, and which still belong to your team? Explain why platform monitoring, business quality checks, access enforcement, and restoration each require distinct evidence. Defer Snowflake specialization until you can demonstrate the first platform's failure behavior.

Continue with [AI-ready data and evaluation](13-ai-ready-data-evaluation.md).

<!-- source: https://docs.databricks.com/aws/en/ldp/expectations | checked: 2026-09-10 | retain/drop/fail policies and limitations -->
<!-- source: https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-lineage | checked: 2026-09-10 | lineage coverage and access -->
<!-- source: https://docs.snowflake.com/en/user-guide/data-quality-intro | checked: 2026-09-10 | DMFs, expectations, Enterprise requirement -->
<!-- source: https://docs.snowflake.com/en/user-guide/dynamic-tables/overview | checked: 2026-09-10 | maintained query results and target lag -->
