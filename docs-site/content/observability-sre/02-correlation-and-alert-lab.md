# Signal correlation and SLO alert lab

> lab level: **Local**. If you already have a Prometheus and OpenTelemetry demo environment, use that environment. If not, first verify the meaning of the query with the data below.

## Lab prerequisites

- **Prerequisite understanding**: You must first be able to explain the differences between HTTP status, request processing time, and metrics·log·trace.
- **Execution environment**: If Prometheus and OpenTelemetry demo are present, execute actual query. If not, this chapter is a worksheet that reads formulas and event records and is not completed as an execution lab.
- **Required data**: Request counter, latency histogram, log with request ID, trace with trace ID are required.
- **Time fixation**: Record the failure start, mitigation, and recovery time and query window in the same timezone.
- **Scope of change**: The first run does not connect alerts to the production pager, but only checks local rule evaluation.
- **Finished state**: Remove temporary rules and test traffic and check whether the original metric trend has returned.

Before entering the PromQL below as is, check your metric name and label. If the names are different, no data will be output even if the grammar is correct, and the result does not mean that the service is normal.

## Understand the model first

What we are trying to create in this lab is not a dashboard, but an explainable incident chain. Starting from one failed user request, we find the request ID and trace ID, check whether that request is included in the overall failure rate, and then narrow down which span and dependency the time increased.

Counters such as `http_server_requests_total` are accumulated after the process starts. Therefore, rather than dividing the current values, use `rate` of a certain window. The histogram bucket is the cumulative number of requests below each latency boundary, and `histogram_quantile` estimates the percentile using multiple buckets. Its role is different from trace, which shows the exact time of each individual request.

| observation | What can be known | Things to watch out for |
|---|---|---|
| 5 minute error ratio | Failure rate in recent traffic | If there is little traffic, even small numbers can cause significant shaking. |
| p95 latency | Estimated threshold at or below which 95% of observations fall | Bucket resolution limits accuracy; it is not the slowest request |
| trace span | Time per hop for selected requests | Sampling does not represent all requests |
| error log | Detailed context recorded by the component | Possible missing records and clock differences |
| burn-rate alert | Budget exhaustion speed exceeds response standards | Threshold must be calculated in SLO window |

## 1. Set request contract

Place the following common fields in the sample API.

```text
request_id=8f3... trace_id=4bf... route=/checkout status=503 duration_ms=842
```

The counter uses a bounded label like `http_server_requests_total{route,status_class}`. Do not include `request_id` or `user_id` as a metric label. Individual request identities are stored in logs and traces.

## 2. Observation of availability and latency

This teaching contract classifies non-5xx responses as good and measures one service. A real checkout SLI must classify rejected, canceled, timed-out, and unrecorded requests explicitly; HTTP status alone may not represent a successful order. Initialize bounded status-class counters to zero so a quiet error series remains observable.

```promql
sum(rate(http_server_requests_total{service="sample-api",status_class!="5xx"}[5m]))
/
sum(rate(http_server_requests_total{service="sample-api"}[5m]))
```

This is an example of calculating 95 percentile in a histogram.

```promql
histogram_quantile(
  0.95,
  sum by (le, route) (rate(http_server_request_duration_seconds_bucket{service="sample-api"}[5m]))
)
```

It records situations where the denominator becomes 0 when traffic is 0, situations where retry increases the number of requests, and at which point among ingress/client it is measured.

## 3. Failure time base connection

Select one error request and fill out the following table.

| hour | evidence | hypothesis | action | verdict |
|---|---|---|---|---|
| T0 | availability SLI decline | upstream error | trace ID lookup | Investigating |
| T1 | Increased DB span latency | connection saturation | Check pool metrics | active=max |
| T2 | Burn reduction after adjusting pool limit | Relieve bottlenecks | Prepare for rollback | observing |

```mermaid
sequenceDiagram
    participant U as User
    participant A as API
    participant D as Database
    participant O as On-call
    U->>A: request + trace context
    A->>D: query span
    D--xA: timeout
    A-->>U: 503 + request ID
    A-->>O: metric alert
    O->>A: Check trace ID in log
    O->>D: Check span·pool status
```

## 4. Alert verification

