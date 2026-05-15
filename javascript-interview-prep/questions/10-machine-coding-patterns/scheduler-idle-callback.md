# Implement a `requestIdleCallback`-like cooperative scheduler

## Source
- Browser API spec (`window.requestIdleCallback`) — not available in Node, and not in Safari until 2022.
- React Fiber's scheduler, Vue's scheduler, the `scheduler` package on npm — all built around this pattern.

## Why this question matters in interviews
This problem hits the **event-loop awareness** axis hard. Implementing a cooperative scheduler in JS forces you to reason about what "yielding back to the event loop" actually means — you don't have threads, so you fake it by chunking work across macrotasks. It probes **`setTimeout(fn, 0)`'s 4ms clamp**, **`MessageChannel` as a faster postTask**, **`performance.now()` for time budgets**, and **how React Fiber renders without blocking the main thread**. As a backend engineer you'll see this pattern in: batch jobs that yield to keep an HTTP server responsive, long-running stream consumers that periodically `await new Promise(setImmediate)`, log-flush batchers that respect a deadline.

## Concepts involved

### Syntax to lock in
```js
// Minimal polyfill for browsers / Node that lack requestIdleCallback
const requestIdle = (callback, { timeout = Infinity } = {}) => {
  const start = performance.now();
  return setTimeout(() => {
    const elapsed = performance.now() - start;
    callback({
      didTimeout: elapsed >= timeout,
      timeRemaining: () => Math.max(0, 50 - (performance.now() - start)),
    });
  }, 1);
};

// usage
requestIdle((deadline) => {
  while (deadline.timeRemaining() > 0 && tasks.length) {
    runOne(tasks.shift());
  }
  if (tasks.length) requestIdle(callback);   // continue next frame
});
```

### Runtime / engine behavior
- The native `requestIdleCallback` runs the callback **after the browser finishes painting and has spare time before the next frame** (typically 50ms of idle budget). In a non-browser environment, you simulate this with a deferred macrotask.
- `setTimeout(fn, 0)` is the simplest fallback. Browsers clamp nested `setTimeout(_, 0)` to **4ms minimum** after 5 levels of nesting — that's why `MessageChannel` is preferred for true zero-delay yielding.
- `MessageChannel`: `const ch = new MessageChannel(); ch.port1.onmessage = fn; ch.port2.postMessage(0);` triggers `fn` on the next macrotask without the 4ms clamp. React Fiber uses this exact trick.
- The "time budget" in the deadline object lets your task code decide whether to keep working or to yield. The native default budget is ~50ms (one frame at 20fps headroom on a 60fps display).
- Macrotask vs microtask: yielding via `setTimeout` or `MessageChannel` lets the event loop process I/O, timers, paints — microtasks (`Promise.then`, `queueMicrotask`) do **not** yield to the event loop, they run to exhaustion before the next macrotask. Use macrotasks for cooperative scheduling.

### Edge cases (these are the interview traps)
1. **`setTimeout(0)` is not actually zero** — it's clamped (4ms in browsers; ~1ms in Node). For tight loops use `setImmediate` (Node only) or `MessageChannel` (browser + Node 15+).
2. **Microtask trap** — `await Promise.resolve()` does **not** yield to the event loop. It runs the next continuation as a microtask, which is still on the same macrotask. Backend engineers `await new Promise(setImmediate)` to truly yield.
3. **`performance.now()` is monotonic** — `Date.now()` is wall-clock, can jump on NTP adjust. Always use `performance.now()` for budgets.
4. **`timeRemaining` is a function**, not a property — it's called repeatedly inside the work loop so the budget reflects "right now."
5. **Task cancellation** — `cancelIdleCallback(handle)` mirrors the API. Your polyfill returns a `setTimeout` handle which you `clearTimeout`.
6. **Starvation prevention** — if you schedule callbacks recursively, the event loop never gets to other work. The deadline + yield pattern ensures cooperation.
7. **`MessageChannel` requires cleanup** — leaks if you don't `port1.close()`. For a shared scheduler, hold a single MessageChannel for the lifetime of the app.
8. **`requestIdleCallback` may never fire** — if the page is always busy, idle time never comes. The `timeout` option forces a deadline-based fire ("run within Xms even if not idle").

## Brute force approach
Use `setTimeout(work, 0)` and run **one task per timeout**. Correct, but inefficient: a queue of 10k tasks takes 10k macrotasks, each with the 4ms clamp = 40 seconds. The `while (deadline.timeRemaining() > 0)` loop is what makes this efficient — drain as much as fits in the budget, then yield.

Another non-starter: run all tasks synchronously and "trust the browser to paint between them." It won't — the main thread is blocked. The whole point of cooperative scheduling is **yielding voluntarily**.

## Optimal approach
- Maintain a task queue (FIFO or priority).
- On each macrotask wakeup, drain as many tasks as fit in the budget.
- If tasks remain, schedule another wakeup via `MessageChannel.postMessage(0)` (fast) or `setTimeout(fn, 0)` (fallback).
- Track `deadline.timeRemaining()` with `performance.now()`.

## Solution (JavaScript)

