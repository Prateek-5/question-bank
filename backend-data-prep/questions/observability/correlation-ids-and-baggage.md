# Correlation IDs and OpenTelemetry Baggage — Threading Identity Through the Stack

## Source / Origin
- Pre-OTel pattern: every mature microservices shop (Twitter, Uber, Shopify) wrote their own `X-Request-ID` middleware before OpenTelemetry standardised baggage.
- W3C Baggage spec: <a href="https://www.w3.org/TR/baggage/" target="_blank" rel="noopener noreferrer">https://www.w3.org/TR/baggage/</a>
- OpenTelemetry Baggage API: <a href="https://opentelemetry.io/docs/specs/otel/baggage/" target="_blank" rel="noopener noreferrer">https://opentelemetry.io/docs/specs/otel/baggage/</a>
- Common interview prompt: "A user reports 'my checkout failed at 14:32'. How do you find every log line, every metric, and every span related to *that one request*?"

## Why this question matters in interviews
This is the **operational hygiene question** — companies separate "engineers who can debug at 3 AM" from "engineers who can't" largely by whether they've internalised correlation. Mid-level says "we'd add request_id." Senior says "request_id is the entry-point correlation key, trace_id is the cross-service one, baggage carries non-identifying context like tenant_id and feature_flag_state, all three injected into the logger MDC at ingress and propagated via traceparent + baggage headers." The distinction between *correlation ids* (identifiers) and *baggage* (key-value attributes you carry along) is exactly what a senior engineer is expected to draw cleanly.

## Concepts involved

### Syntax / mechanism to lock in

Inbound middleware (Express, idiomatic):
```javascript
const { context, propagation, trace } = require('@opentelemetry/api');

app.use((req, res, next) => {
  // 1. Pull existing trace context + baggage from headers (W3C)
  const parentCtx = propagation.extract(context.active(), req.headers);

  // 2. Generate request_id if none on the wire (entry point)
  const requestId = req.headers['x-request-id'] || crypto.randomUUID();
  res.setHeader('x-request-id', requestId);

  // 3. Attach to baggage so downstream services can read it too
  const baggage = propagation.getBaggage(parentCtx)
                  || propagation.createBaggage();
  const enriched = baggage
    .setEntry('request.id',  { value: requestId })
    .setEntry('tenant.id',   { value: req.user?.tenantId ?? 'anon' })
    .setEntry('feature.exp', { value: req.headers['x-experiment'] ?? '' });

  const ctxWithBaggage = propagation.setBaggage(parentCtx, enriched);

  // 4. Run the rest of the request in this context
  context.with(ctxWithBaggage, () => {
    // 5. Bind logger MDC so every log line has these fields
    logger.withContext({
      request_id: requestId,
      trace_id:   trace.getSpan(ctxWithBaggage)?.spanContext().traceId,
      tenant_id:  req.user?.tenantId,
    }, () => next());
  });
});
```

The wire format:
```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
baggage:     request.id=8a7f...,tenant.id=acme,feature.exp=newcheckout=B
x-request-id: 8a7f-...                       ← legacy header, kept for compat
```

### Edge cases / interview traps

1. **`request_id` vs `trace_id` vs `correlation_id`** — pick one, document the mapping. Best practice: `trace_id` from OTel *is* the correlation id; `x-request-id` is its hex string mirrored for human reading.
2. **Baggage is plaintext on the wire.** Don't put PII or auth tokens in it. Tenant id, feature flag bucket, experiment arm: yes. User email, JWT: never.
3. **Baggage size limit** — W3C says servers may reject baggage > 8192 bytes. Keep it under 1 KB; it's appended to every outbound request.
4. **Baggage propagates everywhere by default** — including to third parties (Stripe, Twilio) if your HTTP client doesn't strip it. Configure egress filters.
5. **Async + thread pool context loss** — `setTimeout`, `Promise.then`, worker pools all drop the AsyncLocalStorage context unless you bind explicitly. This is the #1 reason logs lose `trace_id`.
6. **Logger MDC vs span attributes** — same data, two places. Put correlation ids in MDC (so every log line has them). Put business attributes on the span (so the trace search works).
7. **Generated request id collisions** — UUIDv4 is fine; 32-hex of `trace_id` is fine; short tokens (8 hex chars) collide. Don't shorten for "readability."
8. **Frontend-issued vs backend-issued** — let the frontend send `x-request-id` if it has one; backend generates only if missing. Lets you correlate browser console errors with backend logs.

