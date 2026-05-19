# Stable sort — what changed in ES2019

> **Difficulty:** Senior   |   **Time:** ~8 min   |   **Prereqs:** [sort-by-multiple-keys.md](./sort-by-multiple-keys.md)
>
> **Source:** TC39 ES2019 spec. V8 TimSort blog. BFE.dev #150.

---

## 1. Problem statement

**What changed about `Array.prototype.sort` in ES2019?** Be ready to discuss stability, the V8 quicksort→TimSort switch, and the pre-2019 workaround.

**Verification example**

```js
// Same input, same output guaranteed since ES2019:
const arr = [{ k: 1, v: 'a' }, { k: 1, v: 'b' }, { k: 1, v: 'c' }];
arr.sort((a, b) => a.k - b.k);
// Pre-2019 V8 (n > 10): could be any order on ties.
// Post-2019: always 'a','b','c' (stable).
```

**Constraints**
- Stable = equal-keyed items preserve input order.
- Pre-2019 V8 quicksort was unstable for `n > 10`.
- Post-2019: TimSort (V8 7.0+, Node 11+).
- SpiderMonkey/JSC always used stable mergesort.

---

## 2. Plain-English restatement

ES2019 mandated `sort` stability. V8 (Chrome/Node) switched from quicksort to TimSort. Multi-key sort no longer needs index tiebreakers.

---

## 3. Why this matters in interviews

Knowledge question, not coding. Tests whether you keep up with the language. The "why" (TimSort) and implications (no more index workaround) are the real signal.

---

## 4. Mental model

```
   Stable: cmp(a, b) === 0 ∧ a appears before b in input → a before b in output.
   
   Pre-2019 V8:
     length ≤ 10: insertion sort (stable, O(n²) worst).
     length > 10: quicksort with median-of-three pivot (UNSTABLE).
     Cross-browser: SpiderMonkey/JSC used mergesort (stable).
     → V8 was the outlier; real cross-browser bugs.
   
   Post-2019 V8 (7.0+, Node 11+):
     TimSort (same as Python's list.sort, Java's Arrays.sort for objects).
     Adaptive merge sort. O(n log n) worst, O(n) on already-sorted.
     STABLE.
   
   Pre-2019 workaround (multi-key):
     Add original index as final tiebreaker:
       arr.sort((a, b) => cmp(a, b) || origIndex[a] - origIndex[b])
   
   Post-2019:
     Compose comparator naturally; stability handles ties.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What's "stable" mean?
> 2. Why did V8 switch to TimSort?
> 3. Does the spec still allow unstable sort?

---

## 6. Brute force — walked through

The pre-2019 multi-key sort:

```js
// V8 quicksort would break this if n > 10
arr
  .map((x, i) => ({ x, i }))
  .sort((a, b) => cmp(a.x, b.x) || a.i - b.i)    // index tiebreaker
  .map(({ x }) => x);
```

Post-2019: index tiebreaker unnecessary.

---

## 7. The unlocking insight

> **Stability means equal-keyed items keep input order. ES2019 mandated it; V8 switched to TimSort. Multi-key sort no longer needs index tiebreakers.**

Three properties:

1. **ES2019 stability** mandate.
2. **TimSort** in V8; mergesort in others.
3. **Multi-key trivial** post-2019.

---

## 8. Solution (annotated)

```js
// Pre-2019 safe multi-key sort (index tiebreaker)
function multiKeyPre2019(arr, comparator) {
  return arr
    .map((item, i) => [item, i])
    .sort(([a, ai], [b, bi]) => comparator(a, b) || ai - bi)              // step 1: tiebreaker
    .map(([item]) => item);
}

// Post-2019 (and modern) — stability is guaranteed
function multiKey(arr, comparator) {
  return [...arr].sort(comparator);                                       // step 2: stable
}

// Test for stability
function isSortStable() {
  const arr = Array.from({ length: 20 }, (_, i) => ({ k: 1, i }));
  arr.sort((a, b) => a.k - b.k);
  return arr.every((x, idx) => x.i === idx);                              // step 3: original index preserved
}
isSortStable();                                                            // true on all modern runtimes
```

**Try it yourself**

```js
// Test: equal keys preserve order
const arr = [
  { k: 1, v: 'a' }, { k: 1, v: 'b' }, { k: 0, v: 'c' }, { k: 1, v: 'd' }
];
arr.sort((a, b) => a.k - b.k);
// Post-2019: [{k:0,v:'c'}, {k:1,v:'a'}, {k:1,v:'b'}, {k:1,v:'d'}]
// (k=1 items in input order: a, b, d)

