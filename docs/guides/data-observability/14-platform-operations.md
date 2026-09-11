# Platform operations: releases, recovery, capacity, and cost

The engineer who built the pipeline is away when it fails. Can a teammate find the problem and restore the dataset using the recorded procedure?

This chapter makes that recovery repeatable. Add deployment automation, isolation, and capacity as the learning system needs them, and check their cost against useful work.

## Terms introduced in this chapter

| Term | Meaning | Why it matters / when to use it |
|---|---|---|
| RPO | Recovery Point Objective: the acceptable amount of lost progress/data measured against a recovery point | Set backup and replication requirements according to how much recent progress may be lost. **Concrete situation (illustrative):** The recovery requirement permits five minutes of lost progress. → Inspect backup and replication recovery points. → Verify the actual recoverable point meets that limit. |
| RTO | Recovery Time Objective: the target time to restore the agreed service outcome | Choose and rehearse a recovery approach that fits the maximum acceptable interruption. **Concrete situation (illustrative):** The service must recover within thirty minutes. → Rehearse detection, restore, and verification as one timeline. → Compare the measured total with the RTO. |
| Canary | Trying a change on a limited scope and observing it before exposing more users or data. | Limit exposure while comparing a new release's outcomes with an established baseline. **Concrete situation (illustrative):** A pipeline release might corrupt derived data for all consumers. → Expose a limited, representative scope with explicit stop criteria. → Compare correctness and operational signals before widening rollout. |
| Backpressure | Slowing upstream work when the downstream system cannot keep up. | Prevent an overloaded downstream stage from creating unbounded upstream queues or wasted work. **Concrete situation (illustrative):** Events arrive faster than downstream storage can accept them. → Apply bounded buffering and supported upstream flow control. → Verify memory remains bounded and the overload policy is visible. |
| Workload identity | The identity a running service or job uses to request permissions. | Give a running service scoped permissions and attributable actions without embedding permanent user secrets. **Concrete situation (illustrative):** A scheduled job needs storage access without a long-lived embedded key. → Bind its runtime identity to narrowly scoped permissions. → Test token acquisition, allowed actions, and denied unrelated access. |
| Unit cost | The relevant total cost divided by a meaningful amount of successfully completed work. | Compare operating designs using all relevant costs per valid successful output. **Concrete situation (illustrative):** Total platform spending rises, but the team cannot tell whether efficiency worsened. → Normalize attributed cost by a meaningful workload unit. → Compare cost per successful unit alongside volume and service quality. |

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

## Docker, Kubernetes, and Terraform in the data path

A container image should make the transform's runtime reproducible: pin a reviewed base/dependency set, package the same module tested in CI, run with the intended user, and supply configuration through the deployment environment. Mutable notebook state and unrecorded packages defeat that purpose. Keep credentials outside the image and build context. Store checkpoints and output in deliberately durable locations, not the container's disposable writable layer.

For Kubernetes, requests affect scheduling and limits affect available resources under the platform's rules. A Spark executor also needs non-heap/native/Python-worker memory, so its pod memory budget cannot be derived only from JVM heap. A liveness probe that restarts a legitimately long batch can create an endless replay loop. Readiness indicates whether a service should receive traffic, not whether yesterday's dataset is complete.

Workload identity should bind the running component to only its source, sink, checkpoint, and telemetry permissions. Network policy and storage permissions enforce different boundaries. Test a forbidden dataset read under the workload's actual identity, and record the denial. Resource isolation also matters: a large historical backfill should not consume all capacity needed for current publication.

Terraform makes infrastructure changes reviewable through configuration and plans. A plan can show the creation of a bucket or role; it does not validate the table's row-level business contract. State and provider credentials require appropriate storage/access. Keep infrastructure rollback distinct from restoring an already changed dataset. The existing infrastructure tracks provide complete container/orchestration/IaC exercises; use them when this project reaches those boundaries.

## A release bundle and a promotion decision

Promote a bundle containing code revision, runtime/dependencies, source/schema/contract revisions, table features, transformation definitions, policy revision, and telemetry schema. A golden input fixture should include a duplicate, conflicting update, null, late correction, delete, missing interval, and unauthorized caller. Compare full and incremental output by keys/values as well as count and sum.

Run a candidate on a bounded interval or shadow destination, then compare consumer queries against the approved version. Keep candidate output isolated until its checks pass. If a release changes a currency or history rule, a code rollback may leave already written rows and an AI index using the new meaning; plan the correction/republication as part of the release design.

Define an explicit promotion condition such as “all hard invariants pass, no forbidden read, current intervals remain within deadline, and measured catch-up capacity exceeds the required rate.” A canary that sees only easy keys does not establish behavior for skewed keys or late updates. Select representative slices deliberately.

## Recovery arithmetic: replay budget and bottlenecks

For backlog `B`, arrival rate `lambda`, and effective processing rate `mu`, a steady-rate drain estimate is `B / (mu-lambda)` when `mu > lambda`. When `mu <= lambda`, the backlog cannot drain. Use units consistently: events, encoded bytes, replicated bytes, and compressed Parquet bytes are different quantities.

Suppose the replay source keeps six hours of history, detection takes two hours, restoration one hour, and catch-up is estimated at two hours. Only one hour remains for variation before the oldest needed input can expire, assuming retention/positions behave as modeled. Include checkpoint age, source clock, and table recovery point in that analysis. Increasing compute helps only if the source, network, key distribution, and sink can supply/use the added throughput.

A platform should expose backfill admission controls, bounded retries, source-retention alarms, and per-dataset publication evidence. Repeatedly retrying a permanent schema error consumes compute while preserving the same bad outcome. Classify retryable transport/capacity failures separately from invalid inputs and incompatible contracts.

## Unit economics and self-service boundaries

Compute cost per million valid published events using the same accounting period for numerator and denominator. Include ingestion, transforms, failed retries, compaction, storage, transfer, query serving, telemetry, and required checks. If a design drops half the eligible events, its apparent throughput/cost improvement must fail the completeness gate before comparison.

A self-service dataset registration can generate pipeline configuration, quality rules, ownership metadata, dashboards, and access-policy requests. The registration schema should require grain, source/change identity, freshness/completeness population, retention, owner, and permitted consumers. Validate it and compile it into reviewable artifacts. Do not let a YAML label such as `certified: true` replace executed checks and an approved owner decision.

Treat the generated platform artifacts as versioned derivatives of the registration and templates. On template changes, show which datasets are affected, test representative fixtures, and roll out gradually. This is the operational bridge from one working pipeline to a platform serving multiple teams.

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
