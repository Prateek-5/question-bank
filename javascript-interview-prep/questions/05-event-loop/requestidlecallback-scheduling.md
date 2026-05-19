# `requestIdleCallback` — cooperative background scheduling

> **Difficulty:** Medium-Senior   |   **Time:** ~15 min   |   **Prereqs:** [messagechannel-microtask.md](./messagechannel-microtask.md), [`10-machine-coding-patterns/scheduler-idle-callback.md`](../10-machine-coding-patterns/scheduler-idle-callback.md)
>
> **Source:** Browser API. React Fiber initially used it (then moved to MessageChannel for finer slicing). Razorpay, Atlassian, Cloudflare frontend roles.

---

## 1. Problem statement

Use `requestIdleCallback(fn, { timeout })` to drain a queue of work across idle slices without blocking the UI.

**Verification examples**

| Setup                                            | Behaviour                                              |
|--------------------------------------------------|---------------------------------------------------------|
| 10k tasks scheduled                              | drained over many idle slices; UI stays responsive    |
| Heavy scrolling                                  | idle time vanishes; `timeout` forces deadline         |
| `deadline.timeRemaining()`                        | decreases over time; check INSIDE loop                |
| `deadline.didTimeout`                             | true if fired via timeout (no budget)                 |
| Node                                             | no `requestIdleCallback`; use `setImmediate`           |

**Constraints**
- Browser-only.
- `deadline.timeRemaining()` decreases — must re-check per iteration.
- `timeout` knob prevents starvation under heavy frames.
- Cooperative; voluntary yield, no preemption.
- Coarse resolution (~50ms slices); React Fiber moved to `MessageChannel`.

---

## 2. Plain-English restatement

Browser API: "call me back when you have idle time, and tell me how much I have." You drain work while `timeRemaining()` > 0, then ask to be called again next idle. The `timeout` option forces a deadline-based fire if the page is always busy.

---

## 3. Why this matters in interviews

The React Fiber story. Tests browser-perf intuition (60fps rule, frame budget), scheduler awareness, cooperative concurrency.

---

## 4. Mental model

```
   Browser frame loop:
   [frame 16ms] [frame 16ms] [frame 16ms] ...
              ^               ^               ^
              └── after each, if idle time: run rIC callbacks

   rIC callback receives a `deadline` object:
     deadline.timeRemaining() → ms left in this slice (decreasing)
     deadline.didTimeout       → true if forced via timeout

   Drain pattern:
   while (deadline.timeRemaining() > 1 && queue.length) {
     process(queue.shift());
   }
   if (queue.length) requestIdleCallback(again);

   Heavy frames (scrolling, animations): no idle time → rIC may starve.
   → pass { timeout: 200 }: forces fire after 200ms regardless.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Is `requestIdleCallback` parallel or chunked-serial?
> 2. Does `timeRemaining()` return the same value each call?
> 3. What happens under heavy scrolling without a `timeout`?

---

## 6. Brute force — walked through

### Wrong attempt 1: `for` loop blocks UI
10k tasks in a row → frozen UI for seconds.

### Wrong attempt 2: rIC without `timeout`
Heavy scrolling → never idle → queue never drains.

### Wrong attempt 3: check `timeRemaining()` once at start
Decreases over time; must re-check per iteration.

---

## 7. The unlocking insight

> **rIC hands a slice with `timeRemaining()`. Drain queue while time remains, re-schedule if more work. Always pass `timeout` to prevent starvation under heavy frames. React Fiber moved to `MessageChannel`-based scheduling for finer slices.**

Three properties:

1. **Cooperative time-slicing** — voluntary yield.
2. **`timeRemaining()` decreases** — re-check.
3. **`timeout` prevents starvation.**

---

## 8. Solution (annotated)

```js
class IdleScheduler {
  constructor() { this.queue = []; this.scheduled = false; }

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
    while (
      this.queue.length > 0
      && (deadline.timeRemaining() > 1 || deadline.didTimeout)         // step 1: re-check budget
    ) {
      const t = this.queue.shift();
      try { t(); } catch (e) { console.error(e); }
    }
    if (this.queue.length > 0) this._schedule();                       // step 2: reschedule
  }
}

