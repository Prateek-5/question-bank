# Implement `Promise.race(promises)` polyfill — first to settle wins

> **Difficulty:** Easy-Medium   |   **Time:** ~15 min   |   **Prereqs:** [build-promise-from-scratch.md](./build-promise-from-scratch.md), [promise-all-polyfill.md](./promise-all-polyfill.md)
>
> **Source:** Canonical interview problem (BFE.dev, Frontend Masters, codedamn). MDN: [Promise.race](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/race).

---

## 1. Problem statement

**Signature**
```ts
function promiseRace<T>(promises: Iterable<T | PromiseLike<T>>): Promise<T>;
```

**Input / Output examples**

| Setup                                                          | Behaviour                                            |
|----------------------------------------------------------------|-------------------------------------------------------|
| `promiseRace([sleep(100,'slow'), sleep(20,'fast'), sleep(50,'mid')])` | resolves with `'fast'` at `t=20`                    |
| `promiseRace([sleep(100,'a'), Promise.reject('boom')])`         | rejects with `'boom'` (first settle is a reject)    |
| `promiseRace([5, slowP])`                                       | resolves with `5` (`Promise.resolve(5)` is already fulfilled — first microtask wins) |
| `promiseRace([])`                                               | **stays pending forever** (no input → no `resolve` call) |
| Losers keep running                                              | underlying work continues, just ignored             |

**Constraints**
- Settles with the **first to settle** — fulfillment OR rejection (the key distinction from `Promise.any`).
- Non-promise values are coerced via `Promise.resolve`.
- Empty iterable → outer stays pending forever (mirrors native).
- Promise state machine handles "first wins" — no explicit `settled` guard needed.

---

## 2. Plain-English restatement

Take a list of promises. Return a new promise that **resolves or rejects** as soon as **any** of the input promises resolves or rejects, with that one's value or reason. The losers keep doing whatever they were doing; their results are discarded.

This is the polyfill behind every `Promise.race(...)` you've ever called — and it's the foundation of `timeLimit(p, ms)` (race a promise against a timeout).

---

## 3. Why this matters in interviews

`Promise.race` is the second-most-asked promise polyfill after `Promise.all`. It's only six lines, but those six lines test whether you know that (a) the outer promise's `resolve`/`reject` can be invoked from any of the inner promises' settlement handlers, (b) the **promise state machine** silently absorbs later settlements (so "first wins" needs no explicit guard), and (c) **both fulfillment AND rejection** propagate — `race` is not "first fulfilled" (that's `Promise.any`). The single most common bug: candidates skip the rejection handler. The empty-array case is a beautiful trap: native `Promise.race([])` stays pending forever because there's no way for it to settle.

---

## 4. Mental model

The outer Promise constructor exposes one `resolve` and one `reject`. We hand them out to every input promise as their `.then(onFulfilled, onRejected)` handlers. Whichever inner settles first invokes its handler, which calls the outer's resolver. The outer's state machine locks on first settle; subsequent invocations from other inners are silent no-ops.

```
   new Promise((resolve, reject) => {
     ┌───────────────────┐
     │ inputs:           │
     │   p1.then(resolve, reject)   ─┐
     │   p2.then(resolve, reject)   ─┤
     │   p3.then(resolve, reject)   ─┤───▶  whoever fires first wins
     │   ...                         │      others' calls are no-ops
     └───────────────────┘
   })
```

**Why no `settled` flag is needed**: the outer Promise can transition only once. Its `resolve` and `reject` guard with `if (state !== PENDING) return`. The state machine is the implicit single-settle enforcer.

Compare with siblings:

| Combinator     | Settles on              | Final value/reason                                 |
|----------------|--------------------------|-----------------------------------------------------|
| `all`          | all fulfill OR one rejects | array of values OR first rejection                  |
| `allSettled`   | all settle                | array of `{status, value/reason}`                   |
| `any`          | first fulfillment OR all rejected | first value OR `AggregateError`                |
| **`race`**     | **first settle (either)**| **first value OR first reason**                    |

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `Promise.race([5, sleep(100, 'a')])` — what does it resolve with, and when?
> 2. `Promise.race([Promise.reject('x'), sleep(100, 'a')])` — does it resolve or reject?
> 3. `Promise.race([])` — does it resolve, reject, or never settle?

---

## 6. Brute force — walked through

