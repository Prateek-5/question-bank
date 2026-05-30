# Implement `Promise.allSettled(promises)` polyfill — wait-all, never reject

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [promise-all-polyfill.md](./promise-all-polyfill.md), [build-promise-from-scratch.md](./build-promise-from-scratch.md)
>
> **Source:** ES2020. Canonical polyfill interview problem. MDN: <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/allSettled" target="_blank" rel="noopener noreferrer">Promise.allSettled</a>.

---

## 1. Problem statement

**Signature**
```ts
type Settled<T> = { status: 'fulfilled'; value: T } | { status: 'rejected'; reason: any };

function promiseAllSettled<T>(promises: Array<T | PromiseLike<T>>): Promise<Settled<T>[]>;
```

**Input / Output examples**

| Input                                                              | Output                                                                               |
|--------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| `promiseAllSettled([sleep(50,'a'), reject('boom'), 'plain'])`     | `[{status:'fulfilled',value:'a'}, {status:'rejected',reason:'boom'}, {status:'fulfilled',value:'plain'}]` |
| All inputs fulfill                                                  | All-fulfilled descriptors                                                            |
| All inputs reject                                                   | All-rejected descriptors — **outer still resolves** (never rejects)                  |
| `promiseAllSettled([])`                                            | resolves with `[]` immediately                                                       |
| Plain values (`['a', 'b']`)                                        | wrapped as `{status:'fulfilled',value:'a'}` etc.                                     |

**Constraints**
- Resolves with an array of `{status, value | reason}` descriptors in **input order**.
- **Never rejects** — the entire point of this combinator.
- Empty array → resolve with `[]` immediately.
- Status strings must be **exactly** `'fulfilled'` and `'rejected'`. Reason key is **`reason`**, not `error` or `data`.

---

## 2. Plain-English restatement

Fan out N tasks. Wait for **every** one to settle (fulfill or reject). Return an array describing each outcome — same shape as native `Promise.allSettled`. The outer never rejects, even if all inputs reject; you get back a per-input descriptor either way. Useful for "aggregate everything; tell me what worked and what didn't."

This is the **partial-failure-tolerant** version of `Promise.all`. Where `all` is fail-fast, `allSettled` is wait-all-never-fail.

---

## 3. Why this matters in interviews

`Promise.allSettled` is the right tool for **partial-failure-tolerant** backend fan-out (aggregate scores from 5 microservices; missing one is fine). The polyfill is structurally identical to `Promise.all`, with one crucial difference: **it never rejects**. Interviewers love watching candidates struggle to remember which one rejects and which doesn't. They also probe the `{status, value | reason}` shape — wrong key names (`'resolved'`, `error`, `data`) are an obvious "haven't used this in a while" signal.

---

## 4. Mental model

Same fan-out skeleton as `Promise.all`, but the rejection handler **also writes to results** (with a different shape) and decrements the counter. There's no `reject` path on the outer promise — only `resolve`.

```
   new Promise((resolve) => {            ← NO `reject` from constructor!
     const results = new Array(N);
     let remaining = N;
     
     promises.forEach((p, i) => {
       Promise.resolve(p).then(
         (value)  => { results[i] = { status: 'fulfilled', value };  decrementAndMaybeResolve(); },
         (reason) => { results[i] = { status: 'rejected',  reason }; decrementAndMaybeResolve(); },
       );
     });
   });
   
   Both onFulfilled and onRejected write to results[i].
   Counter ticks down on EITHER outcome.
   Outer only resolves; never rejects.
```

The other combinators for comparison:

| Combinator     | Settles on              | Outer can reject? | Output                          |
|----------------|--------------------------|-------------------|----------------------------------|
| `all`          | all fulfill / first reject | yes               | array OR rejection               |
| **`allSettled`** | **all settle**         | **NO**            | array of `{status, value/reason}`|
| `race`         | first either             | yes               | first value OR first reason     |
| `any`          | first fulfill / all reject | yes (AggregateError) | first value OR AggregateError |

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If all 3 inputs reject, does `allSettled` resolve or reject? What's in the result array?
> 2. Are the status strings `'fulfilled'` and `'rejected'`, or `'resolved'` and `'errored'`? (One is correct; the other is a classic interview slip.)
> 3. What's the key name for the failure value — `error`, `reason`, or `data`?

