# Implement a `Set` polyfill (add, has, delete, size, iteration)

## Source
- Classic machine-coding interview problem (BFE.dev, codedamn, Frontend Masters polyfill series).
- Variant of the broader "polyfill an ES collection" family alongside Map, WeakMap.

## Why this question matters in interviews
Set polyfill is deceptively rich. The naive version (array-backed with `indexOf`) is 20 lines and correct, but interviewers will push: "What's `has` complexity? Can you do O(1)? What about `NaN`? `+0` vs `-0`? Iteration order?" That escalation chain probes whether you understand **hash tables**, **SameValueZero equality semantics**, **`Symbol.iterator`**, and the subtle ways JS objects differ from hash maps in C++/Java. Backend engineers see this as: "implement an in-memory dedup cache," "build a request-id ledger with TTL," "do set intersection on two arrays without Set" — all the same skill.

## Concepts involved

### Syntax to lock in
```js
// Array-backed (O(n) has) — educational baseline
class MySet {
  constructor(iterable = []) { this.items = []; for (const x of iterable) this.add(x); }
  add(v)    { if (!this.has(v)) this.items.push(v); return this; }
  has(v)    { return this.items.some((x) => x === v || (x !== x && v !== v)); } // NaN equality
  delete(v) { const i = this.items.findIndex((x) => x === v || (x !== x && v !== v));
              if (i === -1) return false; this.items.splice(i, 1); return true; }
  get size(){ return this.items.length; }
  *[Symbol.iterator]() { yield* this.items; }
}

// Map-backed (O(1) average has) — production-shape
class MySetFast {
  constructor(iterable = []) { this._m = new Map(); for (const x of iterable) this.add(x); }
  add(v)    { this._m.set(v, true); return this; }    // Map handles NaN, ±0 correctly
  has(v)    { return this._m.has(v); }
  delete(v) { return this._m.delete(v); }
  get size(){ return this._m.size; }
  *[Symbol.iterator]() { for (const k of this._m.keys()) yield k; }
}
```

### Runtime / engine behavior
- The native `Set` uses **SameValueZero** equality. That means `NaN === NaN` is `true` for membership purposes (unlike `===`), and `+0 === -0` is `true` (same as `===`). Your polyfill must match this.
- `indexOf` uses **strict equality** (`===`), which says `NaN !== NaN`. So array-backed needs the `x !== x && v !== v` trick to handle NaN. Or use `Array.prototype.includes` (which uses SameValueZero).
- The Map-backed version inherits the correct semantics from `Map` for free — Map already uses SameValueZero on keys.
- Iteration order is **insertion order** in V8 for both Map and Set. Your polyfill must preserve this — that's why `.items.push` (array tail) or `Map` (which preserves insertion order in spec) is the right structure.
- `Symbol.iterator` on the class makes `for...of` work and enables spread `[...mySet]`. Generator-syntax `*[Symbol.iterator]()` is the cleanest definition.

### Edge cases (these are the interview traps)
1. **`NaN`** — `set.add(NaN); set.has(NaN)` must return `true`. With `indexOf` it returns `false`. Use `includes` or the `x !== x && v !== v` check.
2. **`+0` vs `-0`** — both should be the same element. `===` already treats them equal, so this is fine for the strict-equality path. Mention it anyway — interviewers like it.
3. **Object references** — Sets use **reference equality** for objects. `add({}); has({})` is `false` (different references). Demonstrate awareness.
4. **`size` is a getter, not a property** — native Set's `size` is computed on access. Use `get size()`. Storing it as a counter and forgetting to decrement on `delete` is the classic bug.
5. **Iteration during mutation** — adding/removing during `for...of mySet` is implementation-defined in user code. Native Set's behavior: newly added items DO get visited; deleted-not-yet-visited items are skipped. Don't promise this in your polyfill unless asked.
6. **Constructor with iterable** — `new Set([1,2,3])`, `new Set('abc')`, `new Set(otherSet)` all work because iterables are accepted. Use `for (const x of iterable)` to support any iterable, not just arrays.
7. **Chaining** — `add` returns `this` (per spec) so you can chain: `s.add(1).add(2)`.
8. **Performance** — array-backed `has` is O(n). For 10k items, every `add` already does a linear scan via `has`. For real workloads, Map-backed (O(1) avg) is the only viable option.

## Brute force approach
Array-backed with `indexOf` for `has`. Cleanest to write, O(n) per op. Useful when you want to show you understand the semantics but the data set is tiny (<100 items). Mention this as a baseline, then upgrade.

Don't use a plain object (`this._obj = {}`) as a backing store — keys would be coerced to strings, breaking objects/numbers/booleans-as-distinct-keys.

## Optimal approach
Map-backed. `Map` already provides O(1) average `has`/`set`/`delete`, SameValueZero equality, and insertion-order iteration. Set becomes a thin shim over Map. This is essentially how V8 implements it under the hood.

## Solution (JavaScript)

