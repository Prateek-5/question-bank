# Microtask Starvation — Recipes and Cures

## Source / Origin
- Real Node.js outage write-ups; React 18 scheduler design rationale.
- Asked at: Razorpay, Stripe, Atlassian, Cloudflare.
- Concept reference: `concepts/event-loop.md`, sibling `microtask-drainer.md`, `nexttick-starvation.md`.

## Why this question matters in interviews
"The HTTP server stopped responding but the CPU isn't pegged" — this is microtask starvation. A long Promise chain or a `process.nextTick` recursion drains continuously, never letting the macrotask queue (timers, I/O) get a turn. Senior bar: you can produce a starvation example on demand, identify it in code review, and explain how `setImmediate` / `setTimeout(0)` reintroduces a fairness boundary.

## Concepts involved

### Syntax to lock in
```js
// Recipe 1: infinite microtask loop
async function starve1() {
  while (true) await Promise.resolve();   // never yields to macrotasks
}
// timers and I/O callbacks NEVER fire while this runs

// Recipe 2: recursive nextTick (Node only — even higher priority)
function starve2() {
  process.nextTick(starve2);              // drains before microtasks even
}

// Recipe 3: long .then chain
let p = Promise.resolve();
for (let i = 0; i < 1e6; i++) p = p.then(() => {});   // 1M microtasks pile up
// Each unblocks before any timer; server can't respond during drain
```

### Edge cases / interview traps
1. **Single `await Promise.resolve()` is fine.** It's the *infinite/recursive* pattern that starves.
2. **`queueMicrotask` and `.then` share the queue.** Both starve macrotasks equally.
3. **`process.nextTick` (Node) is strictly higher than microtask.** Recursing in nextTick starves *both* microtasks and macrotasks.
4. **`setImmediate` cures it.** Yielding via setImmediate or `setTimeout(0)` puts you in the macrotask queue — gives the loop a chance to run timers and I/O.
5. **Real-world cause**: ORMs that promise-chain through deeply nested async hooks; recursive flatmap over big arrays via `.then`.
6. **Browser symptom**: input lag, jank, frozen scroll. Node symptom: HTTP timeouts, no `setTimeout` callbacks fire.
7. **Detection**: Node's `process._tickCallback` overhead, or `perf` flamegraph showing all time in microtask drain.
8. **Cure pattern**: insert a macrotask boundary every N iterations: `if (i % 1000 === 0) await new Promise(r => setImmediate(r));`.

## Mental Model

The event loop is a **fairness scheduler** between three queues:

```
   Priority (Node):
   1. process.nextTick queue          ← drains FIRST, fully
   2. microtask queue (Promises)      ← drains SECOND, fully
   3. macrotask queue (timers, I/O)   ← finally, ONE callback

   Each macrotask: run callback → drain nextTick → drain microtasks → next macrotask
```

Starvation = an infinite producer of items into 1 or 2:

```
  ┌─ infinite nextTick recursion ─┐
  │  feeds nextTick queue forever  │
  └────────────────────────────────┘
       ↓
   nextTick queue never empties
       ↓
   microtask queue and macrotask queue NEVER get a turn
       ↓
   timers don't fire; setImmediate doesn't fire; HTTP requests pile up
```

Cure: insert `await new Promise(r => setImmediate(r))` periodically. That:
1. Drops you out of microtask drain.
2. Forces the loop to advance to the next macrotask phase.
3. setImmediate fires in the "check" phase, by which time timers and I/O have had their turn.

## Why interviewers care

- **Production debugging skill** — recognizing starvation in code/logs.
- **Event-loop intuition** — the priority order is testable.
- **Performance tradeoffs** — when to yield vs when to drain.

## Common beginner confusion

- **"Async/await yields."** Each `await` is a microtask hop, *not* a macrotask hop. Doesn't break starvation.
- **"`setTimeout(0)` is the same as `queueMicrotask`."** Different queues. setTimeout = macrotask, fairness-restoring.
- **"Node will preempt long microtask chains."** No — cooperative scheduling. You yield, or it starves.
- **"`process.nextTick` is faster than microtask, so use it for hot paths."** Faster in latency, but using it in a loop is *the* canonical Node footgun.
- **"Starvation only happens in infinite loops."** Even 1M chained microtasks can stall the loop for hundreds of ms.

## Brute force approach

```js
// Naïve recursive Promise chain over a giant array
async function processAll(items) {
  for (const item of items) {
    await process(item);     // sync work; each iteration adds a microtask hop
  }
}
// For 1M items where process is cheap, this is fine for CPU but freezes timers
// until the loop completes
```

