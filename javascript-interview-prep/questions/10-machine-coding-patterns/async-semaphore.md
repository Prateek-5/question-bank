# Async Semaphore

## Source / Origin
- Classic concurrency primitive (Dijkstra, 1965); ported to async JS for limiting concurrent IO.
- Variants asked at: Stripe, Atlassian, Cloudflare, Razorpay, ThoughtSpot.
- Concept reference: `concepts/promises.md`, `concepts/event-loop.md`.

## Why this question matters in interviews
Semaphore is the *primitive* behind every "limit N concurrent X" question — promise pools, async pools, connection pools, rate limiters at the egress edge. If you build it once cleanly you've already solved promise-pool, async-pool, mutex (semaphore with permits=1), and bounded request coalescing. Interviewers ask it to test that you can reason about async resource lifecycles: who's waiting, who's running, who gets woken up next, what happens on rejection.

## Concepts involved

### Syntax to lock in
```js
class Semaphore {
  constructor(permits) {
    this.permits = permits;            // free slots
    this.queue = [];                   // FIFO of resolve fns waiting for a permit
  }
  async acquire() {
    if (this.permits > 0) { this.permits--; return; }
    await new Promise(res => this.queue.push(res));
    this.permits--;                     // we were granted; consume the slot we were given
  }
  release() {
    this.permits++;
    const next = this.queue.shift();
    if (next) next();                   // wake exactly one waiter (FIFO)
  }
  async run(task) {
    await this.acquire();
    try { return await task(); }
    finally { this.release(); }
  }
}
```

### Edge cases / interview traps
1. **Forgetting `finally` to release.** If `task()` throws and you `release()` only on success, the slot is leaked forever. Must use `try/finally`.
2. **Rejection inside `acquire()`.** If we ever reject the queued promise (e.g., on close), `permits` may double-count. Track explicit `cancelled` flag per waiter.
3. **FIFO vs LIFO fairness.** Default to FIFO — surprises candidates who shift then `unshift`. LIFO is fine only for opportunistic, non-starvation-prone workloads.
4. **Permits = 0 deadlock.** `new Semaphore(0)` means no one can acquire until somebody calls `release()`. Common with "wait for signal" patterns.
5. **`acquire` race with `release`.** After `await new Promise(res => queue.push(res))` resolves, the `permits--` adjusts the counter we *just* received. Don't accidentally double-decrement by also subtracting at queue-grant time.
6. **Memory leak via `queue`.** Long-lived semaphore with abandoned callers → callbacks stuck forever. Provide `tryAcquire()` and timeout variants for production.

## Mental Model

A semaphore is a **bouncer at a nightclub with N stamps**. The bouncer hands a stamp to anyone who walks up *if* a stamp is free. If all N stamps are out, the patron stands in line. When someone leaves and returns their stamp, the bouncer hands it to the next person in line. The count of stamps in circulation never exceeds N.

```
   permits=2, queue=[]                  semaphore.acquire()  → permits=1
   permits=1, queue=[]                  semaphore.acquire()  → permits=0
   permits=0, queue=[res3, res4]        semaphore.acquire() x2 → both wait
   permits=0, queue=[res4]              release() → wakes res3, permits stays 0
                                                    (res3 will do permits-- itself)
```

## Why interviewers care

- **Async lifecycle reasoning.** Who holds resources, who releases them, what happens on failure.
- **Foundation pattern.** Mutex = Semaphore(1). Promise pool = Semaphore + task queue. Rate limiter (concurrency-based) = Semaphore.
- **Production literacy.** Connection pools (pg, mysql2, ioredis) all use semaphores internally; failure to release = pool exhaustion = 500s.

## Common beginner confusion

- **"Just use Promise.all with a limit."** No — `Promise.all` doesn't limit concurrency; it just awaits all. You need an explicit semaphore to bound active count.
- **"Counter increment is enough."** Without a queue, late-arriving acquirers don't get woken when releases happen.
- **"Use a global counter."** Module-level state is fragile across tests and worker boundaries. Always instantiate.
- **"Releasing twice doesn't hurt."** It does — you've leaked a permit (capacity > N), violating the bound.

