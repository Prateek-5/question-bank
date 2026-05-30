# Implement `diff(a, b)` — deep object differences

> **Difficulty:** Medium-Senior   |   **Time:** ~15 min   |   **Prereqs:** [`concepts/recursion.md`](../../concepts/recursion.md), [`10-machine-coding-patterns/deep-clone-with-cycles.md`](../10-machine-coding-patterns/deep-clone-with-cycles.md)
>
> **Source:** <a href="https://leetcode.com/problems/differences-between-two-objects/" target="_blank" rel="noopener noreferrer">LeetCode 2700 — Differences Between Two Objects</a>. Atlassian, Razorpay, Shopify.

---

## 1. Problem statement

`diff(a, b)` returns nested object showing differences. Equal subtrees → empty `{}`. Different leaves → `[a, b]`.

**Verification examples**

```js
diff(1, 2);                                                              // [1, 2]
diff(1, 1);                                                              // {}
diff({a: 1}, {a: 2});                                                    // {a: [1, 2]}
diff({a: 1, b: 2}, {a: 1, c: 3});                                        // {b: [2, undefined], c: [undefined, 3]}
diff({a: {b: 1}}, {a: {b: 2}});                                          // {a: {b: [1, 2]}}
diff([1, 2], [1, 3]);                                                    // {'1': [2, 3]}
diff(1, '1');                                                            // [1, '1'] (different types)
diff(null, {a: 1});                                                      // [null, {a: 1}]
diff([1, 2], {0: 1, 1: 2});                                              // [[1,2], {0:1, 1:2}] (different types)
```

**Constraints**
- `typeof null === 'object'` trap — guard explicitly.
- `Array.isArray` is only correct array detector (cross-realm safe).
- `Object.keys` for own enumerable (not `for...in`).
- Different types → replace; same type non-primitive → recurse.

---

## 2. Plain-English restatement

Recursively compare two values. Primitives or different types → return `[a, b]` (or `{}` if equal). Both arrays or both objects → recurse into shared/unique keys. Equal subtrees become `{}`.

---

## 3. Why this matters in interviews

Stress test of recursion + type discrimination. Tests `null` handling + `Array.isArray` + own keys discipline.

---

## 4. Mental model

```
   diff(a, b):
   
   1. If primitive or different types or null:
        a === b ? {} : [a, b]
   
   2. If both objects/arrays:
        result = {}
        keys = union(Object.keys(a), Object.keys(b))
        for each key:
          subDiff = diff(a[key], b[key])
          if subDiff is not empty: result[key] = subDiff
        return result
   
   Empty subtree means "equal here, no change to record".
   
   Type discrimination:
   - typeof null === 'object' → guard explicitly.
   - Array.isArray(x) for arrays.
   - Different types → [a, b] without recursion.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `diff({a: 1}, {a: 1})` return?
> 2. What does `diff({a: 1}, {b: 1})` return?
> 3. What does `diff([1,2], {0:1, 1:2})` return?

---

## 6. Brute force — walked through

### Wrong attempt 1: ignore null
`typeof null === 'object'` → recurses into null → crash.

### Wrong attempt 2: `for...in`
Walks prototype chain; includes inherited.

### Wrong attempt 3: assume same shape
`[1,2]` vs `{0:1, 1:2}` — different types, must return as different.

---

## 7. The unlocking insight

> **Recursive diff. At each level: same type + both non-primitive → recurse keys union. Different types or both primitives → `[a, b]` if unequal, `{}` if equal. Guard `null` explicitly. Use `Array.isArray` + `Object.keys`.**

Three properties:

1. **Type-discriminated recursion.**
2. **`null` guard explicit.**
3. **`Array.isArray` + `Object.keys`** — cross-realm safe + own only.

---

## 8. Solution (annotated)

```js
function diff(a, b) {
  if (isPrimitive(a) || isPrimitive(b) || !sameType(a, b)) {            // step 1: leaf
    return a === b ? {} : [a, b];
  }
  
  // Both arrays or both objects
  const result = {};
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);          // step 2: union keys
  
  for (const k of keys) {
    const sub = diff(a[k], b[k]);                                        // step 3: recurse
    if (!isEmpty(sub)) result[k] = sub;                                  // step 4: skip equal
  }
  return result;
}

function isPrimitive(v) {
  return v === null || (typeof v !== 'object' && typeof v !== 'function');
}

function sameType(a, b) {
  if (Array.isArray(a) !== Array.isArray(b)) return false;               // arr vs obj are different
  if (typeof a !== typeof b) return false;
  return true;
}

