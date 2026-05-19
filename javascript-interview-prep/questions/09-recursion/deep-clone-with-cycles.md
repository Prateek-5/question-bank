# `deepClone(obj)` — cycles, Date, RegExp, Map, Set

> **Difficulty:** Senior   |   **Time:** ~20 min   |   **Prereqs:** [`07-arrays/structured-clone-vs-spread.md`](../07-arrays/structured-clone-vs-spread.md), [`08-maps-sets/weakmap-memoize.md`](../08-maps-sets/weakmap-memoize.md)
>
> **Source:** Canonical machine-coding.

---

## 1. Problem statement

Recursively clone an object preserving Date/RegExp/Map/Set + handling cycles.

**Verification examples**

```js
const orig = { a: 1, b: {c: 2}, d: new Date(), m: new Map([[1, 'x']]) };
orig.self = orig;                        // cycle

const clone = deepClone(orig);
clone !== orig;                          // true (deep)
clone.b !== orig.b;                      // true (deep)
clone.d instanceof Date;                 // true
clone.m instanceof Map;                  // true
clone.self === clone;                    // true (cycle preserved)
clone.self !== orig.self;                // true (clone's cycle, not orig's)
```

**Constraints**
- Cycle detection via WeakMap<orig, clone>.
- Register clone in seen BEFORE recursing children.
- Handle Date, RegExp, Map, Set, Array, plain Object.
- Stack-safe for deep input (heap-based seen).
- Function/Symbol: usually skipped or shallow-copy.

---

## 2. Plain-English restatement

Walk the value. Primitives return as-is. For objects: check seen (cycle); allocate clone; register; recurse children. Type-discriminate Date/RegExp/Map/Set.

---

## 3. Why this matters in interviews

THE recursion+identity+type question. Probes: reject `JSON.parse(JSON.stringify)`, reach for WeakMap, handle built-ins, mention structuredClone exists.

---

## 4. Mental model

```
   deepClone(value, seen = WeakMap):
     1. primitive → return value.
     2. seen.has(value) → return seen.get(value)   ← cycle break
     3. Allocate clone by type:
        - Array: []
        - Date: new Date(value)
        - RegExp: new RegExp(value.source, value.flags)
        - Map: new Map()
        - Set: new Set()
        - other: Object.create(getPrototypeOf(value))   ← preserves class
     4. seen.set(value, clone)   ← REGISTER BEFORE RECURSE
     5. Walk children, recurse, assign on clone:
        Array/Object: enumerable own keys
        Map: entries; clone keys and values
        Set: values; clone each
     6. Return clone.
   
   Why register-before-recurse:
     A → B → A.
     Without register: deepClone(A) → recurse B → recurse A → infinite.
     With register: deepClone(A) seen={A: cloneA}, recurse B, B sees A in seen → cloneA. Done.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why register BEFORE recursing?
> 2. Why WeakMap not Map?
> 3. What about functions / Symbol keys?

---

## 6. Brute force — walked through

```js
const wrong = JSON.parse(JSON.stringify(obj));
// LOSES: fn, Date (→ string), undefined, RegExp (→ {}), Map/Set,
// BigInt (throws), Symbol keys, prototype.
// THROWS on cycles.
```

Reject upfront.

---

## 7. The unlocking insight

> **WeakMap<orig, clone>. Register BEFORE recurse children. Type-dispatch Date/RegExp/Map/Set/Array/Object. structuredClone() is modern alternative.**

Three properties:

1. **WeakMap cycle tracker**.
2. **Register first**, recurse second.
3. **Type-dispatch** for built-ins.

---

## 8. Solution (annotated)

```js
function deepClone(value, seen = new WeakMap()) {
  // 1. Primitives
  if (value === null || typeof value !== 'object') return value;          // step 1: base

  // 2. Cycle check
  if (seen.has(value)) return seen.get(value);                            // step 2: cycle break

  // 3. Type dispatch
  let clone;
  if (Array.isArray(value)) {
    clone = [];
  } else if (value instanceof Date) {
    clone = new Date(value);                                                // step 3: Date
  } else if (value instanceof RegExp) {
    clone = new RegExp(value.source, value.flags);
  } else if (value instanceof Map) {
    clone = new Map();
  } else if (value instanceof Set) {
    clone = new Set();
  } else {
    clone = Object.create(Object.getPrototypeOf(value));                   // step 4: preserve prototype
  }

  // 4. Register BEFORE recurse
  seen.set(value, clone);                                                  // step 5: critical

  // 5. Recurse children
  if (Array.isArray(value)) {
    for (let i = 0; i < value.length; i++) {
      clone[i] = deepClone(value[i], seen);
    }
  } else if (value instanceof Map) {
    for (const [k, v] of value) {
      clone.set(deepClone(k, seen), deepClone(v, seen));                   // step 6: clone Map entries
    }
  } else if (value instanceof Set) {
    for (const v of value) {
      clone.add(deepClone(v, seen));
    }
  } else if (!(value instanceof Date) && !(value instanceof RegExp)) {
    for (const k of Object.keys(value)) {                                   // step 7: own enumerable
      clone[k] = deepClone(value[k], seen);
    }
  }

  return clone;
}

