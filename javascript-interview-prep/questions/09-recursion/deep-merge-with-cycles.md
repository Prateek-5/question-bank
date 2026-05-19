# Deep merge with cycles

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [deep-clone-with-cycles.md](./deep-clone-with-cycles.md)
>
> **Source:** `lodash.merge`. Razorpay, Atlassian, Stripe.

---

## 1. Problem statement

Merge config objects deeply. Source overrides target. Handle arrays (merge policy), cycles (WeakMap), prototype-pollution keys.

**Verification examples**

```js
deepMerge({a: 1, b: {x: 1}}, {b: {y: 2}, c: 3});
// {a: 1, b: {x: 1, y: 2}, c: 3}

deepMerge({a: [1, 2]}, {a: [3]});           // {a: [3]} (replace policy default)
deepMerge({a: [1, 2]}, {a: [3]}, {arrayMerge: 'concat'});   // {a: [1, 2, 3]}

// Prototype pollution attempt
deepMerge({}, {__proto__: {polluted: 1}});  // safe (key skipped)
```

**Constraints**
- Source overrides target.
- Array policy: replace (default) / concat / index.
- Skip `__proto__`, `constructor`, `prototype` keys.
- Cycle safety via WeakMap.
- Optional: skip undefined values.

---

## 2. Plain-English restatement

Walk source; for each value: if object, merge recursively into target's same key; else assign. Handle arrays per policy, skip dangerous keys, track cycles.

---

## 3. Why this matters in interviews

Recursion + identity + policy. Senior bar: handle cycles, document array policy, reject `__proto__`.

---

## 4. Mental model

```
   deepMerge(target, source, opts):
     for each key in source:
       skip __proto__, constructor, prototype
       sv = source[key]
       tv = target[key]
       
       if sv is primitive: result[key] = sv
       else if Array.isArray(sv):
         policy decides (replace/concat/index)
       else if Date/Map/Set: clone sv
       else (plain object):
         result[key] = deepMerge(tv ?? {}, sv)
     
     return result
   
   Array policies:
     'replace' (default): sv wins entirely.
     'concat': tv.concat(sv).
     'index': merge element-by-element; sv overrides at each index.
   
   Cycle tracker:
     WeakMap<sourceObj, mergedResult>.
     If source revisited, return cached result.
   
   Prototype pollution:
     {__proto__: {polluted: 1}} → without skip, sets Object.prototype.polluted.
     ALL objects in process now have .polluted. Catastrophic.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Array merge policy default?
> 2. Why skip `__proto__`?
> 3. `deepMerge(undefined, {a: 1})` — what happens?

---

## 6. Brute force — walked through

```js
function brute(t, s) {
  for (const k in s) {       // walks prototype too!
    if (typeof s[k] === 'object') {
      t[k] = brute(t[k] ?? {}, s[k]);
    } else {
      t[k] = s[k];           // overwrites; no policy
    }
  }
  return t;
}
```

Bugs: for..in walks prototype; mutates target; no policy; pollution-vulnerable.

---

## 7. The unlocking insight

> **Recursive walk. Per-key policy. Cycle tracker. Skip dangerous keys. Clone-on-merge for immutability.**

Three properties:

1. **Cycle tracker** WeakMap<source, result>.
2. **Skip `__proto__`** etc. for safety.
3. **Array policy** documented.

---

## 8. Solution (annotated)

```js
const DANGEROUS_KEYS = new Set(['__proto__', 'prototype', 'constructor']);

function deepMerge(target, source, opts = {}) {
  const { arrayMerge = 'replace', skipUndefined = false } = opts;
  const seen = new WeakMap();

  function merge(t, s) {
    if (s === null || typeof s !== 'object') return s;                    // step 1: primitive

    if (Array.isArray(s)) {
      if (arrayMerge === 'concat') return Array.isArray(t) ? t.concat(s) : s.slice();
      if (arrayMerge === 'replace') return s.slice();                      // step 2: array policy
      if (arrayMerge === 'index') {
        const out = Array.isArray(t) ? t.slice() : [];
        s.forEach((v, i) => { out[i] = merge(out[i], v); });
        return out;
      }
    }

    if (s instanceof Map) return new Map(s);
    if (s instanceof Set) return new Set(s);
    if (s instanceof Date) return new Date(s);

    if (seen.has(s)) return seen.get(s);                                   // step 3: cycle

    const result = (t && typeof t === 'object' && !Array.isArray(t)) ? { ...t } : {};
    seen.set(s, result);                                                   // step 4: register first

    for (const key of Object.keys(s)) {
      if (DANGEROUS_KEYS.has(key)) continue;                               // step 5: pollution safety
      const sv = s[key];
      if (skipUndefined && sv === undefined) continue;
      result[key] = merge(result[key], sv);                                // step 6: recurse
    }

    return result;
  }

  return merge(target, source);
}
```

**Try it yourself**

```js
// Basic
deepMerge({a: 1, b: {x: 1}}, {b: {y: 2}, c: 3});
// {a: 1, b: {x: 1, y: 2}, c: 3}

// Array policy
deepMerge({arr: [1, 2]}, {arr: [3]});                         // {arr: [3]}
deepMerge({arr: [1, 2]}, {arr: [3]}, {arrayMerge: 'concat'}); // {arr: [1, 2, 3]}
deepMerge({arr: [1, 2, 3]}, {arr: [9, 99]}, {arrayMerge: 'index'});
// {arr: [9, 99, 3]}

