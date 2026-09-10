# Platform operations: releases, recovery, capacity, and cost

A platform is operable when another engineer can change it, diagnose it, and restore its consumer outcome using recorded procedures. Add infrastructure only as the learning system needs reproducible deployment, isolation, or scale.

## Terms introduced in this chapter

| Term | Meaning |
|---|---|
| RPO | Recovery Point Objective: the acceptable amount of lost progress/data measured against a recovery point |
| RTO | Recovery Time Objective: the target time to restore the agreed service outcome |
| Canary | A constrained rollout used to observe a change before widening it |
| Backpressure | Slowing upstream work when downstream capacity is insufficient |
| Workload identity | The identity a running service uses to obtain permissions |
| Unit cost | Total relevant cost divided by a meaningful unit of successful work |

## Understand the model first

1. Version application code, schemas, contracts, infrastructure, and observability configuration.
2. Validate compatibility and correctness against isolated fixtures.
3. Release to a constrained environment or workload slice.
4. Observe consumer outcomes and capacity, then widen or stop.
5. Reconcile data state during rollback and retain evidence of the release.

Containers package a runtime; they do not define where durable checkpoints live. Kubernetes manages workloads and resources; it does not make an application sink transactional. Terraform manages declared infrastructure; it does not prove a table backup is restorable. Use the existing [Kubernetes roadmap](../../../docs-site/content/kubernetes/00-roadmap.md) and [Terraform roadmap](../../../docs-site/content/terraform-aws/00-roadmap.md) as supporting tracks when these responsibilities appear.

## Release code and data contracts together

| Change | Compatibility question |
|---|---|
| Add a field | Can old readers ignore it and new readers handle historical absence? |
| Rename or change a type | Is there an overlap period and a tested consumer migration? |
| Change a unit or business rule | Is the semantic version visible even if the physical schema is unchanged? |
| Change a streaming stateful operator | Can the selected engine restore the existing checkpoint safely? |
| Enable a table protocol feature | Can every required reader still read and every writer still commit? |

Use expand-and-contract where appropriate: introduce a compatible representation, populate and compare it, migrate consumers, and remove the old representation after observation. Rolling code back cannot automatically undo output already published under a changed business rule. Keep code rollback, data correction, and consumer re-publication as explicit operations.

CI should check schemas and examples, run small deterministic correctness fixtures, compare incremental and full-rebuild results, and exercise allow/deny boundaries. Keep large throughput tests separate and record their environment. A green unit suite is not a capacity benchmark.

## Recovery includes more than table files

Inventory Kafka/source replay retention, source database logs, table metadata and objects, catalog state, stream checkpoints, orchestration metadata, schema registry, policy definitions, and telemetry/lineage retention. Choose recovery points that are mutually usable. A checkpoint beyond available input or pointing to an incompatible sink state can make recovery fail or produce incorrect output.

Rehearse restoration into an isolated destination. Reconstruct the catalog and table, restore a compatible processing state or perform a deliberate replay, rerun checks, and query as the consumer identity. Measure the recovery duration from incident start to the agreed consumer outcome; the backup-download duration alone is not RTO.

Retain raw sources according to policy without quietly deleting evidence during repair. Document when a full replay is impossible and what reconstruction source is available. If the required source history is gone, state the data gap explicitly rather than declaring a successful restart to be full recovery.

## Capacity and cost as a coupled problem

If ingestion averages 10 MB/s and processing stops for an hour, the illustrative backlog is 36 GB in decimal units before replication and overhead. To drain it in another hour while live traffic continues at 10 MB/s, the processor needs an average effective rate of at least 20 MB/s over that recovery period. Measure sink throughput as well; faster reads can simply move the bottleneck.

Watch queue age, storage headroom, source retention, and downstream concurrency together. Backpressure prevents unbounded in-memory accumulation only if upstream systems have a durable place to wait and a policy when that place fills. Autoscaling does not remove an external API rate limit or a hot partition.

Define units such as cost per million **valid published events**, cost per refreshed dataset interval, or cost per successful AI task. Include idle compute, retries, scans, compaction, storage, transfer, telemetry, quality checks, and governance services. A lower cost per attempted event can hide dropped data or failed quality gates.

## An operator's incident sequence

Start from the impacted consumer and time range. Check observation coverage, identify the last valid publication, and follow run and lineage references upstream. Form candidate causes and look for counterevidence. Contain harmful publication or load, repair the underlying condition, replay a bounded interval, and reconcile expected output. Restore alerts and temporary policies after recovery.

Write a post-incident record containing timeline, affected datasets/consumers, actual cause evidence, contributing conditions, recovery actions, remaining gaps, and a regression fixture. A screenshot of a red panel followed by a green panel omits most of that knowledge.

## Example results

Calculated capacity worksheet, not a provider benchmark or price quote.

```text
incoming rate: 100 events/s
recovery processing rate: 300 events/s
backlog: 360000 events
net drain rate: 200 events/s
drain estimate: 1800 seconds
processing rate <= incoming rate: backlog cannot drain
```

If the recovery window is 20 minutes, a 30-minute drain fails even when restart succeeds. Check retention and downstream bottlenecks. Report accepted-publication cost with idle, storage, transfer, and recovery charges included.

## Explain it in your own words

What happens if code rollback succeeds but a downstream index still contains the bad version? Which recovery components must be restored together? Calculate the catch-up capacity for your workload and identify the first retention window that would expire.

Continue with the [capstone](15-capstone.md).

<!-- source: https://spark.apache.org/docs/latest/streaming/apis-on-dataframes-and-datasets.html | checked: 2026-09-10 | recovery semantics after query changes -->
<!-- source: https://sre.google/workbook/implementing-slos/ | checked: 2026-09-10 | consumer-outcome objectives; recovery and capacity exercises are design synthesis -->
