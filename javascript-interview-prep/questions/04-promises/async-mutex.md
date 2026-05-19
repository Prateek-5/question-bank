# Implement an Async Mutex — `runExclusive(fn)` for single-thread serialization

> **Difficulty:** Medium-Hard   |   **Time:** ~25 min   |   **Prereqs:** [deferred-with-resolvers.md](./deferred-with-resolvers.md), [`10-machine-coding-patterns/async-semaphore.md`](../10-machine-coding-patterns/async-semaphore.md), [`concepts/promises.md`](../../concepts/promises.md)
>
> **Source:** `async-mutex` npm package; lock primitive in any async runtime. Asked at Razorpay, Stripe, Atlassian, Booking.

---

## 1. Problem statement

**Signature**
```ts
class Mutex {
  acquire(): Promise<() => void>;        // returns release function
  runExclusive<T>(fn: () => Promise<T>): Promise<T>;
}
```

**Input / Output examples**

| Setup                                                                   | Behaviour                                              |
|--------------------------------------------------------------------------|---------------------------------------------------------|
| `m.runExclusive(work)` × 3 in parallel                                  | Three calls run strictly serially (A → B → C)          |
| `await Promise.all([m.runExclusive(safeIncrement)] × 10)` on counter=0 | Final counter = 10 (no lost updates)                   |
| `runExclusive(throws)` followed by another `runExclusive`               | Lock released by finally; second call proceeds        |
| Same task calls `runExclusive` while holding the lock                   | **Deadlock** (standard mutex is not reentrant)         |
| `Mutex` = `Semaphore(1)` with friendlier API                            | Identical semantics; different ergonomic surface       |

**Constraints**
- FIFO fairness — first waiter gets the lock next.
- `runExclusive(fn)` is the safe public API (try/finally guarantees release).
- Not reentrant — same task acquiring twice deadlocks.
- In-process only — for cross-process, use Redis SETNX + fencing token.

---

## 2. Plain-English restatement

A mutex lets you ensure only **one** async task at a time can run a critical section. The pattern is `runExclusive(fn)` — pass in your work, the mutex acquires the lock, runs your work, releases the lock. Other callers queue up; FIFO order.

JavaScript is single-threaded, but `await` points are interleaving points — two parallel async functions can both `read x`, both `await something`, then both `write x + 1`, losing one update. A mutex serializes the read-modify-write so only one task is in the critical section at a time.

---

## 3. Why this matters in interviews

"I want to make sure only one request mutates this state at a time within a single Node process" — that's a mutex. Semaphore(1), but worth its own implementation because (1) the API is `lock/unlock` not `acquire/release`; (2) you usually want `runExclusive(fn)` to enforce balanced lock/unlock via try/finally; (3) candidates routinely confuse "I awaited it" with "I locked it." Mutex tests whether you understand that Node's single-threaded *cooperative* concurrency still needs explicit locking for read-modify-write across await points.

---

## 4. Mental model

A **single key with a FIFO line**:

```
   t=0   A: mutex.acquire() → _locked=false → take key → _locked=true → return release_A
         A runs work
   t=0   B: mutex.acquire() → _locked=true → queue.push(resolveB) → await
   t=0   C: mutex.acquire() → _locked=true → queue.push(resolveC) → await
   
   t=50  A: release_A() → queue.shift() → resolveB(releaseFn) → _locked stays true
         B's await resolves with releaseFn → B runs work
   t=100 B: release_B() → resolveC(releaseFn) → _locked stays true
         C runs work
   t=150 C: release_C() → queue empty → _locked=false
```

The lock state machine: `free → owned → owned (handed off) → ... → free`.

**Key insight:** the lock stays `_locked=true` while handing off to the next waiter. It only goes back to `false` when the queue drains. This avoids a race window where a new acquirer could sneak in between release and the next handoff.

**Mutex = Semaphore(1)**: identical semantics. The mutex API (`runExclusive`) is just ergonomically cleaner for the binary case.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. JavaScript is single-threaded — why would you ever need a mutex?
> 2. If `fn()` inside `runExclusive` throws, does the lock release?
> 3. What happens if the same task calls `runExclusive` while it already holds the lock?