// Modern alternative
function deepCloneModern(obj) {
  return structuredClone(obj);                                              // Node 17+, all browsers
}
```

**Try it yourself**

```js
// Cycle
const o = { a: 1 };
o.self = o;
const c = deepClone(o);
c.self === c;                                                  // true
c.self !== o;                                                  // true (independent clone)

// Date
const d = { t: new Date('2024-01-01') };
const cd = deepClone(d);
cd.t instanceof Date;                                          // true
cd.t !== d.t;                                                  // true (new Date)
cd.t.getTime() === d.t.getTime();                              // true

// Map of Maps
const m = new Map([[1, new Map([[2, 'nested']])]]);
const cm = deepClone(m);
cm !== m;
cm.get(1).get(2);                                              // 'nested'
cm.get(1) !== m.get(1);                                        // independent

// Class instances — prototype preserved (Object.create + getPrototypeOf)
class Point { constructor(x, y) { this.x = x; this.y = y; } }
const p = new Point(1, 2);
const cp = deepClone(p);
cp instanceof Point;                                           // true
cp.x;                                                          // 1

// Function — not cloned (shallow)
const f = { fn: () => 1 };
const cf = deepClone(f);
cf.fn === f.fn;                                                // true (shared, not cloned)

// structuredClone for comparison
structuredClone({ d: new Date() }).d instanceof Date;          // true
// structuredClone({ fn: () => 1 });                          // DataCloneError
```

---

## 9. Step-by-step dry run

```
const o = { a: 1 }; o.self = o; deepClone(o):

Enter deepClone(o):
  Not primitive. seen.has(o) false.
  Type: plain Object. clone = Object.create(Object.getPrototypeOf(o)) = {}.
  seen.set(o, clone).   ← REGISTER
  
  Recurse children:
    key 'a': deepClone(1) → 1. clone.a = 1.
    key 'self': deepClone(o, seen):
      Not primitive. seen.has(o) TRUE. Return seen.get(o) = clone. ← cycle break
    clone.self = clone.   ← self-cycle in clone
  
  Return clone.

Result:
  clone.a === 1.
  clone.self === clone.   ← independent cycle.
  o.self === o (orig unchanged).

If we DID NOT register before recurse:
  deepClone(o):
    clone = {}.
    Recurse 'self': deepClone(o):
      clone = {}.
      Recurse 'self': deepClone(o):
        ... infinite.

deepClone of Map [['x', {n: 1}]]:
  type Map. clone = new Map().
  seen.set(orig, clone).
  Recurse entries:
    [k='x', v={n:1}]:
      clone.set(deepClone('x'), deepClone({n:1})).
      deepClone('x') = 'x' (primitive).
      deepClone({n:1}):
        type object. clone' = {}. seen.set.
        clone'.n = 1.
        return clone'.
      clone.set('x', {n:1}).

