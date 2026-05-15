# Implement `addTwoPromises(p1, p2)`

## Source
- LeetCode #2723 "Add Two Promises": https://leetcode.com/problems/add-two-promises/
- A 5-minute warm-up to verify you can compose two promises without re-implementing `Promise.all`.

## Why this question matters in interviews
This problem is the canonical "do you actually understand `async`/`await`?" check. There are three valid solutions — `await` + add, `Promise.all` + destructure, manual `.then` chaining — and a senior candidate should know which is idiomatic and **why the parallel one is strictly better than sequential `await`s**. The interviewer is watching for the same mistake juniors make daily in production: `const a = await fetchA(); const b = await fetchB();` instead of `const [a, b] = await Promise.all([fetchA(), fetchB()])`. Sequential awaits double the wall-clock latency for no reason — it is one of the single most common backend perf bugs.

## Concepts involved

### Syntax to lock in
```js
async function addTwoPromises(p1, p2) {
  const [a, b] = await Promise.all([p1, p2]);
  return a + b;
}
```

### Runtime / engine behavior
- An `async` function **always** returns a Promise. `return x` inside an async function is equivalent to `return Promise.resolve(x)`.
- `await p` suspends the async function until `p` settles. The remainder of the function is scheduled as a microtask on `p`'s resolution.
- `Promise.all([p1, p2])` does **not** start the promises — they're already running. It only waits for both to settle.
- If `p1` rejects, `Promise.all` rejects immediately with `p1`'s reason. `p2` keeps running but its result is ignored (and its rejection, if any, becomes an unhandled rejection unless attached elsewhere).

### Edge cases (interview traps)
1. **Sequential vs parallel** — `const a = await p1; const b = await p2;` adds nothing if `p1` and `p2` are already-running promises (they resolve in parallel anyway), but the *moment* you replace them with **factories** (`await fetchA(); await fetchB();`), you've serialized them. The LeetCode signature takes already-running promises, so both styles produce the same timing here — but you must articulate the difference.
2. **One rejects** — `Promise.all` rejects fast. If you use sequential awaits, you must `try/catch` each one or the second never runs.
3. **Non-numeric resolution** — if `p1` resolves to `"5"` and `p2` to `3`, `a + b` becomes `"53"`. Cast or validate if the contract requires numbers.
4. **`p1 === p2`** — passing the same promise twice works fine; it resolves once and both destructure positions get the same value.
5. **Returning a promise from an async function** — `return Promise.resolve(5)` and `return 5` are equivalent inside `async`; the engine flattens it. Don't write `return Promise.resolve(...)` — redundant.
6. **Awaiting non-thenables** — `await 5` is legal: it wraps the value in `Promise.resolve` and resolves on the next microtask. Costs one microtask hop.

## Brute force approach
Two sequential awaits:
```js
async function addTwoPromises(p1, p2) {
  const a = await p1;
  const b = await p2;
  return a + b;
}
```
This **works** and produces identical timing here because both promises are already in-flight when the function is called. But it's bad muscle memory — switch to factories and you've doubled the latency. Mention this distinction explicitly.

## Optimal approach
`Promise.all` + destructure. One microtask hop, parallel by construction, fails fast.

## Solution (JavaScript)

```js
/**
 * Returns a Promise that resolves to the sum of two resolved promises.
 * @param {Promise<number>} p1
 * @param {Promise<number>} p2
 * @returns {Promise<number>}
 */
async function addTwoPromises(p1, p2) {
  const [a, b] = await Promise.all([p1, p2]);
  return a + b;
}

// Equivalent without async/await (interviewer may ask):
function addTwoPromisesThen(p1, p2) {
  return Promise.all([p1, p2]).then(([a, b]) => a + b);
}
```

## Step-by-step dry run

Input:
```js
const p1 = new Promise((r) => setTimeout(() => r(2), 20));
const p2 = new Promise((r) => setTimeout(() => r(5), 60));
addTwoPromises(p1, p2).then(console.log);
```

