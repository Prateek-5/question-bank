# Log Levels and Sampling — DEBUG/INFO/WARN/ERROR Semantics + Sample-by-Level

## Source / Origin
- Syslog severity levels (RFC 5424) — the original 8-level hierarchy that modern loggers compress to 5.
- Google SRE Book, Ch. 16 "Tracking Outages": discipline around what warrants paging vs logging.
- Common interview prompt: "When do you use WARN vs ERROR? Walk me through a 5xx response — does that log at ERROR? What about a 404?"

## Why this question matters in interviews
Level discipline is a **culture marker** in production engineering. Mid-level engineers use ERROR for any caught exception (which floods alerts, dulls on-call, hides real outages). Senior engineers reserve ERROR for "human action required" and route everything else appropriately. This question filters out engineers who treat the logger as a `print` and those who treat it as a signalling pipeline. The follow-up — "how do you sample logs without losing the ability to debug?" — separates engineers who have managed log spend at scale from those who haven't.

## Concepts involved

### Syntax / mechanism to lock in

The semantic ladder:
```
TRACE  rarely used; verbose internal state for a code path under investigation
DEBUG  developer-loop detail; off in prod by default
INFO   notable business events; "request received", "checkout completed"
WARN   unusual but handled; "retry succeeded after 2 attempts", "card declined"
ERROR  the work failed AND a human may need to act (alert-worthy if frequency > threshold)
FATAL  process is dying; emit then exit (very rare in modern services)
```

A canonical decision tree:
```python
try:
    result = process(req)
except RetryableError as e:
    log.warning("upstream.transient", attempt=attempt, err=str(e))
    retry()
except BusinessReject as e:                  # card declined, insufficient stock
    log.info("business.reject", reason=e.code)
    return reject_response(e.code)
except ValidationError as e:                 # bad input from client
    log.info("client.validation_failed", field=e.field)
    return http_400(e.message)
except Exception:
    log.exception("checkout.crashed")        # unhandled → ERROR + stack
    raise
```

Per-logger level override:
```python
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("checkout").setLevel(logging.INFO)
```

### Edge cases / interview traps

1. **5xx response ≠ ERROR.** If you returned 500 because the user uploaded a 50 GB file and your validator rejected it, that's an INFO-level business event for you and a client problem. ERROR is reserved for "*we* couldn't do *our* job."
2. **4xx is almost never ERROR.** 400/401/403/404 are normal user/client behaviour. Logging them at ERROR drowns the signal.
3. **Caught-and-handled ≠ ERROR.** A timeout you retried successfully is WARN, not ERROR. The retry succeeded — the work happened.
4. **WARN vs INFO for retries** — first retry: INFO. Multiple retries before success: WARN. All retries failed: ERROR.
5. **DEBUG in prod is a cost trap.** Even with a level filter at the handler, the *emit cost* (`json.dumps`, attribute lookups) is paid before filtering in many loggers. Disable at the *logger* level, not at the handler.
6. **Sampling logs by request loses debug capability.** If you sample 10% of *all* logs by request_id, the user who reports a problem is in the 90% you dropped. Sample by *level* (drop INFO to 10%, keep WARN+ at 100%) instead.
7. **Sampling preserves "for sampled traces, keep full logs"** — if a trace is sampled, keep its INFO logs at 100%; if not, sample them. Honeycomb, Datadog support this.
8. **`logger.exception` vs `logger.error(exc_info=True)`** — `.exception` is `.error` with `exc_info=True`. Use `.exception` *only* inside `except`, never elsewhere.
9. **FATAL exits the process.** Most modern code skips this level — let the process crash naturally with a stack trace at ERROR.
10. **Alerting off ERROR rate, not ERROR count.** Spike in `errors_per_min` is the metric; the log line is the evidence.

## Mental Model

```
Who reads each level?

   DEBUG  — me, during local development (sometimes during incident, temporarily)
   INFO   — me + dashboards (events I'd chart: signups, checkouts, retries)
   WARN   — me + dashboards (charts I'd want to *trend*; rising = bad)
   ERROR  — me + on-call alerts (rate above threshold = page)
   FATAL  — me + the process supervisor (it's already crashing)

Alerting policy mapped to levels:

   ERROR rate > 1 / sec for 5 min       → page
   WARN  rate > 10 / sec for 5 min      → ticket
   INFO  charts on dashboards           → no alert, just observation
   DEBUG nothing — disabled in prod

The sample-by-level pyramid (volume on left, signal on right):

   DEBUG  ████████████████████  drop in prod                signal: 0%
   INFO   ████████              sample to 10% on hot paths  signal: 60%
   WARN   ██                    keep 100%                   signal: 90%
   ERROR  ▌                     keep 100%                   signal: 100%
```

## Why interviewers care

- Production cost: log ingest fees scale linearly with volume. Level discipline is a 5-10x cost lever.
- Alert hygiene: ERROR-level discipline directly drives on-call quality. Bad levels → alert fatigue → missed real outages.
- Tests whether you understand that "the logger is an API to two systems: the human reader and the alerting pipeline."
- Sampling reveals your scale instincts — sampling-by-request is wrong, sampling-by-level is right.

