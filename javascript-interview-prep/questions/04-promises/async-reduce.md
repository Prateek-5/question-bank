# Implement `asyncReduce(arr, fn, init)`

## Source
- Backend pipeline interview standard — paired with `asyncMap` / `asyncFilter`.
- Used heavily in real Node backends: aggregate paginated API results, accumulate stream chunks, build a config from layered async sources.
- Variants on BFE.dev and InterviewKickstart sets.

## Why this question matters in interviews
Unlike map/filter, `reduce` is **inherently sequential** — each step depends on the previous accumulator. You **cannot parallelize** a true reduce (unless the operation is commutative and associative). Senior interviewers ask this to test whether you (a) recognize the sequential constraint, (b) write the `for...of` + `await` pattern cleanly, and (c) understand the **chained-promise alternative** using `arr.reduce((acc, x) => acc.then(...))` — which is equivalent but a great test of promise-chain literacy.

## Concepts involved

### Syntax to lock in
```js
const total = await asyncReduce(
  ['user:1', 'user:2', 'user:3'],
  async (sum, key) => sum + (await fetchScore(key)),
  0,
);
```

### Runtime / engine behavior
- Each iteration **awaits the previous accumulator** before computing the next. Sequential by definition.
- Two equivalent shapes: `for...of` + `await` (imperative), or `arr.reduce((accP, x) => accP.then(acc => fn(acc, x)), Promise.resolve(init))` (functional chain).
- The functional version builds a long promise chain at iteration time, then drains it. Stack depth is bounded because each `.then` is a microtask.
- Memory: O(1) extra beyond the accumulator (vs `Promise.all` which holds O(N) pending promises).

### Edge cases (interview traps)
1. **No init value** — native `reduce` uses `arr[0]` as initial accumulator and starts from index 1. Same convention applies; throw on empty array with no init.
2. **Error propagation** — first throw / rejection aborts the chain. Subsequent items not processed. (Same as native `reduce` with sync throw.)
3. **Sync `fn`** — should still work. `await` on a non-promise value resolves to it immediately.
4. **`init` is a Promise** — wrap with `await Promise.resolve(init)` at start to normalize.
5. **Passing `index` and `arr` to `fn`** — native `reduce(fn(acc, val, i, arr))`. Match the signature for drop-in compatibility.
6. **No parallelism possible** — interviewer trap: "can you parallelize this?" Answer: **only if** `fn` is associative AND commutative (e.g., sum, max). Otherwise no. For associative-only, you can do a tree-reduce, but commit upfront that you're changing semantics.

## Brute force approach
Brute force *is* the optimal approach here — `for...of` + `await`. The trick is **recognizing** that brute force is correct and resisting the temptation to "parallelize" with `Promise.all`. If `fn` is `(acc, x) => acc + await fetch(x)`, parallel `Promise.all` would lose the running accumulator.

## Optimal approach
Imperative form is the clearest and most efficient. `let acc = init; for (const x of arr) acc = await fn(acc, x); return acc;`. Memory O(1), time O(N × per-item latency).

The promise-chain form is equivalent but harder to debug — useful to know exists.

## Solution (JavaScript)

```js
// Imperative — recommended
async function asyncReduce(arr, fn, init) {
  // Mirror native reduce: if no init and empty array → throw.
  if (arguments.length < 3) {
    if (arr.length === 0) {
      throw new TypeError('Reduce of empty array with no initial value');
    }
    let acc = arr[0];
    for (let i = 1; i < arr.length; i++) {
      acc = await fn(acc, arr[i], i, arr);
    }
    return acc;
  }

  let acc = await init; // normalize if init is a promise
  for (let i = 0; i < arr.length; i++) {
    acc = await fn(acc, arr[i], i, arr);
  }
  return acc;
}

// Equivalent: functional promise-chain form (mention only)
function asyncReduceChain(arr, fn, init) {
  return arr.reduce(
    (accP, x, i, src) => accP.then((acc) => fn(acc, x, i, src)),
    Promise.resolve(init),
  );
}
```

