# Structured Logging Patterns — JSON Logs, Key Naming, Redaction, Levels

## Source / Origin
- Twelve-Factor App, factor XI: "Logs": <a href="https://12factor.net/logs" target="_blank" rel="noopener noreferrer">https://12factor.net/logs</a>
- ELK / Loki / Datadog all expect JSON-structured input; unstructured text loses 80% of the value.
- Frequent interview prompt: "Walk me through what `logger.info('user signed in')` should actually emit in production."

## Why this question matters in interviews
Structured logging is the **table-stakes question** — if you can't answer it cleanly, the interviewer doubts whether you've operated production. The senior signal is specificity: JSON output to stdout, fixed top-level keys (ts, level, msg, service, trace_id, request_id), business attributes nested under `meta`, redaction at *emit* time not at *query* time, level discipline. Mid-level engineers concat strings: `logger.info(f"user {email} signed in from {ip}")` — un-indexable, leaks PII, can't filter. Senior engineers emit structured records with explicit fields. The difference is whether your logs are a *queryable dataset* or a *text dump*.

## Concepts involved

### Syntax / mechanism to lock in

The shape every log line should have:
```json
{
  "ts":         "2026-05-17T10:42:13.214Z",
  "level":      "INFO",
  "service":    "checkout",
  "version":    "v3.14.2",
  "env":        "prod",
  "host":       "ip-10-0-3-17",
  "logger":     "checkout.handlers",
  "msg":        "checkout completed",
  "trace_id":   "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id":    "00f067aa0ba902b7",
  "request_id": "8a7f6c2e-...",
  "user_id":    "usr_8421",
  "tenant_id":  "acme",
  "meta": {
    "order_id":    "ord_7733",
    "total_cents": 12999,
    "items":       3,
    "payment":     "stripe"
  }
}
```

Idiomatic emit (Python with structlog):
```python
import structlog
log = structlog.get_logger().bind(service="checkout", version=os.getenv("GIT_SHA"))

log.info("checkout completed",
         order_id=order.id,
         total_cents=order.total,
         items=len(order.items),
         payment=order.method)
# Output is the JSON above (after a JSONRenderer in the processor chain).
```

Node (pino):
```javascript
const logger = require('pino')({
  base: { service: 'checkout', version: process.env.GIT_SHA, env: process.env.ENV },
  formatters: { level: (label) => ({ level: label.toUpperCase() }) },
  timestamp: pino.stdTimeFunctions.isoTime,
  redact: { paths: ['req.headers.authorization', '*.password', '*.ssn'], censor: '[REDACTED]' },
});

logger.info({ order_id, total_cents, items, payment }, 'checkout completed');
```

### Edge cases / interview traps

1. **`msg` must be a static string.** "checkout completed" is searchable; "checkout completed for user@example.com in 423ms" is not. Put dynamic data in fields, not in the message.
2. **Never log secrets.** Tokens, passwords, JWTs, raw card numbers, SSN, API keys. Redact at emit time via library config — never trust developers to remember per call site.
3. **PII discipline.** Email, phone, full name are PII in most jurisdictions. Log `user_id` (opaque), not `email`. Hash if you must search by email.
4. **High-cardinality fields are fine in logs** (unlike metrics). `user_id`, `order_id`, `trace_id` belong here. The log backend indexes them.
5. **Don't double-nest.** `meta.meta.foo` is what you get when devs add wrappers. Keep one level of `meta` for business attrs; everything else flat at top.
6. **Stack traces as a field, not as multiline.** `err.stack` becomes `error.stack: "..."`. Multiline logs break parsers.
7. **stdout, not files.** In containers, logs go to stdout and the collector picks them up. Writing to files in a container is an anti-pattern.
8. **Synchronous logging blocks the request thread.** Use async loggers or buffered writers. Pino is non-blocking by default; Python `logging` is sync — wrap with `QueueHandler` or use `structlog` with async sinks.
9. **No `print()` in production.** Bypasses level filtering, redaction, formatters. Lint rule it out.
10. **Log sampling vs trace sampling are different.** If you sample logs to 10% you lose the ability to grep for a specific request. Sample by *level* (drop DEBUG, keep WARN+), not by request.

