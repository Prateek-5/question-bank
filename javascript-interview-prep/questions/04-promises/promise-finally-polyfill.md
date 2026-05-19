# Implement `Promise.prototype.finally(cb)` polyfill — pass-through cleanup

> **Difficulty:** Easy-Medium   |   **Time:** ~15 min   |   **Prereqs:** [build-promise-from-scratch.md](./build-promise-from-scratch.md), [promise-all-polyfill.md](./promise-all-polyfill.md)
>
> **Source:** ES2018. BFE.dev #74. MDN: [Promise.prototype.finally](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/finally).

---

## 1. Problem statement

**Signature**
```ts
function myFinally<T>(this: Promise<T>, callback: () => void | Promise<void>): Promise<T>;
```

**Input / Output examples**

| Code                                                                          | Behaviour                                                  |
|-------------------------------------------------------------------------------|-------------------------------------------------------------|
| `Promise.resolve('data').myFinally(() => log('cleanup')).then(v => log(v))`  | logs `cleanup`, then `data` — value passes through         |
| `Promise.reject('err').myFinally(() => log('cleanup')).catch(e => log(e))`   | logs `cleanup`, then `err` — error passes through          |
| `.myFinally(() => 999)`                                                       | cleanup's `999` is **discarded**                          |
| `.myFinally(() => { throw 'cleanup failed'; })` after success                | rejects with `'cleanup failed'` — cleanup error overrides |
| `.myFinally(() => sleep(100))`                                                | downstream `.then` runs ~100ms later — chain **waits** for async cleanup |

**Constraints**
- **Pass-through.** Original value/reason flows downstream unchanged.
- Cleanup callback takes **no arguments** and its return value is **discarded**.
- If cleanup throws or returns a rejected promise → chain rejects with cleanup's reason (overrides original).
- If cleanup returns a pending promise → chain **waits** for it.

---

## 2. Plain-English restatement

`finally(cb)` runs `cb` regardless of whether the upstream promise resolved or rejected. The cleanup callback doesn't change the chain's value — it's a side-effect hook. If the cleanup itself fails, *that* failure takes over the chain. If the cleanup is async, the chain waits for it.

Used for: closing DB connections, releasing locks, removing event listeners, hiding loading spinners — any "run regardless of outcome" cleanup.

---

## 3. Why this matters in interviews

`finally` looks deceptively simple ("just run a callback") but has three sharp edges: (1) it must be a **pass-through** — value and error flow through unchanged, (2) if the cleanup itself throws or returns a rejecting promise, that **overrides** the chain, and (3) if cleanup returns a pending promise, the chain must **wait** for it. Interviewers love this because the obvious one-line `.then(cb, cb)` implementation is **wrong** — it would consume the value. Showing the right answer demonstrates understanding of value vs side-effect callbacks.

---

## 4. Mental model

`finally` is the **try/finally** of async. The cleanup runs regardless of the upstream outcome, but it can't read the value (no args) and its return is discarded — *unless* it throws or rejects, in which case it takes over.

```
                      ┌────────────┐
   upstream  ─────▶  │ finally(cb)│ ─────▶  downstream
                      └────────────┘
                            │
   On fulfillment:      cb() runs (await if returns promise)
                        if cb throws/rejects → downstream gets THAT
                        else → downstream gets ORIGINAL VALUE
   
   On rejection:        cb() runs (await if returns promise)
                        if cb throws/rejects → downstream gets THAT
                        else → downstream RE-THROWS original reason
```

**Implementation core:** `then(onF, onR)` where each handler is `await cb(); pass through`.

```js
return this.then(
  (value) => Promise.resolve(callback()).then(() => value),
  (reason) => Promise.resolve(callback()).then(() => { throw reason; })
);
```

The `Promise.resolve(callback())` wrap lifts both sync and async cleanup into a promise uniformly. The chained `.then(() => value)` / `.then(() => { throw reason; })` ignores the cleanup's return (just waits for it) and propagates the original outcome.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `Promise.resolve(42).finally(() => 999).then(v => log(v))` — does it log `42` or `999`?
> 2. `Promise.resolve(42).finally(() => sleep(100)).then(v => log(v))` — when does the log happen?
> 3. `Promise.resolve(42).finally(() => { throw 'oops' }).catch(e => log(e))` — does it log `42` or `'oops'`?

---

## 6. Brute force — walked through

### Wrong attempt 1: `.then(cb, cb)`

```js
Promise.prototype.myFinally = function (cb) {
  return this.then(cb, cb);   // BUG: consumes value/error
};
```

Three things wrong:
- Callback gets the value or reason as an argument — `cb` is meant to be no-args.
- `cb`'s return value **replaces** the chain's value. `finally(() => 999)` would make downstream see `999`, not the original.
- Errors in `cb` on the success path are lost — `then`'s rejection handler only catches *upstream* errors, not throws in the fulfillment handler (well, it bubbles to the *next* `.catch`, but here we want it to *override* the chain).

### Wrong attempt 2: forget to await async cleanup

```js
Promise.prototype.myFinally = function (cb) {
  return this.then(
    (value) => { cb(); return value; },                    // BUG: doesn't await cb if async
    (reason) => { cb(); throw reason; }
  );
};
```

