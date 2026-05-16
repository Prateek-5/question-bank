# Event Loop (Browser + Node.js / libuv)

> **Senior-mentor framing:** JavaScript is a single-threaded language, but the runtime around it (the browser or Node.js) is not. The "event loop" is the choreography that lets a one-threaded language *feel* concurrent without actually running two pieces of JS at the same instant. Understand this and 80% of "weird async output" questions become trivial.

## Why this concept exists (first principles)

Imagine a restaurant kitchen with **one chef** (the JS thread). The chef can do exactly one thing at a time. But many orders (tasks) keep coming in: timers firing, network responses arriving, user clicks, Promise resolutions.

If the chef tried to do everything *immediately* whenever an order arrived, two orders arriving at the same time would collide. So instead:

- Orders go into a **queue**.
- The chef finishes the current dish completely (run-to-completion).
- Then picks the next order from the queue.
- Some "priority" orders (microtasks, `process.nextTick`) jump the line — they're checked after **every** dish before the next regular order.

That choreography is the event loop. The "kitchen" (libuv in Node, the HTML spec in browsers) handles all the *waiting* — for timers, sockets, files — on background threads, and only hands JS work back to the chef when it's ready to run.

> **Mental Model — the loop in one sentence:** Run one task to completion, drain ALL microtasks, repeat. The macrotask queue is the menu of dishes; the microtask queue is the "before next dish, do these tiny things" list.

## Why interviewers care

- Node.js single-threaded model makes event-loop literacy non-negotiable for senior backend roles.
- Latency outliers, p99 spikes, and "the server hangs sometimes" almost always trace to loop blocking or microtask starvation.
- Output-prediction questions on `setTimeout` vs `Promise` vs `process.nextTick` are interview staples.
- It's the single best way to separate a *coder* from someone who *understands the runtime*. Anyone can write `await fetch(...)`; few can explain when its continuation actually runs.

## Common beginner confusion

- "JavaScript is multi-threaded because of `setTimeout`." — **No.** `setTimeout` schedules a callback on a timer thread inside the runtime; the JS thread is still alone when the callback runs.
- "`setTimeout(fn, 0)` runs immediately." — **No.** It runs *after* the current sync code AND after all pending microtasks. Minimum delay is 1ms (Node) or 4ms (nested in browsers).
- "Promises run in parallel." — **No.** The async *work* (fetch, fs) happens off-thread, but the `.then` callback always runs on the same single JS thread.
- "`process.nextTick` is a microtask." — **No.** It's a Node-specific queue with *higher priority* than microtasks.
- "Microtasks and macrotasks are the same queue." — **No.** They're separate; the microtask queue is fully drained between every macrotask.

## Progressive concept building

**Beginner level:** "There's a stack for sync code and a queue for async callbacks. When the stack is empty, the loop pops the next callback."

**Intermediate level:** "There are *two* queues — microtasks and macrotasks. Microtasks drain completely between macrotasks. Promises go to microtasks; timers and I/O go to macrotasks."

**Advanced level:** "Node has libuv with six phases, and between every phase Node drains the `nextTick` queue, then the microtask queue. `setImmediate` is a separate phase from timers; their ordering depends on whether you're in main or in an I/O callback."

**Interview expectation:** You should be able to *predict the output* of any mix of `setTimeout`, `setImmediate`, `Promise.then`, `process.nextTick`, `await`, and sync logs, AND explain *why* phase-by-phase.

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

> **Mental Model — Browser vs Node:** Browser = simple two-queue dance (macro + micro). Node = same idea but the macrotask side is split into **phases**, each phase being its own mini-queue. The microtask drain rule applies between phases too.

### Picture it: the full machinery

