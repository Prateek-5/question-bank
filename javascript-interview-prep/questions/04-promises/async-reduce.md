# Implement `asyncReduce(arr, fn, init)` — sequential accumulator over async

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [sequential-vs-parallel-async-map.md](./sequential-vs-parallel-async-map.md), [build-promise-from-scratch.md](./build-promise-from-scratch.md)
>
> **Source:** Backend pipeline interview standard.

---

## 1. Problem statement

**Signature**
```ts
function asyncReduce<T, U>(
  arr: T[],
  fn: (acc: U, item: T, index: number, array: T[]) => Promise<U>,
  init: U
): Promise<U>;
```

**Input / Output examples**

| Setup                                                                       | Result                          |
|------------------------------------------------------------------------------|----------------------------------|
| `asyncReduce(['a','bb','ccc'], async (s,k) => s + (await fetchLen(k)), 0)`  | `6` (1+2+3)                     |
| Empty array, no init                                                         | `TypeError` (match native)      |
| Empty array, with init                                                       | returns `init`                  |
| `init` is a Promise                                                          | `await init` first              |
| `fn` throws/rejects mid-iteration                                            | aborts; rejection propagates    |
| **Cannot parallelize** unless `fn` is associative + commutative              | sequential by construction      |

**Constraints**
- **Sequential by definition** — each step depends on the previous accumulator.
- Match native `reduce` signature: `fn(acc, item, index, array)`.
- Empty array + no init → throw `TypeError`.
- Memory O(1) beyond the accumulator.

---

## 2. Plain-English restatement

Walk through the array, calling `fn(acc, item)` once per element, awaiting each call. The result becomes the next accumulator. After the last item, return the final accumulator. The crucial thing: **you cannot parallelize this** — each step needs the previous step's result. Unlike `asyncMap` and `asyncFilter`, parallelization here would lose the running accumulator.

---

## 3. Why this matters in interviews

Unlike map/filter, `reduce` is **inherently sequential** — each step depends on the previous accumulator. You **cannot parallelize** a true reduce (unless the operation is commutative and associative). Senior interviewers ask this to test whether you (a) recognize the sequential constraint, (b) write the `for...of` + `await` pattern cleanly, and (c) understand the **chained-promise alternative** using `arr.reduce((acc, x) => acc.then(...))` — which is equivalent but a great test of promise-chain literacy.

---

## 4. Mental model

```
   asyncReduce(['a', 'bb', 'ccc'], (s, k) => s + len(k), 0):
   
   acc = 0
        │
        ├── await fn(0, 'a')   → 0 + 1 = 1
        │
        ├── await fn(1, 'bb')  → 1 + 2 = 3
        │
        └── await fn(3, 'ccc') → 3 + 3 = 6
   
   return 6
   
   Total time = Σ per-item latency. Cannot parallelize.
```

**The sequential constraint** is fundamental. Each `fn` call needs the accumulator from the previous call. If you tried `Promise.all(arr.map(fn))`, each `fn` would get the *initial* accumulator — not the running one. The output would be N independent transformations, not a fold.

**Two equivalent shapes:**

```
   Imperative (recommended):
     let acc = await init;
     for (let i = 0; i < arr.length; i++) {
       acc = await fn(acc, arr[i], i, arr);
     }
     return acc;
   
   Functional (promise-chain):
     return arr.reduce(
       (accP, x, i, src) => accP.then(acc => fn(acc, x, i, src)),
       Promise.resolve(init)
     );
```

Both produce identical results. The imperative is easier to debug; the functional is a great signal of promise-chain literacy.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Can you parallelize an async reduce? When (and only when)?
> 2. What does `[].reduce(fn)` (no init) return — `undefined`, `null`, or `TypeError`?
> 3. If you accidentally do `arr.reduce(async fn, init)` (sync `reduce` with async `fn`), what's in the result?

---

## 6. Brute force — walked through

### Wrong attempt 1: try to parallelize

```js
async function asyncReduceWrong(arr, fn, init) {
  const results = await Promise.all(arr.map((x) => fn(init, x)));   // BUG
  return results.reduce((s, x) => s + x, init);   // synchronously sum
}
```

