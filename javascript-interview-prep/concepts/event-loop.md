# Event Loop (Browser + Node.js / libuv)

## TL;DR
- **The event loop is JS's mechanism to handle async work on a single thread**: pick a task → run to completion → drain microtasks → repeat.
- Two queues per turn (browser): **macrotask queue** (timers, I/O, UI events) + **microtask queue** (Promise jobs, `queueMicrotask`, `MutationObserver`). Microtasks drain fully between macrotasks.
- Node.js uses **libuv** with phases: timers → pending callbacks → idle/prepare → poll → check (`setImmediate`) → close. `process.nextTick` and microtasks run between *every* phase transition.
- **Blocking the loop = blocking the server.** CPU-bound work belongs in worker threads, child processes, or off-process.
- Priority (Node): `process.nextTick` > microtasks (Promise) > `setTimeout(0)`/`setImmediate` depending on phase.

## Why backend interviewers care
- Node.js single-threaded model makes event-loop literacy non-negotiable for senior backend roles.
- Latency outliers, p99 spikes, and "the server hangs sometimes" almost always trace to loop blocking or microtask starvation.
- Output-prediction questions on `setTimeout` vs `Promise` vs `process.nextTick` are interview staples.

## Core mental model

### Browser (HTML spec)
The agent runs in a loop:
1. Pick **one** task from the macrotask queue.
2. Execute it to completion (no preemption).
3. Drain the **entire** microtask queue.
4. Render if needed.
5. Go to 1.

Microtasks chain: if a microtask enqueues another, the new one runs in the *same* drain. This is how Promise chains feel synchronous.

### Node.js (libuv) — phases in order each tick
1. **timers** — `setTimeout`/`setInterval` callbacks whose threshold elapsed.
2. **pending callbacks** — some system errors deferred.
3. **idle, prepare** — internal.
4. **poll** — retrieves new I/O events; executes their callbacks; may block here.
5. **check** — `setImmediate` callbacks.
6. **close callbacks** — `socket.on('close', ...)`.

Between **every** phase transition (and after each callback in some phases), Node drains:
- the entire `process.nextTick` queue,
- then the entire microtask (Promise) queue.

So `process.nextTick` has higher priority than `Promise.then`. Both can **starve** the loop if recursive.

```js
setTimeout(() => console.log("timeout"), 0);
setImmediate(() => console.log("immediate"));
Promise.resolve().then(() => console.log("promise"));
process.nextTick(() => console.log("nextTick"));
console.log("sync");

// sync
// nextTick
// promise
// timeout  (or immediate first — depends on context)
// immediate
```

`setTimeout(fn, 0)` vs `setImmediate(fn)` ordering is **non-deterministic when called from the main module** (depends on whether the timers phase has a minimum 1ms threshold reached). Inside an I/O callback, `setImmediate` always wins (poll → check is the next phase).

### Why "blocking" matters
Every CPU-heavy synchronous function — JSON.parse on a 50MB payload, a regex with catastrophic backtracking, bcrypt.hashSync — freezes the entire process. No requests can be accepted, no timers fire, no I/O completes. Use `worker_threads`, `crypto.randomBytes` (async), `bcrypt` async APIs, or stream the work.

## Syntax cheat sheet
```js
// Schedule a macrotask
setTimeout(() => console.log("t0"), 0);
setInterval(() => {}, 1000);

// Node-only macrotask in 'check' phase
setImmediate(() => console.log("imm"));

// Microtask
queueMicrotask(() => console.log("micro"));
Promise.resolve().then(() => console.log("promise micro"));

// Node-only: runs BEFORE microtasks, between phases
process.nextTick(() => console.log("nt"));

// Async iteration on the loop without blocking — yield often
async function chunked(items) {
  for (let i = 0; i < items.length; i++) {
    process(items[i]);
    if (i % 1000 === 0) await new Promise(r => setImmediate(r));
  }
}

// CPU offload — worker thread
const { Worker } = require("worker_threads");
new Worker("./hash.js", { workerData: payload });

// AbortController + signal — cancellation through the loop
const ac = new AbortController();
setTimeout(() => ac.abort(), 5000);

// Detecting loop lag (simple)
let last = Date.now();
setInterval(() => {
  const now = Date.now();
  const lag = now - last - 100;
  if (lag > 50) console.warn("loop lag", lag, "ms");
  last = now;
}, 100);

// AsyncLocalStorage — per-async-context state
const { AsyncLocalStorage } = require("async_hooks");
const als = new AsyncLocalStorage();
als.run({ reqId: "abc" }, () => { /* nested async calls see store */ });
```

