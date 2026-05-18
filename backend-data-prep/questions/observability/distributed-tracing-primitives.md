# Distributed Tracing Primitives — Trace, Span, Context Propagation, Sampling

## Source / Origin
- Google's Dapper paper (2010) — the canonical reference for production tracing at scale.
- OpenTelemetry Trace specification: https://opentelemetry.io/docs/specs/otel/trace/
- W3C Trace Context: https://www.w3.org/TR/trace-context/
- Frequent senior interview prompt: "A single user request fans out across 8 microservices; how do you reconstruct what happened?"

## Why this question matters in interviews
This is the **first observability question** in any senior backend interview, and the floor for "can this person debug production." A mid-level engineer says "we'd add some logs." A senior says "trace id flows through baggage, spans nest by parent_span_id, sampling decision pinned at the edge, propagation via `traceparent` header." If you can draw the trace tree, name the four primitives (trace, span, context, sampler), and discuss tail-based vs head-based sampling, you signal that you've actually owned production. Companies running 50+ services literally cannot debug without this — interviewers are checking whether you'd add to the chaos or reduce it.

## Concepts involved

### Syntax / mechanism to lock in

```python
# OpenTelemetry Python — the minimal idiomatic shape
from opentelemetry import trace
from opentelemetry.trace import SpanKind

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("checkout.process", kind=SpanKind.SERVER) as span:
    span.set_attribute("user.id", user_id)
    span.set_attribute("cart.size", len(items))
    # nested span — automatically becomes a child
    with tracer.start_as_current_span("db.query.cart") as child:
        child.set_attribute("db.statement", "SELECT * FROM cart WHERE user_id=$1")
        rows = db.fetch(user_id)
    # outbound call — context is auto-injected into headers
    resp = requests.post("http://payments/charge", json=payload)
```

The wire format (W3C `traceparent`):
```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
            └┬┘ └──────────────┬────────────────┘ └──────┬──────┘ └┬┘
           ver        trace-id (16 bytes)        span-id (8 b)   flags
                                                                 (01 = sampled)
```

### Edge cases / interview traps

