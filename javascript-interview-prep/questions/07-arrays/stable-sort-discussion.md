# Stable sort — what changed in ES2019

## Source
- TC39 spec change: https://tc39.es/ecma262/#sec-array.prototype.sort (note on stability).
- V8 blog post on TimSort migration: https://v8.dev/blog/array-sort
- Canonical "interview trivia that bites in production" question (BFE.dev #150, frontendmasters).

## Why this question matters in interviews
This is a **knowledge** question, not a coding question — and that's the point. Senior interviewers ask "what changed about `Array.prototype.sort` in ES2019?" to test whether you keep up with the language or coast on muscle memory. The answer ("it became stable") is one line; the **why** (V8 switched from quicksort+insertion-sort to TimSort), the **implications** (multi-key sort no longer needs index-tiebreaker tricks), and the **pre-2019 workaround** are the real signal. Backend engineers writing data-pipeline sorts or building lodash-style utilities NEED to know this. It also opens the door to discussing comparator stability, total-order requirements, and engine quirks.

## Concepts involved

### Syntax to lock in
```js
// Same input, same output guaranteed since ES2019:
const arr = [{ k: 1, v: 'a' }, { k: 1, v: 'b' }, { k: 1, v: 'c' }];
arr.sort((a, b) => a.k - b.k);
// Pre-2019 in V8: might be ['a','b','c'] or ['c','b','a'] or ['b','a','c']
// Post-2019:      always ['a','b','c'] (original order preserved on ties)
```

### Runtime / engine behavior

**Pre-ES2019 (V8 before v7.0, mid-2018):**
- V8 used **insertion sort** for arrays with `length <= 10` (stable, O(n²) worst case).
- For larger arrays: **quicksort** with median-of-three pivot. Quicksort is **unstable** — elements equal under the comparator could swap relative order.
- The spec said: "The sort is not required to be stable." Engines were free.
- SpiderMonkey (Firefox) used mergesort — stable. WebKit used mergesort too. **Only V8 was unstable for large arrays.** This caused real cross-browser bugs.

**Post-ES2019 (V8 7.0+, Node 11+):**
- Spec mandates stability.
- V8 adopted **TimSort** (the same algorithm as Python's `list.sort` and Java's `Arrays.sort` for objects). Adaptive merge sort, O(n log n) worst case, O(n) on already-sorted data, **stable**.
- All major engines now stable: V8 (TimSort), SpiderMonkey (mergesort), JSC (mergesort).

### What "stable" means
A sort is **stable** if equal-keyed elements retain their **input relative order**. Formal definition: if `cmp(a, b) === 0` and `a` appears before `b` in input, `a` appears before `b` in output.

### Implications
1. **Multi-key sort is trivial post-2019.** You can sort by minor key first, then major key, and stability preserves the minor ordering on major ties. (You can also write a composed comparator — that's the modern way.)
2. **Original-index tiebreaker** (the old workaround) is now unnecessary. But add it if you support Node 10 or below.
3. **Equal elements don't shuffle.** UI lists won't visually jitter on re-sort.
4. **Schwartzian transform** is now optional, not required for determinism — only used for perf (expensive keys).

### Edge cases (the interview traps)
1. **Non-total comparator** — if your comparator violates antisymmetry (e.g., `cmp(a,b) === cmp(b,a) === -1`), the engine is allowed to do anything. Stability **only kicks in when comparator returns 0**. A buggy comparator can still scramble.
2. **NaN in comparator return value** — `NaN < 0` is false, `NaN > 0` is false, treated as `0`. Indeterminate.
3. **Numeric-string subtract bug** — `'10' - '2'` is `8` (coerces). But `'abc' - 'def'` is `NaN`. Mixed-type arrays bite.
4. **Old Node** — Node 10 LTS ended in 2021 but many CI containers still use it. **Don't assume stability** if you support legacy.
5. **TypedArray sort is also stable** (since ES2019), with a default comparator that does numeric compare (unlike Array's default which is lex-string compare).
6. **Default comparator** — `[10, 2, 1].sort()` is `[1, 10, 2]`. Lexicographic. **Always pass an explicit comparator** for numeric data.

## Brute force approach
The pre-2019 workaround: decorate each element with its original index, sort by `(key, index)` jointly, undecorate.

```js
function stableSort(arr, cmp) {
  return arr
    .map((v, i) => [v, i])
    .sort(([a, i], [b, j]) => cmp(a, b) || i - j)
    .map(([v]) => v);
}
```

Costs: O(n) extra space, O(n log n) time, slightly slower due to allocation. Still useful when targeting Node 10 or pre-Chrome 70.

## Optimal approach
Just use native `sort` and pass a correct, total comparator. Stability is automatic. Use a composed comparator for multi-key needs. No tricks required.

If you need pre-2019 portability, use the decorate-sort-undecorate pattern above.

## Solution (JavaScript)

```js
// Modern (Node 11+, ES2019+) — stable by default
function multiKeySort(arr, fields) {
  const cmp = (a, b) => {
    for (const { key, dir = 'asc' } of fields) {
      const av = a[key], bv = b[key];
      const r = av < bv ? -1 : av > bv ? 1 : 0;
      if (r) return r * (dir === 'desc' ? -1 : 1);
    }
    return 0;   // equal → native sort preserves input order (stable)
  };
  return [...arr].sort(cmp);
}

// Legacy-safe (works on Node 10 and below) — explicit index tiebreaker
function stableMultiKeySort(arr, fields) {
  const decorated = arr.map((v, i) => ({ v, i }));
  decorated.sort((x, y) => {
    for (const { key, dir = 'asc' } of fields) {
      const av = x.v[key], bv = y.v[key];
      const r = av < bv ? -1 : av > bv ? 1 : 0;
      if (r) return r * (dir === 'desc' ? -1 : 1);
    }
    return x.i - y.i;   // explicit tiebreak by original index
  });
  return decorated.map(({ v }) => v);
}

// Detect engine stability at runtime (rarely needed)
function isSortStable() {
  const a = Array.from({ length: 1000 }, (_, i) => ({ k: 0, i }));
  a.sort((x, y) => x.k - y.k);
  return a.every((x, i) => x.i === i);
}
```

## Step-by-step dry run

Pre-2019 V8, sorting 100 user objects all with `role: 'admin'`:
- Quicksort partitions on a pivot element. Equal-keyed items end up on both sides of the pivot non-deterministically.
- Result: input order **not preserved**. List visibly shuffles on every sort with the same key.

Same scenario post-2019:
- TimSort scans for already-sorted runs. Equal-keyed items have `cmp === 0`, treated as a run.
- Result: input order preserved. Sort is **idempotent** on already-sorted input — O(n) too.

Demo:
```js
const arr = [
  { name: 'Alice', i: 0 },
  { name: 'Bob',   i: 1 },
  { name: 'Alice', i: 2 },
  { name: 'Bob',   i: 3 },
];
arr.sort((a, b) => a.name.localeCompare(b.name));
// Post-2019: [Alice@0, Alice@2, Bob@1, Bob@3]
// The `i` field is preserved as 0, 2, 1, 3 — the original order on ties.
```

## Important takeaways

**Syntax to memorize**
- Native `.sort()` is **stable** in Node 11+ / Chrome 70+ / Firefox / Safari (all current).
- For pre-2019 portability: decorate `[v, i]`, sort with `cmp || i - j`, undecorate.
- TimSort: O(n) on sorted input, O(n log n) worst case, stable, O(n) extra space.

**Patterns to reuse**
- "Sort by minor key first, then major key" works post-2019 because of stability.
- "Composed multi-key comparator" is the modern, single-pass approach.
- "Original-index tiebreaker" is the legacy-safe fallback that ALWAYS works.

**Common mistakes**
- Assuming `sort()` is stable on Node 10. It might be (for length ≤ 10) or might not.
- Forgetting the default comparator is **lexicographic** — `[10, 2].sort()` is `[10, 2]`, not `[2, 10]`.
- Writing a non-total comparator (returns NaN, or violates `cmp(a,b) === -cmp(b,a)`) and being surprised by chaos.
- Calling `arr.sort()` and assuming it doesn't mutate. **It mutates and returns the same array.** Use `[...arr].sort()` or `arr.toSorted()`.

**Related questions**
- `sort-by-multiple-keys` — practical multi-key sort using stability.
- Stable algorithms taxonomy: mergesort, insertion sort, bubble sort, TimSort, counting sort — all stable. Quicksort, heapsort, selection sort — unstable by default.
- ES2023's `toSorted()` — immutable variant.

## Variants

1. **TimSort deep-dive** — "Why TimSort specifically?" Answer: real-world data has natural runs; TimSort detects them in O(n) and merges. Pure mergesort is O(n log n) even on sorted input. TimSort beats it on partially-sorted data, which is the common case.

2. **Why was V8 unstable in the first place?** Answer: quicksort is faster on average and has better cache locality. The JS spec didn't require stability, so V8 took the perf win. TC39 standardized stability when it became clear cross-browser variance was hurting more than the speed helped.

3. **Sort vs toSorted (ES2023)** — "Show me the immutable version." `arr.toSorted(cmp)` returns a new array. Same stability guarantee. Use in functional codebases or when you can't mutate the input.

4. **TypedArray.sort** — "Does Uint32Array.sort() work the same way?" Yes, stable since ES2019, BUT the default comparator is numeric (not lex-string). `new Uint32Array([10,2,1]).sort()` is `[1,2,10]`.

## Revision notes

> **stable sort — 60 second recap**
> - **Pre-ES2019:** V8 used quicksort (unstable) for arrays > 10. Spec didn't require stability.
> - **ES2019+ / Node 11+:** spec mandates stability. V8 switched to **TimSort**.
> - Stability means: equal-keyed elements preserve **input order**.
> - Implication: multi-key sort no longer needs index-tiebreaker tricks.
> - Workaround for legacy: decorate `[value, index]`, sort with `cmp || i - j`.
> - **Trap:** default comparator is lex-string — `[10,2].sort()` → `[10,2]`.
> - **Family:** TimSort, mergesort, insertion sort = stable. Quicksort, heapsort = unstable.