Each `fn(init, x)` runs with the **initial** accumulator — not the running one. You've turned a fold into N independent transformations. For an associative+commutative `fn` like sum, this can accidentally work for *that* `fn`, but it's no longer `reduce` semantics — it's `map + sync reduce`. Not a general fix.

### Wrong attempt 2: native `reduce` with async `fn`

```js
const total = ['a','bb','ccc'].reduce(async (sum, k) => {
  return sum + await fetchLen(k);
}, 0);
// total === Promise { '[object Promise]3' }
```

`reduce` doesn't await the callback. The accumulator becomes a Promise. The next iteration adds a number to a Promise — implicit string concat. Output is `'[object Promise]3'` or similar garbage. Junior bug.

### Wrong attempt 3: forget the empty-array-no-init case

```js
async function asyncReduce(arr, fn, init) {
  let acc = init;   // BUG: if init is undefined and arr is empty, returns undefined silently
  for (const x of arr) acc = await fn(acc, x);
  return acc;
}
asyncReduce([], (s, x) => s + x);   // returns undefined
```

Native `reduce` throws `TypeError: Reduce of empty array with no initial value`. Match the convention.

---

## 7. The unlocking insight

> **Sequential `for` loop with `await` on each iteration. The accumulator is updated in place after each await. Match native `reduce` signature: `fn(acc, item, index, array)`. Empty array + no init → throw `TypeError`.**

The shape:

```js
async function asyncReduce(arr, fn, init) {
  if (arguments.length < 3) {
    if (arr.length === 0) throw new TypeError('Reduce of empty array with no initial value');
    let acc = arr[0];
    for (let i = 1; i < arr.length; i++) {
      acc = await fn(acc, arr[i], i, arr);
    }
    return acc;
  }
  let acc = await init;   // normalize promise inits
  for (let i = 0; i < arr.length; i++) {
    acc = await fn(acc, arr[i], i, arr);
  }
  return acc;
}
```

Three properties:

1. **Sequential by construction.** Each `await` happens before the next iteration. Can't be parallelized without changing semantics.

2. **Memory O(1)** beyond the accumulator. No N-sized pending promise array (unlike parallel `asyncMap`).

3. **Match native `reduce` signature** — `(acc, item, index, array)` and the empty-array-no-init throw.

**The functional promise-chain alternative** is worth knowing but rarely used:

```js
function asyncReduceChain(arr, fn, init) {
  return arr.reduce(
    (accP, x, i, src) => accP.then((acc) => fn(acc, x, i, src)),
    Promise.resolve(init)
  );
}
```

Same result; harder to debug; cleaner for FP-style codebases.

**When can you parallelize?** Only when `fn` is **associative AND commutative** (sum, max, min, set union, multiplication). Then you can do a *tree-reduce*: pair up items, reduce in parallel, halve, repeat. Useful for hot paths over big arrays — but it's no longer a `reduce`, it's an `aggregateAssoc` or similar. Explicitly change the contract.

---

## 8. Solution (annotated)

```js
async function asyncReduce(arr, fn, init) {
  // Mirror native reduce: empty array + no init → throw
  if (arguments.length < 3) {                                  // step 1: no init provided
    if (arr.length === 0) {
      throw new TypeError('Reduce of empty array with no initial value');
    }
    let acc = arr[0];                                           // step 2: use arr[0] as init
    for (let i = 1; i < arr.length; i++) {                      // step 3: start from index 1
      acc = await fn(acc, arr[i], i, arr);
    }
    return acc;
  }

  let acc = await init;                                         // step 4: normalize promise init
  for (let i = 0; i < arr.length; i++) {                        // step 5: walk all items
    acc = await fn(acc, arr[i], i, arr);                        //         each step awaits previous
  }
  return acc;
}

// Equivalent: functional promise-chain
function asyncReduceChain(arr, fn, init) {
  return arr.reduce(
    (accP, x, i, src) => accP.then((acc) => fn(acc, x, i, src)),
    Promise.resolve(init)
  );
}

// Variant: tree-reduce (parallelizable for associative + commutative ops)
async function asyncReduceTree(arr, fn) {
  if (arr.length === 0) throw new TypeError('Empty array');
  let current = arr;
  while (current.length > 1) {
    const next = [];
    for (let i = 0; i < current.length; i += 2) {
      if (i + 1 < current.length) {
        next.push(fn(current[i], current[i + 1]));
      } else {
        next.push(current[i]);
      }
    }
    current = await Promise.all(next);
  }
  return current[0];
}
```

