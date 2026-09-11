# Prometheus, Grafana, Loki, and Tempo: operate the evidence pipeline

A dashboard should answer a question and lead to a decision. Begin with “Can a consumer use this dataset now?” and then investigate its processing, storage, and telemetry dependencies.

## Terms introduced in this chapter

| Term | Meaning | Why it matters / when to use it |
|---|---|---|
| Counter | A cumulative count that can reset when its producer restarts | Count cumulative events and derive rates over a chosen window with reset-aware queries. |
| Gauge | A current value that can increase or decrease | Observe current levels such as queue depth or active work that can rise and fall. |
| Histogram | A representation of an observed value distribution | Inspect distributions and threshold fractions that averages alone would conceal. |
| Summary | Observations with client-calculated quantiles where configured | Obtain configured per-producer quantiles when their aggregation limitations fit the question. |
| Label cardinality | The number of distinct label combinations creating time series | Estimate time-series growth before adding labels that would make monitoring costly or unstable. |
| Burn rate | Observed failure fraction divided by the SLO's allowed failure fraction | Relate current failure intensity to how quickly an SLO's error allowance is being consumed. |

## Understand the model first

1. Emit metrics with stable meanings, units, and bounded labels.
2. Store and query them in Prometheus or a compatible metrics backend.
3. Store logs in Loki and traces in Tempo, or evaluate Jaeger as a trace alternative.
4. Use Grafana to explore the backends and connect an aggregate symptom to a run.
5. Route an actionable alert with its owner, impact, and diagnostic links.

Grafana is the exploration layer in this design. Prometheus, Loki, and Tempo have different storage and query models. A common dashboard does not mean all signals have identical retention, availability, or access policies.

## PromQL with explicit semantics

These queries assume **custom application metrics defined by this course**, not built-in Kafka, Spark, or OTel metric names. The application emits one publication outcome per eligible interval, with a bounded `dataset` and `outcome` label. A separate schedule ledger detects intervals that never ran.

```promql
# Publication attempts per second; apply rate before aggregating resets.
sum by (dataset) (rate(data_publications_total[5m]))

# Known failed attempts / all observed attempts over an hour.
sum by (dataset) (increase(data_publications_total{outcome="failed"}[1h]))
/
sum by (dataset) (increase(data_publications_total[1h]))

# p95 delay across classic histogram buckets; retain the le label.
histogram_quantile(
  0.95,
  sum by (dataset, le) (rate(data_publication_delay_seconds_bucket[5m]))
)
```

The failure fraction does not include a missed scheduled run unless another component emits it. An absent series is not automatically zero, and a zero denominator should mean insufficient observations under the declared policy. Initialize known bounded outcome series where appropriate and implement separate missing-data checks. Never hide all absence by indiscriminately appending `or vector(0)`.

For classic histograms, bucket boundaries determine quantile resolution. A threshold count can answer “what fraction finished within 600 seconds?” more directly than a p95 estimate when 600 is an actual bucket boundary. Client-calculated summary quantiles generally cannot be averaged into a fleet quantile. Native histograms have a different representation; verify SDK, ingestion, storage, and query support before changing the metric contract.

## Bound cardinality before an incident

An illustrative metric with 50 datasets, four outcomes, three environments, and 20 instances can have 12,000 label combinations before accounting for histogram components. Adding a per-event ID multiplies that space by the event population. Use logs, traces, or a receipt store for those identities.

Review both allowed values and churn: new pod IDs or run IDs can create a growing historical series set even when concurrent counts look small. Set a telemetry volume budget, estimate retention cost, and load-test the backend under representative labels.

## Build four diagnostic views

| View | Questions |
|---|---|
| Consumer outcome | Which datasets missed validity or publication deadlines? Is observation coverage complete? |
| Pipeline | Where do input rate, lag, processing duration, and output commits diverge? |
| Execution | Which Spark stage, Kafka partition, host, or query explains the delay? |
| Telemetry health | Are scrapes, collectors, queues, ingestion, or queries failing? |

A useful log contains timestamp, severity, operation, run ID, reason code, and relevant version references. Keep sensitive payloads out of default log streams. Store bounded service/environment labels in Loki; putting every event ID into an index label makes the index a poor fit for its role. Connect logs to traces through extracted trace IDs and verify the links in the chosen dashboard configuration.

