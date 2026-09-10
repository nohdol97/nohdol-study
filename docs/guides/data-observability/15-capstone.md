# Capstone: one evolving data and observability platform

Build a synthetic order-data product and an assistant that can answer questions about its published results. Keep the same data contract as you add distributed processing, governance, and AI. Each phase ends with evidence that another engineer can reproduce.

## Lab prerequisites and scope

The first exercise needs only Python 3 and uses no files or network. Later phases require your selected, version-pinned local services and eventually an optional managed-platform account. Use synthetic data throughout. Cloud experiments require a budget, a disposable namespace, and a cleanup inventory.

The following stages are learning assignments. The documentation deployment does not deploy Kafka, Spark, Databricks, Snowflake, or a live AI service on your behalf. Record your own executed commands, versions, measurements, and gaps as you complete them.

## Understand the model first

| Entity | Identity and promise |
|---|---|
| Event | Stable event ID, version, event time, amount unit, currency, source position |
| Processing run | Code revision, contract revision, source range, runtime and input versions |
| Publication | Dataset version, eligible interval, check outcomes, publication time |
| Retrieval index | Source dataset/document versions, chunking and embedding revisions, policy version |
| Answer | Request identity, authorized evidence references, prompt/model revisions, evaluation result |

Use a single identity convention across the stages. A trace, a lineage event, and a publication receipt should link through a run ID while preserving their different responsibilities.

## Phase 1: a correctness oracle you can run now

Save the following as `oracle.py` in your chosen scratch directory and run `python3 oracle.py`. It defines a small in-memory fixture. Only USD orders with valid identities and non-negative integer cents are eligible. Identical retries are deduplicated; conflicting payloads are surfaced separately. This is an oracle for the fixture, not a streaming engine.

```python
def reconcile(events):
    accepted = {}
    rejected = []
    conflicts = []
    for event in events:
        event_id = event.get("event_id")
        amount = event.get("amount_cents")
        if (not isinstance(event_id, str) or not event_id
                or type(amount) is not int or amount < 0
                or event.get("currency") != "USD"):
            rejected.append(event)
            continue
        if event_id in accepted and accepted[event_id] != event:
            conflicts.append(event_id)
            continue
        accepted[event_id] = event.copy()
    return accepted, rejected, conflicts

base = [
    {"event_id": "e1", "amount_cents": 100, "currency": "USD"},
    {"event_id": "e2", "amount_cents": 250, "currency": "USD"},
]
valid, rejected, conflicts = reconcile(base + base)
assert len(valid) == 2
assert sum(row["amount_cents"] for row in valid.values()) == 350
assert not rejected and not conflicts

bad = {"event_id": "e3", "amount_cents": -10, "currency": "USD"}
assert len(reconcile(base + [bad])[1]) == 1
changed = {"event_id": "e1", "amount_cents": 120, "currency": "USD"}
assert reconcile(base + [changed])[2] == ["e1"]
assert set(reconcile(base[:1])[0]) != {"e1", "e2"}  # Missing input detected.
assert reconcile(list(reversed(base)))[0] == reconcile(base)[0]
print("PASS: replay, totals, invalid values, conflicts, missing input, ordering")
```

Do not publish a result when `conflicts` is nonempty: this toy function retains the first accepted payload for diagnostics, not as an approved conflict-resolution rule. Define version ordering and correction semantics before teaching the distributed sink to handle updates.

## Phase 2: files and committed tables

Write the accepted synthetic events to Parquet, verify counts and totals, and compare projected/filtering queries. Introduce a missing file and require a failed completeness check. Add Iceberg or Delta, record versions before and after appends, and demonstrate a supported snapshot query and a restore exercise.

Deliver: data generator, schema, expected ledger, file-layout measurements, table history, and the recovery procedure. Explain which evidence proves physical layout and which proves business totals.

## Phase 3: Kafka and Spark

Send the same fixture through Kafka into Spark and the table sink. Preserve offsets and event IDs. Add identical retries, conflicting versions, out-of-order records, late records, and a consumer restart. Compare the distributed output against the oracle for the cases its contract covers; extend both deliberately for event-time and update semantics.

Deliver: connector/runtime manifest, checkpoint and sink commit strategy, Spark plan/task evidence, and a replay receipt. Demonstrate a crash after sink publication and verify the business result is not counted twice.

## Phase 4: a governed data product

Build dbt staging and a daily-revenue mart, schedule explicit intervals, and gate publication with schema, key, unit, completeness, and deadline checks. Add owner and contract metadata. Emit lineage for the actual runs and connect source positions to table versions and mart outputs.

Deliver: passing and failing fixtures, an incremental/full-rebuild comparison, a bounded backfill, an allow/deny test, and an impact query. Missing lineage must appear as a gap, not an empty blast radius.

## Phase 5: operational evidence

Instrument processing and publication with OTel. Add Prometheus metrics and a Grafana consumer-outcome view, then connect logs and traces through run references. Record label budgets, retention, and observation-coverage checks.

Deliver: a slow-stage incident, a stale-but-HTTP-healthy dataset incident, and an independent telemetry outage. Demonstrate recovery and reconcile data and signal loss separately.

## Phase 6: managed implementation and AI

Reimplement the established contracts on Databricks. Preserve fixture identities and expected outputs. Compare Snowflake afterward using the same workload. Add a small synthetic retrieval corpus and a constrained assistant whose source/index/model/prompt revisions are recorded.

Deliver: account-specific capability notes, quality/lineage/access/recovery checks, cleanup evidence, cost breakdown, and an evaluation set covering missing, stale, forbidden, and conflicting evidence. Cloud and AI calls are optional until you have an environment and budget; the local correctness phases remain useful independently.

## Graduation failure matrix

| Fault | Evidence required before calling recovery complete |
|---|---|
| Duplicate event | Same intended unique keys and totals after replay |
| Conflicting update | Quarantine or declared version resolution with no silent first-writer policy |
| Late event | Accepted/corrected/rejected counts and downstream reconciliation |
| Schema or unit change | Consumer compatibility outcome and a versioned migration |
| Consumer or executor crash | Resumed progress plus correct published output |
| Lost checkpoint or table metadata | Isolated restore/replay with measured recovery time and explicit gaps |
| Missing scheduled run | Included in the SLO denominator and repaired through a bounded backfill |
| Collector/backend outage | Known telemetry backlog/loss and an observation-coverage alert |
| Missing lineage event | Declared coverage gap and verified affected consumer investigation |
| Revoked source access | No forbidden retrieval, prompt, answer, or debugging exposure |
| Bad AI answer | Evidence-based diagnosis and a retained regression evaluation |

## Explain it in your own words

Present a fifteen-minute architecture review and a fifteen-minute incident replay. For every success claim, show the fixture, measurement, source version, or policy check that supports it. State what you have not run. Another engineer should be able to reproduce the small tests and understand why larger-scale claims need separate evidence.

## Portfolio checklist

Keep architecture decisions, version locks, synthetic fixtures, correctness tests, query plans, incident timelines, restoration receipts, cost calculations, and teardown steps in one project. Never replace a measured failure with an idealized diagram. Revisit this course when the next failure exposes a gap.

Return to the [roadmap](00-roadmap.md) or inspect the [source review](16-source-review.md).

<!-- source: https://chatgpt.com/share/6aa266f6-db88-83ee-a8d7-3e7aa8e0821d?ogimg=plain | checked: 2026-09-10 | one evolving project is curriculum input; fixture and graduation criteria are original synthesis -->
