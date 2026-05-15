# Implement `Promise.all` polyfill

## Source
- LeetCode #2724 "Execute Asynchronous Functions in Parallel": https://leetcode.com/problems/execute-asynchronous-functions-in-parallel/
- Canonical interview problem — appears in Frontend Masters, BFE.dev, Greatfrontend, and every senior frontend/backend round.

## Why this question matters in interviews
Re-implementing `Promise.all` is the litmus test for whether you understand the promise state machine. Done right in ~15 lines, it demonstrates: (1) the `Promise` constructor and resolve/reject closure, (2) handling **non-thenables** by wrapping with `Promise.resolve`, (3) preserving **input order** in the results array via the index closure, (4) **fail-fast** behavior — first rejection rejects the outer promise and subsequent settlements are no-ops, (5) the empty-array edge case (resolve immediately with `[]`). Get any of those wrong and the interviewer marks you as "knows the API, doesn't understand the model."

## Concepts involved

### Syntax to lock in
```js
function promiseAll(promises) {
  return new Promise((resolve, reject) => {
    const results = new Array(promises.length);
    let remaining = promises.length;
    if (remaining === 0) return resolve([]);
    promises.forEach((p, i) => {
      Promise.resolve(p).then(
        (value) => {
          results[i] = value;
          if (--remaining === 0) resolve(results);
        },
        reject // fail-fast
      );
    });
  });
}
```

### Runtime / engine behavior
- The outer promise's `resolve`/`reject` are closed over by every per-promise `.then`. The promise state machine guarantees **at most one** transition — subsequent `resolve`/`reject` calls are no-ops. This is what makes fail-fast safe even though losing promises keep settling.
- `Promise.resolve(p)` is the official way to coerce a value (number, thenable, native Promise) into a real Promise. If `p` is already a Promise, it's returned as-is (no extra wrapping).
- The `.then` callbacks run as **microtasks**. Even if every input is `Promise.resolve(x)`, the outer promise resolves at least one microtask later — not synchronously.
- `--remaining === 0` is race-free because JS is single-threaded — no two `.then` callbacks run concurrently.

### Edge cases (interview traps)
1. **Empty array** — must resolve with `[]` immediately. Forgetting this leaves the outer promise pending forever (because `remaining` never decrements).
2. **Non-thenable values** — `Promise.all([1, 2, 3])` resolves with `[1, 2, 3]`. The polyfill must wrap each entry in `Promise.resolve` to handle this uniformly.
3. **Custom thenables** — `Promise.resolve({ then(r){ r(42); } })` adopts the thenable. The polyfill inherits this for free by using `Promise.resolve(p).then(...)`.
4. **Input order preserved** — results must be in the **input** order, not the **resolution** order. Use `i` from the closure, not a push counter.
5. **Fail-fast** — first rejection rejects the outer promise immediately. Later resolutions/rejections are silently dropped. **Other promises keep running** — they are not cancelled (mirrors native behaviour).
6. **Duplicate entries** — `promiseAll([p, p])` works; each gets its own `.then` and writes to its own index. Same underlying promise, two results positions.
7. **Synchronous throw in a thenable's `then`** — `Promise.resolve(thenable).then` handles it via the Promise spec; the outer rejects with the thrown value.
8. **Iterable (not array) input** — native `Promise.all` accepts any iterable. Polyfill above only accepts arrays unless you spread (`[...promises]`). Mention this gap.
9. **Mutation during iteration** — if `promises` is mutated mid-loop, native `Promise.all` uses the iterator snapshot. Polyfill uses array length; close enough for interview.

## Brute force approach
Loop sequentially: `for (const p of promises) { results.push(await p); }`. **Wrong** — this serializes the promises, defeating the entire point of `Promise.all`. A 10-task workload would take the *sum* of latencies instead of the *max*. Mention only to dismiss.

## Optimal approach
Fan out all promises at once. Each writes its result to `results[i]` on fulfillment. A shared `remaining` counter triggers `resolve(results)` when it hits zero. The outer `reject` is passed directly as each `.then`'s rejection handler — first reject wins, subsequent ones are no-ops thanks to the promise state machine.

## Solution (JavaScript)

```js
/**
 * Polyfill of Promise.all.
 * - Resolves with an array of values in INPUT order when all input promises fulfill.
 * - Rejects with the first rejection reason (fail-fast). Other promises keep running.
 * - Empty array resolves with [] immediately.
 * - Non-promise values are passed through (wrapped via Promise.resolve).
 *
 * @template T
 * @param {Array<T | PromiseLike<T>>} promises
 * @returns {Promise<T[]>}
 */
function promiseAll(promises) {
  return new Promise((resolve, reject) => {
    if (!Array.isArray(promises)) {
      return reject(new TypeError('promiseAll expects an array'));
    }
    const n = promises.length;
    if (n === 0) return resolve([]);

    const results = new Array(n);
    let remaining = n;

    for (let i = 0; i < n; i++) {
      // Promise.resolve handles: native Promise, thenable, plain value, sync throw inside thenable.then
      Promise.resolve(promises[i]).then(
        (value) => {
          results[i] = value;
          // Once remaining hits 0, fire. Subsequent calls (none, in practice) would be no-ops anyway.
          if (--remaining === 0) resolve(results);
        },
        (reason) => {
          // First rejection rejects the outer; subsequent settlements no-op via state machine.
          reject(reason);
        }
      );
    }
  });
}

// ----- LeetCode signature: input is array of () => Promise -----
function promiseAllLC(functions) {
  return promiseAll(functions.map((f) => {
    try { return f(); } catch (e) { return Promise.reject(e); }
  }));
}
```

