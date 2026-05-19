# Implement `asyncFilter(arr, predicate)` — `filter` with async predicate

> **Difficulty:** Medium   |   **Time:** ~20 min   |   **Prereqs:** [sequential-vs-parallel-async-map.md](./sequential-vs-parallel-async-map.md), [promise-all-polyfill.md](./promise-all-polyfill.md)
>
> **Source:** Common follow-up to "implement asyncMap"; BFE.dev variants.

---

## 1. Problem statement

**Signatures**
```ts
function asyncFilter<T>(arr: T[], predicate: (x: T, i: number) => Promise<boolean>): Promise<T[]>;
function asyncFilterSerial<T>(arr: T[], predicate: (x: T, i: number) => Promise<boolean>): Promise<T[]>;
function asyncFilterBounded<T>(arr: T[], predicate: (x: T, i: number) => Promise<boolean>, k: number): Promise<T[]>;
```

**Input / Output examples**

| Setup                                                          | Output                                              |
|----------------------------------------------------------------|------------------------------------------------------|
| `asyncFilter([1,2,3,4], async x => x % 2 === 0)`              | `[2, 4]`                                            |
| `arr.filter(async pred)`                                       | **bug** — returns all items (Promise is truthy)     |
| Parallel — predicates evaluated concurrently                   | total time ≈ max(predicate)                         |
| Serial — predicates evaluated sequentially                     | total time ≈ Σ predicates                            |
| Bounded — k predicates concurrent                              | total time ≈ N/k × per-item                          |

**Constraints**
- Preserve **input order** in output.
- Default: parallel via `Promise.all(arr.map(pred))` then recombine.
- Output contains **same references** as input — not copies.
- Sparse arrays: match `Array.prototype.filter` semantics (skip holes).
- `Boolean(await pred(...))` — JS truthiness applies.

---

## 2. Plain-English restatement

You want `arr.filter(pred)` but `pred` is async. The naive `arr.filter(async pred)` is broken — the predicate returns a Promise (which is *truthy*), so `filter` keeps every item. The correct approach: evaluate predicates in parallel via `Promise.all(arr.map(pred))` to get a boolean array, then `arr.filter((_, i) => bools[i])` to recombine while preserving order.

---

## 3. Why this matters in interviews

`asyncFilter` looks trivial — until you realize `Array.prototype.filter` doesn't await predicates. The naive `arr.filter(async pred)` is **always truthy** because the predicate returns a Promise, which is truthy. The correct version requires you to **evaluate predicates in parallel via `Promise.all`, then map booleans back to elements while preserving order**. Great signal for: knowing the bug, picking the right primitive, and discussing memory trade-offs.

---

## 4. Mental model

```
   arr.filter(async pred) — BROKEN
   ────────────────────────────────
   pred returns a Promise (truthy)
   filter keeps every item
   Returns the entire array.

   Parallel asyncFilter — correct
   ──────────────────────────────
   step 1: flags = await Promise.all(arr.map(pred))     ← all in parallel
                  ↓
                  [true, false, true, true]
   step 2: arr.filter((_, i) => flags[i])              ← recombine
                  ↓
                  [arr[0], arr[2], arr[3]]
```

**The two-step decomposition** is the senior insight: separate the async predicate evaluation from the synchronous data manipulation. Same pattern generalizes to `asyncSort`, `asyncPartition`, `asyncGroupBy`.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `[1, 2, 3].filter(async (x) => x > 1)` return? Why?
> 2. With 1000 items and a DB-bound predicate, what shape should you reach for?
> 3. If one predicate rejects, what happens to `Promise.all([pred(x1), pred(x2), ...])`?

---

## 6. Brute force — walked through

### Wrong attempt 1: `arr.filter(async pred)`

```js
const filtered = users.filter(async (u) => await isActive(u.id));
// users.length items returned — every one
```

**Always returns the whole array.** `filter` coerces the predicate's return value with `Boolean(...)`. A Promise is **truthy regardless of its eventual value**. The classic bug. Don't ship.

### Wrong attempt 2: sequential when parallel is fine

```js
async function asyncFilter(arr, pred) {
  const out = [];
  for (const item of arr) {
    if (await pred(item)) out.push(item);
  }
  return out;
}
```

**Works** and preserves order, but slow when predicates are independent. If you have 100 items and each predicate is 30ms, this takes 3s instead of 30ms.

### Wrong attempt 3: parallel but order broken

```js
async function asyncFilterBroken(arr, pred) {
  const out = [];
  await Promise.all(arr.map(async (item) => {
    if (await pred(item)) out.push(item);   // BUG: push order = completion order
  }));
  return out;
}
```

Output order depends on which predicates resolved first — not input order. Use indexed write into a pre-allocated array, or the "boolean vector + recombine" pattern.

