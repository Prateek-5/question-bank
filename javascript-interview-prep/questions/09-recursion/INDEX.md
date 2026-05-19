# 09 — Recursion

Recursion patterns, flattening, sorting, traversal, parsing, FP idioms. v2 13-section template.

---

## How to study this folder

1. **Foundations:** flatten-array-simple → flatten-with-depth → flatten-deeply-nested-array.
2. **Iteration / safety:** iterative-from-recursive, trampoline-pattern, mutual-recursion-even-odd.
3. **Deep transforms:** deep-clone-with-cycles, deep-merge-with-cycles, json-path-resolver.
4. **Sorts:** merge-sort, quick-sort.
5. **DP entry:** climbing-stairs-memoized.
6. **Backtracking:** backtracking-template, permutations, power-set, generate-parentheses.
7. **Traversals:** tree-bfs-dfs, directory-walk-async, tree-zipper-basics.
8. **Generators:** nested-array-generator-codedamn, nested-array-generator-leetcode.
9. **Parsing:** recursive-descent-parser.

---

## Files (22)

### Foundations
- [flatten-array-simple.md](./flatten-array-simple.md) — One level only.
- [flatten-with-depth.md](./flatten-with-depth.md) — Depth control.
- [flatten-deeply-nested-array.md](./flatten-deeply-nested-array.md) — Recursive vs iterative.

### Iteration / safety
- [iterative-from-recursive.md](./iterative-from-recursive.md) — Explicit stack conversion.
- [trampoline-pattern.md](./trampoline-pattern.md) — V8 no-TCO fix.
- [mutual-recursion-even-odd.md](./mutual-recursion-even-odd.md) — Mutual + trampoline.

### Deep transforms
- [deep-clone-with-cycles.md](./deep-clone-with-cycles.md) — WeakMap + register-before-recurse.
- [deep-merge-with-cycles.md](./deep-merge-with-cycles.md) — lodash.merge + pollution defense.
- [json-path-resolver.md](./json-path-resolver.md) — `lodash.get` / `set`.

### Sorts
- [merge-sort.md](./merge-sort.md) — Stable D&C, O(n log n).
- [quick-sort.md](./quick-sort.md) — In-place + pivot.

### DP entry
- [climbing-stairs-memoized.md](./climbing-stairs-memoized.md) — Naive → memo → O(1) space.

### Backtracking
- [backtracking-template.md](./backtracking-template.md) — Choose/explore/unchoose.
- [permutations.md](./permutations.md) — n!.
- [power-set.md](./power-set.md) — 2^n + bitmask.
- [generate-parentheses.md](./generate-parentheses.md) — Catalan + constraint.

### Traversals
- [tree-bfs-dfs.md](./tree-bfs-dfs.md) — Stack vs queue.
- [directory-walk-async.md](./directory-walk-async.md) — `async function*` + symlink cycles.
- [tree-zipper-basics.md](./tree-zipper-basics.md) — Functional cursor.

### Generators
- [nested-array-generator-codedamn.md](./nested-array-generator-codedamn.md) — `function*` + `yield*`.
- [nested-array-generator-leetcode.md](./nested-array-generator-leetcode.md) — `next/hasNext` class.

### Parsing
- [recursive-descent-parser.md](./recursive-descent-parser.md) — LL(1) expression evaluator.

---

## Concept primers

- [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md) — Recursion mechanics + TCO gap.
- [`concepts/maps-sets.md`](../../concepts/maps-sets.md) — WeakMap for cycle tracking.

---

## Companion sections

- `07-arrays/` — polyfill-flat, structured-clone.
- `08-maps-sets/` — deep-diff, JSON stringify.
- `10-machine-coding-patterns/` — memoize, debounce.
- `06-streams/` — custom-iterator, generators.
