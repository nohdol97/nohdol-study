# OpenTelemetry: connect executions without losing control of telemetry

A failed pipeline can leave clues in a scheduler log, an executor metric, and a database error. OpenTelemetry helps instrument and transport signals with consistent context so those clues can be related. You still need storage backends, a query interface, and a deliberate identity model.

## Terms introduced in this chapter

| Term | Meaning |
|---|---|
| Span / trace | A recorded operation / related operations connected through trace context |
| Resource | Attributes identifying the entity producing telemetry, such as a service |
| Context propagation | Passing execution context across calls and message boundaries |
| Baggage | Propagated key/value context that can travel with requests |
| OTLP | OpenTelemetry's telemetry transport protocol |
| Sampling | Selecting which trace information to retain under a defined policy |

## Understand the model first

1. Instrument application operations with an SDK or supported automatic instrumentation.
2. Set consistent service and environment identity.
3. Propagate context across supported boundaries, including message headers where appropriate.
4. Export signals directly or through a Collector pipeline.
5. Query a backend to connect the operation to the dataset version and publication outcome.

Metrics summarize populations, logs record events, and traces describe operations and relationships. Resources describe their producer; they are not a separate storage backend. Profiles help investigate code-level resource consumption where the chosen components support them. Check signal support and semantic-convention status per SDK, Collector distribution, and backend rather than assuming equal maturity across every language and signal.

## Collector responsibilities

| Component | Responsibility | Common misunderstanding |
|---|---|---|
| Receiver | Accept or collect telemetry | Receiving a span does not mean a backend persisted it |
| Processor | Transform, filter, batch, sample, or limit signals | Component order and supported signal types matter |
| Exporter | Send telemetry to a destination | Retry and queue limits can still cause loss |
| Extension | Support the process, such as health or storage | Declaring an extension does not automatically enable it |
| Service pipelines | Connect the enabled components | A configured but unused component does no work |

This is a minimal local traces pipeline for a compatible Collector distribution containing `otlp`, `memory_limiter`, `batch`, and `debug`. It prints synthetic traces; it is not a durable backend or production configuration. Check it with your distribution's configuration validation command before starting that version.

```yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: 127.0.0.1:4318
processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 128
    spike_limit_mib: 32
  batch: {}
exporters:
  debug:
    verbosity: basic
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [debug]
```

Loopback binding assumes the application and Collector share a host network namespace. A separately networked container cannot reach another container's loopback. For a container lab, design an explicit internal network and expose only the required host ports. For a remote deployment, configure identity, transport security, and access controls deliberately.

## Choose identifiers for the question

Use a trace ID to investigate an execution. Add a stable pipeline name, run ID, source range, and dataset version to controlled span/log attributes or a referenced receipt. A dataset may take hours and many jobs to build; forcing its entire lifetime into one never-ending trace creates awkward state and sampling behavior.

Model bounded operations: consume a batch, transform a partition group, validate a candidate, publish a snapshot. Use links where multiple input contexts contribute to one operation instead of inventing a single parent. Keep run IDs and event IDs out of metric labels because their unbounded values create new time series continually.

Do not place secrets, prompts, customer records, or access tokens in baggage. Propagation can cross trust boundaries, and baggage is not an authorization mechanism. Redact as close to collection as practical and verify what actually arrives in every destination.

## Sampling and resilience

Head sampling decides early and has limited knowledge of the eventual outcome. Tail sampling can use later trace information but requires buffering and coherent routing of spans for the same trace. When a trace is not retained, it does not establish that the operation never happened. Build SLO denominators from suitable complete counters or an outcome ledger rather than sampled trace counts.

Collector queues and retries absorb limited downstream outages. In-memory queues can disappear on restart. A supported persistent queue can survive some restarts but still depends on disk capacity, retention/retry limits, and destination recovery. Monitor accepted, refused, exported, failed, and dropped telemetry plus queue/disk usage using the actual metrics exposed by the selected version.

## Guided failure exercise

Prerequisites: one synthetic instrumented operation, the local Collector, and then a separate disposable destination for the resilience phase. First verify that one operation appears with the expected resource and trace context. Break propagation at one boundary and observe the disconnected trace. Repair it and repeat the operation.

Next stop the destination, watch queue growth and failures, and restart it before capacity is exhausted. Compare generated and retained event counts. Then exceed the bounded queue in a separate run and record the loss. A green Collector health endpoint is not proof that it exported every span.

## Example results

Illustrative observation receipt; actual debug-exporter formatting depends on the Collector distribution.

```text
service.name: study-pipeline
propagation intact: parent and child share trace ID
propagation broken: disconnected child trace
destination stopped: bounded export queue grows
queue exhausted: record dropped or unretained spans
example count reconciliation: 100 generated - 93 retained = gap of 7
```

A healthy endpoint or empty queue does not prove lossless export. The debug pipeline demonstrates telemetry receipt; destination-outage behavior needs the separately configured exporter and queue. Record observed counts before claiming recovery.

## Explain it in your own words

What evidence links a span to the exact input snapshot? Which metric remains available when traces are sampled? Describe how you would detect a telemetry pipeline failure without relying exclusively on that same pipeline.

Continue with [metrics, logs, and traces in operation](10-metrics-logs-traces.md).

<!-- source: https://opentelemetry.io/docs/collector/configuration/ | checked: 2026-09-10 | components and service wiring -->
<!-- source: https://opentelemetry.io/docs/collector/resiliency/ | checked: 2026-09-10 | queue persistence and loss boundaries -->
<!-- source: https://opentelemetry.io/docs/concepts/context-propagation/ | checked: 2026-09-10 | context and baggage -->
