# Retry with exponential backoff, full jitter, and a retry budget

> **Difficulty:** Senior   |   **Time:** ~25 min   |   **Prereqs:** [`04-promises/retry-with-backoff.md`](../04-promises/retry-with-backoff.md), [circuit-breaker.md](./circuit-breaker.md), [idempotency-wrapper.md](./idempotency-wrapper.md)
>
> **Source:** AWS "Exponential Backoff And Jitter" (Marc Brooker, 2015). Asked at AWS, Stripe, Razorpay, Atlassian, Uber, Booking.

---

## 1. Problem statement

**Signature**
```ts
function retry<T>(fn: (attempt: number) => Promise<T>, opts?: {
  attempts?: number;
  baseMs?: number;
  maxMs?: number;
  isRetryable?(err): boolean;
  budget?: RetryBudget;
  signal?: AbortSignal;
}): Promise<T>;

class RetryBudget {
  constructor(opts?: { maxTokens?: number; refillPerSec?: number });
  consume(): boolean;
}
```

**Input / Output examples**

| Scenario                                          | Behaviour                                              |
|---------------------------------------------------|---------------------------------------------------------|
| Fails 2x, succeeds 3rd                            | Returns 3rd result; ~3 calls + 2 sleeps with jitter   |
| 4xx error                                          | With `isRetryable: e => !e.message.startsWith('HTTP 4')`, no retry |
| Budget exhausted                                  | Throws original error with `budgetExhausted: true`     |
| `signal.abort()` during sleep                      | sleep rejects; retry throws Aborted                    |
| All attempts fail                                  | Throws last error                                       |

**Constraints**
- **Full jitter** is mandatory (AWS default).
- `maxMs` caps backoff — never unbounded.
- `isRetryable` discriminates: 5xx/timeout/network reset YES; 4xx NO.
- `RetryBudget` is a shared token bucket — prevents amplification.
- Thread `AbortSignal` through `sleep`.

---

## 2. Plain-English restatement

When a call fails, wait a bit and retry — exponentially longer waits each time, randomized so 1000 clients don't all retry in lockstep. Cap the maximum wait. Don't retry caller errors (4xx). Share a "retry budget" across calls so a widely-failing dependency doesn't trigger 5× more load via retries.

---

## 3. Why this matters in interviews

Retry without jitter caused thundering herds that took down half the internet in the late 2000s. Senior interviewers want five things: (1) plain exponential bad — synchronizes herd; (2) full jitter is AWS default; (3) retry budget prevents amplification; (4) only idempotent ops OR idempotency keys; (5) pair with circuit breaker.

---

## 4. Mental model

```
   NO JITTER (synchronized herd):
   1000 clients fail at t=0
   all retry at +100ms   ← 1000 simultaneous hits
   all retry at +200ms   ← 1000 simultaneous hits
   all retry at +400ms

   FULL JITTER (AWS default — random in [0, cap)):
   1000 clients fail at t=0
   retry at U(0, 100ms)   ← spread evenly across 100ms window
   retry at U(0, 200ms)
   retry at U(0, 400ms)

   Exponential capped backoff:
   cap_i = min(maxMs, baseMs * 2^i)
   delay = Math.random() * cap_i        ← full jitter

   Retry budget (token bucket):
   capacity=100, refill=10/s.
   Each retry consumes 1 token.
   When empty, fail without retry → prevents N× amplification cascade.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why does plain exponential (no jitter) cause thundering herd?
> 2. Should you retry a `400 Bad Request`? A `500 Internal Server Error`?
> 3. If 10k clients each retry 5× when a dep fails, what's the multiplier on traffic?

---

## 6. Brute force — walked through

### Wrong attempt 1: retry 3× with fixed sleep
```js
for (let i = 0; i < 3; i++) {
  try { return await fn(); } catch { await sleep(1000); }
}
```
No jitter (herd), no isRetryable (retries 4xx), no maxMs, no budget. Five things missing.

### Wrong attempt 2: linear backoff
Doesn't smooth properly; doesn't relieve load fast enough. Exponential is default.

### Wrong attempt 3: retry 4xx because "API was wrong"
4xx = client bug, fix the client. Retry just amplifies.

---

## 7. The unlocking insight

> **Exponential capped backoff with full jitter `delay = random() * min(maxMs, baseMs * 2^i)`. Inject `isRetryable`. Add `RetryBudget` (shared token bucket) to prevent amplification. Thread `AbortSignal` through `sleep`. Pair with circuit breaker outside.**

Three properties:

1. **Full jitter** = `Math.random() * cap`.
2. **`isRetryable`** discriminates.
3. **`RetryBudget`** caps amplification under widespread failure.

---

## 8. Solution (annotated)

```js
class RetryBudget {
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
  isRetryable = () => true,
  signal, budget,
} = {}) {
  let lastErr;
  for (let i = 0; i < attempts; i++) {
    if (signal?.aborted) throw new Error('Aborted');
    try {
      return await fn(i);                                              // step 1: attempt
    } catch (e) {
      lastErr = e;
      if (!isRetryable(e) || i === attempts - 1) throw e;              // step 2: discriminate
      if (budget && !budget.consume()) {                                // step 3: budget gate
        lastErr.budgetExhausted = true;
        throw lastErr;
      }
      const cap = Math.min(maxMs, baseMs * 2 ** i);                     // step 4: exp + cap
      const delay = Math.random() * cap;                                 // step 5: FULL JITTER
      await sleep(delay, signal);
    }
  }
  throw lastErr;
}
```

**Try it yourself**

```js
const budget = new RetryBudget({ maxTokens: 100, refillPerSec: 10 });
const ac = new AbortController();