**Try it yourself**

```js
const fetchLen = async (k) => new Promise((r) => setTimeout(() => r(k.length), 20));

// Standard fold
const total = await asyncReduce(
  ['a', 'bb', 'ccc'],
  async (sum, k) => sum + (await fetchLen(k)),
  0
);
console.log(total);   // 6

// Layered config build
const config = await asyncReduce(
  ['/etc/default.json', '/etc/override.json', '~/.config.json'],
  async (cfg, path) => ({ ...cfg, ...(await loadJson(path)) }),
  {}
);

// Tree-reduce — only valid for sum
const max = await asyncReduceTree([1, 5, 3, 8, 2], async (a, b) => Math.max(a, b));   // 8
// O(log N) wall-clock instead of O(N) — but only because max is associative AND commutative
```

---

## 9. Step-by-step dry run

Input:

```js
const fetchLen = async (k) => sleep(20, k.length);
const keys = ['a', 'bb', 'ccc'];
await asyncReduce(keys, async (s, k) => s + (await fetchLen(k)), 0);
```

Values-first trace:

| Time (ms) | Step                                          | `acc` | Returned                |
|-----------|-----------------------------------------------|--------|--------------------------|
| 0         | `acc = await 0` → `0`; enter loop             | 0      | —                        |
| 0         | i=0: `await fn(0, 'a', 0, keys)` — inside fn: `await fetchLen('a')` → 1 at t=20 | — | — |
| 20        | fn returns `0 + 1 = 1`; `acc = 1`             | 1      | —                        |
| 20        | i=1: `await fn(1, 'bb', 1, keys)` — `await fetchLen('bb')` → 2 at t=40 | — | — |
| 40        | fn returns `1 + 2 = 3`; `acc = 3`             | 3      | —                        |
| 40        | i=2: `await fn(3, 'ccc', 2, keys)` — `await fetchLen('ccc')` → 3 at t=60 | — | — |
| 60        | fn returns `3 + 3 = 6`; `acc = 6`             | 6      | —                        |
| 60        | loop exits, return 6                          | 6      | `6`                      |

**Total time ≈ 60ms** (sequential, 3 × 20ms). Cannot be made faster without changing semantics.

For comparison, **map + sync-reduce** (works only for sum-like operations):

```js
const total = (await Promise.all(keys.map(fetchLen))).reduce((s, x) => s + x, 0);
// 6, but at t≈20ms (parallel) — NOT a reduce, it's a map then sync fold
```

---

## 10. Common confusion + traps

1. **Trying to parallelize.** Kills the running-accumulator semantics. Only valid for associative+commutative `fn`.

2. **Native `arr.reduce(async fn, init)`.** `reduce` doesn't await. Accumulator becomes a Promise; subsequent iterations add to it → `[object Promise]` in output.

3. **Forgetting `await init`.** Breaks if a caller passes a promise as starting value.

4. **Forgetting the empty-array-no-init case.** Native throws `TypeError`; your version should too.

5. **Mutating `acc` in place.** Works but kills functional reasoning and breaks if `acc` is shared. Return a new accumulator each step.

6. **Wrong signature.** Native is `fn(acc, item, index, array)`. Don't drop the trailing args.

7. **`init` as a primitive vs reference.** Be aware that `acc = []` then `acc.push(x)` mutates the same array. For pure FP, return a new array: `acc = [...acc, x]`.

---

## 11. Senior follow-ups & variants

### Variant 1 — Tree-reduce for parallelizable ops