## Mental Model

```
Three identifiers + one bag of attributes:

   request_id   one per HTTP request   (caller-supplied or generated)
   trace_id     one per distributed trace (cross-service correlation)
   span_id      one per unit of work    (within a trace)
   baggage      arbitrary key/value     (carried in W3C `baggage` header)

How they flow (left to right is downstream calls):

  [ Browser ] ──HTTP──► [ Edge LB / Frontend ] ──HTTP──► [ Auth Svc ] ──HTTP──► [ Order Svc ] ──Kafka──► [ Worker ]
                          │  inject:                        │  extract+pass-on    │ ...               │
                          │  x-request-id: 8a7f...          │                     │                   │
                          │  traceparent: 00-4bf9...-...    │                     │                   │
                          │  baggage: tenant.id=acme        │                     │                   │
                          ▼                                 ▼                     ▼                   ▼
                       [ logger MDC binds: request_id, trace_id, tenant_id ]   ... same ...      ... same ...

Every log line emitted anywhere in that flow now carries:
    {"ts":"...","level":"INFO","msg":"...","request_id":"8a7f...","trace_id":"4bf9...","tenant_id":"acme"}
```

The shift in mindset: **identifiers are for joining datasets** (logs ⨝ traces ⨝ metrics). Baggage is **context you'd otherwise have to re-fetch**.

## Why interviewers care

- It's the single biggest force multiplier on debug speed. Postmortems where the team had correlation ids resolve in hours; without them, in days.
- Tests whether you understand context propagation as a system property, not a per-service convention.
- Baggage forces you to think about **what travels through versus what stays local** — an architecture question dressed up as a logging question.
- It's the bridge between observability (correlate at debug time) and feature flagging / experimentation (carry the assignment downstream).

## Common beginner confusion

- **"Just add `req.id` to every log line."** Works in one service. Falls apart the moment you have a second.
- **"Use the same id everywhere."** Conflates request id, trace id, session id, transaction id. They are different lifetimes; conflating them creates ambiguity.
- **"Baggage is for logging."** No — baggage is for *carrying context* (tenant, flag, experiment) so downstream services can branch on it without re-fetching. Logging is a side benefit.
- **"Put the JWT in baggage so I don't need to re-decode."** Catastrophic — baggage is plaintext, propagates to externals, gets logged.
- **"AsyncLocalStorage propagates everywhere."** It propagates across `await`, but not across worker_threads, child_process, queue boundaries, or `setImmediate` in older Node. Test it.

## Brute force approach

"Add a `req_id` query param to every internal call." Works until someone uses a library that strips query params (caching, proxies). Doesn't survive Kafka, doesn't survive cron jobs picking up DB rows.

"Stuff everything into one big header." Becomes 5 KB; some proxies (CloudFront, certain LBs) cap headers; you've reinvented baggage poorly. Skip this — go straight to the W3C standard.

## Optimal approach

Three layers, each with a clear role:

1. **`trace_id` + `span_id`** (from OTel) — machine-readable cross-service correlation. Propagated via `traceparent`.
2. **`x-request-id`** — human-readable mirror, optionally caller-supplied for end-to-end correlation including the browser/CLI.
3. **W3C `baggage`** — small set of *non-sensitive* context keys (`tenant.id`, `feature.exp`, `region`). Propagated automatically; readable by all downstream code.

At ingress, every service: extracts → enriches → binds to logger MDC → runs the handler in that context. At egress, the OTel propagators auto-inject.

## Solution (production pattern + code/config)

### Python (FastAPI + OpenTelemetry) ingress middleware

