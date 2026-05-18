# Deep Merge with Cycles

## Source / Origin
- `lodash.merge`; common utility with subtle edge cases.
- Asked at: Razorpay, Atlassian, Stripe.
- Concept reference: `concepts/recursion.md`, sibling `10-machine-coding-patterns/deep-clone-with-cycles.md`.

## Why this question matters in interviews
"Merge config objects deeply." Tests recursion, identity tracking, type discrimination, and policy choices (arrays: concat or replace?). Senior bar: you handle cycles via WeakMap of visited pairs, document array policy, and reject prototype-pollution keys.

## Concepts involved

```js
function deepMerge(target, source, opts = {}) {
  const { arrayMerge = 'replace', skipUndefined = false } = opts;
  const seen = new WeakMap();
  function merge(t, s) {
    if (s === null || typeof s !== 'object') return s;
    if (Array.isArray(s)) {
      if (arrayMerge === 'concat') return Array.isArray(t) ? t.concat(s) : s.slice();
      if (arrayMerge === 'replace') return s.slice();
      if (arrayMerge === 'index') {
        const out = Array.isArray(t) ? t.slice() : [];
        s.forEach((v, i) => { out[i] = merge(out[i], v); });
        return out;
      }
    }
    if (s instanceof Map) return new Map(s);
    if (s instanceof Set) return new Set(s);
    if (s instanceof Date) return new Date(s);
    if (seen.has(s)) return seen.get(s);
    const result = (t && typeof t === 'object' && !Array.isArray(t)) ? { ...t } : {};
    seen.set(s, result);
    for (const key of Object.keys(s)) {
      if (['__proto__', 'prototype', 'constructor'].includes(key)) continue;
      const sv = s[key];
      if (skipUndefined && sv === undefined) continue;
      result[key] = merge(result[key], sv);
    }
    return result;
  }
  return merge(target, source);
}
```

### Edge cases / traps
1. **Cycles**: `s.self = s` — without WeakMap of visited, infinite loop. WeakMap from source → result.
2. **Array merge policy** — replace (default), concat, index-merge. Document.
3. **Date / Map / Set / RegExp** — special types; copy, don't recurse into.
4. **Prototype pollution** — reject `__proto__`, `prototype`, `constructor`.
5. **null vs undefined** — undefined source: keep target? or wipe? Provide `skipUndefined` knob.
6. **Functions** — keep by reference, don't try to merge.
7. **Class instances** — same as plain objects, but be wary of prototype-preservation expectations.
8. **Symbol keys** — `Object.keys` skips them; use `Reflect.ownKeys` if needed.

## Mental Model

```
   target:  { a: 1, b: { c: 2 } }
   source:  { b: { d: 3 }, e: 4 }

   merge:   walk source keys
            if both target[k] and source[k] are plain objects → recurse
            else → source[k] wins (or merge by policy)

   result:  { a: 1, b: { c: 2, d: 3 }, e: 4 }

   cycle:   source.self = source
            seen.set(source, partialResult)
            when we encounter source.self again → return partialResult (avoid loop)
```

## Solution

See "Syntax to lock in" above. Usage examples:

```js
// Basic
deepMerge({ a: { x: 1 } }, { a: { y: 2 } });
// { a: { x: 1, y: 2 } }

// Array policy
deepMerge({ a: [1, 2] }, { a: [3, 4] });                  // { a: [3, 4] } (replace)
deepMerge({ a: [1, 2] }, { a: [3, 4] }, { arrayMerge: 'concat' });  // { a: [1,2,3,4] }
deepMerge({ a: [1, 2, 3] }, { a: [9, undefined, 8] }, { arrayMerge: 'index' });
// { a: [9, 2, 8] } — index-merge keeps target where source has undefined

// Cyclic source
const s = { x: 1 };
s.self = s;
const r = deepMerge({}, s);
r === r.self;    // true (cycle preserved)

// Skip undefined sources (don't wipe target)
deepMerge({ a: 1, b: 2 }, { a: undefined, c: 3 }, { skipUndefined: true });
// { a: 1, b: 2, c: 3 }

// Multiple sources
function deepMergeAll(target, ...sources) {
  return sources.reduce((acc, s) => deepMerge(acc, s), target);
}
```

## Dry run

```
target = {a:1, b:{c:2}}
source = {b:{d:3}, e:4}

merge(target, source):
  source is object, not array
  seen.set(source, result={...target}={a:1, b:{c:2}})
  walk source keys: ['b', 'e']
    key 'b': sv={d:3}; result.b = merge(result.b={c:2}, {d:3})
      merge({c:2}, {d:3}): object recurse
      seen.set({d:3}, {c:2})  (note: result starts as copy of target.b)
      walk: key 'd': sv=3; not object; result.d = 3
      return {c:2, d:3}
    key 'e': sv=4; not object; result.e = 4
  return {a:1, b:{c:2,d:3}, e:4}
```

Cycle case:

```
s = {x:1}; s.self = s
deepMerge({}, s):
  merge({}, s): not seen
  seen.set(s, r={})
  walk: key 'x': r.x = 1
  walk: key 'self': sv = s
    merge(undefined, s): s is in seen → return seen.get(s) = r
  r.self = r
  return r → r.self === r ✓
```

## How to think aloud

> "Recursive merge with three policy knobs: array merge (replace/concat/index), skip undefined, and prototype-key rejection. WeakMap of visited sources to handle cycles — set the entry *before* recursing into children so cycles resolve to the partial result. Special-case Date/Map/Set/RegExp — copy, don't merge. Document the array policy clearly; that's where most users get bitten."

## Important takeaways

- **WeakMap for cycle detection** (set entry *before* recurse).
- **Array policy is a knob** — replace by default, concat or index as options.
- **Reject prototype keys** — `__proto__`, `prototype`, `constructor`.
- **Date/Map/Set/RegExp**: copy, don't recurse.
- **`skipUndefined` option** to preserve target on undefined source.

## Variants

- **Immer** for immutable updates with proxies.
- **Lodash `_.mergeWith(target, source, customizer)`** — per-key override.
- **Object.assign** for shallow.
- **`structuredClone` + merge** for deep-copy-then-merge.

## Revision notes

```
deepMerge(target, source, opts):
  WeakMap seen for cycles
  recurse on plain objects
  policy: arrayMerge ∈ {replace, concat, index}
  skipUndefined optional
  reject __proto__, prototype, constructor
  Date/Map/Set: copy, don't recurse

cycle handling:
  seen.set(source, result) BEFORE walking children
  return seen.get(source) on revisit

multiple sources:
  reduce(deepMerge, target, ...sources)
```