deepClone of class instance Point:
  prototype = Point.prototype.
  clone = Object.create(Point.prototype).
  for each own key: clone[k] = recurse.
  Result: instanceof Point true.
```

---

## 10. Common confusion + traps

1. **`JSON.parse(JSON.stringify(o))`** — silent data loss + cycle throw.
2. **Register AFTER recurse** — infinite loop on cycles.
3. **Use Map not WeakMap** — works but originals can't be GC'd.
4. **Drop prototype** — class instance becomes plain object.
5. **Functions clone** — typically shared.
6. **Symbol keys** — `Object.keys` misses; use `Reflect.ownKeys`.
7. **Recursive on deep** — stack overflow; iterative + explicit work stack.

---

## 11. Senior follow-ups & variants

### Variant 1 — `structuredClone`
Node 17+, all browsers; handles cycles, TypedArrays, but throws on fn.

### Variant 2 — Symbol keys
`Reflect.ownKeys` instead of `Object.keys`.

### Variant 3 — Iterative
Replace recursion with explicit work stack — depth-safe.

### Variant 4 — Selective deep
WeakSet of types to deep-clone; rest shallow.

### Variant 5 — Lodash `_.cloneDeep`
Most flexible; supports custom customizer.

---

## 12. How to think aloud

> "Reject `JSON.parse(JSON.stringify(obj))` upfront: loses functions, Date becomes ISO string, RegExp becomes `{}`, Map/Set become `{}`, BigInt throws, Symbol keys lost, prototype lost, cycles throw. Modern alternative: `structuredClone(obj)` (Node 17+, all browsers since 2022) — uses Structured Clone Algorithm; handles Date, RegExp, Map, Set, TypedArrays, cycles correctly; throws on functions/DOM nodes/Symbol keys. Manual implementation: recursion with `WeakMap<orig, clone>` for cycle tracking — must `seen.set(value, clone)` BEFORE recursing children, otherwise `A → B → A` cycles infinitely. WeakMap over Map: lets GC reclaim originals once clone is done. Type dispatch: Array → `[]`, Date → `new Date(value)`, RegExp → `new RegExp(value.source, value.flags)`, Map → `new Map()`, Set → `new Set()`, plain object → `Object.create(getPrototypeOf(value))` to preserve class identity (`clone instanceof Point` works). Recurse: Array indices, Map entries (clone keys AND values), Set members, Object own enumerable keys. Caveats: functions usually shared (can't deep-clone fn); Symbol keys use `Reflect.ownKeys`; stack depth = nesting depth — for 100k-deep linked lists use iterative explicit stack. Trap: register-after-recurse (infinite); JSON trick; drop prototype; forget Symbol keys."

---

## 13. 60-second revision

> - **`WeakMap<orig, clone>`** cycle tracker.
> - **Register BEFORE recurse** — cycles otherwise infinite.
> - **Type dispatch:** Date/RegExp/Map/Set/Array/Object.
> - **`Object.create(getPrototypeOf)`** preserves class.
> - **`structuredClone`** modern alternative.
> - **Reject `JSON.parse(JSON.stringify)`** — list losses.
> - **Iterative for deep** — heap stack.
> - **`Reflect.ownKeys`** for Symbol keys.
> - **Trap:** register-after; JSON trick; drop prototype; fn cloning.

---

**Related:** [`07-arrays/structured-clone-vs-spread.md`](../07-arrays/structured-clone-vs-spread.md) · [`08-maps-sets/weakmap-memoize.md`](../08-maps-sets/weakmap-memoize.md) · [deep-merge-with-cycles.md](./deep-merge-with-cycles.md) · [trampoline-pattern.md](./trampoline-pattern.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md), [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
