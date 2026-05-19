# Implement `diff(a, b)` — deep difference of two objects

> **Difficulty:** Medium   |   **Time:** ~15 min   |   **Prereqs:** [is-object-empty.md](./is-object-empty.md), [`09-recursion/deep-merge-with-cycles.md`](../09-recursion/deep-merge-with-cycles.md)
>
> **Source:** LeetCode #2700. Audit logs, API comparison, JSON patch.

---

## 1. Problem statement

Walk two objects, recurse on nested values, report `[old, new]` at leaves where they differ. Union of keysets.

**Verification examples**

```js
diff({a: 1, b: 2}, {a: 1, b: 3});                // {b: [2, 3]}
diff({a: {x: 1}}, {a: {x: 2}});                  // {a: {x: [1, 2]}}
diff({a: 1}, {a: 1});                            // {}
diff({a: 1, b: 2}, {a: 1});                      // {b: [2, undefined]}
diff([1, 2], [1, 3]);                            // {1: [2, 3]}
diff([1, 2], {0: 1, 1: 2});                      // [[1,2], {0:1, 1:2}] (type differ)
```

**Constraints**
- Union of keys (don't miss b-only keys).
- Leaves where different → `[a, b]` tuple.
- No-diff subtree → `{}`.
- Type mismatch (array vs object) → whole differs.
- `null` is `typeof === 'object'` — guard.

---

## 2. Plain-English restatement

Recursive walk. At leaves: `a === b ? {} : [a, b]`. At nested: union keysets, recurse, include only non-empty results.

---

## 3. Why this matters in interviews

Exercises Set union over keys, recursion with cycle detection, type discrimination, clean output shape.

---

## 4. Mental model

```
   diff(a, b):
     if typeof differs, or one is primitive, or array-ness differs:
       return a === b ? {} : [a, b]
     
     out = {}
     keys = Set(Object.keys(a) ∪ Object.keys(b))
     for k of keys:
       sub = diff(a[k], b[k])
       if sub is [a, b] or has keys → out[k] = sub
     return out
   
   Leaf rule:
     a === b: empty diff {}.
     else: tuple [a, b].
   
   Output shape:
     LeetCode contract: leaves are 2-tuples, parents are objects.
     Empty object means "no diff at this subtree."
   
   Cycle safety:
     WeakMap<a, WeakSet<b>> of seen pairs.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why Set union over keys?
> 2. `null` handling?
> 3. Array vs object differ — what's the output?

---

## 6. Brute force — walked through

```js
function brute(a, b) {
  if (typeof a !== typeof b) return [a, b];
  if (typeof a !== 'object' || a === null || b === null) {
    return a === b ? {} : [a, b];
  }
  const out = {};
  // BUG: only walks a's keys — misses b-only keys.
  for (const k of Object.keys(a)) {
    const sub = brute(a[k], b[k]);
    if (Array.isArray(sub) || Object.keys(sub).length) out[k] = sub;
  }
  return out;
}
```

Misses keys in `b` not in `a`.

---

## 7. The unlocking insight

> **Recursive walk; union keysets at each level; leaves are tuples `[a, b]`; parents are objects; empty `{}` = no diff.**

Three properties:

1. **Union keysets** — Set(a.keys ∪ b.keys).
2. **Leaf rule:** `===` → `{}`; else `[a, b]`.
3. **Type mismatch** at non-leaf → whole subtree differs.

---

## 8. Solution (annotated)

```js
const isPrim = (v) => v === null || typeof v !== 'object';

function diff(a, b, seen = new WeakMap()) {
  // Cycle safety
  if (!isPrim(a) && !isPrim(b)) {
    if (seen.get(a)?.has(b)) return {};                                    // step 1: cycle
    if (!seen.has(a)) seen.set(a, new WeakSet());
    seen.get(a).add(b);
  }

  // Type mismatch or primitive
  if (
    typeof a !== typeof b ||
    isPrim(a) || isPrim(b) ||
    Array.isArray(a) !== Array.isArray(b)
  ) {
    return a === b ? {} : [a, b];                                          // step 2: leaf
  }

  // Both same-shape object/array — union keysets
  const out = {};
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);           // step 3: union
  for (const k of keys) {
    const sub = diff(a[k], b[k], seen);                                   // step 4: recurse
    if (Array.isArray(sub) || Object.keys(sub).length) {
      out[k] = sub;                                                        // step 5: keep non-empty
    }
  }
  return out;
}
```

**Try it yourself**

```js
diff({a: 1, b: 2}, {a: 1, b: 3});                            // {b: [2, 3]}
diff({a: {x: 1, y: 2}}, {a: {x: 1, y: 3}});                  // {a: {y: [2, 3]}}
diff({a: 1}, {a: 1});                                         // {}
diff({a: 1, b: 2}, {a: 1});                                   // {b: [2, undefined]}
diff(null, {a: 1});                                            // [null, {a:1}]
diff([1, 2, 3], [1, 4, 3]);                                  // {1: [2, 4]}
diff([1, 2], {0: 1, 1: 2});                                   // [[1,2], {0:1, 1:2}]