## Step-by-step dry run

Input:
```js
const fetchScore = async (key) => new Promise(r => setTimeout(() => r(key.length), 20));
const keys = ['a', 'bb', 'ccc'];
const total = await asyncReduce(keys, async (sum, k) => sum + (await fetchScore(k)), 0);
```

Trace:
- **t=0** — `acc = await 0` → `acc = 0`. Enter loop.
- **t=0** — i=0: `await fn(0, 'a', 0, keys)`. Inside fn: `await fetchScore('a')` → resolves to 1 at t=20. `acc = 0 + 1 = 1`.
- **t=20** — i=1: `await fn(1, 'bb', 1, keys)`. `await fetchScore('bb')` → 2 at t=40. `acc = 3`.
- **t=40** — i=2: `await fn(3, 'ccc', 2, keys)`. `await fetchScore('ccc')` → 3 at t=60. `acc = 6`.
- **t=60** — loop exits. Return 6.

Output: `total = 6`. Total time ≈ 60ms (sequential, 3 × 20ms).

Note that even if you **could** parallelize the `fetchScore` calls (since they're independent and commutative), you'd need a different shape: `(await Promise.all(keys.map(fetchScore))).reduce((s, x) => s + x, 0)` — but that's no longer a `reduce`-shaped problem, it's a `map → reduce` pipeline.

## Important takeaways

**Syntax to memorize**
- `let acc = await init` to normalize promise inits.
- `for (let i = 0; i < arr.length; i++) acc = await fn(acc, arr[i], i, arr);` — full native-compatible signature.
- Empty-array-no-init guard: throw `TypeError`.

**Patterns to reuse**
- "Sequential accumulator over async sources" is the universal **pipeline reducer** — same shape used in: koa middleware (`reduce` over middleware array), redux-saga effects, ETL transformers, building HTTP responses from chained sub-fetches.
- The functional `arr.reduce((accP, x) => accP.then(...))` form is the canonical **promise-chain builder** pattern.

**Common mistakes**
- Trying to parallelize — kills the running accumulator semantics.
- Using `arr.reduce` with an async `fn` and forgetting that the accumulator becomes a Promise — leads to `[object Promise]` in output.
- Not awaiting `init` — breaks if a caller passes a promise as starting value.
- Forgetting the empty-array-no-init case — native `reduce` throws, your version should too.
- Mutating `acc` in place rather than returning a new one — works but kills functional reasoning and breaks if `acc` is shared.

**Related questions**
- `asyncMap` (parallelizable)
- `asyncFilter` (parallelizable predicates)
- Koa-style middleware composition (a thinly-disguised asyncReduce over middleware functions)

## Variants

1. **`asyncReduceRight`** — same as above but iterate backward. Useful for right-associative ops (function composition).
2. **Parallel reduce for associative+commutative ops** — tree-reduce: pair up adjacent items, sum in parallel, halve the array, repeat. Only valid if `fn` is associative and commutative (sum, max, set-union). Mention as senior signal.
3. **Reduce with early-exit (short-circuit)** — pass a sentinel from `fn` that aborts the reduction. Useful for "find first invalid item" style accumulators.
4. **Compose async middleware** — `asyncReduce(middlewares, (next, mw) => () => mw(req, next), finalHandler)`. Real-world pattern.

## Revision notes

> **asyncReduce — 60 second recap**
> - **Sequential by definition** — each step depends on the previous accumulator.
> - Shape: `let acc = await init; for (...) acc = await fn(acc, x, i, arr); return acc;`.
> - Empty array + no init → throw TypeError (match native).
> - Functional alt: `arr.reduce((accP, x) => accP.then(acc => fn(acc, x)), Promise.resolve(init))`.
> - **Cannot be parallelized** unless `fn` is associative AND commutative (then use tree-reduce).
> - **Trap:** trying `Promise.all` over reduce — silently produces `[object Promise]` and ignores the accumulator.
