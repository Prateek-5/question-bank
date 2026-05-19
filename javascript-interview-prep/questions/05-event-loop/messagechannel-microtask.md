# `MessageChannel` — fast macrotask yield primitive

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [queuemicrotask-deep-dive.md](./queuemicrotask-deep-dive.md), [setimmediate-vs-settimeout-in-io.md](./setimmediate-vs-settimeout-in-io.md)
>
> **Source:** WHATWG HTML spec; React Scheduler source; Vue/Lit schedulers. Senior frontend interviews.

---

## 1. Problem statement

What is `MessageChannel`, what scheduling tier does it post to, and why do React/Vue use it instead of `setTimeout(0)` or `queueMicrotask`?

**Verification examples**

| API                                | Tier             | Min delay              |
|------------------------------------|------------------|------------------------|
| `process.nextTick` (Node)          | nextTick         | none                   |
| `queueMicrotask` / `Promise.then`  | microtask        | none                   |
| `MessageChannel.postMessage`       | **macrotask**    | ~0ms (no clamp)        |
| `setTimeout(fn, 0)`                | macrotask        | 1ms (Node) / 4ms nested clamp (browser) |
| `setImmediate` (Node)              | check phase      | none                   |

**Constraints**
- `MessageChannel` posts a **macrotask** (task in HTML spec), NOT a microtask.
- React Scheduler uses it for sub-4ms yield to main thread.
- Posts in FIFO order within a single channel.
- Cleanup via `port.close()` for long-running services.

---

## 2. Plain-English restatement

Create a pair of `MessagePort` objects. Posting on one fires a `'message'` event on the other — as a **macrotask** (next "task" in HTML spec). Used by React, Vue, Lit schedulers because it's faster than `setTimeout(0)` (no clamp) AND yields to rendering (unlike `queueMicrotask`).

---

## 3. Why this matters in interviews

Senior-level question. The right answer admits `MessageChannel` is NOT a microtask. Production schedulers (React Fiber, Vue 3) use it specifically to yield to the browser between batches while staying faster than `setTimeout(0)`.

---

## 4. Mental model

```
   Why React doesn't use queueMicrotask for time-slicing:
   - Microtasks drain in SAME tick.
   - Browser never paints between microtasks.
   - Recursive microtask → frozen page.

   Why React doesn't use setTimeout(0):
   - 4ms clamp for nested timers (HTML5 spec).
   - React's slice is 5ms → 4ms clamp consumes most budget.

   MessageChannel solution:
   - postMessage queues a TASK (macrotask).
   - No clamp → next task fires sub-millisecond.
   - Yields to rendering between tasks.
   - 60fps stays smooth.

   const { port1, port2 } = new MessageChannel();
   port1.onmessage = (event) => doWork();
   port2.postMessage(0);     // queues task → port1.onmessage next macrotask
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Is `MessageChannel` a microtask or macrotask?
> 2. Why does React not use `queueMicrotask` for time-slicing?
> 3. Why faster than `setTimeout(0)`?

---

## 6. Brute force — walked through

### Wrong attempt 1: `setTimeout(0)` for yielding
4ms clamp kills perf at scale. React migrated away pre-2017.

### Wrong attempt 2: `queueMicrotask` for yielding
Microtasks drain in same tick → no rendering → frozen page.

### Wrong attempt 3: call it a "microtask scheduler"
It's a MACROtask. Easy to confuse.

---

## 7. The unlocking insight

> **`MessageChannel.postMessage` queues a macrotask with no clamp. Faster than `setTimeout(0)` (no 4ms minimum). Yields to rendering between tasks (unlike microtasks). React Fiber and Vue/Lit schedulers use it for cooperative time-slicing.**

Three properties:

1. **Macrotask, not microtask** — distinct from `queueMicrotask`.
2. **No clamp** — sub-millisecond between successive tasks.
3. **Yields to render** — browser paints between tasks.

---

## 8. Solution (annotated)

```js
// Minimal scheduler using MessageChannel
const channel = new MessageChannel();
const queue = [];
let scheduled = false;

channel.port1.onmessage = () => {                                     // step 1: handler
  scheduled = false;
  const tasks = queue.splice(0);                                       // snapshot
  for (const task of tasks) {
    try { task(); }
    catch (e) { setTimeout(() => { throw e; }); }                      // re-throw async
  }
};

function yieldToMain(fn) {
  queue.push(fn);
  if (scheduled) return;
  scheduled = true;
  channel.port2.postMessage(0);                                        // step 2: queue macrotask
}

