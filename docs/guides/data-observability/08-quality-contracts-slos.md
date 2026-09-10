# Data quality, contracts, and outcome-based SLOs

The platform owner cannot decide alone what “good data” means. A domain owner defines business meaning and acceptable defects; platform engineers make those rules measurable and enforceable. Consumers help set deadlines and fallback behavior.

## Terms introduced in this chapter

| Term | Meaning |
|---|---|
| Validity | Whether values meet declared type, range, or format rules |
| Completeness | Whether expected records or fields are present |
| Accuracy | Agreement with the real-world fact or an authoritative reference |
| Freshness | How current the data is under a specified clock and delivery model |
| Contract | A versioned agreement covering meaning, ownership, structure, and service expectations |
| Error budget | The amount of failure allowed by an SLO over its defined window |

## Understand the model first

1. Define a consumer outcome and its eligible population.
2. Measure records or delivery intervals against explicit rules.
3. Record measurement time, input version, and check implementation.
4. Decide whether to publish, quarantine, fail, or serve a labeled prior version.
5. Alert an owner and verify consumer recovery after repair.

Uniqueness and non-null checks are useful but cannot prove completeness. Ten perfectly valid rows may be nine thousand rows short. Compare against an independent expected ledger, upstream control totals, or a clearly labeled estimate. Accuracy similarly needs a reference or domain review; a regex cannot establish whether a valid-looking address is correct.

## An illustrative contract

This YAML is a design artifact, not a configuration accepted by dbt, Soda, or Great Expectations. Map each rule to executable checks in your chosen implementation.

```yaml
dataset: orders.accepted
contract_version: "1.0"
owner: commerce-data
grain: one_current_record_per_event_id
time_basis: UTC
key: event_id
amount_unit: cents
required_fields: [event_id, event_time, amount_cents, currency]
delivery:
  interval_minutes: 5
  deadline_after_interval_end_minutes: 10
  eligible_intervals: all_scheduled_intervals
  missing_measurement: unknown_and_alert
quality:
  duplicate_ids: 0
  unknown_currency_rows: 0
  reconcile_to: source_control_totals
publication:
  on_failure: hold_candidate_and_label_last_good
```

Notice that units, clocks, expected intervals, missing measurements, and publication behavior are part of the agreement. A schema-only contract omits most of what an operator needs during an incident.

## Define freshness without hiding gaps

`now - max(event_time)` measures the age of the newest observed event. One fresh event can make it look healthy while a partition or region is missing. A quiet source can make it look stale while behaving correctly. Clock skew can even make it negative.

For a scheduled dataset, define freshness against expected intervals and their publication deadlines. For a continuous stream, combine event-to-publication delay, expected source progress or heartbeats, and completeness by relevant segment. Track event time, ingestion time, and publication time separately. They answer different questions.

| Measurement | Denominator and edge case |
|---|---|
| Duplicate fraction | Extra rows beyond distinct valid identities / eligible received rows; define zero-input behavior |
| Completeness | Accepted expected identities / independent expected identities; unknown without the reference |
| On-time publication | Valid intervals published before deadline / all eligible intervals, including missed runs |
| Check coverage | Expected checks that produced a fresh result / all expected checks |

## Worked SLO example

Suppose a 30-day period has exactly 8,640 eligible five-minute intervals. An illustrative 99.9% on-time valid-publication SLO permits at most eight failed intervals if the observed success fraction must meet the target: nine failures would fall below 99.9%. This is a mathematical example, not a universal business target.

If the scheduler never launched a run, that interval still belongs in the denominator. If the quality checker stopped, distinguish “unknown” from “passed”; the publication policy can fail closed or serve a clearly labeled previous version according to consumer requirements.

An error budget for on-time delivery does not authorize incorrect monetary totals or access-policy violations. Some invariants require zero tolerated violations and a separate response.

## Quality tools and publication

Start with SQL assertions and dbt data tests. Evaluate Great Expectations or Soda when reusable expectation/check definitions, connectors, and reporting reduce work across datasets. Their check engines do not choose business ownership or make a publication transaction automatically.

Run checks against a candidate version before exposing it. Store failed-record samples under a controlled policy, record the full failure count, and keep consumers informed about the last valid version. A “drop bad rows” policy changes completeness and must be visible in accounting.

## Failure exercise and interpretation

Create one missing scheduled interval, one duplicated ID, and one absent check result. The system should identify three different problems. Repair the duplicate, replay the interval, restart the checker, and verify both data and observation coverage. Keep the failure ledger after recovery rather than replacing historical failures with a green current status.

## Explain it in your own words

Why can freshness improve while completeness worsens? Explain the denominator and authority behind every percentage on your dashboard. Identify which quality rules need domain approval and which are mechanical type checks.

Continue with [OpenTelemetry](09-opentelemetry.md).

<!-- source: https://docs.getdbt.com/docs/build/data-tests | checked: 2026-09-10 | executable data assertions; contracts and SLO arithmetic are teaching synthesis -->
<!-- source: https://sre.google/workbook/implementing-slos/ | checked: 2026-09-10 | outcome-oriented SLIs and SLOs -->