For the teaching SLO of 99.9% over 30 days, allowed error fraction is `0.001`. Burn rate `14.4` sustained for one hour consumes `14.4 × 1 / 720 = 2%` of that window's budget. Requiring the short window too helps detect that burning is still active. Save these complete rules as `sample-api.rules.yml`:

```yaml
groups:
  - name: sample-api-slo
    rules:
      - record: sample_api:error_budget_burn_rate5m
        expr: sum(rate(http_server_requests_total{service="sample-api",status_class="5xx"}[5m])) / sum(rate(http_server_requests_total{service="sample-api"}[5m])) / 0.001
      - record: sample_api:error_budget_burn_rate1h
        expr: sum(rate(http_server_requests_total{service="sample-api",status_class="5xx"}[1h])) / sum(rate(http_server_requests_total{service="sample-api"}[1h])) / 0.001
      - alert: SampleApiFastBurn
        expr: (sample_api:error_budget_burn_rate1h > 14.4) and (sample_api:error_budget_burn_rate5m > 14.4)
        for: 2m
        labels:
          severity: page
        annotations:
          summary: Sample API error budget is burning quickly
```

Run `promtool check rules sample-api.rules.yml` when Prometheus tooling is available. This checks rule validity; it does not supply scrape data. Test sustained 2% errors (burn 20, page after both windows and `for` qualify), 0.1% errors (burn 1, no fast-burn page), a short burst followed by recovery, counter resets, no traffic, and missing scrapes. Zero traffic produces an undefined ratio; missing series can produce no result. Neither proves health. Give scrape availability and expected-traffic absence their own rules and owners. Add slower windows for prolonged lower-rate loss; this minimum fast-burn rule is not the whole paging policy.

## Judgment of completion and summary

- When an alert occurs, a dashboard/runbook linked to the user impact is opened.
- You can go back and forth between log and trace by request or trace ID.
- After recovery, check when the short window and long window normalize.
- Remove only the temporary rule and demo workload. Retain incident evidence according to the lab's retention policy.

## Example results

Calculated examples for the stated synthetic request contract, not measurements from a deployed API.

| Input during both windows | Availability | Burn rate | Fast-burn decision |
|---|---:|---:|---|
| 980 good + 20 failed per 1,000 | 0.98 | 20 | Fires once the condition persists for 2 minutes |
| 999 good + 1 failed per 1,000 | 0.999 | 1 | Does not fire |
| Zero increments on both counters | Undefined (NaN) | Undefined | No health verdict |
| All series absent | Empty result | Empty result | Investigate observation coverage |

```text
# promtool check rules sample-api.rules.yml (expected)
SUCCESS: 3 rules found
# Synthetic firing alert labels
alertname=SampleApiFastBurn severity=page
```

A burst that has ended can leave the 1-hour rate elevated while the 5-minute condition clears. The conjunction should then stop firing. Validate that behavior with time-series fixtures; an alert screenshot alone does not establish recovery.

## How to interpret the results

If the value of the availability expression is `0.98`, it means that about 98% of the areas within the selected 5-minute window and label range were classified as good. The meaning varies depending on which request is excluded from valid or good. Inadvertently subtracting health checks or client cancels from the denominator can hide actual user failures.

If the time when p95 rises overlaps with the increase in DB span, the dependency bottleneck hypothesis becomes stronger, but the causal relationship has not yet been confirmed. View the parent-child time, connection pool, DB wait, and change time of the same trace together. After mitigation, check whether burn rate, tail latency, and backlog, as well as single successful requests, return to normal ranges.

If an alert is fired but there is no action on-call, making the rule more sensitive is not the solution. Conditions associated with user impact, owner, first diagnostic query, and safe mitigation actions must be bundled into a runbook.

## Explain it in your own words

1. Why is it dangerous to put request ID in metric label?
2. Why do the increase in 503 and DB span latency not immediately prove causality?
3. What operational problems are left without testing alert recovery?

<!-- source: https://prometheus.io/docs/prometheus/latest/querying/basics/ | checked: 2026-09-03 -->
<!-- source: https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/ | checked: 2026-09-03 -->
<!-- source: https://opentelemetry.io/docs/concepts/signals/ | checked: 2026-09-03 -->
<!-- source: https://sre.google/workbook/alerting-on-slos/ | checked: 2026-09-03 -->
