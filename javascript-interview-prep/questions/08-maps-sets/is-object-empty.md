# Implement `isEmpty(obj)` — empty object/array/Map/Set

> **Difficulty:** Foundation   |   **Time:** ~5 min   |   **Prereqs:** [object-vs-map-vs-set.md](./object-vs-map-vs-set.md)
>
> **Source:** LeetCode #2727. 30-sec warmup that filters seniors.

---

## 1. Problem statement

Return true if input has no own properties / no elements. Handle plain object, array, Map, Set, null.

**Verification examples**

```js
isEmpty({});                              // true
isEmpty({a: 1});                          // false
isEmpty([]);                              // true
isEmpty([1]);                             // false
isEmpty(new Map());                       // true
isEmpty(new Set());                       // true
isEmpty(null);                            // true
```

**Constraints**
- O(1) — short-circuit, don't allocate keys array.
- `Object.keys(null)` throws; guard.
- Map/Set: use `.size`.
- Consider symbol keys for completeness.

---

## 2. Plain-English restatement

Short-circuit at first key/element. Don't allocate full keys list. Branch by collection type.

---

## 3. Why this matters in interviews

Looks trivial. Senior signal: O(1) over O(n), handle Map/Set, symbol keys, null guard.

---

## 4. Mental model

```
   Naive: Object.keys(obj).length === 0   ← O(n) + alloc.
   
   Better: for..in short-circuit:
     for (const _ in obj) return false
     return true
   → O(1) if any key exists; first hit short-circuits.
   But: for..in walks prototype enumerable; misses symbols.
   
   Best:
     - null/undefined → true.
     - Array → length === 0.
     - Map/Set → size === 0.
     - Plain object → for..in + Object.getOwnPropertySymbols.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why is `Object.keys(o).length === 0` O(n)?
> 2. Does `for..in` see symbols?
> 3. Does `Object.keys(new Map())` work?

---

## 6. Brute force — walked through

```js
const isEmptyBrute = (o) => Object.keys(o).length === 0;
```

Issues: O(n); null throws; misses symbols; lies for Map (always 0).

---

## 7. The unlocking insight

> **Branch by type. for..in short-circuits at first key (O(1)). Map/Set need `.size`. Null guard first.**

Three properties:

1. **Short-circuit** for O(1).
2. **Type branch** — Map/Set differ.
3. **Null guard** first.

---

## 8. Solution (annotated)

```js
function isEmpty(o) {
  if (o == null) return true;                                              // step 1: null guard
  if (Array.isArray(o)) return o.length === 0;                            // step 2: array
  if (o instanceof Map || o instanceof Set) return o.size === 0;          // step 3: Map/Set
  for (const _ in o) return false;                                         // step 4: O(1) string keys
  return Object.getOwnPropertySymbols(o).length === 0;                    // step 5: symbol keys
}
```

**Try it yourself**

```js
isEmpty({});                                                  // true
isEmpty({a: 1});                                              // false
isEmpty([]);                                                   // true
isEmpty([0]);                                                  // false
isEmpty(new Map());                                           // true
isEmpty(new Map([['a', 1]]));                                 // false
isEmpty(new Set([1]));                                        // false
isEmpty(null);                                                 // true
isEmpty(undefined);                                            // true
isEmpty('');                                                   // false (string is not object)

// Symbol-only object
const sym = Symbol('s');
isEmpty({[sym]: 1});                                          // false

// Prototype-inherited only — own-keys check
class Foo { bar() {} }
isEmpty(new Foo());                                           // true (no own keys)

// LeetCode #2727 likely doesn't require Map/Set handling; verify scope.
```

---

## 9. Step-by-step dry run

```
isEmpty({a:1, b:2}):
  Not null. Not array. Not Map/Set.
  for (_ in obj): first iteration 'a' → return false.
  O(1).

isEmpty({}):
  Not null/array/Map/Set.
  for..in body never runs (no keys).
  Continue past for.
  Object.getOwnPropertySymbols({}).length = 0 → true.

isEmpty(Object.keys(huge)):
  Allocates [...huge keys array] then checks length.
  O(n) + heap alloc.

isEmpty(new Map([['a', 1]])):
  instanceof Map → size===0? size is 1. Return false.
  
  vs naive Object.keys(new Map([['a',1]])).length === 0:
    Object.keys on a Map returns [] (no own enumerable properties).
    Naive returns true incorrectly.

isEmpty({[sym]: 1}):
  for..in skips symbols → body doesn't run.
  getOwnPropertySymbols → [sym]. length 1 → return false.
```

---

## 10. Common confusion + traps

1. **`Object.keys(null)` throws** — guard.
2. **`for..in` walks prototype** — usually OK; could see inherited.
3. **`Map` empty via `Object.keys`** — lies; always 0.
4. **`isEmpty(0)` / `isEmpty('')`** — primitives; define behavior.
5. **Symbols missed** — getOwnPropertySymbols.
6. **`hasOwnProperty` for safety** — for..in body short-circuits before this matters.
7. **Frozen empty object** — still empty.

---

## 11. Senior follow-ups & variants

### Variant 1 — Strict own-keys
`for..in` + `hasOwnProperty`.

### Variant 2 — `Reflect.ownKeys`
All own keys (strings + symbols).

### Variant 3 — Custom collections
Duck-type by `.size` or `[Symbol.iterator]`.

### Variant 4 — Deep "is-empty"
All nested values are empty.

### Variant 5 — Object check (not array/Map/Set)
`Object.prototype.toString.call(o) === '[object Object]'`.

---

## 12. How to think aloud

> "isEmpty looks trivial but the 30-second answer (`Object.keys(o).length === 0`) is wrong on three counts: O(n) + heap allocation when O(1) is possible; throws on null; lies on Map (returns 0 for non-empty Map because Map's items aren't own enumerable keys). Correct: null guard first; Array → `length === 0`; Map/Set → `size === 0`; plain object → `for (const _ in o) return false` short-circuits at first key (O(1)), then handle symbol keys via `Object.getOwnPropertySymbols`. for..in walks prototype enumerable; usually OK because Object.prototype has none, but for strict own-keys use `Object.hasOwn` (ES2022) or `hasOwnProperty.call`. Skip symbols? Default for..in skips them — for completeness explicitly check. Variants: `Reflect.ownKeys` returns both strings and symbols (own keys only — not inherited); duck-type custom collections by `.size` or `Symbol.iterator`; deep is-empty for nested. Trap: Object.keys length (O(n)); null throws; Map via keys-length (lies); missed symbols."

---

## 13. 60-second revision

> - **Null guard first.**
> - **Array → `length === 0`.**
> - **Map/Set → `size === 0`.**
> - **Object: `for..in` short-circuits O(1).**
> - **Symbols via `getOwnPropertySymbols`.**
> - **Avoid `Object.keys(o).length`** — O(n) + alloc.
> - **`Object.keys(map)`** lies (always 0).
> - **Trap:** null throws; missed Map; missed symbols.

---

**Related:** [object-vs-map-vs-set.md](./object-vs-map-vs-set.md) · [object-deep-diff.md](./object-deep-diff.md) · [convert-object-to-json-string.md](./convert-object-to-json-string.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
