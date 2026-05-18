# `requestIdleCallback` — Cooperative Background Scheduling

## Source / Origin
- Browser API; React Fiber's scheduler uses an equivalent.
- Node equivalent: `setImmediate` + manual yield.
- Asked at: Razorpay, Atlassian, Cloudflare (browser perf roles).
- Concept reference: `concepts/event-loop.md`, sibling `scheduler-idle-callback.md`.

## Why this question matters in interviews
"You have 10,000 tasks; don't block the main thread." That's the entire React 18 Fiber story. `requestIdleCallback` (rIC) hands you the next idle slice and tells you how many ms you have until the next frame. You yield when time runs out; the runtime calls you back next idle. Senior bar: you know rIC has a deadline contract, that it can starve under heavy work, and that React eventually moved off it for `MessageChannel`-based scheduling because rIC is too coarse.

## Concepts involved

### Syntax to lock in
```js
// Browser-native scheduling
requestIdleCallback((deadline) => {
  while (deadline.timeRemaining() > 0 && tasks.length > 0) {
    const t = tasks.shift();
    process(t);
  }
  if (tasks.length > 0) requestIdleCallback(arguments.callee);    // re-schedule
});

// With timeout fallback (forces a deadline even if browser is busy)
requestIdleCallback(callback, { timeout: 200 });   // run within 200ms even if not idle
```

### Edge cases / interview traps
1. **`deadline.timeRemaining()` decreases over time.** Re-check inside the loop, not just at the start.
2. **`didTimeout`** — `deadline.didTimeout` is `true` if the callback fired because of the `timeout` option, not because of idle time. You then have *no* time budget.
3. **Starvation under heavy frames.** rIC can be skipped frame after frame if the main thread is busy. Hence the `timeout` knob.
4. **Not available in Node.** Use `setImmediate` (Node-specific; macrotask) for a similar yield pattern.
5. **Resolution is coarse.** ~50ms slices is typical; React went to `MessageChannel` (no slicing limit) for finer scheduling.
6. **Tasks must be split into chunks** small enough to fit; one big task that's 100ms doesn't help.
7. **Cooperation, not preemption.** The browser can't interrupt your synchronous code — you must voluntarily check `timeRemaining()` and yield.
8. **`cancelIdleCallback(id)`** for cancellation.

## Mental Model

The browser is a **café**:

```
   [render frame    16ms] [render frame 16ms] [render frame 16ms] ...
                      ^
                      └── after each frame, if there's idle time, run rIC callbacks
                          deadline.timeRemaining() tells you how much time is left

   you (rIC callback):
     while (deadline.timeRemaining() > 0 && tasks.length > 0):
        process(tasks.shift())
     if (tasks.length > 0):
        requestIdleCallback(again)   // ask for another slice next idle

   browser: "OK, I'll call you back when I have idle time again."
```

When the user starts scrolling or the page is animating heavily, idle slices vanish. The `timeout` option forces a deadline anyway.

## Why interviewers care

- **Browser perf intuition** — the 60fps rule, frame budget.
- **Scheduler awareness** — React Fiber uses this exact pattern.
- **Cooperative concurrency** — voluntary yields, no preemption.

## Common beginner confusion

- **"rIC is parallel."** No — same main thread; just chunked.
- **"It runs on a different thread."** Same thread; just deferred.
- **"timeRemaining() is constant."** It decreases; check on every iteration.
- **"Always pass a timeout."** Only if you have a deadline. Without timeout, rIC may delay indefinitely.
- **"setTimeout(0) is the same."** setTimeout is a macrotask — fires regardless of frame; doesn't tell you "how much budget you have."

## Brute force approach

```js
// Blocks the main thread for entire duration → UI freeze
for (const t of bigTasks) process(t);
```

## Optimal approach

Break work into atomic units. Use `requestIdleCallback` to drain the queue across idle slices. Provide a `timeout` so the work eventually completes even under contention.

## Solution (JavaScript)