---

## 7. The unlocking insight

> **Evaluate predicates in parallel via `Promise.all(arr.map(pred))` to get a boolean vector. Then `arr.filter((_, i) => flags[i])` synchronously recombines with input-order preservation.**

The shape:

```js
async function asyncFilter(arr, predicate) {
  const flags = await Promise.all(arr.map((item, i) => predicate(item, i)));
  return arr.filter((_, i) => flags[i]);
}
```

Three properties:

1. **Two-step decomposition.** Async predicate evaluation (parallel) → synchronous data manipulation (sequential). Decoupling them makes the order-preservation trivial.

2. **Order preserved.** `flags[i]` corresponds to `arr[i]`. The final `filter((_, i) => flags[i])` keeps elements in their original positions.

3. **Reuses native `filter`.** No manual indexed-write logic. Just the boolean vector.

**Memory note:** parallel evaluates all N predicates simultaneously, pre-allocating N pending promises. For DB-bound predicates over a 1M-item array, you'll destroy the DB. Use bounded parallel.

**Fail-fast note:** `Promise.all` rejects on first predicate rejection, killing the whole filter. For "skip on error" semantics, attach `.catch(() => false)` to each predicate call — the failed item gets filtered out.

---

## 8. Solution (annotated)

```js
// Parallel — predicates evaluated concurrently
async function asyncFilter(arr, predicate) {
  const flags = await Promise.all(                          // step 1: boolean vector in parallel
    arr.map((item, i) => predicate(item, i))
  );
  return arr.filter((_, i) => flags[i]);                    // step 2: recombine (input order)
}

// Serial — for rate-limited downstream
async function asyncFilterSerial(arr, predicate) {
  const out = [];
  for (let i = 0; i < arr.length; i++) {
    if (await predicate(arr[i], i)) out.push(arr[i]);
  }
  return out;
}

// Bounded parallel — k predicates concurrent
async function asyncFilterBounded(arr, predicate, concurrency = 5) {
  const flags = new Array(arr.length);
  let cursor = 0;

  async function worker() {
    while (cursor < arr.length) {
      const i = cursor++;                                   // capture BEFORE await
      flags[i] = await predicate(arr[i], i);
    }
  }

  await Promise.all(
    Array.from({ length: Math.min(concurrency, arr.length) }, worker)
  );
  return arr.filter((_, i) => flags[i]);
}

// Fault-tolerant: skip on predicate rejection
async function asyncFilterTolerant(arr, predicate) {
  const flags = await Promise.all(
    arr.map((item, i) =>
      Promise.resolve(predicate(item, i)).catch(() => false)   // failed → filter out
    )
  );
  return arr.filter((_, i) => flags[i]);
}
```

**Try it yourself**

```js
const users = [
  { id: 1, name: 'Ava' },
  { id: 2, name: 'Bob' },
  { id: 3, name: 'Cleo' },
];
const isActive = async (u) => new Promise((r) => setTimeout(() => r(u.id % 2 === 1), 30));

const active = await asyncFilter(users, isActive);
// [Ava, Cleo] — at t≈30ms (parallel)

const activeSerial = await asyncFilterSerial(users, isActive);
// [Ava, Cleo] — at t≈90ms (serial)

// Naive bug
console.log(users.filter(async (u) => isActive(u)));
// All three users (every Promise is truthy)
```

---

## 9. Step-by-step dry run

Input:

```js
const users = [{id:1},{id:2},{id:3}];
const isActive = async (u) => sleep(30, u.id % 2 === 1);
await asyncFilter(users, isActive);
```

**Parallel trace:**

| Time | Event                                              | `flags`             |
|------|----------------------------------------------------|----------------------|
| 0    | `arr.map(pred)` fires three predicate calls       | `[pending × 3]`     |
| 30   | all three settle: `[true, false, true]`            | `[true, false, true]` |
| 30+µ | `arr.filter((_, i) => flags[i])` recombines       | —                    |
| 30+µ | return `[users[0], users[2]]`                      | —                    |

**Total: ~30ms.**

**Serial trace:**

| Time | Event                                               | `out`                |
|------|------------------------------------------------------|-----------------------|
| 0    | i=0: `await isActive(u0)` → true at t=30; push      | `[u0]`               |
| 30   | i=1: `await isActive(u1)` → false at t=60; skip     | `[u0]`               |
| 60   | i=2: `await isActive(u2)` → true at t=90; push      | `[u0, u2]`           |

**Total: ~90ms** (3 × 30ms sequential).

---

## 10. Common confusion + traps

1. **`arr.filter(async pred)` returns everything.** Promise is truthy. The classic bug.

2. **Pushing into shared array from parallel callbacks.** Breaks order. Use indexed write or the boolean-vector pattern.