## Step-by-step dry run

Input:
```js
const sleep = (ms, v) => new Promise((r) => setTimeout(() => r(v), ms));
promiseAll([sleep(40, 'a'), 'b', sleep(20, 'c')]).then(console.log);
```

Trace:
- `t=0`: Outer Promise constructed. `n=3`, `results=[empty,empty,empty]`, `remaining=3`.
- Loop iteration `i=0`: `Promise.resolve(sleep(40,'a'))` returns the original sleep promise. `.then` registers callbacks; pending.
- Loop `i=1`: `Promise.resolve('b')` returns a fulfilled promise with value `'b'`. `.then` schedules its fulfillment callback as a microtask.
- Loop `i=2`: `Promise.resolve(sleep(20,'c'))` registers `.then`. Pending.
- Microtask drain: callback for `'b'` runs → `results[1]='b'`, `remaining=2`.
- `t=20`: timer fires → `sleep(20,'c')` resolves. Microtask: `results[2]='c'`, `remaining=1`.
- `t=40`: timer fires → `sleep(40,'a')` resolves. Microtask: `results[0]='a'`, `remaining=0` → `resolve(['a','b','c'])`.
- `.then(console.log)` microtask → prints `['a','b','c']`.

Rejection trace:
```js
promiseAll([sleep(40, 'a'), Promise.reject(new Error('boom')), sleep(20, 'c')])
  .catch(e => console.log(e.message));
```
- `i=0`: pending. `i=1`: `Promise.resolve(rejectedP)` returns the same rejected promise. `.then` schedules rejection handler. `i=2`: pending.
- Microtask drain: rejection callback for index 1 runs → `reject(Error('boom'))`. Outer rejects.
- `t=20`: 'c' fulfills → results[2]='c', remaining=2. But the outer is already rejected — `--remaining === 0` will never be checked since it doesn't matter; even if it were, `resolve` after `reject` is a no-op.
- `t=40`: 'a' fulfills similarly. No-op.
- `.catch` microtask → prints `'boom'`.

Note: the 'a' and 'c' work happens anyway — `Promise.all` does **not** cancel siblings. If those were HTTP requests, the responses arrive and are ignored.

## Important takeaways

**Syntax to memorize**
- `new Promise((resolve, reject) => { ... })` outer.
- `Promise.resolve(promises[i]).then(onFulfilled, onRejected)` — handles all input types.
- Empty array → `resolve([])` early.
- `if (--remaining === 0) resolve(results);` — the counter pattern.

**Patterns to reuse**
- The "outer promise + N inner `.then`s writing to a results array by index + counter" pattern is exactly what `Promise.allSettled` uses (with different per-entry mapping) and what `asyncPool` collects results with.
- "Promise state machine guarantees one transition" is the same insight that makes `once(fn)` and idempotent resolvers work.

**Common mistakes**
- Pushing into `results` instead of `results[i] = value` — destroys input order.
- Awaiting in a `for` loop — serializes the work.
- Forgetting the empty-array case — outer hangs forever.
- Not wrapping with `Promise.resolve` — breaks on non-promise inputs.
- Using `results.length === promises.length` as completion check — fails because `results[i] = undefined` doesn't increment length on sparse arrays.

**Related questions**
- `Promise.race` polyfill (next file).
- `Promise.allSettled` polyfill (next-next).
- `Promise.any` polyfill — resolves with first fulfillment; rejects with `AggregateError` only if **all** reject.

## Variants

1. **`Promise.any` polyfill** — resolves on first fulfillment; rejects with `AggregateError([reasons])` only if every input rejects. Mirror image of `Promise.all`.

2. **Iterable input** — replace `for (let i=0...)` with a `for...of` and a manual index counter, or `Array.from(iter)` upfront. Native `Promise.all` accepts iterables.

3. **Concurrency-limited `Promise.all`** — combine with the asyncPool pattern: cap in-flight to N. Useful when fanning out to a rate-limited API.

4. **Object form** — `promiseAllObject({ a: p1, b: p2 })` resolves to `{ a: v1, b: v2 }`. Trivial extension; very nice in practice.

## Revision notes

> **Promise.all polyfill — 60 second recap**
> - Outer `new Promise((resolve, reject) => ...)`.
> - For each input: `Promise.resolve(p).then(v => { results[i] = v; if (--remaining===0) resolve(results); }, reject);`.
> - **Empty array** → `resolve([])` immediately (else hangs).
> - Wrap each input in `Promise.resolve` — handles plain values, thenables, native promises.
> - Preserve input order via `results[i]` (closure-captured index).
> - **Fail-fast**: first reject rejects the outer; siblings keep running but their results are discarded.
> - Promise state machine guarantees one settle — subsequent resolve/reject calls are no-ops.
> - `--remaining === 0` is race-free (single-threaded JS).
> - Family: `allSettled` (same skeleton, per-entry wrapping), `race` (first settle wins), `any` (first fulfillment wins).
> - **Trap:** pushing into results instead of indexing → wrong order. Forgetting empty case → infinite hang.
