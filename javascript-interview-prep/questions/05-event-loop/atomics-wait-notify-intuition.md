# `Atomics.wait` / `Atomics.notify` — cross-worker coordination

> **Difficulty:** Senior   |   **Time:** ~20 min   |   **Prereqs:** [worker-threads-vs-event-loop.md](./worker-threads-vs-event-loop.md), [structured-clone-cost.md](./structured-clone-cost.md)
>
> **Source:** ES2017 `SharedArrayBuffer` + Atomics. Cloudflare, Atlassian, browser-perf roles.

---

## 1. Problem statement

How do workers coordinate via shared memory beyond async `postMessage`? Use `Atomics.wait` to park a worker on a memory location; `Atomics.notify` to wake it.

**Verification examples**

| Setup                                              | Behaviour                                              |
|----------------------------------------------------|---------------------------------------------------------|
| Worker A `Atomics.wait(view, 0, 0)`                  | parks until value at index 0 changes from 0           |
| Worker B `Atomics.store(view, 0, 1); Atomics.notify(view, 0, 1)` | wakes worker A                              |
| Main thread `Atomics.wait`                           | THROWS (main can't block in browser)                   |
| `Atomics.add(view, 0, 1)`                            | atomic increment                                       |
| `Atomics.compareExchange`                            | atomic CAS — building block for lock-free algos       |

**Constraints**
- `Atomics.wait` only works in workers (main thread can't block in browser).
- Requires `SharedArrayBuffer` + `Int32Array`/`BigInt64Array` view.
- Browsers gate SAB behind cross-origin-isolation headers.
- Building block for mutex/condvar/semaphore.

---

## 2. Plain-English restatement

For tight coordination between workers (barriers, mutexes), `postMessage` is too coarse (async, copies). `Atomics.wait` blocks a worker on a memory address until another worker writes there and calls `Atomics.notify`. The blocking primitive for shared memory.

---

## 3. Why this matters in interviews

Tests deep concurrency knowledge. Senior bar: know this is workers-only, requires SAB + cross-origin-isolation, and is the building block for lock-free / blocking-lock data structures.

---

## 4. Mental model

```
   SharedArrayBuffer + Int32Array view = shared memory.
   Both workers see the same bytes.

   Worker A:                              Worker B:
   Atomics.wait(view, 0, 0)               // do work
   ↑ parks (blocks) while                 Atomics.store(view, 0, 1)
     view[0] === 0                        Atomics.notify(view, 0, 1)
                                          ↑ wake 1 waiter on index 0
   ↓ resumes when:
     - view[0] != 0 (someone wrote), OR
     - Atomics.notify hits, OR
     - timeout

   Used to build:
   - Mutex (lock/unlock)
   - Condition variable (wait/signal)
   - Semaphore
   - Barrier
   - Lock-free queues (with Atomics.compareExchange)
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Can the main thread call `Atomics.wait`?
> 2. Why use Atomics instead of regular reads/writes on shared memory?
> 3. Why is SAB gated behind cross-origin-isolation in browsers?

---

## 6. Brute force — walked through

### Wrong attempt 1: regular reads/writes on SAB
Race conditions; reordering by CPU; silent corruption.

### Wrong attempt 2: `postMessage` for tight coordination
Async + copies; too slow for spin-locks.

### Wrong attempt 3: `Atomics.wait` on main thread
Throws (browser). Node allows but blocks event loop — disaster.

---

## 7. The unlocking insight

> **Shared memory needs Atomics for safe access. `wait/notify` is the blocking primitive: park a worker on a memory cell; another worker writes + notifies. Only callable from workers (main thread can't block).**

Three properties:

1. **Atomics for safety** — `add`, `load`, `store`, `compareExchange`.
2. **`wait/notify` for blocking** — coordinate workers without spin.
3. **Main thread can't `wait`** — would freeze the page.

---

## 8. Solution (annotated)

```js
// shared.js
const sab = new SharedArrayBuffer(8);
const view = new Int32Array(sab);

// Worker A (producer)
view[0] = 0;
// do work
Atomics.store(view, 0, 1);                                            // step 1: write atomically
Atomics.notify(view, 0, 1);                                            // step 2: wake 1 waiter

// Worker B (consumer)
Atomics.wait(view, 0, 0);                                              // step 3: block while [0] === 0
// resumes when notified or value changed
console.log('woke up; value =', Atomics.load(view, 0));

// Lock-free counter via CAS
function increment(view, idx) {
  let cur;
  do { cur = Atomics.load(view, idx); }
  while (Atomics.compareExchange(view, idx, cur, cur + 1) !== cur);
}

// Or simpler — atomic add
Atomics.add(view, 0, 1);
```

**Mutex sketch:**

```js
function lock(view, idx) {
  while (Atomics.compareExchange(view, idx, 0, 1) !== 0) {
    Atomics.wait(view, idx, 1);                                        // block until unlocked
  }
}

function unlock(view, idx) {
  Atomics.store(view, idx, 0);
  Atomics.notify(view, idx, 1);                                        // wake one waiter
}
```

---

## 9. Step-by-step dry run

```
Both workers share view (Int32Array on SAB), index 0 starts at 0.

Worker A:
  // wait for B to signal
  Atomics.wait(view, 0, 0);   // PARKS thread; view[0] currently 0 ✓
  
Worker B:
  // do work for 100ms
  Atomics.store(view, 0, 1);   // atomic write
  Atomics.notify(view, 0, 1);  // wake 1 waiter on index 0

A wakes (notify hit), resumes.
A reads Atomics.load(view, 0) → 1. Proceeds.

Mutex sequence:
A: lock(view, 0) → compareExchange(0→1) succeeds; A holds lock.
B: lock(view, 0) → compareExchange(0→1) fails (already 1).
B: Atomics.wait(view, 0, 1) → parks.
A: unlock(view, 0) → store(view, 0, 0); notify → wakes B.
B: loops, compareExchange(0→1) succeeds; B holds lock.
```

---

## 10. Common confusion + traps

1. **`Atomics.wait` on main** — throws (browser); freezes (Node).
2. **Regular reads on shared memory** — racy; use Atomics.load.
3. **SAB without cross-origin-iso** — browser blocks.
4. **`notify` count** — pass `1` to wake one, `Infinity` for all.
5. **Spin without wait** — burns CPU; use wait/notify.
6. **Float32Array** — `Atomics` only works on Int32/BigInt64/etc.
7. **`Atomics.wait` returns string** — `'ok'`, `'not-equal'`, `'timed-out'`.

---

## 11. Senior follow-ups & variants

### Variant 1 — Mutex (above)
`lock`/`unlock` via `compareExchange` + wait/notify.

### Variant 2 — Condition variable
Wait on a separate "condition" cell; signal via store + notify.

### Variant 3 — Counting semaphore
`compareExchange` to decrement; wait if 0.

### Variant 4 — Lock-free queue (SPSC / MPMC)
`compareExchange` on head/tail pointers. Research-grade complexity.

### Variant 5 — Cross-origin isolation headers
`Cross-Origin-Opener-Policy: same-origin` + `Cross-Origin-Embedder-Policy: require-corp`. Required for SAB in browsers since Spectre.

### Variant 6 — `Atomics.waitAsync` (newer)
Non-blocking — returns a Promise. Allows main thread to coordinate without blocking.

---

## 12. How to think aloud

> "For tight coordination between workers, `postMessage` is too coarse — async, copies. `Atomics.wait` parks a worker on a memory address; another worker writes + `Atomics.notify` wakes it. Workers ONLY — main thread can't block (browser throws; Node would freeze event loop). Build mutex with `compareExchange` + wait/notify. Cross-origin isolation headers required in browsers since Spectre. `Atomics.waitAsync` (newer) is the non-blocking Promise-returning variant, usable from main. Trap: regular memory access without Atomics (race); wait on main thread; SAB without iso headers."

---

## 13. 60-second revision

> - **`Atomics.wait(view, idx, expected)`** parks if `view[idx] === expected`.
> - **`Atomics.notify(view, idx, count)`** wakes `count` waiters.
> - **Workers only** — main thread `wait` throws (browser) or freezes (Node).
> - **`SharedArrayBuffer` + Int32Array view** required.
> - **Browsers gate** SAB behind cross-origin-isolation headers (post-Spectre).
> - **Building blocks:** mutex, condvar, semaphore, lock-free queues.
> - **`Atomics.waitAsync`** = non-blocking Promise variant for main thread.
> - **Trap:** raw reads/writes (race); wait on main; no cross-origin-iso.

---

**Related:** [worker-threads-vs-event-loop.md](./worker-threads-vs-event-loop.md) · [worker-pool-implementation.md](./worker-pool-implementation.md) · [structured-clone-cost.md](./structured-clone-cost.md) · [`10-machine-coding-patterns/async-semaphore.md`](../10-machine-coding-patterns/async-semaphore.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
