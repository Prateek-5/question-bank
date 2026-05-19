# Map vs Record / Tuple (future proposal)

> **Difficulty:** Senior   |   **Time:** ~10 min   |   **Prereqs:** [composite-key-strategies.md](./composite-key-strategies.md), [object-vs-map-vs-set.md](./object-vs-map-vs-set.md)
>
> **Source:** TC39 Records & Tuples (Stage 2). Razorpay, Cloudflare — modern spec awareness.

---

## 1. Problem statement

JS lacks value-typed immutable composites. Records/Tuples (Stage 2) would add `#{}` and `#[]` with structural equality. Discuss today vs future.

**Verification examples**

```js
// Today
{a: 1} === {a: 1};                       // false (identity)
[1, 2] === [1, 2];                       // false

// Future (Stage 2)
#{a: 1} === #{a: 1};                     // true (structural)
#[1, 2] === #[1, 2];                     // true

// Map with object key — today
const m = new Map();
m.set({id: 1}, 'a');
m.get({id: 1});                          // undefined (different ref)

// With Record/Tuple keys — future
m.set(#{id: 1}, 'a');
m.get(#{id: 1});                         // 'a'  (structural eq)
```

**Constraints**
- Stage 2: not in any engine.
- Polyfills (`@bloomberg/record-tuple-polyfill`) for prototypes only.
- Records/Tuples contain only primitives, other records, other tuples (no objects/functions).
- Deeply immutable.

---

## 2. Plain-English restatement

JS has no value-typed objects. Records/Tuples are immutable, structurally equal composites — `#{}` / `#[]`. Stage 2, not shipped. Today's workarounds: stringify, nested Map, lib like Immutable.

---

## 3. Why this matters in interviews

Modern-spec awareness signal. Senior bar: know proposal, semantics, today's workarounds.

---

## 4. Mental model

