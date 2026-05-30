# Build a Promise from scratch — state machine + `.then` chaining

> **Difficulty:** Medium-Hard   |   **Time:** ~45 min   |   **Prereqs:** [`concepts/promises.md`](../../concepts/promises.md), [`05-event-loop/microtask-macrotask-order.md`](../05-event-loop/microtask-macrotask-order.md)
>
> **Source:** Canonical machine-coding interview (Google, Microsoft, Atlassian, Series-B+ startups). BFE.dev #67, GreatFrontEnd. Reference: <a href="https://promisesaplus.com/" target="_blank" rel="noopener noreferrer">Promises/A+ spec</a> — interview level is looser.

---

## 1. Problem statement

**Signature**
```ts
class MyPromise<T> {
  constructor(executor: (resolve: (v: T) => void, reject: (e: any) => void) => void);
  then<U>(onFulfilled?: (v: T) => U | MyPromise<U>, onRejected?: (e: any) => U | MyPromise<U>): MyPromise<U>;
  catch(onRejected: (e: any) => any): MyPromise<any>;
}
```

**Input / Output examples**

| Code                                                                  | Output                          |
|-----------------------------------------------------------------------|----------------------------------|
| `new MyPromise(r => r(42)).then(v => console.log(v))`                | logs `42` (asynchronously)       |
| `let x=0; new MyPromise(r => r(1)).then(() => x=1); console.log(x);` | `0` (then is always async)       |
| `new MyPromise((_, rej) => rej('x')).then(undefined, e => console.log(e))` | logs `'x'`                  |
| `p.then(v => v+1).then(v => v*2)` (p resolves with 10)              | downstream sees `22`             |
| `p.then(v => new MyPromise(r => r(v*2)))` (p resolves with 10)       | downstream sees `20` (unwrapped) |
| `p.then(v => { throw 'oops'; }).catch(e => console.log(e))`         | logs `'oops'`                    |

**Constraints**
- Three states: `PENDING → FULFILLED` or `PENDING → REJECTED`. **Locked on first settle.**
- `.then` callbacks always run on a **microtask**, never inline.
- `.then` returns a **new** promise; chains the user callback's return value into it.
- If a callback returns another promise (or thenable), the outer promise adopts its state.
- Throwing in a callback rejects the returned promise.

---

## 2. Plain-English restatement

Build the Promise primitive — the same class you've been using since ES2015 — by hand. The interviewer wants you to demonstrate that you understand: (1) it's a state machine that locks on first settle; (2) every `.then` callback is scheduled on a microtask, not run inline; (3) `.then` returns a *new* promise whose state depends on the user callback's outcome; (4) if a callback returns a promise, the outer one waits for it ("unwrapping"). Get all four right and you've internalized async/await — which is just syntactic sugar over this.

---

## 3. Why this matters in interviews

This is the **deepest** promise question — it forces you to articulate state transitions, microtask scheduling, and what `then` actually returns. If you can build a 60-line Promise from scratch, you can debug *any* async bug in your career. Senior backend interviewers ask it specifically because Node services live and die by promise correctness — unhandled rejections crash workers, missing `await`s leak handles, and broken chains silently swallow errors. It's also the gateway to understanding async/await (which is sugar over this exact machinery).

---

## 4. Mental model

A Promise is a **box that ends up in exactly one of two final states** — fulfilled with a value, or rejected with a reason. While pending, it holds a list of subscribers ("call me when you settle"). On settle, it fires every subscriber asynchronously and locks forever.

```
   ┌─────────────────────────────────────────────────────────────┐
   │                       MyPromise                             │
   │                                                              │
   │   state: PENDING ─resolve(v)─▶ FULFILLED  (value=v, locked) │
   │            │                                                 │
   │            └─reject(r)──────▶ REJECTED   (reason=r, locked) │
   │                                                              │
   │   onFulfilledQueue: [cb1, cb2, ...]   ← .then subscribers   │
   │   onRejectedQueue:  [cb1, cb2, ...]                          │
   │                                                              │
   │   On settle: queueMicrotask each subscriber, drain the queue │
   └─────────────────────────────────────────────────────────────┘

   .then(fn) returns a NEW promise. The new promise resolves with
   fn(value), or rejects if fn throws, or adopts the state of fn's
   returned promise (unwrapping).
```

The "always async" rule prevents **Zalgo** — code that sometimes runs synchronously and sometimes doesn't. Always-microtask makes Promise behavior predictable.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `let x = 0; new Promise(r => r(1)).then(() => x = 1); console.log(x);` — does this log `0` or `1`? Why?
> 2. If you call `resolve(42)` and then `resolve(99)` from inside the executor, what value does `.then` see?
> 3. `.then(v => fetch(url))` — what does the next `.then` in the chain see? The Promise from fetch, or the resolved value?

