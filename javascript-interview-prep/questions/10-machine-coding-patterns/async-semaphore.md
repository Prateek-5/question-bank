# Async Semaphore — bound concurrent async work

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [`04-promises/promise-pool.md`](../04-promises/promise-pool.md), [`concepts/promises.md`](../../concepts/promises.md)
>
> **Source:** Dijkstra's 1965 semaphore concept ported to async JS. Underlies connection pools (pg, mysql2, ioredis), promise pools, rate limiters.

---

## 1. Problem statement

**Signature**
```ts
class Semaphore {
  constructor(permits: number);
  acquire(): Promise<void>;
  release(): void;
  run<T>(task: () => Promise<T>): Promise<T>;
}
```

**Input / Output examples**

| Setup (permits=2)                              | Behaviour                                              |
|------------------------------------------------|---------------------------------------------------------|
| 4 tasks each taking 100ms via `run`             | concurrent ≤ 2; total time ~200ms; FIFO fairness      |
| Task throws inside `run`                        | permit still released via `finally`                    |
| `new Semaphore(0)`                              | acquirers block until external `release()`             |
| `new Semaphore(1)`                              | mutex                                                   |
| Direct `acquire`/`release` without try/finally  | leak risk if caller throws                             |

**Constraints**
- FIFO fairness by default.
- `run(task)` ties acquire + task + release in `try/finally`.
- Mutex = `new Semaphore(1)`.
- Counting semaphore generalizes to weighted/timeout/abort variants.

---

## 2. Plain-English restatement

A bouncer with N stamps. Anyone who walks up gets a stamp if one's free; otherwise queues. Stamps return when patrons leave. The count of stamps in circulation never exceeds N. In async JS: `acquire` resolves immediately if a permit is free, else parks in a FIFO queue. `release` returns one permit, waking the next waiter.

---

## 3. Why this matters in interviews

The **primitive** behind every "limit N concurrent X" question — promise pools, async pools, connection pools, mutex (`Semaphore(1)`), rate limiters at the egress edge. Tests async resource-lifecycle reasoning: who's waiting, who's running, who gets woken next, what happens on rejection. Pool exhaustion = forgot to release = real production outage.

---

## 4. Mental model

```
   Semaphore(2):  permits=2, queue=[]

   t=0   T1.acquire() → permits=1 → T1 runs
   t=0   T2.acquire() → permits=0 → T2 runs
   t=0   T3.acquire() → queue=[grant3] → T3 waits
   t=0   T4.acquire() → queue=[grant3, grant4] → T4 waits

   t=100 T1 done → release()
                   permits=1 → queue.shift() → grant3()
                                                ↑ runs T3's resolve
                                                permits-- → permits=0
                   T3 starts running

   t=100 T2 done → release() → permits=1 → grant4() → permits=0 → T4 runs

   t=200 T3, T4 done → release × 2 → permits=2 (back to initial)
```

**`run(task)`** ties acquire + task + release in try/finally so callers can't leak.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why does `run(task)` use try/finally?
> 2. What's the difference between `Semaphore(1)` and a mutex?
> 3. If a `task` throws, what happens to the permit?

---

## 6. Brute force — walked through

### Wrong attempt 1: `await Promise.all(tasks)`
No concurrency bound — fires all M in parallel. Memory/load explodes for M=10k.

### Wrong attempt 2: counter without queue
Decrement on acquire; if 0, busy-wait or reject. Doesn't wake parked callers when permits return.

### Wrong attempt 3: direct acquire/release without try/finally
```js
await sem.acquire();
const r = await task();    // throws → permit never released
sem.release();             // never reached
```
Leaks permit. Always wrap.

---

## 7. The unlocking insight

> **Counter + FIFO queue of "grant" resolvers. `acquire` either grants immediately or pushes resolver into queue. `release` increments and shifts the next grant. `run(task)` is the only safe public API: try/finally wraps acquire + task + release.**

Three properties:

1. **Counter + queue** — counter for fast path, queue for parked waiters.
2. **FIFO fairness** — `queue.shift()` (head), not `queue.pop()`.
3. **`run(task)`** ties lifecycle with `try/finally` so leaks are impossible.

---

## 8. Solution (annotated)

```js
class Semaphore {
  constructor(permits) {
    if (!Number.isInteger(permits) || permits < 0) {
      throw new TypeError('permits must be a non-negative integer');
    }
    this.permits = permits;
    this.queue = [];                                                  // step 1: FIFO grant functions
  }

  acquire() {
    return new Promise((resolve) => {
      const grant = () => {                                            // step 2: granted = consume permit
        this.permits--;
        resolve();
      };
      if (this.permits > 0) grant();
      else this.queue.push(grant);                                     // step 3: park
    });
  }

  release() {
    this.permits++;                                                    // step 4: return permit
    const next = this.queue.shift();                                   // step 5: wake head (FIFO)
    if (next) next();
  }

  async run(task) {                                                    // step 6: safe public API
    await this.acquire();
    try {
      return await task();
    } finally {
      this.release();                                                   // step 7: ALWAYS release
    }
  }
}
```