```js
async function asyncReduceTree(arr, fn) {
  // Only valid if fn is associative AND commutative
  let current = arr;
  while (current.length > 1) {
    const next = [];
    for (let i = 0; i < current.length; i += 2) {
      next.push(i + 1 < current.length ? fn(current[i], current[i + 1]) : current[i]);
    }
    current = await Promise.all(next);
  }
  return current[0];
}
```

O(log N) wall-clock for big arrays. **Only valid for sum, max, min, set union, etc.** Explicitly change the contract.

### Variant 2 — Compose async middleware (koa-style)

```js
function composeMiddleware(middlewares, ctx) {
  return asyncReduce(
    middlewares,
    (next, mw) => () => mw(ctx, next),
    () => Promise.resolve(),
  )();
}
```

Koa-style middleware composition is a thinly-disguised `asyncReduce` over middleware functions. Senior signal.

### Variant 3 — `asyncReduceRight` (right-to-left)

```js
async function asyncReduceRight(arr, fn, init) {
  let acc = init;
  for (let i = arr.length - 1; i >= 0; i--) {
    acc = await fn(acc, arr[i], i, arr);
  }
  return acc;
}
```

Useful for right-associative ops (function composition).

### Variant 4 — Early exit (short-circuit)

```js
const STOP = Symbol('stop');

async function asyncReduceUntil(arr, fn, init) {
  let acc = init;
  for (let i = 0; i < arr.length; i++) {
    const result = await fn(acc, arr[i], i, arr);
    if (result === STOP) return acc;
    acc = result;
  }
  return acc;
}

// Usage
const firstFailure = await asyncReduceUntil(rows, async (acc, row) => {
  const ok = await validate(row);
  return ok ? acc : STOP;
}, null);
```

Allow `fn` to signal "done" via a sentinel. Useful for "find first invalid item."

### Variant 5 — Compose async ETL pipeline

```js
async function pipeline(stages, input) {
  return asyncReduce(stages, async (acc, stage) => stage(acc), input);
}

const result = await pipeline(
  [decompress, validateSchema, normalize, transform, enrich, save],
  rawData
);
```

Real-world ETL flow as a one-liner reduce over stage functions.

---

## 12. How to think aloud in the interview

> "Sequential by definition — each step depends on the previous accumulator. `let acc = await init; for (...) acc = await fn(acc, x, i, arr); return acc;`. Empty array + no init → throw `TypeError` to match native. Cannot parallelize unless `fn` is associative AND commutative — then tree-reduce gives O(log N) wall time. Common bug: trying `arr.reduce(async fn, init)` — native `reduce` doesn't await; accumulator becomes a Promise and you get `[object Promise]` in output. Functional alternative: `arr.reduce((accP, x) => accP.then(acc => fn(acc, x)), Promise.resolve(init))` — equivalent, harder to debug. Real-world use cases: koa middleware compose, ETL pipelines, layered config builds, aggregating paginated results."

---

## 13. 60-second revision

> - **Sequential by definition.** Each step depends on the previous accumulator.
> - **Pattern:** `let acc = await init; for (...) acc = await fn(acc, x, i, arr); return acc;`.
> - **Empty array + no init** → throw `TypeError` (match native).
> - **`await init`** to normalize promise inits.
> - **Match native signature:** `fn(acc, item, index, array)`.
> - **Functional alt:** `arr.reduce((accP, x) => accP.then(acc => fn(acc, x)), Promise.resolve(init))`.
> - **Cannot parallelize** unless `fn` is associative + commutative — then tree-reduce.
> - **Family:** koa middleware compose, ETL pipelines, layered config.
> - **Trap:** trying `Promise.all` over reduce; native `arr.reduce(async fn)` silently breaks; forgetting empty-no-init throw.

---

**Related:** [sequential-vs-parallel-async-map.md](./sequential-vs-parallel-async-map.md) · [async-filter.md](./async-filter.md) · [build-promise-from-scratch.md](./build-promise-from-scratch.md) · [`10-machine-coding-patterns/function-composition.md`](../10-machine-coding-patterns/function-composition.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
