# Implement `diff(objA, objB)` — Differences Between Two Objects

## Source
- LeetCode #2700 "Differences Between Two Objects": https://leetcode.com/problems/differences-between-two-objects/
- Variants asked at Atlassian, Razorpay, Shopify (deep diff for change tracking, audit logs, optimistic UI patching).

## Why this question matters in interviews
Deep diff is the **stress test of recursion + type discrimination in JavaScript**. It hits: (1) `typeof` vs `Array.isArray` vs `null` checks (the famous `typeof null === 'object'` trap), (2) recursion that bottoms out cleanly on primitives, (3) merging keysets from two objects without losing either side, (4) prototype-chain awareness (using own keys only). Backend engineers see this in event-sourcing systems, JSON-Patch generators, audit/diff logs, and Redux-style reducers. It also reveals whether a candidate writes structured recursive code or hacks something that "works on the happy path."

## Concepts involved

### Syntax to lock in
```js
// LeetCode signature:
//  - If types differ or one side is primitive/different value → return [a, b]
//  - If both are arrays/objects → recurse into shared keys, omit equal subtrees
//  - Equal primitives at a leaf → return {} (empty diff)
function diff(a, b) { /* ... */ }
```

### Runtime / engine behavior
- `typeof null === 'object'` — the most famous JS bug-feature. Always guard `null` explicitly.
- `Array.isArray(x)` is the only correct array detector. `instanceof Array` fails across realms (iframes, vm contexts in Node).
- `Object.keys(obj)` returns **only own enumerable string keys**. Symbols and inherited keys are skipped — usually what you want for diff (we care about user data, not prototype methods).
- For prototype-chain awareness: prefer `Object.keys(a)` over `for...in`, exactly because `for...in` walks the prototype chain.

### Edge cases (interview traps)
1. **`null` vs `undefined`** — `typeof null === 'object'` will lure you into recursing into `null`. Guard at the top: if either side is `null`, treat as primitive.
2. **Different types** — `diff(1, '1')` must return `[1, '1']`, not `{}`. Type mismatch ⇒ replace.
3. **Array vs object same-shape** — `diff([1,2], {0:1, 1:2})`. Both have keys `'0','1'` but they are different *types*. Must return `[arr, obj]`.
4. **Equal primitives** — return `{}` per the LeetCode contract, *not* `undefined`. Some candidates omit the key entirely; the spec wants an empty object so the parent can decide whether to drop it.
5. **Missing keys on one side** — `diff({a:1}, {})` should *not* throw. Walk keys from *both* sides (e.g., `new Set([...keys(a), ...keys(b)])`).
6. **Date / RegExp / Map / Set** — `typeof` returns `'object'` for all. The LeetCode problem ignores these but a senior candidate should mention them: compare with `.getTime()`, `.source + .flags`, etc.
7. **Cycles** — the LeetCode input is acyclic, but in real-world diff you must track visited nodes via `WeakMap` to avoid infinite recursion.
8. **NaN equality** — `NaN !== NaN`. Use `Object.is(a, b)` if you care about `NaN`-equals-`NaN`. The LeetCode tests don't, but interviewers will.

## Brute force approach
"`JSON.stringify(a) === JSON.stringify(b)` to compare, then if different recompute." Wrong on two counts: (1) `JSON.stringify` loses `undefined`, functions, `NaN`, key order isn't guaranteed across versions; (2) it tells you *equal or not* but doesn't produce a structured diff. Drop it.

## Optimal approach
Recursive walk:
1. If types differ, or either is a primitive (incl. `null`), or one is array and the other isn't → return `[a, b]` (the replacement pair).
2. If both are equal primitives → return `{}`.
3. Both are objects (or both arrays): take the **union** of keys from both sides. For each key, recurse. If the child diff is a non-empty object, include it in the parent diff. Drop empty diffs.

Time: O(n) over total nodes. Space: O(d) recursion depth where `d` is nesting depth.

## Solution (JavaScript)

```js
/**
 * @param {*} a
 * @param {*} b
 * @returns {object | [unknown, unknown]}
 *   - [a, b] when the two values cannot be reconciled at this node
 *   - {}      when they are equal primitives (leaf agreement)
 *   - { key: <subdiff>, ... } when both are objects/arrays of the same kind
 */
function diff(a, b) {
  // 1. Leaf-level / type-mismatch checks.
  const aIsObj = a !== null && typeof a === 'object';
  const bIsObj = b !== null && typeof b === 'object';
  const aIsArr = Array.isArray(a);
  const bIsArr = Array.isArray(b);

  // Either side is a primitive (including null) OR arrayness differs
  // → not reconcilable as a structured diff. Return [a, b] / {}.
  if (!aIsObj || !bIsObj || aIsArr !== bIsArr) {
    return Object.is(a, b) ? {} : [a, b];
  }

  // 2. Both are objects of the same kind (array+array or object+object).
  //    Union the keys so we capture additions/removals on either side.
  const out = {};
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);

  for (const k of keys) {
    const sub = diff(a[k], b[k]);
    // Drop keys where the children are equal (sub is the empty diff).
    const isEmpty = !Array.isArray(sub) && Object.keys(sub).length === 0;
    if (!isEmpty) out[k] = sub;
  }

  return out;
}
```

