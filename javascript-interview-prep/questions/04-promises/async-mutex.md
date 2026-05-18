# Async Mutex (Promise-Based Lock)

## Source / Origin
- `async-mutex` npm package; lock primitive in any async runtime.
- Asked at: Razorpay, Stripe, Atlassian, Booking.
- Concept reference: `concepts/promises.md`, sibling `10-machine-coding-patterns/async-semaphore.md`.

## Why this question matters in interviews
"I want to make sure only one request mutates this state at a time within a single Node process" — that's a mutex. Semaphore(1), but worth its own implementation because (1) the API is `lock/unlock` not `acquire/release`; (2) you usually want `runExclusive(fn)` to enforce balanced lock/unlock via try/finally; (3) candidates routinely confuse "I awaited it" with "I locked it." Mutex tests whether you understand that Node's single-threaded *cooperative* concurrency still needs explicit locking for read-modify-write across await points.

## Concepts involved

### Syntax to lock in
```js
class Mutex {
  constructor() {
    this._queue = [];
    this._locked = false;
  }

  async acquire() {
    if (!this._locked) { this._locked = true; return () => this._release(); }
    await new Promise(res => this._queue.push(res));
    return () => this._release();
  }

  _release() {
    const next = this._queue.shift();
    if (next) next();           // hand the lock to the next waiter (still _locked=true)
    else this._locked = false;
  }

  async runExclusive(fn) {
    const release = await this.acquire();
    try { return await fn(); }
    finally { release(); }
  }
}
```

### Edge cases / interview traps
1. **`runExclusive` is the only safe API.** Direct `acquire`/`release` is fine but a missed `release` deadlocks all future callers.
2. **"Node is single-threaded so I don't need a mutex."** False. Single thread + cooperative await means *interleaving at every await point* — read-modify-write across awaits is a race.
3. **Reentrancy.** Standard mutex is NOT reentrant — calling `runExclusive` while you already hold the lock deadlocks. Reentrant variant tracks owner.
4. **Fairness.** FIFO is the default. LIFO is fine for some workloads but can starve callers.
5. **Cancellation.** If a caller aborts while queued, splice their resolver out; otherwise releases hand the lock to a ghost.
6. **Timeout.** `acquire(timeoutMs)` returns null if no lock within window; combined with try/finally still releases nothing (you never had it).
7. **Cross-process.** This mutex is in-process only. For cross-process: Redis SETNX with TTL + fencing token (see `10-machine-coding-patterns/leader-election-toy.md`).

## Mental Model

**One key, FIFO line of people who want it.**

```
   t=0   A: mutex.acquire → _locked=false → take key → _locked=true → return release_A
   t=0   B: mutex.acquire → _locked=true → queue.push(res_B) → await
   t=0   C: mutex.acquire → _locked=true → queue.push(res_C) → await
   t=50  A: release_A() → _queue.shift() → res_B() → _locked stays true → B owns it
   t=50  B's `await new Promise` resolves → B has the key, runs work
   t=80  B: release_B() → shift → res_C() → C owns
   t=100 C: release_C() → queue empty → _locked=false
```

The lock state machine: free → owned → owned → ... → free.

## Why interviewers care

- **Async race awareness.** Confirms candidate understands that `await` is an interleaving point.
- **Lifecycle hygiene.** try/finally to release.
- **Distinction from synchronization in worker threads** — mutex here is for *async tasks within one thread*, not multi-threaded locks.

## Common beginner confusion

- **"Single-threaded JS doesn't need locks."** Wrong for any code with `await` between read and write. Two parallel handlers both `read counter`, await, `write counter+1` → lost update.
- **"I'll just use a boolean flag."** Without a queue, late callers spin or never get woken.
- **"Use Promise.race to serialize."** Race fires on first resolve; not serialization.
- **"Mutex blocks the event loop."** No — it just makes other callers wait their turn via a promise; the event loop continues to process other work.
- **"Acquire returns the lock."** It returns the *release function*. Holding the lock is implicit in being past the `await`.

## Brute force approach

```js
// Lost update race:
async function increment() {
  const v = await db.get('counter');
  await db.set('counter', v + 1);
}
// 10 parallel increment() with counter=0 → final value might be 1 or 10
```

## Optimal approach

A mutex with `runExclusive(fn)` that wraps acquire + work + release in try/finally. Callers can't forget to release.

## Solution (JavaScript)

```js
class Mutex {
  constructor() { this._queue = []; this._locked = false; }
  acquire() {
    if (!this._locked) {
      this._locked = true;
      return Promise.resolve(() => this._release());
    }
    return new Promise(res => this._queue.push(() => {
      // when shifted, return the release fn to the waiter
      res(() => this._release());
    }));
  }
  _release() {
    const next = this._queue.shift();
    if (next) next();          // gives release fn to next waiter; _locked stays true
    else this._locked = false;
  }
  async runExclusive(fn) {
    const release = await this.acquire();
    try { return await fn(); }
    finally { release(); }
  }
}

// Usage
const mutex = new Mutex();
async function safeIncrement() {
  return mutex.runExclusive(async () => {
    const v = await db.get('counter');
    await db.set('counter', v + 1);
  });
}
await Promise.all(Array(10).fill(0).map(safeIncrement));   // final: 10, no lost updates
```

## Step-by-step dry run

3 parallel `runExclusive(work)` where `work` takes 50ms each:

```
t=0   A: acquire → _locked false → take → _locked=true → return release_A → run work
t=0   B: acquire → _locked true → queue [resB] → await
t=0   C: acquire → _locked true → queue [resB, resC] → await
t=50  A.finally: release_A() → shift resB → resB(releaseFn) → _locked=true (stays)
      B's await resolves → B has releaseFn → B runs work
t=100 B.finally: release_B() → shift resC → resC(releaseFn) → _locked=true
      C runs work
t=150 C.finally: release_C() → queue empty → _locked=false
```

A → B → C run in strict FIFO; never overlap.

## How to think aloud in the interview

> "Mutex = Semaphore(1) with a friendlier API. `acquire` returns a release function; `runExclusive(fn)` wraps acquire+task+release in try/finally so callers can't leak. The lock state stays true while handing from caller to caller — only goes false when the queue drains. JS being single-threaded doesn't avoid races; any read-modify-write across an `await` is a race without locking. For cross-process, this won't work — I'd reach for Redis SETNX + TTL + fencing."

## Important takeaways

- **JS still needs locks.** Read-modify-write across `await` is a race.
- **`runExclusive(fn)`** is the safe public API.
- **Lock stays true** during handoffs.
- **Not reentrant** by default — same task holding then calling `runExclusive` again deadlocks.
- **Cross-process** = Redis + fencing, not this.

## Variants

- **Timed `acquire(timeoutMs)`** — return null if not granted in time.
- **AbortSignal-aware** — caller can abort while queued.
- **Reentrant mutex** — track owner; same owner can re-enter; tracks depth.
- **Read-write lock** — many readers OR one writer; useful for read-heavy state.
- **Priority mutex** — high-priority waiters skip the queue.

## Revision notes

```
Mutex:
  acquire(): if !_locked → take; else queue.push(res) await
  _release(): shift queue & resolve next; or _locked=false if empty
  runExclusive(fn): release = await acquire(); try fn() finally release()
  
  JS races happen ACROSS await; mutex is needed
  not reentrant by default
  cross-process: Redis SETNX + fencing
  variants: timed, abort-aware, RW-lock, reentrant, priority
```