```python
import uuid
import logging
from contextvars import ContextVar
from opentelemetry import trace, baggage, context as otel_context
from opentelemetry.propagate import extract, inject

_request_ctx: ContextVar[dict] = ContextVar("request_ctx", default={})

class CorrelationMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        headers = {k.decode(): v.decode() for k, v in scope["headers"]}
        ctx = extract(headers)
        request_id = headers.get("x-request-id") or uuid.uuid4().hex
        tenant_id  = headers.get("x-tenant-id", "anon")

        ctx = baggage.set_baggage("request.id", request_id, context=ctx)
        ctx = baggage.set_baggage("tenant.id",  tenant_id,  context=ctx)

        token = otel_context.attach(ctx)
        _request_ctx.set({
            "request_id": request_id,
            "trace_id":   trace.get_current_span().get_span_context().trace_id,
            "tenant_id":  tenant_id,
        })
        try:
            await self.app(scope, receive, send)
        finally:
            otel_context.detach(token)


class CorrelationLogFilter(logging.Filter):
    def filter(self, record):
        ctx = _request_ctx.get()
        record.request_id = ctx.get("request_id", "-")
        record.trace_id   = format(ctx.get("trace_id", 0), "032x")
        record.tenant_id  = ctx.get("tenant_id",  "-")
        return True
```

### Egress — auto-injection via OTel HTTP instrumentation

```python
# When you do requests.get(...) or httpx.get(...) the instrumentation
# already injects `traceparent` AND `baggage` headers. You don't write code.
# Verify with:
import requests
r = requests.get("http://downstream/api")
# r.request.headers contains:
#   traceparent: 00-<trace_id>-<span_id>-01
#   baggage:     request.id=...,tenant.id=acme
```

### Logger configuration (JSON output with correlation fields)

```python
import json, logging, sys, time

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "ts":         time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level":      record.levelname,
            "logger":     record.name,
            "msg":        record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "trace_id":   getattr(record, "trace_id",   "-"),
            "tenant_id":  getattr(record, "tenant_id",  "-"),
            "service":    "checkout",
        })

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
handler.addFilter(CorrelationLogFilter())
logging.basicConfig(handlers=[handler], level=logging.INFO)
```

### Kafka producer/consumer baggage propagation

```python
# Producer
from opentelemetry.instrumentation.kafka import KafkaInstrumentor
KafkaInstrumentor().instrument()  # auto-injects into message headers

producer.send("orders", value=payload, headers=[])  # OTel adds traceparent + baggage

# Consumer
def handle(msg):
    ctx = extract({h[0]: h[1].decode() for h in msg.headers})
    token = otel_context.attach(ctx)
    try:
        process(msg)
    finally:
        otel_context.detach(token)
```

## Step-by-step dry run

A user clicks "Place Order" in the browser:

```
1. Browser → POST /checkout
   Headers: (none from browser)

2. Edge LB receives. No traceparent.
   Service generates:
     trace_id   = 4bf92f3577b34da6a3ce929d0e0e4736
     span_id    = 00f067aa0ba902b7
     sampled    = 01
     request_id = 8a7f6c2e-...
   Sets baggage:
     request.id=8a7f6c2e..., tenant.id=acme, feature.exp=ckout=B
   Logs:
     {"ts":"...","level":"INFO","msg":"received POST /checkout",
      "request_id":"8a7f6c2e...","trace_id":"4bf9...","tenant_id":"acme"}

3. Edge calls Order service over HTTP.
   Headers automatically injected:
     traceparent: 00-4bf9...-00f0...-01
     baggage:     request.id=8a7f...,tenant.id=acme,feature.exp=ckout=B

4. Order service extracts. Logger MDC now bound.
   Decides: feature.exp says "ckout=B" → take new code path. No DB lookup needed.
   Logs:
     {"...","request_id":"8a7f6c2e...","trace_id":"4bf9...","tenant_id":"acme",
      "msg":"using checkout B path"}

5. Order publishes to Kafka topic `payment.requested`.
   OTel Kafka instrumentation puts traceparent + baggage into record headers.

6. Worker consumes. Extracts headers, attaches context.
   Worker's log lines also carry the same trace_id / request_id / tenant_id.

7. At 14:32 the user reports failure.
   You search logs in Loki / ES:
     {request_id="8a7f6c2e..."}                ← single grep across all services
     OR
     {trace_id="4bf92f3577b34da6a3ce929d0e0e4736"}
   You find 47 log lines spanning 4 services in 380ms.
   Click "view trace" → Jaeger UI with the full span tree.
```

