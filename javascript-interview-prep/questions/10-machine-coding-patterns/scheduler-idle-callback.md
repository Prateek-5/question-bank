# Cooperative scheduler — `requestIdleCallback`-style time slicing

> **Difficulty:** Senior   |   **Time:** ~25 min   |   **Prereqs:** [`concepts/event-loop.md`](../../concepts/event-loop.md), [`05-event-loop/microtask-macrotask-order.md`](../05-event-loop/microtask-macrotask-order.md)
>
> **Source:** Browser `requestIdleCallback`, React Fiber's scheduler, `scheduler` package, Chromium `scheduler.postTask`.

---

## 1. Problem statement

**Signature**
```ts
function createScheduler(opts?: { frameBudgetMs?: number }): {
  postTask(fn: (deadline: { timeRemaining(): number }) => void, opts?: { priority?: 'high' | 'normal' }): number;
  cancel(token: number): void;
};

// Or polyfill:
function requestIdleCallback(cb, { timeout?: number }): handle;
function cancelIdleCallback(handle): void;
```

**Input / Output examples**

| Setup                                     | Behaviour                                              |
|-------------------------------------------|---------------------------------------------------------|
| 100 small tasks submitted in tight loop   | drained across ~20 macrotasks, ~5/frame; event loop responsive |
| `await Promise.resolve()` between tasks   | DOES NOT yield to event loop (microtask)               |
| `setTimeout(0)` between tasks             | Yields, but 4ms-clamped after 5 nests                  |
| `MessageChannel.postMessage(0)`            | Yields, no clamp — React Fiber's trick                 |
| `cancel(token)` before drain              | task tombstoned, skipped                               |

**Constraints**
- Drain in budgeted bursts (~5ms); yield via macrotask.
- **Microtasks (Promise.then, queueMicrotask) do NOT yield** to event loop.
- `performance.now()` for monotonic budget; `Date.now()` jumps on NTP.
- Cancellation via tombstone (sentinel token) — cheaper than splice.

---

## 2. Plain-English restatement

JS is single-threaded. If you have 10k tasks, naïve `for` blocks the main thread for seconds. A cooperative scheduler runs tasks in bursts within a budget (e.g., 5ms), then **yields to the event loop** so timers, I/O, and paints can happen, then resumes. `MessageChannel.postMessage(0)` is the fast yield primitive; `setTimeout(0)` has a 4ms clamp.

---

## 3. Why this matters in interviews

Probes **event-loop awareness**. You don't have threads, so you fake parallelism by chunking work across macrotasks. Tests: macrotask vs microtask distinction, `setTimeout(0)`'s 4ms clamp, `MessageChannel` for true zero-delay yielding, `performance.now()` for budgets. Backend uses: batch jobs that yield to keep an HTTP server responsive, log-flush batchers, streaming ETL chunkers.

---

## 4. Mental model

