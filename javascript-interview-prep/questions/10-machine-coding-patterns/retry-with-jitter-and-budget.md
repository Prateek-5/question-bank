# Retry with Exponential Backoff, Jitter, and a Retry Budget

## Source / Origin
- AWS Architecture Blog: "Exponential Backoff And Jitter" (Marc Brooker, 2015).
- Asked at: AWS, Stripe, Razorpay, Atlassian, Uber, Booking.
- Concept reference: `concepts/promises.md`; sibling `circuit-breaker.md`.

## Why this question matters in interviews
Retry without jitter caused the "thundering herd" pattern that took down half the internet in the late 2000s. Senior interviewers want to see you know: (1) plain exponential is bad — it synchronizes the herd; (2) full jitter is the AWS default; (3) retry budget prevents amplification cascades; (4) only retry idempotent operations or rely on idempotency keys; (5) pair retry with circuit breaker. Get all five and you're senior. Miss any and you're still mid-level.

## Concepts involved

### Syntax to lock in
```js
async function retry(fn, { attempts = 5, baseMs = 100, maxMs = 30_000, jitter = 'full', isRetryable = (e) => true } = {}) {
  let lastErr;
  for (let i = 0; i < attempts; i++) {
    try { return await fn(i); }
    catch (e) {
      lastErr = e;
      if (!isRetryable(e) || i === attempts - 1) throw e;
      const delay = backoff(i, baseMs, maxMs, jitter);
      await sleep(delay);
    }
  }
  throw lastErr;
}

function backoff(attempt, baseMs, maxMs, jitter) {
  const cap = Math.min(maxMs, baseMs * 2 ** attempt);   // exponential, capped
  switch (jitter) {
    case 'none':         return cap;                                    // bad — herd
    case 'equal':        return cap / 2 + Math.random() * cap / 2;      // half fixed + half random
    case 'decorrelated': /* see below */ return decorrelated(attempt);
    case 'full': default:
      return Math.random() * cap;                                       // AWS default
  }
}

const sleep = (ms) => new Promise(r => setTimeout(r, ms));
```

### Edge cases / interview traps
1. **Retrying non-idempotent ops** — POST that creates a charge: second retry might double-charge. Use idempotency keys (see `idempotency-wrapper.md`) or only retry on safe verbs.
2. **`isRetryable` discrimination** — 4xx (caller error) ≠ retryable; 5xx, timeout, network reset = retryable. Don't retry validation errors.
3. **No cap on backoff** — runaway sleep makes p99 latency unpredictable. Always have `maxMs`.
4. **No jitter** — clients that all started together will all retry together. Herd amplifies on the recovering service.
5. **No budget** — every caller retries 5x; with 3 levels of nesting, that's 125x amplification. Add a *retry budget* (token bucket of retry attempts) shared across calls.
6. **Retry inside a circuit-open zone** — combine with `CircuitBreaker.exec(() => retry(fn))`; the breaker short-circuits when the downstream is dead.
7. **AbortSignal not threaded** — long backoff blocks a request that the caller already cancelled. Accept signal; reject `sleep()` on abort.
8. **Per-call vs per-attempt timeout** — pick one. Don't accidentally allow `attempts × perCall` total time.

## Mental Model

Retries are **rolling a die before each attempt**. Without jitter, all clients roll the same face at the same time — they all retry at t=100, then t=200, then t=400. Jitter randomizes the face: some retry at t=37, some at t=180. The recovering service sees a smoothed load instead of a spike.

```
NO JITTER (synchronized herd):
clients ──▶ failure
  retry @ +100ms   (all 1000 clients hit at once)
  retry @ +200ms   (all 1000 clients hit at once again)
  retry @ +400ms

FULL JITTER (random in [0, cap)):
clients ──▶ failure
  retry @ U(0,100ms)   ← spread evenly over the window
  retry @ U(0,200ms)
  retry @ U(0,400ms)
```

A **retry budget** is a separate token bucket: max X retries per Y window across all callers. When the budget is empty, fail without retry. This prevents amplification when 80% of your traffic is currently failing.

## Why interviewers care

- **Production literacy** — you've operated services and know what AWS's blog post says.
- **Distributed systems judgment** — your retries don't *cause* the next outage.
- **Idempotency reasoning** — you know not all calls are safely retried.

## Common beginner confusion

- **"Just retry 3 times."** No jitter, no idempotency check, no budget, no backoff cap, no isRetryable. Five things missing.
- **"Linear backoff."** Adds load too slowly under transient failure; doesn't smooth properly. Exponential is the default.
- **"Jitter is optional cosmetics."** No — it prevents thundering herd. Mandatory for any client with N>1 caller.
- **"Decorrelated jitter is best."** It's better than `equal` and slightly better than `full` for tail latency, but harder to explain. `full` is the AWS default and a fine interview answer.
- **"Retry on 4xx because the API was wrong."** Almost never. 4xx = client bug, fix the client.