---

## 6. Brute force — walked through

### Wrong attempt 1: store a single callback

```js
class MyPromise {
  constructor(executor) { this.cb = null; executor(v => this.cb?.(v)); }
  then(cb) { this.cb = cb; }
}
```

Fails the moment two `.then` calls register — second clobbers first. Need a queue, not a single slot.

### Wrong attempt 2: call the callback synchronously

```js
class MyPromise {
  constructor(executor) {
    executor((v) => { this.callbacks.forEach(cb => cb(v)); });   // BUG: sync
  }
}
```

Violates the always-async rule. `new MyPromise(r => r(1)).then(() => x = 1); console.log(x);` would log `1` instead of `0`. Real Promises always defer to a microtask.

### Wrong attempt 3: `then` returns `undefined`

```js
then(cb) {
  this.callbacks.push(cb);
  // no return
}
```

Breaks chaining entirely. `.then(...)` must return a **new** Promise that's resolved with the callback's return value (or rejected if it throws).

### Wrong attempt 4: no unwrapping

```js
// Inside then:
resolve(onFulfilled(value));   // BUG: if onFulfilled returns a Promise, downstream sees the Promise itself
```

If `onFulfilled(v)` returns another Promise, the outer chain should *wait* for it and resolve with its eventual value. Missing this breaks every `await fetch()`-style use.

---

## 7. The unlocking insight

> **A Promise is a one-shot state machine with subscriber queues. `then` returns a new promise; the user callback's return value (or thrown error, or returned promise) is wired into that new promise's `resolve`/`reject`. Every callback dispatch is wrapped in `queueMicrotask`.**

Five mechanics make it work:

1. **State + value/reason + two queues.** Five fields are enough: `state`, `value`, `reason`, `onFulfilledQueue`, `onRejectedQueue`.
2. **Settle-and-lock.** `resolve`/`reject` start with `if (state !== PENDING) return` so a second call is a no-op.
3. **Always-async dispatch.** Every callback fires via `queueMicrotask(() => cb(value))` — never inline. This holds even if `resolve` was called synchronously in the executor.
4. **`then` returns a new Promise.** Inside the new Promise's executor, capture references to its `resolve`/`reject`. Wire the user callback's outcome:
   - return → call new promise's `resolve`
   - throw → call new promise's `reject`
   - returned promise → adopt its state via `.then(resolve, reject)`
5. **Unwrap on resolve.** If `resolve(value)` is given a thenable, recurse: `value.then(resolve, reject)`. That's how a `.then(v => fetch())` chain works — fetch's promise gets unwrapped automatically.

Two state-transition rules to memorize:

```
   PENDING + resolve(v)  →  FULFILLED with value=v; drain onFulfilledQueue as microtasks
   PENDING + reject(r)   →  REJECTED with reason=r; drain onRejectedQueue as microtasks
   FULFILLED/REJECTED + resolve/reject  →  no-op (locked)
```

---

## 8. Solution (annotated)

```js
const PENDING = 'pending';
const FULFILLED = 'fulfilled';
const REJECTED = 'rejected';

class MyPromise {
  constructor(executor) {
    this.state = PENDING;                                  // step 1: five fields total
    this.value = undefined;
    this.reason = undefined;
    this.onFulfilledQueue = [];
    this.onRejectedQueue = [];

    const resolve = (value) => {                            // step 2: settle as fulfilled
      if (this.state !== PENDING) return;                    //         lock on first settle
      if (value && typeof value.then === 'function') {       //         unwrap thenables
        return value.then(resolve, reject);
      }
      this.state = FULFILLED;
      this.value = value;
      this.onFulfilledQueue.forEach((cb) =>                   //         drain queue as microtasks
        queueMicrotask(() => cb(value))
      );
      this.onFulfilledQueue = [];
    };

    const reject = (reason) => {                             // step 3: settle as rejected
      if (this.state !== PENDING) return;
      this.state = REJECTED;
      this.reason = reason;
      this.onRejectedQueue.forEach((cb) =>
        queueMicrotask(() => cb(reason))
      );
      this.onRejectedQueue = [];
    };

    try {
      executor(resolve, reject);                              // step 4: run executor; catch sync throws
    } catch (err) {
      reject(err);
    }
  }

  then(onFulfilled, onRejected) {                            // step 5: returns NEW promise
    const fulfilledFn =
      typeof onFulfilled === 'function' ? onFulfilled : (v) => v;          // default: pass-through
    const rejectedFn =
      typeof onRejected === 'function' ? onRejected : (e) => { throw e; }; // default: re-throw

    return new MyPromise((resolve, reject) => {              // step 6: new promise wires callback's outcome
      const handleFulfilled = (value) => {
        try { resolve(fulfilledFn(value)); }                  //         return → new promise resolves
        catch (err) { reject(err); }                           //         throw  → new promise rejects
      };
      const handleRejected = (reason) => {
        try { resolve(rejectedFn(reason)); }                  //         catch handler can recover
        catch (err) { reject(err); }
      };

      if (this.state === FULFILLED) {
        queueMicrotask(() => handleFulfilled(this.value));    //         already settled — schedule now
      } else if (this.state === REJECTED) {
        queueMicrotask(() => handleRejected(this.reason));
      } else {
        this.onFulfilledQueue.push(handleFulfilled);          //         pending — queue for later
        this.onRejectedQueue.push(handleRejected);
      }
    });
  }

  catch(onRejected) { return this.then(undefined, onRejected); }
}
```