---

## 6. Brute force — walked through

### Wrong attempt 1: sequential `await` with try/catch

```js
async function brute(promises) {
  const out = [];
  for (const p of promises) {
    try { out.push({ status: 'fulfilled', value: await p }); }
    catch (reason) { out.push({ status: 'rejected', reason }); }
  }
  return out;
}
```

**Result shape is correct** — but the work is **serialized**. A 10-task workload takes the *sum* of latencies instead of the *max*. Defeats the parallelism. Mention as the wrong path.

### Wrong attempt 2: wrong status string

```js
results[i] = { status: 'resolved', value };   // BUG: spec says 'fulfilled'
```

The native spec uses `'fulfilled'` (matching the Promise state machine vocabulary). `'resolved'` is what people *say* informally; the spec is precise. If a caller does `.filter(r => r.status === 'fulfilled')`, your polyfill returns nothing. Wrong key strings = immediate test failure.

### Wrong attempt 3: forget to call `decrementAndMaybeResolve` on rejection

```js
promises.forEach((p, i) => {
  Promise.resolve(p).then(
    (value)  => { results[i] = { status: 'fulfilled', value }; if (--remaining === 0) resolve(results); },
    (reason) => { results[i] = { status: 'rejected', reason }; /* BUG: missing decrement */ }
  );
});
```

If any input rejects, `remaining` never hits 0 → outer hangs forever. **Both handlers must decrement** — the entire point is wait-for-all.

### Wrong attempt 4: forget empty array

```js
// No `if (n === 0) return resolve([])`.
promiseAllSettled([]);   // BUG: pending forever
```

Same trap as `Promise.all`. Always handle this first.

---

## 7. The unlocking insight

> **Same fan-out as `Promise.all`, with two changes: (1) the rejection handler also writes to results (with a different shape) and decrements the counter, and (2) the outer Promise never invokes `reject` — only `resolve`.**

Three key invariants:

1. **Both handlers write.** Fulfillment writes `{status: 'fulfilled', value}`; rejection writes `{status: 'rejected', reason}`. Both decrement the counter. The outer waits until *every* input settles.

2. **The outer never rejects.** You can omit `reject` from the constructor signature entirely if you want to make this visually obvious. Even if every input rejects, the outer resolves with an array of `{status: 'rejected', ...}` descriptors.

3. **Exact key names.** Spec is precise:
   - `status`: `'fulfilled'` or `'rejected'` (matching the Promise state names).
   - For fulfilled: key is `value`.
   - For rejected: key is `reason`.

Don't deviate. Callers that filter on `r.status === 'fulfilled'` or `.map(r => r.value)` will silently break with wrong keys.

**The elegant alternative**: build `allSettled` on top of `all` by mapping each input to a guaranteed-fulfilled descriptor:

```js
function promiseAllSettled(promises) {
  return promiseAll(
    promises.map((p) =>
      Promise.resolve(p).then(
        (value)  => ({ status: 'fulfilled', value }),
        (reason) => ({ status: 'rejected',  reason })
      )
    )
  );
}
```

Each map step produces a promise that *always* fulfills (with a descriptor). `Promise.all` over those wraps trivially succeeds. Four lines of composition; worth showing.

---

## 8. Solution (annotated)

```js
function promiseAllSettled(promises) {
  return new Promise((resolve) => {                            // step 1: ONLY resolve in signature
    if (!Array.isArray(promises)) {
      return resolve(Promise.reject(                            // step 2: invalid input → reject inner promise
        new TypeError('promiseAllSettled expects an array')
      ));
    }
    const n = promises.length;
    if (n === 0) return resolve([]);                            // step 3: empty array edge

    const results = new Array(n);                               // step 4: index-keyed results
    let remaining = n;

    const settle = (i, descriptor) => {                          // step 5: shared finalizer
      results[i] = descriptor;
      if (--remaining === 0) resolve(results);
    };

    for (let i = 0; i < n; i++) {
      Promise.resolve(promises[i]).then(
        (value)  => settle(i, { status: 'fulfilled', value }),  // step 6: BOTH handlers write
        (reason) => settle(i, { status: 'rejected', reason })   //         and decrement
      );
    }
  });
}

// Compose on top of Promise.all (elegant alternative)
function promiseAllSettledFromAll(promises) {
  return Promise.all(
    promises.map((p) =>
      Promise.resolve(p).then(
        (value)  => ({ status: 'fulfilled', value }),
        (reason) => ({ status: 'rejected',  reason })
      )
    )
  );
}
```

