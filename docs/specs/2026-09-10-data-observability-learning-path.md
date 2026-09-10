# Data and Observability public learning path

- Date: 2026-09-10
- Status: Implemented
- Related decision: [ADR 009](../adr/009-public-docs-root-learning-paths.md)
- Curriculum: [Data and Observability Engineering](../guides/data-observability/00-roadmap.md)

## Objective and source

Provide a detailed English course for becoming a data and observability engineer, based on the user-selected [shared conversation](https://chatgpt.com/share/6aa266f6-db88-83ee-a8d7-3e7aa8e0821d?ogimg=plain), with justified stack extensions and verified public deployment. The shared conversation is a curriculum brief, not technical evidence or authority about the reader's career history.

## Published structure

Add the `data-observability` path and its `data-observability-engineering` topic alongside DevOps and AIOps. Explicitly select 17 English Markdown documents under `docs/guides/data-observability/` in the existing catalog. This implements the user's request to keep the course in `docs/` without publishing unrelated harness documents or copying the private vault.

The existing catalog supports tracked repository Markdown and keeps blocked paths, traversal, untracked-source and repository-boundary checks. No source-discovery expansion or publication-gate relaxation is required. Existing document IDs remain unchanged. Root path cards adapt to three entries and narrow screens.

The chapter sequence covers roadmap, stack selection, SQL/Python, Parquet/object storage, Iceberg/Delta, Spark, Kafka/CDC/streaming, modeling/dbt/orchestration, quality/contracts/SLOs, OpenTelemetry, telemetry backends, lineage/governance, Databricks/Snowflake, AI data/evaluation, operations, capstone, and source review.

## Acceptance criteria

1. The catalog has three paths, 21 topics, and 94 documents; the new path contains all 17 selected course documents and every topic belongs to exactly one path.
2. The curriculum preserves the shared conversation's major stages and one evolving project while adding CDC, compatibility, stream-time boundaries, telemetry loss/cardinality, explicit SLO populations, access enforcement, and restore/cost exercises.
3. Technical explanations cite primary sources with review dates. Synthetic examples and recommendations are distinguished from vendor guarantees. Managed-platform labs and distributed-system exercises are not described as executed deployments.
4. The local SQLite and capstone Python fixtures execute in fresh verification. Every relative course Markdown link resolves to another explicitly published document. JSON examples parse and all new Mermaid diagrams render.
5. Existing privacy, path validation, and English-rendering tests continue to pass. Existing course coverage remains tested separately from the new course.
6. Browser verification covers the third path, chapter navigation, cross-course prerequisites, search, diagram rendering/viewer, and mobile overflow.
7. GitHub Pages deploys the verified commit on `origin/main`. The public content payload and assets match the built artifact, and the new course can be loaded from the public URL.

## Delivery limits

Deployment means the documentation site. The course provides future learning assignments, not a claim that the user has completed them or that a cloud data platform was provisioned. No private notes, employer-specific data, share-page payload, credentials, generated site output, or installation metadata are committed.
