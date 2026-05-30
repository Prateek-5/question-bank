# Implement `sleep(ms)` — the simplest promise wrapper

> **Difficulty:** Easy   |   **Time:** ~5 min   |   **Prereqs:** [`concepts/promises.md`](../../concepts/promises.md)
>
> **Source:** <a href="https://leetcode.com/problems/sleep/" target="_blank" rel="noopener noreferrer">LeetCode 2621 — Sleep</a>. Canonical async-utility warm-up.

---

## 1. Problem statement

**Signature**
```ts
function sleep(ms: number, opts?: { signal?: AbortSignal }): Promise<void>;
```

**Input / Output examples**

| Code                                                            | Behaviour                                       |
|-----------------------------------------------------------------|--------------------------------------------------|
| `await sleep(100)`                                              | Pauses for ~100ms (not less, may be more)        |
| `await sleep(0)`                                                | Yields to the next macrotask + microtask drain   |
| `await sleep(-5)`                                               | Same as `sleep(0)` — clamped                    |
| `await sleep(100, { signal })` after `signal.abort()`           | Rejects with `AbortError`                       |
| `console.log('a'); sleep(100).then(() => log('b')); log('c');` | Logs `a`, `c`, `b` (sync first, then timer)     |

**Constraints**
- Return a Promise that fulfills after at least `ms` milliseconds.
- Must NOT block the event loop (no busy-wait).
- Should support `AbortSignal` for cancellation in production.
- `ms <= 0` clamps to 0 (next-tick), not synchronous.

---

## 2. Plain-English restatement

Make a function that returns a Promise. Inside the executor, schedule a `setTimeout` whose callback calls `resolve`. That's it. Wrapping `setTimeout` in a Promise gives you `await sleep(100)` — pause this async function for 100ms without blocking the event loop.

In one line: `const sleep = (ms) => new Promise((r) => setTimeout(r, ms));`. The interviewer is checking whether you can write that one line and explain the runtime semantics around it.

---

## 3. Why this matters in interviews

`sleep` looks trivial but it's the entry point the interviewer uses to assess your **promise mental model**. In 30 seconds they learn whether you know that (a) the `Promise` constructor executor runs **synchronously**, (b) `setTimeout` schedules a **macrotask** while `.then` schedules a **microtask**, (c) `resolve` can be called with any value, and (d) `await sleep(ms)` returns control to the event loop without blocking it. You'll use `sleep` in every retry-with-backoff, every poll loop, every test fixture. Botching it telegraphs "I haven't written async JS in a while."

---

## 4. Mental model

A `Promise` is a state machine. Its executor runs synchronously *inside* `new Promise(...)`. We use the executor to schedule a `setTimeout` and capture `resolve`. When the timer fires, `resolve()` settles the promise, which schedules `.then` callbacks as microtasks.

```
   new Promise((resolve) => setTimeout(resolve, ms))
        │
        │  sync: executor runs, schedules timer (macrotask)
        │  sync: Promise returned (PENDING)
        │
        ▼
   ... event loop runs other work ...
        │
        │  t = ms: timer fires → resolve() → state = FULFILLED
        │           → schedule .then callbacks as microtasks
        ▼
   .then(cb) runs in next microtask drain
```

`ms = 0` is **not** synchronous — it's "next macrotask tick" (browsers clamp nested timers to ~4ms). `await sleep(0)` always defers at least one task + microtask hop.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `console.log('a'); sleep(0).then(() => log('b')); log('c');` — what's the output order?
> 2. Will `while (Date.now() - start < ms) {}` produce the same behavior as `sleep(ms)`? Why or why not?
> 3. How would you make `sleep` cancellable with `AbortController`?

---

## 6. Brute force — walked through

### Wrong attempt 1: busy-wait

```js
function sleep(ms) {
  const start = Date.now();
  while (Date.now() - start < ms) { /* spin */ }
}
```

**Never do this.** JS is single-threaded — the busy loop blocks the event loop. Every timer, every I/O callback, every microtask sits behind it. Mention only to dismiss; the interviewer is checking you know not to.