## Edge cases & interview traps
1. **`setTimeout(fn, 0)` is NOT 0ms** — minimum 1ms in Node, 4ms after several nested timers in browsers.
2. **`Promise.resolve().then` runs before `setTimeout(0)`** — microtasks beat macrotasks.
3. **`process.nextTick` is NOT a microtask** — it's a Node-specific queue checked before microtasks.
4. **Microtask starvation**: a tight `Promise.resolve().then(self)` loop prevents any macrotask (incl. I/O) from running.
5. **`setImmediate` vs `setTimeout(0)`**: in an I/O callback, immediate wins; in main, indeterminate.
6. **Async functions return on the *next* microtask** even if they have no `await` — `async () => 1` resolves async-ly.
7. **`await` always yields**, even for non-promises — minimum one microtask tick per `await`.
8. **Long sync work blocks ALL connections** — including the keep-alive heartbeat; clients see timeouts.
9. **`crypto.randomBytes(N)` async vs sync** — sync version blocks; use async for high N.
10. **`fs.readFileSync` in a request handler** is the classic mistake — convert to `fs.promises.readFile`.
11. **`unref()`** on timers/sockets lets the process exit even if they're pending.
12. **Server.close() waits for active connections** — combine with keep-alive timeouts to drain.
13. **`setInterval` drift** — callbacks queue up if the loop is busy; use a self-rescheduling `setTimeout` for accuracy.
14. **`process.on('uncaughtException', ...)`** is a last-resort log-and-exit hook — Node may be in a corrupt state.
15. **Cluster vs worker_threads**: cluster forks processes (separate memory); worker_threads share memory via `SharedArrayBuffer`. Use cluster for I/O-bound horizontal scale, workers for CPU.
16. **`AsyncLocalStorage`** is the right way to do request-scoped context — survives across `await` boundaries via `async_hooks`.
    ```js
    als.run({ reqId: "r1" }, async () => {
      await db.query(...);              // store still visible
      als.getStore();                   // { reqId: "r1" }
    });
    ```

## Interview worked examples

### Example 1 — Predict mixed setTimeout / Promise / nextTick output
**Asked as:** "Walk me through what this prints in Node, in order."

I'd say: "Sync logs run first. Then between phases, Node drains nextTick (highest priority) and then microtasks (Promise.then). Macrotasks (setTimeout, setImmediate) run on their own phases after."

```js
setTimeout(() => console.log("timeout"), 0);
Promise.resolve().then(() => console.log("promise"));
process.nextTick(() => console.log("nextTick"));
console.log("sync");

// Output:
// sync
// nextTick
// promise
// timeout
```

**What the interviewer is testing:** Microtask vs macrotask vs nextTick priority.
**Sharp follow-up they often ask:** "Add `setImmediate` — where does it land?" → After timeout (or before, in main context — non-deterministic w/ setTimeout(0)).

### Example 2 — `setImmediate` vs `setTimeout(0)` inside an I/O callback
**Asked as:** "Inside `fs.readFile` callback, which fires first?"

I'd say: "In an I/O (poll-phase) callback, `setImmediate` ALWAYS wins. The next phase after poll is check, where setImmediate runs. Timers must wait for the next loop turn. In the main module, the ordering is non-deterministic because we don't know if the timers threshold has elapsed."

```js
const fs = require("fs");
fs.readFile(__filename, () => {
  setTimeout(() => console.log("timeout"), 0);
  setImmediate(() => console.log("immediate"));
});
// Always:
// immediate
// timeout
```

**What the interviewer is testing:** libuv phase order; deterministic ordering inside I/O.
**Sharp follow-up they often ask:** "Why is ordering non-deterministic from the main module?" → setTimeout has minimum 1ms; if event-loop entry is < 1ms in, timer hasn't elapsed → immediate wins; else timer wins.

### Example 3 — `queueMicrotask` vs `Promise.resolve().then`
**Asked as:** "Are these identical? Predict order."

I'd say: "Both schedule a microtask in the same queue, in registration order. `queueMicrotask` is the explicit, lighter API — no Promise allocation. Functionally interchangeable for ordering."

```js
Promise.resolve().then(() => console.log("a"));
queueMicrotask(() => console.log("b"));
Promise.resolve().then(() => console.log("c"));
// Output: a, b, c — same queue, FIFO
```

**What the interviewer is testing:** Microtask queue is a single queue regardless of API.
**Sharp follow-up they often ask:** "When would you prefer `queueMicrotask`?" → No promise allocation; explicit signal to readers; doesn't create unhandled-rejection risk.

### Example 4 — `await` ordering inside an async function
**Asked as:** "Predict the output."

I'd say: "Inside `f`, the sync part runs up to the await. The awaited expression returns a Promise; the continuation after `await` is scheduled as a microtask. Meanwhile, the rest of the top-level sync code runs, then microtasks drain."

```js
async function f() {
  console.log("1");
  await Promise.resolve();
  console.log("3");
}
f();
console.log("2");
// Output: 1, 2, 3
```