// Node fallback (no rIC)
const scheduler = typeof requestIdleCallback === 'function'
  ? new IdleScheduler()
  : { schedule: (t) => setImmediate(t) };
```

**Try it yourself**

```js
for (let i = 0; i < 10_000; i++) {
  scheduler.schedule(() => processItem(items[i]));
}
// UI stays responsive; tasks drain over many idle slices.

// Yield helper for async loops
async function yieldToBrowser() {
  return new Promise((r) => requestIdleCallback(() => r(), { timeout: 200 }));
}
async function heavyAsync(items) {
  for (let i = 0; i < items.length; i++) {
    process(items[i]);
    if (i % 100 === 0) await yieldToBrowser();
  }
}
```

---

## 9. Step-by-step dry run

```
10 tasks, each ~2ms, frame budget ~50ms idle:

t=0    schedule(t1..t10) → queue.length=10; requestIdleCallback queued.
t=16   browser idle after frame → callback fires.
       deadline.timeRemaining()=50ms.
       drain: t1 (50→48), t2 (48→46), ... 10 tasks fit easily.
       queue=[].

Heavy scrolling scenario:
t=0    schedule(t1..t10); requestIdleCallback queued.
t=16   frame busy with scrolling; rIC NOT called.
t=33   still busy.
...
t=200  timeout fires → callback runs with didTimeout=true.
       drain regardless of timeRemaining → all 10 process.

Without timeout: queue might never drain during scrolling.
```

---

## 10. Common confusion + traps

1. **"rIC is parallel"** — same main thread; chunked.
2. **"`timeRemaining()` constant"** — decreases; check per iter.
3. **"Always pass `timeout`"** — only if you have a deadline.
4. **"Same as `setTimeout(0)`"** — setTimeout doesn't tell you budget.
5. **Forget atomic units** — one 100ms task doesn't fit a slice.
6. **Available in Node** — no, browser-only.
7. **Preemption** — no; cooperative only.

---

## 11. Senior follow-ups & variants

### Variant 1 — `MessageChannel`-based scheduler
React Fiber moved to this for finer slicing. No frame-budget knowledge but no rate limit.

### Variant 2 — Priority queues
High/normal/low; drain in priority order.

### Variant 3 — `Scheduler.postTask` (new spec)
Chromium-native; priorities (`user-blocking`, `user-visible`, `background`).

### Variant 4 — Web Worker offload
For CPU-bound work, move off main thread entirely. rIC only helps if work can split into small chunks.

### Variant 5 — Yield helper
`await new Promise(r => requestIdleCallback(r, { timeout: 200 }))` — async yield.

---

## 12. How to think aloud

> "rIC hands me a slice with `deadline.timeRemaining()`. I split work into atomic units, drain while time remains, re-schedule if queue not empty. Always pass `timeout` so heavy frames can't starve me forever. For UI-critical work I'd use MessageChannel-based scheduling instead — that's what React Fiber moved to for finer slicing. Node has no rIC; `setImmediate` is the rough equivalent. Cooperative, not preemptive. Trap: not re-checking `timeRemaining` (decreases); large tasks that can't split."

---

## 13. 60-second revision

> - **Browser only;** Node uses `setImmediate`.
> - **`deadline.timeRemaining()`** decreases — re-check per iter.
> - **`timeout` knob** prevents starvation under heavy frames.
> - **Atomic units** — tasks must fit a slice.
> - **Cooperative**, not preemptive.
> - **React Fiber moved off rIC** to `MessageChannel` for finer slices.
> - **Family:** `Scheduler.postTask` (priorities), `MessageChannel`, Web Workers.
> - **Trap:** check timeRemaining once; large tasks; assume parallel; no timeout.

---

**Related:** [messagechannel-microtask.md](./messagechannel-microtask.md) · [`10-machine-coding-patterns/scheduler-idle-callback.md`](../10-machine-coding-patterns/scheduler-idle-callback.md) · [worker-threads-vs-event-loop.md](./worker-threads-vs-event-loop.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
