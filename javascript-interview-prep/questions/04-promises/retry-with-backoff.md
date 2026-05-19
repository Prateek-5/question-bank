# Implement `retryWithBackoff(fn, opts)` — exponential backoff + jitter + cancellation

> **Difficulty:** Medium   |   **Time:** ~25 min   |   **Prereqs:** [`concepts/promises.md`](../../concepts/promises.md), [sleep.md](./sleep.md), [abortcontroller-fanout.md](./abortcontroller-fanout.md)
>
> **Source:** Canonical backend interview; inspired by `p-retry`, AWS SDK retry config, `axios-retry`.

---

## 1. Problem statement

**Signature**
```ts
function retryWithBackoff<T>(
  fn: (ctx: { attempt: number; signal?: AbortSignal }) => Promise<T>,
  opts?: {
    retries?: number;                // total = retries + 1 attempts
    base?: number;                   // ms; default 100
    factor?: number;                 // exponential factor; default 2
    maxDelay?: number;               // ms cap; default 30_000
    jitter?: 'full' | 'equal' | 'none'; // default 'full'
    shouldRetry?: (err: any, attempt: number) => boolean;
    signal?: AbortSignal;
  }
): Promise<T>;
```

**Input / Output examples**

| Setup                                                                  | Behaviour                                                  |
|------------------------------------------------------------------------|-------------------------------------------------------------|
| `fn` fails twice, succeeds on attempt 2 (`retries: 3, base: 100, factor: 2, jitter: 'none'`) | sleeps 100, 200; succeeds; total ~300 ms          |
| `fn` always fails (`retries: 2`)                                       | attempts 0, 1, 2; throws the **last** error                |
| `shouldRetry: (e) => e.code === 'ETIMEDOUT'`; `fn` throws non-timeout | throws immediately (no retry)                              |
| `signal.abort()` during a backoff sleep                                | rejects with `AbortError`                                  |
| `retries: 0`                                                           | runs once, no retry                                        |
| `jitter: 'full'`, 1000 clients failing together                        | retry times spread across `[0, delay]` — no thundering herd |

**Constraints**
- Exponential backoff: `delay = base * factor^attempt`, capped by `maxDelay`.
- Full jitter by default: `Math.random() * delay` (AWS recommendation).
- `shouldRetry(err)` filters non-transient errors (no retries for 4xx).
- `AbortSignal` checked at three points: loop top, threaded to `sleep`, threaded to `fn`.
- On exhaustion, throw the **last** error (preserve diagnostic context).
- Idempotency is the caller's responsibility — flag it.

---

## 2. Plain-English restatement

Wrap an async function in a retry loop. After each failure, sleep for an exponentially-growing delay with random jitter; then try again. Stop after a configurable number of attempts, or earlier if the error type tells you the operation isn't worth retrying (e.g., a `400 Bad Request`). Support cancellation through `AbortSignal` so a caller can bail out of a long retry chain. On final failure, throw the last error so the caller sees the real cause, not a generic "out of retries."

---

## 3. Why this matters in interviews