```
   Cooperative time-slicing:
   ┌─────────────────────────────────────────────────────────────┐
   │ Macrotask 1: drain tasks for ~5ms → yield (postMessage)     │
   │ ←── event loop runs I/O, timers, paints ──→                 │
   │ Macrotask 2: drain more for ~5ms → yield                    │
   │ ←── event loop runs I/O, timers, paints ──→                 │
   │ ...                                                          │
   └─────────────────────────────────────────────────────────────┘

   Yield primitives (best → worst):
   1. MessageChannel.port2.postMessage(0)   ← no clamp, fastest
   2. setImmediate(cb)                       ← Node only
   3. setTimeout(cb, 0)                      ← 4ms clamp after 5 nests

   CAREFUL: Promise.resolve().then(cb) does NOT yield to event loop.
   Microtasks run to exhaustion BEFORE the next macrotask.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why does `await Promise.resolve()` NOT yield to the event loop?
> 2. Why is `setTimeout(0)` 4ms instead of 0?
> 3. What's the right way to yield in a tight loop in modern code?

---

## 6. Brute force — walked through

### Wrong attempt 1: `setTimeout(work, 0)` one task per tick
Correct but slow — 10k tasks × 4ms clamp = 40 seconds.

### Wrong attempt 2: run all sync, "trust the browser to paint"
Main thread blocks; paints stall; HTTP server unresponsive.

### Wrong attempt 3: `await Promise.resolve()` to "yield"
Microtask — runs in same macrotask. Event loop never gets a chance for I/O/timers.

---

## 7. The unlocking insight

> **Drain a queue inside a budget; yield via `MessageChannel.postMessage(0)` (browser/Node 15+) or `setImmediate` (Node). Track time with `performance.now()` and a `timeRemaining()` callback. Tombstone cancellation.**

Three properties:

1. **Macrotask yield, not microtask** — only macrotasks let the event loop run other work.
2. **`MessageChannel`** beats `setTimeout(0)` — no 4ms clamp.
3. **`performance.now()`** for monotonic budgeting.

---

## 8. Solution (annotated)

```js
function createScheduler({ frameBudgetMs = 5 } = {}) {
  const queue = [];
  let scheduled = false;
  let cancelToken = 0;

  const channel = typeof MessageChannel !== 'undefined' ? new MessageChannel() : null;
  const yieldNow = (cb) => {                                       // step 1: fast macrotask yield
    if (channel) {
      channel.port1.onmessage = cb;
      channel.port2.postMessage(0);
    } else if (typeof setImmediate !== 'undefined') {
      setImmediate(cb);
    } else {
      setTimeout(cb, 0);
    }
  };

  function drain() {                                                // step 2: bounded burst
    scheduled = false;
    const start = performance.now();
    while (queue.length && performance.now() - start < frameBudgetMs) {
      const { fn, token } = queue.shift();
      if (token === -1) continue;                                   // tombstoned (cancelled)
      try {
        fn({ timeRemaining: () => Math.max(0, frameBudgetMs - (performance.now() - start)) });
      } catch (e) {
        queueMicrotask(() => { throw e; });                          // isolate
      }
    }
    if (queue.length) schedule();                                    // step 3: schedule continuation
  }

  function schedule() {
    if (scheduled) return;                                            // dedupe
    scheduled = true;
    yieldNow(drain);
  }

  function postTask(fn, { priority = 'normal' } = {}) {
    const task = { fn, token: ++cancelToken };
    if (priority === 'high') queue.unshift(task);
    else queue.push(task);
    schedule();
    return task.token;
  }

  function cancel(token) {
    const t = queue.find((x) => x.token === token);
    if (t) t.token = -1;                                              // step 4: tombstone
  }

  return { postTask, cancel };
}

// Simple polyfill matching requestIdleCallback API
const requestIdleCallback = (cb, { timeout = 50 } = {}) => {
  const start = performance.now();
  return setTimeout(() => {
    cb({ didTimeout: false, timeRemaining: () => Math.max(0, timeout - (performance.now() - start)) });
  }, 1);
};
const cancelIdleCallback = (h) => clearTimeout(h);
```

**Try it yourself**

```js
const sch = createScheduler({ frameBudgetMs: 5 });
for (let i = 0; i < 1000; i++) {
  sch.postTask(({ timeRemaining }) => {
    // simulate ~1ms of work
    const end = performance.now() + 1;
    while (performance.now() < end);
  });
}
// 1000 tasks drained across ~200 macrotasks; main thread responsive throughout.

// Cancel
const t = sch.postTask(() => console.log('never runs'));
sch.cancel(t);
```

---

## 9. Step-by-step dry run

```
postTask × 1000 in tight loop:
  push 1000 tasks → queue.length=1000
  schedule() called 1000 times, scheduled=true dedupes → 1 yieldNow call

Macrotask 1 (after current macrotask ends):
  drain():
    start = T0
    while queue.length>0 and now - start < 5ms:
      task = queue.shift()
      task.fn(...)  ← ~1ms each → roughly 5 tasks
    queue.length=995 → schedule() again

Macrotask 2: same → drains 5 more. queue.length=990.
...
Macrotask 200: queue.length=0; no reschedule.

