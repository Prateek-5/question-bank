# Implement `sleep(ms)`

## Source
- LeetCode #2621 "Sleep": https://leetcode.com/problems/sleep/
- Canonical async-utility warm-up; appears as a pre-question on almost every promise round.

## Why this question matters in interviews
`sleep` looks trivial — "wrap `setTimeout` in a promise" — but it's the entry point the interviewer uses to assess your **promise mental model**. In 30 seconds they learn whether you know that (a) the `Promise` constructor executor runs **synchronously**, (b) `setTimeout` schedules a **macrotask** while `.then` schedules a **microtask**, (c) `resolve` can be called with any value (including another thenable), and (d) `await sleep(ms)` returns control to the event loop without blocking it. As a backend engineer you will use `sleep` in every retry-with-backoff, every poll loop, every test fixture that simulates latency. Botching it telegraphs "I haven't written async JS in a while" — exactly the impression you don't want.

## Concepts involved

### Syntax to lock in
```js
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
await sleep(100); // pauses the calling async function for ~100ms
```

### Runtime / engine behavior
- `new Promise(executor)` calls `executor` **synchronously and exactly once**. Anything you write outside the `setTimeout` callback runs before the function returns.
- `setTimeout(resolve, ms)` enqueues a macrotask. When it fires, `resolve()` is called, which schedules the `.then` continuation as a **microtask** drained at the end of the current task.
- `ms` of `0` does **not** mean "synchronous" — it means "next macrotask tick" (clamped to ~4ms in browsers for nested timers).
- `await` desugars to `.then` — so `await sleep(0)` defers the rest of the function to a microtask after the timer fires.

### Edge cases (interview traps)
1. **Negative or `NaN` ms** — `setTimeout` clamps negatives to `0`; `NaN` is treated as `0` in V8. Guard if you care: `Math.max(0, ms | 0)`.
2. **`ms` huge (> 2^31-1)** — Node treats anything > 24.8 days as `1` ms (signed-32-bit overflow). Cite this if asked about long-lived timers.
3. **Cancellation** — vanilla `sleep` is **uncancellable**. The timer fires regardless. For real backend use, support an `AbortSignal` (see Variants).
4. **Unhandled rejection** — `sleep` never rejects, so no risk here. But if you add `AbortSignal` support, rejecting on abort with a non-`Error` (like `'aborted'`) trips lint rules — always reject with an `Error` subclass.
5. **Drift** — `setTimeout(fn, 100)` does **not** guarantee firing at exactly 100ms. It guarantees *no earlier than* 100ms. Under event-loop pressure it can be much later.
6. **Top-level await** — `await sleep(100)` at module top-level works in ESM but not in CJS without an IIFE.

## Brute force approach
Block the thread with a `while (Date.now() - start < ms)` busy-loop. **Never do this.** It freezes the event loop, blocks every other timer, every I/O completion, every microtask. JavaScript is single-threaded; the entire point of `sleep` is to *yield* control. Mention this only to dismiss it — interviewers test whether you know not to do it.

## Optimal approach
Return a new `Promise` whose `resolve` is wired to `setTimeout`. One line. The work happens in the event loop, not on the call stack.

## Solution (JavaScript)

```js
/**
 * Pauses for at least `ms` milliseconds.
 * @param {number} ms
 * @param {{ signal?: AbortSignal }} [opts]
 * @returns {Promise<void>}
 */
function sleep(ms, { signal } = {}) {
  return new Promise((resolve, reject) => {
    // Fast-path: already aborted.
    if (signal?.aborted) {
      return reject(signal.reason ?? new DOMException('Aborted', 'AbortError'));
    }

    const timerId = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort);
      resolve();
    }, Math.max(0, ms));

    function onAbort() {
      clearTimeout(timerId);
      reject(signal.reason ?? new DOMException('Aborted', 'AbortError'));
    }

    signal?.addEventListener('abort', onAbort, { once: true });
  });
}

// Minimal one-liner (no cancellation):
// const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
```