Retry-with-backoff is the **single most important production resilience pattern**. Every senior backend engineer should be able to whiteboard it in 5 minutes. The interviewer probes five things at once: (1) **exponential backoff formula** — `base * 2^attempt`, not linear; (2) **jitter** — randomize to avoid thundering herd when N clients retry simultaneously; (3) **retryability** — not every error is worth retrying (don't retry 4xx, retry 5xx + network); (4) **cancellation** via `AbortSignal`; (5) **give up cleanly** — surface the final error. Hit all five and you stand out. Get any wrong and you telegraph "I've copy-pasted retry code without thinking."

---

## 4. Mental model

The pattern is a **dice game with growing pauses**. Roll the dice (call `fn`). On failure, take a pause that doubles each round, then roll again. Add jitter to the pause so that when 100 dice-rollers fail in sync, they don't all retry on the same beat. The bouncer (`AbortSignal`) can throw you out at any time.

```
   attempt 0  ─▶  fn()  ─▶  fail   ─▶  sleep( random in [0, 100ms] )  ─▶
   attempt 1  ─▶  fn()  ─▶  fail   ─▶  sleep( random in [0, 200ms] )  ─▶
   attempt 2  ─▶  fn()  ─▶  fail   ─▶  sleep( random in [0, 400ms] )  ─▶
   attempt 3  ─▶  fn()  ─▶  fail   ─▶  isLastAttempt → throw lastErr
   
   At every step:
     - check signal.aborted → throw AbortError
     - check shouldRetry(err) → if false, throw immediately
     - sleep also accepts signal → cancellable mid-backoff
```

The exponential growth is what gives the downstream server time to recover. The jitter is what prevents synchronized retries from re-overloading it.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. With `base=100, factor=2`, what are the first four delay values (no jitter)? What about with full jitter?
> 2. Why is `Math.random() * delay` better than a fixed `delay` when 1000 clients fail simultaneously?
> 3. If the caller passes `signal.abort()` during a 30-second backoff sleep, should the retry function bail out immediately or wait for the sleep to finish?

---

## 6. Brute force — walked through

### Wrong attempt 1: fixed-delay retry

```js
async function bruteRetry(fn, n) {
  for (let i = 0; i < n; i++) {
    try { return await fn(); }
    catch (e) { if (i === n - 1) throw e; await sleep(100); }
  }
}
```

Works for trivial cases but: hammers servers with constant 100ms delays, no jitter (synchronized retries when many clients fail), retries 4xx (waste), no cancellation. Show this to dismiss and build up.

### Wrong attempt 2: linear backoff

```js
const delay = base * attempt;        // BUG: linear, not exponential
```

For `base=100`: delays are 100, 200, 300, 400. Adds load too slowly under transient failure; doesn't smooth properly. **Exponential is the default** for a reason — it adds backoff *aggressively* so the downstream gets time to recover.

### Wrong attempt 3: no jitter

```js
const delay = base * Math.pow(factor, attempt);   // BUG: no randomization
```

For `base=100, factor=2`: delays are 100, 200, 400, 800. Looks fine — until you have 1000 clients all failing at `t=0`. They all retry at `t=100`, all fail again, all retry at `t=200`, etc. **Synchronized retry → thundering herd → server stays down**. Full jitter (`Math.random() * delay`) spreads them across `[0, delay]`.

### Wrong attempt 4: no cancellation

```js
for (let attempt = 0; ; attempt++) {
  try { return await fn(); }
  catch (e) { await sleep(delay); }
}
```

Caller has no way to bail out. A long retry chain (15 attempts × 30s max delay = 7.5 minutes) is stuck. Always thread `AbortSignal` through.

### Wrong attempt 5: retry 4xx errors

```js
catch (e) { /* retry no matter what */ }
```

`400 Bad Request` is permanent — retrying wastes resources and may double-side-effect (double-charge). **Use a `shouldRetry` predicate** to filter.

---

## 7. The unlocking insight

> **The retry loop has five inputs (retries, base, factor, maxDelay, jitter), one predicate (shouldRetry), and one cancellation signal — all of which must be honored on every iteration. Exponential backoff with full jitter is the AWS-recommended default.**

The loop body has a precise structure:

1. **Check signal at loop top.** If aborted, throw `AbortError`. This catches cancellation between sleep and the next attempt.
2. **Try `fn({ attempt, signal })`.** Pass the signal in so `fn` can cancel its own work mid-attempt. Return on success.
3. **On error:** save as `lastErr`. Check `isLastAttempt` and `shouldRetry(err, attempt)`. If either is false, throw the error.
4. **Compute delay:**
   - Raw: `Math.min(maxDelay, base * factor^attempt)`.
   - Jittered: `Math.random() * raw` (full jitter).
5. **Sleep with signal threading.** `await sleep(delay, { signal })` — the sleep itself is cancellable.

The four jitter flavours, briefly:

| Jitter   | Formula                                       | Use when                                  |
|----------|-----------------------------------------------|--------------------------------------------|
| `none`   | `raw`                                         | testing; never in production               |
| `equal`  | `raw/2 + random(0, raw/2)`                    | half-randomized; conservative              |
| `full`   | `random(0, raw)`                              | **AWS default; recommended**               |
| decorrelated | `random(base, lastDelay * 3)`             | reduces head-of-line clustering            |

**The three integration points for `AbortSignal`** are critical to call out:

```
   1. loop top:    if (signal?.aborted) throw signal.reason
   2. sleep:       await sleep(delay, { signal })       ← cancellable
   3. inner call:  fn({ attempt, signal })              ← passes signal to fn
```

Miss any one and the caller can't cancel cleanly.

**Idempotency is the caller's responsibility.** Auto-retrying non-idempotent POSTs creates duplicates. The retry function doesn't know whether `fn` is idempotent — flag this in your monologue. Real systems combine retry with idempotency keys (see [`10-machine-coding-patterns/idempotency-wrapper.md`](../10-machine-coding-patterns/idempotency-wrapper.md)).

---

## 8. Solution (annotated)

```js
class AbortError extends Error {
  constructor(reason) {
    super('Aborted');
    this.name = 'AbortError';
    this.reason = reason;
  }
}

// Cancellable sleep — sibling helper
const sleep = (ms, { signal } = {}) =>
  new Promise((resolve, reject) => {
    if (signal?.aborted) return reject(signal.reason ?? new AbortError());
    const t = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort);
      resolve();
    }, ms);
    function onAbort() {
      clearTimeout(t);
      reject(signal.reason ?? new AbortError());
    }
    signal?.addEventListener('abort', onAbort, { once: true });
  });

async function retryWithBackoff(fn, opts = {}) {
  const {
    retries = 3,
    base = 100,
    factor = 2,
    maxDelay = 30_000,
    jitter = 'full',
    shouldRetry = () => true,
    signal,
  } = opts;

  let lastErr;
  for (let attempt = 0; attempt <= retries; attempt++) {     // step 1: total attempts = retries + 1
    if (signal?.aborted) {                                      // step 2: signal check at loop top
      throw signal.reason ?? new AbortError();
    }
    try {
      return await fn({ attempt, signal });                     // step 3: pass signal into fn
    } catch (err) {
      lastErr = err;                                            // step 4: preserve last error
      const isLastAttempt = attempt === retries;
      if (isLastAttempt || !shouldRetry(err, attempt)) {         // step 5: bail out conditions
        throw err;
      }
      const raw = Math.min(                                      // step 6: exponential, capped
        maxDelay,
        base * Math.pow(factor, attempt)
      );
      const delay =                                              // step 7: apply jitter
        jitter === 'full'  ? Math.random() * raw :
        jitter === 'equal' ? raw / 2 + Math.random() * raw / 2 :
        raw;
      await sleep(delay, { signal });                            // step 8: cancellable sleep
    }
  }
  throw lastErr;                                                 // unreachable; TS-friendly
}

// Example retryability predicate for HTTP
const isTransientHttp = (err) =>
  err?.code === 'ECONNRESET' ||
  err?.code === 'ETIMEDOUT' ||
  (err?.response?.status >= 500 && err.response.status < 600) ||
  err?.response?.status === 429;   // Too Many Requests
```

**Try it yourself**

```js
let calls = 0;
const flaky = async () => {
  calls++;
  if (calls < 3) throw new Error(`fail ${calls}`);
  return 'ok';
};

const result = await retryWithBackoff(flaky, {
  retries: 5, base: 100, factor: 2, jitter: 'none',
});
// calls=3, returns 'ok'; total wait ≈ 100 + 200 = 300 ms

// HTTP retry with predicate
await retryWithBackoff(
  ({ signal }) => fetch('/api/flaky', { signal }),
  { retries: 5, shouldRetry: isTransientHttp }
);

// Cancellation
const ctrl = new AbortController();
setTimeout(() => ctrl.abort(), 150);
try {
  await retryWithBackoff(neverSucceeds, {
    retries: 10, base: 100, factor: 2, jitter: 'none', signal: ctrl.signal,
  });
} catch (e) {
  console.log(e.name);   // 'AbortError'
}
```

---

## 9. Step-by-step dry run

Input:

```js
let calls = 0;
const flaky = async () => {
  calls++;
  if (calls < 3) throw new Error(`fail ${calls}`);
  return 'ok';
};
await retryWithBackoff(flaky, { retries: 5, base: 100, factor: 2, jitter: 'none' });
```

Values-first trace:

| `attempt` | Action                       | `calls` | `raw delay`           | `jitter='none' → delay` | Outcome                       |
|-----------|------------------------------|---------|------------------------|--------------------------|-------------------------------|
| 0         | `fn()` throws `'fail 1'`     | 1       | `min(30k, 100*1)=100` | `100`                    | `await sleep(100)`            |
| 1         | `fn()` throws `'fail 2'`     | 2       | `min(30k, 100*2)=200` | `200`                    | `await sleep(200)`            |
| 2         | `fn()` returns `'ok'`        | 3       | —                      | —                        | returns `'ok'`                |

Total wall time ≈ 300 ms (plus fn execution). With `jitter: 'full'`, delays would be `U(0,100)` and `U(0,200)` — same expected total but spread across the time window so multiple clients don't bunch up.

Abort during backoff:

| Time | Action                                          | Outcome                              |
|------|--------------------------------------------------|---------------------------------------|
| t=0  | `attempt=0`: `fn()` throws                       | sleep(100) starts                    |
| t=100| `attempt=1`: `fn()` throws                       | sleep(200) starts                    |
| t=150| external `ctrl.abort()` fires                    | sleep(200)'s onAbort fires → reject  |
| t=150| outer `await sleep(...)` throws `AbortError`     | bubbles out                          |

---

## 10. Common confusion + traps

1. **Linear backoff** (`base * attempt`) instead of exponential.
   Wrong formula. Use `base * factor^attempt`.

2. **No jitter** → thundering herd.
   Mandatory. Use `Math.random() * delay` (full jitter, AWS default).

3. **Retrying non-transient errors.**
   400, 401, 422, validation failures — these are permanent. Don't retry. Use `shouldRetry(err)` predicate.

4. **No cancellation** → caller can't abort a long retry chain.
   Thread `signal` to three places: loop top, `sleep`, `fn`.

5. **Generic "out of retries" error.**
   Loses the diagnostic root cause. Throw the **last** error.

6. **Retrying non-idempotent operations** without an idempotency key.
   Caller's responsibility. Flag explicitly. POSTs that create resources must use idempotency keys or NOT be auto-retried.

7. **First call inside the loop, not before.**
   Don't write `await fn()` before the loop "to avoid sleep on first call." The loop's `attempt=0` is the first call; sleep only happens after a failure (inside the catch). Cleanly handled by `for (attempt=0; attempt<=retries)`.

8. **`retries=0`** must run once with no retry.
   Loop condition `attempt <= retries` makes this work.

9. **Total timeout vs per-attempt timeout.**
   These are different. "Give up after 30s total" needs `AbortSignal.timeout(30_000)`. "Each attempt is 5s" needs `Promise.race([fn(), timer])` around the inner call.

10. **No `maxDelay` cap.**
    Without it, exponential growth gives 30+ minute backoffs after 15 retries. Cap with `Math.min(maxDelay, raw)`.

---

## 11. Senior follow-ups & variants

### Variant 1 — Decorrelated jitter (AWS recommendation for their services)

```js
let lastDelay = base;
// ...
lastDelay = Math.min(maxDelay, Math.random() * (lastDelay * 3));
```

Reduces head-of-line clustering better than full jitter for high-throughput services. Mention as a follow-up; full jitter is the safe default.

### Variant 2 — `AbortSignal.timeout(ms)` for total-timeout

```js
await retryWithBackoff(fn, {
  retries: 10,
  signal: AbortSignal.timeout(30_000),
});
```

One-liner total deadline. Node 17.3+ and modern browsers. The retry function doesn't need any other change.

### Variant 3 — Per-attempt timeout via `Promise.race`

```js
const timeLimit = (p, ms) => Promise.race([
  p,
  new Promise((_, rej) => setTimeout(() => rej(new Error('per-attempt timeout')), ms)),
]);

await retryWithBackoff(
  async ({ signal }) => timeLimit(fetch('/api', { signal }), 5_000),
  { retries: 3 }
);
```

Combines retry with per-attempt deadline.

### Variant 4 — Honor `Retry-After` header

```js
shouldRetry: (err) => err.response?.status === 429,
// inside the loop, before sleep:
const retryAfter = err.response?.headers.get('retry-after');
if (retryAfter) delay = Number(retryAfter) * 1000;
```

When the server tells you how long to wait, listen. Common with 429 (Too Many Requests).

### Variant 5 — `onRetry` hook for observability

```js
opts.onRetry?.({ attempt, error, delay });
```

Production-grade: emit a metric or log per retry. Helps debug "why is this endpoint slow today."

### Variant 6 — Combine with circuit breaker

```js
breaker.exec(() => retryWithBackoff(fn, opts));
```

Retry handles transient blips. Circuit breaker handles sustained failure. They compose. See [`10-machine-coding-patterns/circuit-breaker.md`](../10-machine-coding-patterns/circuit-breaker.md).

### Variant 7 — Generator-based for testability

```js
function* backoffSchedule({ base, factor, maxDelay, retries, jitter }) {
  for (let i = 0; i <= retries; i++) {
    yield Math.random() * Math.min(maxDelay, base * factor ** i);
  }
}

async function retry(fn, sched) {
  for (const delay of sched) {
    try { return await fn(); }
    catch (e) { await sleep(delay); }
  }
  throw new Error('out');
}
```

Decouples *policy* (schedule) from *driver* (loop). Easier to unit-test the schedule independently.

---

## 12. How to think aloud in the interview

> "Retry-with-backoff: loop from attempt 0 to retries. Try `fn`, return on success. On failure: check if it's the last attempt or non-retryable; if so, throw. Otherwise compute delay — `base * factor^attempt`, capped at maxDelay, then full-jittered with `Math.random() * raw`. Sleep, retry. Thread `AbortSignal` to three places: loop-top check, sleep, fn. On exhaustion, throw the last error to preserve diagnostic context. Idempotency is the caller's responsibility — flag it. For total-timeout, `AbortSignal.timeout(30_000)`; for per-attempt timeout, wrap fn in `Promise.race`. Composes with circuit breaker: retry handles blips, breaker handles sustained failure."

---

## 13. 60-second revision

> - **Loop:** `for (attempt = 0; attempt <= retries; attempt++)` — total = `retries + 1`.
> - **Exponential delay:** `Math.min(maxDelay, base * factor^attempt)`.
> - **Full jitter:** `Math.random() * delay` — **mandatory** to avoid thundering herd.
> - **`shouldRetry(err)`** — don't retry 4xx, validation, auth failures.
> - **`AbortSignal` at three points:** loop top, `sleep`, `fn`.
> - **Throw the last error** on exhaustion — preserve stack/code.
> - **Idempotency** is the caller's responsibility. Auto-retry only safe ops.
> - **Family:** `timeLimit` (per-attempt), `circuit-breaker` (composes), `idempotency-wrapper` (caller-side).
> - **Trap:** linear backoff; no jitter; retrying 4xx; generic "out of retries" error.

---

**Related:** [sleep.md](./sleep.md) · [abortcontroller-fanout.md](./abortcontroller-fanout.md) · [promise-time-limit.md](./promise-time-limit.md) · [promise-pool.md](./promise-pool.md) · [`10-machine-coding-patterns/circuit-breaker.md`](../10-machine-coding-patterns/circuit-breaker.md) · [`10-machine-coding-patterns/idempotency-wrapper.md`](../10-machine-coding-patterns/idempotency-wrapper.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