```
   ┌───────────────────────────────────────────────────────────────┐
   │                       JS RUNTIME                              │
   │                                                               │
   │   ┌─────────────┐         ┌──────────────────────────────┐    │
   │   │  CALL STACK │  <----  │   currently executing task   │    │
   │   │             │         └──────────────────────────────┘    │
   │   │  [frame N]  │                                             │
   │   │  [frame 2]  │                                             │
   │   │  [frame 1]  │                                             │
   │   └─────────────┘                                             │
   │         ^                                                     │
   │         | when empty, pull next task                          │
   │         |                                                     │
   │   ┌─────┴───────────────────────────────────────────────┐     │
   │   │            EVENT LOOP (the dispatcher)              │     │
   │   └──┬──────────────────────────────────────────────┬───┘     │
   │      |                                              |         │
   │      v                                              v         │
   │  ┌────────────────────┐                  ┌────────────────────┐│
   │  │ MICROTASK QUEUE    │                  │ MACROTASK QUEUE    ││
   │  │ (FIFO, drains FULL)│                  │ (one per loop turn)││
   │  │                    │                  │                    ││
   │  │ Promise.then jobs  │                  │ setTimeout         ││
   │  │ queueMicrotask     │                  │ setInterval        ││
   │  │ MutationObserver   │                  │ setImmediate(Node) ││
   │  │ await continuation │                  │ I/O callbacks      ││
   │  └────────────────────┘                  │ UI events (browser)││
   │           ^                              └────────────────────┘│
   │           |                                                    │
   │   (Node only, even higher priority)                            │
   │   ┌────────────────────┐                                       │
   │   │ nextTick QUEUE     │                                       │
   │   │ process.nextTick   │                                       │
   │   └────────────────────┘                                       │
   │                                                                │
   └────────────────────────────────────────────────────────────────┘
```

### Browser (HTML spec)
> **Intuition first:** The browser does one task, then "tidies up" all the microtask side-effects of that task, then renders if needed, then moves on. Microtasks are how "after this finishes, do X" works — they don't get interleaved with a new task.

The agent runs in a loop:
1. Pick **one** task from the macrotask queue.
2. Execute it to completion (no preemption).
3. Drain the **entire** microtask queue.
4. Render if needed.
5. Go to 1.

Microtasks chain: if a microtask enqueues another, the new one runs in the *same* drain. This is how Promise chains feel synchronous.

### Node.js (libuv) — phases in order each tick

> **Intuition first:** Node breaks the macrotask side into specialized "rooms" (phases). Each room only handles one kind of callback — one for timers, one for I/O, one for `setImmediate`, etc. Between *every* room transition, Node empties its priority queues (nextTick, then microtasks). That's why a `process.nextTick` you scheduled inside an I/O callback runs **before** the next phase begins — not at the end of the loop.

```
       ┌──────────────────────────────┐
       │       LIBUV EVENT LOOP       │
       └──────────────┬───────────────┘
                      v
   ┌─────────────────────────────────────┐
   │ 1. TIMERS                           │  ← setTimeout / setInterval
   │    (expired timer callbacks)        │
   └────────────────┬────────────────────┘
                    | drain nextTick + microtasks
                    v
   ┌─────────────────────────────────────┐
   │ 2. PENDING CALLBACKS                │  ← deferred system ops
   └────────────────┬────────────────────┘
                    | drain nextTick + microtasks
                    v
   ┌─────────────────────────────────────┐
   │ 3. IDLE / PREPARE  (internal)       │
   └────────────────┬────────────────────┘
                    | drain nextTick + microtasks
                    v
   ┌─────────────────────────────────────┐
   │ 4. POLL                             │  ← I/O callbacks; may BLOCK here
   │    (file read, socket data, etc.)   │
   └────────────────┬────────────────────┘
                    | drain nextTick + microtasks
                    v
   ┌─────────────────────────────────────┐
   │ 5. CHECK                            │  ← setImmediate
   └────────────────┬────────────────────┘
                    | drain nextTick + microtasks
                    v
   ┌─────────────────────────────────────┐
   │ 6. CLOSE CALLBACKS                  │  ← socket.on('close', ...)
   └────────────────┬────────────────────┘
                    | drain nextTick + microtasks
                    └───── loops back to 1 ─────┐
                                                v
                                          (next tick)
```

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

> **Step-by-step walkthrough of the code below:**
> 1. Sync code runs first → logs `sync`.
> 2. Call stack empties. Node drains nextTick → logs `nextTick`.
> 3. Then drains microtasks → logs `promise`.
> 4. Enters timers phase → logs `timeout`.
> 5. Moves to check phase → logs `immediate`.

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

> **Mental Model:** The chef has only two hands. While they're chopping onions for 30 seconds, **no other order moves**. Not the soup boiling over, not the customer asking for the bill — *nothing*. In Node, a 30-second sync function means 30 seconds of unanswered HTTP requests.