**Try it yourself**

```js
const p = new MyPromise((resolve) => setTimeout(() => resolve(10), 50));
p.then((v) => v + 1)
 .then((v) => v * 2)
 .then((v) => console.log('final:', v));   // final: 22

// Always-async test
let x = 0;
new MyPromise((r) => r(1)).then(() => { x = 1; });
console.log(x);                              // 0  (then is async)

// Unwrapping
new MyPromise((r) => r(new MyPromise((r2) => r2(42))))
  .then((v) => console.log(v));              // 42  (unwrapped)

// Throwing recovers via catch
new MyPromise((r) => r(1))
  .then((v) => { throw 'oops'; })
  .catch((e) => console.log(e));             // 'oops'
```

---

## 9. Step-by-step dry run

Input:

```js
const p = new MyPromise((resolve) => setTimeout(() => resolve(10), 50));
p.then((v) => v + 1)
 .then((v) => v * 2)
 .then((v) => console.log('final:', v));
```

Values-first trace:

| Time | Action                       | State        | Microtask queue                | Output         |
|------|------------------------------|--------------|---------------------------------|----------------|
| t=0  | `p` constructed, executor runs | PENDING    | (timer queued)                  | —              |
| t=0  | `p.then(v=>v+1)` returns p2   | both PENDING | (handler pushed onto p's queue) | —              |
| t=0  | `p2.then(v=>v*2)` returns p3  | all PENDING  | (handler pushed onto p2's queue)| —              |
| t=0  | `p3.then(v=>log(v))` returns p4 | all PENDING | (handler pushed onto p3's queue) | —          |
| t=50 | timer fires, `resolve(10)`    | p: FULFILLED | `[handler1(10)]`                | —              |
| µ1   | handler1(10): `resolve(11)` on p2 | p2: FULFILLED | `[handler2(11)]`             | —              |
| µ2   | handler2(11): `resolve(22)` on p3 | p3: FULFILLED | `[handler3(22)]`             | —              |
| µ3   | handler3(22): `console.log('final:', 22)` | p4: FULFILLED | empty                | `final: 22`    |

Three microtasks between resolve at t=50 and the final log. No timers in between.

---

## 10. Common confusion + traps

1. **Calling `then` callback inline in `resolve`.**
   Violates the always-async rule. `new MyPromise(r => r(1)).then(() => x = 1); console.log(x);` must log `0`, not `1`. Always `queueMicrotask`.

2. **Single callback slot instead of queue.**
   Breaks multi-subscriber: `p.then(a); p.then(b);` must fire both. Use arrays.

3. **`then` returning `undefined`.**
   Breaks chaining entirely. Must return a NEW promise.

4. **Forgetting to unwrap returned promises.**
   `then(v => fetch(...))` passes a Promise to the next `then` instead of fetch's resolved value. Recurse in `resolve`: if `value` has a `.then`, call `value.then(resolve, reject)`.

5. **Letting `resolve` fire twice.**
   State must lock on first settle. Without the guard, late callers see weird inconsistencies.

6. **`reject` should NOT unwrap.**
   Only `resolve` adopts the state of a thenable. `reject(somePromise)` should reject with that *promise as the reason*. (Spec detail; mention briefly if asked.)

7. **Forgetting to handle sync throws in the executor.**
   `new MyPromise(() => { throw new Error('oops') })` must reject. Wrap the executor call in try/catch.

8. **Default handlers wrong.**
   `then()` with no args must propagate the value or error to the next `.then`/`.catch`. Default `onFulfilled = v => v` and `onRejected = e => { throw e; }`.

---

## 11. Senior follow-ups & variants

### Variant 1 — `Promise.resolve` / `Promise.reject` static methods

```js
MyPromise.resolve = (v) => new MyPromise((res) => res(v));
MyPromise.reject  = (e) => new MyPromise((_, rej) => rej(e));
```

`Promise.resolve(thenable)` should adopt the thenable's state (unwrap). Already handled by `resolve`'s unwrapping logic.

### Variant 2 — Promises/A+ compliance

Spec is 5 pages of edge cases:
- Thenable resolution must call `then` only once (defensive).
- Resolving with the *same* promise must throw `TypeError` (cycle detection).
- The `then` of a thenable must be called with the thenable as `this`.
- Reentrant `resolve`/`reject` (when thenable's `then` calls them) needs guarded flags.

Most interviewers stop at "unwrap thenables." Mention you know A+ exists for the full spec.

### Variant 3 — Implement `Promise.all` on top of MyPromise

```js
MyPromise.all = (promises) => new MyPromise((resolve, reject) => {
  const results = new Array(promises.length);
  let pending = promises.length;
  if (pending === 0) return resolve([]);
  promises.forEach((p, i) => {
    MyPromise.resolve(p).then((v) => {
      results[i] = v;
      if (--pending === 0) resolve(results);
    }, reject);
  });
});
```

If your MyPromise is correct, this works in 10 lines. Common follow-up. See [promise-all-polyfill.md](./promise-all-polyfill.md) for the full breakdown.

### Variant 4 — `.finally(cb)`

```js
finally(cb) {
  return this.then(
    (v) => MyPromise.resolve(cb()).then(() => v),
    (e) => MyPromise.resolve(cb()).then(() => { throw e; })
  );
}
```

Run cleanup regardless of outcome; preserve the original settle. See [promise-finally-polyfill.md](./promise-finally-polyfill.md).

### Variant 5 — async/await desugaring

```js
async function fetchAndDouble(url) {
  const data = await fetch(url);
  return data * 2;
}
// Desugars to:
function fetchAndDouble(url) {
  return MyPromise.resolve(fetch(url)).then((data) => data * 2);
}
```

`await x` is `then(resolved => /* rest of function */)`. `async function f(){ ... }` returns a Promise. The whole feature is sugar over the state machine you just built.

### Variant 6 — `Promise.race` and `Promise.any`

```js
MyPromise.race = (ps) => new MyPromise((res, rej) => ps.forEach((p) => MyPromise.resolve(p).then(res, rej)));
MyPromise.any  = (ps) => new MyPromise((res, rej) => {
  const errs = new Array(ps.length);
  let pending = ps.length;
  if (pending === 0) return rej(new AggregateError([], 'No promises'));
  ps.forEach((p, i) => MyPromise.resolve(p).then(res, (e) => {
    errs[i] = e;
    if (--pending === 0) rej(new AggregateError(errs, 'All promises rejected'));
  }));
});
```

Confirms the state-machine handles "first settle wins" correctly. See [promise-race-polyfill.md](./promise-race-polyfill.md), [promise-any-polyfill.md](./promise-any-polyfill.md).

---

## 12. How to think aloud in the interview

> "Promise is a state machine: PENDING → FULFILLED or PENDING → REJECTED, locked on first settle. Five fields: `state`, `value`, `reason`, and two callback queues. Resolve/reject guard with `if (state !== PENDING) return`. Every callback dispatch goes through `queueMicrotask` so we never run sync — that's the always-async rule. `then(onF, onR)` returns a NEW promise. Inside the new promise's executor, wire the user callback's outcome: return → resolve, throw → reject, returned promise → unwrap via `.then(resolve, reject)`. Resolve also unwraps if given a thenable. With this, async/await is free — it desugars to `.then` chains. Promises/A+ adds defensive edge cases (cycle detection, thenable-call-once) but the core is 60 lines."

---

## 13. 60-second revision

> - **State machine:** PENDING → FULFILLED or PENDING → REJECTED. **Locked on first settle.**
> - **Five fields:** `state`, `value`, `reason`, `onFulfilledQueue`, `onRejectedQueue`.
> - **Always-async dispatch:** wrap every callback in `queueMicrotask` — never inline.
> - **`then` returns a NEW promise.** User callback's return → new promise's resolve; throw → reject; returned promise → unwrap.
> - **`resolve` unwraps thenables.** `reject` does NOT.
> - **`catch(fn)` = `then(undefined, fn)`.**
> - **Default handlers:** `onFulfilled = v => v` (pass-through), `onRejected = e => { throw e }` (re-throw).
> - **async/await is sugar** over `.then` chains.
> - **Trap:** single callback slot; sync dispatch; missing unwrap; double-settle without guard.

---

**Related:** [promise-all-polyfill.md](./promise-all-polyfill.md) · [promise-race-polyfill.md](./promise-race-polyfill.md) · [promise-allsettled-polyfill.md](./promise-allsettled-polyfill.md) · [promise-finally-polyfill.md](./promise-finally-polyfill.md) · [deferred-with-resolvers.md](./deferred-with-resolvers.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md), [`05-event-loop/microtask-macrotask-order.md`](../05-event-loop/microtask-macrotask-order.md)
