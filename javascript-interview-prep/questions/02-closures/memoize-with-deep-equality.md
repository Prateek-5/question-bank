# Memoize with Deep-Equality Key (Composite/Object Arguments)

## Source / Origin
- Lodash's `_.memoize` with custom resolver; React's `useMemo` reasoning.
- Asked at: Stripe, Razorpay, Atlassian.
- Concept reference: `concepts/closures.md`, sibling `memoize.md`, `memoize-ii.md`.

## Why this question matters in interviews
Stock memoize keys on first argument or `JSON.stringify(args)` — both have problems with non-primitive args. Stripe's "how would you memoize a function that takes an object?" filters for: (1) you know `JSON.stringify` has order/cycle issues, (2) you can build a stable canonical hash, (3) you reason about Map vs WeakMap tradeoffs for object-keyed caches.

## Concepts involved

### Syntax to lock in
```js
// Bad: WRONG result for object args
function memoize1(fn) {
  const cache = new Map();
  return (arg) => {
    if (cache.has(arg)) return cache.get(arg);
    const result = fn(arg);
    cache.set(arg, result);
    return result;
  };
}
const m = memoize1(({ a, b }) => a + b);
m({ a: 1, b: 2 });    // 3
m({ a: 1, b: 2 });    // 3 — but DIFFERENT object literal; not cached, recomputes!

// Better: canonical key for deep equality
function memoizeDeep(fn) {
  const cache = new Map();
  return (...args) => {
    const key = canonicalize(args);
    if (cache.has(key)) return cache.get(key);
    const result = fn(...args);
    cache.set(key, result);
    return result;
  };
}

function canonicalize(value) {
  if (value === null || typeof value !== 'object') return String(typeof value) + ':' + String(value);
  if (Array.isArray(value)) return 'A[' + value.map(canonicalize).join(',') + ']';
  const keys = Object.keys(value).sort();
  return 'O{' + keys.map(k => k + ':' + canonicalize(value[k])).join(',') + '}';
}
```

### Edge cases / interview traps
1. **`JSON.stringify` is not deterministic for keys.** Object key insertion order is implementation-defined; sort keys before stringifying for a stable hash.
2. **Cyclic objects break JSON.stringify.** Use a `WeakSet` to detect cycles; throw or canonical-mark.
3. **Date, Map, Set, RegExp.** JSON drops them. Canonicalize explicitly.
4. **Same object identity, mutated later** — cache key based on `===` won't detect mutation. Hash by content if mutation is possible; use WeakMap if identity is the contract.
5. **Big-object hash cost.** Computing canonical hash on a 1MB arg may cost more than running the function. Memoize only if work >> hash cost.
6. **Memory growth.** Caches grow unbounded. Pair with LRU.
7. **`NaN`, `-0`, `+0`, `undefined`** — JSON loses NaN, undefined; treats -0 == 0. Canonicalize explicitly if those matter.
8. **`Symbol` keys** — `Object.keys` skips them. Use `Reflect.ownKeys` if needed.

## Mental Model

The function's *true* signature is: "given a value-shape, return a result." `JSON.stringify` is a one-way hash; canonicalize is your contract for "same shape = same key":

```
   arg → canonicalize(arg) → key
        |                       |
        | depends on            ▼
        | the EQUIVALENCE class  same → cache hit
        | you care about         different → compute
        ▼
        - identity (===)      ← WeakMap, no hash
        - shape (deep equal)  ← canonical hash
        - first-arg-only      ← Map keyed on arg[0]
```

For object-as-cache-key you have three options:

```
   Identity:  cache = new WeakMap();   key = obj;
   Content:   cache = new Map();       key = canonicalize(obj);
   Hybrid:    Map<contentHash, WeakRef<lastObj>> with cleanup
```

## Why interviewers care

- **Equivalence-class thinking** — what counts as "the same input?"
- **Canonicalization** — knowing JSON.stringify isn't a hash function.
- **Memory awareness** — Map vs WeakMap vs LRU choice.

## Common beginner confusion

- **"`JSON.stringify(obj)` is a fingerprint."** Not stable across key order; not safe with cycles; loses non-JSON types.
- **"WeakMap memoize for objects."** Only helps if SAME object instance is reused. Two distinct `{ a: 1 }` literals have different identities.
- **"Map keyed by an object works."** It works (uses identity), but different literals miss the cache.
- **"Memoization always speeds things up."** Hash cost can exceed compute cost.
- **"Stale entries are fine."** Memory leak. Always bound.

## Brute force approach

```js
function memoizeJSON(fn) {
  const cache = new Map();
  return (...args) => {
    const key = JSON.stringify(args);    // breaks on cycles, key order, Date, Map
    if (cache.has(key)) return cache.get(key);
    const r = fn(...args);
    cache.set(key, r);
    return r;
  };
}
```

## Optimal approach

Custom canonicalize with sorted keys, type prefixes (so `1` ≠ `'1'`), explicit handling for Date/Map/Set/cycles. LRU bound on cache.

## Solution (JavaScript)