## Common beginner confusion

- **"Errors always log at ERROR."** Plenty of "errors" are business outcomes — log INFO/WARN. Reserve ERROR for "human action."
- **"More logging = better debug."** Past a point, more is worse — signal drowns in noise. Each log line should *earn its keep*.
- **"DEBUG in prod is fine, we filter."** Filter happens after emit cost. Disable at the logger.
- **"Sampling logs means we lose data."** Sampling by *level* loses noise, keeps signal. Sampling by *request* loses signal.
- **"WARN and INFO are interchangeable."** WARN should trend *up* when something is wrong. INFO is baseline activity.
- **"I'll just paste the exception into the message."** Use `.exception()` so the stack becomes structured (`err.type`, `err.msg`, `err.stack`), not a multiline blob.

## Brute force approach

"Log everything at INFO; we'll filter later." Costs 10x what disciplined logging costs, dulls the signal so much that on-call missed alerts become the norm. The filter you'll write later is harder than the discipline you should have applied up front.

"Page on every ERROR." Within a week, on-call is numb to pages. By month two, real outages get missed because the team has banner blindness for the alerting tool.

## Optimal approach

1. **Define the level contract in a doc.** Concrete examples per level.
2. **Lint enforcement** — no `print()`, no `logger.error()` for caught-and-handled-and-retried.
3. **Disable DEBUG in prod at the logger** (config flag, default OFF).
4. **Library noise filtering** — set `sqlalchemy`, `urllib3`, `boto3` to WARN by default.
5. **Sample INFO on hot paths**, keep WARN/ERROR 100%.
6. **Alert on ERROR rate**, not raw count; thresholds tied to baselines.
7. **Periodic level audit** — quarterly review of top emitters; demote chatty INFOs.

## Solution (production pattern + code/config)

### Python: per-logger level config from env

```python
import logging, os

DEFAULT = os.getenv("LOG_LEVEL", "INFO").upper()
OVERRIDES = {
    "sqlalchemy.engine":          "WARNING",
    "urllib3.connectionpool":     "WARNING",
    "botocore":                   "WARNING",
    "checkout.handlers":          DEFAULT,
    "checkout.payment":           DEFAULT,
}

logging.getLogger().setLevel(getattr(logging, DEFAULT))
for name, lvl in OVERRIDES.items():
    logging.getLogger(name).setLevel(getattr(logging, lvl))
```

### Sample-by-level at the collector (Vector config)

```toml
# vector.toml — drop 90% of INFO lines unless the trace is sampled
[sources.app_logs]
type = "stdin"

[transforms.parse]
type    = "remap"
inputs  = ["app_logs"]
source  = '. = parse_json!(.message)'

[transforms.sample_info]
type    = "sample"
inputs  = ["parse"]
rate    = 10                   # keep 1 in 10
exclude = '''
  .level == "WARN" || .level == "ERROR" || exists(.sampled_trace)
'''

[sinks.loki]
type   = "loki"
inputs = ["sample_info"]
endpoint = "http://loki:3100"
```

### "If trace sampled, keep all logs" pattern

```python
# After context setup, mark logs so the collector keeps them all for sampled traces
@app.middleware("http")
async def mark_sampled(request, call_next):
    span = trace.get_current_span()
    if span.get_span_context().trace_flags.sampled:
        structlog.contextvars.bind_contextvars(sampled_trace=True)
    return await call_next(request)
```

### Alert rule (Prometheus / Grafana)

```yaml
# alerts.yml
groups:
- name: log-derived
  rules:
  - alert: ServiceErrorRateHigh
    expr: |
      sum by (service) (rate(log_lines_total{level="ERROR"}[5m]))
      / sum by (service) (rate(log_lines_total[5m]))
      > 0.01
    for: 10m
    labels: { severity: page }
    annotations:
      summary: "{{ $labels.service }} error rate > 1% for 10m"
```

### Level decision table (post on the team wiki)

| Situation                                          | Level | Why                         |
|----------------------------------------------------|-------|------------------------------|
| Request received                                   | INFO  | dashboard event             |
| Request completed OK                               | INFO  | dashboard event             |
| Client sent bad input (400)                        | INFO  | client problem              |
| Auth failed (401/403)                              | INFO  | normal user behaviour       |
| Not found (404)                                    | INFO  | normal                      |
| Card declined / business reject                    | INFO  | normal business outcome     |
| Retry succeeded on first attempt                   | INFO  | normal                      |
| Retry succeeded after 2+ attempts                  | WARN  | trending = upstream issues  |
| Circuit breaker opened                             | WARN  | degraded but handled        |
| Slow request > p99 baseline                        | WARN  | degraded                    |
| All retries exhausted; request failed              | ERROR | human may need to act       |
| Unhandled exception                                | ERROR | bug                         |
| DB connection pool exhausted                       | ERROR | needs paging                |
| Out of memory / process about to die               | FATAL | crashing                    |

## Step-by-step dry run

A request to `/checkout`; the payment gateway is flapping.