```js
/**
 * Polyfill of the built-in Set, with SameValueZero equality, insertion-order
 * iteration, and O(1) average has/add/delete.
 */
class MySet {
  constructor(iterable = []) {
    // Backing Map. Value side is unused; presence of key = membership.
    this._m = new Map();
    if (iterable != null) {
      for (const v of iterable) this.add(v);
    }
  }

  add(value) {
    this._m.set(value, true);
    return this;                       // chainable, per spec
  }

  has(value) {
    return this._m.has(value);
  }

  delete(value) {
    return this._m.delete(value);      // boolean: was-present
  }

  clear() {
    this._m.clear();
  }

  get size() {
    return this._m.size;
  }

  *[Symbol.iterator]() {
    yield* this._m.keys();             // insertion order
  }

  *keys()    { yield* this._m.keys(); }
  *values()  { yield* this._m.keys(); }
  *entries() { for (const k of this._m.keys()) yield [k, k]; }

  forEach(cb, thisArg) {
    for (const k of this._m.keys()) cb.call(thisArg, k, k, this);
  }
}
```

## Step-by-step dry run

Input:
```js
const s = new MySet([1, 2, 2, NaN, NaN, 'a']);
console.log(s.size);            // 3 distinct: 1, 2, 'a'? Wait — and NaN counts as 1.
console.log(s.has(NaN));        // true
console.log(s.has(2));          // true
console.log([...s]);            // insertion order
s.delete(2);
console.log(s.size);            // one fewer
```

Trace:
- `constructor([1,2,2,NaN,NaN,'a'])`: backing Map starts empty.
  - `add(1)`: `_m.set(1, true)`. size 1.
  - `add(2)`: size 2.
  - `add(2)`: `Map.set` overwrites — still size 2.
  - `add(NaN)`: Map treats NaN as a valid key (SameValueZero). size 3.
  - `add(NaN)`: overwrite. size 3.
  - `add('a')`: size 4.
- `s.size` → 4. (Outputs above were illustrative; the real count is 4.)
- `s.has(NaN)` → `_m.has(NaN)` → `true`. SameValueZero gives this for free.
- `[...s]` → `[1, 2, NaN, 'a']`. Insertion order preserved by Map.
- `s.delete(2)` → `true`. Size becomes 3.
- `[...s]` → `[1, NaN, 'a']`. Holes don't shift positions because Map maintains an ordered key list internally.

## Important takeaways

**Syntax to memorize**
- Backing store = `Map`, not array (for O(1) and SameValueZero for free).
- `add` returns `this` (chainable, per spec).
- `delete` returns boolean (was-present).
- `size` is a getter, not a stored counter.
- `*[Symbol.iterator]() { yield* this._m.keys(); }` for `for...of`.

**Patterns to reuse**
- "Reuse Map for collection semantics" — same trick works for WeakSet (on top of WeakMap), LRU cache (Map + ordering tricks), TTL set (Map + timer).
- Generator-method `Symbol.iterator` definition is the cleanest way to make any class iterable.

**Common mistakes**
- Array + `indexOf` for `has` — breaks on `NaN` (`NaN !== NaN`). Use `includes` or the `x !== x` check.
- Storing `size` as a number and forgetting to decrement on delete.
- Using a plain object as backing store — coerces all keys to strings.
- Forgetting to accept the iterable in the constructor — native Set takes `new Set([1,2,3])` and `new Set('abc')`.
- Not returning `this` from `add` — breaks chaining.

**Related questions**
- Map polyfill (same structure, but key→value pairs).
- WeakSet / WeakMap polyfill (requires actual weak refs — only possible with the built-in WeakRef/FinalizationRegistry; otherwise you can't truly polyfill).
- Array intersection/union/difference using Set.
- LRU cache (Map + reordering on access).

## Variants

1. **`OrderedSet` with explicit comparator** — accept a `equals(a, b)` function in the constructor. Becomes array-backed (you can't hash by user-defined equality without a hash function). Useful when you need value-equality (e.g., deep-equal objects).

2. **Polyfill `Set.prototype.intersection / union / difference`** — ES2025 additions. Trivial on top of `MySet`:
   ```js
   intersection(other) { return new MySet([...this].filter(x => other.has(x))); }
   union(other)        { return new MySet([...this, ...other]); }
   difference(other)   { return new MySet([...this].filter(x => !other.has(x))); }
   ```

3. **TTL Set** — entries auto-expire after `ttl` ms. Either active (per-entry `setTimeout`) or lazy (check expiry on `has`). Trade-off: timers consume memory, lazy is cheaper but bounded by access frequency.

4. **Read-only Set view** — `Object.freeze`-able wrapper exposing only `has`, `size`, iteration. Useful for safely sharing config sets across modules.

## Revision notes

> **Set polyfill — 45 second recap**
> - Back with `Map` (not array, not plain object). Get SameValueZero + O(1) + insertion-order for free.
> - Naive array+indexOf: O(n) has, broken on `NaN`. Use as a baseline only.
> - `add` returns `this`; `delete` returns boolean; `size` is a getter.
> - Iteration: `*[Symbol.iterator]() { yield* this._m.keys(); }`. Insertion order.
> - Constructor accepts any iterable, not just array.
> - Trap: NaN with strict equality, +0 vs -0, object references (always !==).
> - Same shape extends to Map polyfill and to TTL/LRU variants.
