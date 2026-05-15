# `process.nextTick` recursive starvation of I/O

## Source
- Node.js docs (the warning is explicit): https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick#processnexttick
- Real-world post-mortem: Node core has had multiple bugs from accidental `nextTick` recursion (e.g., GitHub Issue #6034 in early days).
- Discussion thread at Node.js technical steering committee about renaming the API.

## Why this question matters in interviews
Senior backend interviewers ask this because a real production outage at one of the FAANG-equivalent companies was caused by exactly this bug — a library author wrote `process.nextTick(retry)` inside a retry loop for "fast retry," and the server stopped serving HTTP requests entirely (the I/O poll phase never ran). The candidate who can describe **why** (priority queue order) and **how to detect / fix it** (replace with `setImmediate`) demonstrates real Node operational experience. It's also the easiest way to crash a Node service silently — no exception, no log, just an unresponsive process.

## Concepts involved

### Priority refresher
- `process.nextTick` queue is drained **completely** between every operation, **before** microtasks, **before** any libuv phase advances.
- This means: if `nextTick` re-queues itself, the queue **never empties**, and the loop **never advances** to the `poll` phase where I/O lives.
- Result: HTTP requests come in, OS buffers them, your Node process never reads them. **Silent freeze.**

### Syntax to lock in
```js
// THE STARVATION BUG
function starvationBug() {
  process.nextTick(starvationBug); // queue keeps re-filling, never drains
}
starvationBug();
console.log('hi'); // logs once, then process hangs forever (kind of)
```

After this runs, your server:
- Stops responding to HTTP.
- Stops resolving DNS.
- Stops reading files.
- Stops emitting timers.
- Doesn't even crash — it's stuck in an infinite drain loop.
- CPU pegs at 100% (one core).

### Why `setImmediate` is the cure
`setImmediate` enqueues to the `check` phase. The loop **must finish** the current phase, then **run** the poll phase, **then** run check. So between each `setImmediate` callback, I/O has a chance to run.

```js
function safeLoop() {
  setImmediate(safeLoop); // gives I/O a chance every iteration
}
safeLoop();
// HTTP server keeps responding.
```

### Why `setTimeout(fn, 0)` is also fine (mostly)
`setTimeout(fn, 0)` goes to the `timers` phase. Between callbacks, poll runs. But there's a 1ms minimum coercion, so it's slower than `setImmediate`. In starvation-recovery scenarios, prefer `setImmediate`.

### Edge cases
1. **Microtask recursion starves too** — `queueMicrotask(fn)` where `fn` recursively calls `queueMicrotask(fn)` has the same effect. Node 11+ specifically did NOT fix this because spec-compliance requires it.
2. **`nextTick` from within a microtask**: still goes to the nextTick queue. The next microtask drain happens after the nextTick drain. So it's a small reordering, not a fix.
3. **Mixed**: `setImmediate(() => process.nextTick(fn))` is safe — the nextTick fires once per loop iteration, not infinitely.
4. **Detection via `event-loop-lag`**: tools like `blocked-at`, `event-loop-stats`, or simply measuring `setImmediate` round-trip lag exposes this. If lag > 100ms consistently, you've got starvation or sync work hogging the loop.
5. **Why Node didn't rename `process.nextTick`**: it was named for the browser-ish "next tick of the loop" idea — but it actually runs *before* the next tick. The Node TSC discussed renaming for years; backward compat won.
6. **`process.nextTick` predates Promises** — it was added before V8 had a native microtask queue. The Node-vs-browser priority difference is partly historical accident.

## Brute force approach
"I'd just use `setImmediate` for everything." Not wrong, but you need to know **when** `nextTick` is the right answer:
- Emitting events synchronously after an async operation but before user code runs (Node uses this pattern internally — see EventEmitter).
- Deferring an error throw to the next tick so the listener can be attached.
- Cleanup actions you want to run "right after the current sync work."

`nextTick` is faster and higher priority than `setImmediate` — when you need *exactly* that, use it. When you don't, default to `setImmediate`.

## Optimal approach
Two-part answer:
1. **Why**: `nextTick` queue drains before phase advance; recursion fills the queue faster than it drains.
2. **Fix**: replace recursive `nextTick` with `setImmediate` to yield to I/O each iteration. If you must use `nextTick`, add a counter that breaks out after N iterations.

## Solution (JavaScript)

```js
const http = require('node:http');

// --- Scenario: a "fast retry" loop that accidentally starves I/O ---

let retries = 0;
function brokenRetry() {
  retries++;
  if (retries % 1_000_000 === 0) console.log('retries:', retries);
  // The bug: never yields to I/O. Server hangs.
  process.nextTick(brokenRetry);
}

// --- Fix using setImmediate: yields to poll phase between iterations ---
function fixedRetry() {
  retries++;
  if (retries % 1_000_000 === 0) console.log('retries:', retries);
  setImmediate(fixedRetry);          // <-- the only change
}

// --- Or, bounded nextTick — use sparingly ---
function boundedTick(maxPerLoop = 1000) {
  let i = 0;
  function tick() {
    if (i++ < maxPerLoop) {
      retries++;
      process.nextTick(tick);
    } else {
      setImmediate(() => boundedTick(maxPerLoop)); // yield, then resume
    }
  }
  tick();
}

const server = http.createServer((req, res) => {
  res.end('ok');
});
server.listen(3000, () => {
  console.log('listening on 3000');
  // brokenRetry();   // <-- uncomment to crash I/O
  fixedRetry();       // <-- works, server still responds
});
```

### Detection helper

```js
function measureEventLoopLag(intervalMs = 100) {
  let last = Date.now();
  setInterval(() => {
    const now = Date.now();
    const lag = now - last - intervalMs;
    if (lag > 50) console.warn('event loop lag:', lag, 'ms');
    last = now;
  }, intervalMs).unref();
}
```

If lag spikes above 50ms continuously, your loop is being starved.

## Step-by-step dry run

```js
process.nextTick(function a() {
  console.log('a');
  process.nextTick(function b() {
    console.log('b');
    process.nextTick(function c() {
      console.log('c');
      // imagine this kept calling process.nextTick forever
    });
  });
});

setTimeout(() => console.log('timer'), 0);
setImmediate(() => console.log('immediate'));
```

Trace:
- Sync code: queue `a` to nextTick, queue timer to timers phase, queue immediate to check phase.
- Sync ends. Drain nextTick: run `a`. Inside `a`, queue `b`. **Queue is not empty, keep draining.**
- Run `b`. Inside `b`, queue `c`. **Queue is not empty.**
- Run `c`. (Nothing more queued in our example.)
- Microtask queue is empty.
- Loop advances to timers phase. Run timer cb → log `timer`.
- Drain nextTick (empty) + microtask (empty).
- Loop advances to check phase. Run immediate → log `immediate`.

Output: `a b c timer immediate`.

**Now mutate**: if `c` had re-queued itself recursively, we'd never reach the timers phase. `timer` and `immediate` would never log. Server would hang.

## Important takeaways

**Syntax to memorize**
- `process.nextTick(fn)` — Node-only, highest async priority.
- `setImmediate(fn)` — `check` phase, after poll runs. Use to yield to I/O.
- `setTimeout(fn, 0)` — `timers` phase, also yields to I/O (with ~1ms minimum).

**Patterns to reuse**
- "Recursive deferred work" → use `setImmediate`, not `nextTick`.
- Need to fire "before any I/O" → `nextTick` is fine, but cap depth.
- Long synchronous loops → break into chunks with `setImmediate(processNext)`.
- Event loop lag monitoring as a SLO — alert at >50ms.

**Common mistakes**
- Using `nextTick` "because it's faster" without knowing the starvation risk.
- Believing the bug will cause a crash. **It causes a silent hang.** The process is alive but unresponsive — kubernetes liveness probes may not catch it without an HTTP-level check.
- Thinking the microtask queue is the culprit. Same risk exists, but `nextTick` is faster to fill, so it manifests first.
- Confusing `nextTick` with "next iteration of the event loop." It actually runs *before* the next iteration.

**Related questions**
- `setImmediate` vs `setTimeout(0)` inside an I/O callback
- `queueMicrotask` vs `Promise.resolve().then` (the microtask version of this problem)
- Mixed async output prediction

## Variants

1. **"How would you detect this in production?"** — measure event-loop lag with `setInterval` round-trip, or use Node's `perf_hooks.monitorEventLoopDelay()`.
2. **"What if the library is a transitive dependency and you can't change its code?"** — wrap calls in a worker_thread, or use `--experimental-vm-modules` with timeouts. Practical: use `pm2 reload` health checks at HTTP level so a frozen process gets recycled.
3. **"Why does Node *allow* this if it's so dangerous?"** — `nextTick` is sometimes the *only* way to emit a synchronous-feeling event after async setup (EventEmitter uses it for `error` events with no listener). Removing it would break a decade of code.
4. **"Browser equivalent?"** — `queueMicrotask` recursion. Browsers handle it slightly better (some throttle nested microtasks under DevTools), but you can still freeze a tab.

## Revision notes

> **process.nextTick starvation — 60 second recap**
> - `nextTick` queue drains **fully** between every operation, **before** microtasks and **before** any libuv phase.
> - Recursive `process.nextTick(self)` → queue never empties → I/O phase never runs → silent hang.
> - **Fix**: replace recursive `nextTick` with `setImmediate` (yields to poll phase).
> - **Detection**: event-loop lag monitoring (`perf_hooks.monitorEventLoopDelay` or interval round-trip).
> - Same risk with `queueMicrotask` recursion (microtask starvation).
> - `nextTick` is still useful — for emit-once-after-current-sync; just don't recurse.
> - **Trap**: thinking the process will crash. It hangs. CPU pegs at 100% on one core.