### Wrong attempt 1: only handle fulfillment

```js
function promiseRace(promises) {
  return new Promise((resolve, reject) => {
    for (const p of promises) {
      Promise.resolve(p).then(resolve);   // BUG: no rejection handler
    }
  });
}
```

If the first to settle is a rejection, the outer stays pending — eventually the second one fulfills and resolves. That's **`Promise.any`** semantics (first fulfillment wins), not `race` semantics. Add the second arg.

### Wrong attempt 2: explicit `settled` flag (works but redundant)

```js
function promiseRace(promises) {
  return new Promise((resolve, reject) => {
    let settled = false;
    for (const p of promises) {
      Promise.resolve(p).then(
        (v) => { if (!settled) { settled = true; resolve(v); } },
        (e) => { if (!settled) { settled = true; reject(e); } }
      );
    }
  });
}
```

**Works**, but the `settled` guard is dead weight. The promise state machine already enforces single-settle — subsequent calls to `resolve`/`reject` are no-ops. Submitting the clean version *and articulating* "we don't need a guard because the outer promise can only settle once" scores senior signal.

### Wrong attempt 3: handle empty array by resolving with `undefined`

```js
if (promises.length === 0) return Promise.resolve();   // BUG: doesn't mirror native
```

**Native `Promise.race([])` stays pending forever.** There's no input to provide a value; resolving with `undefined` would silently swap one definition for another. Mirror the native behavior or *intentionally* deviate with a documented reason.

---

## 7. The unlocking insight

> **The outer Promise's `resolve` and `reject` are just functions you can pass to every input's `.then(onFulfilled, onRejected)`. Whichever input settles first calls its handler; the outer's state machine locks on first settle and ignores the rest.**

Six lines:

```js
function promiseRace(promises) {
  return new Promise((resolve, reject) => {
    for (const p of promises) {
      Promise.resolve(p).then(resolve, reject);
    }
  });
}
```

Three subtle properties to articulate:

1. **`Promise.resolve(p)` coerces** non-promise values and thenables into real promises. Without it, a literal `5` in the input would crash on `.then`. With it, `5` becomes a pre-fulfilled promise whose `.then` enqueues `resolve(5)` as the next microtask — winning the race if no other inner is already fulfilled.

2. **Two-arg `.then(resolve, reject)`** registers both fulfillment and rejection handlers in one call. Equivalent to `.then(resolve).catch(reject)` semantically but one fewer microtask (no intermediate promise). This is `race`'s signature move.

3. **Empty iterable → pending forever.** The loop doesn't execute → no handlers registered → `resolve` and `reject` never invoked → outer stays pending. This mirrors native `Promise.race([])`. Many candidates think it should resolve with `undefined`; state explicitly that the native behavior is intentional.

**Side effects of losing:** the losers' underlying work runs to completion. `race` does not cancel siblings. If they're HTTP requests, the responses arrive and are discarded — possibly wasting bandwidth, but harmless for correctness. For true cancellation, combine with `AbortController` (see Variant 3).

---

## 8. Solution (annotated)

```js
function promiseRace(promises) {
  return new Promise((resolve, reject) => {                              // step 1: outer Promise
    if (promises == null || typeof promises[Symbol.iterator] !== 'function') {
      return reject(new TypeError('promiseRace expects an iterable'));    // step 2: validate
    }
    for (const p of promises) {                                            // step 3: iterate inputs
      Promise.resolve(p).then(resolve, reject);                            // step 4: hand outer's resolvers
                                                                            //         to each input's .then
    }
    // Note: empty iterable → loop doesn't execute → outer stays pending forever.
    // This matches native Promise.race([]).
  });
}
```

**Try it yourself**

```js
const sleep = (ms, v) => new Promise((r) => setTimeout(() => r(v), ms));

// First fulfillment wins
promiseRace([sleep(100, 'slow'), sleep(20, 'fast'), sleep(50, 'mid')])
  .then(console.log);   // 'fast' at t≈20

// First rejection wins
promiseRace([sleep(100, 'a'), Promise.reject('boom')])
  .then(console.log, (e) => console.log('err:', e));   // err: boom (at t=0 microtask)

// Non-promise values coerced
promiseRace([5, sleep(100, 'a')]).then(console.log);   // 5 (next microtask)

// All fulfilled — first in iteration order wins
promiseRace([Promise.resolve('a'), Promise.resolve('b')]).then(console.log);   // 'a'

// Empty array stays pending forever
const stuck = promiseRace([]);
setTimeout(() => console.log('5s passed, still:', stuck), 5_000);
// after 5s: "5s passed, still: Promise { <pending> }"
```