function isEmpty(o) {
  return typeof o === 'object' && !Array.isArray(o) && Object.keys(o).length === 0;
}
```

**Try it yourself**

```js
diff(1, 2);                                                              // [1, 2]
diff(1, 1);                                                              // {}
diff({a: 1}, {a: 2});                                                    // {a: [1, 2]}
diff({a: 1, b: 2}, {a: 1, c: 3});                                        // {b: [2, undefined], c: [undefined, 3]}
diff({a: {b: 1, c: 2}}, {a: {b: 1, c: 3}});                              // {a: {c: [2, 3]}}
diff([1, 2, 3], [1, 9, 3]);                                              // {'1': [2, 9]}
diff(null, {a: 1});                                                      // [null, {a:1}]
diff({a: null}, {a: 1});                                                 // {a: [null, 1]}
diff(1, '1');                                                            // [1, '1']
diff([1, 2], {0: 1, 1: 2});                                              // [[1,2], {0:1, 1:2}]
```

---

## 9. Step-by-step dry run

```
diff({a: {b: 1, c: 2}}, {a: {b: 1, c: 3}}):
  a not primitive, b not primitive. sameType (both objects). Recurse.
  keys union: {'a'}.
  diff(a.a, b.a) = diff({b:1, c:2}, {b:1, c:3}):
    both objects. keys union: {'b', 'c'}.
    diff(1, 1) → primitives, equal → {}.
    diff(2, 3) → primitives, unequal → [2, 3].
    result = {c: [2, 3]} (b skipped — equal).
  result = {a: {c: [2, 3]}}.

diff(1, '1'):
  Both primitive (typeof 'number', 'string').
  sameType → typeof differs → false.
  Return [1, '1'].

diff([1,2], {0:1, 1:2}):
  Both non-primitive but Array.isArray differs → sameType false.
  Return [[1,2], {0:1,1:2}].
```

---

## 10. Common confusion + traps

1. **`typeof null === 'object'`** — recurses into null; guard explicitly.
2. **`for...in`** — walks chain; use `Object.keys`.
3. **`instanceof Array`** — fails cross-realm; use `Array.isArray`.
4. **Assume same shape** — `[]` vs `{}` are different types.
5. **Missing keys** — one side has `undefined`; diff returns `[value, undefined]`.
6. **Empty subtree** — return `{}` and SKIP at parent (or include — depends on contract).
7. **Cyclic objects** — infinite recursion; LeetCode usually doesn't test, but add WeakMap for production.

---

## 11. Senior follow-ups & variants

### Variant 1 — JSON Patch (RFC 6902)
Generate `{op: 'replace', path, value}` ops instead of nested diff.

### Variant 2 — Cyclic refs
Add `WeakMap` of visited pairs.

### Variant 3 — Custom equality
Pass `eq` function for floats with tolerance, dates, etc.

### Variant 4 — Apply patch
`applyDiff(obj, diff)` reverse operation.

### Variant 5 — Performance
For large objects, stream key-by-key or use specialized libs (`fast-json-patch`).

---

## 12. How to think aloud

> "Recursive diff. At each level: if either side is primitive OR types differ (null guard! Array.isArray check!), return `[a, b]` if unequal, `{}` if equal. If both are same type and non-primitive (both arrays or both objects), recurse over the UNION of their keys. For each key, recurse; if result is non-empty, add to current result. Empty results are skipped — that's how we represent 'no change here'. Type discrimination is the trickiest: `typeof null === 'object'` is the classic JS bug — guard null explicitly. `Array.isArray` is the only cross-realm-safe array detector (`instanceof Array` fails across iframes). Use `Object.keys` not `for...in` — own enumerable, no chain walk. Trap: null recursion; for...in; assuming `[]` vs `{}` same; cyclic refs (add WeakMap for production)."

---

## 13. 60-second revision

> - **Recursive type-discriminated diff.**
> - **Primitive or different types** → `[a, b]` (or `{}` if equal).
> - **Same type non-primitive** → recurse keys UNION.
> - **`null` guard explicit** — `typeof null === 'object'`.
> - **`Array.isArray`** for arrays (cross-realm safe).
> - **`Object.keys`** for own enumerable (not for...in).
> - **Empty subtree → skip** at parent.
> - **Cycles:** WeakMap for production.
> - **Trap:** null; for...in; instanceof Array; cyclic refs.

---

**Related:** [`10-machine-coding-patterns/deep-clone-with-cycles.md`](../10-machine-coding-patterns/deep-clone-with-cycles.md) · [`concepts/recursion.md`](../../concepts/recursion.md) · [`08-maps-sets/deep-equal.md`](../08-maps-sets/deep-equal.md)

**Concept primer:** [`concepts/prototype.md`](../../concepts/prototype.md), [`concepts/recursion.md`](../../concepts/recursion.md)