**Try it yourself**

```js
const sleep = (ms, v) => new Promise((r) => setTimeout(() => r(v), ms));
const fail  = (ms, e) => new Promise((_, j) => setTimeout(() => j(e), ms));

const results = await promiseAllSettled([
  sleep(50, 'a'),
  fail(20, new Error('boom')),
  'plain',
]);
console.log(results);
// [
//   { status: 'fulfilled', value: 'a' },
//   { status: 'rejected',  reason: Error('boom') },
//   { status: 'fulfilled', value: 'plain' },
// ]

// All reject — outer still resolves
const allFail = await promiseAllSettled([Promise.reject('x'), Promise.reject('y')]);
console.log(allFail);
// [{status:'rejected',reason:'x'}, {status:'rejected',reason:'y'}]

// Empty
await promiseAllSettled([]);   // []

// Best-effort fan-out pattern
const successes = results.filter((r) => r.status === 'fulfilled').map((r) => r.value);
const failures  = results.filter((r) => r.status === 'rejected').map((r) => r.reason);
```

---

## 9. Step-by-step dry run

Input:

```js
const sleep = (ms, v) => new Promise((r) => setTimeout(() => r(v), ms));
const fail  = (ms, e) => new Promise((_, j) => setTimeout(() => j(e), ms));

promiseAllSettled([sleep(50, 'a'), fail(20, new Error('boom')), 'plain']).then(console.log);
```

Values-first trace:

| Time (ms) | Event                                                            | `results`                                                                       | `remaining` |
|-----------|------------------------------------------------------------------|---------------------------------------------------------------------------------|-------------|
| 0         | outer constructed; 3 handlers registered                          | `[_, _, _]`                                                                     | 3           |
| 0+µ       | `'plain'` (already-fulfilled wrapper) fires onFulfilled           | `[_, _, {status:'fulfilled', value:'plain'}]`                                  | 2           |
| 20        | `fail(20, 'boom')` rejects; onRejected fires                       | `[_, {status:'rejected', reason:Error('boom')}, {status:'fulfilled', value:'plain'}]` | 1           |
| 50        | `sleep(50, 'a')` fulfills; onFulfilled fires                       | `[{status:'fulfilled', value:'a'}, {status:'rejected',...}, {status:'fulfilled',...}]` | 0 → resolve |
| 50+µ      | outer's `.then(console.log)` fires                                 |                                                                                 |             |

Output: array in **input order** `[a, boom, plain]` — not completion order `[plain, boom, a]`. Index-keyed writes ensure this.

---

## 10. Common confusion + traps

1. **Wrong status string.** Spec says `'fulfilled'` / `'rejected'`. Not `'resolved'`, not `'errored'`, not `'ok'`. Match the Promise state-name vocabulary.

2. **Wrong reason key.** Spec says `reason`. Not `error`, not `data`. Don't improvise.

3. **Forgetting to decrement on rejection.** Outer hangs forever if any input rejects. Both handlers must call the shared `settle` function.

4. **Forgetting empty array.** Counter never hits 0. Always `if (n === 0) return resolve([])` first.

5. **Submitting the sequential `await` version.** Correct result but serializes. Defeats parallelism.

6. **Trying to make `allSettled` reject.** It doesn't. Even if all inputs reject, the outer resolves with the rejection descriptors. That's the point.

7. **Building on top of `all` without unwrapping.** If you forget the `.then` wrap, a rejection from any input crashes `all`. The composition only works because the `.then` converts rejections into fulfilled descriptors.

8. **Non-thenable inputs.** `Promise.resolve('plain').then(...)` produces a fulfilled descriptor. Wrap every input uniformly.

---

## 11. Senior follow-ups & variants

### Variant 1 — Built on top of `Promise.all` (composition)