## Brute force approach

```js
// no jitter, no budget, will cause thundering herd
for (let i = 0; i < 3; i++) {
  try { return await fn(); } catch (e) { await sleep(1000); }
}
```

## Optimal approach

Exponential capped backoff with **full jitter** (AWS default), `isRetryable` discrimination, AbortSignal threading, retry budget for amplification control.

## Solution (JavaScript) — production-shape

```js
class RetryBudget {                                     // token bucket of retry capacity
  constructor({ maxTokens = 100, refillPerSec = 10 } = {}) {
    this.tokens = maxTokens;
    this.maxTokens = maxTokens;
    this.refillPerSec = refillPerSec;
    this.lastRefill = Date.now();
  }
  consume() {
    const now = Date.now();
    this.tokens = Math.min(this.maxTokens, this.tokens + (now - this.lastRefill) / 1000 * this.refillPerSec);
    this.lastRefill = now;
    if (this.tokens >= 1) { this.tokens -= 1; return true; }
    return false;
  }
}

const sleep = (ms, signal) => new Promise((res, rej) => {
  const t = setTimeout(res, ms);
  if (signal) signal.addEventListener('abort', () => { clearTimeout(t); rej(new Error('Aborted')); }, { once: true });
});

async function retry(fn, {
  attempts = 5, baseMs = 100, maxMs = 30_000,
  isRetryable = (e) => true,
  signal, budget,
} = {}) {
  let lastErr;
  for (let i = 0; i < attempts; i++) {
    if (signal?.aborted) throw new Error('Aborted');
    try { return await fn(i); }
    catch (e) {
      lastErr = e;
      if (!isRetryable(e) || i === attempts - 1) throw e;
      if (budget && !budget.consume()) { lastErr.budgetExhausted = true; throw lastErr; }
      const cap = Math.min(maxMs, baseMs * 2 ** i);
      const delay = Math.random() * cap;                 // full jitter (AWS)
      await sleep(delay, signal);
    }
  }
  throw lastErr;
}

// Usage
const budget = new RetryBudget({ maxTokens: 100, refillPerSec: 10 });
await retry(
  () => fetch(url).then(r => r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))),
  { attempts: 5, isRetryable: (e) => /HTTP 5\d\d|ETIMEDOUT|ECONNRESET/.test(e.message), budget, signal: ac.signal }
);
```

## Step-by-step dry run

`attempts=4, baseMs=100, maxMs=30s`. Failures at every attempt except last.

```
i=0  attempt → fail → cap=min(30000, 100*1)=100   → delay=U(0,100)=37ms → sleep
i=1  attempt → fail → cap=min(30000, 100*2)=200   → delay=U(0,200)=158ms → sleep
i=2  attempt → fail → cap=min(30000, 100*4)=400   → delay=U(0,400)=240ms → sleep
i=3  attempt → success → return result

Total wall time ≈ 4*op_latency + ~435ms
```

If `i=3` had failed and `attempts=4` exhausted → throw.

If 100 clients run in parallel, each rolls independent dice → loads at t=37, 80, 92, 240, 380, 444... not all at t=100/200/400 like no-jitter would.

## How to think aloud in the interview

> "Exponential capped at maxMs, full jitter (U(0, cap)). Inject isRetryable so I don't retry 4xx. Pair with idempotency keys if the op isn't safe. Add a shared retry budget — token bucket — so I can't amplify load when the dep is widely failing. Thread AbortSignal so a cancelled request doesn't sleep for 30 seconds. Outer wrap in a CircuitBreaker so when the dep is fully down I fail fast."

## Important takeaways

- **Full jitter, not none.** Mandatory.
- **isRetryable.** Don't retry caller errors.
- **maxMs cap.** Never unbounded.
- **Idempotency.** Either the op is idempotent or you have a key.
- **Retry budget.** Shared token bucket to prevent amplification.
- **AbortSignal.** Threaded throughout.
- **Pair with circuit breaker.** Retry + breaker, always together.

## Variants

- **Decorrelated jitter** — `sleep = U(baseMs, prevSleep*3)`; AWS-blog claims tighter tail.
- **Per-error backoff multiplier** — slow harder on rate-limit (429) than on connection reset.
- **Honor `Retry-After` header** — if the server tells you when to retry, use it.
- **Async generator version** — yields each attempt; caller can inspect/stop.

## Revision notes

```
retry(fn, attempts, baseMs, maxMs, isRetryable, budget, signal):
  loop i in [0, attempts):
    try: return await fn()
    catch: if !retryable || last: throw
           if !budget.consume(): throw
           cap = min(maxMs, baseMs*2^i)
           sleep U(0, cap)                  # full jitter
  
  full jitter > none (no herd)
  inject isRetryable (skip 4xx)
  retry budget = token bucket; prevents amplification
  thread AbortSignal in sleep
  pair with circuit breaker + idempotency
```
