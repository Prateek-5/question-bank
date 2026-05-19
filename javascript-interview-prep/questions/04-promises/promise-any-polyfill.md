# Implement `Promise.any(promises)` polyfill — first fulfillment wins; AggregateError on all-reject

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [promise-all-polyfill.md](./promise-all-polyfill.md), [promise-race-polyfill.md](./promise-race-polyfill.md)
>
> **Source:** ES2021. BFE.dev #45, LeetCode #2637 family. MDN: [Promise.any](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/any).

---

## 1. Problem statement

**Signature**
```ts
function promiseAny<T>(promises: Iterable<T | PromiseLike<T>>): Promise<T>;
```

**Input / Output examples**

| Input                                                                  | Output                                                |
|------------------------------------------------------------------------|--------------------------------------------------------|
| `promiseAny([fail('A'), fail('B'), sleep(100,'C')])`                  | resolves with `'C'` at t=100 (first fulfillment wins) |
| `promiseAny([fail('A'), fail('B'), fail('C')])`                       | rejects with `AggregateError(['A','B','C'], '...')`   |
| `promiseAny([1, sleep(100,'a')])`                                      | resolves with `1` immediately (non-promise coerced)   |
| `promiseAny([])`                                                       | rejects with `AggregateError([], 'No promises')`      |
| Mix of rejects and successes — first fulfillment in time wins         | input order preserved in `.errors` array              |

**Constraints**
- Resolves with **first fulfillment**. Ignores intermediate rejections.
- Rejects with `AggregateError` **only when all inputs reject**.
- Empty iterable → reject with empty `AggregateError`.
- `errors` array on the AggregateError is in **input order**, not settlement order.

---

## 2. Plain-English restatement

Take a list of promises. Return a new promise that resolves with the value of the **first one to succeed**, regardless of how many fail along the way. If *every* one fails, reject with an `AggregateError` whose `.errors` array contains every reason in input order.

This is the **failure-tolerant racer**. Use it when you have N redundant data sources (CDN mirrors, fallback APIs, replica DBs) and you want the first that works — without giving up just because the first to *respond* happens to have failed.

---

## 3. Why this matters in interviews

`Promise.any` completes the trio after `all` and `race`. It's the **failure-tolerant racer**. Interviewers ask it to test (1) whether you know it exists at all (juniors don't), (2) **`AggregateError` handling** — the only standard Promise combinator that wraps multiple errors, (3) whether you correctly *invert* `all`'s logic — reject-on-all instead of fulfill-on-all. The classic mistake is using `race` semantics, which fail too fast.

---

## 4. Mental model

Mirror image of `Promise.all`. Where `all` resolves on *all* fulfillments and rejects on *first* rejection, `any` resolves on *first* fulfillment and rejects on *all* rejections. The outer counts rejections, not fulfillments. Counter hits zero → all failed → reject with `AggregateError`.

```
   new Promise((resolve, reject) => {
     const errors = new Array(N);
     let pending = N;
     
     promises.forEach((p, i) => {
       Promise.resolve(p).then(
         (v) => resolve(v),                    // first fulfillment wins
         (e) => {
           errors[i] = e;                       // collect rejection by index
           if (--pending === 0) reject(new AggregateError(errors, 'All rejected'));
         }
       );
     });
   });
   
   N tasks fire in parallel.
   First fulfillment → outer resolves with that value.
   Every rejection writes to errors[i] and decrements.
   Counter hits 0 → outer rejects with AggregateError.
```

**Side-by-side comparison with siblings:**

| Combinator     | Resolves on        | Rejects on              | Output on success      | Output on failure                |
|----------------|---------------------|--------------------------|--------------------------|------------------------------------|
| `all`          | all fulfill         | first reject             | array of values          | first reason                       |
| `allSettled`   | all settle          | (never)                  | array of descriptors     | (never)                            |
| `race`         | first fulfill       | first reject             | first value              | first reason                       |
| **`any`**      | **first fulfill**   | **all reject**           | **first value**          | **`AggregateError(errors)`**       |

`race` and `any` look similar — both "first something wins." The difference: `race` accepts the first *anything* (resolve or reject); `any` ignores rejections and waits for the first fulfillment.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `promiseAny([Promise.reject('A'), Promise.reject('B'), Promise.resolve('C')])` — does it resolve with `'C'` or reject?
> 2. `promiseAny([])` — does it resolve, reject, or stay pending?
> 3. If `errors` is collected via `push` (settlement order) vs `errors[i] = e` (input order), what's the difference observable? When would it matter?

