# 07 — Arrays

Array polyfills, mutation patterns, sort, performance internals. v2 13-section template.

---

## How to study this folder

1. **Polyfills:** map → filter → reduce → some/every → find/findIndex → flat.
2. **Mutation patterns:** move-zeros, rotate, find-runs, sliding-window-helper.
3. **Composition:** chunk, dedup, set-ops, zip/unzip, transpose, group-and-partition.
4. **Sort:** sort-by-multiple-keys, stable-sort-discussion.
5. **Math:** math-array-ops.
6. **Performance internals:** holey-vs-packed-arrays, typed-array-basics, structured-clone-vs-spread.
7. **Lodash bridge:** lodash-reduce.

---

## Files (23)

### Polyfills (spec literacy)
- [polyfill-map.md](./polyfill-map.md) — Hole-preserving + thisArg.
- [polyfill-filter.md](./polyfill-filter.md) — Hole-skipping; dense output.
- [polyfill-reduce.md](./polyfill-reduce.md) — Seed handling + TypeError.
- [polyfill-some-every.md](./polyfill-some-every.md) — Short-circuit + vacuous truth.
- [polyfill-find-findindex.md](./polyfill-find-findindex.md) — No hole skipping (ES6 cleanup).
- [polyfill-flat.md](./polyfill-flat.md) — Iterative stack avoids RangeError.

### Mutation patterns
- [move-zeros-in-place.md](./move-zeros-in-place.md) — Two-pointer write-index.
- [rotate-array.md](./rotate-array.md) — Three-reverse trick, O(1).
- [find-runs.md](./find-runs.md) — Two-pointer scan + string compression.
- [sliding-window-helper.md](./sliding-window-helper.md) — Fixed and variable templates.

### Composition
- [chunk-array.md](./chunk-array.md) — Fixed-size buckets.
- [array-dedup.md](./array-dedup.md) — Set / Map / filter+indexOf tradeoffs.
- [array-set-ops.md](./array-set-ops.md) — Intersection/union/diff; ES2025 Set methods.
- [zip-unzip.md](./zip-unzip.md) — Variadic + transpose.
- [transpose-matrix.md](./transpose-matrix.md) — In-place square swap.
- [group-and-partition.md](./group-and-partition.md) — ES2024 Object/Map.groupBy.

### Sort
- [sort-by-multiple-keys.md](./sort-by-multiple-keys.md) — Composed comparator.
- [stable-sort-discussion.md](./stable-sort-discussion.md) — ES2019 TimSort migration.

### Math
- [math-array-ops.md](./math-array-ops.md) — sum/avg/min/max/median; spread trap.

### Performance internals
- [holey-vs-packed-arrays.md](./holey-vs-packed-arrays.md) — V8 element kinds.
- [typed-array-basics.md](./typed-array-basics.md) — ArrayBuffer + views.
- [structured-clone-vs-spread.md](./structured-clone-vs-spread.md) — Deep clone tradeoffs.

### Lodash bridge
- [lodash-reduce.md](./lodash-reduce.md) — Reduce on objects too.

---

## Concept primers

- [`concepts/arrays.md`](../../concepts/arrays.md) — Array mechanics.
- [`concepts/maps-sets.md`](../../concepts/maps-sets.md) — Set/Map equality.
- [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md) — Iterative vs recursive.

---

## Companion sections

- `08-maps-sets/` — group-by, dedup-by-key, set operations.
- `09-recursion/` — flatten variants, deep-clone.
- `10-machine-coding-patterns/` — debounce/throttle, LRU cache.