// Sort by minor key first, then major (relies on stability)
function sortByMinorThenMajor(arr, minorKey, majorKey) {
  arr.sort((a, b) => a[minorKey] - b[minorKey]);
  arr.sort((a, b) => a[majorKey] - b[majorKey]);
  // Minor order preserved within major ties (only true if stable).
}

// ES2023 non-mutating
const sorted = [3, 1, 2].toSorted();                          // [1, 2, 3]
const og = [3, 1, 2];
og.toSorted();
console.log(og);                                              // [3, 1, 2] (unchanged)
```

---

## 9. Step-by-step dry run

```
Pre-2019 V8 with n=15 array of equal keys:
  Quicksort with median-of-three.
  Partition may swap equal-keyed elements arbitrarily.
  Result: order of equal-keyed elements UNPREDICTABLE.

Post-2019 (TimSort):
  Detect already-sorted runs.
  Merge adjacent runs (mergesort step).
  Merge is STABLE — equal-keyed take left run first.
  Result: input order preserved on ties.

Cross-browser pre-2019:
  Chrome (V8): quicksort → unstable.
  Firefox (SpiderMonkey): mergesort → stable.
  Safari (JSC): mergesort → stable.
  → Code worked in FF/Safari but broke in Chrome.

TimSort benefits beyond stability:
  - O(n) on already-sorted input.
  - O(n) on reversed input.
  - Galloping mode for runs.
  - Cache-friendly merge.
```

---

## 10. Common confusion + traps

1. **Old code with index tiebreaker** — now redundant but harmless.
2. **Cross-browser test pre-2019** — bugs only showed in V8 large arrays.
3. **`sort` mutates** — even now. Use `[...arr].sort()` or `toSorted()`.
4. **Comparator must be total** — non-deterministic → undefined behavior.
5. **Comparator returns boolean** — coerces; broken sort.
6. **TypedArray sort** — different algorithm; doesn't share guarantees fully.
7. **`Intl.Collator.compare` stability** — same as standard.

---

## 11. Senior follow-ups & variants

### Variant 1 — TimSort runs
Detect already-sorted prefixes; gallop-merge runs.

### Variant 2 — Sort by minor then major
Relies on stability.

### Variant 3 — `toSorted` (ES2023)
Non-mutating; same stability.

### Variant 4 — TypedArray sort
Numeric default (different from Array's lex default).

### Variant 5 — Custom Intl.Collator
Reusable; locale-aware.

---

## 12. How to think aloud

> "Pre-ES2019, V8 used quicksort for `length > 10` — unstable — while SpiderMonkey and JSC used mergesort — stable. Cross-browser sort bugs were real. ES2019 mandated stability; V8 adopted TimSort (same as Python `list.sort`, Java `Arrays.sort` for objects) — adaptive merge sort, O(n log n) worst case, O(n) on already-sorted runs, **stable**. Stable means: if `cmp(a, b) === 0` and `a` came before `b` in input, `a` comes before `b` in output. Implication for multi-key sort: pre-2019 you had to add an original-index tiebreaker (`cmp(a, b) || ai - bi`) to guarantee stability; post-2019 you just write the composed comparator. Or you can sort by minor key first, then major — minor order preserved within major ties (only true if stable). Engines: V8 TimSort, SpiderMonkey mergesort, JSC mergesort — all stable now. `Array.prototype.sort` still mutates; use `[...arr].sort()` or ES2023 `arr.toSorted()` for non-mutation. Trap: relying on stability on Node 10 or older; comparator returning boolean; non-total comparators; sort mutates by default."

---

## 13. 60-second revision

> - **ES2019: stable sort mandated.**
> - **Pre-2019 V8:** quicksort > 10, unstable. SM/JSC: stable mergesort.
> - **Post-2019 V8:** TimSort — stable, O(n log n), O(n) on sorted.
> - **Stable = equal keys keep input order.**
> - **Multi-key:** composed comparator; pre-2019 needed index tiebreaker.
> - **`sort` mutates;** `toSorted` (ES2023) doesn't.
> - **Comparator must return number, be total.**
> - **Trap:** Node 10; boolean return; non-total comparator.

---

**Related:** [sort-by-multiple-keys.md](./sort-by-multiple-keys.md) · [structured-clone-vs-spread.md](./structured-clone-vs-spread.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