---

## 6. Brute force — walked through

### Wrong attempt 1: "single-threaded JS doesn't need locks"

```js
async function increment() {
  const v = await db.get('counter');   // await 1
  await db.set('counter', v + 1);       // await 2
}

// 10 parallel calls
await Promise.all(Array(10).fill(0).map(increment));
// counter could be 1, not 10 — lost updates
```

**Wrong.** JS is single-threaded but `await` is an interleaving point. Two parallel `increment()` calls can both read counter=0, both `await`, both write counter=1. Lost update. You need a mutex for read-modify-write across awaits.

### Wrong attempt 2: boolean flag without queue

```js
let locked = false;
async function lock() {
  while (locked) await new Promise(r => setTimeout(r, 0));   // BUG: spin
  locked = true;
}
function unlock() { locked = false; }
```

Busy-waits (microtask spin). Two simultaneous waiters race for the unset moment. Order is undefined. Wakeups don't fan out cleanly. Use a proper queue.

### Wrong attempt 3: `Promise.race` to serialize

```js
let chain = Promise.resolve();
function serialize(fn) {
  chain = chain.then(fn);
  return chain;
}
```

This chains tasks but isn't a mutex — it doesn't expose an explicit `acquire`/`release`. Works for simple serialization but breaks if you want `acquire` without immediate work (e.g., reading a shared resource manually).

### Wrong attempt 4: forget `finally` on release

```js
async runExclusive(fn) {
  const release = await this.acquire();
  const result = await fn();
  release();   // BUG: if fn() throws, lock never released
  return result;
}
```

If `fn` throws, the lock stays held forever — every future caller deadlocks. Always use `try { ... } finally { release(); }`.

---

## 7. The unlocking insight

> **A FIFO queue of "next waiter" resolvers + a single `_locked` boolean. `acquire` takes the lock if free, else queues. `release` resolves the next waiter (keeping `_locked=true` during handoff). `runExclusive` wraps acquire/work/release in try/finally so callers can't leak.**

The shape:

```js
class Mutex {
  constructor() { this._queue = []; this._locked = false; }
  acquire() {
    if (!this._locked) { this._locked = true; return Promise.resolve(() => this._release()); }
    return new Promise(res => this._queue.push(() => res(() => this._release())));
  }
  _release() {
    const next = this._queue.shift();
    if (next) next();              // hand the lock to next waiter (still _locked=true)
    else this._locked = false;
  }
  async runExclusive(fn) {
    const release = await this.acquire();
    try { return await fn(); }
    finally { release(); }
  }
}
```

Three properties:

1. **FIFO via array shift.** First waiter gets the lock next. `unshift` (LIFO) is fine for some workloads but can starve waiters.

2. **`_locked` stays true during handoffs.** When `_release` shifts the queue and resolves the next waiter, the lock state stays true. No window where a new acquirer could sneak in. Only when the queue is empty does `_locked` go back to false.

3. **`runExclusive(fn)` is the safe public API.** Direct `acquire`/`release` is for advanced callers who promise to pair them; a single missed release deadlocks everything.

**JS still needs locks.** The `await` point is where interleaving happens. Two parallel async functions doing `read → await → write` need a mutex around the entire transaction, not just the writes.

---

## 8. Solution (annotated)

```js
class Mutex {
  constructor() {
    this._queue = [];                              // step 1: FIFO of next-waiter resolvers
    this._locked = false;
  }

  acquire() {
    if (!this._locked) {                            // step 2: lock is free
      this._locked = true;
      return Promise.resolve(() => this._release()); //         return release fn immediately
    }
    return new Promise((res) => {                    // step 3: lock held — queue waiter
      this._queue.push(() => res(() => this._release()));
      //              ^ when shifted, give release fn to the waiter
    });
  }

  _release() {
    const next = this._queue.shift();                // step 4: hand off to next waiter
    if (next) next();                                 //         _locked stays true
    else this._locked = false;                        // step 5: queue empty — go back to free
  }

  async runExclusive(fn) {                            // step 6: safe public API
    const release = await this.acquire();
    try { return await fn(); }
    finally { release(); }                             //         ALWAYS release, even on throw
  }
}

// Usage — safe counter increment under concurrency
const mutex = new Mutex();
async function safeIncrement() {
  return mutex.runExclusive(async () => {
    const v = await db.get('counter');
    await db.set('counter', v + 1);
  });
}

await Promise.all(Array(10).fill(0).map(safeIncrement));
// counter === 10 (no lost updates)
```