## How to think aloud in the interview

> "Two distinct concerns: *identifiers for joining* and *context to carry*. I'd standardise on three.
>
> First, `trace_id` from OpenTelemetry is the cross-service correlation. Generated at the edge, propagated via W3C `traceparent`. 128 bits, hex-encoded.
>
> Second, `x-request-id` is the human-facing mirror. Caller-supplied if available (browser, mobile client, CLI); generated at the edge otherwise. I bind both to the logger MDC at ingress so every log line in every service has them.
>
> Third, W3C `baggage` for the non-identifying context that downstream services need: `tenant.id`, `feature.exp`, `region`. This is what lets a downstream service make a routing decision without an RPC back to identity service.
>
> Critical hygiene: baggage is plaintext on the wire and gets logged, so no PII, no tokens, no anything you wouldn't print on a billboard. Strip baggage at egress to third parties. Cap size — proxies start rejecting at 8 KB. Don't shorten ids for "readability" — collisions are silent.
>
> The hard part is async context propagation. AsyncLocalStorage covers `await`; worker_threads, queue handoffs, and `setImmediate` need explicit binding. The symptom of getting it wrong is log lines without `trace_id` — that's the smoke test.
>
> Payoff: when a user says 'my checkout failed at 14:32', I grep `request_id=...` and get every log line across every service in one query. From there, one click to the trace UI for the timing breakdown. Resolution moves from hours to minutes."

## Important takeaways

- Three identifiers: `request_id` (entry-point), `trace_id` (cross-service), `span_id` (work unit). Make the mapping explicit.
- W3C `baggage` carries small, non-sensitive context (tenant, flag, region) — *not* logging.
- Bind all of them into logger MDC at ingress so every log line has them.
- Strip baggage on egress to third parties.
- Async context loss (workers, queues) is where this breaks; test it explicitly.
- Caller-supplied `x-request-id` lets you correlate browser → backend.
- Never put PII, JWTs, or secrets in baggage.

## Variants

1. **Inject baggage into DB queries** — pg_stat_statements or APM agents tag queries with `/* trace_id=..., tenant_id=... */` comments so DB-side slow logs correlate to traces.
2. **Lambda / serverless** — env var `_X_AMZN_TRACE_ID` carries trace info; baggage requires custom propagator since AWS uses its own format. OTel has an X-Ray propagator that bridges.
3. **Cron / batch jobs** — no incoming request; generate a fresh trace at job start, treat the cron name as the entry point.
4. **GraphQL** — one HTTP request → many resolvers. Use one trace, one span per resolver, baggage carries `operation.name`.
5. **WebSocket** — long-lived connection; create a new trace per *message*, not per connection. Connection id is just an attribute.
6. **Cross-region with sensitive baggage** — encrypt the baggage value with a per-region KMS key; decrypt at consumer.

## Revision notes

> **correlation ids and baggage — 60 second recap**
> - **request_id**: entry-point, caller-supplied or generated, human-readable.
> - **trace_id / span_id**: OTel, cross-service joins, 128/64-bit.
> - **baggage** (W3C): key/value context, propagated automatically, *not* for PII.
> - **Bind all into logger MDC at ingress** — every log line has them.
> - **OTel propagators auto-inject on egress** — HTTP, gRPC, Kafka headers.
> - **Async context loss** = #1 failure mode (worker threads, queue handoffs).
> - **Size cap**: keep baggage < 1 KB; some proxies reject > 8 KB.
> - **Payoff**: grep `request_id=X` returns every log line across N services.
