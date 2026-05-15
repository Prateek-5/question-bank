# Implement `Promise.race` polyfill

## Source
- Canonical interview problem (BFE.dev, Frontend Masters, codedamn).
- MDN: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/race

## Why this question matters in interviews
`Promise.race` is the second-most-likely promise polyfill after `Promise.all`. It's six lines, but those six lines test whether you know that (a) the outer promise's `resolve`/`reject` can be invoked from any of the inner promises' settlement handlers, (b) the **promise state machine** silently absorbs later settlements (so "first wins" needs no explicit guard), and (c) **both fulfillment AND rejection** propagate — race is not the same as "first fulfilled" (that's `Promise.any`). The single most common bug: candidates skip the rejection handler thinking `reject` is implicit. It is not — you must hook it. The empty-array case is a beautiful trap: native `Promise.race([])` **stays pending forever** because there is no way for it to settle.

## Concepts involved

### Syntax to lock in
```js
function promiseRace(promises) {
  return new Promise((resolve, reject) => {
    for (const p of promises) {
      Promise.resolve(p).then(resolve, reject);
    }
  });
}
```

### Runtime / engine behavior
- The outer Promise constructor's `resolve`/`reject` are closed over. Multiple `.then` callbacks may call them, but the state machine ensures **only the first call wins**; all subsequent calls are silent no-ops.
- `Promise.resolve(p)` coerces non-promise values and thenables to real promises. If `p` is already settled (like the literal `5`), its handler runs in the **next microtask** — so race never settles synchronously, even with all-fulfilled-already inputs.
- `.then(resolve, reject)` is the **two-arg form** — `resolve` is called on fulfillment, `reject` on rejection. Identical to `.then(resolve).catch(reject)` semantics-wise, but cheaper (one fewer microtask).