Trace:
- `t=0`: `p1` and `p2` constructed; both `setTimeout`s scheduled. `addTwoPromises(p1, p2)` invoked — async function starts, hits `await Promise.all([p1, p2])`, suspends. The async function's outer promise is pending.
- `t=20`: `p1`'s timer fires → resolve(2). Internal `Promise.all` aggregator notes p1 settled, count = 1/2; not done yet.
- `t=60`: `p2`'s timer fires → resolve(5). Aggregator notes p2 settled, count = 2/2; resolves the all-promise with `[2, 5]`.
- Microtask drain: `addTwoPromises` resumes, destructures `[a=2, b=5]`, returns `7`. The async function's outer promise resolves with `7`.
- Microtask drain: `.then(console.log)` runs → prints `7`.

Total wall time: ~60ms (the slower of the two), not 80ms. That's the parallelism win.

Rejection trace:
```js
const p1 = Promise.reject(new Error('boom'));
const p2 = sleep(1000).then(() => 5);
addTwoPromises(p1, p2).catch(e => console.log(e.message));
```
- `Promise.all` rejects immediately with `Error('boom')`. The async function's `await` throws, the function's returned promise rejects with the same error. `p2` keeps running for ~1s, its eventual `5` is discarded. No unhandled rejection because we have `.catch`.

## Important takeaways

**Syntax to memorize**
- `const [a, b] = await Promise.all([p1, p2]);` — the destructure makes the parallel intent obvious.
- `async` function's return value is **auto-wrapped** in `Promise.resolve` — don't double-wrap.

**Patterns to reuse**
- "Parallel-fan-out, await-once" is the bread-and-butter pattern for any I/O-heavy backend handler: `await Promise.all([db.user(id), db.orders(id), cache.permissions(id)])`.
- For independent calls that can tolerate partial failure, use `Promise.allSettled` instead. For "first one wins," `Promise.race`. Pick the right tool — see polyfill questions in this bucket.

**Common mistakes**
- Sequential `await` when the calls are independent. Doubles latency.
- Wrapping returns in `Promise.resolve` inside async functions.
- Forgetting that `Promise.all` is fail-fast — if you need all results regardless, use `Promise.allSettled`.
- Mutating shared state inside the awaited expressions and relying on order — order of resolution is unpredictable.

**Related questions**
- `Promise.all` polyfill (next file).
- `addNPromises(arr)` — generalize to N promises with `arr.reduce((s, x) => s + x, 0)` after the `all`.

## Variants

1. **N-promise sum** — `async function sumPromises(arr) { return (await Promise.all(arr)).reduce((s, x) => s + x, 0); }`. Same idea; tests if you can scale the pattern.

2. **Partial failure tolerance** — "sum the resolved values, treat rejections as 0." Use `Promise.allSettled` and filter.
   ```js
   const settled = await Promise.allSettled(arr);
   return settled.reduce((s, r) => s + (r.status === 'fulfilled' ? r.value : 0), 0);
   ```

3. **Strict-number variant** — reject if either value is not a finite number. Tests defensive coding posture.

## Revision notes

> **addTwoPromises — 60 second recap**
> - `const [a, b] = await Promise.all([p1, p2]); return a + b;` — one line.
> - `async` returns a Promise; `return x` ≡ `return Promise.resolve(x)`.
> - **Parallel** by construction; sequential `await`s would serialize *factory calls*, not pre-existing promises.
> - `Promise.all` is **fail-fast** — first reject wins; other promises keep running but their results are discarded.
> - Family: `Promise.all` for "all or nothing", `allSettled` for "tell me about each", `race` for "first wins", `any` for "first success."
> - **Trap:** writing `const a = await p1; const b = await p2;` and forgetting that with *factory functions* this serializes them.
> - String coercion bites: `"5" + 3 === "53"`. Validate types if the contract is numeric.
