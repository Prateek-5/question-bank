# Event Loop and Concurrency (Conceptual)

## Source
- codedamn: https://codedamn.com/news/javascript/event-loop-concurrency
- Canonical mental model used in every senior interview for Node/JS roles.

## Why this question matters in interviews
Every senior JS round opens with some flavor of "JavaScript is single-threaded but non-blocking — explain how." If you give a hand-wavy "it uses an event loop" answer, the bar is set low for the rest of the session. The correct answer in 90 seconds names: **call stack**, **Web APIs / libuv**, **task queue (macrotasks)**, **microtask queue**, **the rule that the microtask queue drains to empty between every macrotask**, and (for Node) **`process.nextTick` runs before microtasks**. Backend engineers also need to explain how I/O is offloaded: libuv's thread pool handles fs, dns, crypto; the kernel handles sockets via epoll/kqueue.

## Concepts involved

### The mental model
```
  ┌─────────────────────────┐
  │       Call Stack         │   single thread runs sync JS
  └────────────┬─────────────┘
               │ when empty
               ▼
  ┌─────────────────────────┐
  │   nextTick queue (Node)  │   drain to empty first
  ├─────────────────────────┤
  │   Microtask queue        │   then drain to empty
  │  (Promise jobs,          │
  │   queueMicrotask)        │
  └────────────┬─────────────┘
               │ pick ONE
               ▼
  ┌─────────────────────────┐
  │   Next libuv phase       │   timers → pending → poll → check → close
  │   (browser: task queue)  │
  └─────────────────────────┘
```

### Concurrency without threads
- **Concurrency vs parallelism** — JS gives you *concurrency* (multiple in-flight tasks interleaved) without *parallelism* (multiple cores running JS at once). All JS code in a single isolate runs on one thread.
- **Parallelism IS available** via: `worker_threads` (Node), Web Workers (browser), `cluster` (Node multi-process), libuv's internal thread pool (used for fs / crypto / dns — but only the C++ side is parallel; the JS callback always queues back on the main thread).
- **Non-blocking I/O** — when JS calls `fs.readFile`, Node hands the syscall to libuv. libuv either uses the kernel's async API (epoll for sockets) or its 4-thread default pool (for fs). The main thread returns to the event loop immediately. When the syscall completes, the callback is queued in libuv's **poll phase**.

### Priority order (Node, exact)
1. **Current sync code** finishes on the call stack.
2. **`process.nextTick` queue** drains completely.
3. **Microtask queue** drains completely (Promise `.then` / `.catch` / `.finally`, `queueMicrotask`, `await` continuations).
4. **Next libuv phase** picks ONE callback from its queue and runs it.
5. After that callback, repeat from step 2 (nextTick + microtasks drain between every single phase callback).

The "drain to empty" rule for microtasks is the most common interview gotcha. It means an infinite `Promise.resolve().then(loop)` chain **starves all I/O** indefinitely.

### Browser vs Node differences
- Browser has a single "task queue" (timers, DOM events, fetch callbacks, etc.) and a single microtask queue. No phases, no `process.nextTick`. Animation frames live in their own queue serviced by `requestAnimationFrame`.
- Node has six libuv phases (timers / pending / idle-prepare / poll / check / close) plus the `nextTick` queue (not part of libuv) and the microtask queue (V8-managed).
- `setImmediate` only exists in Node (it runs in the **check** phase).

### Edge cases (interview traps)
1. **`Promise.resolve().then(...)` runs before `setTimeout(..., 0)`.** Microtask drains before next macrotask.
2. **`await` is sugar for `.then`.** Code after `await` runs in a microtask.
3. **`process.nextTick` runs before Promise jobs.** Yes, even before `Promise.resolve().then`.
4. **Microtask starvation** — recursively scheduling microtasks blocks the entire libuv loop. Same for `process.nextTick` (even more aggressively).
5. **`setImmediate` vs `setTimeout(0)`** — non-deterministic order from main module, deterministic (immediate first) from inside an I/O callback.
6. **Long sync work blocks everything** — including microtasks. Single-threaded means single-threaded.
7. **`async` function called synchronously** runs synchronously up to the first `await`, THEN suspends — common bug source.

## Brute force approach
"Everything is a callback queue, JS picks one at a time." This misses the macrotask/microtask split entirely. If the interviewer asks "what runs first, `setTimeout(fn, 0)` or `Promise.resolve().then(fn)`?" you'll get it wrong. Don't lead with this answer.

## Optimal approach
Lead with the four-layer model: **stack → nextTick → microtask → next phase**. Then explain that microtasks drain to empty between every macrotask (this is the load-bearing fact). Mention libuv phases by name for Node. Show that you know `Promise.resolve().then` beats `setTimeout(0)`. Close with how I/O is offloaded to libuv's thread pool / kernel epoll.

## Solution (JavaScript)

```js
// Canonical demonstration: explains everything in one snippet.
console.log('1. sync start');

setTimeout(() => console.log('5. setTimeout(0)'), 0);
setImmediate(() => console.log('6. setImmediate'));      // Node only

Promise.resolve().then(() => console.log('4. promise.then (microtask)'));

process.nextTick(() => console.log('3. process.nextTick'));  // Node only

console.log('2. sync end');

// Predicted output (Node, from main module):
// 1. sync start
// 2. sync end
// 3. process.nextTick
// 4. promise.then (microtask)
// 5. setTimeout(0)        ← order with setImmediate non-deterministic from main
// 6. setImmediate         ← but DETERMINISTIC inside an I/O callback (immediate first)
```