### Edge cases (interview traps)
1. **Empty array** — native `Promise.race([])` is **pending forever**. The polyfill above mirrors this (loop doesn't execute, no `resolve` is called, outer stays pending). **State this explicitly**; many candidates think it should resolve to `undefined`.
2. **First settle wins — even rejection** — if the first to settle is a rejection, `Promise.race` rejects with that reason. This is the key distinction from `Promise.any`.
3. **Non-promise values** — `Promise.race([5, slowP])` resolves with `5` on the next microtask (because `Promise.resolve(5)` is already fulfilled and fires its `.then` first).
4. **All inputs already fulfilled** — race resolves with the **first one in iteration order** (because their `.then` callbacks enqueue microtasks in iteration order and microtasks run FIFO).
5. **Synchronous throw in a thenable** — `Promise.resolve(thenable).then` handles it; outer rejects.
6. **Losers keep running** — same as `Promise.all`; race does not cancel siblings. If they're HTTP requests, they complete and are ignored.
7. **Memory** — every input promise has a `.then` callback attached. If you race a "fast" promise against a "never settles" promise, the never-settles promise retains its `.then` reactions forever (small leak in long-lived processes).

## Brute force approach
Track a `settled` flag manually:
```js
let settled = false;
for (const p of promises) {
  Promise.resolve(p).then(
    (v) => { if (!settled) { settled = true; resolve(v); } },
    (e) => { if (!settled) { settled = true; reject(e); } }
  );
}
```
Works, but the `settled` guard is **redundant** — the promise state machine already enforces single-settle. Submit the clean version and mention "we don't need a guard because the outer promise can only settle once." That awareness scores points.

## Optimal approach
Loop the inputs, hand each one `.then(resolve, reject)` against the outer's resolvers. Promise state machine handles the "first wins" semantics for free.

## Solution (JavaScript)

```js
/**
 * Polyfill of Promise.race.
 * Settles (resolve OR reject) as soon as ANY input promise settles.
 * - Empty array → stays pending forever (mirrors native).
 * - Non-promise inputs are coerced via Promise.resolve.
 *
 * @template T
 * @param {Iterable<T | PromiseLike<T>>} promises
 * @returns {Promise<T>}
 */
function promiseRace(promises) {
  return new Promise((resolve, reject) => {
    // Iterable support (mirror native). If you only need array, replace with `for (let i=0;...)`.
    if (promises == null || typeof promises[Symbol.iterator] !== 'function') {
      return reject(new TypeError('promiseRace expects an iterable'));
    }
    for (const p of promises) {
      Promise.resolve(p).then(resolve, reject);
    }
    // Note: empty iterable → no .then callbacks registered → outer stays pending forever.
    // This matches native Promise.race([]).
  });
}
```

### Variant with explicit cancellation of losers (production)

```js
function promiseRaceCancelable(promises) {
  const controllers = promises.map(() => new AbortController());
  const wrapped = promises.map((p, i) => Promise.resolve(p));
  return new Promise((resolve, reject) => {
    wrapped.forEach((p, i) => {
      p.then(
        (v) => { resolve(v); controllers.forEach((c, j) => j !== i && c.abort()); },
        (e) => { reject(e); controllers.forEach((c, j) => j !== i && c.abort()); }
      );
    });
  });
}
// Only useful if your input promise factories actually honour the signal.
```

## Step-by-step dry run

Input:
```js
const sleep = (ms, v) => new Promise((r) => setTimeout(() => r(v), ms));
promiseRace([sleep(100, 'slow'), sleep(20, 'fast'), sleep(50, 'mid')]).then(console.log);
```

Trace:
- `t=0`: outer Promise constructed (`pending`). Loop:
  - `i=0`: `sleep(100,'slow')` returned a pending promise; `.then(resolve, reject)` attaches handlers.
  - `i=1`: `sleep(20,'fast')` pending; handlers attached.
  - `i=2`: `sleep(50,'mid')` pending; handlers attached.
- `t=20`: timer fires → `sleep(20,'fast')` fulfills with `'fast'`. Microtask: its fulfillment handler is `resolve` (outer's resolver). Outer transitions `pending → fulfilled('fast')`.
- `t=50`: `sleep(50,'mid')` fulfills. Microtask: `resolve('mid')` is invoked — but the outer is already settled, **no-op**.
- `t=100`: `sleep(100,'slow')` fulfills. Microtask: `resolve('slow')` — no-op.
- `.then(console.log)` microtask runs (was queued at t=20 right after outer fulfilled) → prints `fast`.

Rejection-first trace:
```js
promiseRace([sleep(100, 'a'), Promise.reject(new Error('boom'))]).then(
  console.log,
  (e) => console.log('err:', e.message)
);
```
- Loop: `Promise.resolve(rejectedP).then(resolve, reject)` — registers `reject` as the rejection handler. The rejected promise's rejection handler is scheduled as a microtask immediately.
- Microtask drain: `reject(Error('boom'))` → outer rejects.
- `.then`'s rejection handler microtask: prints `err: boom`.
- `t=100`: 'a' fulfills, `resolve('a')` called — no-op.

Empty trace:
```js
promiseRace([]).then(() => console.log('done'), () => console.log('err'));
// (nothing ever logged — outer stays pending forever)
```

## Important takeaways

**Syntax to memorize**
- `.then(resolve, reject)` two-arg form — race's signature move.
- `Promise.resolve(p)` to coerce values + thenables.
- No `settled` flag needed — promise state machine handles it.

**Patterns to reuse**
- Same skeleton as `timeLimit(promise, ms)` — race `promise` vs `sleep(ms).then(reject)`.
- Pattern of "first-to-settle wins via shared resolver" is also how `AbortSignal` race-aborts work.

**Common mistakes**
- Omitting the rejection handler (`.then(resolve)` only) — race becomes `Promise.any`-like, ignoring rejections. **Wrong.**
- Returning `undefined` for empty array — native stays pending. State the mirror behaviour.
- Adding a `settled` guard — works but redundant. Show you trust the state machine.
- Conflating `Promise.race` with `Promise.any`. `any` rejects only if all reject, with `AggregateError`. `race` settles on the first of either.

**Related questions**
- `Promise.any` polyfill — flip the logic: count rejections, resolve on first fulfillment.
- `timeLimit(p, ms)` — production use of race.
- `firstSuccessful(promises)` — like `any` but with `.find`-style semantics.

## Variants

1. **`Promise.any` polyfill** — resolves on first **fulfillment**. Rejects with `AggregateError` only if **all** reject. Use a remaining counter, mirror image of `Promise.all`.

2. **`firstResolved(promises, timeoutMs)`** — race + timeout combined: `race([...promises, sleep(t).then(reject)])`.

3. **Cancellable race** — wrap each input promise's underlying work in an `AbortController`; when one wins, `abort()` the others. Only useful if inner work actually honours signals.

4. **Race-with-priority** — given `[(promise, priority)]`, settle with the highest-priority result that arrives within a time window. Used in fallback chains (CDN → origin).

## Revision notes

> **Promise.race polyfill — 60 second recap**
> - Six lines: `new Promise((resolve, reject) => { for (const p of promises) Promise.resolve(p).then(resolve, reject); })`.
> - **First settle wins — resolve OR reject.** Different from `Promise.any` (first fulfillment only).
> - Empty iterable → **pending forever**. Mirrors native.
> - No `settled` flag — promise state machine ensures one transition. Subsequent calls are no-ops.
> - Losers are **not cancelled**; their underlying work runs to completion and is discarded.
> - Use `Promise.resolve(p)` to coerce non-promises + thenables uniformly.
> - Two-arg `.then(onFulfilled, onRejected)` — race's signature move.
> - Family: `all` (all must settle), `allSettled` (never rejects), `any` (first fulfillment), `race` (first either).
> - **Trap:** forgetting the rejection handler. **Trap:** thinking empty array resolves to `undefined`.
