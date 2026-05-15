# Implement `asyncFilter(arr, predicate)`

## Source
- Common follow-up to "implement asyncMap" — every senior Node interview eventually asks it.
- Real-world: filter rows by a permission check that hits the DB, filter files by an async stat call.
- BFE.dev "implement async filter" variants.

## Why this question matters in interviews
`asyncFilter` looks trivial — until you realize `Array.prototype.filter` doesn't await predicates. The naive `arr.filter(async pred)` is **always truthy** because the predicate returns a Promise, which is truthy. The correct version requires you to **evaluate predicates in parallel via `Promise.all`, then map booleans back to elements while preserving order**. It's a great signal for: knowing the bug, picking the right primitive, and discussing memory trade-offs.

## Concepts involved

### Syntax to lock in
```js
const validUsers = await asyncFilter(users, async (u) => await isActive(u.id));
// Only users where isActive(...) resolved to true.
```

### Runtime / engine behavior
- `Array.prototype.filter(pred)` treats the predicate's return value with `Boolean(...)`. A Promise object is **truthy regardless of its eventual value**, so `arr.filter(async pred)` returns the entire array. Subtle, classic bug.
- Parallel correct version: `Promise.all(arr.map(pred))` produces `[bool, bool, ...]`, then `arr.filter((_, i) => bools[i])` recombines.
- Serial version: walk with `for...of`, `await pred(item)`, conditionally push. Slower but lower memory.

### Edge cases (interview traps)
1. **Order preservation** — output preserves input order. Both parallel and serial achieve this naturally.
2. **Fail-fast** — `Promise.all` rejects on first predicate rejection, killing the whole filter. For "skip on error", attach `.catch(() => false)` to each predicate call.
3. **Memory pressure** — parallel pre-evaluates N predicates. If predicates are heavy (DB queries), bound the concurrency.
4. **Object identity** — output contains the **same references** as input, not copies. Mutation of an element is shared.
5. **Sparse arrays** — `arr.map` skips holes; behavior matches native `filter`. Worth mentioning.
6. **Returning truthy non-booleans** — coerce with `Boolean(await pred(...))` or rely on JS truthiness; native `filter` does the latter.

## Brute force approach
`arr.filter(async pred)` — wrong, always returns whole array (the async predicate returns a truthy Promise). Don't ship.

A correct but suboptimal brute force: serial `for...of` with manual push. Works, preserves order, but doesn't exploit parallelism when predicates can run concurrently.

## Optimal approach
**Parallel:** `Promise.all(arr.map(pred))` to get boolean array, then `arr.filter((_, i) => bools[i])`. O(N) time (max-bounded), O(N) memory.

**Serial (when needed):** for-of with await — same order preservation, lower memory, no rate-limit risk.

## Solution (JavaScript)

```js
// Parallel — predicates run concurrently
async function asyncFilter(arr, predicate) {
  const flags = await Promise.all(arr.map((item, i) => predicate(item, i)));
  return arr.filter((_, i) => flags[i]);
}

// Serial — predicates run one at a time (safer for rate-limited downstream)
async function asyncFilterSerial(arr, predicate) {
  const out = [];
  for (let i = 0; i < arr.length; i++) {
    if (await predicate(arr[i], i)) {
      out.push(arr[i]);
    }
  }
  return out;
}

// Bounded parallel — concurrency-limited version
async function asyncFilterBounded(arr, predicate, concurrency = 5) {
  const flags = new Array(arr.length);
  let cursor = 0;

  async function worker() {
    while (cursor < arr.length) {
      const i = cursor++;
      flags[i] = await predicate(arr[i], i);
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, arr.length) }, worker));
  return arr.filter((_, i) => flags[i]);
}
```

## Step-by-step dry run

Input:
```js
const users = [
  { id: 1, name: 'Ava' },
  { id: 2, name: 'Bob' },
  { id: 3, name: 'Cleo' },
];
const isActive = async (u) => new Promise(r => setTimeout(() => r(u.id % 2 === 1), 30));
const active = await asyncFilter(users, isActive);
```

Trace (parallel version):
- **t=0** — `arr.map((u, i) => isActive(u, i))` fires three predicate calls: p1 (id=1), p2 (id=2), p3 (id=3). All pending, all return after 30ms.
- **t=30** — all three settle. `Promise.all` resolves with `[true, false, true]`.
- **filter step** — `arr.filter((_, i) => [true,false,true][i])` produces `[users[0], users[2]]`.

Output: `[{ id: 1, name: 'Ava' }, { id: 3, name: 'Cleo' }]`. **Total time ≈ 30ms** (vs ~90ms serial).

Trace (serial version):
- t=0: i=0, await isActive(Ava) → true at t=30. Push Ava.
- t=30: i=1, await isActive(Bob) → false at t=60. Skip.
- t=60: i=2, await isActive(Cleo) → true at t=90. Push Cleo.
- **Total ≈ 90ms.**

## Important takeaways

**Syntax to memorize**
- `const flags = await Promise.all(arr.map(pred))` — get the boolean vector.
- `arr.filter((_, i) => flags[i])` — recombine with original elements.
- Serial fallback: `for...of` + `if (await pred(item)) out.push(item)`.

**Patterns to reuse**
- "Evaluate predicate vector in parallel, then recombine" — same pattern works for `asyncSort` (compute keys in parallel, sort by key), `asyncPartition`, `asyncGroupBy`.
- The parallel-then-recombine idiom decouples async evaluation from synchronous data manipulation. Very reusable.

**Common mistakes**
- `arr.filter(async pred)` — **the classic bug**. Always returns the whole array.
- Pushing into shared array from inside parallel callbacks without ordering — breaks order. Use indexed write into pre-allocated array instead.
- Not bounding parallelism when predicates are DB-bound — destroys the DB.
- Forgetting to handle predicate rejections — `Promise.all` fails fast; one bad row kills the whole filter.

**Related questions**
- `asyncMap` (the parent pattern)
- `asyncReduce` (the sibling — must be sequential)
- `asyncPartition(arr, pred)` — split into `[matching, nonMatching]`

## Variants

1. **`asyncFilter` with error tolerance** — wrap each predicate in `.catch(() => false)` so one rejection doesn't kill the batch. Discuss the trade-off (silent skipping).
2. **`asyncFind(arr, pred)`** — return the first match. Sequential makes sense to avoid wasted work. With parallel + short-circuit, you'd need an AbortController.
3. **Streaming async filter** — yield matches as they're confirmed. Use a generator + `for await...of`.
4. **`asyncFilter` over an async iterable** — input is already a stream. Different shape: `for await (const item of source) { if (await pred(item)) yield item; }`.

## Revision notes

> **asyncFilter — 60 second recap**
> - **Bug to avoid:** `arr.filter(async pred)` — Promise is truthy, returns all.
> - **Parallel:** `Promise.all(arr.map(pred))` → boolean vector → `arr.filter((_, i) => flags[i])`.
> - **Serial:** `for...of` + `await pred(item)` + conditional push. Same order, less memory, no rate limit.
> - **Bounded:** cursor + N workers for DB-bound predicates.
> - Order preserved by indexed write or input-order iteration.
> - **Trap:** confusing async truthiness — Promise is always truthy.