### Wrong attempt 2: forget to wrap in a Promise

```js
function sleep(ms) {
  setTimeout(() => {}, ms);
}
await sleep(100);   // BUG: returns undefined, await is a no-op
```

`setTimeout` returns a Timeout handle, not a Promise. `await undefined` is `Promise.resolve(undefined)` — completes on the next microtask, ignoring the timer.

### Wrong attempt 3: return the setTimeout return value

```js
const sleep = (ms) => setTimeout(() => {}, ms);
```

Same problem — returns the handle, not a Promise.

---

## 7. The unlocking insight

> **`new Promise((resolve) => setTimeout(resolve, ms))` — the executor runs synchronously, schedules the timer, returns a pending Promise. The timer's callback calls `resolve`, settling the promise; `await` resumes the calling async function.**

Four properties:

1. **Executor is synchronous.** Inside `new Promise((res) => { ... })`, the arrow function runs **immediately**. We use it to schedule the timer and let the constructor return a pending Promise.

2. **`setTimeout` is a macrotask.** When it fires (no earlier than `ms`), it runs as a task. `resolve()` then schedules the `.then` continuation as a **microtask**, drained at the end of the current task.

3. **`ms <= 0` is "next tick," not synchronous.** Browsers and Node clamp negative or fractional `ms` to 0; nested timers in browsers are further clamped to ~4ms after 4 levels of nesting.

4. **`AbortSignal` integration** adds production-grade cancellation. Three pieces: (a) fast-path on already-aborted; (b) abort listener that clears the timer and rejects; (c) cleanup the listener on resolve to avoid leaks.

---

## 8. Solution (annotated)

```js
function sleep(ms, { signal } = {}) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {                                       // step 1: fast-path
      return reject(signal.reason ?? new DOMException('Aborted', 'AbortError'));
    }
    const timerId = setTimeout(() => {                            // step 2: schedule timer
      signal?.removeEventListener('abort', onAbort);              //         cleanup listener on resolve
      resolve();
    }, Math.max(0, ms));                                          //         clamp negatives
    function onAbort() {
      clearTimeout(timerId);                                       // step 3: cancel timer on abort
      reject(signal.reason ?? new DOMException('Aborted', 'AbortError'));
    }
    signal?.addEventListener('abort', onAbort, { once: true });   // step 4: listen for abort
  });
}

// Minimal one-liner (no cancellation)
const sleepMin = (ms) => new Promise((r) => setTimeout(r, ms));
```

**Try it yourself**

```js
console.log('a');
sleep(100).then(() => console.log('b'));
console.log('c');
// a, c, b

// Cancellation
const ctrl = new AbortController();
const p = sleep(1000, { signal: ctrl.signal });
ctrl.abort();
try { await p; } catch (e) { console.log(e.name); }  // 'AbortError'

// Node 18+ has node:timers/promises with native AbortSignal support:
// import { setTimeout as sleep } from 'node:timers/promises';
// await sleep(100, undefined, { signal });
```

---

## 9. Step-by-step dry run

```js
console.log('a');
sleep(100).then(() => console.log('b'));
console.log('c');
```

Values-first trace:

| Phase     | Event                                            | Output  |
|-----------|---------------------------------------------------|---------|
| sync      | `console.log('a')`                                | `a`     |
| sync      | `sleep(100)`: executor runs, schedules setTimeout | —       |
| sync      | `.then(cb)`: registers cb on pending promise      | —       |
| sync      | `console.log('c')`                                | `c`     |
| event loop| stack empties; wait                              | —       |
| t≈100ms   | timer fires → resolve() → schedules cb microtask | —       |
| microtask | cb runs → `console.log('b')`                      | `b`     |

`c` prints before `b` — the function did not block.

---

## 10. Common confusion + traps