If `cb` returns a Promise, downstream runs **before** cleanup finishes. Breaks the "chain waits for async cleanup" rule.

### Wrong attempt 3: forget to pass through error

```js
Promise.prototype.myFinally = function (cb) {
  return this.then(
    (value) => Promise.resolve(cb()).then(() => value),
    (reason) => Promise.resolve(cb()).then(() => reason)   // BUG: returns reason as VALUE
  );
};
```

On rejection, the chain should re-throw the original reason. Returning it as a value silently converts the rejection into a fulfillment. Use `.then(() => { throw reason; })`.

---

## 7. The unlocking insight

> **`finally` is "run a side effect, then forward the original outcome." Implement as `then(onF, onR)` where each handler awaits the cleanup via `Promise.resolve(cb())`, then passes through the original value (or re-throws the reason).**

Four invariants:

1. **Pass-through.** `finally(() => 999)` does not change the chained value. The cleanup's return is discarded.
2. **Cleanup can override.** If cleanup throws or returns a rejecting promise, that takes over the chain. The original value/reason is lost.
3. **Async cleanup is awaited.** If `cb()` returns a pending promise, downstream must wait for it.
4. **No arguments.** `cb` takes no args — you can't tell if you're in the success or error path.

The `Promise.resolve(cb())` wrap is the "uniform sync/async lift" — a common pattern. Whether `cb` returned `undefined` (sync), a value (sync), or a Promise (async), `Promise.resolve(cb())` produces a Promise we can `.then` on. The chained `.then(() => value)` ignores the cleanup's value, waits for it, then continues the chain with the original value.

For the error path, we use `.then(() => { throw reason; })` instead of `.catch`. The `throw` inside the success handler converts the new promise into a rejection — preserving the original reason.

---

## 8. Solution (annotated)

```js
if (!Promise.prototype.myFinally) {
  Promise.prototype.myFinally = function (callback) {
    const P = this.constructor || Promise;                   // step 1: support subclassing

    return this.then(
      (value) =>
        P.resolve(callback())                                 // step 2: lift cleanup to Promise (sync or async)
          .then(() => value),                                  // step 3: pass through original value
      (reason) =>
        P.resolve(callback())
          .then(() => { throw reason; })                        // step 4: re-throw original reason
    );
  };
}

// Native usage
Promise.resolve(42).myFinally(() => console.log('cleanup'))
  .then((v) => console.log('value:', v));
// Output: cleanup
//         value: 42
```

**Try it yourself**

```js
const sleep = (ms, v) => new Promise((r) => setTimeout(() => r(v), ms));

// Happy path
Promise.resolve('data')
  .myFinally(() => console.log('cleanup ran'))
  .then((v) => console.log('final:', v));
// cleanup ran
// final: data

// Error path
Promise.reject(new Error('upstream'))
  .myFinally(() => console.log('cleanup'))
  .catch((e) => console.log('caught:', e.message));
// cleanup
// caught: upstream

// Cleanup overrides on throw
Promise.resolve('data')
  .myFinally(() => { throw new Error('cleanup failed'); })
  .catch((e) => console.log('caught:', e.message));
// caught: cleanup failed   ← original 'data' is lost

// Async cleanup — chain waits
Promise.resolve('data')
  .myFinally(() => sleep(100))
  .then((v) => console.log('after', v));
// ... waits 100ms ...
// after data

// Real-world: close connection after fetch
async function fetchAndClose(url, conn) {
  return fetch(url)
    .then((r) => r.json())
    .myFinally(() => conn.close());
}
```

---

## 9. Step-by-step dry run

**Case 1: happy path**

```js
Promise.resolve('data')
  .myFinally(() => console.log('cleanup ran'))
  .then((v) => console.log('final:', v));
```

| Step | Action                                                | Output      |
|------|-------------------------------------------------------|--------------|
| 1    | Upstream fulfills with `'data'`                        | —            |
| 2    | `myFinally` returns `this.then(onF, onR)`              | —            |
| 3    | `onF('data')` runs: `P.resolve(callback())` calls cb   | `cleanup ran` |
| 4    | cb returns `undefined`; `P.resolve(undefined)` is fulfilled | — |
| 5    | `.then(() => value)` returns `'data'`                  | —            |
| 6    | Final `.then(v => log(...))` fires                    | `final: data` |

**Case 2: cleanup throws**

```js
Promise.resolve('data').myFinally(() => { throw new Error('cleanup failed'); }).catch(/* ... */);
```

| Step | Action                                                 | Outcome                           |
|------|--------------------------------------------------------|------------------------------------|
| 1    | `onF('data')` runs                                     | —                                  |
| 2    | `P.resolve(callback())` — cb throws synchronously       | The throw bubbles out of the success handler |
| 3    | New promise rejects with `Error('cleanup failed')`     | Original `'data'` is lost          |
| 4    | `.catch` fires                                         | logs `'cleanup failed'`            |

**Case 3: async cleanup**

```js
Promise.resolve('data').myFinally(() => new Promise((r) => setTimeout(r, 100))).then(/* ... */);
```

