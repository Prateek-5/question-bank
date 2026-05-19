# Event Loop and Concurrency — the four-layer mental model

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [`concepts/event-loop.md`](../../concepts/event-loop.md), [`concepts/promises.md`](../../concepts/promises.md)
>
> **Source:** Canonical opener for every senior JS/Node round.

---

## 1. Problem statement

Explain how JavaScript achieves concurrency on a single thread. Be specific about: call stack, microtask queue, macrotask queue (libuv phases in Node), `process.nextTick`, and the rule that microtasks drain to empty between every macrotask.

**Verification examples**

| Question                                                         | Correct answer                                          |
|------------------------------------------------------------------|---------------------------------------------------------|
| What runs first: `Promise.resolve().then(fn)` or `setTimeout(fn, 0)`? | `Promise.then` — microtask drains before next macrotask |
| What's the priority of `process.nextTick`?                        | Higher than microtasks; Node-specific queue            |
| How many libuv phases are there?                                   | 6: timers, pending, idle/prepare, poll, check, close   |
| Does the event loop run on a separate thread?                      | No — it IS the main thread                              |
| How does `fs.readFile` "not block"?                                | Dispatches to libuv thread pool; cb queued in poll phase |

**Constraints**
- JS is single-threaded; concurrency = interleaved callbacks.
- Parallelism requires `worker_threads`, `cluster`, or Web Workers.
- Microtasks drain to empty between every macrotask.
- `process.nextTick` outranks microtasks.

---

## 2. Plain-English restatement

JavaScript runs on one thread. To stay responsive, it doesn't *do* the work for I/O — it hands it to libuv (or browser APIs) and continues. When the work completes, a callback is queued. The event loop is a scheduler that picks one callback at a time from prioritized queues. The headline rule: **all currently-queued microtasks run before the next macrotask**.

---

## 3. Why this matters in interviews

A hand-wavy "it uses an event loop" answer sets a low bar for the rest of the session. The senior answer names the four layers: **stack → nextTick → microtask → next phase** — and explains microtasks drain to empty between every macrotask.

---

## 4. Mental model

```
   ┌─────────────────────────┐
   │       Call Stack         │   single thread runs sync JS
   └────────────┬─────────────┘
                │ when empty
                ▼
   ┌─────────────────────────┐
   │  process.nextTick (Node) │   drain to empty FIRST
   ├─────────────────────────┤
   │  Microtask queue         │   then drain to empty
   │  (Promise.then,          │
   │   queueMicrotask, await) │
   └────────────┬─────────────┘
                │ pick ONE
                ▼
   ┌─────────────────────────┐
   │  Next libuv phase        │   timers → pending → poll → check → close
   │  (browser: task queue)   │
   └─────────────────────────┘

   Between EVERY single phase callback: re-drain nextTick + microtask.

   libuv phases (Node):
   1. timers          setTimeout / setInterval
   2. pending cb's    deferred system errors
   3. idle / prepare  internal libuv
   4. poll            I/O callbacks (fs, net); BLOCKS here
   5. check           setImmediate
   6. close           'close' events
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What's the output of `setTimeout(()=>log(1),0); Promise.resolve().then(()=>log(2)); log(3)`?
> 2. What runs first: `process.nextTick(fn)` or `Promise.resolve().then(fn)`?
> 3. Why does `for(;;){}` block timers?

---

## 6. Brute force — walked through

### Wrong attempt 1: "everything's a queue, picks one at a time"
Misses microtask/macrotask split. Can't predict ordering.

### Wrong attempt 2: "the event loop runs in a background thread"
No — IS the main thread.

### Wrong attempt 3: "Promise.then runs on a worker"
No — microtask on the same thread.

---

## 7. The unlocking insight

> **Four priority layers: (1) sync stack, (2) `process.nextTick`, (3) microtasks, (4) one macrotask. Layers 2+3 drain to EMPTY between every macrotask.**

Three properties:

1. **Microtasks drain to empty** — most common interview gotcha.
2. **`nextTick > microtasks`** — Node-specific.
3. **I/O offloaded** to libuv thread pool (fs/dns/crypto) or kernel epoll (sockets).

---

## 8. Solution (annotated)

```js
console.log('1: sync start');

setTimeout(() => console.log('5: setTimeout(0)'), 0);                // step 1: macrotask (timers)
setImmediate(() => console.log('6: setImmediate'));                  // step 2: macrotask (check, Node)

Promise.resolve().then(() => console.log('4: promise.then'));        // step 3: microtask

process.nextTick(() => console.log('3: process.nextTick'));          // step 4: nextTick (Node)