**Try it yourself**

```js
const m = new Mutex();
const work = (label, ms) => () =>
  new Promise((r) => setTimeout(() => { console.log('done', label); r(); }, ms));

// Three parallel runExclusive calls — execute serially
m.runExclusive(work('A', 50));
m.runExclusive(work('B', 50));
m.runExclusive(work('C', 50));
// done A   (t=50)
// done B   (t=100)
// done C   (t=150)

// Throw safety
try {
  await m.runExclusive(async () => { throw new Error('oops'); });
} catch {}
// Lock is released; next runExclusive proceeds
await m.runExclusive(async () => console.log('next runs fine'));
```

---

## 9. Step-by-step dry run

Input: 3 parallel `runExclusive(work)` where `work` takes 50ms each.

Values-first trace:

| Time | Event                                                                          | `_locked` | `_queue` (next-waiter resolvers) |
|------|--------------------------------------------------------------------------------|------------|------------------------------------|
| 0    | A: `acquire()` — `_locked=false`, take, return `release_A`. A runs work       | true       | []                                 |
| 0    | B: `acquire()` — `_locked=true`, push to queue                                | true       | [resolveB]                         |
| 0    | C: `acquire()` — `_locked=true`, push to queue                                | true       | [resolveB, resolveC]               |
| 50   | A: work done → `finally` → `release_A()` → `_release()` → shift `resolveB` → resolveB resolves with `release_B`; `_locked` stays true | true | [resolveC] |
| 50   | B: `acquire()` resolves with `release_B`. B runs work                          | true       | [resolveC]                         |
| 100  | B: `finally` → `release_B()` → shift `resolveC` → resolveC resolves; `_locked` stays true | true | []                          |
| 100  | C: `acquire()` resolves with `release_C`. C runs work                          | true       | []                                 |
| 150  | C: `finally` → `release_C()` → queue empty → `_locked = false`                | false      | []                                 |

A → B → C run strictly serially in FIFO order. Three parallel calls become three sequential executions.

---

## 10. Common confusion + traps

1. **"JS is single-threaded so I don't need a mutex."**
   Wrong for any code with `await` between read and write. Two parallel handlers both `read counter`, await, `write counter+1` → lost update.

2. **Just a boolean flag without a queue.**
   Late callers spin or never get woken. Use FIFO queue.

3. **`Promise.race` to serialize.**
   Race fires on first resolve; not serialization.

4. **Mutex blocks the event loop.**
   No — other callers wait via a Promise. The event loop continues to service other work.

5. **`acquire` returns the lock.**
   It returns the **release function**. Holding the lock is implicit in being past the `await`.

6. **Not reentrant.**
   Standard mutex: same task calling `runExclusive` while holding deadlocks. Use a reentrant variant if you need re-entry (track owner + depth).

7. **`runExclusive` without try/finally.**
   If `fn` throws, lock never releases. Always wrap.

8. **Cross-process.**
   This is in-process only. Cross-process needs Redis SETNX + TTL + fencing token. See [`10-machine-coding-patterns/leader-election-toy.md`](../10-machine-coding-patterns/leader-election-toy.md).

---

## 11. Senior follow-ups & variants

### Variant 1 — Timed `acquire(timeoutMs)`

```js
acquireWithTimeout(ms) {
  if (!this._locked) { this._locked = true; return Promise.resolve(() => this._release()); }
  return new Promise((resolve, reject) => {
    const entry = () => resolve(() => this._release());
    this._queue.push(entry);
    const t = setTimeout(() => {
      const i = this._queue.indexOf(entry);
      if (i >= 0) { this._queue.splice(i, 1); reject(new Error('acquire timeout')); }
    }, ms);
    // ... clear timer on success in entry...
  });
}
```

Reject if no lock within window.