Between each macrotask: event loop runs I/O, timers, paints.
Compare with sync loop: ~1000ms block; with scheduler: ~5ms bursts × 200 = same total CPU but main thread responsive between.

Cancel:
  postTask → token=T
  cancel(T): queue entry's token = -1 (tombstone)
  drain: encounters tombstone, continue (skip)
```

---

## 10. Common confusion + traps

1. **`setTimeout(0)` is not actually 0** — clamped to 4ms after 5 nests.
2. **`await Promise.resolve()` to "yield"** — microtask, doesn't yield to event loop.
3. **`Date.now()` for budgets** — non-monotonic; clock can jump backward.
4. **No dedupe on `schedule()`** — every postTask posts its own message; queue grows polynomially.
5. **Recursive `setTimeout(0)` chains** — hits 4ms clamp; use `MessageChannel`.
6. **Forgetting `timeRemaining` is a function** — passing the value at start time ignores budget.
7. **`MessageChannel` leak** — `port1.close()` if you create many short-lived ones. For a shared scheduler, hold one channel for the app lifetime.

---

## 11. Senior follow-ups & variants

### Variant 1 — Priority scheduler
Heap-backed priority queue (see [min-heap-priority-queue.md](./min-heap-priority-queue.md)). React has 5 priority levels.

### Variant 2 — `requestAnimationFrame` budget
Browser-only; use `rAF` instead of MessageChannel. Aligns work with paint cycles; budget = 16.67ms − frame-time-used.

### Variant 3 — Worker offload
For genuinely CPU-bound work, cooperative scheduling on the main thread doesn't help. Move to a Worker. Scheduler decides when to enqueue.

### Variant 4 — `scheduler.postTask` (Chromium native)
Modern API with `'user-blocking'`, `'user-visible'`, `'background'` priorities. Future replacement for `requestIdleCallback`.

### Variant 5 — Continuation-passing tasks
Each task can `yield` (return a continuation) to be resumed in a later frame. Used by React Fiber to split rendering work.

---

## 12. How to think aloud

> "Queue + macrotask yield. Yield primitive: `MessageChannel.postMessage(0)` (fastest, no 4ms clamp), `setImmediate` in Node, `setTimeout(0)` as last resort. Microtasks (Promise, queueMicrotask) do NOT yield to event loop — they run to exhaustion before next macrotask. `performance.now()` for budgets — monotonic. Inside drain loop: `while (queue.length && now() - start < budget)`. Cancellation via tombstone (sentinel token), cheaper than splice. Trap: 4ms clamp on nested setTimeout; microtask 'yield' that doesn't actually yield; not deduping schedule() so queue grows polynomially. Same pattern in log batchers, GC pacing, streaming ETL, React Fiber, RxJS `bufferTime`."

---

## 13. 60-second revision

> - **Queue + macrotask yield** = cooperative time-slicing.
> - **Yield primitive:** `MessageChannel.postMessage(0)` > `setImmediate` > `setTimeout(0)`.
> - **Microtasks do NOT yield** to event loop (run to exhaustion first).
> - **`performance.now()`** for monotonic budgets.
> - **`timeRemaining()`** is a function — recomputed inside the loop.
> - **Tombstone cancellation** (sentinel token); skip on drain.
> - **Dedupe `schedule()` calls** with a `scheduled` flag.
> - **Family:** React Fiber, log batchers, ETL chunkers, GC pacing, `scheduler.postTask`.
> - **Trap:** 4ms clamp; microtask "yield"; missing dedupe; `Date.now()` for budgets.

---

**Related:** [`05-event-loop/microtask-macrotask-order.md`](../05-event-loop/microtask-macrotask-order.md) · [`05-event-loop/microtask-starvation-recipes.md`](../05-event-loop/microtask-starvation-recipes.md) · [`04-promises/microtask-drainer.md`](../04-promises/microtask-drainer.md) · [min-heap-priority-queue.md](./min-heap-priority-queue.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
