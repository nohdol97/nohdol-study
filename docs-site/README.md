# Public learning guide

This English learning gateway presents DevOps, AIOps, and Data & Observability as separate paths on GitHub Pages. It starts with application developers who can create files and run basic shell commands, then connects terminology, normal behavior, failure, recovery, and operational judgment. The catalog contains 21 topics and 94 documents: 15 DevOps topics with 57 documents, 5 AIOps topics with 20 documents, and one Data & Observability topic with 17 chapters.

- Public URL: <https://nohdol97.github.io/nohdol-study/>
- Public content: `docs-site/content/<topic>/` and the explicitly selected `docs/guides/data-observability/` course
- Catalog: `docs-site/catalog.json`

Only the selected course in `docs/guides/data-observability/` is published from `docs/`. Harness ADRs, specifications, other guides, and the personal `vault/` remain outside the catalog's publication scope. Vault notes may help identify topics, but public articles are written separately under `docs-site/content/` after checking facts against official documentation and primary sources.

## Expanding topics and articles

When a user provides an official documentation link, read the source and expand the appropriate chapter in the topic's learning sequence. Each article combines verified facts with an independently written explanation, comparisons, and examples. Consult the official documentation for exact version-specific APIs and the complete set of options.

1. Start with a familiar problem that explains why the technology is needed.
2. Introduce technical terms with plain-language definitions and their official English names.
3. Trace an input through the steps that produce a result.
4. Specify prerequisites and establish a working baseline.
5. Change one condition to cause a failure and compare observations before and after it.
6. Explain what the command output proves and what remains unknown.
7. Verify the user outcome and remaining resources after recovery and cleanup.
8. Include comprehension questions and operational decisions about security, reliability, performance, and cost.
9. Preserve source metadata, the evidence-check date, and version or translation freshness limitations.

If an official Korean translation is marked as outdated, check the current English documentation and API reference for claims where freshness matters. Write explanations and examples independently; plain-language definitions, analogies, scenarios, and comparison tables are teaching syntheses rather than quotations. Keep source URLs and evidence-check dates in Markdown HTML comments, which the build removes from published articles. Translating an existing article does not change its evidence-check date or establish that its technical claims have been reverified.

Markdown `mermaid` blocks render using the Mermaid bundle shipped with the site. Diagrams and sequences appear within the article without an external CDN. The Data & Observability course also includes a dedicated source-review chapter with readable primary-source links; its teaching chapters remain complete explanations inside the site.

The root presents the `infra`, `aiops`, and `data-observability` learning paths. Each path orders its topics by prerequisites. Every topic has its own roadmap and articles, is explicitly registered in `catalog.json`, and belongs to exactly one path. Relative Markdown links connect prerequisites and follow-up reading across topics and become internal document routes during the build.

DevOps implements the [DevOps public learning path specification](../docs/specs/2026-09-03-infra-specialist-public-learning-path.md); AIOps implements the [AIOps public learning path specification](../docs/specs/2026-09-03-aiops-public-learning-path.md). Smaller topics provide a roadmap, conceptual model, and guided lab. Broader topics provide chapters for each module. DevOps connects traffic control with backend requests, transactions, capacity, distributed workflows, caching, and compatible deployments. AIOps connects AI Specialist topics—LLMs, vision, on-device models, time series, recommendation, and RAG/MCP—with AI Transformation platforms—GPUs, MLOps/LLMOps, AI DevOps/FinOps, and enterprise agents—through operational evidence, diagnosis, and approved remediation.

The [Data & Observability course](../docs/guides/data-observability/00-roadmap.md) implements its [learning-path specification](../docs/specs/2026-09-10-data-observability-learning-path.md). It follows one evolving project through SQL/Python, Parquet, Iceberg/Delta, Spark, Kafka/CDC, dbt, quality/SLOs, OpenTelemetry, telemetry backends, lineage/governance, Databricks/Snowflake, AI evaluation, and recovery/cost engineering. The course sources live in `docs/` at the user's request; no duplicate article tree is generated.

## Reading lab results

Each hands-on chapter and Data & Observability exercise provides an **Example results** section. Runnable fixtures distinguish expected values from variable names, times, and IDs; plan-only assignments provide explicitly synthetic review receipts. Compare the normal, failed, and recovered states and record command exits as well as business outcomes. Never copy a worksheet receipt into an execution record.

The [full documentation review](../docs/reviews/2026-09-10-full-documentation-review.md) records corrections, reproducible checks, and the boundary between local execution and unrun cloud or cluster exercises.

## Run locally

Node.js 20 or later and Python 3 are required; CI uses Node.js 22. Python runs the documented standard-library correctness fixtures during tests.

```sh
cd docs-site
npm ci
npm test
npm run build
npm run preview
```

Open `http://127.0.0.1:4174/` in your browser.

Optional [local lab checks](labs/README.md) reproduce the PostgreSQL transaction/restore and Prometheus alert fixtures with separately installed tools. They create no cloud resources. The default site test checks JSON and internal links across all 94 documents and compares the two self-contained Python examples with their documented output.

## Publication and deployment

The catalog accepts only Git-tracked Markdown within the repository. The build rejects `vault/`, `REGISTRY.md`, `_workspace/`, absolute paths, and parent-directory traversal.

Changes on `main` trigger `.github/workflows/docs-pages.yml`, which tests and builds the site, then deploys a Pages artifact. The repository's **Settings → Pages → Build and deployment → Source** must be `GitHub Actions`.

This repository has standing authorization to commit and push completed, freshly verified changes to `origin/main` without separate confirmation. That authorization excludes force pushes, history rewrites, releases, and other remotes or branches.

`dist/` is generated output and must not be committed.
