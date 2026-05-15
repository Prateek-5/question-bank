# `Set.prototype.intersection` / `union` / `difference` polyfills

## Source
- TC39 "Set Methods" proposal (Stage 4, shipped in ES2025): https://github.com/tc39/proposal-set-methods
- MDN reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Set
- Real backend use: feature flags, permission sets, tag matching, A/B segment overlap.

## Why this question matters in interviews
This question lives at the **fundamentals × modern-platform** intersection — interviewers ask it for three reasons: (1) do you know **what's new in ES2025** (recency signal), (2) can you reason about **iteration cost and the smaller-set-first optimization** (algorithmic signal), (3) can you write a clean polyfill that mirrors the spec, including the new "set-like" protocol (`size`, `has`, `keys`) for cross-collection interop (spec literacy signal). On the job you'll write these every week for feature-flag sets, tag intersections in cache invalidation, permission overlaps in auth checks, and segment intersection in analytics — most codebases still have hand-rolled versions because they pre-date ES2025.

## Concepts involved

### Syntax to lock in
```js
// Native (Node 22+, modern browsers — ES2025)
const a = new Set([1, 2, 3]);
const b = new Set([2, 3, 4]);

a.intersection(b);              // Set { 2, 3 }
a.union(b);                     // Set { 1, 2, 3, 4 }
a.difference(b);                // Set { 1 }
a.symmetricDifference(b);       // Set { 1, 4 }
a.isSubsetOf(b);                // false
a.isSupersetOf(b);              // false
a.isDisjointFrom(b);            // false
```