```js
// What "non-blocking I/O" actually means
const fs = require('node:fs');

console.log('A');
fs.readFile('/etc/hosts', () => {
  console.log('D — runs in libuv poll phase callback');
  setTimeout(() => console.log('F — timers phase'), 0);
  setImmediate(() => console.log('E — check phase, DETERMINISTIC here'));
});
console.log('B');
Promise.resolve().then(() => console.log('C — microtask, drains before any phase'));

// Output:
// A
// B
// C
// D
// E    (setImmediate beats setTimeout when scheduled from inside an I/O cb)
// F
```

## Step-by-step dry run

For the first snippet:

| Tick | Call stack | nextTick Q | Microtask Q | Timers | Check (setImmediate) |
|------|-----------|------------|-------------|--------|----------------------|
| 0 | `console.log('1.')` | — | — | — | — |
| 0 | `setTimeout` registers `fn5` | — | — | `[fn5]` | — |
| 0 | `setImmediate` registers `fn6` | — | — | `[fn5]` | `[fn6]` |
| 0 | `.then` enqueues `fn4` | — | `[fn4]` | `[fn5]` | `[fn6]` |
| 0 | `process.nextTick` enqueues `fn3` | `[fn3]` | `[fn4]` | `[fn5]` | `[fn6]` |
| 0 | `console.log('2.')` | `[fn3]` | `[fn4]` | `[fn5]` | `[fn6]` |
| 0 | stack empty → drain nextTick | run `fn3` → log `3.` | `[fn4]` | `[fn5]` | `[fn6]` |
| 0 | nextTick empty → drain microtasks | — | run `fn4` → log `4.` | `[fn5]` | `[fn6]` |
| 1 | enter timers phase | — | — | run `fn5` → log `5.` | `[fn6]` |
| 1 | enter check phase | — | — | — | run `fn6` → log `6.` |

Output: `1, 2, 3, 4, 5, 6`. (The 5/6 order can flip from main module due to timer arming jitter; it's deterministic inside an I/O callback.)

## Important takeaways

**The 4 layers (memorize)**
1. Call stack (sync)
2. `process.nextTick` queue (Node only)
3. Microtask queue (Promise jobs, `queueMicrotask`)
4. Macrotask: one callback from the next libuv phase / browser task queue

Layers 2 + 3 drain **completely** between each step of layer 4.

**The 6 libuv phases (memorize the names + one example each)**
1. **timers** — `setTimeout`, `setInterval` callbacks
2. **pending callbacks** — deferred system errors (e.g., TCP ECONNREFUSED)
3. **idle, prepare** — internal libuv housekeeping
4. **poll** — I/O callbacks (fs, net) + blocking wait for new I/O
5. **check** — `setImmediate` callbacks
6. **close callbacks** — `socket.on('close', ...)`

**Concurrency model — one-liners**
- "JS is single-threaded; concurrency is achieved by *cooperative interleaving* of callbacks on the event loop."
- "Parallelism requires `worker_threads`, `cluster`, or Web Workers."
- "libuv uses a 4-thread pool (configurable via `UV_THREADPOOL_SIZE`) for fs/dns/crypto and kernel epoll/kqueue for sockets."

**Common mistakes**
- Saying "the event loop runs in a separate thread" — it doesn't, it IS the main thread.
- Saying "Promise.then puts work on a background thread" — no, it's a microtask on the SAME thread.
- Forgetting that microtasks drain between phases (not just after sync code).
- Conflating `process.nextTick` with `setImmediate`. They are very different.

## Variants

1. **Output prediction** — interviewer dumps a snippet with mixed `setTimeout`, `Promise`, `await`, `process.nextTick`. See `microtask-macrotask-order.md` and `nexttick-vs-setimmediate.md`.

2. **"How would you parallelize CPU work?"** — answer: `worker_threads` for compute; pass data via `postMessage` or `SharedArrayBuffer` for zero-copy.

3. **"What's the difference between `node` and `bun`/`deno`?"** — they replace libuv with their own loops (Bun uses `uvloop`-like, Deno uses tokio). Same conceptual model, different implementation.

4. **"How does `cluster` differ from `worker_threads`?"** — cluster forks processes (separate event loops, IPC); worker_threads share the process but have separate isolates.

## Revision notes

> **event-loop-concurrency — 60 second recap**
> - **Single thread, single call stack.** Concurrency via interleaved callbacks.
> - **Priority:** stack → `process.nextTick` → microtasks → next libuv phase.
> - Microtasks **drain to empty** between every macrotask — most common gotcha.
> - **6 libuv phases:** timers, pending, idle/prepare, poll, check, close.
> - `setImmediate` → check phase. `setTimeout(0)` → timers phase.
> - I/O is offloaded to libuv thread pool (fs/dns/crypto) or kernel epoll (sockets).
> - Parallelism: `worker_threads`, `cluster`, or `child_process`.
> - **Trap:** infinite microtask chain starves I/O. Same for `process.nextTick` (worse).
> - **Trap:** `async` fn runs sync up to first `await`, then suspends.
