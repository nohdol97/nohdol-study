# Prometheus, Grafana, Loki, and Tempo: operate the evidence pipeline

A dashboard should answer a question and lead to a decision. Begin with “Can a consumer use this dataset now?” and then investigate its processing, storage, and telemetry dependencies.

## Terms introduced in this chapter

| Term | Meaning |
|---|---|
| Counter | A cumulative count that can reset when its producer restarts |
| Gauge | A current value that can increase or decrease |
| Histogram | A representation of an observed value distribution |
| Summary | Observations with client-calculated quantiles where configured |
| Label cardinality | The number of distinct label combinations creating time series |
| Burn rate | Observed failure fraction divided by the SLO's allowed failure fraction |

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
