# OpenTelemetry: connect executions without losing control of telemetry

A data job fails. Its clues are scattered across the scheduler log, worker metrics, and a database error message. How can you tell which records belong to the same execution?

OpenTelemetry helps collect and send these signals with consistent context. You still choose where to store and query them, and which identifiers connect the records.

## Terms introduced in this chapter

| Term | Meaning | Why it matters / when to use it |
|---|---|---|
| Span / trace | A span records one operation. A trace connects related spans so a request can be followed across operations. | Explain one request's work across operation boundaries and identify where latency accumulated. **Concrete situation (illustrative):** A slow checkout crosses an API, database, and payment service. → Link timed spans into one distributed trace. → Identify the critical path while checking for missing instrumentation. |
| Resource | Attributes identifying the source of telemetry, such as the service name and deployment environment. | Attribute telemetry to the producing service or instance when comparing deployments and failures. **Concrete situation (illustrative):** Metrics from staging and production appear under the same service label. → Attach stable resource attributes that identify service and environment. → Verify queries separate the intended deployments consistently. |
| Context propagation | Passing execution context to the next service or message handler so related work can stay connected. | Keep causal execution links intact across HTTP calls or message processing boundaries. **Concrete situation (illustrative):** A trace stops at an outgoing HTTP call. → Inject and extract supported trace context across the boundary. → Confirm the downstream span belongs to the same intended trace. |
| Baggage | Key/value context that travels with requests across service boundaries. | Carry small approved context values across calls when downstream components need them. **Concrete situation (illustrative):** A request needs a non-sensitive routing hint across several services. → Propagate a bounded, allowlisted baggage field where justified. → Check it neither exposes secrets nor grows without limit. |
| OTLP | The OpenTelemetry protocol used to send telemetry between compatible components. | Send telemetry through a common protocol instead of writing a separate transport for every backend. **Concrete situation (illustrative):** Services emit telemetry through different client libraries. → Use compatible OTLP exporters and collector receivers. → Send a controlled signal and verify transport, attributes, and backend arrival. |
| Sampling | Choosing which trace information to keep according to a defined policy. | Control trace volume and cost while documenting which evidence the selection policy can lose. **Concrete situation (illustrative):** Keeping every trace exceeds the telemetry budget. → Choose a sampling policy tied to investigation needs. → Measure retained error and latency examples and document what may be missed. |

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

## Resource, span attributes, context, and baggage

A resource identifies the producer, for example `service.name=orders-transform` and `deployment.environment.name=study`. Span attributes describe a particular operation, such as a controlled dataset name and source version. An instrumentation scope identifies the library emitting telemetry. If every batch puts its run ID into the resource, the service identity becomes unstable and downstream grouping suffers. Keep stable producer identity separate from per-operation identity.

A trace ID identifies related operations; each span has its own span ID and optionally a parent. Context is the in-process carrier of the current execution relationship. Propagators serialize selected context into a transport carrier such as HTTP or Kafka headers, and extract it at the receiving boundary. The W3C `traceparent` value includes a version, trace ID, parent span ID, and flags; it is a relationship carrier, not a trusted user identity.

Baggage propagates application key/value context separately from span attributes. Setting baggage does not automatically record it as a span attribute, nor does recording an attribute automatically propagate it. An application must deliberately copy allowed values where appropriate. Treat inbound propagated values as untrusted, limit their size, and prevent secrets or arbitrary customer fields from reaching downstream services through them.

## A real SDK lab: inject, extract, and detect broken propagation

This local lab uses `opentelemetry-sdk==1.44.0` and its matching API dependency. If you choose to install it, use a scratch virtual environment: `python3 -m venv .venv` followed by `.venv/bin/python -m pip install opentelemetry-sdk==1.44.0`. Save the complete code as `trace_lab.py` and run `.venv/bin/python trace_lab.py`. The in-memory exporter sends nothing over the network and needs no Collector or account.

The explicit empty context for the broken consumer prevents a still-active local producer span from accidentally masking the missing transport propagation. In this example, the producer has already ended before consumers start, which resembles a queued message boundary.

<!-- executable-optional: otel-propagation -->
```python
from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.propagate import inject, extract
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

exporter = InMemorySpanExporter()
provider = TracerProvider(resource=Resource.create({
    'service.name': 'study-pipeline',
    'deployment.environment.name': 'study',
}))
provider.add_span_processor(SimpleSpanProcessor(exporter))
tracer = provider.get_tracer('study.propagation', '1.0')
headers = {}
with tracer.start_as_current_span('produce'):
    inject(headers)
with tracer.start_as_current_span('consume', context=extract(headers)):
    trace.get_current_span().set_attribute('study.dataset', 'orders.accepted')
with tracer.start_as_current_span('consume_broken', context=Context()):
    pass

spans = {span.name: span for span in exporter.get_finished_spans()}
parent, child, broken = (spans[name] for name in ('produce','consume','consume_broken'))
assert child.context.trace_id == parent.context.trace_id
assert child.parent.span_id == parent.context.span_id
assert broken.parent is None
assert broken.context.trace_id != parent.context.trace_id
assert all(s.resource.attributes['service.name']=='study-pipeline' for s in spans.values())
print('exported_spans:', len(spans))
print('traceparent_present:', 'traceparent' in headers)
print('parent_child_same_trace:', child.context.trace_id == parent.context.trace_id)
print('broken_consumer_new_trace:', broken.context.trace_id != parent.context.trace_id)
provider.shutdown()
```

