# Implement `diff(a, b)` — deep difference of two objects

## Source
- LeetCode #2700 "Differences Between Two Objects" — https://leetcode.com/problems/differences-between-two-objects/
- Variants: lodash `_.isEqualWith` / `_.differenceWith`, json-patch RFC 6902.

## Why this question matters in interviews
Object diff is the natural escalation from "is this empty?" — you walk **two** keysets, recurse on nested values, and report **what changed**. It's a small problem that exercises a surprising stack: `Set` union over keys, recursion with cycle detection via `WeakMap`, type-discrimination (primitive vs array vs object), and clean output shape (path-keyed vs nested). Backend engineers use this constantly: comparing API responses, generating audit logs, building config-change diffs for deploys, computing JSON patches for syncing. The interviewer is also checking whether you'll **`Object.keys` the union** (correct) versus only one side (subtly wrong — misses keys removed in `b`).

## Concepts involved

### Syntax to lock in
```js
function diff(a, b) {
  // Different types or one is primitive -> the whole thing differs.
  if (typeof a !== typeof b || isPrim(a) || isPrim(b) || Array.isArray(a) !== Array.isArray(b)) {
    return a === b ? {} : [a, b];
  }
  const out = {};
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  for (const k of keys) {
    const sub = diff(a[k], b[k]);
    if (Array.isArray(sub) || (sub && Object.keys(sub).length)) {
      out[k] = sub;
    }
  }
  return out;
}
const isPrim = (v) => v === null || typeof v !== 'object';
```

