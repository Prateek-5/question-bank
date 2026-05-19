# Polyfill `Set` (add / has / delete / size / iteration)

> **Difficulty:** Easy-Medium   |   **Time:** ~15 min   |   **Prereqs:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
>
> **Source:** BFE.dev, GreatFrontEnd polyfill series. The polyfill that teaches SameValueZero.

---

## 1. Problem statement

**Signature**
```ts
class MySet<T> {
  constructor(iterable?: Iterable<T>);
  add(v: T): this;
  has(v: T): boolean;
  delete(v: T): boolean;
  clear(): void;
  size: number;
  [Symbol.iterator](): Iterator<T>;
  forEach(cb: (v: T, _: T, set: this) => void, thisArg?: any): void;
}
```

**Input / Output examples**

| Setup                                          | Behaviour                                              |
|-------------------------------------------------|---------------------------------------------------------|
| `new MySet([1, 2, 2, NaN, NaN, 'a'])`          | size 4: `1, 2, NaN, 'a'` (NaN deduped via SameValueZero) |
| `s.add(1).add(2).add(3)`                       | chainable; returns `this`                              |
| `s.has(NaN)` after `s.add(NaN)`                | `true` (NaN === NaN under SameValueZero)               |
| `s.has(+0)` after `s.add(-0)`                  | `true` (+0 and -0 equal)                               |
| `[...s]`                                        | insertion order                                        |
| `s.add({}); s.has({})`                          | `false` (different refs)                               |

**Constraints**
- SameValueZero equality (NaN equals NaN; +0 equals -0).
- Insertion-order iteration.
- O(1) average `add`/`has`/`delete`.
- `size` is a getter, not a property.

---

## 2. Plain-English restatement

A built-in `Set` polyfill. Stores unique values. Key choice: how to handle `NaN`, `+0`/`-0`, and object references. The native API uses **SameValueZero** — `NaN === NaN` is true for membership; `+0 === -0` is true; objects use reference equality. The trick: back the polyfill with a **`Map`**, not an array, to inherit SameValueZero, O(1) ops, and insertion-order iteration.

---

## 3. Why this matters in interviews

Deceptively rich. The naive array-backed `indexOf` version breaks on `NaN`. Interviewers escalate: "What about NaN? +0 vs -0? Iteration order? Complexity?" Probes hash tables, SameValueZero, `Symbol.iterator`, and the ways JS objects differ from hash maps in other languages.

---

## 4. Mental model

```
   Backed by Map (Map<value, true>):
   ┌──────────────────────────────────────────┐
   │ _m: Map<T, true>                         │
   ├──────────────────────────────────────────┤
   │ 1     → true                             │
   │ 2     → true                             │
   │ NaN   → true   (SameValueZero!)          │
   │ 'a'   → true                             │
   └──────────────────────────────────────────┘

   add(v):    _m.set(v, true); return this
   has(v):    _m.has(v)
   delete(v): _m.delete(v)
   size:      get → _m.size
   iter:      yield* _m.keys()

   Why Map > array?
     - O(1) has/add/delete (avg) vs O(n)
     - SameValueZero for free (Map already uses it)
     - Insertion order preserved
     - No need to write NaN dance manually
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Does `[1, NaN].indexOf(NaN)` return `1` or `-1`? Why does that matter for a Set polyfill?
> 2. What does `add(+0); has(-0)` return?
> 3. Why is backing with a plain object `{}` wrong?

---

## 6. Brute force — walked through

### Wrong attempt 1: array + `indexOf`
```js
has(v) { return this.items.indexOf(v) !== -1; }
```
`indexOf` uses strict equality — `NaN !== NaN` → can't find NaN. Use `includes` (SameValueZero) or the `x !== x && v !== v` trick.

### Wrong attempt 2: plain object as backing
```js
this._obj = {};
this._obj[key] = true;
```
Keys are coerced to strings. `add(1)` and `add('1')` collide; objects become `"[object Object]"`. Use Map.

### Wrong attempt 3: stored `size` counter
Maintaining a counter manually is fragile; forget to decrement on delete and `size` drifts. Use a getter over `_m.size`.

---

## 7. The unlocking insight

> **Back with `Map<value, true>`. Inherits SameValueZero, O(1) ops, and insertion-order iteration for free. The polyfill becomes a thin shim.**

Three properties:

1. **`Map` already does the hard work** — SameValueZero, ordering, O(1).
2. **`size` as getter** over the backing Map's `size`.
3. **Generator `*[Symbol.iterator]()`** for `for...of` + spread.

---

## 8. Solution (annotated)

```js
class MySet {
  constructor(iterable = []) {
    this._m = new Map();                                              // step 1: Map-backed
    if (iterable != null) {
      for (const v of iterable) this.add(v);                          // step 2: accept any iterable
    }
  }

  add(value) {
    this._m.set(value, true);
    return this;                                                       // step 3: chainable per spec
  }

