# Microtask Starvation — recipes and cures

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [nexttick-starvation.md](./nexttick-starvation.md), [queuemicrotask-deep-dive.md](./queuemicrotask-deep-dive.md)
>
> **Source:** Real Node outage write-ups; React 18 scheduler rationale.

---

## 1. Problem statement

What recipes cause microtask starvation? How do you detect it? How do you cure it?

**Verification examples**

| Recipe                                          | Effect                                                 |
|-------------------------------------------------|---------------------------------------------------------|
| `while (true) await Promise.resolve()`           | starves macrotasks indefinitely                        |
| `function loop() { queueMicrotask(loop) } loop()` | same — microtask never empties                        |
| `function s() { process.nextTick(s) } s()` (Node) | starves microtasks AND macrotasks                     |
| Chained `.then` × 1M                              | bounded starvation; loop unresponsive during drain    |
| Cure: `await new Promise(r => setImmediate(r))` periodically | yields to macrotask phase            |

**Constraints**
- Microtasks drain to empty before each macrotask — recursive scheduling starves I/O.
- Symptom: process is alive, CPU pegged on one core, HTTP timeouts.
- Cure: insert macrotask boundary every N iterations.

---

## 2. Plain-English restatement

A long chain or infinite loop of microtasks (`.then`, `queueMicrotask`, `await Promise.resolve()`) blocks all macrotasks. Timers don't fire, I/O callbacks don't run, HTTP requests time out. Process is alive but unresponsive. The cure: yield to a macrotask via `setImmediate` (Node) or `setTimeout(0)` (browser) periodically.

---

## 3. Why this matters in interviews

Production debugging skill — recognizing starvation in code review and logs. Event-loop intuition testable.

---

## 4. Mental model

```
   Priority (Node):
   1. process.nextTick queue   ← drains FIRST, fully
   2. microtask queue           ← drains SECOND, fully
   3. macrotask queue           ← finally, ONE callback

   Starvation = infinite producer in tier 1 or 2.

   ┌─ while(true) await Promise.resolve() ─┐
   │  each iter enqueues new microtask     │
   └────────────────────────────────────────┘
            ↓
   microtask queue refills forever
            ↓
   macrotask queue NEVER gets a turn
            ↓
   timers don't fire; I/O doesn't run; HTTP times out

   Cure pattern: insert macrotask boundary every N iterations.
     for (let i = 0; i < items.length; i++) {
       await process(items[i]);
       if (i % 1000 === 0) await new Promise(r => setImmediate(r));   ← macrotask yield
     }
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Does `await` yield to macrotask queue?
> 2. Will `setTimeout(cb, 100)` fire while `while(true) await Promise.resolve()` runs?
> 3. Why is 1M chained `.then`s also starvation?

---

## 6. Brute force — walked through

### Wrong attempt 1: "`async/await` yields"
Each `await` is a microtask hop — does NOT cross macrotask boundary.

### Wrong attempt 2: "`setTimeout(0)` is the same as `queueMicrotask`"
Different queues. `setTimeout` is macrotask; reintroduces fairness.

### Wrong attempt 3: "Node will preempt long chains"
Cooperative scheduling — no preemption. You yield or it starves.

---

## 7. The unlocking insight

> **Microtask starvation = unbounded producer in microtask/nextTick queue blocks all macrotasks. Cure: `await new Promise(r => setImmediate(r))` every N iterations to insert a macrotask boundary. Detect via event-loop lag monitoring.**

Three properties:

1. **Microtasks block macrotasks** until queue empties.
2. **`await` doesn't escape** — same queue.
3. **`setImmediate` or `setTimeout(0)`** creates fairness boundary.

---

## 8. Solution (annotated)

```js
// Cooperative yield helper
async function cooperative(items, fn, { yieldEvery = 1000 } = {}) {
  for (let i = 0; i < items.length; i++) {
    await fn(items[i], i);
    if (i % yieldEvery === 0) {                                       // step 1: periodic yield
      await new Promise((res) => (
        typeof setImmediate === 'function' ? setImmediate(res) : setTimeout(res, 0)
      ));
    }
  }
}

// Lag detection
let lastTick = Date.now();
setInterval(() => {                                                    // step 2: monitor
  const dt = Date.now() - lastTick;
  if (dt > 500) console.warn(`Event loop stalled ${dt}ms`);
  lastTick = Date.now();
}, 100).unref();
```

**Try it yourself**

```js
// BAD: starves all macrotasks for ~600ms
async function bad() {
  let p = Promise.resolve();
  for (let i = 0; i < 1_000_000; i++) p = p.then(() => i * 2);
  await p;
}

