# Implement `timeLimit(fn, t)` — Promise with Timeout

## Source
- LeetCode #2637 "Promise Time Limit": https://leetcode.com/problems/promise-time-limit/
- Canonical: `Promise.race` against a timeout — used in every HTTP client (axios, got, undici).

## Why this question matters in interviews
Every production backend wraps external calls with a timeout. Senior engineers are expected to know two things cold: (1) **`Promise.race` is the primitive** — race the real work against a `sleep(t).then(reject)`; (2) **a timed-out promise keeps running** — the timer rejecting the race does *not* cancel the original work. The latter is the subtle one — interviewers grade harshly because if you don't know it you'll write code that leaks file handles, DB connections, and pending HTTP requests after a "timeout." The proper fix involves `AbortController`/`AbortSignal`, which doubles as a great follow-up.

## Concepts involved

### Syntax to lock in
```js
const limited = timeLimit(fn, 100);
await limited(...args); // resolves if fn finishes in 100ms, else rejects 'Time Limit Exceeded'.

function timeLimit(fn, t) {
  return async function (...args) {
    return Promise.race([
      fn.apply(this, args),
      new Promise((_, reject) =>
        setTimeout(() => reject('Time Limit Exceeded'), t)
      ),
    ]);
  };
}
```

### Runtime / engine behavior
- `Promise.race([a, b])` settles with whichever of `a` or `b` settles first — resolve **or** reject. It does **not** cancel the loser; the loser keeps running and its eventual settlement is discarded.
- The timer rejection is scheduled as a macrotask at `t=t`. If `fn` resolves at `t=t-1`, the race resolves first and the timer fires harmlessly later (no observable effect, but the timer is **not** auto-cleared).
- Best practice: `clearTimeout` the timer when `fn` wins, to avoid keeping the event loop alive on graceful shutdown (Node will keep running until all timers complete or are cleared).

### Edge cases (interview traps)
1. **`fn` throws synchronously** — `fn.apply(this, args)` throws before returning a promise. Without `async`/try-catch wrapping, the wrapper itself throws synchronously rather than returning a rejected promise. The `async function` wrapper above auto-converts sync throws to rejections. If you write a non-async wrapper, wrap in `try/catch` or use `Promise.resolve().then(() => fn.apply(this, args))`.
2. **`fn` returns a non-promise** — fine, `Promise.race` coerces it via `Promise.resolve`.
3. **Timer not cleared on success** — keeps the event loop alive. Memory leak in long-lived servers if you create thousands of such wrappers.
4. **No cancellation of the loser** — the original `fn` keeps running. For `fetch` you need to pass an `AbortSignal` and `abort()` on timeout.
5. **Negative `t`** — `setTimeout` clamps to 0; the race basically rejects on the next tick. Document or guard.
6. **`t === 0`** — same as above: rejects on the next tick *unless* `fn` resolves synchronously-from-microtask first. Microtasks drain before macrotasks, so a `Promise.resolve(5)`-returning `fn` will actually win the race against a 0ms timer. Subtle but worth knowing.
7. **Rejection reason** — LeetCode wants the string `'Time Limit Exceeded'`. In production, reject with a `TimeoutError` class so callers can `instanceof`-check.

## Brute force approach
Use `setTimeout` to set a flag and check it after `fn` resolves. Bad: requires polling, can't reject early, doesn't compose. The interviewer will guide you to `Promise.race` within 60 seconds — go there immediately.

## Optimal approach
`Promise.race` between `fn(...args)` and a timeout-promise that rejects. Wrap in `async` so sync `throw`s become rejections. Clear the timer on settle.

## Solution (JavaScript)

```js
class TimeoutError extends Error {
  constructor(ms) {
    super(`Time Limit Exceeded (${ms}ms)`);
    this.name = 'TimeoutError';
  }
}

/**
 * Returns a wrapped version of `fn` that rejects if it takes longer than `t` ms.
 * Note: the underlying `fn` is NOT cancelled — it keeps running. Use AbortController for real cancellation.
 *
 * @param {Function} fn  async or sync function returning a Promise
 * @param {number} t  timeout in ms
 * @returns {Function}
 */
function timeLimit(fn, t) {
  return async function (...args) {
    let timerId;
    const timeout = new Promise((_, reject) => {
      timerId = setTimeout(() => reject(new TimeoutError(t)), t);
    });

    try {
      // Promise.resolve wraps sync return values AND coerces thenables.
      // `async function` already converts sync throws to rejections.
      return await Promise.race([fn.apply(this, args), timeout]);
    } finally {
      clearTimeout(timerId); // prevent event loop from being held open
    }
  };
}

// LeetCode-string-shape variant:
const timeLimitLC = (fn, t) => async (...args) =>
  Promise.race([
    fn(...args),
    new Promise((_, rej) => setTimeout(() => rej('Time Limit Exceeded'), t)),
  ]);
```