Every CPU-heavy synchronous function — JSON.parse on a 50MB payload, a regex with catastrophic backtracking, bcrypt.hashSync — freezes the entire process. No requests can be accepted, no timers fire, no I/O completes. Use `worker_threads`, `crypto.randomBytes` (async), `bcrypt` async APIs, or stream the work.

## Bridge: from theory to syntax

You now know **what** the queues do. The next section lists the **APIs** that put callbacks into each queue. As you read, mentally tag each line: "this goes to the macrotask queue", "this goes to microtasks", "this is nextTick-only", etc.

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

## Bridge: edge cases reveal the *real* model

The cheat sheet above is the "happy path". Real interviews probe the *boundary cases*: what happens when timers have minimum delays, when microtasks recurse, when sync and async ordering collide. The next section is where most candidates trip up.

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

## Bridge: from edge cases to live interview practice

The next section is what the interview *actually feels like*: an examiner reads a code snippet, you predict output and explain phase-by-phase. Each example below includes "how to think aloud" — the actual sentences you'd say.

## Interview worked examples

### Example 1 — Predict mixed setTimeout / Promise / nextTick output
**Asked as:** "Walk me through what this prints in Node, in order."

> **How to think aloud (interview storytelling):**
> "I'm going to mentally simulate the loop. First pass: any sync code runs immediately. Then when the stack is empty, Node drains its priority queues — nextTick first because it's the highest priority, then microtasks (Promise.then). Then the loop enters its phases: timers, poll, check, etc. So I expect: sync → nextTick → promise → timeout."

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

> **Step-by-step walkthrough:**
> 1. `setTimeout(...)` is registered → goes to timers phase queue. Nothing prints yet.
> 2. `Promise.resolve().then(...)` schedules a microtask. Nothing prints yet.
> 3. `process.nextTick(...)` adds to nextTick queue. Nothing prints yet.
> 4. `console.log("sync")` runs immediately → **"sync"**.
> 5. Call stack empty. Node drains nextTick → **"nextTick"**.
> 6. Then microtasks → **"promise"**.
> 7. Loop enters timers phase → **"timeout"**.

**What the interviewer is testing:** Microtask vs macrotask vs nextTick priority.
**Sharp follow-up they often ask:** "Add `setImmediate` — where does it land?" → After timeout (or before, in main context — non-deterministic w/ setTimeout(0)).

### Example 2 — `setImmediate` vs `setTimeout(0)` inside an I/O callback
**Asked as:** "Inside `fs.readFile` callback, which fires first?"

> **How to think aloud:**
> "The `fs.readFile` callback runs in the **poll** phase. The very next phase after poll is **check**, where `setImmediate` callbacks live. The timers phase only runs at the start of the *next* loop iteration. So setImmediate wins, deterministically. This is one of the very few places `setImmediate` vs `setTimeout(0)` ordering is guaranteed."

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

> **Step-by-step walkthrough:**
> 1. `fs.readFile` starts; its callback is registered to fire in the poll phase when the read completes.
> 2. Read completes → callback runs in poll phase. Both `setTimeout` and `setImmediate` are scheduled.
> 3. Phase transition: poll → check. The check phase processes setImmediate → **"immediate"**.
> 4. Loop continues to close phase (nothing there), wraps around to timers next iteration → **"timeout"**.

**What the interviewer is testing:** libuv phase order; deterministic ordering inside I/O.
**Sharp follow-up they often ask:** "Why is ordering non-deterministic from the main module?" → setTimeout has minimum 1ms; if event-loop entry is < 1ms in, timer hasn't elapsed → immediate wins; else timer wins.

### Example 3 — `queueMicrotask` vs `Promise.resolve().then`
**Asked as:** "Are these identical? Predict order."

> **How to think aloud:**
> "Both APIs append to the **same** microtask queue. There's no separate 'queueMicrotask queue'. So the order is purely the order of scheduling — FIFO. The only difference is that `queueMicrotask` is the lighter, explicit API; no Promise object is allocated."

I'd say: "Both schedule a microtask in the same queue, in registration order. `queueMicrotask` is the explicit, lighter API — no Promise allocation. Functionally interchangeable for ordering."

```js
Promise.resolve().then(() => console.log("a"));
queueMicrotask(() => console.log("b"));
Promise.resolve().then(() => console.log("c"));
// Output: a, b, c — same queue, FIFO
```

