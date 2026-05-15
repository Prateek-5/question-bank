# Implement `Promise.prototype.finally` polyfill

## Source
- Common polyfill question — `.finally` shipped in ES2018 but the polyfill is a classic interview probe.
- BFE.dev #74 "implement Promise.prototype.finally"; GreatFrontEnd JS polyfill set.
- MDN: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/finally

## Why this question matters in interviews
`finally` looks deceptively simple ("just run a callback") but has three sharp edges: (1) it must be a **pass-through** — value and error flow through unchanged, (2) if the cleanup itself throws or returns a rejecting promise, that **overrides** the chain, and (3) if cleanup returns a pending promise, the chain must **wait** for it. Interviewers love this because the obvious one-line `.then(cb, cb)` implementation is WRONG — it consumes the value and would need the cleanup to re-throw. Showing the right answer demonstrates understanding of value vs side-effect callbacks.

## Concepts involved

### Syntax to lock in
```js
fetchData()
  .then(data => process(data))
  .catch(err => log(err))
  .finally(() => closeConnection());
// closeConnection runs regardless. Value/error passes through.
```

### Runtime / engine behavior
- `finally(cb)` returns a **new** Promise.
- The new promise is fulfilled/rejected with the **same** value/reason as the original — UNLESS the cleanup callback throws or returns a rejected promise.
- The callback receives **no arguments** — you don't know if you're in the success or error path.
- If `cb()` returns a Promise, the chain waits for it before propagating. (This is the surprising bit.)

### Edge cases (interview traps)
1. **Pass-through** — `.finally(() => 999)` does NOT change the chained value. Cleanup's return value is discarded.
2. **Cleanup throws** — chain rejects with that throw, hiding the original value/error.
3. **Cleanup returns a rejected promise** — same as throw: chain rejects with the cleanup's reason.
4. **Cleanup returns a pending promise** — chain pauses until it settles; if it fulfills, original value flows through.
5. **Naive `.then(cb, cb)` is wrong** — it would call `cb` with the value/reason as arg, and the return value would replace the chain value.
6. **`Promise.resolve(cb())` wrapper** — used to lift cleanup's return into a promise uniformly, even if `cb` is sync.

## Brute force approach
"Just do `.then(cb, cb)`." Wrong because:
- The callback signature is wrong (`finally` cb takes no args).
- Returning anything from `cb` would replace the chained value.
- Errors in `cb` would be lost in the success path (the error-callback in `.then` only handles upstream errors, not its own throws).

Drop this approach.

## Optimal approach
On fulfillment: run `cb()`, wait for its result via `Promise.resolve(cb())`, then return the **original value**. On rejection: run `cb()`, wait for it, then **re-throw** the original reason. If `cb()` itself rejects or throws, that takes over.

This is "run side-effect, then restore original outcome" — implementable cleanly with `then(onF, onR)` where each handler awaits `cb()` then passes through.

## Solution (JavaScript)

```js
// Implemented as a polyfill on Promise.prototype
if (!Promise.prototype.myFinally) {
  Promise.prototype.myFinally = function (callback) {
    const P = this.constructor || Promise;

    return this.then(
      (value) =>
        P.resolve(callback()).then(() => value),       // pass value through
      (reason) =>
        P.resolve(callback()).then(() => {
          throw reason;                                // pass error through
        }),
    );
  };
}

// Usage
Promise.resolve(42)
  .myFinally(() => console.log('cleanup'))
  .then(v => console.log('value:', v));
// Logs: cleanup
// Logs: value: 42
```

Notes on the code:
- `P.resolve(callback())` handles both sync (`callback` returns a value) and async (`callback` returns a promise) — both become a promise we can `.then` on.
- The success branch returns `value` after cleanup; the error branch re-throws `reason` after cleanup.
- If `callback()` throws synchronously, `P.resolve(...)` itself doesn't catch it — but the surrounding `then` callback's exception handling will reject the returned promise with the cleanup's error. Same applies if it returns a rejecting promise.

## Step-by-step dry run

