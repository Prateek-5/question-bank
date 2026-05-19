# Implement `timeLimit(fn, ms)` — Promise + timeout via race

> **Difficulty:** Easy-Medium   |   **Time:** ~15 min   |   **Prereqs:** [promise-race-polyfill.md](./promise-race-polyfill.md), [sleep.md](./sleep.md)
>
> **Source:** [LeetCode 2637 — Promise Time Limit](https://leetcode.com/problems/promise-time-limit/); the standard pattern in every HTTP client.

---

## 1. Problem statement

**Signature**
```ts
function timeLimit<F extends (...args: any[]) => Promise<any>>(fn: F, t: number): F;
```

**Input / Output examples**

| Setup                                                                | Behaviour                                              |
|----------------------------------------------------------------------|---------------------------------------------------------|
| `timeLimit(fast, 100)` where `fast` resolves in 20ms                | resolves with `fast`'s value at t≈20                   |
| `timeLimit(slow, 50)` where `slow` resolves in 100ms                | rejects at t=50 with `'Time Limit Exceeded'`           |
| `timeLimit(fn, 0)`                                                    | `setTimeout(0)` rejects on next macrotask              |
| Underlying `slow` keeps running after rejection                       | timer wins the race, but `slow`'s work continues       |
| With AbortController integration (production)                         | underlying request is actually cancelled               |

**Constraints**
- Race the work against a `setTimeout`-rejecter.
- The **loser is not cancelled** — for real cancellation, integrate `AbortController`.
- Wrap in `async` to convert sync throws into rejections.
- **Always `clearTimeout` in `finally`** — otherwise the event loop stays alive.

---

## 2. Plain-English restatement

Wrap an async function with a deadline. If `fn` finishes within `ms` milliseconds, resolve with its value; otherwise reject with a timeout error. The implementation is `Promise.race([fn(...args), sleep(ms).then(reject)])` — but with the production caveat that the timer rejecting the race does **not** cancel the underlying work. For that, you need `AbortController`.

---

## 3. Why this matters in interviews

Every production backend wraps external calls with a timeout. Senior engineers are expected to know two things cold: (1) **`Promise.race` is the primitive** — race the real work against a `sleep(t).then(reject)`; (2) **a timed-out promise keeps running** — the timer rejecting the race does *not* cancel the original work. The second is the subtle one — interviewers grade harshly because not knowing it means writing code that leaks file handles, DB connections, and pending HTTP requests after a "timeout." The proper fix involves `AbortController`/`AbortSignal`, which doubles as a great follow-up.

---

## 4. Mental model

`Promise.race` between the real work and a timer-rejecter. Whichever settles first wins. The loser keeps running — its eventual settlement is discarded.

```
   timeLimit(fn, t)(...args)
        │
        ├──▶ Promise.race([
        │       fn(...args),                    ← real work
        │       sleep(t).then(reject)           ← timer
        │    ])
        │
        ├── fn finishes first   →  resolves with value, timer fires harmlessly later
        └── timer finishes first →  rejects with TimeoutError, fn keeps running (!)
```

**Key warning:** `Promise.race` doesn't cancel the loser. For HTTP, this means the response still arrives, body still streams, connection pool still holds the socket. Real cancellation needs `AbortController` threaded through to the underlying `fetch`/DB call.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If `fn` is `() => fetch('/slow')` and the timeout fires, does the actual HTTP request cancel?
> 2. Why is `clearTimeout` in `finally` important even when the timer hasn't won?
> 3. If `t = 0`, can `fn` ever win? (Hint: think microtasks vs macrotasks.)

---

## 6. Brute force — walked through

### Wrong attempt 1: poll a flag

```js
function timeLimit(fn, t) {
  return async (...args) => {
    let timedOut = false;
    setTimeout(() => { timedOut = true; }, t);
    const result = await fn(...args);
    if (timedOut) throw new Error('timeout');
    return result;
  };
}
```

**Wrong** — `await fn(...args)` waits for `fn` to complete *anyway*, then checks the flag. The timeout doesn't actually reject early. If `fn` takes 10s and `t=100ms`, the caller waits 10s.

### Wrong attempt 2: forget to clear the timer

```js
function timeLimit(fn, t) {
  return async (...args) =>
    Promise.race([
      fn(...args),
      new Promise((_, rej) => setTimeout(() => rej('TLE'), t)),
    ]);
}
```

Works but **keeps the timer alive** even on success. Node keeps running until all timers fire or are cleared — graceful shutdown is delayed. In a long-running server with thousands of timeLimited calls, this leaks until each timer naturally fires.

### Wrong attempt 3: `Promise.race` thinking it cancels

```js
const result = await Promise.race([fetch(url), sleep(5000).then(() => { throw new Error('timeout') })]);
// If timeout wins, fetch keeps streaming bytes. Connection pool exhausted.
```

A "timed out" fetch still completes. The socket stays open, the response body buffers in memory, the connection counts against your pool's concurrency limit. This is the resource-leak bug `AbortController` exists to fix.

---

## 7. The unlocking insight

> **`Promise.race([work, timer])` wins on first settle. Wrap in `async` for sync-throw safety. Clear the timer in `finally` for cleanup. For real cancellation, thread an `AbortController.signal` into `fn` and abort on timeout.**

The skeleton:

```js
function timeLimit(fn, t) {
  return async function (...args) {
    let timerId;
    const timeout = new Promise((_, reject) => {
      timerId = setTimeout(() => reject(new TimeoutError(t)), t);
    });
    try {
      return await Promise.race([fn.apply(this, args), timeout]);
    } finally {
      clearTimeout(timerId);
    }
  };
}
```

Three properties:

1. **`async function` wrapper** — converts sync throws inside `fn` into rejections of the returned promise. Without it, `fn(...args)` that throws synchronously crashes the wrapper instead of returning a rejected promise.

2. **`Promise.race`** — first settle wins. If `fn` resolves at t=20ms (microtask), it beats the 50ms macrotask timer. Microtasks always drain before macrotasks — so even `t=0` is beatable if `fn` returns `Promise.resolve(...)`.

3. **`clearTimeout` in `finally`** — runs whether the race resolves or rejects, ensures the timer doesn't keep the event loop alive after `fn` wins.

**The cancellation caveat** is the senior-bar talking point. State explicitly: "the timer rejecting the race doesn't cancel `fn`'s underlying work — for that, pass an `AbortSignal` into `fn` and abort on timeout."

---

## 8. Solution (annotated)

```js
class TimeoutError extends Error {
  constructor(ms) {
    super(`Time Limit Exceeded (${ms}ms)`);
    this.name = 'TimeoutError';
  }
}

function timeLimit(fn, t) {
  return async function (...args) {                            // step 1: async wrapper for sync-throw safety
    let timerId;
    const timeout = new Promise((_, reject) => {                // step 2: timer rejection promise
      timerId = setTimeout(() => reject(new TimeoutError(t)), t);
    });
    try {
      return await Promise.race([fn.apply(this, args), timeout]); // step 3: race
    } finally {
      clearTimeout(timerId);                                     // step 4: always clean up
    }
  };
}

// LeetCode shape (string reason)
const timeLimitLC = (fn, t) => async (...args) =>
  Promise.race([
    fn(...args),
    new Promise((_, rej) => setTimeout(() => rej('Time Limit Exceeded'), t)),
  ]);

// Production: with cancellation
function timeLimitWithAbort(fn, t) {
  return async function (...args) {
    const ctrl = new AbortController();
    const timerId = setTimeout(() => ctrl.abort(new TimeoutError(t)), t);
    try {
      // fn is expected to honor signal (e.g., fetch with {signal})
      return await fn.apply(this, [...args, { signal: ctrl.signal }]);
    } finally {
      clearTimeout(timerId);
    }
  };
}
```

**Try it yourself**

```js
const sleep = (ms, v) => new Promise((r) => setTimeout(() => r(v), ms));

const fast = (x) => sleep(20, x * 2);
const slow = (x) => sleep(100, x * 2);

const limFast = timeLimit(fast, 50);
const limSlow = timeLimit(slow, 50);

await limFast(10);              // 20 — finishes before timeout
try { await limSlow(10); }      // rejects at t=50
catch (e) { console.log(e.message); }   // 'Time Limit Exceeded (50ms)'

// With cancellation (production)
async function fetchSlow({ signal }) {
  const res = await fetch('/api/slow', { signal });
  return res.json();
}
const limited = timeLimitWithAbort(fetchSlow, 2000);
try { await limited(); }
catch (e) { console.log(e.name); }   // 'AbortError' or 'TimeoutError'
```

---

## 9. Step-by-step dry run

Input: `slow` resolves in 100ms, `t=50`:

```js
const slow = (x) => new Promise((r) => setTimeout(() => r(x * 2), 100));
const limited = timeLimit(slow, 50);
limited(10).then(console.log, (e) => console.log('err:', e.message));
```

Values-first trace:

| Time (ms) | Event                                                              | Outcome                            |
|-----------|--------------------------------------------------------------------|-------------------------------------|
| 0         | `limited(10)` runs; race starts; `slow` schedules 100ms timer; `timeout` schedules 50ms timer | both pending |
| 50        | timer fires → `reject(TimeoutError(50))`                            | race rejects with TimeoutError      |
| 50+µ      | `finally` runs `clearTimeout` (50ms timer already fired, no-op)    |                                     |
| 50+µ      | `.then`'s rejection handler logs `err: Time Limit Exceeded (50ms)` |                                     |
| 100       | `slow`'s timer fires → `resolve(20)`                                | nobody listening; result discarded |

The `slow` work completed at t=100 — but nobody saw the result. If `slow` were `fetch`, the response arrived (using bandwidth) and was discarded.

Happy path:

```js
const fast = (x) => Promise.resolve(x * 2);
await timeLimit(fast, 50)(10);   // 20, immediately
```

| Step | Event                                                       | Outcome     |
|------|-------------------------------------------------------------|--------------|
| 1    | `fast(10)` returns already-fulfilled `Promise.resolve(20)` | —            |
| 2    | `Promise.race` settles on next microtask with `20`         | race fulfills |
| 3    | `await` returns `20`                                        | —            |
| 4    | `finally` runs `clearTimeout` (50ms timer cleared)         | timer cancelled — won't fire later |

Microtask beats macrotask — `fast` wins.

---

## 10. Common confusion + traps

1. **Timeout doesn't cancel `fn`.** The race rejects, but `fn`'s underlying work continues. For real cancellation, use `AbortController`.

2. **Forgetting `clearTimeout`.** Timer stays alive; Node won't exit gracefully until it fires. Always `clearTimeout` in `finally`.

3. **`Promise.race` without `async` wrapper.** Sync throws in `fn` crash the wrapper. `async function` converts them to rejections automatically.

4. **`t = 0` doesn't mean instant fail.** Microtasks drain before macrotasks. `Promise.resolve(...)`-returning `fn` will beat a 0ms timer.

5. **Reusing the same controller across calls.** Each call needs a fresh `AbortController`. Once aborted, controllers are permanently aborted.

6. **LeetCode wants the string `'Time Limit Exceeded'`.** Production wants a `TimeoutError` class so callers can `instanceof`-check.

7. **`fn` throws synchronously.** `fn.apply(this, args)` may throw before returning a promise. The `async function` wrapper auto-converts to rejection. Without it, wrap in `Promise.resolve().then(() => fn(...))`.

---

## 11. Senior follow-ups & variants

### Variant 1 — First-class cancellation via AbortController

See `timeLimitWithAbort` above. `fn` accepts `{ signal }` as last arg, the wrapper aborts on timeout, `fn` cleans up.

### Variant 2 — Per-call timeout override

```js
function timeLimit(fn, defaultT) {
  return async function (...args) {
    const opts = args[args.length - 1];
    const t = (opts && typeof opts.timeout === 'number') ? opts.timeout : defaultT;
    // ... same race ...
  };
}
```

Callers can pass `{ timeout: 500 }` as the last arg to override.

### Variant 3 — Soft timeout (resolve with fallback)

```js
function softTimeout(fn, t, fallback) {
  return async function (...args) {
    return Promise.race([
      fn.apply(this, args),
      new Promise((resolve) => setTimeout(() => resolve(fallback), t)),
    ]);
  };
}

const fastOrCached = softTimeout(slowFetch, 100, cachedValue);
await fastOrCached();   // returns slow's value if <100ms, else cachedValue
```

For caches where stale-but-fast beats fresh-but-slow.

### Variant 4 — Total timeout vs per-attempt timeout (with retry)

Compose with `retry`:

```js
const limited = timeLimit(fn, 5000);           // per-attempt: 5s
await retryWithBackoff(limited, { retries: 3 }); // total: up to 3×5s + sleep
```

Or use `AbortSignal.timeout` for total deadline:

```js
const controller = new AbortController();
setTimeout(() => controller.abort(), 30_000);
await retryWithBackoff(fn, { retries: 10, signal: controller.signal });
```

### Variant 5 — `Promise.any` with timeout for fallback chains

```js
async function firstResponderOrFail(promises, timeoutMs) {
  return Promise.race([
    Promise.any(promises),
    new Promise((_, rej) => setTimeout(() => rej(new TimeoutError(timeoutMs)), timeoutMs)),
  ]);
}
```

"First success across replicas, with a deadline."

---

## 12. How to think aloud in the interview

> "`Promise.race([fn(...args), timeout])` where timeout is `new Promise((_, rej) => setTimeout(() => rej(err), t))`. Wrap in `async` so sync throws in `fn` become rejections. `clearTimeout` in `finally` — otherwise the event loop stays alive in Node. Critical caveat: race doesn't cancel the loser. If `fn` is fetch, the underlying request keeps streaming. For real cancellation, use `AbortController`: bind a fresh controller per call, abort on timeout, pass `signal` to `fn`. LeetCode wants the string `'Time Limit Exceeded'`; production wants a `TimeoutError` class. Compose with retry by wrapping each attempt with `timeLimit`."

---

## 13. 60-second revision

> - **`Promise.race([fn(...args), timeoutPromise])`** — the whole pattern.
> - **`async function` wrapper** converts sync throws to rejections.
> - **Always `clearTimeout` in `finally`** — event loop hygiene.
> - **Timeout does NOT cancel `fn`'s underlying work** — race just discards the result. For real cancel, use `AbortController`.
> - **Microtasks beat 0ms macrotasks** — `Promise.resolve(...)` wins even at `t=0`.
> - **Production version:** thread `signal` into `fn`, abort on timeout.
> - **LeetCode** wants string `'Time Limit Exceeded'`; **production** wants a `TimeoutError` class.
> - **Family:** same race skeleton powers `firstSuccessful`, `softTimeout`, `staleWhileRevalidate`, `retry`'s per-attempt timeout.
> - **Trap:** thinking timeout cancels the underlying request; forgetting `clearTimeout`.

---

**Related:** [promise-race-polyfill.md](./promise-race-polyfill.md) · [sleep.md](./sleep.md) · [retry-with-backoff.md](./retry-with-backoff.md) · [fetch-with-abort.md](./fetch-with-abort.md) · [abortcontroller-fanout.md](./abortcontroller-fanout.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