**What the interviewer is testing:** Every `await` yields one microtask, even on resolved values.
**Sharp follow-up they often ask:** "What if I add `console.log('4')` after `f()` and another await inside f?" → walk through extra microtask scheduling.

### Example 5 — CPU-bound work blocking the loop
**Asked as:** "Why does my Express server stop responding when this runs?"

I'd say: "A sync CPU-heavy loop blocks the only JS thread. While it runs, no I/O callbacks, no timers, no incoming requests are handled. Even pending Promise.then callbacks wait. Two fixes: yield to the loop with `setImmediate`, or offload to a worker_thread."

```js
// BLOCKS:
function hashBlocking() {
  for (let i = 0; i < 1e10; i++) { /* burn */ }
}

// YIELDS:
async function hashCooperative() {
  for (let i = 0; i < 1e10; i++) {
    if (i % 1e6 === 0) await new Promise(r => setImmediate(r));
  }
}
```

**What the interviewer is testing:** Single-threaded model awareness; cooperative yielding pattern.
**Sharp follow-up they often ask:** "When does yielding NOT work?" → If the work is one indivisible computation (e.g. bcrypt's internal loop) — must use worker_threads or async-native APIs.

### Example 6 — Microtask starvation
**Asked as:** "What happens if I recursively schedule microtasks?"

I'd say: "Microtasks drain fully before the next macrotask. A recursive Promise.then chain (or repeated `process.nextTick`) prevents timers and I/O from ever running — the loop is starved. The process appears to hang from outside. The fix is to schedule the next iteration via setImmediate/setTimeout."

```js
let count = 0;
function starve() {
  if (++count < 1e6) Promise.resolve().then(starve);
}
starve();
setTimeout(() => console.log("never logs until starve finishes"), 0);
```

**What the interviewer is testing:** Microtask queue can monopolize the loop.
**Sharp follow-up they often ask:** "How would you detect this in production?" → `perf_hooks.monitorEventLoopDelay()` — sustained high lag is the signal.

## Common machine-coding patterns
- **Output-ordering question** — when used: every JS interview ever. Sketch: mix `setTimeout(0)`, `setImmediate`, `Promise.then`, `process.nextTick`, sync logs. Walk through phases.
- **Cooperative chunking for big work** — when used: processing 1M-row CSV. Sketch:
  ```js
  for (let i = 0; i < n; i++) {
    work(i);
    if (i % 1000 === 0) await new Promise(r => setImmediate(r));
  }
  ```
- **Loop-lag monitor** — sketch above. Production: `perf_hooks.monitorEventLoopDelay()`.
- **Polyfill `setImmediate` in browser** — when used: code portability. Sketch:
  ```js
  const setImm = (fn) => Promise.resolve().then(fn); // microtask, not exact
  // exact: postMessage trick
  ```
- **Async semaphore using event loop** — pair with promise pool (see promises.md).

## Backend-specific notes
A healthy Node server keeps the loop lag under ~10ms. Above 50ms you'll see request latency spikes; above 200ms you have an outage. Tools: `clinic doctor`, `perf_hooks.monitorEventLoopDelay`, Datadog's runtime metrics.

**Don't block on**: synchronous file I/O, large `JSON.parse`/`stringify` (use streaming with `stream-json` or `JSONStream`), `crypto.pbkdf2Sync`, `zlib.*Sync`, regex with catastrophic backtracking, deeply recursive functions on big inputs.

**`AsyncLocalStorage`** replaces "this" or "request-context" libraries — works across async boundaries because Node tracks async resources via `async_hooks`. Cost is small but nonzero; benchmark for ultra-hot paths.

**Cluster** forks one process per core (`os.cpus().length`), each with its own loop. **Worker threads** share the parent's process but run on their own loop — ideal for CPU work without IPC overhead.

## 60-second revision (day-before)
```text
┌──────────────────────────────────────────────────────────┐
│ EVENT LOOP — DAY-BEFORE CRAM                             │
├──────────────────────────────────────────────────────────┤
│ • Loop = pick task → run → drain microtasks → repeat     │
│ • Node phases: timers → pending → poll → check → close   │
│ • Between each phase: nextTick queue, then microtasks    │
│ • Priority (Node): nextTick > Promise > timer/immediate  │
│ • setTimeout(0) min 1ms (Node), 4ms (nested, browser)    │
│ • setImmediate wins over setTimeout(0) inside I/O cb     │
│ • async fn returns on next microtask even w/o await      │
│ • Microtask & nextTick can STARVE the loop               │
│ • Block the loop = block ALL connections                 │
│ • CPU work → worker_threads or child_process             │
│ • use fs/promises, never *Sync in handlers               │
│ • loop-lag monitor: setInterval drift > 50ms = bad       │
│ • AsyncLocalStorage = per-request context                │
│ • cluster = process per CPU; worker = thread             │
│ • unref() to allow process exit                          │
└──────────────────────────────────────────────────────────┘
```