**Case 1 — happy path:**
```js
Promise.resolve('data')
  .myFinally(() => console.log('cleanup ran'))
  .then(v => console.log('final:', v));
```
- `myFinally` returns a new promise built from `this.then(onF, onR)`.
- Upstream fulfills with `'data'`. `onF('data')` runs: `P.resolve(callback())` — callback logs `'cleanup ran'`, returns undefined. `P.resolve(undefined).then(() => 'data')` resolves with `'data'`.
- Final `.then` logs `final: data`.

Output:
```
cleanup ran
final: data
```

**Case 2 — cleanup throws:**
```js
Promise.resolve('data')
  .myFinally(() => { throw new Error('cleanup failed'); })
  .catch(e => console.log('caught:', e.message));
```
- `onF('data')` runs: `P.resolve(callback())` — callback throws synchronously. The throw propagates out of the `then` success handler → returned promise rejects with `Error('cleanup failed')`.
- Final `.catch` logs `caught: cleanup failed`. **Original value `'data'` is lost — cleanup's error wins.**

**Case 3 — async cleanup:**
```js
Promise.resolve('data')
  .myFinally(() => new Promise(r => setTimeout(r, 100)))
  .then(v => console.log('value at', Date.now() % 1000, ':', v));
```
- `P.resolve(callback())` is a pending promise that settles at t=100.
- `.then(() => 'data')` waits, then resolves with `'data'`.
- Final `.then` runs ~100ms after start. Chain correctly **waits**.

**Case 4 — upstream rejects, cleanup runs, error still propagates:**
```js
Promise.reject(new Error('upstream')).myFinally(() => console.log('cleanup')).catch(e => console.log('caught:', e.message));
```
- `onR` runs: logs cleanup, then `.then(() => { throw reason; })` re-throws the upstream error.
- Output: `cleanup`, then `caught: upstream`.

## Important takeaways

**Syntax to memorize**
- `Promise.resolve(callback())` — uniform lifting of sync/async cleanup into a promise.
- `.then(() => value)` after the cleanup — pass-through.
- `.then(() => { throw reason; })` after the cleanup on error path — re-throw to preserve rejection.

**Patterns to reuse**
- "Run side-effect, then forward outcome" is the same shape as **try/finally** in synchronous code, **defer** in Go, and **using/dispose** in C#. `.finally` is the JS equivalent.
- The "wrap-with-`Promise.resolve` for uniform sync/async handling" trick shows up everywhere — `promisify`, middleware runners, async pipelines.

**Common mistakes**
- `.then(cb, cb)` instead of two distinct branches — loses pass-through semantics.
- Returning `callback()`'s result instead of the original value — breaks the contract.
- Forgetting that cleanup's throw/rejection wins — leads to "where did my error go" confusion in production.
- Not awaiting an async cleanup — chain races ahead before cleanup completes.

**Related questions**
- `Promise.all` / `Promise.any` polyfills
- Implementing async middleware (Koa-style) — uses the same "lift to promise" trick
- try/finally in async functions — `.finally` is just the chained form

## Variants

1. **Async-aware `finally` with timeout** — if cleanup takes too long, give up. Wrap cleanup in `Promise.race([cleanup, timeout])`.
2. **`finallyOnce`** — guarantee cleanup runs exactly once even if you `.finally` the same promise multiple times. Trick question — each `.finally` call is independent.
3. **`tap`** — like `finally` but only on the success path. Useful for logging without affecting the chain. Easy follow-up.

## Revision notes

> **Promise.prototype.finally — 60 second recap**
> - **Pass-through**: value/error flow through unchanged.
> - Cleanup callback takes **no args** and its return value is **discarded** (unless it throws/rejects).
> - If cleanup throws or returns a rejecting promise → chain rejects with cleanup's reason (overrides upstream).
> - If cleanup returns a pending promise → chain **waits** for it.
> - Implementation: `.then(v => P.resolve(cb()).then(() => v), e => P.resolve(cb()).then(() => { throw e; }))`.
> - **Trap:** the naive `.then(cb, cb)` is WRONG — it consumes the value.
