# `process.nextTick` recursive starvation

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [nexttick-vs-setimmediate.md](./nexttick-vs-setimmediate.md), [microtask-starvation-recipes.md](./microtask-starvation-recipes.md)
>
> **Source:** Node docs (explicit warning). Real production outage cause at multiple FAANG-tier orgs.

---

## 1. Problem statement

What happens when `process.nextTick(self)` recurses? Why does it starve I/O? How do you detect and fix it?

**Verification examples**

| Setup                                                  | Behaviour                                              |
|--------------------------------------------------------|---------------------------------------------------------|
| `function starve(){ process.nextTick(starve) } starve()` | nextTick queue never empties → loop never advances    |
| HTTP server with starvation running                     | requests pile up; never read; no response             |
| `setTimeout(cb, 100)` while starving                    | cb NEVER fires; process hangs at 100% CPU             |
| Replace with `setImmediate(starve)`                     | yields to poll each iter; I/O continues               |

**Constraints**
- `nextTick` queue drains fully between every operation, before microtasks and phases.
- Silent hang — no crash, no exception, CPU pegged at 100% on one core.
- Cure: replace recursive `nextTick` with `setImmediate`.

---

## 2. Plain-English restatement

`process.nextTick` queue drains COMPLETELY before any libuv phase advances. If a `nextTick` callback re-queues another `nextTick`, the queue refills faster than it drains — loop never reaches poll → I/O never runs → HTTP server hangs silently. The fix: replace with `setImmediate`, which yields to poll between iterations.

---

## 3. Why this matters in interviews

Top-3 cause of silent Node-service hangs in production. Tests whether you understand the priority hierarchy AND can debug operational issues.

---

## 4. Mental model

```
   nextTick queue drains BEFORE microtasks BEFORE any libuv phase advances.

   Recursive starvation:
   ┌─────────────────────────────────┐
   │ NT queue: [starve]              │
   │ drain → starve() runs           │
   │ inside: process.nextTick(starve)│
   │ NT queue: [starve] again         │
   │ drain → never empties            │
   └─────────────────────────────────┘
            ↓
   I/O phase NEVER runs.
   Timers NEVER fire.
   setImmediate NEVER fires.
   HTTP requests pile up unread.
   CPU 100% on one core.
   Process is alive but unresponsive.

   Fix: replace nextTick with setImmediate.
   setImmediate runs in check phase → loop must visit poll first → I/O runs.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Will `setTimeout(cb, 100)` ever fire if `process.nextTick(self)` is recursing?
> 2. Does the process crash or hang silently?
> 3. Why does `setImmediate(self)` recursion NOT starve I/O?

---

## 6. Brute force — walked through

### Wrong attempt 1: "use `nextTick` because it's faster"
Faster latency, but recursive use kills I/O.

### Wrong attempt 2: "the process will crash"
No — silent hang. Liveness probes need to be HTTP-level, not process-level.

### Wrong attempt 3: "microtask recursion is the same"
Same risk but `nextTick` is faster to fill and outranks microtasks.

---

## 7. The unlocking insight

> **`nextTick` queue drains BEFORE phases advance. Recursive `nextTick` refills queue forever → loop stuck. Replace with `setImmediate` to yield to poll each iteration.**

Three properties:

1. **NT outranks everything deferred** — drains before MQ and any phase.
2. **Silent hang** — no exception; just unresponsiveness.
3. **`setImmediate` is the cure** — check phase requires loop to traverse poll first.

---

## 8. Solution (annotated)

```js
const http = require('node:http');

let retries = 0;

// THE STARVATION BUG
function brokenRetry() {
  retries++;
  process.nextTick(brokenRetry);                                     // step 1: never yields
}

// THE FIX
function fixedRetry() {
  retries++;
  setImmediate(fixedRetry);                                          // step 2: yields to poll
}

// Bounded nextTick (use sparingly)
function boundedTick(maxPerLoop = 1000) {
  let i = 0;
  function tick() {
    if (i++ < maxPerLoop) {
      retries++;
      process.nextTick(tick);
    } else {
      setImmediate(() => boundedTick(maxPerLoop));                    // step 3: yield then resume
    }
  }
  tick();
}

