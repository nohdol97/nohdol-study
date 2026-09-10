# Full documentation review and lab results

- Reviewed: 2026-09-10
- Scope: all 94 catalog learning documents across 21 topics, supporting docs/, navigation, and operational example READMEs
- Acceptance: [Documentation review specification](../specs/2026-09-10-documentation-review.md)
- Public entry: [Study Gateway](https://nohdol97.github.io/nohdol-study/)

The review corrects technical explanations and exercises, adds **Example results** to 42 lab or exercise chapters, and distinguishes historical decisions from current operating instructions. The catalog retains its existing document IDs and publication boundary. The personal knowledge root is not changed by this work.

## Material corrections

| Area | Problem found | Resulting behavior or explanation |
|---|---|---|
| Terraform | A plan-only test asserted a computed output that can remain unknown | Assert planned input, explain exit codes 0/1/2 and the end of plan locking |
| Helm and GitOps | Incomplete chart scaffold and ambiguous release ownership | Supply four complete chart files, verify schema rejection, distinguish Helm CLI releases from Argo CD template rendering, and scope flags by major version |
| Networking | Route lookup used an unrelated destination; SNI was confused with hostname verification | Resolve the actual destination, explicitly verify the hostname and chain, and separate TCP refusal, DNS failure, TLS failure, and HTTP outcomes |
| Linux | Service privilege, served directory, and cleanup boundaries were unclear | Use a transient unprivileged service identity and scoped runtime directory; preserve unrelated failure state |
| Kubernetes | Port-forward and EndpointSlice diagrams blurred metadata and packet paths; storage startup rewrote the persistence marker | Explain the API tunnel and ready endpoints, write the marker once before Pod replacement, and distinguish scheduling, image preparation, readiness, and rollout |
| PostgreSQL and backend | Transaction examples could disconnect an event from its created order or leave duplicate effects unguarded | Use INSERT RETURNING and guarded updates; supply temporary fixtures and verify business state, locks, constraints, and isolated restoration |
| Observability | Alert rules lacked the full burn-rate definition and testable input boundaries | Provide both windows, the SLO denominator, six time-series fixtures, and separate missing evidence from a healthy result |
| Security and traffic | A missing upload file could masquerade as an IAM test; TLS prerequisites and retry accounting were incomplete | Create the local deny fixture, distinguish secret labels from credential revocation, include certificate references, and calculate the full attempt budget |
| Karpenter | Voluntary disruption controls were generalized to forceful paths | Separate budget-controlled voluntary disruption from expiration, interruption, and repair; clarify scheduled Pending Pods |
| AI and AIOps | Translation errors reversed mechanisms; candidate evidence and operation states were underspecified | Correct LoRA, diffusion terminology, recommendation, and gang-scheduling descriptions; add KV-cache arithmetic, evaluation leakage boundaries, evidence references, and bounded reconciliation |
| Data platform | A small default Parquet row group could hide layout differences; the oracle only described a publication gate | Set an explicit row-group size and test sorted/unsorted candidates; reject invalid, incomplete, and conflicting input before returning a replacement snapshot |

Changed version-sensitive claims retain source URLs and review dates in their Markdown source comments. Unchanged historical source dates are not advanced merely because a chapter was reread. This is not a claim that every linked vendor page or historical dependency received a new audit.

## Whole-catalog coverage

Each row covers the roadmap and every chapter in that topic. Examples are execution outputs for runnable fixtures or labeled review receipts for plan-only assignments; conceptual chapters are not presented as executed labs.

| Topic | Documents reviewed | Result-example chapters | Review emphasis |
|---|---:|---:|---|
| Kubernetes | 11 | 10 | API ownership, networking, persistence, scheduling, RBAC, debugging, overlays |
| Linux | 3 | 1 | Process/resource model, port conflict, privilege and cleanup |
| Networking | 3 | 1 | DNS, destination route, TCP, TLS identity, HTTP |
| AWS foundations | 3 | 1 | Caller identity, routing, audit coverage, read-only limits |
| Terraform | 3 | 1 | Planned values, test semantics, drift, locking, exit codes |
| Helm and GitOps | 3 | 1 | Complete rendering fixture, schema, release ownership, rollback |
| Observability and SRE | 3 | 1 | Signal correlation, SLI math, missing series, alert recovery |
| PostgreSQL | 3 | 1 | MVCC visibility, WAL durability scope, lock wait, restore |
| NoSQL | 3 | 1 | TTL versus eviction, hot keys, access-pattern limits |
| Infrastructure security | 3 | 1 | Allow/deny pairs, identity, credential lifecycle, artifacts |
| Messaging | 3 | 1 | Atomic deduplication, replay, poison messages, DLQ reconciliation |
| Reliability and FinOps | 3 | 1 | Recovery objectives, capacity, cost, scoped capstone evidence |
| Karpenter | 3 | 1 | Provisioning versus scheduling, disruption classes and recovery |
| Traffic resilience | 3 | 1 | Route attachment, TLS prerequisites, retries, deadlines, ejection |
| Backend engineering | 7 | 1 | API semantics, invariants, concurrency, workflows, cache, delivery |
| AI Specialist | 6 | 0 | Model mechanisms, memory arithmetic, compression, evaluation, retrieval |
| AI Transformation | 5 | 0 | Serving, lifecycle, quotas, FinOps, agent execution contracts |
| AIOps foundations | 3 | 1 | Incident identity, time window, field presence versus evidence |
| AIOps diagnosis | 3 | 1 | Correlation versus causation, test leakage, abstention and coverage |
| AIOps remediation | 3 | 1 | Approval binding, unknown outcomes, bounded reconciliation |
| Data and Observability | 17 | 15 | End-to-end data correctness, telemetry, governance, cloud and AI |
| **Total** | **94** | **42** | All three learning paths |

## Supporting documentation

All nine ADRs were reviewed for current-state consistency. ADRs 002 and 003 now point to NotebookLM withdrawal; ADRs 008/009 and the initial gateway specification explain the selected docs/ course extension. Earlier decisions remain readable as historical rationale.

The existing eight implementation specifications, three historical reviews, direction proposal, session handoff, docs map, changelog, root README, skill guide, public-site guide, workspace-portal guide, and feed/Telegram guides were checked for scope and navigation. Historical measurements and completed task lists are explicitly dated instead of being presented as today's capabilities or active backlog. The new review specification and this receipt document the additional work.

Feed and Telegram setup instructions were checked against their reference code. The guides now distinguish HTTP requests from model calls, generated reading queues from verified notes, sequential marker deduplication from concurrent writes, and read-only filesystem access from external transmission. Credentials are injected outside the harness, vault, and workspace. The Telegram guide explicitly states that an empty allowed-chat setting permits all chats in the current template; this review does not silently change a running installation.

## Verification receipt

| Check | Observed result |
|---|---|
| Site tests | 9 tests pass, including all 22 JSON fixtures, internal document routes, and output-to-execution comparison |
| Python and SQLite | The documented output `[('c1', 350)]` and capstone PASS line match execution; disabling the publication gate is detected |
| Terraform 1.16.0 | fmt, init, validate, plan-only test, valid plan, and invalid environment rejection pass; no apply |
| Helm 4.3.0 | Complete chart lint/render pass; two-replica output and zero-replica schema rejection verified |
| kubectl Kustomize | Rendered `prod-study-web`, four replicas, and the selected image tag match the overlay |
| DuckDB 1.5.0 | 100,000 rows / 10,000,000 cents; selected day 3,334 / 333,400; candidate row groups sorted=1 and event-ID ordered=13 |
| PostgreSQL 18.1 | Conditional inventory update, outbox key/payload match, duplicate effects 1→1, rollback/retry 1→2, blocked transaction, restored 2 rows / 200.00, and restored constraint rejection pass |
| promtool 3.14.0 | Three rules parse; six alert fixtures pass, including reset, recovery, zero traffic, and missing series |
| Browser | All 94 desktop and 390-pixel mobile routes load without page overflow; 108 Mermaid diagrams render without errors; search, cross-topic links, and diagram viewer work |
| Harness | `verify_harness.py` passes for 18 skills |
| Operational references | Feed engine, wrapper, and bot fixture tests pass; bot tests use the existing dependency environment and make no Telegram calls |

The reusable [local-check instructions](../../docs-site/labs/README.md) provide the PostgreSQL runner and Prometheus fixtures. Other tool checks use code copied directly from the reviewed chapter into temporary directories. Tool downloads and the PostgreSQL build were confined to temporary locations; no optional global tool was installed.

## Limits and learner evidence

Linux/systemd execution, a live Kubernetes cluster or Redis server, EKS/Karpenter, cloud IAM, managed brokers, Spark, Databricks/Snowflake, and production telemetry/AI services were not deployed or exercised in this review. Their outputs are labeled expected or synthetic. The PostgreSQL test does not establish PITR, high availability, or a production RPO/RTO; the alert fixtures do not establish live scrape coverage. Fresh Telegram/agent sessions and launchd service behavior were not tested.

For a learner's execution receipt, retain the actual command, tool version, selected environment, timestamp, exit code, output, and the business-result assertion. Replace example IDs and measurements with observed values while preserving failures and evidence gaps. An example transcript is a comparison target, never proof that the learner ran it.
