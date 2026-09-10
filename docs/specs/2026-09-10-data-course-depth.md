# Data course technical depth

- Date: 2026-09-10
- Status: Implemented
- Course: [Data and Observability](../guides/data-observability/00-roadmap.md)

The shared curriculum names individual mechanisms that the initial course compressed into overview paragraphs. Expand the existing chapters without changing their public routes. A result worksheet alone does not meet the learning requirement.

## Acceptance criteria

1. Map the source's SQL/Python, storage, table formats, Spark, Kafka, modeling, quality, telemetry, governance, cloud, and AI subtechnologies to substantive sections. Explain what each mechanism does, how it works, when it helps, and a concrete failure or limitation.
2. Give worked examples for query/window semantics, historical joins, table commits, distributed execution, replication/replay, streaming time/state, telemetry propagation, metric math, access policy, managed pipelines, and retrieval/evaluation.
3. Pair executable examples with input fixtures, commands, expected output, and interpretation. Run self-contained local examples and distinguish those observations from unexecuted distributed or managed-platform exercises.
4. Validate new SDK/configuration claims against official documentation and record version scope. Do not treat the shared conversation as technical evidence.
5. Preserve the 17 chapter IDs, existing publication restrictions, earlier correctness fixes, and other learning paths. Run documentation tests, build checks, the harness verifier, and browser navigation/render checks before delivery.
6. Synchronize the roadmap, source coverage register, capstone, public documentation navigation, and changelog. Publish the freshly verified commit through the existing Pages workflow.

## Verification receipt

Fresh verification completed on 2026-09-11: ten site tests, the 94-document build/check, and the 18-skill harness verifier passed. The browser opened all 94 documents on desktop and mobile, rendered 108 diagrams, and verified path navigation, prerequisite links, search, the diagram viewer, and overflow checks.

Seven new standard-library examples reproduced their printed outputs. Optional local checks passed with OTel SDK 1.44.0, DuckDB 1.5.0, dbt-core 1.12.4, and dbt-duckdb 1.11.0: real context propagation, equal Parquet results with 1 versus 13 candidate groups, incremental correction/retry/full-rebuild equality, and the documented deletion gap. The synthetic dbt seed declares column types explicitly rather than relying on small-CSV inference.

Spark/Java, Kafka/Flink, Iceberg/Delta engine integrations, telemetry network/backends, identity-policy execution, and managed Databricks/Snowflake exercises were not deployed in this verification. Their explanations and syntax were reviewed against primary documentation; their expected results remain labeled exercises. No performance, cloud billing, production authorization, or model-quality measurement is claimed from the local fixtures.