---

## 9. Step-by-step dry run

Input:

```js
const sleep = (ms, v) => new Promise((r) => setTimeout(() => r(v), ms));
promiseRace([sleep(100, 'slow'), sleep(20, 'fast'), sleep(50, 'mid')])
  .then(console.log);
```

Values-first trace:

| Time (ms) | Event                                       | Outer state         | Output       |
|-----------|----------------------------------------------|----------------------|---------------|
| 0         | outer Promise constructed; loop registers 3 `.then` handlers | PENDING | — |
| 20        | `sleep(20,'fast')` fulfills with `'fast'`    | PENDING → FULFILLED  | (queue cb)    |
| 20+µ      | outer's `.then(console.log)` microtask runs  | FULFILLED            | `fast`        |
| 50        | `sleep(50,'mid')` fulfills; `resolve('mid')` called | FULFILLED      | (no-op)       |
| 100       | `sleep(100,'slow')` fulfills; `resolve('slow')` called | FULFILLED  | (no-op)       |

The outer settles at t=20. Later settle calls are silent no-ops because the state machine has locked.

**Rejection-first trace:**

```js
promiseRace([sleep(100, 'a'), Promise.reject(new Error('boom'))])
  .then(console.log, (e) => console.log('err:', e.message));
```

| Time | Event                                         | Outer state        | Output      |
|------|------------------------------------------------|---------------------|--------------|
| 0    | `Promise.reject(...)` is already rejected; `.then(resolve, reject)` schedules `reject(...)` as a microtask | PENDING | — |
| 0+µ  | microtask fires: `reject(Error('boom'))`        | PENDING → REJECTED  | (queue cb)   |
| 0+2µ | outer's `.then`'s rejection handler microtask  | REJECTED            | `err: boom`  |
| 100  | `sleep(100,'a')` fulfills; `resolve('a')` called | REJECTED          | (no-op)      |

Note: the rejection wins at t=0 (effectively), not at t=100.

**Empty trace:**

```js
promiseRace([]).then(() => console.log('done'), () => console.log('err'));
// nothing ever logs — outer stays pending forever
```

---

## 10. Common confusion + traps

1. **Forgetting the rejection handler.**
   `.then(resolve)` alone makes the function behave like `Promise.any` (first fulfillment wins). Use `.then(resolve, reject)` to mirror `race`'s "first either wins" semantics.

2. **Conflating `race` with `any`.**
   `any` = first **fulfillment** wins; rejects only if all reject (with `AggregateError`). `race` = first **either** wins.

3. **Empty array returning `undefined`.**
   Native stays pending forever. Some interviewers expect you to deviate and document; usually they want the mirror behavior. State both options.

4. **Adding a `settled` guard.**
   Works, but redundant. The promise state machine enforces single-settle. Show you trust it.

5. **Forgetting `Promise.resolve(p)`.**
   Without it, a non-promise input (a literal `5`) crashes on `.then`. Always coerce.

6. **Cancellation expectations.**
   `race` does not cancel losers. Their underlying work continues. For true cancellation, wrap each input in an `AbortController` and abort on first settle (see Variant 3).

7. **Memory in long-running processes.**
   Every input promise has a `.then` callback attached. If you race a "fast" promise against a "never settles" promise, the never-settles one retains its handlers forever. Small leak; matters in long-lived processes.

---

## 11. Senior follow-ups & variants

### Variant 1 — `Promise.any` polyfill (first fulfillment, AggregateError on all-reject)

```js
function promiseAny(promises) {
  return new Promise((resolve, reject) => {
    const arr = Array.from(promises);
    if (arr.length === 0) return reject(new AggregateError([], 'No promises'));
    const errors = new Array(arr.length);
    let pending = arr.length;
    arr.forEach((p, i) => {
      Promise.resolve(p).then(resolve, (e) => {
        errors[i] = e;
        if (--pending === 0) reject(new AggregateError(errors, 'All promises were rejected'));
      });
    });
  });
}
```