1. **Busy-wait blocks the event loop.** Single-threaded JS — `while (...)` freezes everything until it ends. Never use.
2. **`Promise` executor is synchronous.** It runs immediately during `new Promise(...)`. Don't think it's deferred.
3. **`sleep(0)` is not synchronous.** It's "next macrotask + microtask drain." Browsers clamp nested timers to ~4ms.
4. **`ms > 2^31 - 1`** overflows in Node (treated as `1ms`). Don't use for very long timers; use `setInterval` or schedule chained shorter timers.
5. **`setTimeout` doesn't fire at exactly `ms`.** It fires *no earlier than* `ms`. Under event-loop pressure it can be much later.
6. **`AbortSignal` listener leak.** If you forget `removeEventListener` in the success path, long-lived signals retain stale listeners.
7. **Top-level await in CJS.** `await sleep(...)` at module top-level works in ESM but not in CJS without an IIFE.
8. **Reject with a real Error.** Don't `reject('aborted')` (string) — lint rules and stack traces want `Error` subclasses. `DOMException('Aborted', 'AbortError')` or a custom AbortError.

---

## 11. Senior follow-ups & variants

### Variant 1 — `sleep(ms, value)`

Resolve with a value (useful in test fixtures):

```js
const sleep = (ms, value) => new Promise((r) => setTimeout(() => r(value), ms));
await sleep(100, 'done');   // 'done'
```

### Variant 2 — Native Node 18+

```js
import { setTimeout as sleep } from 'node:timers/promises';
await sleep(100, undefined, { signal });
```

Built-in cancellation, no manual wrapper needed.

### Variant 3 — `sleepUntil(timestamp)`

```js
const sleepUntil = (ts) => sleep(Math.max(0, ts - Date.now()));
```

Wait until wall-clock time. Beware clock skew / DST changes.

### Variant 4 — Composes with retry, timeout, poll

```js
// retry: see retry-with-backoff.md
async function retry(fn, n) {
  for (let i = 0; i < n; i++) {
    try { return await fn(); } catch (e) { await sleep(100 * 2 ** i); }
  }
}

// timeout via race
const timeout = (p, ms) => Promise.race([p, sleep(ms).then(() => { throw new Error('timeout'); })]);

// poll
async function pollUntil(pred, intervalMs) {
  while (!await pred()) await sleep(intervalMs);
}
```

`sleep` is the substrate for almost every time-aware async utility.

---

## 12. How to think aloud in the interview

> "One line: `(ms) => new Promise(r => setTimeout(r, ms))`. The executor runs synchronously, schedules the timer, returns a pending Promise. When the timer fires, `resolve()` settles it; `.then` callbacks run as microtasks. Never busy-wait — single-threaded JS, the loop freezes. `ms = 0` is not synchronous, it's next-tick. For production, add AbortSignal: fast-path on already-aborted, abort listener that clears the timer and rejects, cleanup the listener on resolve. Node 18+ has it built-in via `node:timers/promises`."

---

## 13. 60-second revision

> - **One line:** `(ms) => new Promise(r => setTimeout(r, ms))`.
> - **Executor runs synchronously**; timer callback is a macrotask; `.then` continuation is a microtask.
> - **Never busy-wait** — single-threaded JS, the loop blocks.
> - **`ms <= 0`** clamps to 0 (next-tick). **`ms > 2^31`** overflows in Node.
> - **Cancellation:** AbortSignal — fast-path on already-aborted, abort listener clears timer and rejects, cleanup on resolve.
> - **Node 18+:** `import { setTimeout as sleep } from 'node:timers/promises'`.
> - **Family:** substrate for `timeout`, `retry`, `poll`, `delay`.
> - **Trap:** thinking `sleep(0)` is synchronous; forgetting AbortSignal cleanup; rejecting with a string instead of Error.

---

**Related:** [retry-with-backoff.md](./retry-with-backoff.md) · [promise-time-limit.md](./promise-time-limit.md) · [abortcontroller-fanout.md](./abortcontroller-fanout.md) · [promise-race-polyfill.md](./promise-race-polyfill.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md), [`05-event-loop/microtask-macrotask-order.md`](../05-event-loop/microtask-macrotask-order.md)