### Variant 2 — AbortSignal-aware

```js
acquireWithSignal(signal) {
  if (signal?.aborted) return Promise.reject(signal.reason);
  if (!this._locked) { this._locked = true; return Promise.resolve(() => this._release()); }
  return new Promise((resolve, reject) => {
    const entry = () => resolve(() => this._release());
    this._queue.push(entry);
    signal?.addEventListener('abort', () => {
      const i = this._queue.indexOf(entry);
      if (i >= 0) { this._queue.splice(i, 1); reject(signal.reason); }
    }, { once: true });
  });
}
```

Caller can cancel while queued.

### Variant 3 — Reentrant mutex

```js
class ReentrantMutex {
  constructor() { this._owner = null; this._depth = 0; this._queue = []; }
  async runExclusive(fn, ownerKey) {
    if (this._owner === ownerKey) {
      this._depth++;
      try { return await fn(); }
      finally { this._depth--; }
    }
    // ... standard acquire logic ...
    this._owner = ownerKey;
    this._depth = 1;
    try { return await fn(); }
    finally {
      this._depth--;
      if (this._depth === 0) { this._owner = null; this._release(); }
    }
  }
}
```

Same owner can re-enter; tracks depth.

### Variant 4 — Read-write lock (multiple readers, one writer)

```js
class RWLock {
  constructor() { this._readers = 0; this._writer = false; this._queue = []; }
  async runReader(fn) { /* ... allow multiple readers ... */ }
  async runWriter(fn) { /* ... exclusive ... */ }
}
```

Useful for read-heavy state (e.g., config cache).

### Variant 5 — Priority mutex

High-priority waiters skip ahead of normal queue. Built on a priority heap instead of FIFO array. See [priority-async-queue.md](./priority-async-queue.md) for the heap shape.

### Variant 6 — Cross-process via Redis

```js
async acquireDistributed(key, ttl) {
  const fencingToken = await redis.incr(`${key}:fence`);
  while (!(await redis.set(key, fencingToken, 'NX', 'PX', ttl))) {
    await sleep(100);
  }
  return { release: () => redis.del(key), fencingToken };
}
```

Cross-process locks via Redis SETNX + TTL + fencing token. See [`10-machine-coding-patterns/leader-election-toy.md`](../10-machine-coding-patterns/leader-election-toy.md).

---

## 12. How to think aloud in the interview

> "Mutex = Semaphore(1) with a friendlier API. `acquire` returns a release function. `runExclusive(fn)` wraps acquire + task + release in try/finally so callers can't leak. The lock state stays `true` while handing from caller to caller — only goes false when the queue drains. JS being single-threaded doesn't avoid races; any read-modify-write across an `await` is a race without locking. For cross-process, this won't work — I'd reach for Redis SETNX + TTL + fencing. Variants: timed acquire, AbortSignal-aware, reentrant (track owner+depth), read-write lock (many readers / one writer), priority queue instead of FIFO."

---

## 13. 60-second revision

> - **Mutex = Semaphore(1).** FIFO queue + boolean `_locked`.
> - **`acquire()` returns the release function** (or queues if locked).
> - **`_release()` shifts queue and resolves next waiter** — `_locked` stays true during handoff.
> - **`runExclusive(fn)` is the safe API:** try/finally guarantees release.
> - **JS races happen ACROSS `await`** — mutex is needed for read-modify-write.
> - **Not reentrant by default** — same task acquiring twice deadlocks.
> - **In-process only** — cross-process needs Redis SETNX + fencing.
> - **Variants:** timed, abort-aware, RW-lock, reentrant, priority.
> - **Trap:** boolean flag without queue; `runExclusive` without try/finally; thinking single-thread = no races.

---

**Related:** [deferred-with-resolvers.md](./deferred-with-resolvers.md) · [priority-async-queue.md](./priority-async-queue.md) · [abortcontroller-fanout.md](./abortcontroller-fanout.md) · [`10-machine-coding-patterns/async-semaphore.md`](../10-machine-coding-patterns/async-semaphore.md) · [`10-machine-coding-patterns/leader-election-toy.md`](../10-machine-coding-patterns/leader-election-toy.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