## Optimal approach

Yield to macrotask queue periodically:

```js
async function processAll(items) {
  for (let i = 0; i < items.length; i++) {
    await process(items[i]);
    if (i % 1000 === 0) await new Promise(r => setImmediate(r));   // yield every 1000
  }
}
```

For CPU-bound work, offload to a worker (see `worker-pool-implementation.md`).

## Solution (JavaScript)

```js
// Generic "yield every N" helper
async function cooperative(items, fn, { yieldEvery = 1000 } = {}) {
  for (let i = 0; i < items.length; i++) {
    await fn(items[i], i);
    if (i % yieldEvery === 0) {
      // setImmediate in Node; setTimeout(0) in browser
      await new Promise(res => (typeof setImmediate === 'function' ? setImmediate(res) : setTimeout(res, 0)));
    }
  }
}

// Detect microtask-only loops via instrumentation
let lastMacrotask = Date.now();
setInterval(() => {
  const dt = Date.now() - lastMacrotask;
  if (dt > 500) console.warn(`Event loop stalled ${dt}ms — likely microtask starvation`);
  lastMacrotask = Date.now();
}, 100);

// Cure a recursive nextTick — break with setImmediate
function safeRecursive(workItem) {
  process.nextTick(() => {
    // ... work ...
    if (more) setImmediate(safeRecursive);    // setImmediate, not nextTick
  });
}
```

## Step-by-step dry run

Starvation example: 100k Promise chain in a request handler.

```
HTTP req comes in at t=0  → handler starts
t=0     handler builds 100k .then chain in one tick (synchronous queueing)
t=5ms   all microtasks queued; script returns
t=5ms   event loop: drain microtasks → m1 runs in 0.001ms → schedules m2
        m2 runs → schedules m3 → ... → 100k chained
        microtask queue NEVER empties until 100k drained
t=600ms drain complete; loop checks macrotasks
        meanwhile, /healthcheck request that arrived at t=10ms times out (5s)
        meanwhile, setTimeout for connection cleanup fires 590ms late
```

Symptoms in monitoring: p99 latency spike on unrelated routes; healthcheck flaps; log "event loop stalled".

After fix (yielding every 1000):

```
t=0    handler queues 1000 .then; setImmediate; queues 1000 more; setImmediate; ...
t=5ms  first 1000 microtasks drain (~6ms); setImmediate runs (macrotask)
       — at this point, timers and I/O can interleave
       healthcheck and other requests handled normally
t=600ms work done; total wall ≈ same, but loop stayed responsive
```

## How to think aloud in the interview

> "Microtask starvation: an unbounded producer of microtasks (chained .then, recursive queueMicrotask) or process.nextTick blocks the loop from servicing timers and I/O. CPU isn't pegged on individual work, but everything else is starved. Detect via 'loop lag' instrumentation — setInterval-vs-actual delta. Cure: insert `await new Promise(r => setImmediate(r))` periodically; or move CPU-bound work to a worker. For nextTick recursion: switch to setImmediate."

## Important takeaways

- **Priority order (Node):** nextTick > microtasks > macrotasks.
- **Each level drains before yielding to the next.**
- **Starvation = infinite producer in nextTick/microtask queue.**
- **Cure**: `setImmediate` or `setTimeout(0)` for fairness boundary.
- **Detect via loop-lag monitoring.**
- **Workers** for genuine CPU-bound work.

## Variants

- **Setting `process.maxTickDepth`** (Node deprecated) — used to limit nextTick recursion; removed.
- **`setImmediate` in browsers** — doesn't exist; use `MessageChannel.postMessage` for similar semantics.
- **AbortSignal-based cooperative yield** — stop when external signal aborts.
- **Worker offload** — move starving work off main thread entirely.
- **Detecting starvation in observability** — Node `perf_hooks.monitorEventLoopDelay`.

## Revision notes

```
Microtask starvation = unbounded producer in microtask/nextTick queue
  drains before macrotask gets a turn
  symptoms: timers don't fire; HTTP times out; CPU not pegged

Recipes:
  while (true) await Promise.resolve()       — starves
  process.nextTick(self)                     — starves harder
  1M chained .then()                         — bounded starvation
  process.nextTick recursion                 — starves nextTick + micro + macro

Cure:
  await new Promise(r => setImmediate(r))    — macrotask boundary
  cooperative yield every N iterations
  worker pool for CPU-bound

Detect:
  perf_hooks.monitorEventLoopDelay
  setInterval-vs-actual lag log
```