console.log('2: sync end');

// Output (Node, main module):
// 1: sync start
// 2: sync end
// 3: process.nextTick                ← drained first
// 4: promise.then                    ← microtask drain
// 5: setTimeout(0)                   ← order vs 6 non-deterministic from main
// 6: setImmediate                    ← inside I/O cb, 6 always beats 5
```

**Try it yourself**

```js
const fs = require('node:fs');

console.log('A');
fs.readFile('/etc/hosts', () => {
  console.log('D — poll phase');
  setTimeout(() => console.log('F'), 0);
  setImmediate(() => console.log('E — check (deterministic here)'));
});
console.log('B');
Promise.resolve().then(() => console.log('C'));

// A, B, C, D, E, F (setImmediate beats setTimeout inside I/O cb)
```

---

## 9. Step-by-step dry run

```
Walk the first snippet's queues:

Sync execution:
  log '1'
  register setTimeout cb5 → Timers=[cb5]
  register setImmediate cb6 → Check=[cb6]
  schedule promise.then cb4 → MQ=[cb4]
  schedule nextTick cb3 → NT=[cb3]
  log '2'

Sync done; drain queues:
  drain NT: run cb3 → log '3'. NT=[].
  drain MQ: run cb4 → log '4'. MQ=[].

Loop iteration:
  Timers phase: run cb5 → log '5'. Then drain NT/MQ (empty).
  Check phase:  run cb6 → log '6'. Then drain NT/MQ.

Output: 1, 2, 3, 4, 5, 6 (5 vs 6 can flip from main due to timer-arm jitter).
```

---

## 10. Common confusion + traps

1. **"Event loop runs in another thread"** — no, IS main thread.
2. **"Promise.then is on a worker"** — no, microtask same thread.
3. **Microtasks drain only at end of sync** — no, between every phase callback (Node 11+).
4. **`process.nextTick` is a microtask** — no, separate higher-priority queue.
5. **Infinite microtask chain** — starves all macrotasks (I/O, timers).
6. **`async` fn runs entirely later** — no, sync up to first `await`, then suspends.
7. **`setImmediate` vs `setTimeout(0)` from main is deterministic** — non-deterministic; deterministic only inside I/O cb.

---

## 11. Senior follow-ups & variants

### Variant 1 — "How parallelize CPU work?"
`worker_threads` for compute; pass data via `postMessage` or `SharedArrayBuffer` for zero-copy.

### Variant 2 — `cluster` vs `worker_threads`
Cluster forks processes (separate event loops, IPC); worker_threads share process, separate V8 isolates.

### Variant 3 — Bun/Deno vs Node
Replace libuv with their own loops (Bun: `uvloop`-like, Deno: tokio). Same conceptual model.

### Variant 4 — `UV_THREADPOOL_SIZE`
Defaults to 4; tune for crypto-heavy workloads.

### Variant 5 — Event-loop lag measurement
`perf_hooks.monitorEventLoopDelay()` or schedule `setImmediate` and measure delta.

---

## 12. How to think aloud

> "Single-threaded, single call stack. Concurrency via interleaved callbacks. Priority: stack → `process.nextTick` → microtasks → next libuv phase callback. Between every phase callback, re-drain nextTick + microtasks. Six libuv phases: timers, pending, idle/prepare, poll, check, close. `setImmediate` → check; `setTimeout(0)` → timers. I/O offloaded to libuv thread pool (fs/dns/crypto) or kernel epoll (sockets). Parallelism via `worker_threads`, `cluster`, or Web Workers. Trap: infinite microtask chain starves I/O. Trap: `async` fn runs sync until first await."

---

## 13. 60-second revision

> - **4 layers:** stack → nextTick → microtask → one macrotask.
> - **Microtasks drain to empty** between every macrotask (Node 11+).
> - **6 libuv phases:** timers, pending, idle/prepare, poll, check, close.
> - **`setImmediate`** → check; **`setTimeout(0)`** → timers.
> - **I/O offloaded** to libuv thread pool or kernel epoll.
> - **Parallelism:** worker_threads, cluster, Web Workers.
> - **Trap:** "event loop is another thread"; infinite microtask chain starves I/O; `async` runs sync up to first `await`.

---

**Related:** [microtask-macrotask-order.md](./microtask-macrotask-order.md) · [nodejs-event-loop-phases.md](./nodejs-event-loop-phases.md) · [nexttick-vs-setimmediate.md](./nexttick-vs-setimmediate.md) · [predict-mixed-async-output.md](./predict-mixed-async-output.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