Expected output; random trace IDs are intentionally not printed:

```text
exported_spans: 3
traceparent_present: True
parent_child_same_trace: True
broken_consumer_new_trace: True
```

Replace `extract(headers)` with `Context()` and the parent/child assertion must fail. This tests real SDK propagation and export. It does not test Kafka header serialization, network OTLP delivery, tail sampling, or backend retention; add those boundaries one at a time to the same fixture.

## Parent-child relationships and span links

For one request causing one downstream request, parent-child spans describe the causal nesting naturally. A batch consuming 500 messages with independent trace contexts has 500 potential inputs, so inventing one parent hides most of the relationship. A consumer span can link to input contexts while keeping a bounded execution trace. A dataset-level lineage edge answers “what derived from what,” whereas a span link answers an execution relationship; retain a shared run/publication reference to connect them.

Record start/end around the operation you mean to measure. A span around queue submission measures enqueue duration, not worker completion. A retry can be represented as a child attempt under a bounded logical operation, with outcome and attempt metadata. Avoid double instrumentation by verifying the emitted span count when a framework and manual wrapper both instrument the same call.

## Metrics, logs, and their SDK semantics

An SDK counter records non-negative additions, such as accepted events. An up/down counter represents additive changes that can increase or decrease, such as active work. A histogram records a distribution, such as publication delay in seconds. Observable instruments report values through callbacks. Choose the instrument from the quantity's mathematical behavior, then verify the exporter/backend mapping rather than treating every number as a gauge.

Aggregation temporality describes whether an export represents change over an interval or accumulation since a start point. A backend expecting cumulative counters needs compatible conversion when the source emits deltas. Reset/start-time handling matters during restarts. Attribute sets define aggregation dimensions: adding `run_id` to a metric can create one series per run even though it was harmless on a sampled span.

Logs can carry trace/span context so a selected event links back to an execution. A log outside an active span may have no valid trace context. Keep its operation/run reference meaningful independently. Log bodies, span events, and attributes all contribute to volume and can expose payloads; capture fields deliberately rather than copying entire input records.

## Head sampling, tail sampling, and routing

Head sampling decides when a trace begins, often using a deterministic trace-ID ratio and a parent-based policy. It cannot know that an operation will fail thirty seconds later. Tail sampling can retain completed traces with errors or high latency after buffering evidence, but it needs spans from the same trace to reach the relevant decision state. Load-balancing arbitrary spans across independent tail samplers can fragment traces and defeat the intended policy.

If an upstream head sampler discards 99% of traces, a downstream tail sampler cannot recover those missing spans. A policy that retains all observed errors plus a sample of successes biases the retained trace population. Use unsampled outcome metrics or the publication ledger for SLO counts; evaluate sampling with generated/retained traces grouped by known fixture outcome.

For a hypothetical 1,000 traces/s, ten spans/trace, and a 30-second tail-decision window, as many as 300,000 spans arrive during the decision period before accounting for late spans and overhead. This is an arrival-volume estimate, not a memory measurement. Measure actual retained state, sizing, and timeout behavior under the chosen processor/version.

## Collector ordering, queues, and loss accounting

In the earlier traces pipeline, the receiver accepts OTLP, the memory limiter applies pressure before later processing allocates more work, the batch processor groups exports, and the exporter sends them. The memory limiter is not extra storage; refused telemetry depends on upstream retry behavior for recovery. Processors are configured per signal pipeline, and a traces processor is not automatically applied to metrics or logs.

An exporter queue buys finite time. At 2 MB/s and 600 MB of usable capacity, an empty byte-sized queue gives roughly five minutes of outage headroom before overhead and retry limits. Some exporters configure capacity in requests or batches instead of bytes, so convert using measured batch sizes. If recovery throughput is 3 MB/s while arrivals remain 2 MB/s, a 600 MB backlog takes roughly ten minutes to drain.

Persistent queue storage can preserve queued exports across supported restarts, but disk exhaustion, unrecoverable destinations, expiration, and permanent errors still matter. Acknowledgement at the Collector receiver is not necessarily acknowledgement of backend persistence. Reconcile generated IDs against received/retained IDs in a synthetic failure test; monitor telemetry health through an independent route when testing complete pipeline loss.

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
<!-- source: https://opentelemetry.io/docs/languages/python/instrumentation/ | checked: 2026-09-10 | SDK spans/resources/export; lab pinned to 1.44.0 -->
<!-- source: https://opentelemetry.io/docs/languages/python/propagation/ | checked: 2026-09-10 | inject/extract transport boundary -->
<!-- source: https://opentelemetry.io/docs/concepts/sampling/ | checked: 2026-09-10 | head and tail sampling tradeoffs -->
<!-- source: https://opentelemetry.io/docs/specs/otel/metrics/data-model/ | checked: 2026-09-11 | temporality and aggregation identities -->