## Step-by-step dry run

Input:
```js
const A = { a: 1, b: { c: 2, d: [1, 2] }, e: 'hi' };
const B = { a: 1, b: { c: 9, d: [1, 2] }, f: 'new' };
diff(A, B);
```

Walk:
1. `diff(A, B)` — both objects, not arrays. Key union: `{a, b, e, f}`.
2. `a`: `diff(1, 1)` → primitives, `Object.is(1,1)` true → `{}` → dropped.
3. `b`: `diff({c:2, d:[1,2]}, {c:9, d:[1,2]})` — both objects. Key union: `{c, d}`.
   - `c`: `diff(2, 9)` → `[2, 9]` (replacement pair).
   - `d`: `diff([1,2], [1,2])` — both arrays. Keys `{0, 1}`.
     - `0`: `diff(1, 1)` → `{}` → drop.
     - `1`: `diff(2, 2)` → `{}` → drop.
     - Returns `{}` → parent drops the `d` key.
   - Sub-result for `b` is `{ c: [2, 9] }` → kept.
4. `e`: `diff('hi', undefined)` → primitive vs primitive, not equal → `['hi', undefined]`.
5. `f`: `diff(undefined, 'new')` → `[undefined, 'new']`.

Final:
```js
{
  b: { c: [2, 9] },
  e: ['hi', undefined],
  f: [undefined, 'new'],
}
```

Note how equal subtrees collapse to nothing, and additions/removals naturally surface as `[undefined, x]` / `[x, undefined]`.

## Important takeaways

**Syntax to memorize**
- `Array.isArray(x)` — **only** correct array test.
- `x !== null && typeof x === 'object'` — the universal "is it a non-null object?" check.
- `new Set([...Object.keys(a), ...Object.keys(b)])` — union of keysets.
- `Object.is(a, b)` — like `===` but treats `NaN === NaN` and distinguishes `+0` from `-0`.

**Patterns to reuse**
- The "leaf vs branch" recursive skeleton: classify the node, recurse on branches, drop empty subtrees as you bubble up.
- Same template solves: deep equality, deep clone, JSON-patch generation, schema validation.

**Common mistakes**
- Forgetting the `null` guard → `typeof null === 'object'` and you recurse into `null` and crash on key access.
- Using `for...in` — walks the prototype chain. If anyone monkey-patched `Object.prototype.foo` (see the previous question), your diff includes `foo`.
- Iterating only `Object.keys(a)` — misses keys present only in `b` (additions).
- Returning `undefined` instead of `{}` for equal leaves — breaks the "drop empty children" filter in the parent.
- Using `JSON.stringify` for equality — loses `undefined`, functions, key order guarantees, and chokes on cycles.

**Why interviewers ask this**
- It surfaces every recursion-on-objects skill in 25 lines: type discrimination, keyset union, structural recursion, idiomatic JS quirks.

## Variants

1. **Cycle-safe deep equal** — same skeleton plus a `WeakMap` of seen pairs to break cycles. Return `true`/`false` instead of a diff structure.
2. **JSON-Patch / RFC 6902** — emit `{op:'replace', path:'/b/c', value: 9}` operations instead of a tree. Useful in real-world APIs (k8s, Stripe).
3. **Merge / 3-way merge** — given `base`, `local`, `remote`, produce a merged object and a conflict list. Same recursion shape, different combine logic.
4. **Date / RegExp / Map / Set support** — extend the leaf check: if both are `Date`, compare `.getTime()`. Mention this even if not implemented — shows real-world awareness.

## Revision notes

> **diff(a, b) — 60 second recap**
> - Two-case recursion: leaf (primitives or type mismatch) vs branch (both same-kind objects).
> - Leaf: `Object.is(a,b) ? {} : [a, b]`.
> - Branch: union keys from both sides, recurse, drop children with empty diff.
> - Guard `null` explicitly — `typeof null === 'object'` is the classic trap.
> - `Array.isArray(x)` is the only safe array check; `arr instanceof Array` fails across realms.
> - `Object.keys` ≠ `for...in`; the former skips inherited and symbol keys (what you want for diff).
> - Real-world extensions: Date/RegExp/Map/Set leaves, cycle tracking via WeakMap, NaN equality via `Object.is`.
> - JSON-stringify shortcut is **wrong** (loses `undefined`, functions, key order).
> - **Trap:** forgetting that one side may not have a given key — always union both keysets.
> - Time O(n nodes), space O(depth).
