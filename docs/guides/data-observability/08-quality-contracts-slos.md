# Data quality, contracts, and outcome-based SLOs

A report arrives on time but omits one region's orders. Is that good data? The answer depends on what its consumers were promised.

The business owner defines the meaning and acceptable errors. Platform engineers turn those rules into checks. Consumers help decide delivery deadlines and what to do when data is unavailable.

## Terms introduced in this chapter

| Term | Meaning | Why it matters / when to use it |
|---|---|---|
| Validity | Whether a value follows its declared type, range, and format rules. | Reject values that violate the accepted schema or domain before publishing data. **Concrete situation (illustrative):** A feed contains impossible negative quantities under its business rules. → Validate values against the declared domain constraints. → Quarantine or reject invalid rows and report their count. |
| Completeness | Whether all expected records and required fields are present. | Detect absent expected inputs that cannot be found by testing only the rows that arrived. **Concrete situation (illustrative):** A daily report looks normal, but one region's file never arrived. → Check expected partitions and required-field coverage. → Flag the missing region even when received rows pass value checks. |
| Accuracy | Whether the data agrees with the real fact or a trusted reference. | Check truth against a trusted reference when syntactically valid data may still be wrong. **Concrete situation (illustrative):** A dataset passes format checks but lists the wrong delivery addresses. → Compare a justified sample with an authoritative reference. → Record disagreement rather than treating valid formatting as correctness. |
| Freshness | How up to date the data is, measured using an explicitly chosen timestamp and delivery rule. | Detect stale delivery using the clock and consumer expectations defined for the dataset. **Concrete situation (illustrative):** A dashboard responds quickly but still displays yesterday's orders. → Track the latest usable source and processed timestamps against a target. → Alert on stale data even when the query endpoint is healthy. |
| Contract | A versioned agreement about a dataset's meaning, structure, owner, and expected service. | Give producers and consumers a reviewable agreement for meaning, changes, and service obligations. **Concrete situation (illustrative):** A producer renames a field that several downstream models require. → Define schema, semantics, ownership, and compatibility expectations in a data contract. → Test the change against consumers before rollout. |
| Error budget | The failures an SLO allows during its measurement window. | Prioritize reliability and release decisions according to the failure allowance that remains. **Concrete situation (illustrative):** Repeated pipeline delays threaten an agreed freshness objective. → Calculate consumed error budget over the defined window. → Use the remaining allowance to prioritize reliability work and release decisions. |

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

## Six quality dimensions require different evidence

Validity asks whether a value satisfies the declared domain, such as a supported currency and a non-negative integer amount. Uniqueness asks whether identities are repeated; define whether the duplicate fraction counts extra copies or every row belonging to a duplicate group. Completeness asks what expected data is missing, so its denominator comes from a source ledger, control total, or other explicitly qualified expectation. Accuracy asks whether the value matches an authoritative fact, which can fail even when validity passes.

Consistency compares representations that should agree: the sum of accepted order lines versus the order header, or the same currency/unit definition in two marts. Freshness compares a declared event, progress, or publication clock with a deadline. These dimensions can disagree. A fresh 120-cent value may be inaccurate against a 100-cent source, while an old 100-cent value is accurate but stale for a current-state consumer.

Here is a locally executable metric calculation, not a vendor quality-tool API. The source oracle is deliberately explicit, the accepted candidate excludes invalid records, and duplicate deliveries are counted before candidate deduplication. Conflicting values for an identity must go through the capstone conflict gate before using this simplified metric fixture.

<!-- executable: quality-dimensions -->
```python
expected = {'e1': 100, 'e2': 250, 'e3': 50}
deliveries = [('e1',100), ('e1',100), ('e2',270), ('bad',-1)]
valid = [(key,amount) for key,amount in deliveries
         if key in expected and type(amount) is int and amount >= 0]
candidate = dict(valid)  # Only identical duplicates exist in this fixture.
extra = len(valid) - len(candidate)
complete = len(set(candidate) & set(expected)) / len(expected)
accurate = sum(candidate[k] == expected[k] for k in candidate) / len(candidate)
assert (len(valid), extra, len(candidate)) == (3,1,2)
assert sum(candidate.values()) == 370
print(f'validity={len(valid)}/{len(deliveries)}')
print(f'extra_duplicate_fraction={extra}/{len(valid)}')
print(f'completeness={complete:.3f} accuracy_on_present={accurate:.3f}')
print(f'candidate_total={sum(candidate.values())} source_total={sum(expected.values())}')
print('publication=HOLD: missing e3 and incorrect e2')
```

Expected output:

```text
validity=3/4
extra_duplicate_fraction=1/3
completeness=0.667 accuracy_on_present=0.500
candidate_total=370 source_total=400
publication=HOLD: missing e3 and incorrect e2
```

A total comparison alone is insufficient: changing e2 to 300 would make the candidate sum 400 while still missing e3 and misrepresenting e2. Keep identity-level reconciliation where the domain requires it. In an empty population, report an explicit no-observation result rather than divide by zero or automatically declare 100% accuracy.

## Turn checks into a publication state machine

Use states such as `BUILDING -> CHECKING -> APPROVED -> PUBLISHED`, with failures producing a held candidate. Bind every result to the candidate version, rule revision, measured population, and completion time. A passing check on version A must not authorize version B written a minute later. Publish with a supported atomic pointer/swap/transaction after all required checks pass, and record the committed output identity.

Warning, quarantine, dropping, and failure are different policies. A warning permits publication with visible defects. Quarantine retains rejected records for repair and requires reconciliation. Dropping changes the delivered population; the dropped count belongs in completeness accounting. Failure blocks the proposed update, but the old version's availability and stale-data label need their own serving design.

For a schema change, first add a compatible field, populate it, run old/new consumer fixtures, then move consumers before removing the old representation. For a semantic change such as gross-to-net revenue, version the definition even if SQL column names/types stay identical. Ownership should specify who approves the rule and who is paged when it fails, rather than assigning every business decision to the platform team.

## dbt, Great Expectations, and Soda in the same workflow

dbt data tests fit relations already built by a SQL transformation graph. Great Expectations organizes expectations into suites and validation workflows; Soda expresses checks through its supported check language and scan/runtime. The useful comparison is whether your execution engine, deployment mode, failed-row handling, and result storage fit the publication boundary. A connector list is not proof that a tool can evaluate the same transaction snapshot the writer will publish.

Keep domain rules tool-independent in meaning, but translate them into the exact supported configuration. The earlier illustrative contract is not SodaCL or a GX suite. For example, “no null event IDs” maps easily across tools; “all expected customer partitions arrived by deadline” requires a schedule/reference population as well as a scan. Decide who stores that population before selecting a check library.

## SLO measurement, burn rate, and volume anomalies

If the allowed failure fraction is 0.001 and the observed failure fraction is 0.02, burn rate is `0.02 / 0.001 = 20`. At a constant comparable event rate, an hour at 20 times the budget rate consumes the same failure allowance as twenty hours at the target rate. Bursty workloads and interval-based SLOs require the actual eligible populations; clock duration alone cannot replace them.

A volume anomaly can detect an unusual drop before a strict reconciliation is available, but seasonality, holidays, and known source pauses affect the baseline. Compare like intervals and segments, record the historical reference, and distinguish an anomaly from a proven missing-record count. An anomaly threshold should not silently waive a zero-tolerance money or access invariant.

Measure the checker too: an independent schedule knows which check results should exist, and a coverage rule detects missing or stale results. Keep SLO history after repair. Backfilling yesterday's interval restores data completeness today but cannot make yesterday's missed deadline on time.

## Failure exercise and interpretation

Create one missing scheduled interval, one duplicated ID, and one absent check result. The system should identify three different problems. Repair the duplicate, replay the interval, restart the checker, and verify both data and observation coverage. Keep the failure ledger after recovery rather than replacing historical failures with a green current status.

## Example results

Calculated worksheet for ten scheduled intervals.

```text
scheduled intervals: 10
on-time and valid: 8
late: 1
never ran: 1
good / eligible: 8 / 10 = 80%
incorrect denominator using completed runs only: 8 / 9
missing checker result: UNKNOWN, not PASS
```

Repair can restore current data usability without erasing missed-deadline history. Distinguish duplicate-key failure, missing interval, and absent check evidence. The never-started interval still counts.

## Explain it in your own words

Why can freshness improve while completeness worsens? Explain the denominator and authority behind every percentage on your dashboard. Identify which quality rules need domain approval and which are mechanical type checks.

Continue with [OpenTelemetry](09-opentelemetry.md).

<!-- source: https://docs.getdbt.com/docs/build/data-tests | checked: 2026-09-10 | executable data assertions; contracts and SLO arithmetic are teaching synthesis -->
<!-- source: https://sre.google/workbook/implementing-slos/ | checked: 2026-09-10 | outcome-oriented SLIs and SLOs -->
<!-- source: https://docs.greatexpectations.io/docs/core/introduction/ | checked: 2026-09-10 | GX expectations and validation workflow -->
<!-- source: https://docs.soda.io/soda-cl/soda-cl-overview.html | checked: 2026-09-10 | Soda check-language scope -->