1. **Trace id must be 128-bit, span id 64-bit.** Anything narrower (e.g., UUID-as-string, db autoincrement) collides under load. W3C mandates this.
2. **Sampling decision belongs at the edge, not per-service.** If each service samples independently, you get partial traces — span 1 sampled, span 2 not, span 3 sampled. Decision is encoded in the `traceparent` `flags` byte and propagated unchanged.
3. **Span context propagation across async boundaries** is the #1 source of broken traces. `await`, thread pools, message queues all drop context unless you explicitly carry it.
4. **Clock skew across hosts breaks span ordering.** Durations are computed per-span on each host (monotonic clock), but cross-host ordering uses wall clock — NTP drift of even 5ms shows children "starting before parents." Annotate, don't reorder.
5. **`SpanKind` matters.** SERVER, CLIENT, PRODUCER, CONSUMER, INTERNAL. Mislabeling breaks span-link analysis (e.g., async fan-out via Kafka).
6. **High-cardinality attributes blow up the backend.** Putting `user.id` on every span is fine (it's high cardinality but bounded per trace); putting full URLs with query strings creates millions of distinct labels and kills the index.
7. **Don't trace inside tight loops.** Each span is 100-500 bytes on the wire. A loop that emits 10k spans per request is a self-DoS.
8. **Tail-based sampling vs head-based.** Head: decide at trace start (cheap, randomised). Tail: decide after trace completes (expensive, keeps all errors and slow traces). Tail-based requires a Collector that buffers spans.

## Mental Model

```
A trace is a TREE of spans linked by parent_span_id.

trace_id = 4bf9...4736
│
├─ span A: "GET /checkout" (root, kind=SERVER)          [t=0     duration=180ms]
│   │   parent_span_id = null
│   │
│   ├─ span B: "auth.validate" (kind=INTERNAL)          [t=2     duration=8ms]
│   │
│   ├─ span C: "db.query.cart" (kind=CLIENT)            [t=15    duration=22ms]
│   │   attrs: db.system=postgres, db.statement=SELECT...
│   │
│   ├─ span D: "rpc.payment.charge" (kind=CLIENT)       [t=40    duration=120ms]
│   │   │  ← propagates traceparent header
│   │   │
│   │   └─ span E: "POST /charge" (kind=SERVER, remote) [t=42    duration=115ms]
│   │       │
│   │       ├─ span F: "db.tx.insert" (kind=CLIENT)     [t=50    duration=30ms]
│   │       └─ span G: "stripe.api.charge" (kind=CLIENT)[t=85    duration=70ms]
│   │
│   └─ span H: "cache.set" (kind=CLIENT)                [t=165   duration=4ms]
│
Each span: (trace_id, span_id, parent_span_id, name, kind, start, duration, attrs, events)
```

The two fundamental operations: **start a span (capturing parent from current context)** and **propagate context (injecting `traceparent` on egress, extracting on ingress)**.

## Why interviewers care

- Tracing is the **only tool** that gives you per-request latency breakdown across services. Logs don't do it; metrics don't do it.
- Tests whether you understand **context propagation** — the hidden plumbing that makes the trace tree exist at all.
- The sampling discussion separates engineers who've read the docs from engineers who've operated at scale (you cannot keep 100% in a 500k-rps system).
- Span attributes / cardinality is a budget question — same skill as Prometheus label cardinality.

## Common beginner confusion

- **"Tracing replaces logging."** It doesn't. Spans are structured records of *unit of work*. Logs are records of *events within work*. You correlate them by trace_id.
- **"Trace id is generated per service."** No. Generated at the edge, propagated unchanged. If each service makes its own, you have N disconnected traces, not one.
- **"Sampling is fine; we'll just trace everything."** At 1k rps with 20 spans per request, you generate 20k spans/sec ≈ 1.7B/day. Backend storage cost alone kills this.
- **"OpenTelemetry is a backend."** It's an SDK + protocol (OTLP) + Collector. The backend is Jaeger, Tempo, Honeycomb, X-Ray, Datadog, etc.
- **"`request_id` and `trace_id` are the same."** Often coexist. `request_id` is your app's correlation id (added to logs). `trace_id` is the tracing system's id. Best practice: make them equal or include both.

## Brute force approach

"I'll print the request id in every log line and grep across services." Works for one request when you know exactly which service to look at, falls apart at the second hop. No timing info, no parent/child relationship, no flame graph. This is what tracing replaces.

"I'll add a UUID to a header and pass it through." Half a solution — you've got correlation but no spans, no durations, no fan-out graph. Mention this as the starting point you'd evolve from, not the endpoint.

## Optimal approach

Three pillars of the solution:

1. **One SDK at the edge generates `trace_id` + root `span_id` + sampling decision.** OpenTelemetry SDK with W3C propagator.
2. **Every service in the path extracts on ingress, injects on egress.** HTTP via `traceparent`/`tracestate` headers; gRPC via metadata; Kafka via record headers. Auto-instrumentation handles 80% of cases.
3. **A Collector aggregates + samples + exports to a backend.** Head-based sampling at the SDK is cheap; tail-based at the Collector is what you graduate to when you need "keep all errors and slow traces."

Cardinality budget: attributes are **labels**, not free text. Use semantic conventions (`http.method`, `db.system`, `messaging.system`) so the backend can build indices.

## Solution (production pattern + code/config)

### SDK setup (Node.js, OpenTelemetry)

```javascript
// tracing.js — bootstrap, must be required BEFORE app code
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');
const { ParentBasedSampler, TraceIdRatioBasedSampler } = require('@opentelemetry/sdk-trace-base');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { W3CTraceContextPropagator } = require('@opentelemetry/core');

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'checkout',
    [SemanticResourceAttributes.SERVICE_VERSION]: process.env.GIT_SHA,
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.ENV,
  }),
  traceExporter: new OTLPTraceExporter({
    url: 'http://otel-collector:4318/v1/traces',
  }),
  // Head sampling: keep 10% randomly, BUT respect parent's decision (don't mix).
  sampler: new ParentBasedSampler({
    root: new TraceIdRatioBasedSampler(0.1),
  }),
  textMapPropagator: new W3CTraceContextPropagator(),
  instrumentations: [getNodeAutoInstrumentations({
    '@opentelemetry/instrumentation-fs': { enabled: false }, // too noisy
  })],
});

sdk.start();
```

### Manual span around critical business logic

```javascript
const { trace, SpanStatusCode } = require('@opentelemetry/api');
const tracer = trace.getTracer('checkout');

async function processCheckout(userId, cart) {
  return tracer.startActiveSpan('checkout.process', async (span) => {
    span.setAttributes({
      'user.id': userId,
      'cart.size': cart.items.length,
      'cart.total_cents': cart.total,
    });
    try {
      const result = await runCheckout(userId, cart);
      span.setAttribute('order.id', result.orderId);
      return result;
    } catch (err) {
      span.recordException(err);
      span.setStatus({ code: SpanStatusCode.ERROR, message: err.message });
      throw err;
    } finally {
      span.end();
    }
  });
}
```

### Tail-based sampling at the Collector

```yaml
# otel-collector-config.yaml
processors:
  tail_sampling:
    decision_wait: 10s
    num_traces: 100000
    policies:
      - name: keep-errors
        type: status_code
        status_code: { status_codes: [ERROR] }
      - name: keep-slow
        type: latency
        latency: { threshold_ms: 1000 }
      - name: keep-10pct
        type: probabilistic
        probabilistic: { sampling_percentage: 10 }
```

## Step-by-step dry run

A user POSTs `/checkout`. Tracing in action:

```
t=0    Edge LB receives request, no traceparent.
       Frontend service generates:
         trace_id = 4bf9...4736
         span_id  = 00f0...02b7
         sampled  = 1 (10% roll, this one won)
       Emits span "GET /checkout" (kind=SERVER, parent=null).

t=2    Frontend calls auth service via HTTP.
       Auto-instrumentation injects:
         traceparent: 00-4bf9...4736-00f0...02b7-01

t=2    auth service receives, propagator extracts the trace context.
       Starts span "auth.verify" (parent_span_id = 00f0...02b7).
       Span_id = aaaa...0001.

t=8    auth returns. Span ends, duration 6ms.

t=15   Frontend queries Postgres.
       db instrumentation auto-emits span "db.query.cart" (parent=00f0...02b7).
       attrs: db.system=postgres, db.statement (sanitized)=SELECT * FROM cart WHERE user_id=$1

t=40   Frontend calls payment service.
       Span "rpc.payment.charge" (kind=CLIENT, parent=00f0...02b7).
       Injects header. payment-service receives,
       starts span "POST /charge" (kind=SERVER, parent=that CLIENT span's id).

t=180  Response returned. Root span ends.
       All 8 spans exported to Collector with same trace_id.
       Collector waits 10s for late spans, then makes tail-sampling decision.
       Latency > 1s? No (180ms). Errors? No. Probability roll? Yes, keep.
       Exported to Jaeger.
```

In Jaeger UI you see the flame graph — exactly the tree above with bars proportional to duration.

## How to think aloud in the interview

> "Distributed tracing solves the 'where did the latency go' problem when a single request touches N services. Three primitives — trace, span, context propagation — plus a sampler.
>
> A trace is a tree of spans linked by `parent_span_id`. Each span captures one unit of work — an HTTP handler, a DB query, an outbound RPC — with start, duration, kind (SERVER/CLIENT/INTERNAL), and a bag of attributes.
>
> Context propagation is the hidden machinery: at the edge, the SDK generates `trace_id` and the sampling decision, then injects `traceparent` on every outbound call. Each downstream service extracts it on ingress and uses it as the parent for its own spans. The whole tree shares one `trace_id`.
>
> Sampling: at our scale you cannot keep 100%. Head-based (decide at root, propagate the bit) is cheap and gives you predictable volume. Tail-based (decide after the trace completes, in the Collector) lets you keep all errors and slow traces — much higher signal but needs more memory in the Collector. We typically run head sampling at 10% plus tail-based 'keep errors and >1s' for the long tail.
>
> Watch-outs: don't put high-cardinality free-text in attributes; do use semantic conventions; do propagate across async/queue boundaries explicitly; do use 128-bit trace ids."

## Important takeaways

- Trace = tree of spans linked by `parent_span_id`; root has no parent.
- W3C `traceparent` is the standard wire format: `ver-trace_id-span_id-flags`.
- Context propagation is the actual hard part — async, threads, queues, lambdas all need explicit carriers.
- Sampling decision pinned at the edge, encoded in flags byte, never re-rolled downstream.
- Head sampling = cheap, naive; tail sampling = keep errors + slow traces, needs Collector buffering.
- Semantic conventions (`http.method`, `db.system`, etc.) are how the backend builds indices.
- Cardinality discipline applies to span attributes the same as Prometheus labels.

## Variants

1. **Tail-based sampling design** — buffer traces in the Collector, decide after `decision_wait`. Memory budget = rps × avg trace size × wait.
2. **Tracing through Kafka / SQS** — inject `traceparent` into message headers (Kafka has them natively, SQS via message attributes). Consumer extracts and starts a CONSUMER-kind span with the producer span as a `Link`, not a parent (because the work is async).
3. **Tracing in serverless** — Lambda's X-Ray integration injects trace context via env vars; cold start spans show up as a notable first-span gap.
4. **eBPF-based tracing** (Pixie, Beyla) — auto-instruments without code changes, lower fidelity but zero deploy cost.
5. **Trace-to-log correlation** — every log line includes `trace_id` and `span_id`; one click in the trace UI jumps to filtered logs.
6. **Span events vs child spans** — events are tagged points-in-time within a span (no duration), child spans are nested work. Use events for "lock acquired", child spans for "DB query".

## Revision notes

> **distributed tracing primitives — 60 second recap**
> - **Trace** = tree of spans sharing one `trace_id`.
> - **Span** = one unit of work; has `span_id`, `parent_span_id`, kind, start, duration, attrs, events.
> - **Context propagation** = inject `traceparent` on egress, extract on ingress. W3C format. 128-bit trace id, 64-bit span id.
> - **Sampling** decided at edge, encoded in flags byte, propagated unchanged. Head (cheap) vs tail (keep errors + slow).
> - **SDK** (OpenTelemetry) instruments code; **Collector** receives, processes, exports; **Backend** (Jaeger/Tempo/Honeycomb) stores + queries.
> - **Traps**: per-service id generation, dropping context across async, high-cardinality attributes, tracing tight loops.
> - **Correlate with logs** via `trace_id` in log fields.