```js
function canonicalize(value, seen = new WeakSet()) {
  if (value === null) return 'null';
  const t = typeof value;
  if (t !== 'object' && t !== 'function') {
    if (value !== value) return 'NaN';      // NaN
    if (Object.is(value, -0)) return '-0';
    return `${t}:${String(value)}`;
  }
  if (value instanceof Date) return `D:${value.getTime()}`;
  if (value instanceof RegExp) return `R:${value.source}/${value.flags}`;
  if (seen.has(value)) return '<cycle>';
  seen.add(value);
  if (Array.isArray(value)) return 'A[' + value.map(v => canonicalize(v, seen)).join(',') + ']';
  if (value instanceof Map) return 'M{' + [...value.entries()].sort().map(([k,v]) => canonicalize(k,seen)+'='+canonicalize(v,seen)).join(',') + '}';
  if (value instanceof Set)  return 'S{' + [...value].map(v => canonicalize(v, seen)).sort().join(',') + '}';
  const keys = Object.keys(value).sort();
  return 'O{' + keys.map(k => k + ':' + canonicalize(value[k], seen)).join(',') + '}';
}

class LRU {
  constructor(cap = 1000) { this.cap = cap; this.map = new Map(); }
  has(k) { return this.map.has(k); }
  get(k) {
    if (!this.map.has(k)) return undefined;
    const v = this.map.get(k); this.map.delete(k); this.map.set(k, v); return v;
  }
  set(k, v) {
    if (this.map.has(k)) this.map.delete(k);
    this.map.set(k, v);
    if (this.map.size > this.cap) this.map.delete(this.map.keys().next().value);
  }
}

function memoizeDeep(fn, { cacheSize = 1000 } = {}) {
  const cache = new LRU(cacheSize);
  return (...args) => {
    const key = canonicalize(args);
    if (cache.has(key)) return cache.get(key);
    const result = fn(...args);
    cache.set(key, result);
    return result;
  };
}

// Usage
const computeShipping = memoizeDeep(({ items, address }) => {
  return items.reduce((s, i) => s + i.weight, 0) * (address.zone === 'A' ? 1 : 1.5);
});
computeShipping({ items: [{weight:1}], address:{zone:'A'} });   // computes
computeShipping({ address: {zone:'A'}, items: [{weight:1}] });  // cache hit despite key order
```

## Step-by-step dry run

```js
const fn = memoizeDeep((opts) => expensive(opts));

call 1: fn({ a: 1, b: 2 })
  args = [{a:1, b:2}]
  canonicalize(args) → 'A[O{a:number:1,b:number:2}]'
  cache miss → compute; cache.set('A[O{...}]', result)
  return result

call 2: fn({ b: 2, a: 1 })       // different key order
  canonicalize(args) → 'A[O{a:number:1,b:number:2}]'   // sorted keys → SAME
  cache hit → return cached

call 3: fn({ a: 1, b: 2, extra: undefined })
  canonicalize → 'A[O{a:number:1,b:number:2,extra:undefined:undefined}]'   // DIFFERENT
  cache miss → compute
```

## How to think aloud in the interview

> "Stock memoize keys on identity, which fails for object literals. JSON.stringify isn't stable — key order, cycles, Date/Map. I'd write canonicalize: sorted keys, type prefixes so `1` ≠ `'1'`, explicit Date/RegExp/Map/Set handling, cycle detection via WeakSet. Pair with LRU bound — caches must die. For identity-only semantics (same object instance), WeakMap is simpler and GC-friendly. Measure: a hash takes microseconds, only memoize when fn is more expensive."

## Important takeaways

- **`JSON.stringify` is NOT a hash function.** Key order, cycles, types.
- **Canonicalize**: sort keys, type prefixes, handle Date/Map/Set/cycles.
- **LRU bound** the cache.
- **WeakMap for identity semantics; Map for content semantics.**
- **Hash cost vs compute cost** — measure before memoizing.

## Variants

- **structuredClone-based hash** — pass through structured clone, hash the result. Heavy but accurate.
- **`fast-equals` or `dequal`** — npm libs with optimized deep-equal hash.
- **Hash + verify** — fast hash for lookup, full deep-equal on collision.
- **Per-property fingerprint** — only specific properties are part of the key.
- **Memoize with TTL** — invalidate entries on time.

## Revision notes

```
memoizeDeep(fn):
  canonicalize(args): sorted-key, type-prefixed, cycle-safe
    primitives: typeof + value
    Date/RegExp: explicit encoding
    Array: 'A[' + canonicalize(items) + ']'
    Object: 'O{' + sorted key:canonicalize(val) + '}'
    Map/Set: explicit handling
    cycles: WeakSet seen
  
  cache = LRU(cap)
  
  TRAPS:
    - JSON.stringify is NOT deterministic (key order)
    - cycles break JSON
    - Date/Map/Set lost
    - NaN, -0, undefined collapsed
    - memory grows unbounded without LRU
  
  WeakMap when:
    - key is the SAME OBJECT INSTANCE (identity)
    - want GC to clean cache when object dies
  
  Map+canonicalize when:
    - "same shape" should be a cache hit
    - keys may be reconstructed
```