```
   Records (#{}): immutable, structural-equality objects.
   Tuples (#[]):  immutable, structural-equality arrays.
   
   Equality:
     #{a:1, b:2} === #{a:1, b:2}        // true (deep structural)
     #{a:1, b:2} === #{b:2, a:1}        // true (order-independent)
     #[1, 2] === #[1, 2]                 // true
   
   Constraints:
     Can contain: primitives (number, string, bigint, bool, null, undefined, Symbol), records, tuples.
     Cannot contain: regular objects, arrays, functions, Date, Map, Set.
   
   typeof:
     typeof #{} === 'record'
     typeof #[] === 'tuple'
   
   Use cases:
     - React state — referential equality without manual memoization.
     - Map keys with value-equality (`m.get(#{x:1, y:2})`).
     - Set membership — `mySet.has(#{a:1})`.
     - Memoization keys for objects.
   
   Today's workarounds:
     1. JSON.stringify as key — brittle (key order).
     2. Stable hash function (lodash.hash, fast-hash).
     3. Immutable.js / Immer — third-party.
     4. Nested Map for tuples.
     5. Symbol-interned tuples.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Can a Record contain a Date?
> 2. What's `typeof #{}` ?
> 3. What stops `#{a: () => 1}`?

---

## 6. Brute force — walked through

```js
// Today: Map with object key — broken
const m = new Map();
m.set({id: 1}, 'a');
m.get({id: 1});           // undefined — different object ref
```

---

## 7. The unlocking insight

> **Records/Tuples (#{}, #[]) — value-typed, structural eq, deeply immutable, primitives-only inside. Stage 2 not shipped; use workarounds today.**

Three properties:

1. **Structural equality** by content.
2. **Deeply immutable**.
3. **Primitives only** inside.

---

## 8. Solution (annotated)

```js
// Today's workaround #1: JSON.stringify key (brittle)
class StringKeyMap {
  #m = new Map();
  #key(obj) {
    // Sort keys for deterministic order
    const ordered = Object.keys(obj).sort().reduce((acc, k) => {
      acc[k] = obj[k];
      return acc;
    }, {});
    return JSON.stringify(ordered);
  }
  set(obj, v) { this.#m.set(this.#key(obj), v); return this; }
  get(obj) { return this.#m.get(this.#key(obj)); }
}

// Today's workaround #2: stable hash function
const hash = require('object-hash');
class HashKeyMap {
  #m = new Map();
  set(obj, v) { this.#m.set(hash(obj), v); return this; }
  get(obj) { return this.#m.get(hash(obj)); }
}

// Future (Stage 2 — when shipped)
// const m = new Map();
// m.set(#{id: 1}, 'value');
// m.get(#{id: 1});           // 'value' — structural equality

// Polyfill (prototype only)
// import { Record, Tuple } from '@bloomberg/record-tuple-polyfill';
// Record({a: 1}) === Record({a: 1});  // true

// Records as React keys
// function MemoComponent({ data }) {
//   // data is #{}; reference stable across renders if content unchanged.
// }
```

**Try it yourself**

```js
// Today — Map by object content (using JSON.stringify, brittle)
const m = new StringKeyMap();
m.set({x: 1, y: 2}, 'point-1');
m.get({x: 1, y: 2});                                          // 'point-1'
m.get({y: 2, x: 1});                                          // 'point-1' (sorted keys)

// Brittle cases:
m.get({x: 1, y: 2, z: undefined});                            // undefined keys are dropped by JSON
m.get({x: 1.0, y: 2});                                        // 1 stringifies to '1' (fine)
m.get({x: 1n, y: 2});                                         // throws (BigInt in JSON)
m.set({fn: () => 1}, 'x');                                    // fn dropped → key collision risk

// Future — Records would handle these (where applicable)
// #{x: 1, y: 2} === #{x: 1, y: 2}                            // true
// const m2 = new Map();
// m2.set(#{x: 1, y: 2}, 'point-1');
// m2.get(#{y: 2, x: 1});                                     // 'point-1' (order-independent)

// React example (with Record)
// const config = useMemo(() => #{theme: 'dark', size: 'lg'}, []);
// // Stable across renders — content-based equality.
```

---

## 9. Step-by-step dry run

```
Today: Map with object key.
  m.set({id: 1}, 'a').
  m has entry with reference {id:1}-A as key.
  
  m.get({id: 1}).
  {id:1}-B is different reference.
  Map.has uses SameValueZero on keys → identity for objects → not found.
  Return undefined.

JSON.stringify workaround:
  key1 = JSON.stringify({id:1, name:'a'}) → '{"id":1,"name":"a"}'.
  key2 = JSON.stringify({name:'a', id:1}) → '{"name":"a","id":1}'.
  key1 !== key2 → COLLIDES MISS.
  Fix: sort keys before stringify.

Future Records:
  #{id: 1, name: 'a'} === #{name: 'a', id: 1}.
  Compiled / interpreted as: canonical hash by content; order-independent.
  Records are primitives in the spec sense (===, typeof 'record').
```

---

## 10. Common confusion + traps

1. **Stage 2 ≠ shipped** — no engine has it yet.
2. **Polyfill is incomplete** — `===` can't be polyfilled.
3. **Records can hold objects** — NO. Primitives + records + tuples only.
4. **`JSON.stringify` key order** — not deterministic; sort first.
5. **Records vs frozen objects** — frozen objects still have identity equality.
6. **Comparison performance** — structural eq is O(content size); not free.
7. **Records and TypeScript** — TS has type-level Records; different concept.

---

## 11. Senior follow-ups & variants

### Variant 1 — `Object.freeze` for immutability
Today's partial answer; identity equality still.

### Variant 2 — Immutable.js / Immer
Third-party value-typed.

### Variant 3 — `Map<JSON.stringify(key), value>`
Brittle but ships today.

### Variant 4 — Bloomberg / TC39 polyfill
Stage-2 ergonomics; not `===` (uses `.equals`).

### Variant 5 — Map.groupBy with Record-like keys
Future: composite keys natively.

---

## 12. How to think aloud

> "JS lacks value-typed immutable composites. `{a: 1} === {a: 1}` is false because objects compare by reference. Records and Tuples are a Stage 2 proposal that would add `#{a: 1}` and `#[1, 2]` with structural equality (`#{a:1} === #{a:1}` true; order-independent) and deep immutability. Constraints: records and tuples can only contain primitives (including BigInt, Symbol), other records, and other tuples — no objects, arrays, Dates, Maps, functions. `typeof #{} === 'record'`, `typeof #[] === 'tuple'`. Use cases: React state with referential equality without manual memoization; Map keys with value-equality (`m.get(#{x:1, y:2})`); Set membership with content. Today's workarounds: (1) `JSON.stringify` key with sorted keys — brittle (BigInt throws, undefined dropped, functions dropped); (2) stable hash function (object-hash, fast-hash); (3) Immutable.js / Immer — third-party; (4) nested Map for tuples; (5) Symbol-interned tuples. Stage 2 ≠ shipped; no engine has them yet (Bloomberg polyfill exists but can't make `===` work — uses `.equals` instead). Trap: assuming polyfill is complete; Records holding objects (not allowed); JSON.stringify non-determinism."

---

## 13. 60-second revision

> - **Records/Tuples:** Stage 2 proposal.
> - **`#{}` / `#[]`** — structural equality, deeply immutable.
> - **Primitives only inside** — no objects, fns, Date.
> - **`typeof #{} === 'record'`.**
> - **Use cases:** React state, Map keys, Set membership.
> - **Today's workarounds:** JSON.stringify (sorted), stable hash, Immutable.js.
> - **Polyfill exists** but can't override `===`.
> - **Trap:** assume shipped; records holding objects; JSON order.

---

**Related:** [composite-key-strategies.md](./composite-key-strategies.md) · [object-vs-map-vs-set.md](./object-vs-map-vs-set.md) · [ordered-map-insertion-order-quiz.md](./ordered-map-insertion-order-quiz.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