## Step-by-step dry run

Input:
```js
console.log('a');
sleep(100).then(() => console.log('b'));
console.log('c');
```

Trace:
- **Sync phase:** `console.log('a')` prints `a`. Then `sleep(100)` runs — its executor runs synchronously: `setTimeout(resolve, 100)` schedules a timer; the `Promise` is returned in pending state. `.then(cb)` registers `cb` on the promise's fulfillment reactions. `console.log('c')` prints `c`.
- **Event loop:** call stack empties. Microtask queue empty. Wait ~100ms.
- **t≈100ms:** timers phase fires the callback → `resolve()` → promise becomes fulfilled → `.then` callback enqueued as a **microtask**.
- Microtask drains: `cb()` → `console.log('b')` prints `b`.

Output: `a`, `c`, `b`. The `c` printing before `b` is the whole point — the function did not block.

Now with abort:
```js
const ctrl = new AbortController();
const p = sleep(1000, { signal: ctrl.signal });
ctrl.abort();
// p rejects synchronously-from-microtask with AbortError.
```

## Important takeaways

**Syntax to memorize**
- `new Promise((resolve) => setTimeout(resolve, ms))` — burn this into muscle memory.
- `Math.max(0, ms)` guard for negatives.
- `signal?.aborted` short-circuit before scheduling.

**Patterns to reuse**
- The Promise-wrapping-timer pattern is reused in: `timeout(promise, ms)` (race vs sleep-then-reject), `retryWithBackoff` (sleep between attempts), `pollUntil(predicate, interval)`.
- AbortSignal integration is the same shape for `fetch`, `setTimeout`-promise wrappers, and async iterators.

**Common mistakes**
- Forgetting that the `Promise` executor is synchronous — candidates sometimes write `await new Promise(...)` thinking the executor is deferred.
- Using `Promise.resolve().then(() => setTimeout(...))` — adds a needless microtask without changing behavior.
- Returning `setTimeout(...)`'s return value (a Timeout object) instead of a Promise.
- Not removing the `abort` listener on success — small memory leak in long-lived signals.

**Related questions**
- `delay(ms, value)` — resolves with `value` after `ms`.
- `timeout(promise, ms)` — see `promise-time-limit.md`.
- `retry(fn, { retries, base })` — see `retry-with-backoff.md`.

## Variants

1. **`sleep(ms, value)`** — resolve with a value: `new Promise(r => setTimeout(() => r(value), ms))`. Useful for promise-pipeline tests.

2. **`sleepAbortable(ms, signal)`** — the version above. Production code in Node 18+ should prefer `setTimeout` from `node:timers/promises` which supports `{ signal }` natively: `import { setTimeout as sleep } from 'node:timers/promises'; await sleep(100, undefined, { signal });`.

3. **`sleepUntil(timestamp)`** — `sleep(timestamp - Date.now())`. Watch for negative diffs and clock skew if you care about wall-clock accuracy.

## Revision notes

> **sleep — 60 second recap**
> - `(ms) => new Promise(r => setTimeout(r, ms))` is the canonical one-liner.
> - Promise executor runs **synchronously**; timer callback runs as a macrotask, `.then` continuation as a microtask.
> - Vanilla `sleep` is **uncancellable** — use `AbortSignal` for production.
> - `ms <= 0` clamps to 0 (next-tick), not synchronous. `ms > 2^31-1` overflows in Node.
> - Never busy-wait (`while (Date.now()-s < ms)`) — blocks the entire single-threaded loop.
> - Node 18+ ships `node:timers/promises` `setTimeout(ms, value, { signal })` — use it.
> - **Trap:** thinking `await sleep(0)` is synchronous. It defers to the next macrotask + microtask drain.
> - Family: same skeleton powers `timeout`, `retry`, `pollUntil`.