## Brute force approach
"I'll await each task one at a time" — sequential, ignores concurrency. Wrong: you wanted N parallel.

"I'll use `Promise.all(tasks)` with no bound" — explodes if `tasks.length > N`, e.g., 10k DB connections.

## Optimal approach
A FIFO-fair semaphore with `acquire`/`release`/`run`. `run(task)` is the safe public API — it ties acquire+task+release in a single try/finally so callers can't leak permits.

## Solution (JavaScript)

```js
class Semaphore {
  constructor(permits) {
    if (!Number.isInteger(permits) || permits < 0) throw new TypeError('permits must be a non-negative integer');
    this.permits = permits;
    this.queue = [];
  }

  acquire() {
    return new Promise((resolve) => {
      const grant = () => { this.permits--; resolve(); };
      if (this.permits > 0) grant();
      else this.queue.push(grant);
    });
  }

  release() {
    this.permits++;
    const next = this.queue.shift();
    if (next) next();
  }

  async run(task) {
    await this.acquire();
    try { return await task(); }
    finally { this.release(); }
  }
}

// Usage: limit 3 concurrent HTTP calls
const sem = new Semaphore(3);
const urls = [/* 1000 URLs */];
const results = await Promise.all(urls.map(u => sem.run(() => fetch(u).then(r => r.json()))));
```

## Step-by-step dry run

Start with `permits=2`, four tasks `T1..T4` that each take 100ms.

```
t=0:  T1.acquire() → permits=1 → T1 runs
t=0:  T2.acquire() → permits=0 → T2 runs
t=0:  T3.acquire() → queue=[res3] → T3 waits
t=0:  T4.acquire() → queue=[res3,res4] → T4 waits
t=100: T1 done → release() → permits=1; queue.shift() → grant res3
                grant: permits-- → permits=0 → T3 runs
t=100: T2 done → release() → permits=1; queue.shift() → grant res4
                grant: permits-- → permits=0 → T4 runs
t=200: T3 done → release() → permits=1
t=200: T4 done → release() → permits=2 (back to initial)
```

Concurrency capped at 2; FIFO order honored.

## How to think aloud in the interview

> "Semaphore is N permits with a FIFO queue. acquire takes one if free, else parks. release returns one and wakes the head of the queue. I'll provide `run` so callers can't leak — acquire + task + release in try/finally. Mutex is just `new Semaphore(1)`. For a production version I'd add `acquireWith(timeoutMs)` and an abort signal, but I'll keep this clean for now."

## Important takeaways

- **Mutex = Semaphore(1).** Don't write two implementations.
- **`run(task)` is the only safe public API.** Direct `acquire()`/`release()` is for advanced callers who promise to pair them.
- **FIFO is the default contract.** Anything else needs justification.
- **Pool exhaustion = bug.** If permits never come back to N, someone forgot `finally`.

## Variants

- **Weighted semaphore** — each task requests `k` permits (e.g., big batch = 4 permits, tiny = 1). Replace `permits--` with `permits -= k`; on release, loop the wake-up while the head request fits.
- **Timeout variant** — `acquire(timeoutMs)` returns a token or `null`; on timeout, remove your `grant` from the queue.
- **AbortSignal-aware** — accept an `AbortSignal`; if aborted while queued, splice out and reject.
- **Reentrant mutex** — track owner; same owner can re-enter without blocking; release decrements depth.

## Revision notes

```
Semaphore(N):
  acquire(): permits>0 ? grant : queue.push(grant)
  release(): permits++; queue.shift()?.()
  run(t):    try { await acquire(); return await t(); } finally { release(); }
  mutex = Semaphore(1)
  pool exhaustion = forgot finally
  FIFO fairness; weighted/timeout/abort are senior variants
```