## Mental Model

```
Three audiences for logs:

   1. Humans during incident  — need: msg + level + context to grep
   2. Aggregators / dashboards — need: indexed fields (level, status, latency)
   3. Compliance / audit       — need: who-did-what-when, immutable, no PII

A single line that serves all three:

   {
     ts | level | service | host       ← INFRA fields (always)
     trace_id | request_id | user_id   ← CORRELATION fields (when in a request)
     msg                                ← STATIC human-readable event
     meta: { ... }                      ← BUSINESS attributes (kv pairs)
     err: { type, msg, stack }          ← ERROR sub-object (only if error)
   }

How it flows:

   app code → logger.info(msg, **fields)
            → processor chain (add ts, level, host, trace_id from MDC)
            → redaction processor (mask known sensitive paths)
            → JSON renderer
            → stdout
            → container runtime captures
            → log shipper (Vector, Fluent Bit, Promtail)
            → backend (Loki, Elasticsearch, Datadog, CloudWatch)
            → indexed for query
```

## Why interviewers care

- Logs are 60-80% of observability spend at most companies; getting the schema right is a budget decision.
- Tests whether you treat logs as a **dataset** (structured, queryable, joined to traces) or a **debug print stream** (text grep).
- Redaction discipline reveals security awareness — leaked secrets show up in logs more than anywhere else.
- Level discipline distinguishes "this engineer was woken up at 2 AM" from "this engineer wasn't" — DEBUG-everywhere production logs cost more and signal less.

## Common beginner confusion

- **"Structured logging just means JSON."** Format is necessary but not sufficient. Field discipline (names, types, cardinality), redaction, and level discipline matter more.
- **"f-strings are fine — I'll parse later."** Parsing free-text in 2026 is malpractice. Emit structured at source.
- **"DEBUG in prod is fine, we can filter."** DEBUG is the loudest level — even if you filter, the *emitting* cost (json.dumps, network, storage) is real. Disable at the logger, not at the query.
- **"Log everything; we can search later."** Storage is not free; per-GB-ingest pricing exists for a reason. Be intentional.
- **"Use `error` for any caught exception."** Error means "we couldn't do the work and human action may be needed." Caught-and-handled-and-retried is WARN or INFO.

## Brute force approach

Plain text:
```
[2026-05-17 10:42:13] INFO user 8421 signed in from 1.2.3.4 (took 423ms)
```

Works for one engineer reading one server. Fails the moment you grep across services, want to chart "signups per minute by region", or need to filter out PII for an external auditor. Acknowledge it, evolve from it.

## Optimal approach

1. **JSON to stdout.** One line per log event. No multiline.
2. **Fixed top-level keys** (`ts`, `level`, `msg`, `service`, `version`, `env`, `host`, `logger`).
3. **Correlation keys auto-injected from MDC** (`trace_id`, `span_id`, `request_id`, `user_id`, `tenant_id`) by ingress middleware.
4. **Business attributes flat or under `meta`** — kept *types*, not stringified.
5. **Redaction at the library level** — paths configured once, applied to every emit.
6. **Level discipline**: ERROR is rare; WARN is unusual-but-handled; INFO is "notable event in the request"; DEBUG is *off* in prod.
7. **One logger per module**, named by import path; lets you raise/lower level per package.

## Solution (production pattern + code/config)

### Python: `structlog` configuration

