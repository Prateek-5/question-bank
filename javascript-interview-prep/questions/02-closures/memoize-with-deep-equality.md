# Build `memoize(fn)` with deep-equality cache keys (object arguments)

> **Difficulty:** Medium-Hard   |   **Time:** ~30 min   |   **Prereqs:** [memoize-with-ttl.md](./memoize-with-ttl.md), [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
>
> **Source:** lodash `_.memoize` with custom resolver; React's `useMemo` reasoning. Asked at Stripe, Razorpay, Atlassian.

---

## 1. Problem statement

**Signature**
```ts
function memoizeDeep<F extends (...args: any[]) => any>(
  fn: F,
  options?: { cacheSize?: number }
): F;
```

**Input / Output examples**

| Setup                                                          | Sequence                                              | Behaviour                                  |
|----------------------------------------------------------------|--------------------------------------------------------|---------------------------------------------|
| `const m = memoizeDeep(({a,b}) => a+b)`                        | `m({a:1, b:2}); m({a:1, b:2});`                       | second call is a **cache hit** (same shape) |
| same                                                            | `m({a:1, b:2}); m({b:2, a:1});`                       | hit despite key order                       |
| same                                                            | `m({a:1, b:2}); m({a:1, b:2, extra:undefined});`      | miss — different shapes                     |
| Cycles                                                          | `const o = {a:1}; o.self = o; m(o);`                 | works (cycle-safe canonicalize)             |
| `m(new Date('2024-01-01'))`                                    | second call same date                                 | hit — Date canonicalized by timestamp       |

**Constraints**
- Cache key derived from a **canonical hash** of arguments — same shape → same key, regardless of property order.
- Handle Date, RegExp, Map, Set, cycles, `NaN`, `-0`, `undefined`.
- Bound cache size with LRU eviction.
- Cache the result (or Promise, for async).

---

## 2. Plain-English restatement

The interviewer says "memoize a function that takes an object." Naive `Map`-keyed-by-arg memoize fails because two different object literals `{a:1, b:2}` are different references. You need to canonicalize the args into a string that captures the *shape* — sorted keys, type prefixes, special handling for non-JSON types, cycle detection — and use that as the cache key. Then bound the cache so it doesn't grow forever.

In ~50 lines you're building the careful, correct version of lodash `_.memoize` with a non-trivial resolver — the kind of utility that lives in production codebases when the naive memoize stops working.

---

## 3. Why this matters in interviews

This is the **memoize the interviewer actually cares about**. Plain memoize on primitives is a warmup; senior backend interviewers reach for "what if the args are objects?" to test three things at once: (1) you know `JSON.stringify` has key-order / cycle / type-loss issues; (2) you can build a stable canonical hash from scratch; (3) you reason about `Map` vs `WeakMap` tradeoffs and pair the cache with LRU bounds. Bombing this signals "knows the term, not the substance."

---

## 4. Mental model

The cache key is a **fingerprint of the input's shape, not its identity**. The function's *true* signature is `(value-shape) → result`. You need a canonicalize function that produces the same string for any two inputs you consider "equivalent":

```
   args → canonicalize(args) → key string → Map<key, result>
            │
            └── definition of "equivalent":
                ├── identity (===)        ← WeakMap, no hash
                ├── shape (deep equal)    ← canonical hash (this question)
                └── primitives only       ← JSON.stringify
```

For object-keyed caches you have three options:

```
   Identity caching:  cache = new WeakMap();   key = obj;
                       hits only when SAME instance is reused
                       GC-friendly (entries die with the key)
   
   Content caching:   cache = new Map();       key = canonicalize(obj);
                       hits whenever shape matches
                       must bound with LRU
   
   Hybrid:            Map<contentHash, WeakRef<lastObj>>
                       advanced; auto-evicts when the original is GC'd
```

This question is about **content caching** — the canonical-hash route.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `JSON.stringify({a:1, b:2}) === JSON.stringify({b:2, a:1})`? If not, why?
> 2. `m({a: undefined})` and `m({})` — should they be cache hits for each other? What does JSON do? What should canonicalize do?
> 3. For very large nested args, when does the hash cost exceed the compute cost? How would you decide whether to memoize at all?

---

## 6. Brute force — walked through

### Wrong attempt 1: Map keyed on the object reference

```js
function memoize(fn) {
  const cache = new Map();
  return (arg) => {
    if (cache.has(arg)) return cache.get(arg);   // BUG: identity check
    const r = fn(arg);
    cache.set(arg, r);
    return r;
  };
}
const m = memoize(({a, b}) => a + b);
m({a: 1, b: 2});   // 3
m({a: 1, b: 2});   // 3 — but different literal → CACHE MISS → recomputes
```

Identity check fails for object literals that look the same. Wrong equivalence class for the use case.

### Wrong attempt 2: `JSON.stringify` as the key

```js
function memoize(fn) {
  const cache = new Map();
  return (...args) => {
    const key = JSON.stringify(args);
    if (cache.has(key)) return cache.get(key);
    const r = fn(...args);
    cache.set(key, r);
    return r;
  };
}
```

Three problems:

1. **Key order is implementation-defined**. `JSON.stringify({a:1, b:2})` and `JSON.stringify({b:2, a:1})` may produce different strings depending on engine and insertion order. Brittle.
2. **Cycles throw** `TypeError: Converting circular structure to JSON`.
3. **Types are lost**: `Date` becomes an ISO string (later indistinguishable from a literal string); `Map` and `Set` become `{}`; `undefined` and functions disappear; `NaN` and `Infinity` become `null`.

### Wrong attempt 3: unbounded canonical-hash cache

```js
function memoize(fn) {
  const cache = new Map();
  return (...args) => {
    const key = canonicalize(args);
    if (cache.has(key)) return cache.get(key);
    return cache.set(key, fn(...args)).get(key);
  };
}
```

Works for correctness but the cache grows forever. Memory leak in long-running services. Pair with LRU bound.

---

## 7. The unlocking insight

> **Replace `JSON.stringify` with a custom `canonicalize` that's stable across key order, cycle-safe, and explicit about types. Pair with an LRU-bounded cache.**

The canonicalize function recursively produces a string fingerprint:

- **Primitives**: prefix with `typeof` so `1` (number) ≠ `'1'` (string). Encode special values: `NaN`, `-0`, `null`, `undefined`.
- **Date / RegExp**: explicit tag + canonical representation.
- **Array**: `'A[' + items.map(canonicalize).join(',') + ']'`.
- **Object**: sort keys with `Object.keys(value).sort()`, then format as `'O{key:canonicalize(val), ...}'`.
- **Map / Set**: explicit handling — entries / values, ordered.
- **Cycles**: track visited with a `WeakSet`; emit `'<cycle>'` on revisit (or throw).

The result is deterministic across runs and instances. Two args with the same shape produce the same key, regardless of property order or temporal context.

The **LRU cache** wraps a `Map` with a delete-then-set trick (Map preserves insertion order; deleting and re-inserting on hit moves the entry to the tail; the oldest key is at the head).

Trade-offs you must articulate:

- **Hash cost vs compute cost.** A 1 MB nested arg's canonicalize takes ~10ms. If `fn` is 1ms, you've made it 11x slower. Memoize only when `fn` >> hash.
- **Identity vs content.** If callers always pass *the same object reference*, `WeakMap` is simpler and GC-friendly. If they construct fresh objects each call, you need content hashing.
- **Cache invalidation.** This pattern handles "same input → cached output" but not "input changed → invalidate." For TTL-based invalidation, see [memoize-with-ttl.md](./memoize-with-ttl.md).

---

## 8. Solution (annotated)

```js
function canonicalize(value, seen = new WeakSet()) {            // step 1: recursive fingerprint
  if (value === null) return 'null';
  const t = typeof value;
  if (t !== 'object' && t !== 'function') {                       // step 2: primitives — typeof prefix + value
    if (value !== value) return 'NaN';                              //         NaN
    if (Object.is(value, -0)) return '-0';                          //         distinguish -0 from 0
    return `${t}:${String(value)}`;
  }
  if (value instanceof Date)   return `D:${value.getTime()}`;        // step 3: known special types
  if (value instanceof RegExp) return `R:${value.source}/${value.flags}`;
  if (seen.has(value)) return '<cycle>';                            // step 4: cycle detection
  seen.add(value);
  if (Array.isArray(value))    return 'A[' + value.map(v => canonicalize(v, seen)).join(',') + ']';
  if (value instanceof Map)    return 'M{' + [...value.entries()].sort().map(([k, v]) => canonicalize(k, seen) + '=' + canonicalize(v, seen)).join(',') + '}';
  if (value instanceof Set)    return 'S{' + [...value].map(v => canonicalize(v, seen)).sort().join(',') + '}';
  const keys = Object.keys(value).sort();                            // step 5: object — sort keys for stability
  return 'O{' + keys.map(k => k + ':' + canonicalize(value[k], seen)).join(',') + '}';
}

class LRU {                                                          // step 6: bounded cache
  constructor(cap = 1000) { this.cap = cap; this.map = new Map(); }
  has(k) { return this.map.has(k); }
  get(k) {
    if (!this.map.has(k)) return undefined;
    const v = this.map.get(k); this.map.delete(k); this.map.set(k, v);  // refresh LRU
    return v;
  }
  set(k, v) {
    if (this.map.has(k)) this.map.delete(k);
    this.map.set(k, v);
    if (this.map.size > this.cap) this.map.delete(this.map.keys().next().value);  // evict oldest
  }
}

function memoizeDeep(fn, { cacheSize = 1000 } = {}) {                // step 7: assemble
  const cache = new LRU(cacheSize);
  return (...args) => {
    const key = canonicalize(args);
    if (cache.has(key)) return cache.get(key);
    const result = fn(...args);
    cache.set(key, result);
    return result;
  };
}
```

**Try it yourself**

```js
const computeShipping = memoizeDeep(({ items, address }) => {
  const weight = items.reduce((s, i) => s + i.weight, 0);
  return weight * (address.zone === 'A' ? 1 : 1.5);
});

computeShipping({ items: [{weight: 1}], address: {zone: 'A'} });   // computes
computeShipping({ address: {zone: 'A'}, items: [{weight: 1}] });   // CACHE HIT (key order doesn't matter)
computeShipping({ items: [{weight: 1}], address: {zone: 'B'} });   // miss (different shape)
```

---

## 9. Step-by-step dry run

Input:

```js
const fn = memoizeDeep((opts) => expensive(opts));
fn({ a: 1, b: 2 });
fn({ b: 2, a: 1 });
fn({ a: 1, b: 2, extra: undefined });
```

Values-first trace:

| Step | Call                                  | `canonicalize(args)`                                       | Cache hit? | `fn` runs? |
|------|---------------------------------------|--------------------------------------------------------------|------------|-------------|
| 1    | `fn({a:1, b:2})`                      | `'A[O{a:number:1,b:number:2}]'`                              | no         | yes         |
| 2    | `fn({b:2, a:1})`                      | `'A[O{a:number:1,b:number:2}]'` (sorted keys → same)         | **yes**    | no          |
| 3    | `fn({a:1, b:2, extra: undefined})`    | `'A[O{a:number:1,b:number:2,extra:undefined:undefined}]'`    | no         | yes         |

Step 2 is the senior signal — content-equal inputs hit the cache despite different property order.

---

## 10. Common confusion + traps

1. **`JSON.stringify` is a hash function.**
   It isn't. Key order is implementation-defined; cycles throw; Date/Map/Set/undefined are lost or misencoded; `NaN`/`Infinity` become `null`. Roll a canonicalize that's explicit about all of these.

2. **`WeakMap` memoize for objects.**
   `WeakMap` keys are identity-based — two object literals with the same shape have different identities and miss the cache. `WeakMap` only helps if callers reuse the *same* object reference.

3. **Memoization always speeds things up.**
   Not always. Hash cost can exceed compute cost for big args + cheap functions. Measure with `performance.now()` before reaching for memoize.

4. **Unbounded cache.**
   Without LRU, the Map grows forever. Memory leak in long-running services. Always pair with a size cap (or TTL — see sibling).

5. **Caching mutable objects.**
   If callers mutate an argument after the cache has stored its canonical hash, the *next* call with the mutated arg may hit a stale entry (the new shape hashes differently — actually a miss, which is correct). But if `fn`'s result was a reference into the arg, the cached result now reflects the mutation. Document.

6. **`NaN`, `-0`, `+0`, `undefined`.**
   JSON loses NaN and undefined; collapses -0 and +0. Canonicalize explicitly if those matter (e.g., financial math, signed-zero ID schemes).

7. **`Symbol` keys.**
   `Object.keys` skips them. Use `Reflect.ownKeys` if you need to canonicalize over symbols too. Symbols don't survive serialization but you can use `Symbol.description`.

---

## 11. Senior follow-ups & variants

### Variant 1 — Async memoize with in-flight dedupe

Cache the **Promise**, not the resolved value, so concurrent callers share one in-flight call. Delete the entry on rejection so transient failures don't stick:

```js
function memoizeAsyncDeep(fn) {
  const cache = new LRU(1000);
  return async (...args) => {
    const key = canonicalize(args);
    if (cache.has(key)) return cache.get(key);
    const p = Promise.resolve().then(() => fn(...args));
    cache.set(key, p);
    p.catch(() => cache.delete(key));
    return p;
  };
}
```

Same skeleton as [`10-machine-coding-patterns/cache-stampede-single-flight.md`](../10-machine-coding-patterns/cache-stampede-single-flight.md).

### Variant 2 — `structuredClone`-based hash

For complete fidelity (handles all structured-cloneable types: Date, Map, Set, TypedArray, ArrayBuffer, cycles), pass through `structuredClone` and then canonicalize. Heavy (allocates a full copy) but more correct than handcrafted recursion:

```js
function deepHash(value) {
  const cloned = structuredClone(value);
  return canonicalize(cloned);
}
```

Trade: 2x memory during hashing. Use when correctness matters more than speed.

### Variant 3 — Hash + verify (collision-resistant)

For very large args, compute a fast hash (e.g., `xxhash` over canonicalize output) and **verify equality on collision**:

```js
function memoizeHashVerify(fn) {
  const cache = new Map();   // hash → [arg, result] pairs
  return (...args) => {
    const hash = xxhash(canonicalize(args));
    const bucket = cache.get(hash);
    if (bucket) {
      for (const [storedArgs, result] of bucket) {
        if (deepEqual(storedArgs, args)) return result;
      }
    }
    const result = fn(...args);
    if (!cache.has(hash)) cache.set(hash, []);
    cache.get(hash).push([args, result]);
    return result;
  };
}
```

Heavier but immune to hash collisions corrupting cache hits.

### Variant 4 — Per-property fingerprint

Sometimes only a subset of the arg matters for the result. Let the caller specify which fields contribute to the key:

```js
const m = memoizeDeep(fn, { keyFn: (args) => canonicalize([args[0].id, args[0].version]) });
```

Now mutating other fields doesn't bust the cache.

### Variant 5 — Fast-equals / dequal libraries

In real code, `fast-equals` (~3 KB) or `dequal` (~1 KB) do this professionally. Mention you'd reach for these in production rather than hand-rolling, unless the canonicalization is bespoke.

---

## 12. How to think aloud in the interview

> "Stock memoize keyed on identity fails for object literals. JSON.stringify isn't stable — key order, cycles, Date/Map/Set, NaN, undefined. I'd write a canonicalize: sorted keys, typeof prefixes so `1` ≠ `'1'`, explicit Date/RegExp/Map/Set handling, cycle detection via WeakSet. Pair with an LRU cap — caches must die. For identity-only semantics (same instance reused), WeakMap is simpler and GC-friendly. For async, cache the Promise and delete on rejection. Measure: a hash takes microseconds, only memoize when fn is more expensive. In production I'd reach for fast-equals/dequal unless the canonical shape is bespoke."

---

## 13. 60-second revision

> - **`JSON.stringify` is NOT a hash function.** Key order, cycles, types.
> - **Canonicalize**: sort object keys; typeof prefixes for primitives; explicit Date/RegExp/Map/Set; cycle detection via WeakSet.
> - **LRU bound** the cache — `Map` + delete-then-set + evict-oldest-on-overflow.
> - **`WeakMap` for identity semantics** (same instance reused); **`Map`+canonicalize for content semantics** (any matching shape).
> - **Hash cost vs compute cost** — measure before memoizing.
> - **Async:** cache the Promise; `.catch(() => cache.delete(key))` so failures don't stick.
> - **Trap:** mutating cached args; assuming WeakMap works for object literals.
> - **Family:** memoize, memoize-with-ttl, request-dedupe, cache-invalidate-by-tag.

---

**Related:** [memoize-with-ttl.md](./memoize-with-ttl.md) · [`08-maps-sets/weakmap-memoize.md`](../08-maps-sets/weakmap-memoize.md) · [`10-machine-coding-patterns/memoize.md`](../10-machine-coding-patterns/memoize.md) · [`10-machine-coding-patterns/cache-stampede-single-flight.md`](../10-machine-coding-patterns/cache-stampede-single-flight.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md), [`concepts/closures.md`](../../concepts/closures.md)