  has(value) {
    return this._m.has(value);                                         // SameValueZero for free
  }

  delete(value) {
    return this._m.delete(value);                                      // step 4: returns boolean
  }

  clear() {
    this._m.clear();
  }

  get size() {                                                         // step 5: getter, not property
    return this._m.size;
  }

  *[Symbol.iterator]() {
    yield* this._m.keys();                                             // step 6: insertion order
  }

  *keys()    { yield* this._m.keys(); }
  *values()  { yield* this._m.keys(); }
  *entries() { for (const k of this._m.keys()) yield [k, k]; }

  forEach(cb, thisArg) {
    for (const k of this._m.keys()) cb.call(thisArg, k, k, this);
  }
}
```

**Try it yourself**

```js
const s = new MySet([1, 2, 2, NaN, NaN, 'a']);
s.size;                          // 4 (deduped)
s.has(NaN);                       // true (SameValueZero)
s.has(2);                          // true
[...s];                            // [1, 2, NaN, 'a'] (insertion order)
s.add({}).add({});                 // chainable; two different refs → size 6
s.delete(2);                       // true → size 5
```

---

## 9. Step-by-step dry run

```
new MySet([1, 2, 2, NaN, NaN, 'a']):
  _m starts empty
  add(1):   _m.set(1, true)    → size 1
  add(2):   _m.set(2, true)    → size 2
  add(2):   _m.set(2, true)    → existing key, size still 2
  add(NaN): _m.set(NaN, true)  → size 3 (SameValueZero)
  add(NaN): existing → size still 3
  add('a'): _m.set('a', true)  → size 4

s.has(NaN):   _m.has(NaN) → true   (SameValueZero NaN equals NaN)
s.has(+0) after s.add(-0):  → true   (SameValueZero treats them equal)

[...s]:
  yield* _m.keys() → 1, 2, NaN, 'a'   (insertion order preserved)

s.delete(2):
  _m.delete(2) → true. size 3.
```

---

## 10. Common confusion + traps

1. **`indexOf` for `has`** — broken on `NaN`.
2. **Plain object backing** — keys coerced to strings.
3. **Stored `size` counter** — drifts when delete misses; use getter.
4. **Not returning `this` from `add`** — breaks chaining.
5. **Constructor only accepting array** — native accepts any iterable.
6. **Iterating while mutating** — implementation-defined; native handles via insertion-order; don't promise this unless asked.
7. **`+0` vs `-0`** — `===` already treats them equal; mention for senior cred.

---

## 11. Senior follow-ups & variants

### Variant 1 — `intersection` / `union` / `difference` (ES2025)
```js
intersection(other) { return new MySet([...this].filter((x) => other.has(x))); }
union(other)        { return new MySet([...this, ...other]); }
difference(other)   { return new MySet([...this].filter((x) => !other.has(x))); }
```

### Variant 2 — TTL Set
Entries auto-expire after `ttl` ms. Active (per-entry timer) or lazy (check expiry on `has`). Lazy is cheaper.

### Variant 3 — Custom equality
Accept `equals(a, b)` in constructor. Becomes array-backed (no hash function for user equality). Useful for deep-equal keys.

### Variant 4 — Read-only view
`Object.freeze`-able wrapper exposing only `has`, `size`, iteration.

### Variant 5 — Map polyfill
Same structure: backing the polyfill itself with another Map is circular, but the implementation pattern (insertion-order linked list + hash bucket) generalizes.

---

## 12. How to think aloud

> "Back with `Map<value, true>`. Inherits SameValueZero, O(1) ops, insertion-order iteration. Polyfill is a thin shim. `add` returns `this` (chainable). `delete` returns boolean. `size` is a getter, not a stored counter. `*[Symbol.iterator]() { yield* this._m.keys() }` for `for...of` + spread. Constructor accepts any iterable, not just array. Trap: `indexOf` for has breaks on `NaN`. Trap: plain object backing coerces keys to strings. Trap: stored size counter drifts. Same pattern extends to Map polyfill and TTL/LRU sets."

---

## 13. 60-second revision

> - **Back with `Map<value, true>`** (NOT array, NOT plain object).
> - **SameValueZero** (NaN===NaN, +0===-0) — Map gives this free.
> - **`add` returns `this`**; **`delete` returns boolean**; **`size` is getter**.
> - **`*[Symbol.iterator]() { yield* _m.keys() }`** for iteration.
> - **Constructor accepts any iterable.**
> - **ES2025:** `intersection`/`union`/`difference`/`isSubsetOf`/etc.
> - **TTL Set** = Map<v, expiry> + lazy expire on `has`.
> - **Trap:** indexOf for has; plain object; stored size; not returning `this`.

---

**Related:** [memoize.md](./memoize.md) · [lru-cache.md](./lru-cache.md) · [bloom-filter.md](./bloom-filter.md) · [`08-maps-sets/set-deduplication.md`](../08-maps-sets/set-deduplication.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