```js
function promiseAllSettledFromAll(promises) {
  return Promise.all(
    promises.map((p) =>
      Promise.resolve(p).then(
        (value)  => ({ status: 'fulfilled', value }),
        (reason) => ({ status: 'rejected',  reason })
      )
    )
  );
}
```

Each map step converts a possibly-rejecting promise into a guaranteed-fulfilled descriptor. `Promise.all` over those trivially succeeds. Show this for senior signal — demonstrates composability.

### Variant 2 — Result filter helper

The most common downstream pattern:

```js
const settled = await promiseAllSettled(promises);
const okValues = settled.filter((r) => r.status === 'fulfilled').map((r) => r.value);
const errors   = settled.filter((r) => r.status === 'rejected').map((r) => r.reason);
```

In real code, you might want a small helper:

```js
function partitionSettled(settled) {
  const successes = [];
  const failures  = [];
  for (const r of settled) {
    if (r.status === 'fulfilled') successes.push(r.value);
    else failures.push(r.reason);
  }
  return { successes, failures };
}
```

### Variant 3 — Tagged result map (object form)

`allSettledObject({ a: p1, b: p2 })` returns `{ a: {status,...}, b: {status,...} }`:

```js
async function allSettledObject(obj) {
  const keys = Object.keys(obj);
  const settled = await promiseAllSettled(keys.map((k) => obj[k]));
  return Object.fromEntries(keys.map((k, i) => [k, settled[i]]));
}
```

Useful when fanning out to many APIs and you want to refer to results by name.

### Variant 4 — Concurrency-limited `allSettled`

Combine with `asyncPool` (see [promise-pool.md](./promise-pool.md)) for "fan out to a rate-limited API; collect all outcomes":

```js
async function asyncPoolSettled(concurrency, tasks) {
  const results = new Array(tasks.length);
  let i = 0;
  async function worker() {
    while (i < tasks.length) {
      const idx = i++;
      try { results[idx] = { status: 'fulfilled', value: await tasks[idx]() }; }
      catch (reason) { results[idx] = { status: 'rejected', reason }; }
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, tasks.length) }, worker));
  return results;
}
```

### Variant 5 — `Promise.any` polyfill (mirror image)

`any` is the mirror image of `all`: count *rejections*, resolve on first fulfillment.

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
        if (--pending === 0) reject(new AggregateError(errors, 'All rejected'));
      });
    });
  });
}
```

See [promise-any-polyfill.md](./promise-any-polyfill.md).

---

## 12. How to think aloud in the interview

> "Same skeleton as `Promise.all`: outer Promise, pre-allocated results array, remaining counter. The difference: both onFulfilled and onRejected write to `results[i]` — with different shapes — and both decrement the counter. The outer only ever calls `resolve`; never `reject`. Exact key names: `status: 'fulfilled' | 'rejected'`, `value` for fulfilled, `reason` for rejected. Don't deviate. Empty array → `resolve([])` immediately. Elegant alternative: build on top of `Promise.all` by mapping each input to a guaranteed-fulfilled descriptor — four lines of composition. Use case: best-effort fan-out — aggregate scores from 5 services; missing one is fine. Filter results to extract successes vs failures."

---

## 13. 60-second revision

> - **Same skeleton as `Promise.all`.** Both handlers write to `results[i]`; both decrement counter.
> - **Outer NEVER rejects.** Even if all inputs reject, descriptors are returned.
> - **Exact shape:** `{ status: 'fulfilled', value }` or `{ status: 'rejected', reason }`.
> - **Empty array** → `resolve([])` immediately.
> - **Composable:** build on top of `Promise.all` by mapping inputs to guaranteed-fulfilled descriptors.
> - **Use case:** best-effort fan-out; aggregate everything; report what worked vs failed.
> - **Family:** `all` (fail-fast), **`allSettled`** (wait-all, never reject), `race` (first either), `any` (first fulfill / AggregateError).
> - **Trap:** wrong key strings (`'resolved'` instead of `'fulfilled'`, `error` instead of `reason`).
> - **Trap:** sequential `await` version (correct result, serialized work).

---

**Related:** [promise-all-polyfill.md](./promise-all-polyfill.md) · [promise-any-polyfill.md](./promise-any-polyfill.md) · [promise-race-polyfill.md](./promise-race-polyfill.md) · [promise-pool.md](./promise-pool.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