try {
  const data = await retry(
    () => fetch('https://api.example.com').then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    }),
    {
      attempts: 5,
      isRetryable: (e) => /HTTP 5\d\d|ETIMEDOUT|ECONNRESET/.test(e.message),
      budget,
      signal: ac.signal,
    }
  );
} catch (e) {
  if (e.budgetExhausted) console.log('Skipped retry — budget empty');
  throw e;
}
```

---

## 9. Step-by-step dry run

```
attempts=4, baseMs=100, maxMs=30000. Fails first 3 times, succeeds 4th.

i=0 fn() throws → isRetryable? yes. budget.consume()? yes.
     cap = min(30000, 100*1)=100. delay = U(0,100) = 37ms. sleep 37ms.
i=1 fn() throws → cap = min(30000, 200)=200. delay = U(0,200) = 158ms.
i=2 fn() throws → cap = 400. delay = U(0,400) = 240ms.
i=3 fn() SUCCEEDS → return result.

Total wall time ≈ 4×op_latency + ~435ms.

For 100 concurrent clients with INDEPENDENT random:
  retries spread across [0,100), [0,200), [0,400) windows.
  No spike at exactly +100, +200, +400.

Budget exhausted scenario:
  After many retries cluster-wide, budget.consume() returns false on next caller.
  retry throws original err with .budgetExhausted=true → caller falls back fast.
```

---

## 10. Common confusion + traps

1. **No jitter** — synchronized herd.
2. **Retry 4xx** — client bug, just amplifies.
3. **No `maxMs`** — runaway sleep destroys p99.
4. **No budget** — N callers × M retries → N×M amplification cascade.
5. **Retry non-idempotent ops** — second retry may double-charge. Use idempotency keys.
6. **Don't thread `AbortSignal`** — cancelled request still sleeps 30s.
7. **Per-call vs per-attempt timeout** — pick one; don't accidentally `attempts × perCall`.

---

## 11. Senior follow-ups & variants

### Variant 1 — Decorrelated jitter
`sleep = U(baseMs, prevSleep * 3)`. AWS blog claims tighter tail latency.

### Variant 2 — Per-error backoff multiplier
Slow harder on 429 (rate-limit) than on ECONNRESET. Honor `Retry-After` header.

### Variant 3 — Pair with circuit breaker
`breaker.exec(() => retry(fn))`. Retry inside; breaker contains amplification when dep is down.

### Variant 4 — Async generator
`for await (const attempt of retryStream(fn, opts))` — caller inspects each attempt.

### Variant 5 — Hedged requests
Fire backup request after `Pᴴ` time; cancel slow one. Tail-latency reduction at cost of 2× requests.

---

## 12. How to think aloud

> "Exponential capped at maxMs, FULL JITTER `Math.random() * cap` (AWS default — no synchronized herd). Inject `isRetryable` so I don't retry 4xx. Add a shared `RetryBudget` (token bucket) — prevents amplification when a dep is widely failing. Thread `AbortSignal` so cancelled requests don't sleep 30s. Pair with idempotency keys for non-safe verbs and a circuit breaker outside for fail-fast on dead deps. Trap: no jitter; retry 4xx; no maxMs; no budget. Five things together separate senior from mid."

---

## 13. 60-second revision

> - **Exponential cap:** `cap = min(maxMs, baseMs * 2^i)`.
> - **Full jitter:** `delay = Math.random() * cap` (AWS default).
> - **`isRetryable`** — skip 4xx; retry 5xx/timeout/reset.
> - **`RetryBudget`** (shared token bucket) — prevents amplification.
> - **`AbortSignal`** threaded through `sleep`.
> - **Pair:** idempotency key (non-safe verbs) + circuit breaker (outside).
> - **Variants:** decorrelated jitter; honor `Retry-After`; hedged requests.
> - **Trap:** no jitter; retry 4xx; no maxMs; no budget; non-idempotent ops.

---

**Related:** [`04-promises/retry-with-backoff.md`](../04-promises/retry-with-backoff.md) · [circuit-breaker.md](./circuit-breaker.md) · [idempotency-wrapper.md](./idempotency-wrapper.md) · [rate-limiter-token-bucket.md](./rate-limiter-token-bucket.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