```js
class IdleScheduler {
  constructor() { this.queue = []; this.scheduled = false; this.deadline = null; }

  schedule(task) {
    this.queue.push(task);
    if (!this.scheduled) this._schedule();
  }

  _schedule() {
    this.scheduled = true;
    requestIdleCallback((deadline) => this._drain(deadline), { timeout: 200 });
  }

  _drain(deadline) {
    this.scheduled = false;
    while (this.queue.length > 0 && (deadline.timeRemaining() > 1 || deadline.didTimeout)) {
      const t = this.queue.shift();
      try { t(); } catch (e) { console.error(e); }
    }
    if (this.queue.length > 0) this._schedule();
  }
}

// Node fallback (no rIC)
const scheduler = typeof requestIdleCallback === 'function'
  ? new IdleScheduler()
  : { schedule: (t) => setImmediate(t) };

// Usage
for (let i = 0; i < 10_000; i++) {
  scheduler.schedule(() => processItem(items[i]));
}
// UI stays responsive; tasks drain over multiple idle slices
```

For high-priority work that *must* run soon (React-style):

```js
const microtaskChannel = new MessageChannel();
microtaskChannel.port1.onmessage = drain;
function scheduleHighPriority(task) {
  highQueue.push(task);
  microtaskChannel.port2.postMessage(null);    // macrotask, but no frame-rate gating
}
```

## Step-by-step dry run

10 tasks; each takes ~2ms; frame budget ~50ms idle:

```
t=0    schedule(t1..t10) → queue=[t1..t10]; requestIdleCallback
t=16   browser idle → callback fires; deadline.timeRemaining()=50ms
       drain: t1 (2ms remaining=48), t2 (2ms r=46), ... 10 tasks fit easily
       queue=[]; done
```

Heavy-frame scenario (page scrolling):

```
t=0    schedule(t1..t10); requestIdleCallback
t=16   frame is busy; rIC not called
t=33   still busy
...
t=200  timeout fires → callback runs with deadline.didTimeout=true
       drain: process tasks regardless of timeRemaining()
       queue=[]; done
```

Without `timeout: 200`, the queue might never drain during heavy scrolling.

## How to think aloud in the interview

> "rIC hands me a slice with `timeRemaining()`. I split work into atomic units, drain while time remains, re-schedule if queue not empty. Always pass a `timeout` so heavy frames can't starve me forever. For UI-critical work I'd use `MessageChannel`-based scheduling instead — that's what React Fiber moved to for finer slicing. Node has no rIC; `setImmediate` is the rough equivalent — macrotask boundary, no time budget."

## Important takeaways

- **rIC = browser-only.** Node has `setImmediate`.
- **`timeRemaining()` decreases** — check on each iteration.
- **`timeout` knob** prevents starvation.
- **Split tasks into atomic units** small enough to fit a slice.
- **Cooperative, not preemptive.**
- **React Fiber moved off rIC** to `MessageChannel` — same pattern, finer slices.

## Variants

- **MessageChannel-based scheduler** — postMessage is a macrotask; no frame-budget knowledge but no rate limit.
- **Priority queues** — high/normal/low; drain in priority order.
- **`Scheduler.postTask`** (new spec) — finer priorities (user-blocking, user-visible, background).
- **`yield` helper** — `await new Promise(r => requestIdleCallback(r))` to yield in an async loop.
- **Web Workers offload** — for CPU work, just move it off main thread entirely.

## Revision notes

```
requestIdleCallback(cb, {timeout?}):
  cb(deadline) — deadline.timeRemaining(), deadline.didTimeout
  cooperative: must voluntarily yield
  re-schedule if queue not empty
  
  PATTERN:
    while (queue.length && (deadline.timeRemaining() > 1 || deadline.didTimeout)):
      process(queue.shift())
    if queue.length: requestIdleCallback(again)
  
  TRAPS:
  - heavy frames → starvation; pass timeout
  - tasks must be SMALL (atomic units)
  - browser-only; Node uses setImmediate
  - cooperative, not preemptive
  
  alternative: MessageChannel for high-priority; Web Worker for CPU-bound
```