Mirror image of `all`: count rejections, resolve on first fulfillment.

### Variant 2 — `timeLimit(promise, ms)` — race with timeout

```js
function timeLimit(promise, ms) {
  return Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error(`timeout ${ms}ms`)), ms)),
  ]);
}

await timeLimit(slowFetch(), 5_000);   // throws if slowFetch takes > 5s
```

The canonical use of `race` in production. See [promise-time-limit.md](./promise-time-limit.md) for the full breakdown.

### Variant 3 — Cancellable race (abort losers)

```js
function promiseRaceCancelable(promiseFactories) {
  const controllers = promiseFactories.map(() => new AbortController());
  return new Promise((resolve, reject) => {
    promiseFactories.forEach((factory, i) => {
      Promise.resolve(factory(controllers[i].signal)).then(
        (v) => {
          resolve(v);
          controllers.forEach((c, j) => j !== i && c.abort());
        },
        (e) => {
          reject(e);
          controllers.forEach((c, j) => j !== i && c.abort());
        }
      );
    });
  });
}

// Usage
const result = await promiseRaceCancelable([
  (signal) => fetch('/replica-a', { signal }),
  (signal) => fetch('/replica-b', { signal }),
]);
// Whichever responds first wins; the other's fetch is aborted.
```

Only useful if the inner work actually honors the signal (`fetch` does).

### Variant 4 — `firstSuccessful` — like `any` but with timeout

```js
function firstSuccessful(promises, timeoutMs) {
  return Promise.race([
    promiseAny(promises),
    new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), timeoutMs)),
  ]);
}
```

"Either someone succeeds within the budget, or we error out." Used in fallback chains (CDN → origin → cache).

### Variant 5 — Race with priority (fallback chains)

Given `[(promise, priority)]`, settle with the **highest-priority** result that arrives within a time window. Used for "try fast cache first; fall back to slower DB after 50ms."

```js
function priorityRace(items, windowMs) {
  return new Promise((resolve, reject) => {
    let best = null;
    items.forEach(({ promise, priority }) => {
      Promise.resolve(promise).then((v) => {
        if (!best || priority > best.priority) best = { value: v, priority };
      });
    });
    setTimeout(() => best ? resolve(best.value) : reject(new Error('none')), windowMs);
  });
}
```

---

## 12. How to think aloud in the interview

> "`Promise.race` settles as soon as any input settles, with that one's value or reason. Six lines: `new Promise((resolve, reject) => { for (const p of promises) Promise.resolve(p).then(resolve, reject); })`. Two-arg `.then` registers both handlers in one call. `Promise.resolve(p)` coerces non-promises and thenables. No `settled` flag needed — the outer promise's state machine ensures one transition; subsequent calls are no-ops. Empty iterable stays pending forever (mirrors native). Losers' work continues unless you wrap with `AbortController`. Don't confuse with `Promise.any` — `any` waits for the first fulfillment and rejects with `AggregateError` only if all reject. Canonical production use: `timeLimit(promise, ms)` races the work against a setTimeout-rejecter."

---

## 13. 60-second revision

> - **Six lines:** `new Promise((resolve, reject) => { for (const p of promises) Promise.resolve(p).then(resolve, reject); })`.
> - **First settle wins — resolve OR reject.** Different from `Promise.any` (first fulfillment only).
> - **Empty iterable → pending forever.** Mirrors native.
> - **No `settled` flag** — state machine ensures one transition.
> - **Losers keep running.** Combine with `AbortController` for real cancellation.
> - **`Promise.resolve(p)`** to coerce values + thenables.
> - **Two-arg `.then(onFulfilled, onRejected)`** — `race`'s signature move.
> - **Family:** `all` (all-or-first-reject), `allSettled` (never rejects), `any` (first fulfillment + `AggregateError`), `race` (first either).
> - **Canonical use:** `timeLimit(p, ms)`.
> - **Trap:** forgetting the rejection handler; conflating with `Promise.any`; expecting empty to resolve.

---

**Related:** [promise-all-polyfill.md](./promise-all-polyfill.md) · [promise-allsettled-polyfill.md](./promise-allsettled-polyfill.md) · [promise-any-polyfill.md](./promise-any-polyfill.md) · [promise-time-limit.md](./promise-time-limit.md) · [build-promise-from-scratch.md](./build-promise-from-scratch.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