---

## 6. Brute force — walked through

### Wrong attempt 1: sequential `await`

```js
async function brute(promises) {
  const errors = [];
  for (const p of promises) {
    try { return await p; }
    catch (e) { errors.push(e); }
  }
  throw new AggregateError(errors, 'All rejected');
}
```

**Sequential** — defeats parallel racing. If `p1` takes 5s to reject and `p2` succeeds in 100ms, this waits 5s before even trying `p2`. The whole point of `any` is to fan out in parallel; the first to *fulfill* wins regardless of others.

### Wrong attempt 2: use `race` semantics

```js
function promiseAny(promises) {
  return promiseRace(promises);   // BUG: wrong semantics
}
```

`race` settles on the first to *settle* — including rejections. `any` ignores rejections. If the first promise to settle is a rejection, `race` rejects with it; `any` waits for a fulfillment (or for all to reject).

### Wrong attempt 3: `errors.push` instead of `errors[i] = e`

```js
(err) => {
  errors.push(err);            // BUG: settlement order, not input order
  if (errors.length === total) reject(new AggregateError(errors));
}
```

The spec requires `errors` in **input order**. Settlement order is non-deterministic and unhelpful (caller can't correlate `errors[k]` with `promises[k]`). Use `errors[i] = e` with the closure-captured index.

### Wrong attempt 4: forget empty array

```js
function promiseAny(promises) {
  // No empty check.
  return new Promise((resolve, reject) => {
    promises.forEach((p, i) => { ... });
  });
}
promiseAny([]);   // BUG: pending forever (no inputs → no rejection counter triggers)
```

Spec: empty iterable rejects **synchronously** with empty `AggregateError`. Always handle first.

---

## 7. The unlocking insight

> **Invert `Promise.all`'s logic: count *rejections* instead of fulfillments. Resolve on first fulfillment; reject with `AggregateError(errors)` when the rejection count hits N.**

Four key invariants:

1. **First fulfillment wins.** `resolve(value)` is called directly from the fulfillment handler. The state machine ensures only the first such call has effect; subsequent fulfillments are silent no-ops.

2. **Rejections accumulate by input index.** `errors[i] = e` (not `errors.push`) preserves input order. The closure captures `i` per `.forEach` iteration.

3. **All-rejected → `AggregateError`.** This is the only standard combinator that wraps multiple errors. Construct with `new AggregateError(errorsArray, messageString)`.

4. **Empty iterable** rejects synchronously (well, on the microtask) with an empty `AggregateError`. Don't return undefined or stay pending.

**`AggregateError` cheat sheet:**

```js
const err = new AggregateError(['err1', 'err2', 'err3'], 'All rejected');
err instanceof AggregateError;   // true
err instanceof Error;             // true
err.errors;                       // ['err1', 'err2', 'err3']  (the original iterable)
err.message;                      // 'All rejected'
err.name;                         // 'AggregateError'
```

Available in Node 15+ / modern browsers. For older runtimes, polyfill:

```js
if (typeof AggregateError === 'undefined') {
  globalThis.AggregateError = class extends Error {
    constructor(errors, message) {
      super(message);
      this.name = 'AggregateError';
      this.errors = Array.from(errors);
    }
  };
}
```

---

## 8. Solution (annotated)

```js
function promiseAny(iterable) {
  return new Promise((resolve, reject) => {
    const promises = Array.from(iterable);                                // step 1: materialize iterable

    if (promises.length === 0) {                                           // step 2: empty edge case
      return reject(new AggregateError([], 'All promises were rejected'));
    }

    const errors = new Array(promises.length);                             // step 3: index-keyed errors
    let rejectedCount = 0;

    promises.forEach((p, i) => {
      Promise.resolve(p).then(                                              // step 4: wrap non-promises
        (value) => resolve(value),                                           //         first fulfillment wins
        (err) => {                                                            //         collect rejection
          errors[i] = err;                                                    //         INPUT INDEX, not push
          rejectedCount += 1;
          if (rejectedCount === promises.length) {                            // step 5: all rejected
            reject(new AggregateError(errors, 'All promises were rejected'));
          }
        }
      );
    });
  });
}
```

**Try it yourself**

```js
const sleep = (ms, v) => new Promise((r) => setTimeout(() => r(v), ms));
const fail  = (ms, e) => new Promise((_, j) => setTimeout(() => j(e), ms));

// First fulfillment wins
const winner = await promiseAny([fail(50, 'A'), sleep(30, 'B'), fail(20, 'C')]);
console.log(winner);   // 'B' at t=30

// All reject
try {
  await promiseAny([fail(10, 'A'), fail(20, 'B'), fail(30, 'C')]);
} catch (e) {
  console.log(e instanceof AggregateError);   // true
  console.log(e.errors);                       // ['A', 'B', 'C']  (INPUT order)
  console.log(e.message);                      // 'All promises were rejected'
}

// Empty
try { await promiseAny([]); } catch (e) {
  console.log(e.errors);                       // []
}

// Non-promise coerced
await promiseAny([1, sleep(100, 'a')]);        // resolves with 1 immediately

// Use case: redundant data sources
const data = await promiseAny([
  fetch('https://cdn-a.example.com/data'),
  fetch('https://cdn-b.example.com/data'),
  fetch('https://cdn-c.example.com/data'),
]);
// Whichever CDN responds first wins; others continue but their results are dropped
```

---

## 9. Step-by-step dry run

Input:

```js
const p1 = new Promise((_, rej) => setTimeout(() => rej('A failed'), 50));
const p2 = new Promise((_, rej) => setTimeout(() => rej('B failed'), 30));
const p3 = new Promise((res)    => setTimeout(() => res('C wins'),   100));

promiseAny([p1, p2, p3]).then((v) => console.log(v), (e) => console.log(e.errors));
```

Values-first trace:

| Time (ms) | Event                                            | `errors`                                | `rejectedCount` | Outer state         |
|-----------|---------------------------------------------------|------------------------------------------|------------------|----------------------|
| 0         | outer constructed; 3 handlers registered          | `[_, _, _]`                              | 0                | PENDING              |
| 30        | p2 rejects with `'B failed'`                       | `[_, 'B failed', _]`                     | 1                | PENDING              |
| 50        | p1 rejects with `'A failed'`                       | `['A failed', 'B failed', _]`            | 2                | PENDING              |
| 100       | p3 fulfills with `'C wins'`                        | (unchanged)                              | 2                | FULFILLED            |
| 100+µ     | outer's `.then(...)` fires; prints `'C wins'`     |                                          |                  |                      |

Output: `C wins` at t=100. The two earlier rejections are silently absorbed.

**All-reject trace** (replace p3 with `fail(60, 'C failed')`):

| Time | Event                                | `errors`                                 | `rejectedCount` | Outer state         |
|------|---------------------------------------|-------------------------------------------|------------------|----------------------|
| 30   | p2 rejects                            | `[_, 'B failed', _]`                      | 1                | PENDING              |
| 50   | p1 rejects                            | `['A failed', 'B failed', _]`             | 2                | PENDING              |
| 60   | p3 rejects                            | `['A failed', 'B failed', 'C failed']`    | 3 → all rejected | REJECTED with `AggregateError`  |
| 60+µ | outer's rejection handler fires; prints `.errors` array | | | |

Output: `['A failed', 'B failed', 'C failed']` — **input order**, not settlement order (`['B', 'A', 'C']`).

---

## 10. Common confusion + traps

1. **Confusing `any` with `race`.** `race` settles on first either; `any` ignores rejections, waits for first fulfillment. Don't conflate.

2. **`errors.push(err)` instead of `errors[i] = err`.** Push gives settlement order; spec requires input order.

3. **Forgetting `AggregateError`.** Must be `new AggregateError(errors, message)`, not a plain Error. `err.errors` is the array.

4. **Forgetting empty array.** Spec: reject immediately with empty `AggregateError`. Don't return `undefined` or stay pending.

5. **Sequential `await` version.** Correct shape, but kills the parallel racing — defeats `any`'s purpose.

6. **Forgetting `Promise.resolve` wrap.** Non-promise inputs (`[1, p, ...]`) crash on `.then`. Always coerce.

7. **`AggregateError` polyfill.** Node 15+ / modern browsers have it. For older targets, polyfill by extending Error.

8. **Not deciding what "fulfilled" means.** `any` treats any successful settle as a win — even `Promise.resolve(undefined)`. There's no "first non-undefined" or "first truthy" semantics; that's `Promise.firstWhere(predicate)`, a different beast.

9. **Memory leak on long-running rejects.** Every input has `.then` callbacks attached. If you race a fast fulfiller against a "never settles" promise, the never-settles one retains its handlers forever. Small leak in long-lived processes.

---

## 11. Senior follow-ups & variants

### Variant 1 — `Promise.firstSuccessful` with timeout

```js
function firstSuccessful(promises, timeoutMs) {
  return Promise.race([
    promiseAny(promises),
    new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), timeoutMs)),
  ]);
}
```

"Any of these within the budget, or fail." Common in fallback chains (CDN → origin → cache).

### Variant 2 — `anyWithLimit(promises, k)` — first `k` to fulfill

```js
function anyWithLimit(promises, k) {
  return new Promise((resolve, reject) => {
    const arr = Array.from(promises);
    if (k > arr.length) return reject(new RangeError('k > N'));
    const fulfilled = [];
    const errors = new Array(arr.length);
    let rejectedCount = 0;
    arr.forEach((p, i) => {
      Promise.resolve(p).then(
        (v) => { fulfilled.push(v); if (fulfilled.length === k) resolve(fulfilled); },
        (e) => {
          errors[i] = e;
          if (++rejectedCount > arr.length - k) {
            reject(new AggregateError(errors, `fewer than ${k} fulfilled`));
          }
        }
      );
    });
  });
}
```

"Need at least k successes." Useful for quorum reads or rate-limited fan-outs.

### Variant 3 — Cancel losing requests on first win

```js
async function promiseAnyCancelable(factories) {
  const controllers = factories.map(() => new AbortController());
  try {
    return await promiseAny(factories.map((f, i) => f(controllers[i].signal)));
  } finally {
    controllers.forEach((c) => c.abort());   // abort any still-pending
  }
}
```

Each input is a factory `(signal) => Promise`. On first win, abort the others. Useful for redundant fetches that consume bandwidth.

### Variant 4 — Tolerate at most N failures

```js
function tolerantAll(promises, maxFailures) {
  return new Promise((resolve, reject) => {
    const arr = Array.from(promises);
    const results = new Array(arr.length);
    const errors = [];
    let pending = arr.length;
    arr.forEach((p, i) => {
      Promise.resolve(p).then(
        (v) => { results[i] = v; if (--pending === 0) resolve({ results, errors }); },
        (e) => {
          errors.push(e);
          if (errors.length > maxFailures) reject(new AggregateError(errors, 'too many failed'));
          else if (--pending === 0) resolve({ results, errors });
        }
      );
    });
  });
}
```

"At most M can fail." Useful for quorum-style consistency models.

### Variant 5 — Compose with retry

`Promise.any` of retried promises:

```js
const winner = await promiseAny([
  retryWithBackoff(() => fetchA(), { retries: 3 }),
  retryWithBackoff(() => fetchB(), { retries: 3 }),
  retryWithBackoff(() => fetchC(), { retries: 3 }),
]);
```

Each lane retries on its own; the first lane to ultimately succeed wins. See [retry-with-backoff.md](./retry-with-backoff.md).

---

## 12. How to think aloud in the interview

> "`Promise.any` is the mirror image of `Promise.all`. Where `all` resolves on all-fulfilled and rejects on first-reject, `any` resolves on first-fulfilled and rejects on all-rejected. Same fan-out skeleton: outer Promise, `errors = new Array(n)`, `rejectedCount = 0`. Each input's `.then(resolve, onReject)` — fulfillment resolves the outer directly; rejection writes `errors[i] = err` and increments the counter. When counter equals N, reject with `new AggregateError(errors, 'All rejected')`. Empty iterable → reject immediately with empty AggregateError. `errors` is in input order (use index, not push). Use case: redundant data sources, CDN failover, quorum reads."

---

## 13. 60-second revision

> - **Pattern:** mirror image of `Promise.all`. Count *rejections*, resolve on first fulfillment.
> - **First fulfillment → resolve outer** (state machine handles "first wins").
> - **All-rejected → reject with `AggregateError(errors, 'All rejected')`.**
> - **`errors[i] = e`** (index-keyed) — preserves input order.
> - **Empty iterable** → reject immediately with empty AggregateError.
> - **`AggregateError.errors`** is the original iterable; `.message` is the string.
> - **`Promise.resolve(p)`** to coerce non-promises and thenables.
> - **Family:** `all` (fail-fast), `allSettled` (wait-all, never reject), `race` (first either), **`any`** (first fulfill / all-reject).
> - **Trap:** confusing with `race`; `errors.push` instead of index; forgetting empty case; not using `AggregateError`.

---

**Related:** [promise-all-polyfill.md](./promise-all-polyfill.md) · [promise-allsettled-polyfill.md](./promise-allsettled-polyfill.md) · [promise-race-polyfill.md](./promise-race-polyfill.md) · [retry-with-backoff.md](./retry-with-backoff.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