// GOOD: yields every 1000 iterations
async function good() {
  for (let i = 0; i < 1_000_000; i++) {
    // ... work ...
    if (i % 1000 === 0) await new Promise((r) => setImmediate(r));
  }
}

// Server still responds to /healthcheck during good().
```

---

## 9. Step-by-step dry run

```
Bad case: 100k Promise chain in HTTP handler

t=0     handler builds 100k .then chain synchronously (~5ms queue setup)
t=5ms   all microtasks queued; script returns
t=5ms   event loop: drain microtasks
          m1 runs (0.001ms) → schedules m2
          m2 runs → schedules m3
          ... 100k chained microtasks ...
          microtask queue NEVER empties until 100k drained
t=600ms drain complete; loop finally checks macrotasks
        meanwhile, /healthcheck request at t=10ms timed out (5s wait)

Symptom: p99 latency spike on unrelated routes; healthcheck flaps.

Good case: yield every 1000

t=0     handler queues 1000 .then → setImmediate → next 1000 → ...
t=5ms   first 1000 microtasks drain (~6ms); setImmediate runs
        → timers, I/O can interleave; healthcheck handled normally
t=600ms work done; total wall ≈ same, but loop stayed responsive
```

---

## 10. Common confusion + traps

1. **"`async/await` yields"** — microtask hop, not macrotask yield.
2. **"`setTimeout(0)` == `queueMicrotask`"** — different queues; setTimeout reintroduces fairness.
3. **"Node preempts long chains"** — cooperative only.
4. **"Starvation only with infinite loops"** — bounded 1M chains still freeze ~600ms.
5. **"`process.nextTick` is microtask"** — separate higher-priority queue (Node).
6. **"CPU peg = same as starvation"** — different; starvation can be low-CPU if each microtask is cheap.
7. **"Workers fix everything"** — they help for CPU work; don't help if you starve the worker's own loop.

---

## 11. Senior follow-ups & variants

### Variant 1 — `process.nextTick` recursion
Worse than microtask starvation — outranks MQ. See [nexttick-starvation.md](./nexttick-starvation.md).

### Variant 2 — Browser `setImmediate` polyfill
Use `MessageChannel.postMessage(0)` or `setTimeout(0)`.

### Variant 3 — AbortSignal-aware cooperative yield
Stop when external signal aborts. Cleaner cancellation.

### Variant 4 — Worker offload for CPU-bound
Move starving work entirely off main thread.

### Variant 5 — Detection via observability
`perf_hooks.monitorEventLoopDelay()` exposes percentile stats.

---

## 12. How to think aloud

> "Microtask starvation: unbounded producer of microtasks blocks macrotasks. Cause: `while(true) await Promise.resolve()`, recursive `queueMicrotask`, or 1M chained `.then`. Symptoms: CPU pegged on one core, timers don't fire, HTTP times out — process is alive but unresponsive. Detect via loop-lag instrumentation. Cure: insert `await new Promise(r => setImmediate(r))` periodically (every 1000 iterations) — that's a macrotask boundary. For nextTick recursion: switch to setImmediate. For CPU-bound: move to a worker. Trap: thinking `await` yields to macrotask — it doesn't; same queue."

---

## 13. 60-second revision

> - **Microtask starvation** = unbounded producer in MQ/NT queue.
> - **Symptoms:** CPU pegged, timers don't fire, HTTP times out — alive but unresponsive.
> - **`await` doesn't yield** to macrotask — same queue.
> - **Cure:** `await new Promise(r => setImmediate(r))` every N iters.
> - **Detect:** `perf_hooks.monitorEventLoopDelay()` or interval round-trip.
> - **Workers** for CPU-bound work.
> - **`process.nextTick` recursion** is worse (outranks MQ too).
> - **Trap:** "async/await yields"; "Node preempts"; bounded chains can't starve.

---

**Related:** [nexttick-starvation.md](./nexttick-starvation.md) · [queuemicrotask-deep-dive.md](./queuemicrotask-deep-dive.md) · [`10-machine-coding-patterns/scheduler-idle-callback.md`](../10-machine-coding-patterns/scheduler-idle-callback.md) · [worker-pool-implementation.md](./worker-pool-implementation.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