| Step | Action                                                  | Time        |
|------|---------------------------------------------------------|--------------|
| 1    | `onF('data')` runs; `cb()` returns a pending promise    | t=0          |
| 2    | `P.resolve(pendingPromise)` adopts its state            | t=0          |
| 3    | `.then(() => 'data')` waits for the pending to settle    | t=0..100     |
| 4    | At t=100, cleanup resolves; `.then(() => 'data')` fires | t=100        |
| 5    | Final `.then` runs                                      | t=100+µ      |

Chain correctly waits ~100ms for async cleanup.

---

## 10. Common confusion + traps

1. **Naive `.then(cb, cb)`** — consumes the value/reason. The right shape is two distinct branches with explicit pass-through.

2. **Returning `callback()`'s result.** Breaks pass-through. The cleanup's return is ignored *unless* it's a Promise (in which case we wait for it but still discard the resolved value).

3. **Forgetting cleanup's throw wins.** When cleanup throws or returns a rejected promise, the chain rejects with cleanup's reason — overriding the original. Document this in production code.

4. **Not awaiting async cleanup.** Downstream runs before cleanup completes. Breaks the "chain waits" rule. Always wrap with `Promise.resolve(cb())`.

5. **Where the throw goes.** On the error path, you must `throw reason` (not `return reason`) to keep the chain rejected. Returning the reason converts the rejection into a fulfillment.

6. **`P = this.constructor || Promise`** is for subclass support. `class MyPromise extends Promise {}` should produce a `MyPromise` from `.myFinally`, not a plain `Promise`. Use `this.constructor` to honor the subclass.

7. **Cleanup runs once per `.finally` call.** If you chain `.finally(cb)` twice, `cb` runs twice. Each `.finally` is its own subscription.

---

## 11. Senior follow-ups & variants

### Variant 1 — Cleanup with timeout

If cleanup hangs, give up:

```js
Promise.prototype.myFinallyWithTimeout = function (callback, ms) {
  return this.myFinally(() => Promise.race([
    Promise.resolve(callback()),
    new Promise((_, rej) => setTimeout(() => rej(new Error('cleanup timeout')), ms)),
  ]));
};
```

### Variant 2 — `tap` (success-only side effect)

Like `finally` but only on the success path. Useful for logging:

```js
Promise.prototype.tap = function (callback) {
  return this.then((value) => Promise.resolve(callback(value)).then(() => value));
};

fetchUser(id).tap((user) => log('fetched', user.id)).then(/* ... */);
```

### Variant 3 — `tapError` (failure-only side effect)

```js
Promise.prototype.tapError = function (callback) {
  return this.then(
    (value) => value,
    (reason) => Promise.resolve(callback(reason)).then(() => { throw reason; })
  );
};

fetchUser(id).tapError((err) => metrics.increment('fetch-fail')).then(/* ... */);
```

### Variant 4 — Multi-`finally` cleanup chain

`.finally(closeDb).finally(closeCache).finally(unlock)` — each runs in order, on success and failure paths. Mimics nested try/finally blocks.

### Variant 5 — Native equivalent: `using` declaration (ES2023+)

Modern alternative: `using` and `await using` (TC39 Stage 3 / ES2026 candidate) for explicit resource management. Eventually replaces some `.finally` patterns with declarative `using conn = openConnection();` and auto-cleanup at scope exit.

---

## 12. How to think aloud in the interview

> "Pass-through cleanup. `myFinally(cb)` returns `this.then(onF, onR)` where each handler runs `P.resolve(cb())` (uniform sync/async lift), then chains `.then(() => value)` on the success path to preserve the original value, and `.then(() => { throw reason })` on the error path to re-throw. The `Promise.resolve` wrap means we wait for async cleanup. The naive `.then(cb, cb)` is wrong — it consumes the value. Cleanup's return is discarded *unless* it throws or rejects, in which case it overrides the chain. `this.constructor || Promise` supports subclassing. Real use: close connections, release locks, hide spinners — anything regardless of outcome."

---

## 13. 60-second revision

> - **Pass-through:** value/error flow through unchanged.
> - **Cleanup callback** takes **no args**; return is **discarded** unless it throws/rejects.
> - **Cleanup throws/rejects → overrides** chain; original is lost.
> - **Cleanup returns pending promise → chain waits** for it.
> - **Implementation:** `.then(v => P.resolve(cb()).then(() => v), e => P.resolve(cb()).then(() => { throw e; }))`.
> - **Use `P = this.constructor || Promise`** for subclass support.
> - **Variants:** `tap` (success only), `tapError` (error only).
> - **Family:** try/finally in sync code, `defer` in Go, `using/dispose` in C#.
> - **Trap:** naive `.then(cb, cb)` consumes the value; forgetting to wait for async cleanup; returning reason instead of throwing.

---

**Related:** [build-promise-from-scratch.md](./build-promise-from-scratch.md) · [promise-all-polyfill.md](./promise-all-polyfill.md) · [promise-race-polyfill.md](./promise-race-polyfill.md) · [deferred-with-resolvers.md](./deferred-with-resolvers.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