### Runtime / engine behavior
- The LeetCode contract uses a **discriminator output**: leaves where `a !== b` become `[a, b]` (a 2-tuple), and parents recursively become nested objects keyed by the same path. An empty object `{}` means "no diff at this subtree."
- `new Set([...Object.keys(a), ...Object.keys(b)])` — classic **union over keysets**. `Set` dedupes for free. Walking only `Object.keys(a)` would miss keys that exist in `b` but not `a`.
- For cycle safety in real code, pair each visit with a `WeakMap<a, WeakSet<b>>` of seen `(a, b)` pairs. (LeetCode tests don't include cycles, but mention it.)
- Property order in the output: keys are inserted in iteration order of the `Set`, which is insertion order — `a`'s keys first, then any `b`-only keys.

### Edge cases (these are the interview traps)
1. **`null` is `typeof === 'object'`** — must short-circuit `null`/`undefined` before recursing. `diff(null, {a: 1})` should return `[null, {a:1}]`, not crash.
2. **Array vs object mismatch** — `diff([1,2], {0:1, 1:2})` should treat them as different (one is array, one isn't). Check `Array.isArray(a) !== Array.isArray(b)` early.
3. **Arrays of different length** — your code walks the union of indices. Missing indices become `undefined` on one side → leaf diff `[1, undefined]` or `[undefined, 2]`. Acceptable for LeetCode; real diffs use LCS / json-patch.
4. **NaN equality** — `NaN !== NaN`. If you want "NaN equals NaN" semantics, use `Object.is(a, b)` at the leaf check.
5. **Order sensitivity for arrays** — `diff([1,2,3], [3,2,1])` reports diffs at indices 0 and 2. Expected, but worth flagging.
6. **Cycles** — `a.self = a`. Naïve recursion stack-overflows. Add `WeakMap` seen-pair tracking.
7. **Same reference shortcut** — `if (a === b) return {}` saves work on shared subtrees.
8. **Special types** — `Date`, `RegExp`, `Map`, `Set`. The naive walk treats them as plain objects; usually wrong. For LeetCode, assume JSON-shaped input.
9. **Symbol keys** — `Object.keys` skips them. If you need them, also union `Object.getOwnPropertySymbols`.

## Brute force approach
`JSON.stringify(a) === JSON.stringify(b)` to detect equality, then bisect to find the differing path. O(n) string compare gives boolean only — useless for reporting *what* differs. Also lies about key order (`{a:1,b:2}` vs `{b:2,a:1}` stringify differently in some engines).

## Optimal approach
Single recursive walk. At each node:
1. Reference-equal? Return empty diff.
2. Either is primitive (or type mismatch)? Return the leaf tuple `[a, b]` if unequal, else empty.
3. Both are objects/arrays of the matching kind? Build a `Set` union of keys, recurse on each, collect only the non-empty sub-diffs.

Time: O(n) where n is total nodes in the union. Space: O(d) recursion + O(k) for the seen-set if cycles are handled.

## Solution (JavaScript)

```js
/**
 * Deep diff of two values.
 * Leaves where a !== b -> [a, b].
 * Internal nodes -> object of same shape with only differing keys.
 * Same value (deep-equal) at any subtree -> omitted from the parent.
 *
 * @param {unknown} a
 * @param {unknown} b
 * @returns {object | [unknown, unknown]}
 */
function diff(a, b) {
  const seen = new WeakMap();   // a -> WeakSet<b>, cycle guard

  function isPrim(v) {
    return v === null || typeof v !== 'object';
  }

  function walk(a, b) {
    // Identity short-circuit (also handles NaN if you swap in Object.is)
    if (a === b) return EMPTY;

    // Type mismatch or one is primitive -> leaf diff
    if (isPrim(a) || isPrim(b) || Array.isArray(a) !== Array.isArray(b)) {
      return Object.is(a, b) ? EMPTY : [a, b];
    }

    // Cycle guard: if (a, b) already in flight, treat as equal subtree
    let set = seen.get(a);
    if (set && set.has(b)) return EMPTY;
    if (!set) { set = new WeakSet(); seen.set(a, set); }
    set.add(b);

    const out = {};
    const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
    for (const k of keys) {
      const sub = walk(a[k], b[k]);
      if (sub !== EMPTY) out[k] = sub;
    }
    return Object.keys(out).length ? out : EMPTY;
  }

  const EMPTY = {};
  const result = walk(a, b);
  return result === EMPTY ? {} : result;
}
```

## Step-by-step dry run

Input:
```js
const a = { x: 1, y: { a: 2, b: 'old' }, z: [1, 2, 3] };
const b = { x: 1, y: { a: 2, b: 'new' }, z: [1, 4, 3], extra: true };

diff(a, b);
```

Trace:
1. Top call. Both are objects, neither is array. Union keys: `{x, y, z, extra}`.
2. `x`: both `1`. `walk(1, 1)` → `a === b` → `EMPTY`. Skip.
3. `y`: both objects. Recurse. Union keys: `{a, b}`.
   - `a`: both `2`. `EMPTY`. Skip.
   - `b`: `'old'` vs `'new'`. Both primitive, unequal → return `['old', 'new']`. Push into `out.b`.
   - Return `{ b: ['old', 'new'] }`. Push into `out.y`.
4. `z`: both arrays. Recurse. Union indices: `{'0', '1', '2'}`.
   - `'0'`: both `1`. Skip.
   - `'1'`: `2` vs `4`. Return `[2, 4]`. Push into `out['1']`.
   - `'2'`: both `3`. Skip.
   - Return `{ '1': [2, 4] }`. Push into `out.z`.
5. `extra`: `undefined` vs `true`. Both primitive, unequal → return `[undefined, true]`. Push into `out.extra`.
6. Top-level result:
```js
{
  y: { b: ['old', 'new'] },
  z: { '1': [2, 4] },
  extra: [undefined, true],
}
```

## Important takeaways

**Syntax to memorize**
- `new Set([...Object.keys(a), ...Object.keys(b)])` — union of two keysets.
- `Array.isArray(a) !== Array.isArray(b)` — detect array-vs-object mismatch.
- `null`-check **before** `typeof === 'object'`.
- `Object.is(a, b)` for `NaN`-safe leaf compare.
- `WeakMap<a, WeakSet<b>>` for cycle guard.

**Patterns to reuse**
- Set-union over keysets is the same shape as: deep-equal, deep-merge, deep-clone-with-overrides, structuredClone polyfill.
- `EMPTY` sentinel returned up the call stack to signal "skip me" — cleaner than threading an `omit` flag.

**Common mistakes**
- Walking only `Object.keys(a)` — misses keys that exist only in `b`. Top reason candidates fail this question.
- Forgetting `null` is `typeof === 'object'` → recursing into `null` → crash.
- Treating arrays like objects with no index check — `diff([1,2,3], {})` should be a wholesale leaf, not "key 0,1,2 missing."
- Returning the same `{}` literal both as "empty diff" and as a real result — using a `EMPTY` sentinel via reference compare disambiguates cleanly.
- Forgetting cycles. Test with `a.self = a`.

**Related questions**
- Deep equality (`isEqual`) — same walk but returns boolean.
- Deep merge — same walk but combines instead of comparing.
- json-patch (RFC 6902) — output is an array of `{ op, path, value }` operations, replayable.
- `Object.keys` union vs `Reflect.ownKeys` (includes symbols).

## Variants

1. **Path-keyed flat output** — instead of nested objects, output `{ "y.b": ['old', 'new'], "z.1": [2, 4] }`. Easier to scan in logs. Track path string while recursing.

2. **JSON Patch (RFC 6902)** — produce `[{ op: 'replace', path: '/y/b', value: 'new' }, ...]`. Replayable on the source to produce the target. Used by Kubernetes, FHIR, JSON-Patch libraries.

3. **Custom equality / ignore keys** — pass `{ ignore: ['updatedAt'], eq: (a,b) => ... }` for fuzzy compares (timestamps, IDs that don't matter). Common in test-snapshot diffing.

## Revision notes

> **diff — 60 second recap**
> - Recurse with `Set` union of both keysets. Skip same-value subtrees.
> - Leaf format: `[a, b]`. Internal: nested object of only-differing keys.
> - Guards: `null`-check first, `Array.isArray` mismatch is a wholesale diff, `Object.is` for NaN.
> - Cycles: `WeakMap<a, WeakSet<b>>`.
> - **Trap:** walking only `Object.keys(a)` — misses keys in `b` only.
> - Family: `isEqual`, `merge`, `structuredClone`, json-patch — same two-tree walk.