const server = http.createServer((req, res) => res.end('ok'));
server.listen(3000, () => {
  // brokenRetry();  // uncomment to hang server
  fixedRetry();      // works fine
});
```

**Detection helper:**

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

// Or use perf_hooks.monitorEventLoopDelay()
```

---

## 9. Step-by-step dry run

```
process.nextTick(function a() {
  console.log('a');
  process.nextTick(function b() {
    console.log('b');
    process.nextTick(function c() {
      console.log('c');
      // imagine c keeps re-queueing forever
    });
  });
});

setTimeout(() => console.log('timer'), 0);
setImmediate(() => console.log('immediate'));

Walk:
- sync: queue cb_a in NT; cb_T in timers; cb_I in check.
- sync done; drain NT:
    run cb_a → log 'a'; queue cb_b.
    NT NOT EMPTY → keep draining.
    run cb_b → log 'b'; queue cb_c.
    NT NOT EMPTY → run cb_c → log 'c'.
    (if c re-queued itself, we'd loop here forever)
- drain MQ (empty).
- timers phase → cb_T → log 'timer'.
- (drain NT/MQ — empty).
- check phase → cb_I → log 'immediate'.

Output: a, b, c, timer, immediate.

Starvation case (c re-queues forever):
- a, b, c, c, c, c, c, ... forever.
- timer, immediate NEVER log.
- CPU 100%.
```

---

## 10. Common confusion + traps

1. **"nextTick is faster, so use it everywhere"** — recursive use kills I/O.
2. **"The process will crash"** — silent hang.
3. **"Liveness probe will catch it"** — only HTTP-level probes catch it (process is alive).
4. **"Microtask is safer"** — same risk, slightly less aggressive (microtask doesn't outrank itself).
5. **"`nextTick` is on the next loop tick"** — no, BEFORE next tick.
6. **`process.maxTickDepth`** — deprecated; can't rely on it.
7. **`queueMicrotask` recursion is fine** — same starvation risk.

---

## 11. Senior follow-ups & variants

### Variant 1 — Detect in production
`perf_hooks.monitorEventLoopDelay()` or `setInterval` round-trip. Alert at >50ms continuous lag.

### Variant 2 — Library is transitive dep
Wrap in worker_thread; or use pm2/k8s HTTP-level health checks for auto-restart.

### Variant 3 — Why Node allows nextTick if dangerous?
Sometimes the only way to emit a sync-feeling event after async setup (EventEmitter `error` with no listener). Removing it breaks a decade of code.

### Variant 4 — Browser equivalent
`queueMicrotask` recursion. Browsers throttle nested microtasks under DevTools but still freeze tabs.

### Variant 5 — Bounded nextTick pattern
Counter + `setImmediate` fallback when over limit. Allows nextTick speed without infinite recursion.

---

## 12. How to think aloud

> "process.nextTick queue drains FULLY between every operation, BEFORE microtasks, BEFORE any libuv phase. Recursive `process.nextTick(self)` refills the queue → loop never advances → I/O never runs → HTTP server silently hangs at 100% CPU. Fix: replace with `setImmediate(self)` — runs in check phase, loop must visit poll first, I/O continues. Detect via `perf_hooks.monitorEventLoopDelay()` or interval round-trip lag. nextTick is still useful for emit-once-after-current-sync — just don't recurse. Modern advice: prefer `queueMicrotask` to nextTick; prefer `setImmediate` to setTimeout(0)."

---

## 13. 60-second revision

> - **`nextTick` queue drains** between every op, before MQ, before any phase.
> - **Recursive `nextTick(self)`** → queue never empties → silent hang.
> - **NOT a crash** — process alive, 100% CPU, unresponsive.
> - **Fix:** `setImmediate(self)` yields to poll each iter.
> - **Detect:** `perf_hooks.monitorEventLoopDelay()` or interval lag.
> - **Same risk** with recursive `queueMicrotask`.
> - **`nextTick` still useful** for sync-feeling event emit; don't recurse.
> - **Trap:** "process will crash"; "liveness will catch it"; "use nextTick because faster."

---

**Related:** [nexttick-vs-setimmediate.md](./nexttick-vs-setimmediate.md) · [microtask-starvation-recipes.md](./microtask-starvation-recipes.md) · [setimmediate-vs-settimeout-in-io.md](./setimmediate-vs-settimeout-in-io.md) · [event-loop-concurrency.md](./event-loop-concurrency.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