> **Step-by-step walkthrough:**
> 1. Line 1 enqueues microtask "a".
> 2. Line 2 enqueues microtask "b" (same queue, after "a").
> 3. Line 3 enqueues microtask "c" (after "b").
> 4. Sync code ends. Microtask queue drains in FIFO order → a, b, c.

**What the interviewer is testing:** Microtask queue is a single queue regardless of API.
**Sharp follow-up they often ask:** "When would you prefer `queueMicrotask`?" → No promise allocation; explicit signal to readers; doesn't create unhandled-rejection risk.

### Example 4 — `await` ordering inside an async function
**Asked as:** "Predict the output."

> **How to think aloud:**
> "Every `await` *splits* the function in two: the sync part before, and the 'continuation' after. The continuation is scheduled as a microtask once the awaited promise settles. Even `await Promise.resolve()` — already resolved — costs one microtask tick. So inside `f`, line `1` logs sync; then `await` yields; control returns to caller; `2` logs sync; stack empties; microtasks drain → `3` logs."

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

> **Step-by-step walkthrough:**
> 1. `f()` is called. Enters async function. Logs **"1"**.
> 2. Hits `await Promise.resolve()`. Even though the promise is already resolved, the continuation (`console.log("3")`) is scheduled as a microtask, **not** run immediately.
> 3. `f()` returns (a pending Promise) back to top-level.
> 4. Top-level sync continues → logs **"2"**.
> 5. Sync ends. Microtask queue drains → continuation runs → logs **"3"**.

**What the interviewer is testing:** Every `await` yields one microtask, even on resolved values.
**Sharp follow-up they often ask:** "What if I add `console.log('4')` after `f()` and another await inside f?" → walk through extra microtask scheduling.

### Example 5 — CPU-bound work blocking the loop
**Asked as:** "Why does my Express server stop responding when this runs?"

> **How to think aloud:**
> "The chef analogy: while one route handler is doing a 10-second loop, the chef can't even pick up other orders. There's literally no other thread to handle incoming requests. Two repairs: (a) make the work cooperative — yield to the loop every N iterations via `setImmediate`, or (b) move it off the JS thread entirely with `worker_threads`. (a) works for divisible work; (b) is required for one-shot CPU operations like bcrypt."

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

> **Step-by-step walkthrough of the cooperative version:**
> 1. Loop runs 1 million iterations synchronously.
> 2. Hits `await new Promise(r => setImmediate(r))` — schedules a setImmediate, yields.
> 3. Loop returns control. Other queued I/O / timers / requests get a chance to run.
> 4. setImmediate fires in next check phase → resolves the promise → microtask continuation resumes the loop.
> 5. Next 1M iterations. Repeat.

**What the interviewer is testing:** Single-threaded model awareness; cooperative yielding pattern.
**Sharp follow-up they often ask:** "When does yielding NOT work?" → If the work is one indivisible computation (e.g. bcrypt's internal loop) — must use worker_threads or async-native APIs.

### Example 6 — Microtask starvation
**Asked as:** "What happens if I recursively schedule microtasks?"

> **How to think aloud:**
> "Microtasks drain **fully** before the loop moves on. If each microtask schedules another microtask, the drain never ends — macrotasks (timers, I/O, requests) never get a turn. The process appears hung to the outside world even though the CPU is busy. This is the JavaScript equivalent of a deadlock from the loop's perspective. The fix is to break the recursion by scheduling the next iteration via `setImmediate` or `setTimeout(0)`, which is a *macrotask* and gives the loop a chance to do other work between iterations."

I'd say: "Microtasks drain fully before the next macrotask. A recursive Promise.then chain (or repeated `process.nextTick`) prevents timers and I/O from ever running — the loop is starved. The process appears to hang from outside. The fix is to schedule the next iteration via setImmediate/setTimeout."

```js
let count = 0;
function starve() {
  if (++count < 1e6) Promise.resolve().then(starve);
}
starve();
setTimeout(() => console.log("never logs until starve finishes"), 0);
```

> **Step-by-step walkthrough:**
> 1. `starve()` runs. Schedules a microtask `starve`.
> 2. Sync ends. Microtask drain begins.
> 3. Microtask runs `starve` → schedules ANOTHER microtask.
> 4. The drain rule says "drain fully" — the new microtask is part of the same drain.
> 5. 999,998 more iterations later, the drain finally finishes.
> 6. Only NOW does the loop enter the timers phase and run `setTimeout`.

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
