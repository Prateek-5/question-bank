# 08 — Maps & Sets

Map/Set/WeakMap mechanics, caches, frequency maps, JSON quirks. v2 13-section template.

---

## How to study this folder

1. **Foundation:** object-vs-map-vs-set → two-sum-map → multiset-counter.
2. **Counter / group:** first-non-repeating-char, group-by, group-anagrams.
3. **Cache patterns:** lru-cache-with-map, ttl-map, cache-invalidate-by-tag.
4. **WeakMap / GC:** weakmap-memoize, weakref-finalization-registry.
5. **JSON:** is-object-empty, convert-object-to-json-string, json-with-map-replacer.
6. **Diff / shape:** object-deep-diff.
7. **Order quirks:** ordered-map-insertion-order-quiz.
8. **Composite keys / future:** composite-key-strategies, map-vs-record-and-tuple.
9. **ES2025 Set methods:** set-operations-polyfill.

---

## Files (19)

### Foundation
- [object-vs-map-vs-set.md](./object-vs-map-vs-set.md) — Decision table.
- [two-sum-map.md](./two-sum-map.md) — Canonical hash-trick.
- [multiset-counter.md](./multiset-counter.md) — Frequency Map.

### Counter / group
- [first-non-repeating-char.md](./first-non-repeating-char.md) — Two-pass with Counter.
- [group-by.md](./group-by.md) — Array.prototype.groupBy polyfill.
- [group-anagrams.md](./group-anagrams.md) — Map keyed by canonical.

### Cache patterns
- [lru-cache-with-map.md](./lru-cache-with-map.md) — Insertion-order LRU.
- [ttl-map.md](./ttl-map.md) — Lazy vs active eviction.
- [cache-invalidate-by-tag.md](./cache-invalidate-by-tag.md) — Forward+reverse index.

### WeakMap / GC
- [weakmap-memoize.md](./weakmap-memoize.md) — Per-object cache + private state.
- [weakref-finalization-registry.md](./weakref-finalization-registry.md) — ES2021 advanced GC.

### JSON
- [is-object-empty.md](./is-object-empty.md) — O(1) short-circuit.
- [convert-object-to-json-string.md](./convert-object-to-json-string.md) — Polyfill JSON.stringify.
- [json-with-map-replacer.md](./json-with-map-replacer.md) — Round-trip Map/Set/Date.

### Diff / shape
- [object-deep-diff.md](./object-deep-diff.md) — Union keysets + recursion.

### Order quirks
- [ordered-map-insertion-order-quiz.md](./ordered-map-insertion-order-quiz.md) — Object int-like first.

### Composite keys / future
- [composite-key-strategies.md](./composite-key-strategies.md) — Stringify / nested / Symbol.
- [map-vs-record-and-tuple.md](./map-vs-record-and-tuple.md) — Stage 2 future.

### ES2025 Set methods
- [set-operations-polyfill.md](./set-operations-polyfill.md) — intersection / union / difference / etc.

---

## Concept primers

- [`concepts/maps-sets.md`](../../concepts/maps-sets.md) — Map/Set/WeakMap mechanics.
- [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md) — JSON/diff recursion.

---

## Companion sections

- `07-arrays/` — array-dedup, set-ops, structured-clone.
- `09-recursion/` — deep-clone, deep-merge.
- `10-machine-coding-patterns/` — memoize, LRU.