```python
# logging_setup.py
import logging, sys, time, structlog
from contextvars import ContextVar

_mdc: ContextVar[dict] = ContextVar("mdc", default={})

def add_mdc(logger, method_name, event_dict):
    event_dict.update(_mdc.get())
    return event_dict

def censor_secrets(logger, method_name, event_dict):
    SENSITIVE = {"password", "token", "ssn", "card_number", "authorization"}
    def walk(d):
        if isinstance(d, dict):
            return {k: ("[REDACTED]" if k.lower() in SENSITIVE else walk(v)) for k, v in d.items()}
        return d
    return walk(event_dict)

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        add_mdc,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts"),
        structlog.processors.dict_tracebacks,
        censor_secrets,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(sys.stdout),
    cache_logger_on_first_use=True,
)

log = structlog.get_logger()
```

Usage in a request handler:
```python
@app.post("/checkout")
async def checkout(req: CheckoutRequest):
    log.info("checkout.started", cart_size=len(req.items))
    try:
        order = await process(req)
        log.info("checkout.completed",
                 order_id=order.id,
                 total_cents=order.total_cents,
                 items=len(order.items),
                 payment=order.method)
        return order
    except StripeError as e:
        log.warning("checkout.payment_failed",
                    reason=e.code,
                    decline_code=e.decline_code)
        raise HTTPException(402, "payment_failed")
    except Exception:
        log.exception("checkout.crashed")          # exception → ERROR + stack
        raise
```

### Node / Pino — same shape

```javascript
const logger = require('pino')({
  base: { service: 'checkout', version: process.env.GIT_SHA },
  level: process.env.LOG_LEVEL || 'info',
  redact: {
    paths: ['req.headers.authorization', '*.password', '*.token', '*.card_number'],
    censor: '[REDACTED]',
  },
  formatters: {
    level: (label) => ({ level: label.toUpperCase() }),
    bindings: (b) => ({ host: b.hostname, pid: b.pid }),
  },
  timestamp: () => `,"ts":"${new Date().toISOString()}"`,
});

// Bound child logger per request
app.use((req, res, next) => {
  req.log = logger.child({
    request_id: req.id,
    trace_id:   req.span?.spanContext().traceId,
    user_id:    req.user?.id,
  });
  next();
});

app.post('/checkout', async (req, res) => {
  req.log.info({ cart_size: req.body.items.length }, 'checkout.started');
  // ...
});
```

### Log schema (document this in your repo)

```yaml
# docs/log-schema.yaml
top_level:
  ts:         { type: string, format: iso8601 }
  level:      { type: enum, values: [DEBUG, INFO, WARN, ERROR] }
  service:    { type: string }
  version:    { type: string, format: git-sha }
  env:        { type: enum, values: [dev, staging, prod] }
  host:       { type: string }
  logger:     { type: string }
  msg:        { type: string, must_be_static: true }
correlation:
  trace_id:   { type: string, format: hex32 }
  span_id:    { type: string, format: hex16 }
  request_id: { type: string }
  user_id:    { type: string, format: opaque_id }
  tenant_id:  { type: string }
business:
  meta:       { type: object, schemaless: true }
error:
  err.type:   { type: string }
  err.msg:    { type: string }
  err.stack:  { type: string }
```

## Step-by-step dry run

A user POSTs `/checkout` and Stripe declines:

```
1. Ingress middleware binds MDC:
     trace_id = 4bf9...4736
     request_id = 8a7f...
     user_id = usr_8421
     tenant_id = acme

2. Handler: log.info("checkout.started", cart_size=3)
   Emits:
     {"ts":"2026-05-17T10:42:13.000Z","level":"INFO","service":"checkout",
      "msg":"checkout.started","trace_id":"4bf9...","request_id":"8a7f...",
      "user_id":"usr_8421","tenant_id":"acme","cart_size":3}

3. Handler calls Stripe; Stripe returns card_declined.
   Catch StripeError:
   log.warning("checkout.payment_failed", reason="card_declined", decline_code="insufficient_funds")
   Emits:
     {"ts":"...","level":"WARN","msg":"checkout.payment_failed",
      "trace_id":"4bf9...","request_id":"8a7f...","reason":"card_declined",
      "decline_code":"insufficient_funds"}
   ← WARN, not ERROR: this is an expected business outcome, not a system fault.

4. Operator runs in Loki:
     {service="checkout", level="WARN", reason="card_declined"} | rate(5m) by (decline_code)
   Gets a chart of declines per minute by reason. Useful for product ops.

5. The user reports "my checkout failed."
   Operator: {service="checkout", request_id="8a7f..."}
   Sees both lines, plus the trace_id. Click → Jaeger flame graph.

6. Compliance audit asks "did we ever log card numbers in May?"
   Operator: {service="checkout"} |= "4242 4242"
   Zero matches — redaction worked.
```

