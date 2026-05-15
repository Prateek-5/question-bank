# Implement `Promise.allSettled` polyfill

## Source
- Canonical interview problem (added to the spec in ES2020).
- MDN: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/allSettled

## Why this question matters in interviews
`Promise.allSettled` is the "I need all results regardless of failure" primitive — the right tool for **partial-failure-tolerant** backend fan-out (e.g., aggregate scores from 5 microservices; missing one is fine). Implementing it is structurally identical to `Promise.all`, with one crucial difference: **it never rejects**. The polyfill demonstrates whether you can articulate that distinction (interviewers love watching candidates struggle to remember which one rejects). It also tests the `{ status, value | reason }` shape exactly — `'fulfilled'` / `'rejected'`, not `'resolved'` / `'errored'` or anything else. Wrong key names = an obvious "haven't used this in a while" signal.

## Concepts involved

### Syntax to lock in
```js
function promiseAllSettled(promises) {
  return new Promise((resolve) => {
    const results = new Array(promises.length);
    let remaining = promises.length;
    if (remaining === 0) return resolve([]);
    promises.forEach((p, i) => {
      Promise.resolve(p).then(
        (value)  => { results[i] = { status: 'fulfilled', value };  if (--remaining === 0) resolve(results); },
        (reason) => { results[i] = { status: 'rejected',  reason }; if (--remaining === 0) resolve(results); }
      );
    });
  });
}
```

### Runtime / engine behavior
- **No `reject`** path exists in the outer Promise. The outer can only resolve, never reject. (You could omit `reject` from the constructor signature; including it is fine and harmless.)
- The output is an array of `{ status: 'fulfilled', value }` or `{ status: 'rejected', reason }` objects — **always in input order**, preserved via `results[i]`.
- Same microtask + counter pattern as `Promise.all`. Same single-threadedness guarantee for `--remaining`.
- `Promise.resolve(p)` coerces non-promises; a non-promise `5` becomes a fulfilled result with `value: 5`.

### Edge cases (interview traps)
1. **Empty array** — resolves with `[]` immediately. Don't forget; otherwise outer hangs (counter never decrements).
2. **Output shape exactness** — `{ status: 'fulfilled', value }` and `{ status: 'rejected', reason }`. **Not** `'resolved'`, not `error`, not `data`. Match the spec.
3. **Never rejects** — even if every input rejects, the outer resolves with an array of `{ status: 'rejected' }` objects. This is the entire point.
4. **Non-thenable inputs** — wrap via `Promise.resolve`. A plain `5` becomes `{ status: 'fulfilled', value: 5 }`.
5. **Synchronous throw in a thenable** — `Promise.resolve(thenable).then` routes it to the rejection handler → `{ status: 'rejected', reason }`.
6. **No fail-fast** — every input always runs to settlement. This is desirable for "aggregate everything" use cases but bad if early termination would save resources. For early termination on first reject, use `Promise.all` instead.
7. **Input order preserved** — same `results[i]` pattern.
8. **Iterable support** — native accepts any iterable; polyfill above expects array. Mention the gap.

## Brute force approach
Loop and `await` sequentially with try/catch:
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
**Correct** result shape, but **serializes** the work — totally defeats the parallelism. Mention as the wrong path, then implement the parallel polyfill.

## Optimal approach
Outer Promise + fan-out loop + per-promise `.then` writing to `results[i]` + remaining counter. The rejection handler also writes (with a different shape) and decrements — no fail-fast.

## Solution (JavaScript)

```js
/**
 * Polyfill of Promise.allSettled.
 * - Resolves with [{status:'fulfilled',value} | {status:'rejected',reason}] in INPUT order.
 * - Never rejects. Waits for every input to settle.
 * - Empty array resolves with [] immediately.
 *
 * @template T
 * @param {Array<T | PromiseLike<T>>} promises
 * @returns {Promise<Array<{ status: 'fulfilled', value: T } | { status: 'rejected', reason: any }>>}
 */
function promiseAllSettled(promises) {
  return new Promise((resolve) => {
    if (!Array.isArray(promises)) {
      // Mirror native: TypeError before any work. Wrap so the polyfill is still a Promise.
      return resolve(Promise.reject(new TypeError('promiseAllSettled expects an array')));
    }
    const n = promises.length;
    if (n === 0) return resolve([]);

    const results = new Array(n);
    let remaining = n;

    const settle = (i, descriptor) => {
      results[i] = descriptor;
      if (--remaining === 0) resolve(results);
    };

    for (let i = 0; i < n; i++) {
      Promise.resolve(promises[i]).then(
        (value)  => settle(i, { status: 'fulfilled', value }),
        (reason) => settle(i, { status: 'rejected', reason })
      );
    }
  });
}
```

### Pattern: build `allSettled` from `all`

