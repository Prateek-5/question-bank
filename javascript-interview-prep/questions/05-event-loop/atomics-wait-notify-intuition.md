# `Atomics.wait` / `Atomics.notify` — Cross-Worker Coordination

## Source / Origin
- ES2017 `SharedArrayBuffer` + Atomics.
- Asked at: Cloudflare, Atlassian, AWS, browser-perf-focused roles.
- Concept reference: `concepts/event-loop.md`, sibling `worker-threads-vs-event-loop.md`.

## Why this question matters in interviews
`postMessage` between workers is async and copies/transfers data. For tight coordination — barriers, mutexes, signal-after-write — you need *blocking* primitives on shared memory. `Atomics.wait` lets a worker park on a memory location until another worker `Atomics.notify`s it. Senior bar: you know (1) this only works in workers (not the main thread, which can't block); (2) it requires `SharedArrayBuffer`; (3) modern browsers gate SAB behind cross-origin isolation headers; (4) wait/notify is the building block for mutex/condvar/semaphore.

## Concepts involved

### Syntax to lock in
```js
// shared.js
export const sab = new SharedArrayBuffer(8);              // 8 bytes = 2 × Int32
export const counter = new Int32Array(sab);               // [counter, flag]

// worker A
import { counter } from './shared.js';
Atomics.add(counter, 0, 1);                                // counter[0]++  atomic
Atomics.store(counter, 1, 1);                              // flag = 1
Atomics.notify(counter, 1, 1);                             // wake 1 waiter on index 1

// worker B
import { counter } from './shared.js';
Atomics.wait(counter, 1, 0);                               // wait while counter[1] === 0
// resumes when counter[1] !== 0 OR a notify hits us
console.log('counter:', Atomics.load(counter, 0));
```

### Edge cases / interview traps
1. **Main thread cannot `Atomics.wait`.** Doing so throws `TypeError`. Use `Atomics.waitAsync` (returns a Promise) on main if available.
2. **`SharedArrayBuffer` is gated.** Browsers require `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp` headers; introduced after Spectre.
3. **`wait(view, index, expected, timeout?)`** — if `view[index]` is already `!== expected`, returns `'not-equal'` immediately. Otherwise blocks until notify or timeout.
4. **`notify(view, index, count?)`** — wakes at most `count` waiters; default = Infinity.
5. **Spurious wake-ups not specified to occur but always re-check** the condition in a loop.
6. **Atomic primitives only on `Int8Array | Uint8Array | Int16Array | Uint16Array | Int32Array | Uint32Array | BigInt64Array | BigUint64Array`** views over SAB. Not floats.
7. **`Atomics.compareExchange`** — the CAS primitive for lock-free algorithms.
8. **Performance** — atomic ops are slower than plain reads; use only when you need ordering.

## Mental Model

A **shared whiteboard** where workers can both write and "park sleeping at a cell" until something changes:

```
   SharedArrayBuffer (visible to all workers):
   +----+----+----+----+
   | 0  | 0  | 0  | 0  |     (Int32 view)
   +----+----+----+----+

   Worker B: Atomics.wait(view, 1, 0)
              ↓
   parks until view[1] changes OR notify(view, 1, ...)

   Worker A: Atomics.store(view, 1, 42);
             Atomics.notify(view, 1, 1);
              ↓
   B wakes up; reads view[1] === 42; proceeds.
```

This is the *exact* primitive operating systems use for futex (Linux). It's how mutexes, semaphores, condition variables are built — JS just exposes it directly.

## Why interviewers care

- **Low-level concurrency literacy** — most JS devs never touch Atomics.
- **CPU/CPU coordination** — the only way to do tight cross-worker handshakes without postMessage overhead.
- **Awareness of platform gating** — cross-origin isolation, main-thread restriction.

## Common beginner confusion

- **"I can use Atomics.wait on the main thread."** No — only workers.
- **"SharedArrayBuffer works anywhere."** Gated by COOP/COEP headers in browsers; default not available.
- **"Atomic = transactional."** Atomic = indivisible single operation. Doesn't compose; for multi-step coordination use `compareExchange` or wait/notify.
- **"Notify counts must equal wait count."** No — notify wakes *up to* `count` waiters; extras keep waiting.
- **"Wait is the same as setTimeout."** Wait is *blocking* — the worker thread halts. setTimeout suspends a callback without blocking.

## Brute force approach

```js
// Spin-wait — wastes CPU, never yields to event loop
while (Atomics.load(view, 1) === 0) { /* burn CPU */ }
```

100% CPU. `Atomics.wait` lets the thread sleep until something changes.

## Optimal approach

`Atomics.wait` in workers to block until a condition is met; `Atomics.notify` from another worker to release. Build mutexes/semaphores on top via `compareExchange`.

## Solution (JavaScript) — barrier and mutex

```js
// Barrier: N workers all wait at a checkpoint until everyone arrives
class Barrier {
  constructor(sab, slot, count) {
    this.view = new Int32Array(sab);
    this.slot = slot;
    this.count = count;
  }
  arrive() {
    const arrived = Atomics.add(this.view, this.slot, 1) + 1;
    if (arrived === this.count) {
      Atomics.store(this.view, this.slot, 0);          // reset for next phase
      Atomics.notify(this.view, this.slot, this.count - 1);
    } else {
      while (Atomics.load(this.view, this.slot) !== 0) {
        Atomics.wait(this.view, this.slot, arrived);
      }
    }
  }
}

// Mutex (toy) via compareExchange + wait/notify
class SharedMutex {
  constructor(sab, slot) {
    this.view = new Int32Array(sab);
    this.slot = slot;
  }
  lock() {
    while (true) {
      const prev = Atomics.compareExchange(this.view, this.slot, 0, 1);
      if (prev === 0) return;                                          // got it
      Atomics.wait(this.view, this.slot, 1);                           // wait while 1
    }
  }
  unlock() {
    Atomics.store(this.view, this.slot, 0);
    Atomics.notify(this.view, this.slot, 1);
  }
}

// Main thread (no wait) — use waitAsync
async function waitOnMain(view, idx, expected) {
  const { async, value } = Atomics.waitAsync(view, idx, expected);
  if (!async) return value;                                            // already !== expected
  return value;                                                        // Promise<'ok'|'timed-out'|'not-equal'>
}
```

## Step-by-step dry run

Barrier with 3 workers; one of them arrives last.

```
t=0   counter = 0
      worker A: arrive() → atomic add → counter=1 → arrived=1 ≠ 3 → wait while counter !== 0
      worker B: arrive() → atomic add → counter=2 → arrived=2 ≠ 3 → wait while counter !== 0
t=50  worker C: arrive() → atomic add → counter=3 → arrived=3 == 3
                → store counter=0 (reset for next phase)
                → notify(slot, 2) → wake A and B
      A's wait returns; A re-checks counter === 0 → exits while loop
      B's wait returns; B re-checks counter === 0 → exits while loop
      all 3 proceed past the barrier
```

## How to think aloud in the interview

> "Atomics.wait blocks a worker on a memory location until either a value change or `Atomics.notify`. Main thread can't `wait` — would block UI. Used to build mutexes (compareExchange to claim; wait on busy; notify on unlock), semaphores, barriers. SharedArrayBuffer is the substrate — gated by COOP/COEP in browsers post-Spectre. For main-thread async wait, `Atomics.waitAsync` returns a Promise. This is the futex primitive — operating-system-grade synchronization, available in JS workers."

## Important takeaways

- **Workers only** for `wait`; main uses `waitAsync`.
- **`SharedArrayBuffer` required** — gated by COOP/COEP.
- **Typed array views over SAB** — Int8 to BigUint64.
- **`compareExchange` for CAS-based algorithms.**
- **Always re-check the condition** after wait (spurious wakes possible).
- **Build mutex/semaphore/barrier on top.**

## Variants

- **`waitAsync(view, idx, expected)`** — main-thread version; returns `{async, value}` where `value` is a Promise.
- **Lock-free queues** — using `compareExchange` for enqueue/dequeue.
- **Condition variable pattern** — wait + notify with a "predicate" Int32 cell.
- **Cross-process** — *not* supported; SAB is per-process. Use `MessageChannel` or shared memory at OS level.

## Revision notes

```
SharedArrayBuffer + Atomics (worker concurrency):
  Atomics.wait(view, idx, expected[, timeout]) — block worker
  Atomics.notify(view, idx, count) — wake up to count waiters
  Atomics.compareExchange(view, idx, expected, replacement) — CAS
  Atomics.add/sub/load/store/or/and/xor — atomic ops
  
  TRAPS:
  - wait only in workers; main uses waitAsync (Promise)
  - SAB needs COOP/COEP in browsers
  - re-check predicate after wait (spurious wake)
  - only integer typed arrays
  
  BUILD:
  - mutex: compareExchange + wait/notify
  - barrier: counter + reset + notify N
  - condvar: predicate Int32 + wait + notify
```