### Runtime / engine behavior
- All seven methods accept any **"set-like"** object: a value with numeric `size`, callable `has(v)`, and callable `keys()` returning an iterator. This means `Map` is accepted (Map's `keys()` returns keys, has `size` and `has`), as are custom collections like `BTreeSet`. The spec carefully avoided locking it to `Set` instances.
- The **smaller-set-first optimization**: `a.intersection(b)` iterates whichever of `a`, `b` is smaller and checks `has` on the other. This is **O(min(|a|, |b|))** instead of O(|a|). The spec actually mandates this — implementations check `b.size` to decide iteration direction. Worth replicating in your polyfill.
- `Set.prototype.has` is **O(1) amortized** (hash table). The polyfill leans entirely on this — every operation is `iterate one set, check membership in the other`.
- All operations return a **new Set**; they don't mutate. This is the same immutability discipline as `Array.prototype.toSorted` / `toReversed` (ES2023).

### Edge cases (these are the interview traps)
1. **`NaN` handling** — `Set` uses **SameValueZero** equality: `NaN` matches `NaN`, `+0` matches `-0`. So `new Set([NaN]).has(NaN) === true` despite `NaN !== NaN`. The polyfill inherits this from `Set.prototype.has`.
2. **`other` is not a Set** — the spec accepts any set-like. Cheap polyfills that do `other instanceof Set` fail on `Map` / custom types. Use the duck-type check: `typeof other.size === 'number' && typeof other.has === 'function'`.
3. **Self-operation** — `a.intersection(a)` returns a *copy* of `a`, not `a` itself. New Set, every time.
4. **Empty sets** — `a.intersection(new Set()) → ∅`. `a.union(new Set()) → copy of a`. `a.isSubsetOf(new Set()) → a.size === 0`.
5. **Iteration order** — result Set preserves insertion order based on the *first* set iterated. Polyfill must match.
6. **Object equality** — `{a:1}` and `{a:1}` are different references → different Set members. No deep equality.
7. **`isSubsetOf` performance** — must check `a.size <= b.size` first, then `a.has` for every element of... wait, no: iterate `a`, check `b.has(elem)`. Spec says: if `a.size > b.size` return false immediately.
8. **`isDisjointFrom` short-circuit** — return false on first overlap; iterate the smaller set.

## Brute force approach
Convert both sets to arrays and use `Array.prototype.filter` + `Array.prototype.includes`. **O(n·m) time** because `Array.includes` is linear. Acceptable for tiny inputs (< 50 elements) but catastrophic at scale. Mention it as the naive baseline, then jump to Set-based O(n+m).

## Optimal approach
Polyfill each method by iterating one set and probing membership of the other via `has` (O(1)). Always **iterate the smaller set** when commutative — `intersection`, `isDisjointFrom`, `symmetricDifference` benefit.

- `union(other)`: copy `this`, add every elem of `other`. **O(|a| + |b|)**.
- `intersection(other)`: iterate smaller, push elem if other.has(elem). **O(min(|a|, |b|))**.
- `difference(other)`: iterate `this`, push elem if !other.has(elem). **O(|a|)**.
- `symmetricDifference(other)`: iterate both; include elements present in exactly one.
- `isSubsetOf(other)`: if `|a| > |b|` return false; else every elem of `a` must be in `b`.
- `isSupersetOf(other)`: mirror.
- `isDisjointFrom(other)`: iterate smaller; return false on any `has` hit.

## Solution (JavaScript)

```js
/**
 * Polyfills for Set methods. Install only if not natively supported.
 * Accepts any "set-like" other: must have numeric `size`, `has(v)`, `keys()`.
 */
function assertSetLike(other) {
  if (other == null || typeof other.size !== 'number'
      || typeof other.has !== 'function' || typeof other.keys !== 'function') {
    throw new TypeError('argument must be set-like (size, has, keys)');
  }
}

function intersection(other) {
  assertSetLike(other);
  const result = new Set();
  // Iterate the smaller collection — spec-mandated optimization.
  const [small, big] = this.size <= other.size ? [this, other] : [other, this];
  for (const v of small.keys ? small.keys() : small) {
    if (big.has(v)) result.add(v);
  }
  return result;
}

function union(other) {
  assertSetLike(other);
  const result = new Set(this);                    // copy this preserves order
  for (const v of other.keys()) result.add(v);
  return result;
}

function difference(other) {
  assertSetLike(other);
  const result = new Set();
  for (const v of this) if (!other.has(v)) result.add(v);
  return result;
}

function symmetricDifference(other) {
  assertSetLike(other);
  const result = new Set();
  for (const v of this) if (!other.has(v)) result.add(v);
  for (const v of other.keys()) if (!this.has(v)) result.add(v);
  return result;
}

function isSubsetOf(other) {
  assertSetLike(other);
  if (this.size > other.size) return false;
  for (const v of this) if (!other.has(v)) return false;
  return true;
}

function isSupersetOf(other) {
  assertSetLike(other);
  if (this.size < other.size) return false;
  for (const v of other.keys()) if (!this.has(v)) return false;
  return true;
}

function isDisjointFrom(other) {
  assertSetLike(other);
  const [small, big] = this.size <= other.size ? [this, other] : [other, this];
  for (const v of small.keys ? small.keys() : small) {
    if (big.has(v)) return false;
  }
  return true;
}

// Install polyfills (only the missing ones).
const proto = Set.prototype;
for (const [name, fn] of Object.entries({
  intersection, union, difference, symmetricDifference,
  isSubsetOf, isSupersetOf, isDisjointFrom,
})) {
  if (typeof proto[name] !== 'function') {
    Object.defineProperty(proto, name, {
      value: fn, writable: true, configurable: true, enumerable: false,
    });
  }
}
```

## Step-by-step dry run

```js
const a = new Set(['read', 'write', 'admin']);     // user roles
const b = new Set(['read', 'delete']);             // required permissions

a.intersection(b);                                  // Set { 'read' }
a.union(b);                                         // Set { 'read', 'write', 'admin', 'delete' }
a.difference(b);                                    // Set { 'write', 'admin' }
b.difference(a);                                    // Set { 'delete' }
a.symmetricDifference(b);                           // Set { 'write', 'admin', 'delete' }
a.isSubsetOf(b);                                    // false (a has 'write', b doesn't)
b.isSubsetOf(a);                                    // false (b has 'delete')
a.isDisjointFrom(new Set(['guest']));               // true (no overlap)
```

Trace `a.intersection(b)`:
- `a.size = 3`, `b.size = 2` → iterate `b` (smaller).
- `b.keys()` yields `'read'`, `'delete'`.
- `'read'`: `a.has('read')` → true → add.
- `'delete'`: `a.has('delete')` → false → skip.
- Result: `Set { 'read' }`. **2 has-checks instead of 3** — smaller-set-first paid off.

Trace `a.isSubsetOf(b)`:
- `a.size (3) > b.size (2)` → return false **immediately**, no iteration. Spec optimization.

## Important takeaways

**Syntax to memorize**
- Seven methods: `intersection`, `union`, `difference`, `symmetricDifference`, `isSubsetOf`, `isSupersetOf`, `isDisjointFrom`.
- Accept any **set-like** (duck-typed: `size`, `has`, `keys`).
- All non-predicate methods return a **new Set** (immutable).

**Patterns to reuse**
- **Iterate small, probe big** is the universal hash-join pattern. Same trick is used by V8's `Array.prototype.includes` lookup tables, SQL hash joins (build phase on the smaller table), and Bloom-filter-fronted lookups.
- **Set-like duck typing** (`size + has + keys`) lets the algorithm work over `Set`, `Map`, custom collections, and even `WeakSet`-backed wrappers. Mirror this discipline in your own APIs.
- **Immutable return + new collection** (`toSorted`, `toReversed`, `with`, set methods) is the modern JS direction. Adopt it in custom utilities.

**Common mistakes**
- Using `Array.from(a).filter(x => b.has(x))` — same big-O, but allocates an array you immediately throw away. Stick to `for...of`.
- `for (const v of other)` instead of `other.keys()` — works for `Set` (whose default iterator is `keys`) but breaks for `Map` (whose default iterator is `entries`). The spec mandates `keys()` so it works on Map.
- `other instanceof Set` instead of duck-typing — rejects valid set-likes.
- Forgetting smaller-set-first → 2-3x slower on asymmetric inputs.
- Returning `this` when intersecting `a` with itself → unexpected aliasing. Always new Set.
- Polluting Set.prototype unconditionally → may conflict with native. Always feature-check.

**Big-O cheat sheet**
| Method               | Time              | Notes                            |
|----------------------|-------------------|----------------------------------|
| union                | O(\|a\| + \|b\|)  | Must visit every element         |
| intersection         | O(min(\|a\|, \|b\|)) | Iterate smaller, probe larger |
| difference           | O(\|a\|)          | Iterate `this`                   |
| symmetricDifference  | O(\|a\| + \|b\|)  | Both directions                  |
| isSubsetOf           | O(\|a\|)          | Returns early if \|a\| > \|b\|   |
| isSupersetOf         | O(\|b\|)          | Mirror of subset                 |
| isDisjointFrom       | O(min(\|a\|, \|b\|)) | Short-circuits on overlap     |

**Related questions**
- Array intersection / union / difference (with duplicates — different semantics)
- LRU cache eviction (uses Map ordering)
- LeetCode #349 Intersection of Two Arrays
- Feature flag / permission overlap design

## Variants

1. **Multiset / bag semantics** — duplicates allowed, intersection takes min count, union takes max. Switch to `Map<value, count>` instead of `Set`. Different problem; clarify with interviewer.

2. **Sorted-array intersection** — if inputs are sorted arrays (not sets), use **two-pointer merge** for O(n+m) with **O(1) extra space** (output goes to a new array). Beats Set on space when input is already sorted.

3. **Generic over WeakSet** — WeakSet has no `keys()` or `size`, so set methods don't apply. Mention this if asked about "why don't WeakSet methods exist?"

4. **Lazy / streaming intersection** — produce a generator that yields elements of `a` as they're found in `b`. Useful for short-circuited consumers. `function* lazyIntersection(a, b) { for (const v of a) if (b.has(v)) yield v; }`.

5. **Bloom-filter-backed approximate intersection** — for very large sets, replace `b.has(v)` with a Bloom filter probe. Allows false positives but uses constant memory. Cite for "what if the sets don't fit in memory?"

## Revision notes

> **set-operations-polyfill — 60 second recap**
> - **ES2025 added seven methods**: `intersection`, `union`, `difference`, `symmetricDifference`, `isSubsetOf`, `isSupersetOf`, `isDisjointFrom`.
> - Accept any **set-like** (`size`, `has`, `keys`) — Map works too.
> - All non-predicate methods return a **new Set** (immutable).
> - **Iterate the smaller** set, **probe the larger** — O(min(|a|, |b|)) for `intersection` / `isDisjointFrom`.
> - `isSubsetOf` short-circuits if `|a| > |b|`.
> - Polyfill via `Object.defineProperty` on `Set.prototype` — feature-check first.
> - Set uses **SameValueZero** — `NaN === NaN` in Set-land.
> - Family: hash-join, feature-flag overlap, permission intersection.