```js
const promiseAllSettledFromAll = (promises) =>
  promiseAll(
    promises.map((p) =>
      Promise.resolve(p).then(
        (value)  => ({ status: 'fulfilled', value }),
        (reason) => ({ status: 'rejected',  reason })
      )
    )
  );
```
This is elegant — wrap each input to a guaranteed-fulfilled descriptor, then `Promise.all` over the wraps. Worth showing to demonstrate composability.

## Step-by-step dry run

Input:
```js
const sleep = (ms, v) => new Promise((r) => setTimeout(() => r(v), ms));
const fail  = (ms, e) => new Promise((_, j) => setTimeout(() => j(e), ms));

promiseAllSettled([
  sleep(50, 'a'),
  fail(20, new Error('boom')),
  'plain',
]).then(console.log);
```

Trace:
- `t=0`: outer constructed. `n=3`, `results=[empty,empty,empty]`, `remaining=3`. Loop attaches `.then(resolve, reject)`-shaped handlers to each input.
  - `i=0`: pending until t=50.
  - `i=1`: pending until t=20.
  - `i=2`: `Promise.resolve('plain')` is already fulfilled — its fulfillment microtask is scheduled.
- Microtask drain: `i=2` fulfillment → `results[2] = { status: 'fulfilled', value: 'plain' }`, `remaining=2`.
- `t=20`: rejection timer fires for `i=1`. Microtask: rejection handler → `results[1] = { status: 'rejected', reason: Error('boom') }`, `remaining=1`.
- `t=50`: fulfillment timer fires for `i=0`. Microtask: → `results[0] = { status: 'fulfilled', value: 'a' }`, `remaining=0` → `resolve(results)`.
- `.then(console.log)` microtask prints:
  ```
  [
    { status: 'fulfilled', value: 'a' },
    { status: 'rejected', reason: Error('boom') },
    { status: 'fulfilled', value: 'plain' },
  ]
  ```

Key observation: result order is `[a, boom, plain]` (input order), not `[plain, boom, a]` (completion order). This is the whole point of indexing by `i`.

## Important takeaways

**Syntax to memorize**
- `{ status: 'fulfilled', value }` and `{ status: 'rejected', reason }` — **exact** key names.
- Never call `reject` on the outer — even include only `resolve` in the constructor signature if you want to make it visually obvious.
- Same `results[i]` + `--remaining` counter pattern as `Promise.all`.

**Patterns to reuse**
- "Map each promise to a guaranteed-fulfilled descriptor, then `Promise.all` over the descriptors" is a beautiful 4-line composition. Show it.
- Same skeleton produces `Promise.any`'s polyfill (flipped: count rejections, resolve on first fulfillment).

**Common mistakes**
- Wrong status strings (`'resolved'`, `'error'`, `'ok'`). The spec is `'fulfilled'` / `'rejected'`.
- Wrong value keys (`error` instead of `reason`, `result` instead of `value`). Match the spec.
- Forgetting the empty-array case.
- Submitting the sequential `await` version (functionally correct, but serializes the work).
- Forgetting `Promise.resolve` wrap on inputs — breaks for plain values.

**Related questions**
- `Promise.all` polyfill (same skeleton, fail-fast).
- `Promise.any` polyfill — first fulfillment wins; only rejects (with `AggregateError`) if **all** reject.
- `Promise.race` polyfill — first settle wins, either way.

## Variants

1. **Result filter** — return only `.filter(r => r.status === 'fulfilled').map(r => r.value)`. The common "best-effort fan-out" pattern: aggregate what worked, log what didn't.

2. **`Promise.any` polyfill** — given the `allSettled` polyfill, build `any` as: settle with first fulfilled value; if all rejected, reject with `new AggregateError(reasons, 'All promises rejected')`. Use a counter mirroring `Promise.all`.

3. **Tagged result map** — `allSettledObject({ a: p1, b: p2 })` returns `{ a: {status,...}, b: {status,...} }`. Slight tweak; nice in practice.

4. **`allSettled` with concurrency limit** — combine with the `asyncPool` pattern: cap in-flight, still collect all results regardless of outcome.

## Revision notes

> **Promise.allSettled polyfill — 60 second recap**
> - Same skeleton as `Promise.all` but **never rejects**. Both fulfillment and rejection write to `results[i]` with different shapes.
> - Shape: `{ status: 'fulfilled', value }` or `{ status: 'rejected', reason }`. Exact key names matter.
> - Empty array → resolve `[]` immediately.
> - Counter: `if (--remaining === 0) resolve(results)`.
> - Composable: build from `Promise.all` by mapping each input to a "wrapped to always fulfill with descriptor" promise.
> - Family: `all` (fail-fast), `allSettled` (wait-all, never reject), `race` (first settle), `any` (first fulfillment).
> - **When to use:** partial-failure tolerance, aggregate dashboards, "tell me what worked and what didn't".
> - **Trap:** wrong status string (`'resolved'`). **Trap:** wrong reason key (`error`).