```js
/**
 * Cooperative scheduler — runs tasks across macrotasks so the event loop
 * stays responsive. Inspired by React's scheduler package.
 */
function createScheduler({ frameBudgetMs = 5 } = {}) {
  const queue = [];
  let scheduled = false;
  let cancelToken = 0;

  // Fast yield primitive. MessageChannel avoids setTimeout's 4ms clamp.
  const channel = typeof MessageChannel !== 'undefined' ? new MessageChannel() : null;
  const yieldNow = (cb) => {
    if (channel) {
      channel.port1.onmessage = cb;
      channel.port2.postMessage(0);
    } else if (typeof setImmediate !== 'undefined') {
      setImmediate(cb);                          // Node
    } else {
      setTimeout(cb, 0);                         // last resort
    }
  };

  function drain() {
    scheduled = false;
    const start = performance.now();
    while (queue.length && performance.now() - start < frameBudgetMs) {
      const { fn, token } = queue.shift();
      if (token === -1) continue;                // cancelled
      try { fn({ timeRemaining: () => Math.max(0, frameBudgetMs - (performance.now() - start)) }); }
      catch (e) { queueMicrotask(() => { throw e; }); }
    }
    if (queue.length) schedule();
  }

  function schedule() {
    if (scheduled) return;
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
    if (t) t.token = -1;                          // tombstone; skip on drain
  }

  return { postTask, cancel };
}

// Simpler polyfill matching the requestIdleCallback API
const requestIdleCallback = (cb, { timeout = 50 } = {}) => {
  const start = performance.now();
  return setTimeout(() => {
    cb({
      didTimeout: false,
      timeRemaining: () => Math.max(0, timeout - (performance.now() - start)),
    });
  }, 1);
};
const cancelIdleCallback = (h) => clearTimeout(h);
```

## Step-by-step dry run

Input: 100 small tasks (each ~1ms) submitted in a tight loop.

```js
const sch = createScheduler({ frameBudgetMs: 5 });
const start = performance.now();
for (let i = 0; i < 100; i++) {
  sch.postTask(() => { /* simulate 1ms of work */ });
}
```

Trace:
- All 100 tasks are pushed to `queue`. `schedule()` is called once (`scheduled` flag dedups).
- `yieldNow(drain)` posts a message on the channel. The current macrotask (the `for` loop) finishes.
- **Macrotask 1**: drain wakes up. `start = T0`. Loop drains tasks while `now - start < 5ms`. Roughly 5 tasks fit. Queue: 95 left. `schedule()` again.
- **Macrotask 2**: same — drains ~5 more. 90 left.
- ... continues for ~20 macrotasks total, ~5 tasks each. Between each macrotask the event loop can process I/O, paints, other timers.

Compare with naive `for` loop without scheduler: 100ms blocking the main thread → dropped frames, unresponsive UI / blocked I/O.

Cancellation:
```js
const t1 = sch.postTask(work1);
const t2 = sch.postTask(work2);
sch.cancel(t1);                // tombstone — work1 skipped on drain
```

## Important takeaways

**Syntax to memorize**
- `MessageChannel` postMessage trick — fast macrotask yield without the 4ms clamp.
- `performance.now()` for budgets (monotonic, sub-ms precision).
- `setImmediate` in Node, `setTimeout(0)` as last fallback.
- Tombstone cancellation (mark with sentinel, skip on drain) is cheaper than splicing.

**Patterns to reuse**
- "Drain queue inside a budget, yield, repeat" is the same pattern as: log-flushing batchers, GC pacing, streaming ETL chunkers, RxJS's `bufferTime`.
- The deadline object pattern (`{ timeRemaining: () => ms }`) generalizes — it's the right shape for any time-budgeted callback API.

**Common mistakes**
- Using `Date.now()` for budgets — non-monotonic, can go backwards on clock sync.
- Using `await Promise.resolve()` to "yield" — that's a microtask, not a macrotask. Event loop never breaks.
- Forgetting to dedupe `schedule()` calls — every `postTask` posts its own message, queue grows polynomially.
- Recursive `setTimeout(0)` chains — hits the 4ms clamp; for high-throughput use `MessageChannel`.
- Forgetting `timeRemaining` is a function — passing the value at start time means the work loop ignores the budget.

**Related questions**
- Node `setImmediate` vs `setTimeout(0)` ordering inside I/O callbacks.
- React Fiber's `unstable_scheduleCallback`.
- `queueMicrotask` vs `Promise.resolve().then` — both schedule microtasks; queueMicrotask is cheaper.
- Worker threads (CPU-bound work needs real parallelism, not cooperation).

## Variants

1. **Priority scheduler** — heap-backed priority queue instead of FIFO. Each task has a priority + deadline. Pick the most urgent under deadline pressure. React's scheduler does this with 5 priority levels.

2. **`requestAnimationFrame` budget** — use `rAF` instead of MessageChannel; budget the frame at 16.67ms - frame-time-used. Aligns work with paint cycle. Browser-only.

3. **Worker offload** — for genuinely CPU-bound work (image processing, parsing), cooperative scheduling on the main thread doesn't help. Move it to a Worker. Combine: scheduler decides when to enqueue to the worker.

4. **`scheduler.postTask` (native, Chromium)** — modern web platform API with priority levels (`'user-blocking'`, `'user-visible'`, `'background'`). Future replacement for `requestIdleCallback`. Mention as the spec direction.

## Revision notes

> **Cooperative scheduler — 75 second recap**
> - Queue + macrotask yield = cooperative time-slicing without threads.
> - Yield primitive: `MessageChannel.postMessage(0)` (fast, no 4ms clamp) > `setImmediate` (Node) > `setTimeout(0)` (last resort).
> - Microtasks (Promise, queueMicrotask) do NOT yield to the event loop. Macrotasks do.
> - `performance.now()` for budgets — monotonic. Inside the drain loop call `now() - start < budget`.
> - Cancellation via tombstone (set sentinel token, skip on drain) is cheaper than splice.
> - Trap: 4ms clamp on nested setTimeout, microtask "yield" that doesn't actually yield, recomputing budget incorrectly.
> - Pattern reused in log batchers, ETL streamers, React Fiber, RxJS bufferTime.