## Alert on outcomes and corroborate causes

For an illustrative 99.9% SLO, a 1% failure fraction burns budget at ten times the allowed rate. Use multiple windows to distinguish a sustained serious incident from a transient sample, and include volume and missing-observation checks. Exact thresholds are design choices that require traffic and response-time assumptions.

Prometheus Alertmanager adds routing, grouping, inhibition, and silencing. A silence is an operational action with an expiry and owner. It does not change historical SLO performance. Group notifications by actionable scope; one upstream incident should not automatically page every downstream owner independently.

## Counter, gauge, histogram, and summary in one pipeline

Use a counter for completed publication attempts because each observation adds an event. Use a gauge for current backlog because it rises and falls. Use a histogram for publication delay because threshold compliance and tail behavior matter. A summary with configured quantiles computes rank estimates at the observing client; those ranks cannot normally be combined into a correct fleet percentile.

`rate(counter[5m])` estimates per-second increase while accounting for resets within the range. `increase(counter[1h])` estimates the increase over the range and can be fractional because Prometheus extrapolates to range boundaries. It is not an exact financial ledger. Apply `rate` to individual counters before summing so one process restart is not hidden inside an aggregate. Applying `rate` to a backlog gauge misinterprets decreases as counter behavior.

Suppose process A's counter restarts while B keeps increasing. `sum(rate(...))` preserves the separate reset information; subtracting two fleet-wide summed samples can confuse A's reset with negative work. Keep exact scheduled-publication counts in the ledger and use the metric for operational trends with declared coverage.

## Classic histogram buckets: work the percentile by hand

Classic bucket counts are cumulative: `le="5"` includes every observation in `le="1"`. Retain `le` when aggregating buckets across instances with compatible boundaries. This Python fixture computes cumulative counts and linear interpolation for a deliberately uneven latency distribution.

<!-- executable: histogram-math -->
```python
delays = [1, 2, 3, 4, 5, 10, 100, 200, 600, 900]
bounds = [5, 100, 600, 1000]
counts = [sum(value <= bound for value in delays) for bound in bounds]
rank = 0.95 * len(delays)
lower, upper = 600, 1000
before, through = counts[2], counts[3]
estimate = lower + (rank-before)/(through-before)*(upper-lower)
assert counts == [5,7,9,10]
assert estimate == 800
print('cumulative_buckets:', counts)
print('within_600_seconds: 9/10')
print('interpolated_p95_seconds:', int(estimate))
```

Expected output:

```text
cumulative_buckets: [5, 7, 9, 10]
within_600_seconds: 9/10
interpolated_p95_seconds: 800
```

The actual final observation is 900, while the bucket-based p95 estimate is 800. The histogram knows a rank lies inside `(600,1000]`, not the exact observation positions. Add a bucket at a contractual threshold when measuring its fraction directly. A classic histogram with ten finite boundaries has eleven buckets including `+Inf`, plus count and sum: thirteen series per non-bucket label combination before optional implementation-specific additions.

For the course's declared 600-second threshold, use:

```promql
sum by (dataset) (rate(data_publication_delay_seconds_bucket{le="600"}[5m]))
/
sum by (dataset) (rate(data_publication_delay_seconds_count[5m]))
```

This includes recorded observations, not intervals that never emitted a delay. Pair it with the independent schedule check. Native histograms change the representation; validate the producer, backend, query, and recording-rule chain together before migrating.

## Cardinality: multiplication and churn

Fifty datasets × four outcomes × three environments × twenty instances is 12,000 combinations. Thirteen classic-histogram constituent series can raise that illustrative maximum to 156,000. Multiplying by one million event IDs makes the metric unsuitable for its aggregate purpose. Real combinations may be sparse, but churn keeps creating historical series even after old workers disappear.

Keep bounded dataset labels in metrics and run/event identities in logs or traces. An exemplar can connect a representative metric observation to a trace where supported; it is a navigation sample, not every request in the bucket. Normalize unique URL paths to route templates where supported so identifiers do not become metric labels accidentally.

## Loki: select streams, then parse log lines

