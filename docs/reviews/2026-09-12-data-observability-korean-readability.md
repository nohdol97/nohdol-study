# Data and Observability Korean readability review

- Reviewed: 2026-09-12
- Scope: all 17 Data & Observability translations and all three Observability/SRE translations, including titles, summaries, definitions, body explanations, and exercise interpretation.
- Change type: editorial. English source bindings, routes, shared code/output/diagram fences, and evidence-review comments are preserved.

## Findings and revision

Short introductions were followed by compressed operational prose. Several mechanisms and qualifications appeared in one sentence without identifying who performed the action. Some glossary purposes repeated this abstraction instead of explaining why a reader would use the concept. The English source also contains compressed passages; literal Korean translation amplified them.

Repeated terms such as reconciliation, publication, population, invariant, identity, and boundary required readers to infer the action. Observability/SRE additionally mixed ordinary English nouns with Korean sentence structure. Some headings described abstract models instead of the question the chapter answers.

The revision explains concrete actions and consequences within the existing paired blocks. Publication is introduced as making an approved data version available to consumers. Reconciliation identifies the IDs or values to compare. Kafka recovery follows processing and offset commits in order. SLO explanations distinguish missing observations from success. Technical names remain where readers need them for documentation, commands, and search.

For example, “효과 전 커밋에는 최대 한 번의 유실 구간” is replaced with the sequence of committing a position, crashing before the database update, and skipping that message on restart. The reverse ordering explains why replay can repeat an update. “출력 대사” becomes a comparison of output values or IDs, with the actual objects named in the explanation.

## Coverage

Article names below refer to the Korean translations selected in `docs-site/catalog.json`.

| Article | Main editorial work |
|---|---|
| Data 00: Roadmap | A responding API versus a usable report; learning months and concrete completion tasks. |
| Data 01: Stack | Publication, tool responsibilities, and event/offset/run/snapshot/trace identities. |
| Data 02: SQL/Python | Conflicting duplicates, window ordering, CTE execution, transaction snapshots, asynchronous retries. |
| Data 03: Parquet | Layout measurements, candidate groups versus fetched bytes, nested values. |
| Data 04: Table formats | Metadata-to-file lookup, ACID behavior, consumer compatibility. |
| Data 05: Spark | Execution roles, join algorithms, driver memory, partial aggregation, salting. |
| Data 06: Kafka/CDC | Processing/commit/crash order, database updates, watermark limits, checkpoint barriers. |
| Data 07: Modeling/dbt | Historical classification, references/materialization, incremental replacement, remote work after timeout. |
| Data 08: Quality/SLO | Missing inputs, independent denominators, publication states, failure policies, checker outages. |
| Data 09: OpenTelemetry | Service versus operation identity, propagation versus recording, sampling versus counting. |
| Data 10: Telemetry backends | Absent series, counter resets, histograms, label growth, recording rules. |
| Data 11: Lineage/governance | Facets, table/column relationships, collection gaps, account-based access tests. |
| Data 12: Cloud platforms | Scheduled identities, catalog/storage roles, stream consumption, refresh intent, MERGE limits. |
| Data 13: AI data/evaluation | Vector proximity versus relevance, rank fusion, graph relationships, held-out evaluation. |
| Data 14: Operations | Code/data recovery, compatible recovery points, catch-up time, rollout decisions, response order. |
| Data 15: Capstone | Conflict rejection and the transition from local correctness to service integration tests. |
| Data 16: Source review | Using the source map; teaching examples versus product evidence. |
| SRE 00: Roadmap | Slow-service scenario, measurement, targets, alerts, natural Korean terminology. |
| SRE 01: Signals/SLO | Failed-payment investigation, telemetry terms, responsibilities, error budgets, incident response. |
| SRE 02: Correlation lab | Counter/rate interpretation, causal uncertainty, alert tests, recovery, response instructions. |

## Verification and limits

Changed explanatory passages were compared with their paired English sources. Primary-source spot checks covered [Kafka delivery ordering](https://kafka.apache.org/41/design/design/), [Flink checkpoint barriers](https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/stateful-stream-processing/), [OpenTelemetry propagation](https://opentelemetry.io/docs/concepts/context-propagation/), and [SRE alerting](https://sre.google/workbook/alerting-on-slos/). This is not a fresh technical audit of every product claim; original evidence dates remain unchanged.

All 24 documentation tests, the 94-document publication check/build, the harness verifier, and all seven standard-library course fixtures passed. Local Chrome opened all 20 revised articles at desktop and mobile widths (1440 and 390 pixels), expanded all 102 chapter definitions, exercised Korean/English/paired modes, verified shared code counts and all 11 diagrams, and found no page overflow or JavaScript exceptions. Desktop and mobile screenshots were also inspected.

The review does not measure reader comprehension. Advanced sections still require the prerequisites taught earlier. Code and Mermaid labels remain shared with English. Distributed and managed-platform exercises were not deployed for this editorial change.
