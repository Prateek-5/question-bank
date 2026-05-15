# Implement `retryWithBackoff(fn, options)`

## Source
- Canonical backend interview problem; inspired by `p-retry`, AWS SDK retry config, `axios-retry`.
- Pattern surfaces in every distributed system: HTTP retries, DB reconnects, queue consumers, idempotent job runners.

## Why this question matters in interviews
Retry-with-backoff is the **single most important production resilience pattern**. Every senior backend engineer should be able to whiteboard this in 5 minutes. The interviewer probes five things at once: (1) **exponential backoff formula** — `base * 2^attempt`, not linear; (2) **jitter** — randomize to avoid thundering herd when N clients retry simultaneously; (3) **retryability** — not every error is worth retrying (don't retry 4xx, retry 5xx + network); (4) **cancellation** via `AbortSignal`; (5) **give up cleanly** — surface the final error, not a generic "out of retries." Getting any of these wrong telegraphs "I've copy-pasted retry code without thinking about it." Hit all five and you stand out.

## Concepts involved

### Syntax to lock in
```js
async function retry(fn, { retries = 3, base = 100, factor = 2, jitter = 'full', signal, shouldRetry = () => true } = {}) {
  let lastErr;
  for (let attempt = 0; attempt <= retries; attempt++) {
    if (signal?.aborted) throw signal.reason ?? new Error('Aborted');
    try {
      return await fn({ attempt, signal });
    } catch (err) {
      lastErr = err;
      if (attempt === retries || !shouldRetry(err, attempt)) throw err;
      const delay = computeDelay(base, factor, attempt, jitter);
      await sleep(delay, { signal });
    }
  }
  throw lastErr;
}
```

### Runtime / engine behavior
- The retry loop is a **sequential** chain of `await fn()` — by design. Parallel retries would defeat the backoff (and hammer the server).
- Each iteration's `await sleep(...)` yields to the event loop, allowing other work to run between attempts.
- `AbortSignal` integration requires checking `signal?.aborted` at the **start of each attempt** AND threading the signal into `sleep` (so an in-flight backoff sleeps cancel) AND into `fn` (so the inner request cancels). Three integration points; miss any one and you've got a bug.
- Microtask hop on each `await` — for 1000 retries, that's 1000 microtasks. Negligible cost.

### Edge cases (interview traps)
1. **Exponential formula** — `delay = base * factor^attempt`. Common bug: `base * factor * attempt` (linear) or `base ^ attempt` (no `factor`). For `base=100, factor=2`: delays are 100, 200, 400, 800, 1600 ms. Lock this in.
2. **Jitter** — without it, N clients fail at the same time and retry at the same backoff → second wave of synchronized failure ("thundering herd"). Three flavours:
   - **Full jitter** (recommended): `Math.random() * delay`. Spreads retries across `[0, delay]`.
   - **Equal jitter**: `delay/2 + Math.random() * delay/2`. Half the variance.
   - **Decorrelated**: `Math.random() * (lastDelay * factor)`. Better for AWS-style services; less head-of-line clustering.
3. **Max delay cap** — `Math.min(delay, maxDelay)`. Prevents the backoff from growing to 30 minutes after 15 retries.
4. **Total timeout vs per-attempt timeout** — these are different! "Give up after 30s total" requires a wall-clock check; "each attempt times out at 5s" requires `timeLimit(fn, 5000)` around the inner call.
5. **Retryability predicate** — `shouldRetry(err, attempt)` returns false for non-transient errors (HTTP 4xx, validation errors, auth failures). Don't retry these — wastes resources and may double-charge users.
6. **Idempotency** — only retry **idempotent** operations. POSTs that create resources without an idempotency key must NOT be auto-retried — you'll create duplicates. Mention this is a *caller-side concern*, not solvable by the retry function alone.
7. **AbortSignal threading** — must be checked at loop start AND passed to `sleep` AND passed to `fn`. Three places.
8. **Last error** — on final failure, throw the **last** error encountered, not a generic "out of retries" — preserves the diagnostic context.
9. **`retries = 0`** — runs once, no retry. The loop condition `attempt <= retries` makes this work.
10. **First call inside loop, not before** — common bug to call `fn()` once before the loop "to avoid sleep on first call," then duplicate logic. Cleaner: loop from `attempt=0`, only sleep when `attempt > 0` (or after a failure).

## Brute force approach
Fixed delay, no jitter, no retryability check, no cancellation:
```js
async function bruteRetry(fn, n) {
  for (let i = 0; i < n; i++) {
    try { return await fn(); }
    catch (e) { if (i === n - 1) throw e; await sleep(100); }
  }
}
```
"Works" for simple cases but: hammers servers with constant 100ms delays, no jitter (thundering herd), retries 4xx (waste), no cancellation. Show this only to dismiss and build up.

## Optimal approach
Loop with exponential backoff + full jitter + capped max delay + retryability predicate + AbortSignal at three points. Throw the last error on exhaustion.

## Solution (JavaScript)

```js
class AbortError extends Error {
  constructor(reason) { super('Aborted'); this.name = 'AbortError'; this.reason = reason; }
}

const sleep = (ms, { signal } = {}) =>
  new Promise((resolve, reject) => {
    if (signal?.aborted) return reject(signal.reason ?? new AbortError());
    const t = setTimeout(() => { signal?.removeEventListener('abort', onAbort); resolve(); }, ms);
    function onAbort() { clearTimeout(t); reject(signal.reason ?? new AbortError()); }
    signal?.addEventListener('abort', onAbort, { once: true });
  });

/**
 * Retry an async function with exponential backoff + jitter.
 *
 * @template T
 * @param {(ctx: { attempt: number, signal?: AbortSignal }) => Promise<T>} fn
 * @param {object} [opts]
 * @param {number}  [opts.retries=3]      max additional attempts after the first (total = retries+1)
 * @param {number}  [opts.base=100]       base delay in ms
 * @param {number}  [opts.factor=2]       exponential factor
 * @param {number}  [opts.maxDelay=30000] cap on per-attempt delay
 * @param {'full'|'equal'|'none'} [opts.jitter='full']
 * @param {(err: unknown, attempt: number) => boolean} [opts.shouldRetry] retryability predicate
 * @param {AbortSignal} [opts.signal]     cancellation signal
 * @returns {Promise<T>}
 */
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
  for (let attempt = 0; attempt <= retries; attempt++) {
    if (signal?.aborted) throw signal.reason ?? new AbortError();
    try {
      return await fn({ attempt, signal });
    } catch (err) {
      lastErr = err;
      const isLastAttempt = attempt === retries;
      if (isLastAttempt || !shouldRetry(err, attempt)) throw err;

      // delay = base * factor^attempt, capped, then jittered.
      const raw = Math.min(maxDelay, base * Math.pow(factor, attempt));
      const delay =
        jitter === 'full'  ? Math.random() * raw :
        jitter === 'equal' ? raw / 2 + Math.random() * raw / 2 :
        raw;
      await sleep(delay, { signal });
    }
  }
  // Unreachable, but TS-friendly.
  throw lastErr;
}

// Example retryability predicate for HTTP:
const isTransientHttp = (err) =>
  err?.code === 'ECONNRESET' ||
  err?.code === 'ETIMEDOUT'  ||
  (err?.response && err.response.status >= 500 && err.response.status < 600) ||
  err?.response?.status === 429;
```

## Step-by-step dry run

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

Trace:
- `attempt=0`: `signal?.aborted` false. `await flaky()` → `calls=1`, throws `'fail 1'`. `isLastAttempt = (0===5)` false. `shouldRetry` returns true. `raw = min(30k, 100 * 2^0) = 100`. `jitter='none'` → delay=100. `await sleep(100)`. Continue.
- `attempt=1`: `calls=2`, throws `'fail 2'`. `raw = 100*2 = 200`. Sleep 200. Continue.
- `attempt=2`: `calls=3`, succeeds → returns `'ok'`. Function returns `'ok'`.

Total: 3 calls, ~300ms backoff. Without jitter the timing is deterministic — for prod, set `jitter: 'full'` so delay becomes `[0, 100], [0, 200]` etc.

Abort trace:
```js
const ctrl = new AbortController();
setTimeout(() => ctrl.abort(), 150);
await retryWithBackoff(neverSucceeds, {
  retries: 10, base: 100, factor: 2, jitter: 'none', signal: ctrl.signal
});
// Throws AbortError around t=150 — either during the in-flight sleep or at the next loop iteration's signal check.
```

Backoff exhaustion trace:
```js
await retryWithBackoff(() => Promise.reject(new Error('persistent fail')), { retries: 2 });
// attempt=0 → fail → sleep(100) →
// attempt=1 → fail → sleep(200) →
// attempt=2 → fail → isLastAttempt true → throw last error 'persistent fail'
```
The error thrown is the **last** error encountered, with its stack/code preserved.

## Important takeaways

**Syntax to memorize**
- Loop `for (let attempt = 0; attempt <= retries; attempt++)` — gives `retries+1` total calls.
- `Math.min(maxDelay, base * Math.pow(factor, attempt))` — capped exponential.
- Full jitter: `Math.random() * raw`.
- `signal?.aborted` short-circuit at the top of every iteration.
- Throw `lastErr` (not a generic message).

**Patterns to reuse**
- Combine with `timeLimit` to add per-attempt timeout: `await timeLimit(fn, perAttemptMs)({ attempt, signal })`.
- Combine with circuit breaker: skip retry if circuit is open.
- Compose with `asyncPool` for "retry every task with concurrency 10."

**Common mistakes**
- Linear backoff (`base * attempt`) instead of exponential — wrong formula.
- No jitter → thundering herd.
- Retrying non-transient errors (4xx, validation) — wastes resources, may double-side-effect.
- No cancellation → caller can't abort a long retry chain.
- Throwing a generic "out of retries" — loses the diagnostic root cause.
- Retrying non-idempotent operations without an idempotency key. **Caller's responsibility — flag it.**

**Related questions**
- `timeLimit` for per-attempt timeout.
- `asyncPool` for bounded concurrency over retried tasks.
- Circuit breaker (state machine: closed → open → half-open).
- Token-bucket rate limiter for the caller side.

## Variants

1. **Decorrelated jitter** — `delay = min(maxDelay, random(base, lastDelay * 3))`. AWS recommends this for their services; reduces head-of-line clustering.

2. **Linear with jitter** — `delay = (attempt * base) + random(0, jitter)`. Simpler; use when exponential is overkill (e.g., DB reconnect after a known-short outage).

3. **`AbortController.timeout` (Node 17.3+)** — `AbortSignal.timeout(30_000)` gives you a one-liner total-timeout signal: `retry(fn, { signal: AbortSignal.timeout(30_000) })`.

4. **Generator-based** — yield delay values from a generator, decoupling the *policy* (delays) from the *driver* (loop). Clean for testability.

5. **`onRetry` hook** — `opts.onRetry({ attempt, error, delay })` for logging/metrics. Production-grade.

6. **Retry-After header** — when the server tells you `Retry-After: 5`, honour it instead of computing your own backoff. Combine with `shouldRetry` access to `err.response.headers`.

## Revision notes

> **retryWithBackoff — 60 second recap**
> - Loop `for attempt in 0..retries` (total `retries+1` calls). Try → catch → sleep → retry.
> - **Exponential**: `delay = base * factor^attempt`, cap with `Math.min(maxDelay, ...)`.
> - **Jitter** (full): `Math.random() * delay`. Critical to avoid thundering herd.
> - **Retryability**: `shouldRetry(err)` — never retry 4xx, validation errors, auth failures.
> - **Cancellation**: check `signal?.aborted` at loop top, pass `signal` to `sleep` AND to `fn`. Three integration points.
> - **Final error**: throw the **last** error, preserve stack/code. Never throw a generic "out of retries."
> - **Idempotency** is the caller's responsibility — only auto-retry idempotent ops, or require idempotency keys.
> - Family: composes with `timeLimit` (per-attempt timeout), circuit breaker, token-bucket rate limiter.
> - **Trap:** linear backoff. **Trap:** no jitter. **Trap:** retrying 400s.