3. **Not bounding parallelism for DB-bound predicates.** Destroys the database. Use `asyncFilterBounded`.

4. **`Promise.all` fail-fast.** One predicate rejection kills the whole filter. For tolerance, wrap each in `.catch(() => false)`.

5. **Object identity.** Output contains the **same references** as input — not copies. Mutating an element is shared.

6. **Sparse arrays.** `arr.map` skips holes (matches native `filter`). Document if relevant.

7. **Truthy non-booleans.** `Boolean(await pred(...))` applies. `0`, `''`, `null`, `undefined`, `NaN` → false. Match native semantics.

---

## 11. Senior follow-ups & variants

### Variant 1 — `asyncFind(arr, pred)` — first match

Sequential to avoid wasted work; or parallel with AbortController to cancel siblings:

```js
async function asyncFind(arr, predicate) {
  for (let i = 0; i < arr.length; i++) {
    if (await predicate(arr[i], i)) return arr[i];
  }
  return undefined;
}

// Parallel with short-circuit (more complex):
async function asyncFindParallel(arr, predicate) {
  return new Promise((resolve, reject) => {
    let pending = arr.length;
    arr.forEach((item, i) => {
      Promise.resolve(predicate(item, i))
        .then((ok) => {
          if (ok) resolve(item);
          else if (--pending === 0) resolve(undefined);
        })
        .catch(reject);
    });
  });
}
```

### Variant 2 — `asyncPartition(arr, pred)` — split into [yes, no]

```js
async function asyncPartition(arr, predicate) {
  const flags = await Promise.all(arr.map(predicate));
  const yes = [];
  const no = [];
  arr.forEach((item, i) => (flags[i] ? yes : no).push(item));
  return [yes, no];
}
```

Useful for "process this batch, but also log rejections."

### Variant 3 — Streaming async filter

For huge input or pipeline use:

```js
async function* asyncFilterStream(source, predicate) {
  for await (const item of source) {
    if (await predicate(item)) yield item;
  }
}

for await (const item of asyncFilterStream(hugeSource, asyncCheck)) {
  process(item);
}
```

Memory bounded.

### Variant 4 — `asyncSort` (compute keys in parallel, sort by key)

Same decomposition trick:

```js
async function asyncSort(arr, keyFn) {
  const keys = await Promise.all(arr.map(keyFn));
  return arr
    .map((item, i) => ({ item, key: keys[i] }))
    .sort((a, b) => a.key - b.key)
    .map(({ item }) => item);
}
```

Compute async keys in parallel, then sort synchronously by them.

### Variant 5 — Error-tolerant variant

```js
async function asyncFilterSkipErrors(arr, predicate) {
  const flags = await Promise.all(
    arr.map((item, i) =>
      Promise.resolve(predicate(item, i)).catch(() => false)
    )
  );
  return arr.filter((_, i) => flags[i]);
}
```

Treat rejections as "doesn't pass the filter" — useful when failures are recoverable.

---

## 12. How to think aloud in the interview

> "Classic bug: `arr.filter(async pred)` returns the whole array because Promise is truthy. The correct two-step approach: `const flags = await Promise.all(arr.map(pred))` to get a boolean vector in parallel; then `arr.filter((_, i) => flags[i])` to recombine in input order. This decouples async evaluation from sync data manipulation — same pattern generalizes to `asyncSort`, `asyncPartition`, `asyncGroupBy`. For DB-bound predicates over large arrays, use bounded concurrency. For fault tolerance, wrap each predicate in `.catch(() => false)` so rejections are treated as 'doesn't pass.' For 'first match', use sequential `asyncFind` or parallel-with-short-circuit via AbortController."

---

## 13. 60-second revision

> - **Bug:** `arr.filter(async pred)` — Promise is truthy, returns all.
> - **Parallel:** `Promise.all(arr.map(pred))` → boolean vector → `arr.filter((_, i) => flags[i])`.
> - **Two-step pattern:** async eval (parallel) → sync recombine (filter).
> - **Serial:** `for...of` + `await pred(item)` + conditional push. Use when downstream is rate-limited.
> - **Bounded:** k workers + shared cursor for huge or DB-bound predicates.
> - **Fault-tolerant:** wrap each predicate in `.catch(() => false)`.
> - **Order preserved** via indexed write or input-order iteration.
> - **Family:** `asyncMap`, `asyncReduce`, `asyncFind`, `asyncPartition`, `asyncSort`.
> - **Trap:** confusing async truthiness — Promise is always truthy.

---

**Related:** [sequential-vs-parallel-async-map.md](./sequential-vs-parallel-async-map.md) · [async-reduce.md](./async-reduce.md) · [promise-all-polyfill.md](./promise-all-polyfill.md) · [promise-pool.md](./promise-pool.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