console.log('sync 1');
queueMicrotask(() => console.log('microtask'));
yieldToMain(() => console.log('yielded 1'));
yieldToMain(() => console.log('yielded 2'));
setTimeout(() => console.log('setTimeout 4ms+'), 0);
console.log('sync 2');

// Output: sync 1, sync 2, microtask, yielded 1, yielded 2, setTimeout 4ms+
//   Sync first → microtask drain → MessageChannel task (sub-ms) → setTimeout (clamped)
```

**Try it yourself**

```js
// Node cross-thread (worker_threads)
const { Worker, MessageChannel } = require('node:worker_threads');
const { port1, port2 } = new MessageChannel();

const worker = new Worker(`
  const { parentPort } = require('node:worker_threads');
  parentPort.once('message', ({ port }) => {
    port.on('message', (msg) => port.postMessage('echo: ' + msg));
  });
`, { eval: true });

worker.postMessage({ port: port2 }, [port2]);        // transfer port2
port1.on('message', (msg) => console.log(msg));
port1.postMessage('hello');
// Logs: echo: hello
```

---

## 9. Step-by-step dry run

```
const ch = new MessageChannel();
ch.port1.onmessage = () => console.log('port1');
console.log('A');
ch.port2.postMessage('x');     // queues TASK (macrotask)
queueMicrotask(() => console.log('B'));  // queues MICROtask
console.log('C');

Sync:
  log 'A'
  postMessage → Macro=[task]
  queueMicrotask → MQ=[mt_B]
  log 'C'

Sync done. Drain MQ:
  mt_B → log 'B'

Browser pumps next task:
  task → port1.onmessage → log 'port1'

Output: A, C, B, port1

Microtask drains BEFORE MessageChannel task — different tiers.
```

---

## 10. Common confusion + traps

1. **"`MessageChannel` is a microtask scheduler"** — NO, macrotask.
2. **Forget `port.close()`** — long-running schedulers leak channels.
3. **`postMessage` without transferList** — copies large data; use transferables.
4. **Same as `setTimeout(0)`** — no clamp; sub-ms vs 1-4ms.
5. **Cancelling a posted message** — can't; ignore via generation counter.
6. **In browser** — global. **In Node** — from `worker_threads` (also global since Node 15).
7. **`port` GC'd without listener** — attach `onmessage` before posting.

---

## 11. Senior follow-ups & variants

### Variant 1 — Polyfill `requestIdleCallback`
Combine `MessageChannel` for yield + `performance.now()` for budget tracking.

### Variant 2 — Why no browser `setImmediate`?
IE/Edge legacy had it; others rejected. Standard replacement is essentially `MessageChannel`.

### Variant 3 — Backpressured queue between iframes
Port-based comms with explicit ack messages.

### Variant 4 — React Scheduler actual usage
Each slice does ~5ms work then `postMessage` to schedule next. Smooth 60fps.

### Variant 5 — `Scheduler.postTask` (new spec)
Chromium native API with priorities (`user-blocking`, `user-visible`, `background`). Future replacement.

---

## 12. How to think aloud

> "`MessageChannel` posts a macrotask (task in HTML spec), NOT a microtask. React/Vue/Lit schedulers use it because it's faster than `setTimeout(0)` (no 4ms nested-timer clamp) AND it yields to rendering between tasks (unlike `queueMicrotask`, which drains in same tick — frozen page). Idiom: `const {port1, port2} = new MessageChannel(); port1.onmessage = fn; port2.postMessage(0)`. In Node: from `worker_threads`, supports cross-thread + transferables for zero-copy. Cleanup with `port.close()`. Trap: calling it a microtask scheduler; forgetting `port.close()`; not using transferList for large data."

---

## 13. 60-second revision

> - **`MessageChannel` posts MACROTASK** (not microtask).
> - **Faster than `setTimeout(0)`** (no 4ms clamp).
> - **Yields to rendering** (unlike `queueMicrotask` — drains same tick).
> - **React/Vue schedulers** use it for cooperative time-slicing.
> - **Idiom:** `port1.onmessage = fn; port2.postMessage(0)`.
> - **Node:** `worker_threads.MessageChannel` — cross-thread + transferables.
> - **Cleanup:** `port.close()`.
> - **Trap:** "microtask scheduler"; missed transferList; uncleaned ports.

---

**Related:** [queuemicrotask-deep-dive.md](./queuemicrotask-deep-dive.md) · [setimmediate-vs-settimeout-in-io.md](./setimmediate-vs-settimeout-in-io.md) · [requestidlecallback-scheduling.md](./requestidlecallback-scheduling.md) · [`10-machine-coding-patterns/scheduler-idle-callback.md`](../10-machine-coding-patterns/scheduler-idle-callback.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