### Production version with cancellation

```js
function timeLimitWithAbort(fn, t) {
  return async function (...args) {
    const ctrl = new AbortController();
    const timerId = setTimeout(() => ctrl.abort(new TimeoutError(t)), t);
    try {
      // fn is expected to accept { signal } as its last arg and honour it.
      return await fn.apply(this, [...args, { signal: ctrl.signal }]);
    } finally {
      clearTimeout(timerId);
    }
  };
}
```

## Step-by-step dry run

Input:
```js
const slow = (x) => new Promise((r) => setTimeout(() => r(x * 2), 100));
const limited = timeLimit(slow, 50);
limited(10).then(console.log, (e) => console.log('err:', e.message));
```

Trace:
- `t=0`: `limited(10)` invoked. Async wrapper starts. `Promise.race` is called with `[slow(10), timeout]`. `slow(10)` schedules a 100ms timer; `timeout` schedules a 50ms timer. Both promises are pending. The `await` suspends.
- `t=50`: timeout's timer fires → `reject(new TimeoutError(50))`. `Promise.race` rejects with TimeoutError. The `await` throws.
- Microtask: `finally` runs → `clearTimeout(timerId)` (the 50ms one — already fired, harmless). The async function's promise rejects with TimeoutError.
- `.then`'s rejection handler runs → prints `err: Time Limit Exceeded (50ms)`.
- `t=100`: `slow(10)`'s timer **still fires**. `resolve(20)` runs on the inner promise. Nobody is listening — no observable effect, no unhandled-rejection warning (it resolved, not rejected). But the underlying work happened — if `slow` had been a real HTTP request, the response would have been received and discarded.

Now happy path:
```js
const fast = (x) => Promise.resolve(x * 2);
const limited = timeLimit(fast, 50);
limited(10).then(console.log);
```
- `t=0`: `fast(10)` returns `Promise.resolve(20)` immediately (fulfilled). `Promise.race` settles with `20` in the next microtask (before the 50ms timer fires). `finally` clears the timer. Prints `20`.

## Important takeaways

**Syntax to memorize**
- `Promise.race([work, timeoutPromise])` — the whole pattern.
- `async function` wrapper to convert sync throws to rejections.
- `clearTimeout` in `finally` — always.

**Patterns to reuse**
- Same skeleton powers `retry(fn, { perAttemptTimeout })` — wrap each attempt with `timeLimit`.
- Cancellation pattern: bind a fresh `AbortController` per call, abort it on timeout, pass `signal` to inner work.

**Common mistakes**
- Forgetting `clearTimeout` — keeps the Node process alive until the timer fires.
- Believing timeout cancels the inner work. It does not. Articulate this — interviewer will probe.
- Using `setTimeout(() => reject(...))` outside a Promise — that's just an unhandled error.
- Returning the race result without `await` — works, but you lose the `finally` cleanup opportunity. Always `await` so you can clear the timer.

**Related questions**
- `retry(fn, opts)` with per-attempt timeout (see `retry-with-backoff.md`).
- Cancellable fetch via `AbortController` — same primitive.
- Circuit breaker — counts timeouts as failures.

## Variants

1. **First-class cancellation** — accept a `signal` arg in the wrapper, abort on timeout *and* pass it down so the inner work bails. Production-grade.

2. **Per-call timeout override** — `timeLimit(fn, defaultT)` returns a wrapper that accepts `{ timeout }` as the last arg to override `defaultT`. Useful when one call site needs a longer leash.

3. **Soft vs hard timeout** — resolve with a fallback value on timeout instead of rejecting: `Promise.race([fn(...args), sleep(t).then(() => fallback)])`. Pattern for caches where a stale value is better than no value.

## Revision notes

> **timeLimit — 60 second recap**
> - `Promise.race([fn(...args), timeoutPromise])` — done.
> - Timeout promise: `new Promise((_, rej) => setTimeout(() => rej(err), t))`.
> - **Critical:** the loser is NOT cancelled — `fn` keeps running. For real cancellation, use `AbortController` and pass `signal` to `fn`.
> - `async function` wrapper auto-converts sync `throw` in `fn` to a rejection.
> - **Always** `clearTimeout` in `finally` — otherwise the event loop stays alive in Node.
> - LeetCode wants the literal string `'Time Limit Exceeded'`. Production wants a `TimeoutError` class.
> - Family: same race skeleton powers `firstSuccessful`, `softTimeout`, `staleWhileRevalidate`.
> - **Trap:** assuming timeout cancels the underlying HTTP/DB call. It does not.