**Try it yourself**

```js
const sem = new Semaphore(3);
const urls = [/* 1000 URLs */];

// All 1000 launched but only 3 in-flight at a time
const results = await Promise.all(
  urls.map((u) => sem.run(() => fetch(u).then((r) => r.json())))
);

// Mutex
const mutex = new Semaphore(1);
async function criticalSection() {
  await mutex.run(async () => {
    // only one caller at a time
  });
}
```

---

## 9. Step-by-step dry run

```
permits=2, queue=[]

T1.acquire():  permits=2>0 → grant() → permits--=1; resolve(). T1 runs.
T2.acquire():  permits=1>0 → grant() → permits--=0; resolve(). T2 runs.
T3.acquire():  permits=0  → queue.push(grant3). T3 awaits.
T4.acquire():  permits=0  → queue.push(grant4). T4 awaits.

State: permits=0, queue=[grant3, grant4], running={T1, T2}.

t=100: T1 done → release():
  permits++=1
  queue.shift() = grant3 → grant3():
    permits--=0; resolve T3's awaited promise.
  T3 runs.

t=100: T2 done → release():
  permits++=1
  queue.shift() = grant4 → grant4():
    permits--=0; resolve T4.
  T4 runs.

t=200: T3 done → release(): permits=1, queue empty → no wake.
t=200: T4 done → release(): permits=2, queue empty.

Final: permits=2 (initial state). Concurrent count never exceeded 2. FIFO honored.
```

Failure case:

```
await sem.run(async () => { throw new Error('oops'); }):
  acquire() → permits--=N-1
  try { await task() } → throws
  finally { release() → permits=N, wake next waiter }
  rethrown to caller
```

---

## 10. Common confusion + traps

1. **No try/finally** — `task` throws and permit leaks → pool exhaustion.
2. **`unshift` instead of `shift`** — LIFO; risks starvation under sustained load.
3. **Counter without queue** — late acquirers never wake up.
4. **Releasing twice** — leaks a permit (capacity > N), violates the bound.
5. **`Semaphore(0)` deadlock** — no permits, no acquire can proceed unless external `release()` is called.
6. **Race between acquire-grant-resolve and release** — careful with double-decrement (grant fn decrements; resolved promise doesn't decrement again).
7. **Memory leak via queue** — abandoned callers stuck forever. Add `acquireWith(timeoutMs)` for production.

---

## 11. Senior follow-ups & variants

### Variant 1 — Weighted semaphore
Each task requests `k` permits. Replace `permits--` with `permits -= k`; on release, loop wake-up while head request fits.

### Variant 2 — Timeout / `acquireWith(ms)`
Returns token or `null`; on timeout, splice the grant out of the queue.

### Variant 3 — AbortSignal-aware
Accept `AbortSignal`; if aborted while queued, splice and reject.

### Variant 4 — Reentrant mutex
Track owner; same owner can re-enter without blocking; release decrements depth.

### Variant 5 — Fair vs unfair (LIFO) variants
LIFO is fine only for non-starvation-prone workloads (small/bursty queue).

### Variant 6 — Distributed semaphore
Redis Lua script + token; bounds concurrency across processes.

---

## 12. How to think aloud

> "Counter + FIFO queue. `acquire`: if `permits > 0`, decrement and resolve immediately; else push a grant function into queue. `release`: increment, shift the head of queue (FIFO) and invoke it. The grant function does the `permits--` so we never double-decrement. `run(task)`: try/finally — `acquire`, then `task`, then `release` ALWAYS. Mutex = `Semaphore(1)`. Connection pools = larger semaphore. Trap: skip try/finally → permit leaks → pool exhaustion → 500s in prod. Trap: LIFO under sustained load → starvation. Production: add `acquireWith(timeoutMs)` and AbortSignal support."

---

## 13. 60-second revision

> - **Counter + FIFO queue of grant functions.**
> - **`acquire`:** permits>0 → grant; else `queue.push(grant)`.
> - **`release`:** permits++, `queue.shift()?.()` (FIFO wake).
> - **`run(task)`:** `try { acquire; return await task() } finally { release() }`.
> - **Mutex = `Semaphore(1)`.**
> - **Family:** connection pools, promise-pool, rate limiter (concurrency-based).
> - **Variants:** weighted, timeout, AbortSignal, reentrant, distributed.
> - **Trap:** no try/finally → permit leak; LIFO starvation; counter without queue.

---

**Related:** [`04-promises/promise-pool.md`](../04-promises/promise-pool.md) · [`04-promises/async-mutex.md`](../04-promises/async-mutex.md) · [async-pool.md](./async-pool.md) · [rate-limiter-token-bucket.md](./rate-limiter-token-bucket.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