// JSON-Patch RFC 6902 variant
function jsonPatch(a, b, path = '') {
  if (a === b) return [];
  if (isPrim(a) || isPrim(b) || typeof a !== typeof b || Array.isArray(a) !== Array.isArray(b)) {
    return [{ op: 'replace', path, value: b }];
  }
  const ops = [];
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  for (const k of keys) {
    const subPath = `${path}/${k}`;
    if (!(k in a)) ops.push({ op: 'add', path: subPath, value: b[k] });
    else if (!(k in b)) ops.push({ op: 'remove', path: subPath });
    else ops.push(...jsonPatch(a[k], b[k], subPath));
  }
  return ops;
}
```

---

## 9. Step-by-step dry run

```
diff({a: 1, b: {x: 2}}, {a: 1, b: {x: 3, y: 4}}):

Top: both objects, same array-ness.
  keys = Set{'a', 'b'}.
  
  k='a': diff(1, 1):
    Primitive, equal → {}.
    {} not Array, no keys → don't include in out.
  
  k='b': diff({x:2}, {x:3, y:4}):
    Both objects.
    keys = Set{'x', 'y'}.
    
    k='x': diff(2, 3):
      Primitive, not equal → [2, 3].
    
    k='y': diff(undefined, 4):
      typeof differs (undefined vs number).
      Both primitives.
      undefined !== 4 → [undefined, 4].
    
    out_b = {x: [2, 3], y: [undefined, 4]}.
  
  out_b has keys → include in top.
  
  Final: {b: {x: [2, 3], y: [undefined, 4]}}.

diff(null, {a:1}):
  isPrim(null) true.
  typeof null === 'object', typeof {a:1} === 'object'.
  But isPrim(null) || isPrim(b)? isPrim(null) is true.
  Branch fires → null === {a:1}? No → return [null, {a:1}].

diff([1,2], {0:1, 1:2}):
  Both typeof 'object'.
  Array.isArray differs → branch fires.
  [1,2] === {0:1,1:2}? No → return [[1,2], {0:1,1:2}].
```

---

## 10. Common confusion + traps

1. **Walk only `a`'s keys** — miss b-only.
2. **`null` is `typeof === 'object'`** — guard with isPrim.
3. **Array vs object** — explicit check.
4. **Output shape** — leaves `[a, b]`, parents `{}` for no-diff.
5. **Cycles** — WeakMap pair tracking.
6. **`Date`/`RegExp`** — treated as objects; would walk enumerable props (empty); === check would still pass for same ref. Decide policy.
7. **Empty object vs no-diff** — disambiguate via spec.

---

## 11. Senior follow-ups & variants

### Variant 1 — JSON-Patch RFC 6902
Output ops: add/remove/replace with paths.

### Variant 2 — Path-keyed output
`{'a.b.c': [old, new]}` — flatter for log lines.

### Variant 3 — `_.isEqualWith`
Lodash with custom comparator.

### Variant 4 — Apply diff
Reverse: `apply(a, diff) === b`.

### Variant 5 — Streaming diff
For huge objects; yield ops lazily.

---

## 12. How to think aloud

> "Object deep-diff: walk both, union keysets at each level, recurse on values. Leaf rule: `a === b ? {} : [a, b]` — empty object means 'no diff here,' tuple means 'differ.' Parent rule: collect non-empty sub-diffs into an object. Critical: must union `Object.keys(a) ∪ Object.keys(b)` — walking only `a`'s keys misses keys removed in `b` (or added in `b` only). Type discrimination: `null` is `typeof === 'object'` so guard with an `isPrim` helper (`v === null || typeof v !== 'object'`); also check `Array.isArray(a) !== Array.isArray(b)` to treat array-vs-object as whole-differ. Cycle safety: WeakMap<a, WeakSet<b>> tracking seen pairs — if revisit same pair, treat as equal (assume same subtree). Output shape options: (1) recursive `{key: [a, b] | nested}` (LeetCode #2700); (2) JSON-Patch RFC 6902 — `[{op: 'replace', path: '/a/b', value: x}, ...]` for transmission; (3) path-keyed flat — `{'a.b.c': [old, new]}` for log lines. Lodash `_.isEqualWith` for custom comparator. Trap: walking only a's keys; null type-of; array vs object same-typeof; cycles."

---

## 13. 60-second revision

> - **Union keysets** at each level (don't miss b-only).
> - **Leaf:** `a === b ? {} : [a, b]`.
> - **Parent:** include non-empty sub-diffs.
> - **`null` is object-typed** — isPrim guard.
> - **`Array.isArray(a) !== Array.isArray(b)`** → whole differ.
> - **Cycles:** WeakMap<a, WeakSet<b>>.
> - **JSON-Patch RFC 6902** for transmission.
> - **Apply diff = inverse.**
> - **Trap:** only walk a; null typeof; array vs object.

---

**Related:** [is-object-empty.md](./is-object-empty.md) · [convert-object-to-json-string.md](./convert-object-to-json-string.md) · [`07-arrays/structured-clone-vs-spread.md`](../07-arrays/structured-clone-vs-spread.md) · [`09-recursion/deep-merge-with-cycles.md`](../09-recursion/deep-merge-with-cycles.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md), [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