// Prototype pollution defense
const bad = JSON.parse('{"__proto__": {"polluted": true}}');
deepMerge({}, bad);
({}).polluted;                                                 // undefined ✓ (skipped)

// Without defense:
// const obj = {};
// for (const k of Object.keys(bad)) obj[k] = bad[k];
// ({}).polluted === true   ← Object.prototype mutated!

// Cycle in source
const s = { a: 1 }; s.self = s;
const m = deepMerge({}, s);
m.self === m;                                                  // true (cycle in merged)
m.self !== s;                                                  // true (independent)

// Multiple sources
function deepMergeAll(target, ...sources) {
  return sources.reduce((acc, src) => deepMerge(acc, src), target);
}

deepMergeAll({a: 1}, {b: 2}, {c: 3});                         // {a:1, b:2, c:3}
```

---

## 9. Step-by-step dry run

```
deepMerge({a: 1, b: {x: 1}}, {b: {y: 2}, c: 3}):

merge(t, s):
  s is object. Not array/Map/Set/Date. Not seen.
  result = {...t} = {a: 1, b: {x: 1}}.
  seen.set(s, result).
  
  for key 'b' in s:
    sv = {y: 2}. tv = {x: 1}.
    result['b'] = merge({x: 1}, {y: 2}):
      Inner merge:
        result' = {x: 1}. seen.set.
        key 'y': merge(undefined, 2) = 2. result'.y = 2.
        return {x: 1, y: 2}.
    result.b = {x: 1, y: 2}.
  
  for key 'c' in s:
    sv = 3. result.c = 3.
  
  return {a: 1, b: {x: 1, y: 2}, c: 3}.

Pollution attempt:
  bad = JSON.parse('{"__proto__": {"polluted": true}}').
  Object.keys(bad) → ['__proto__']  ← own key (JSON.parse preserves as own).
  Wait, actually JSON.parse may either set __proto__ as own or via setter. In modern Node, JSON.parse sets it as own enumerable.
  
  for key '__proto__': DANGEROUS_KEYS.has → SKIP.
  
  Safe. Object.prototype untouched.

Without defense (the brute force):
  for k in bad: obj[k] = bad[k];
  k='__proto__': obj.__proto__ = {polluted:true}.
  This sets obj's prototype to {polluted:true}.
  {}.polluted now true → catastrophic.

Cycle source:
  s = {a:1}; s.self = s.
  merge(target, s):
    seen.set(s, result). result = {a:1}.
    key 'self': merge(undefined, s):
      seen.has(s) → return result.
    result.self = result (cycle in clone).
```

---

## 10. Common confusion + traps

1. **`for..in` walks prototype** — use `Object.keys`.
2. **Mutate target** — lodash mutates by default; document.
3. **No array policy** — silent overwrite confusion.
4. **`__proto__` pollution** — catastrophic.
5. **No cycle tracker** — infinite recursion.
6. **`Object.assign` instead** — shallow merge only.
7. **`spread` recursive** — would still need policy.

---

## 11. Senior follow-ups & variants

### Variant 1 — Lodash parity
lodash mutates target; document divergence.

### Variant 2 — Multi-source
`deepMergeAll(target, ...sources)`.

### Variant 3 — Customizer
Per-key callback override.

### Variant 4 — `Object.assign` for shallow
Spread/assign for one-level.

### Variant 5 — Symbol keys
Use `Reflect.ownKeys` instead of `Object.keys`.

---

## 12. How to think aloud

> "Deep merge: walk source, per-key: if primitive → assign; if object → recurse into target's same key; if array → policy (default replace; concat; element-wise index merge). Three critical concerns: (1) Prototype pollution — `__proto__`, `constructor`, `prototype` keys in source must be SKIPPED. Without skip, `deepMerge({}, JSON.parse('{\"__proto__\":{\"polluted\":true}}'))` sets `Object.prototype.polluted` — every object in the process now has it. Catastrophic. Modern JSON.parse sets __proto__ as own enumerable; assignment via `obj.__proto__ = ...` mutates prototype. (2) Cycles — WeakMap<source, result> tracker; register BEFORE recurse children. (3) Array policy must be DOCUMENTED — lodash.merge does element-wise; that's surprising for users expecting concat or replace. Default to replace; expose option. Use `Object.keys` (own enumerable) NOT `for..in` (walks prototype enumerable). Clone Date/Map/Set values instead of merging (no good 'merge' semantic). Non-mutating: spread `{...target}` to start each level; mutating variant matches lodash but breaks immutability. Trap: `__proto__` pollution (security CVE); for..in proto walk; no cycle tracker (infinite); ambiguous array policy."

---

## 13. 60-second revision

> - **Recursive walk; per-key dispatch.**
> - **Skip `__proto__`, `constructor`, `prototype`** — pollution defense.
> - **Array policy:** replace (default) / concat / index.
> - **WeakMap cycle tracker** + register-before-recurse.
> - **`Object.keys`** not `for..in`.
> - **Date/Map/Set clone**, not merge.
> - **Non-mutating** via `{...target}`.
> - **Multi-source:** reduce.
> - **Trap:** pollution; proto walk; cycle infinite; mutation surprise.

---

**Related:** [deep-clone-with-cycles.md](./deep-clone-with-cycles.md) · [`08-maps-sets/object-deep-diff.md`](../08-maps-sets/object-deep-diff.md) · [`07-arrays/structured-clone-vs-spread.md`](../07-arrays/structured-clone-vs-spread.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