```
1. INFO  "checkout.started" cart_size=3
   ← dashboards count this; baseline event.

2. INFO  "payment.attempt" gateway="stripe" attempt=1
   ← attempt 1 fails (502 from Stripe).

3. WARN  "payment.retry" gateway="stripe" attempt=2 reason="upstream_5xx"
   ← we retried; trending count of WARN tells ops Stripe is flapping.

4. INFO  "payment.attempt" gateway="stripe" attempt=2  (succeeds)
5. INFO  "checkout.completed" order_id=ord_7733 total_cents=12999

Volume: 5 lines for 1 request.

Now in prod with sample-by-level (INFO→10%, WARN+→100%):
   Line 1 sampled out (90%)         dropped
   Line 2 sampled out               dropped
   Line 3 kept (WARN)               KEPT
   Line 4 sampled out               dropped
   Line 5 sampled out               dropped

We kept the *signal* (Stripe flap) and dropped the *noise* (baseline events).

But this request's trace was sampled by head sampler. Middleware bound
`sampled_trace=true`; Vector rule excludes it from drop. All 5 lines kept.

For unsampled traces with the same shape: only the WARN line lands in storage.
We still see "Stripe flap rate" trend on the dashboard. Cost down ~10x.
```

If Stripe goes fully down:
```
1. INFO  "checkout.started"
2. INFO  "payment.attempt" attempt=1   (fails)
3. WARN  "payment.retry"   attempt=2   (fails)
4. WARN  "payment.retry"   attempt=3   (fails)
5. ERROR "payment.exhausted" reason="upstream_unavailable" attempts=3
6. INFO  "checkout.failed" reason="payment_unavailable"

ERROR rate spikes → alert fires after 10 min sustained → on-call paged.
WARN rate spikes earlier → dashboard shows pre-trigger; on-call may pre-empt.
```

## How to think aloud in the interview

> "Levels aren't aesthetic — they're a contract with two consumers: the human grepping logs during an incident, and the alerting pipeline.
>
> ERROR means 'we couldn't do the work and a human may need to act.' It's rare. 4xx responses don't qualify — those are client problems. Caught-and-retried-and-succeeded doesn't qualify — that's WARN. Business rejects (card declined, out of stock) don't qualify — that's INFO.
>
> WARN is the trend signal. Anything you want to chart and alert on when it spikes. Retries that succeed after multiple attempts, circuit breakers opening, slow requests above baseline.
>
> INFO is the dashboard workhorse: request started, request completed, business event. High volume, no alert.
>
> DEBUG is off in prod by default. Even with a handler-level filter the emit cost is real; disable at the logger.
>
> For sampling: I sample *by level*, not by request. Drop 90% of INFO on hot paths, keep all WARN and ERROR. If a trace is head-sampled, keep all its INFO too — so the trace UI has full logs but the bulk is dropped. Sampling by request loses the user-reported-bug case; sampling by level loses only noise.
>
> Alerting fires off ERROR *rate*, not raw count. 1% of requests at ERROR sustained 10 min → page. The threshold is calibrated to baseline so a tiny background level doesn't wake anyone."

## Important takeaways

- ERROR = "human may need to act"; reserve it.
- 4xx is rarely ERROR; business rejects are INFO; caught-and-handled is WARN.
- DEBUG off in prod at the logger, not at the handler.
- Sample by level (drop INFO noise, keep WARN+); never sample by request id.
- "If trace sampled, keep all logs" pattern is the best of both.
- Alert on ERROR *rate* relative to baseline, with `for: 10m` to dampen spikes.
- Library noise (`sqlalchemy`, `urllib3`) silenced to WARN by default.
- Quarterly audit the top INFO emitters and demote them.

## Variants

1. **Per-tenant level overrides** — escalate one tenant to DEBUG temporarily for a support case without affecting others.
2. **Dynamic level change without restart** — admin endpoint or feature-flag-driven log level adjustment per logger.
3. **First-N-then-sample** — keep first 100 of each (level, key) per minute, sample the rest. Captures the leading edge of incidents.
4. **Forensic mode** — under sustained ERROR, automatically raise nearby loggers to DEBUG for the next 5 min.
5. **Severity-aware retry** — only retry on WARN-class transient failures; ERROR-class is "stop and surface."
6. **OTel Logs Severity** — maps to numeric severity (1-24); standardised across exporters.

## Revision notes

> **log levels and sampling — 60 second recap**
> - **ERROR** = human-action; **WARN** = unusual-handled / trend signal; **INFO** = business event; **DEBUG** = dev loop, off in prod.
> - **4xx and business rejects are INFO**, not ERROR.
> - **Retry success is WARN**, retry exhausted is ERROR.
> - **Disable DEBUG at the logger**, not the handler — emit cost is real.
> - **Sample by level, not by request**: drop 90% of INFO, keep WARN+ at 100%.
> - **Sampled traces keep all logs** — bind `sampled_trace=true`, exclude from drop rule.
> - **Alert on ERROR rate relative to baseline**, with sustained-time gate.
> - **Library noise silenced**: sqlalchemy/urllib3 → WARN by default.
> - **Audit quarterly**; demote chatty emitters.
