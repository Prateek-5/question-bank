# Implement a Promise from scratch (state machine + then chaining)

## Source
- Canonical machine-coding interview, asked at Google, Microsoft, Atlassian, every major Series-B+ startup.
- LeetCode-style variants on BFE.dev (#67 "implement a simple Promise") and GreatFrontEnd.
- Reference: Promises/A+ spec (https://promisesaplus.com/) — but interview level is much looser.

## Why this question matters in interviews
This is the **deepest** promise question — it forces you to articulate state transitions, microtask scheduling, and what `then` actually returns. If you can build a 60-line Promise from scratch, you can debug *any* async bug in your career. Senior backend interviewers ask it specifically because Node services live and die by promise correctness — unhandled rejections crash workers, missing `await`s leak handles, and broken chains silently swallow errors. It's also the gateway to understanding async/await (which is sugar over this exact machinery).

## Concepts involved

### Syntax to lock in
```js
const p = new MyPromise((resolve, reject) => {
  setTimeout(() => resolve(42), 100);
});
p.then(v => v * 2).then(v => console.log(v)); // 84
```

### Runtime / engine behavior
- A Promise is a **state machine** with three states: `PENDING` → `FULFILLED` or `PENDING` → `REJECTED`. **Once settled, never moves**.
- Settlement is **asynchronous** even if `resolve` is called synchronously — the `.then` callback always runs on a microtask, never inline. This is the rule that prevents Zalgo (releasing control flow unpredictably).
- `then(onFulfilled, onRejected)` returns a **new** Promise. The new promise resolves with whatever the callback returns, or rejects if it throws.
- If a callback returns *another* promise, the outer promise adopts its state (this is "promise unwrapping").

### Edge cases (interview traps)
1. **Synchronous resolve, async then** — if `resolve(42)` is called in the executor synchronously, a later `.then(cb)` must still defer `cb` to a microtask. Schedule via `queueMicrotask` (or `setTimeout(fn,0)` as a coarse fallback).
2. **Multiple `then` on the same promise** — every `.then` registers an independent callback. Need a queue, not a single slot.
3. **`then` called BEFORE settlement vs AFTER** — pending case → push to queue; settled case → schedule callback immediately on microtask.
4. **Throwing in a callback** — `then(v => { throw err; })` must reject the returned promise with `err`.
5. **Returning a promise from then** — must wait for it and adopt its state. Easy to forget.
6. **Calling `resolve` twice** — second call is a no-op (state already locked).
7. **`reject` with a promise** — should *not* unwrap; only `resolve` adopts. (A+ spec detail; mention briefly.)

## Brute force approach
Naive thought: "store the callback, call it when resolve happens." Falls apart the moment you have `p.then(x).then(y)` because the inner `then` returns a new promise that doesn't exist yet, and the value-chaining is wrong. Also breaks if `then` is registered after settlement. Don't ship this — it's a 5-line toy that fails every realistic test.

## Optimal approach
Three pieces: **(1)** a state field with `PENDING/FULFILLED/REJECTED`; **(2)** queues of `onFulfilled` and `onRejected` callbacks for the pending case; **(3)** `then` returns a NEW promise and wires the result of the user callback into that new promise's resolve/reject. Schedule every callback dispatch as a microtask.

## Solution (JavaScript)

```js
const PENDING = 'pending';
const FULFILLED = 'fulfilled';
const REJECTED = 'rejected';

class MyPromise {
  constructor(executor) {
    this.state = PENDING;
    this.value = undefined;
    this.reason = undefined;
    this.onFulfilledQueue = [];
    this.onRejectedQueue = [];

    const resolve = (value) => {
      if (this.state !== PENDING) return;
      // Adopt the state of another promise (basic unwrap)
      if (value && typeof value.then === 'function') {
        return value.then(resolve, reject);
      }
      this.state = FULFILLED;
      this.value = value;
      this.onFulfilledQueue.forEach((cb) => queueMicrotask(() => cb(value)));
      this.onFulfilledQueue = [];
    };

    const reject = (reason) => {
      if (this.state !== PENDING) return;
      this.state = REJECTED;
      this.reason = reason;
      this.onRejectedQueue.forEach((cb) => queueMicrotask(() => cb(reason)));
      this.onRejectedQueue = [];
    };

    try {
      executor(resolve, reject);
    } catch (err) {
      reject(err);
    }
  }

  then(onFulfilled, onRejected) {
    const fulfilledFn =
      typeof onFulfilled === 'function' ? onFulfilled : (v) => v;
    const rejectedFn =
      typeof onRejected === 'function'
        ? onRejected
        : (e) => {
            throw e;
          };

    return new MyPromise((resolve, reject) => {
      const handleFulfilled = (value) => {
        try {
          resolve(fulfilledFn(value));
        } catch (err) {
          reject(err);
        }
      };
      const handleRejected = (reason) => {
        try {
          resolve(rejectedFn(reason)); // recovered → new promise fulfills
        } catch (err) {
          reject(err);
        }
      };

      if (this.state === FULFILLED) {
        queueMicrotask(() => handleFulfilled(this.value));
      } else if (this.state === REJECTED) {
        queueMicrotask(() => handleRejected(this.reason));
      } else {
        this.onFulfilledQueue.push(handleFulfilled);
        this.onRejectedQueue.push(handleRejected);
      }
    });
  }

  catch(onRejected) {
    return this.then(undefined, onRejected);
  }
}
```

## Step-by-step dry run

Input:
```js
const p = new MyPromise((resolve) => {
  setTimeout(() => resolve(10), 50);
});
p.then(v => v + 1)
 .then(v => v * 2)
 .then(v => console.log('final:', v));
```

Trace:
- **t=0** — `p` constructed, state = PENDING. `setTimeout` queued.
- **t=0** — `.then(v=>v+1)` runs. `p` is pending, so push `handleFulfilled1` into `p.onFulfilledQueue`. Returns `p2` (pending).
- **t=0** — `.then(v=>v*2)` runs on `p2`. `p2` pending, push `handleFulfilled2` into `p2.onFulfilledQueue`. Returns `p3`.
- **t=0** — `.then(v=>console.log(...))` runs on `p3`. Push `handleFulfilled3` into `p3.onFulfilledQueue`. Returns `p4`.
- **t=50** — timer fires. `resolve(10)` called on `p`. State → FULFILLED, value=10. Schedules `handleFulfilled1(10)` as microtask.
- **microtask 1** — `handleFulfilled1(10)` runs: `fulfilledFn(10) = 11`. Calls `resolve(11)` on `p2`. p2 → FULFILLED, schedules `handleFulfilled2(11)`.
- **microtask 2** — `handleFulfilled2(11)` runs: `22`. Resolves `p3` with 22, schedules `handleFulfilled3(22)`.
- **microtask 3** — `handleFulfilled3(22)` runs: `console.log('final:', 22)`.

Output: `final: 22`. Three microtasks, one timer.

## Important takeaways

**Syntax to memorize**
- `state`, `value`, `reason`, `onFulfilledQueue`, `onRejectedQueue` — these five fields are all you need.
- `then` returns a **new** MyPromise. The executor of that new promise wires the user callback's result into its `resolve/reject`.
- `queueMicrotask(() => ...)` for every callback dispatch — guarantees async behavior even when `resolve` is sync.

**Patterns to reuse**
- The "state machine with subscriber queues" pattern is identical to: observables (Subject), event emitters, request batchers. State-once-settled is the unique twist.
- Wrapping user callback in `try/catch` and routing the exception to `reject` is the universal "safe callback dispatch" pattern.

**Common mistakes**
- Calling the callback inline in `resolve` — violates the rule that `.then` is always async. Test: `let x = 0; new MyPromise(r => r(1)).then(() => x = 1); console.log(x);` should print `0`, not `1`.
- Storing a single callback instead of a queue — breaks `p.then(a); p.then(b);` (multi-subscriber).
- Forgetting that `then` returns a NEW promise — breaks chaining entirely.
- Not unwrapping when a callback returns a promise — `then(v => fetch(...))` will pass a *promise* to the next `then` instead of the resolved value.
- Letting `resolve` fire twice — state must lock on first settle.

**Related questions**
- `Promise.all` / `Promise.any` / `Promise.race` polyfills
- `Promise.prototype.finally` polyfill
- async/await desugaring (it's a generator + this Promise)

## Variants

1. **Add `Promise.resolve` / `Promise.reject` static methods** — one-liners using the constructor.
2. **Make it Promises/A+ compliant** — handle the thenable resolution procedure rigorously (call `then` only once, handle reentrancy). Spec is 5 pages; most interviewers stop at unwrapping.
3. **Implement `Promise.all` on top of MyPromise** — proves your then-chaining works. Common follow-up.
4. **Add `.finally`** — runs cleanup regardless of state; pass-through value/error (see `promise-finally-polyfill.md`).

## Revision notes

> **MyPromise — 60 second recap**
> - States: PENDING → FULFILLED or PENDING → REJECTED. **Locked on first settle.**
> - Fields: `state`, `value`, `reason`, `onFulfilledQueue`, `onRejectedQueue`.
> - `resolve`/`reject` defined inside constructor (closure over `this`); guard with `if (state !== PENDING) return`.
> - `then(onF, onR)` returns a **new** MyPromise. User callback's return value → `resolve` of new promise. Throw → `reject`.
> - Dispatch every callback via `queueMicrotask` — never inline.
> - Unwrap thenables in `resolve` so returning a promise from `then` works.
> - **Trap:** single callback slot instead of queue; sync dispatch when already settled.