## How to think aloud in the interview

> "Structured logging means JSON to stdout with a fixed schema. Top-level keys are infra (`ts`, `level`, `service`, `host`, `version`); correlation keys are auto-injected from request MDC (`trace_id`, `request_id`, `user_id`, `tenant_id`); the message is a *static* string — searchable; dynamic data goes in fields, never interpolated into `msg`.
>
> Redaction happens at the library level, not at the call site, with known sensitive paths configured once. Never log raw tokens, passwords, full card numbers, SSNs. Log `user_id` not `email`.
>
> Level discipline matters more than people realise. ERROR means 'we couldn't do the work and a human may need to act.' WARN means 'unusual but handled.' INFO is the workhorse — every notable event in a request. DEBUG is off in prod; if you need it, raise per-logger temporarily.
>
> Cost angle: per-GB ingest is real money. Log discipline is a budget lever. Drop the 50 log lines per request that nobody reads.
>
> Async: synchronous logging blocks the request thread. Pino is non-blocking; Python's stdlib `logging` is sync — wrap with `QueueHandler` or use structlog with an async sink.
>
> Output is stdout; the container runtime captures it; Vector or Fluent Bit ships to the backend; Loki or Elasticsearch indexes. The shape of the field is what makes that indexing useful — and that's the entire point of structured."

## Important takeaways

- JSON to stdout, fixed top-level schema, business attrs in fields not interpolated into `msg`.
- Correlation keys (trace_id, request_id, user_id, tenant_id) injected from MDC by ingress middleware.
- Redact at the library, not per call site.
- Levels: ERROR=human-action; WARN=unusual-handled; INFO=notable-event; DEBUG=off-in-prod.
- `print()` and f-string concatenation are banned at the linter level.
- Log volume is a budget; INFO discipline is a cost lever.
- High-cardinality identifiers belong in logs (unlike metrics).
- Document the schema and version it like an API.

## Variants

1. **Log levels per logger** — `logging.getLogger("sqlalchemy.engine").setLevel(WARNING)` to silence verbose libraries without losing your own DEBUG.
2. **Sampling by level** — keep 100% of ERROR+WARN, sample INFO to 10% on extremely hot paths. Done at the collector, not the app.
3. **Audit logs as a separate sink** — security events go to a write-once store (S3 + object lock), not the regular log backend.
4. **OTEL Logs SDK** — emits logs *as part of the trace* via OTLP, joining the three pillars at the source. Newer pattern, gaining adoption.
5. **Per-tenant log isolation** — multi-tenant SaaS sometimes needs `tenant_id` indexed and routed to per-tenant log streams.
6. **Forensic logging** — bigger payload (full request body) for a small sampled %, used for incident replay.

## Revision notes

> **structured logging patterns — 60 second recap**
> - **JSON to stdout**, one line per event, fixed schema.
> - **Top-level**: ts, level, service, version, host, msg, trace_id, request_id, user_id, tenant_id.
> - **Business attrs as fields**, not interpolated into msg.
> - **Redaction at library level** (known sensitive paths).
> - **Level discipline**: ERROR rare, WARN unusual-handled, INFO notable, DEBUG off-in-prod.
> - **MDC injected by ingress middleware** — correlation keys appear on every line.
> - **No print(), no multiline, no PII**.
> - **Logger per module**, raise/lower per package.
> - Logs are a **dataset**, not a debug stream.
