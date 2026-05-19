# Node.js Event Loop — six libuv phases

> **Difficulty:** Senior   |   **Time:** ~20 min   |   **Prereqs:** [event-loop-concurrency.md](./event-loop-concurrency.md), [`concepts/event-loop.md`](../../concepts/event-loop.md)
>
> **Source:** Node docs, libuv source. Every staff-level Node round.

---

## 1. Problem statement

Name the 6 libuv phases in order, what each runs, where `process.nextTick` + microtask queues fit (not phases — interleaved), and why `setImmediate` deterministically beats `setTimeout(0)` inside an I/O callback.

**Verification examples**

| Question                                                            | Answer                                          |
|---------------------------------------------------------------------|--------------------------------------------------|
| Name the 6 libuv phases in order                                     | timers → pending → idle/prepare → poll → check → close |
| What runs in poll?                                                    | I/O callbacks (fs, net); blocks here when nothing else pending |
| What runs in check?                                                   | `setImmediate` callbacks                         |
| Where does nextTick run?                                              | Between every callback (NOT a phase)             |
| `UV_THREADPOOL_SIZE` default?                                         | 4                                                |

**Constraints**
- 6 phases, in order, per iteration.
- nextTick + microtask drain between every callback.
- Only `poll` blocks; other phases run callbacks and move on.
- `setImmediate` deterministically beats `setTimeout(0)` inside I/O cb.

---

## 2. Plain-English restatement

The Node event loop is a state machine with 6 phases. On each iteration, it visits each phase in order. The interesting one is **poll**, which is where I/O callbacks run AND where the loop blocks waiting for new events. Between every individual callback in every phase, the `nextTick` and microtask queues drain to empty — they're not phases themselves, they're interleaved.

---

## 3. Why this matters in interviews

Every senior Node interview asks this directly. Bonus points for naming the phase-by-phase behavior and the I/O-callback determinism rule. Shows up in system-design when latency budgets and "what blocks the loop" come up.

---

## 4. Mental model

```
   ┌───────────────────────────┐
   │ 1. timers                  │  setTimeout/setInterval whose deadline passed
   ├───────────────────────────┤
   │ 2. pending callbacks       │  deferred system errors (rare)
   ├───────────────────────────┤
   │ 3. idle, prepare           │  internal libuv (almost never user-visible)
   ├───────────────────────────┤
   │ 4. poll                    │  I/O callbacks; BLOCKS here for new events
   ├───────────────────────────┤
   │ 5. check                   │  setImmediate callbacks
   ├───────────────────────────┤
   │ 6. close callbacks         │  socket.on('close'), etc.
   └────────┬──────────────────┘
            │ loop back to phase 1
            ▼

   Between EVERY callback in EVERY phase:
     drain process.nextTick → drain microtask queue

   poll is the only blocking phase. It waits for new I/O if nothing else pending.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. List the 6 phases in order.
> 2. Why is `setImmediate` after `setTimeout(0)` inside an I/O callback non-deterministic? (Trick — it's actually deterministic the OTHER way.)
> 3. Why does long sync work in an I/O callback block all other I/O?

---

## 6. Brute force — walked through

### Wrong attempt 1: "Node has an event loop"
Too vague.

### Wrong attempt 2: list only 3-4 phases
Six. Idle/prepare is rarely user-visible but exists.

### Wrong attempt 3: "microtasks drain at end of each iteration"
No — drain between every callback (Node 11+).

---

## 7. The unlocking insight

> **Six phases in fixed order. Each phase has its own callback queue. The loop visits in order; between every callback in every phase, drain nextTick + microtask. Poll is the only blocking phase. From I/O cb (poll), `check` (setImmediate) deterministically follows.**

Three properties:

1. **Six phases, fixed order**: timers, pending, idle/prepare, poll, check, close.
2. **NT + MQ drain between every callback** (not just at phase boundaries).
3. **Poll blocks** waiting for I/O; everything else runs and moves on.

---

## 8. Solution (annotated)

```js
const fs = require('node:fs');

// Phase 1: timers
setTimeout(() => console.log('[timers] setTimeout(0)'), 0);

// Phase 5: check
setImmediate(() => console.log('[check] setImmediate'));

// Between-phase queues
process.nextTick(() => console.log('[between] nextTick'));            // step 1
Promise.resolve().then(() => console.log('[between] microtask'));     // step 2

// Phase 4: poll
fs.readFile(__filename, () => {
  console.log('[poll] fs.readFile callback');

  // From inside I/O cb, ordering is DETERMINISTIC
  setTimeout(() => console.log('  [timers]  inner setTimeout(0)'), 0);
  setImmediate(() => console.log('  [check]   inner setImmediate'));
  process.nextTick(() => console.log('  [between] inner nextTick'));
  Promise.resolve().then(() => console.log('  [between] inner microtask'));
});

console.log('sync end');

// Output (Node):
// sync end
// [between] nextTick                  ← drained first
// [between] microtask                 ← MQ drain
// [timers] setTimeout(0)              ← order with setImmediate may flip
// [check] setImmediate                ← from main module = racy
// [poll] fs.readFile callback
//   [between] inner nextTick
//   [between] inner microtask
//   [check]   inner setImmediate      ← DETERMINISTIC: check follows poll
//   [timers]  inner setTimeout(0)     ← next iteration
```

---

## 9. Step-by-step dry run

```
Trace the fs.readFile dispatch:

Sync execution:
  register cb_T (timers), cb_I (check), cb_N (NT), cb_M (MQ).
  fs.readFile → libuv thread pool starts read.
  log 'sync end'.

Sync done; drain NT → cb_N → log 'nextTick'. NT=[].
Drain MQ → cb_M → log 'microtask'. MQ=[].

Iteration 1:
  timers phase: cb_T deadline passed → run → log 'setTimeout(0)'.
  drain NT, MQ (empty).
  pending/idle/prepare: nothing.
  poll: fs not done yet → block until fs completes OR timeout.
  check: empty wait... actually we have cb_I queued. Wait — check phase fires AFTER poll.
  Reorder: in iteration 1, poll is still waiting; loop blocks here UNTIL fs done OR
           UNTIL non-zero timeout. With setImmediate queued, poll has a max wait of 0.

  Skip poll wait (immediates pending) → check phase → run cb_I → log 'setImmediate'.
  drain NT, MQ. close phase: nothing.

Iteration 2:
  timers: nothing.
  poll: fs.readFile finally done → run fs callback (cb_F).
    log '[poll] fs.readFile callback'.
    inside cb_F: schedule cb_T2 (timers), cb_I2 (check), cb_N2 (NT), cb_M2 (MQ).
  cb_F returns.
  drain NT → cb_N2 → log 'inner nextTick'.
  drain MQ → cb_M2 → log 'inner microtask'.
  poll queue empty (cb_F was its only callback) → check phase → run cb_I2 → log 'inner immediate'.

Iteration 3:
  timers: cb_T2 deadline passed → run → log 'inner setTimeout(0)'.

Output:
  sync end, nextTick, microtask, setTimeout(0), setImmediate,
  fs.readFile callback, inner nextTick, inner microtask, inner immediate, inner setTimeout(0).
```

---

## 10. Common confusion + traps

1. **Only 3-4 phases** — there are 6.
2. **Microtasks drain "at end"** — no, between every callback.
3. **`nextTick` as microtask** — no, own queue.
4. **`poll` doesn't block** — it does, when nothing else pending.
5. **`setTimeout(1)` fires after exactly 1ms** — minimum, not exact; depends on phase reach.
6. **`UV_THREADPOOL_SIZE` for sockets** — no, sockets use kernel epoll/kqueue; pool is for fs/dns/crypto.
7. **Long sync in I/O cb is fine** — blocks all other I/O for that duration.

---

## 11. Senior follow-ups & variants

### Variant 1 — Why might `setTimeout(fn, 1)` fire later than 1ms?
Phase reach. If poll blocks for 50ms, timer fires at 50ms+.

### Variant 2 — Measure event loop lag
`perf_hooks.monitorEventLoopDelay()` or schedule `setImmediate` and measure delta.

### Variant 3 — `worker_threads` and the loop
Each worker has its own V8 isolate + libuv loop. Communicate via `MessageChannel`.

### Variant 4 — CPU-heavy fs callback
Blocks poll phase. Move to worker thread or chunk with `setImmediate`.

### Variant 5 — `process.exit()` vs natural exit
Natural exit when loop has zero pending handles. `unref`'d handles don't count.

---

## 12. How to think aloud

> "Six phases in fixed order: timers, pending, idle/prepare, poll, check, close. Between every callback in every phase, drain nextTick THEN microtasks. Poll is the only blocking phase — waits for new I/O when nothing else is pending. `setTimeout(0)` runs in timers; `setImmediate` runs in check. From main: setImmediate vs setTimeout(0) is racy; from inside an I/O callback (poll), check follows deterministically so setImmediate wins. libuv thread pool (size 4, `UV_THREADPOOL_SIZE`) backs fs/dns/crypto; sockets use kernel epoll/kqueue. Trap: listing only 3-4 phases; treating nextTick as microtask; assuming poll never blocks."

---

## 13. 60-second revision

> - **6 phases:** timers → pending → idle/prepare → poll → check → close.
> - **Each callback** in each phase, drain NT + MQ between.
> - **poll** is the only blocking phase.
> - **`setTimeout/setInterval`** → timers; **`setImmediate`** → check; **`'close'`** → close.
> - **Inside I/O cb:** setImmediate > setTimeout(0) deterministic.
> - **libuv thread pool** (4, `UV_THREADPOOL_SIZE`) for fs/dns/crypto.
> - **Sockets** use kernel epoll/kqueue (no pool).
> - **Trap:** only 3-4 phases; nextTick as microtask; poll never blocks; long sync in cb blocks loop.

---

**Related:** [event-loop-concurrency.md](./event-loop-concurrency.md) · [microtask-macrotask-order.md](./microtask-macrotask-order.md) · [nexttick-vs-setimmediate.md](./nexttick-vs-setimmediate.md) · [setimmediate-vs-settimeout-in-io.md](./setimmediate-vs-settimeout-in-io.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
