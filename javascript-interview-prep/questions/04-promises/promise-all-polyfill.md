# Implement `Promise.all(promises)` polyfill — fail-fast fan-out

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [build-promise-from-scratch.md](./build-promise-from-scratch.md), [`concepts/promises.md`](../../concepts/promises.md)
>
> **Source:** [LeetCode 2724 — Execute Asynchronous Functions in Parallel](https://leetcode.com/problems/execute-asynchronous-functions-in-parallel/); BFE.dev; every senior frontend/backend round.

---

## 1. Problem statement

**Signature**
```ts
function promiseAll<T>(promises: Array<T | PromiseLike<T>>): Promise<T[]>;
```

**Input / Output examples**

| Input                                                            | Output                                                |
|------------------------------------------------------------------|--------------------------------------------------------|
| `promiseAll([sleep(40,'a'), 'b', sleep(20,'c')])`                | resolves with `['a', 'b', 'c']` (input order!) at t≈40 |
| `promiseAll([sleep(40,'a'), Promise.reject('boom'), sleep(20,'c')])` | rejects with `'boom'` (first reject wins; 'a' and 'c' still run, results discarded) |
| `promiseAll([])`                                                  | resolves with `[]` **immediately**                     |
| `promiseAll([Promise.resolve(1), 2, Promise.resolve(3)])`         | resolves with `[1, 2, 3]`                              |
| `promiseAll([{then(r){r(42)}}])`                                  | resolves with `[42]` (custom thenable wrapped)         |

**Constraints**
- Resolves with **input-order** array when **all** inputs fulfill.
- Rejects with the **first** rejection (fail-fast); siblings keep running but their results are discarded.
- **Empty array → resolve with `[]` immediately.** Otherwise outer hangs forever.
- Non-promise values pass through via `Promise.resolve` wrap.

---

## 2. Plain-English restatement

Fan out N tasks in parallel. Wait for all to finish; return their results in the same order you passed them in. If any one rejects, reject the whole thing with that error — but the other tasks are *not* cancelled, they just run to completion and their results are silently dropped. Empty array gets `[]` back instantly.

The most-asked promise polyfill in interviews. In ~15 lines you demonstrate the entire async fan-out idiom: outer promise + per-input `.then` + index-based results + remaining counter.

---

## 3. Why this matters in interviews

Re-implementing `Promise.all` is the litmus test for whether you understand the promise state machine. Done right in ~15 lines, it demonstrates: (1) the Promise constructor and resolve/reject closure, (2) handling **non-thenables** by wrapping with `Promise.resolve`, (3) preserving **input order** via the index closure, (4) **fail-fast** — first rejection rejects the outer; subsequent settlements are silent no-ops thanks to the state machine, (5) the empty-array edge case. Get any wrong and the interviewer marks you as "knows the API, doesn't understand the model."

---

## 4. Mental model

The outer Promise distributes its `resolve` and `reject` to N inner promises. Each inner promise's `.then(onFulfill, onReject)` writes into a shared results array at its assigned index. A remaining counter ticks down; when it hits zero, `resolve(results)` fires. Any rejection invokes the outer's `reject` directly — first one wins thanks to the state machine.

```
   new Promise((resolve, reject) => {
     const results = new Array(N);
     let remaining = N;
     
     promises.forEach((p, i) => {
       Promise.resolve(p).then(
         (v) => { results[i] = v; if (--remaining === 0) resolve(results); },
         (err) => reject(err),     // fail-fast — first reject wins
       );
     });
   });
   
   N tasks fire in parallel.
   Each writes to results[i] on success.
   Counter hits 0 → resolve.
   Any reject → outer rejects; subsequent settle calls are silent no-ops.
```

**Compared to siblings:**

| Combinator     | Settles when                              | Output                                        |
|----------------|--------------------------------------------|------------------------------------------------|
| **`all`**      | **all fulfill OR one rejects**             | array of values OR first rejection            |
| `allSettled`   | all settle                                 | array of `{status, value/reason}`              |
| `race`         | first settle (either)                      | first value OR first reason                   |
| `any`          | first fulfillment OR all rejected          | first value OR `AggregateError`               |

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `promiseAll([])` return — `[]`, `undefined`, or a pending promise?
> 2. If task #1 rejects at t=10 and task #2 fulfills at t=100, what state is the outer in at t=50? At t=200?
> 3. Why is `--remaining === 0` race-free in JavaScript without a lock?

---

## 6. Brute force — walked through

### Wrong attempt 1: sequential `await`

```js
async function bruteAll(promises) {
  const results = [];
  for (const p of promises) results.push(await p);
  return results;
}
```

**Wrong** — this serializes the work. A 10-task workload would take the *sum* of latencies instead of the *max*. Defeats the entire point of `Promise.all`. Mention only to dismiss.

### Wrong attempt 2: forget the empty-array case

```js
function promiseAll(promises) {
  return new Promise((resolve, reject) => {
    const results = new Array(promises.length);
    let remaining = promises.length;
    // (no empty check)
    promises.forEach((p, i) => {
      Promise.resolve(p).then(
        (v) => { results[i] = v; if (--remaining === 0) resolve(results); },
        reject
      );
    });
  });
}
promiseAll([]);   // BUG: outer pending forever (counter never decrements)
```

`promises.length === 0` means the loop doesn't execute → no `.then` callbacks ever run → counter stays at 0 → `resolve` never fires. Always handle this case: `if (n === 0) return resolve([]);`.

### Wrong attempt 3: push to results instead of indexing

```js
promises.forEach((p, i) => {
  Promise.resolve(p).then((v) => {
    results.push(v);                            // BUG: order = completion order, not input order
    if (results.length === promises.length) resolve(results);
  });
});
```

Two bugs. (1) Order is now non-deterministic — `[c, b, a]` if `c` finished first. (2) Using `results.length === promises.length` as the completion check fails for sparse arrays (e.g., if you pre-allocated with `new Array(n)`, the indices are "holes" and `length` already equals `n`). Always use `results[i] = v` and a separate counter.

### Wrong attempt 4: forget `Promise.resolve` wrap

```js
promises.forEach((p, i) => {
  p.then(...);     // BUG: throws if p is not a Promise
});
promiseAll([1, 2, 3]);   // TypeError: p.then is not a function
```

Non-promise values can be in the input. `Promise.resolve(p)` coerces them (and thenables) into real promises uniformly.

---

## 7. The unlocking insight

> **Outer Promise distributes its `resolve`/`reject` to N inner `.then` calls. Each inner writes to `results[i]` (index-keyed, input-order). A `remaining` counter decrements on each fulfillment; when it hits 0, `resolve(results)`. Any rejection invokes the outer's `reject` directly — first one wins thanks to the state machine, no `settled` flag needed.**

Five mechanics:

1. **Empty array → `resolve([])` immediately.** First check. Without this, the counter never hits zero and the outer hangs forever.

2. **`Promise.resolve(p)` wraps non-promises and thenables.** Lets you treat all inputs uniformly. `Promise.resolve(5)` is a pre-fulfilled promise; its `.then` fires on the next microtask. Native promises pass through unchanged. Thenables (`{then(r){...}}`) are adopted.

3. **Index-keyed results.** `results[i] = v` preserves input order regardless of completion order. The closure captures `i` per iteration.

4. **`--remaining === 0` is race-free** because JS is single-threaded. No two `.then` callbacks run concurrently; the decrement-and-check is a single atomic statement. **State this aloud — senior signal.**

5. **State machine handles "first reject wins."** The outer Promise can transition only once. After `reject(err)` is called, subsequent `resolve(results)` calls are silent no-ops. No `settled` flag needed.

**Siblings keep running.** `Promise.all` does NOT cancel the other tasks when one rejects. Their underlying work — HTTP requests, DB queries, file reads — runs to completion. The results are just discarded. For real cancellation, wrap inputs with `AbortController`.

---

## 8. Solution (annotated)

```js
function promiseAll(promises) {
  return new Promise((resolve, reject) => {
    if (!Array.isArray(promises)) {                              // step 1: validate input shape
      return reject(new TypeError('promiseAll expects an array'));
    }
    const n = promises.length;
    if (n === 0) return resolve([]);                              // step 2: empty array edge case

    const results = new Array(n);                                 // step 3: pre-allocate, index-keyed
    let remaining = n;                                            // step 4: counter

    for (let i = 0; i < n; i++) {
      Promise.resolve(promises[i]).then(                          // step 5: wrap with Promise.resolve
        (value) => {                                                //         (handles non-thenables + thenables)
          results[i] = value;                                       //         write at INPUT INDEX, not push
          if (--remaining === 0) resolve(results);                 // step 6: counter race-free in single-thread JS
        },
        (reason) => {                                              // step 7: fail-fast
          reject(reason);                                           //         state machine ensures one-settle
        }
      );
    }
  });
}

// LeetCode signature: input is Array<() => Promise>
function promiseAllLC(functions) {
  return promiseAll(
    functions.map((f) => {
      try { return f(); } catch (e) { return Promise.reject(e); }
    })
  );
}
```

**Try it yourself**

```js
const sleep = (ms, v) => new Promise((r) => setTimeout(() => r(v), ms));

await promiseAll([sleep(40, 'a'), 'b', sleep(20, 'c')]);
// ['a', 'b', 'c']  (input order, NOT [c, b, a])

await promiseAll([]);
// []  (resolves immediately)

try {
  await promiseAll([sleep(40, 'a'), Promise.reject('boom'), sleep(20, 'c')]);
} catch (e) {
  console.log(e);   // 'boom' — 'a' and 'c' still ran, results discarded
}

await promiseAll([Promise.resolve(1), 2, Promise.resolve(3)]);
// [1, 2, 3]  (non-promises coerced)
```

---

## 9. Step-by-step dry run

Input:

```js
const sleep = (ms, v) => new Promise((r) => setTimeout(() => r(v), ms));
promiseAll([sleep(40, 'a'), 'b', sleep(20, 'c')]).then(console.log);
```

Values-first trace (fulfillment path):

| Time (ms) | Event                                                | `results`         | `remaining` |
|-----------|------------------------------------------------------|--------------------|-------------|
| 0         | outer constructed; loop registers 3 `.then` handlers | `[_, _, _]`        | 3           |
| 0+µ       | `'b'` already fulfilled (Promise.resolve), microtask | `[_, 'b', _]`      | 2           |
| 20        | `sleep(20, 'c')` fulfills                            | `[_, 'b', 'c']`    | 1           |
| 40        | `sleep(40, 'a')` fulfills                            | `['a', 'b', 'c']`  | 0 → resolve |
| 40+µ      | outer's `.then(console.log)` fires                   |                    |             |

Output: `['a', 'b', 'c']` at t≈40. **Input order**, not completion order.

Rejection trace:

```js
promiseAll([sleep(40, 'a'), Promise.reject(new Error('boom')), sleep(20, 'c')])
  .catch((e) => console.log(e.message));
```

| Time | Event                                       | Outer state         | Output |
|------|----------------------------------------------|----------------------|---------|
| 0    | 3 `.then` handlers registered                 | PENDING              | —       |
| 0+µ  | `Promise.reject(...)` already rejected; rejection handler fires | PENDING → REJECTED   | (queue cb) |
| 0+2µ | outer's `.catch` microtask                    | REJECTED             | `boom`  |
| 20   | `sleep(20, 'c')` fulfills; `results[2]='c'`; decrement to 1 but no resolve | REJECTED (locked) | (no-op) |
| 40   | `sleep(40, 'a')` fulfills; `results[0]='a'`; decrement to 0 but no resolve | REJECTED | (no-op) |

The 'a' and 'c' work happens — `Promise.all` does NOT cancel siblings. If those were HTTP requests, the responses arrive (using bandwidth) and are ignored.

---

## 10. Common confusion + traps

1. **`await` in a `for` loop** — serializes the work. Defeats `Promise.all`'s purpose entirely.

2. **`results.push(v)` instead of `results[i] = v`** — destroys input order.

3. **Empty array hangs forever.** Always `if (n === 0) return resolve([])` first.

4. **Forgetting `Promise.resolve` wrap** — breaks for non-promise inputs (literal numbers, strings, thenables).

5. **Using `results.length === promises.length` as completion check** — fails when results array was pre-allocated (sparse). Use a separate counter.

6. **Trying to cancel siblings on reject** — `Promise.all` doesn't. For cancellation, you need `AbortController` integration on the inputs themselves.

7. **Iterable vs array** — native `Promise.all` accepts any iterable. Polyfill above accepts only arrays. Mention the gap; fix with `Array.from(iterable)`.

8. **Mutating `promises` during iteration** — native uses an iterator snapshot. Polyfill uses array length at call time; behavior is similar but not identical. Edge case rarely matters.

9. **Synchronous throw in a thenable's `then` method** — handled correctly because `Promise.resolve(thenable).then(...)` catches the throw and routes it to the rejection handler.

10. **Duplicate entries** — `promiseAll([p, p])` works; each `.then` is independent, each writes to its own index. Same promise, two result positions.

---

## 11. Senior follow-ups & variants

### Variant 1 — `Promise.allSettled` (never rejects)

Wrap each input's outcome in a descriptor:

```js
function promiseAllSettled(promises) {
  return promiseAll(
    promises.map((p) =>
      Promise.resolve(p).then(
        (value) => ({ status: 'fulfilled', value }),
        (reason) => ({ status: 'rejected', reason })
      )
    )
  );
}
```

Elegant composition: every input maps to a guaranteed-fulfilled descriptor, then `all` over them. See [promise-allsettled-polyfill.md](./promise-allsettled-polyfill.md).

### Variant 2 — `Promise.any` (first fulfillment wins)

Mirror image: count *rejections*, resolve on first fulfillment:

```js
function promiseAny(promises) {
  return new Promise((resolve, reject) => {
    const arr = Array.from(promises);
    if (arr.length === 0) return reject(new AggregateError([], 'All rejected'));
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

### Variant 3 — Object form (named results)

`promiseAllObject({ a: p1, b: p2 })` resolves to `{ a: v1, b: v2 }`. Trivial extension; very nice in practice:

```js
async function promiseAllObject(obj) {
  const keys = Object.keys(obj);
  const values = await promiseAll(keys.map((k) => obj[k]));
  return Object.fromEntries(keys.map((k, i) => [k, values[i]]));
}
```

### Variant 4 — Iterable input (mirror native)

```js
function promiseAll(iterable) {
  return new Promise((resolve, reject) => {
    const arr = Array.from(iterable);
    if (arr.length === 0) return resolve([]);
    const results = new Array(arr.length);
    let remaining = arr.length;
    arr.forEach((p, i) => {
      Promise.resolve(p).then(
        (v) => { results[i] = v; if (--remaining === 0) resolve(results); },
        reject
      );
    });
  });
}
```

`Array.from(iterable)` materializes any iterable upfront. Cleaner than dual-mode handling.

### Variant 5 — `Promise.all` with concurrency limit

Combine with `asyncPool` (see [promise-pool.md](./promise-pool.md)) for "fan out to a rate-limited API." `Promise.all` runs all in parallel; `asyncPool` bounds in-flight count.

### Variant 6 — Composed cancellation

For real cancellation of siblings when one rejects:

```js
async function promiseAllCancelable(promiseFactories) {
  const ac = new AbortController();
  try {
    return await promiseAll(promiseFactories.map((f) => f(ac.signal)));
  } catch (err) {
    ac.abort();
    throw err;
  }
}
```

Each input is now a factory `(signal) => Promise`. On rejection, abort the signal — all siblings can cancel their work if they honor it.

---

## 12. How to think aloud in the interview

> "Outer `new Promise((resolve, reject) => ...)`. Pre-allocate `results = new Array(n)` and `remaining = n`. Empty array → `resolve([])` immediately, otherwise the counter never hits zero. Loop: `Promise.resolve(promises[i]).then(value => { results[i] = value; if (--remaining === 0) resolve(results); }, reject);`. Use the index `i` from the closure to preserve input order — never push. `Promise.resolve` wraps non-promises and thenables uniformly. Fail-fast: pass `reject` as the second `.then` handler — first rejection wins; the state machine ensures subsequent calls are no-ops. JS is single-threaded so `--remaining` is race-free. Siblings keep running on rejection — for true cancellation, combine with AbortController."

---

## 13. 60-second revision

> - **Pattern:** outer Promise + per-input `.then(onFulfill, reject)` + index-keyed results + remaining counter.
> - **Empty array → `resolve([])` immediately.** Or it hangs.
> - **Index-keyed results** (`results[i] = v`), not `push` — preserves input order.
> - **`Promise.resolve(p)`** to coerce non-promises and thenables.
> - **Fail-fast:** pass `reject` directly; state machine handles first-wins.
> - **JS single-thread** makes `--remaining` race-free — no lock needed.
> - **Siblings keep running on reject** — not cancelled. Wrap with AbortController for that.
> - **Family:** `all` (fail-fast), `allSettled` (wait-all, never reject), `race` (first either), `any` (first fulfillment).
> - **Trap:** `await` in loop (sequential); `push` instead of index; missing empty case; no `Promise.resolve` wrap.

---

**Related:** [promise-race-polyfill.md](./promise-race-polyfill.md) · [promise-allsettled-polyfill.md](./promise-allsettled-polyfill.md) · [promise-any-polyfill.md](./promise-any-polyfill.md) · [promise-pool.md](./promise-pool.md) · [build-promise-from-scratch.md](./build-promise-from-scratch.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