Loki's labels identify streams. A bounded service/environment selector reduces the search space; LogQL can then filter and parse log bodies. Keep `run_id` in the structured body or supported structured metadata rather than creating one indexed stream per run. For JSON lines carrying `reason` and `run_id`, use:

```logql
{service_name="study-pipeline", environment="study"}
  |= "QUALITY_FAILED"
  | json
  | reason="QUALITY_FAILED"
  | __error__=""
```

These stream labels are a course ingestion contract, not guaranteed OTel-to-Loki defaults. The line filter reduces candidate text, parsing exposes fields, and the reason filter selects the event. Inspect parse errors separately; excluding them here must not erase a malformed-log incident. Restrict the time window before widening service scope.

## Tempo, Jaeger, and Grafana correlation

Tempo stores/query-serves traces and provides TraceQL for supported span/trace searches. Jaeger is another tracing backend with its own deployment and query behavior. Recover the execution path after metrics/logs identify a bounded incident. Find a trace by ID or known service, duration, and operation attributes; absence can mean sampling, propagation loss, ingestion failure, or retention expiration.

Grafana joins investigation steps through configured data sources and links. A panel needs a time range, units, aggregation scope, and a route to the relevant run or diagnostic query. A five-minute rate panel and a daily cumulative table can both be correct while appearing inconsistent. Align windows and populations before explaining the difference as loss.

## Recording rules and Alertmanager behavior

A recording rule precomputes a stable PromQL expression, trading storage/evaluation work for predictable query cost and consistent definitions. Version it when its denominator changes. An alerting rule evaluates a condition; a `for` duration requires it to remain active before firing. Scrape gaps, evaluation cadence, and missing series affect that lifecycle, so test absent data and resets alongside positive examples.

Alertmanager groups related notifications, routes them to receivers, applies inhibition, and manages time-bounded silences. Inhibition can reduce duplicate paging when an upstream failure explains downstream symptoms, but it does not mark datasets healthy. Group by an actionable owner/dataset scope; grouping every alert only by environment can hide which consumer needs repair. The [SLO lab](../../../docs-site/content/observability-sre/02-correlation-and-alert-lab.md) contains complete recording/alert rules and promtool fixtures.

## Failure exercise and interpretation

In an isolated lab, stop publication while keeping the HTTP endpoint alive. The dataset view should fail while service availability can remain healthy. Restore publication and verify the missing intervals are repaired. Then stop telemetry export while publication continues. The observation-coverage view should report unknown evidence, not a sudden zero error rate.

Compare dashboard timestamps against raw backend queries and the independent ledger. A panel that says “no data” may reflect a label change, expired retention, failed ingestion, or an empty population. Distinguish them before changing an alert.

## Example results

Illustrative query outcomes, not backend measurements.

```text
HTTP healthy + publication stopped: DATA FRESHNESS FAILURE
publication continues + telemetry absent: COVERAGE UNKNOWN
2 known failures / 100 observed attempts: 0.02
empty PromQL vector: NO EVIDENCE, not zero failures
```

An attempt-based ratio does not count jobs that never started. Reconcile scheduled intervals independently and label the histogram p95 estimate in seconds. Recovery must restore both publication and observation coverage.

## Explain it in your own words

Why can average latency improve when slow requests are dropped from observation? Why is a per-dataset p95 not safely averaged into a platform p95? Describe how an operator can reach the affected dataset version from a bounded aggregate metric.

Continue with [lineage and governance](11-lineage-governance.md).

<!-- source: https://prometheus.io/docs/practices/histograms/ | checked: 2026-09-10 | histogram and summary interpretation -->
<!-- source: https://prometheus.io/docs/prometheus/latest/querying/functions/ | checked: 2026-09-10 | rate, increase, histogram_quantile -->
<!-- source: https://prometheus.io/docs/alerting/latest/alertmanager/ | checked: 2026-09-10 | grouping, routing, inhibition and silences -->
<!-- source: https://grafana.com/docs/loki/latest/get-started/labels/ | checked: 2026-09-10 | label cardinality -->
<!-- source: https://grafana.com/docs/loki/latest/query/log_queries/ | checked: 2026-09-10 | stream selection and parsing -->
<!-- source: https://grafana.com/docs/tempo/latest/traceql/ | checked: 2026-09-10 | trace search -->
