# Object vs Map vs Set — when to use which

> **Difficulty:** Foundation   |   **Time:** ~10 min   |   **Prereqs:** [`07-arrays/array-dedup.md`](../07-arrays/array-dedup.md)
>
> **Source:** Canonical conceptual. Every senior JS round.

---

## 1. Problem statement

Pick the right keyed collection for the task. Know the trade-offs cold.

**Verification scenarios**

```js
// Object: static shape, JSON-friendly
const config = { port: 3000, host: 'localhost' };

// Map: any key type, insertion order, O(1) size
const cache = new Map();
cache.set({}, 1);                                 // object key — Object would coerce
cache.size;                                       // O(1)

// Set: dedup / membership
const seen = new Set([1, 2, 2, 3]);              // {1, 2, 3}
seen.has(2);

// WeakMap / WeakSet: GC-friendly metadata
const meta = new WeakMap();
meta.set(domNode, { hits: 0 });                  // released when domNode GC'd
```

**Constraints**
- Object keys: strings/symbols only; numeric coerced.
- Map keys: any (objects, NaN, etc.).
- Set/Map use SameValueZero (NaN handled).
- Object `.size` is O(n); Map `.size` is O(1).
- WeakMap/WeakSet keys must be objects; entries vanish on GC.

---

## 2. Plain-English restatement

A decision table: Object for static shapes / JSON / config. Map for runtime keyed data, any key type. Set for unique-membership. WeakMap/WeakSet for object-keyed metadata you want GC'd.

---

## 3. Why this matters in interviews

"I use JS" vs "I understand JS." Every senior has been burned by prototype pollution, string-only keys, `for..in` walking prototype, JSON ignoring Maps.

---

## 4. Mental model

```
   Decision table:
   
   Need               | Pick       | Why
   -------------------+------------+----------------------------------
   Static shape       | Object     | hidden class, inline cache.
   JSON-friendly      | Object     | JSON.stringify works.
   Dynamic key churn  | Map        | no shape deopt; O(1) size.
   Non-string key     | Map        | objects/NaN preserved.
   Insertion order    | Map        | guaranteed by spec.
   Unique items       | Set        | O(1) has + add.
   Object key + GC    | WeakMap    | auto-cleanup.
   Object membership  | WeakSet    | auto-cleanup.
   
   Equality:
     Map/Set: SameValueZero (NaN === NaN; +0 === -0).
     Object: string coercion (5 and '5' collide).
   
   Iteration:
     Map: insertion order.
     Object: integer-like keys ascending, then strings insertion, then Symbols.
     Set: insertion order.
   
   Prototype pollution:
     {} inherits Object.prototype → 'toString', '__proto__' keys are dangerous.
     Object.create(null) for safer.
     Map has none.
   
   JSON:
     JSON.stringify(map) → '{}' (Map → empty object).
     JSON.stringify(set) → '{}'.
     Use replacer or .entries() / [...set].
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `JSON.stringify(new Map([[1, 'a']]))` return?
> 2. Why does `obj[5]` equal `obj['5']`?
> 3. When use WeakMap vs Map?

---

## 6. Brute force — walked through

```js
// Object as map — these break:
const o = {};
o['__proto__'] = 'bad';                          // prototype pollution
o[5] = 1; o['5'];                                 // string coercion — collide
Object.keys(o).length;                            // O(n)
for (const k in o) ...;                           // walks prototype
```

---

## 7. The unlocking insight

> **Map is the general-purpose keyed collection — use it by default. Object only for static shapes / JSON. Set for membership. WeakMap/WeakSet for GC-friendly metadata.**

Three properties:

1. **Default to Map** for dynamic data.
2. **Object for JSON/static.**
3. **WeakMap/WeakSet** for auto-cleanup.

---

## 8. Solution (annotated)

```js
// Object — static config; JSON-friendly
const config = Object.freeze({                                            // step 1: immutable static
  port: 3000,
  host: 'localhost',
});

// Object as dictionary (with care)
const dict = Object.create(null);                                          // step 2: no prototype pollution
dict['__proto__'] = 'safe';                                                // own key, not prototype

// Map — general-purpose keyed collection
const cache = new Map();
cache.set('key1', 'value1');
cache.set({}, 'object key');                                               // step 3: any key
cache.set(NaN, 'NaN works');
cache.size;                                                                // O(1)

for (const [k, v] of cache) {                                              // step 4: insertion order
  console.log(k, v);
}

// Set — dedup / membership
const seen = new Set();
seen.add(1); seen.add(1);                                                   // step 5: idempotent
seen.size;                                                                  // 1
seen.has(1);                                                                // true

// WeakMap — object-keyed metadata
const requestMeta = new WeakMap();
function tagRequest(req, meta) {
  requestMeta.set(req, meta);                                               // step 6: GC-friendly
}
// When req is GC'd, the meta entry vanishes automatically.

// WeakSet — object membership with GC
const visited = new WeakSet();
function visit(node) {
  if (visited.has(node)) return;
  visited.add(node);
  // process
}
```

**Try it yourself**

```js
// JSON quirks
JSON.stringify(new Map([[1, 'a']]));                          // '{}' — Map → {}
JSON.stringify([...new Map([[1, 'a']])]);                     // '[[1,"a"]]' — array works
JSON.stringify(Object.fromEntries(map));                       // '{"1":"a"}'

// String coercion in Object
const o = {};
o[5] = 'five';
o['5'];                                                        // 'five' — same key
o[true] = 'bool';
o['true'];                                                     // 'bool' — coerced

// Map handles NaN
const m = new Map();
m.set(NaN, 1);
m.get(NaN);                                                    // 1

// for..in vs for..of
const obj = { a: 1 };
Object.prototype.bad = 'leak';
for (const k in obj) console.log(k);                          // 'a', 'bad' — walks prototype!
for (const k of Object.keys(obj)) console.log(k);             // 'a' only — own enumerable

// Map size O(1) vs Object O(n)
const m2 = new Map();
m2.size;                                                       // direct property — O(1)
Object.keys({a:1, b:2}).length;                               // O(n) — must enumerate
```

---

## 9. Step-by-step dry run

```
Object as map traps:
  o = {}
  o[5] = 'a' → o['5'] = 'a' (string coerced).
  o[true] = 'b' → o['true'] = 'b'.
  o[{a:1}] = 'c' → o['[object Object]'] = 'c'.
  o[null] = 'd' → o['null'] = 'd'.
  
  All keys collide if they string-coerce to the same value.

Map preserves identity:
  m.set(5, 'a'); m.get(5) === 'a'; m.get('5') === undefined.
  m.set(obj, 'b'); m.get(obj) === 'b'.

JSON.stringify(map):
  JSON has no concept of Map.
  Result: '{}'.
  Workaround: [...map] or Object.fromEntries(map) (if keys are strings).

WeakMap behavior:
  let req = { id: 1 };
  wm.set(req, 'meta');
  req = null;     // remove last strong ref
  // GC later: entry removed automatically.
  // No way to detect; no iteration on WeakMap (by design).

for..in walks prototype:
  Object.prototype.foo = 'leak'.
  for (const k in {a: 1}) → 'a', 'foo'.
  Object.keys filters to own enumerable.
```

---

## 10. Common confusion + traps

1. **`{}` for runtime keyed data** — string coercion + prototype pollution.
2. **`Object.keys(obj).length`** — O(n); Map size O(1).
3. **JSON.stringify(map)** — `{}`.
4. **`for..in`** walks prototype — use Object.keys.
5. **WeakMap not iterable** — by design (GC).
6. **WeakSet for primitives** — only objects allowed.
7. **Map insertion order** — preserved; Object integer keys reorder.

---

## 11. Senior follow-ups & variants

### Variant 1 — WeakMap private state
Use as `#private` analog pre-class-fields.

### Variant 2 — `Object.fromEntries` / `entries`
Bridge Map ↔ Object.

### Variant 3 — ES2024 `Object.groupBy` / `Map.groupBy`
Native group-by; Map preserves key identity.

### Variant 4 — JSON.stringify replacer
Custom serialize Map/Set.

### Variant 5 — `Record`/`Tuple` proposal
Stage 2 immutable values; structurally equal.

---

## 12. How to think aloud

> "Decision-tree by use case. **Object** — static shape, JSON-friendly, hidden-class optimized in V8 (fast property access for declared shapes). Pitfalls: keys coerce to strings (`obj[5] === obj['5']`); prototype pollution (`__proto__` is dangerous); `Object.keys().length` is O(n); `for..in` walks prototype. Mitigate with `Object.create(null)`. **Map** — general-purpose keyed; any key type (objects, NaN, functions); insertion-order iteration guaranteed by spec; O(1) size; SameValueZero equality (handles NaN). Default to Map for runtime data. **Set** — unique-membership; O(1) add/has; dedup idiom `[...new Set(arr)]`; SameValueZero. **WeakMap / WeakSet** — object-only keys; entries auto-cleared on key GC; not iterable (by design — no way to enumerate GC-determined state); use for per-instance metadata (e.g., tag DOM nodes, mark visited request objects). JSON: `JSON.stringify(map)` returns `'{}'` — Map has no JSON encoding; use `[...map]` or `Object.fromEntries(map)` (when keys are strings). Trap: Object as runtime map (coercion, pollution); for..in (walks proto); JSON on Map (silent loss); WeakMap iteration (impossible by design)."

---

## 13. 60-second revision

> - **Object:** static shape, JSON, hidden-class fast.
> - **Map:** any key, O(1) size, insertion order; **default for runtime data**.
> - **Set:** unique-membership, O(1).
> - **WeakMap/WeakSet:** object keys; GC-friendly; not iterable.
> - **`Object.create(null)`** for safer object-as-dict.
> - **`JSON.stringify(map) = '{}'`** — known limitation.
> - **`for..in` walks proto**; `Object.keys` is own-enumerable.
> - **SameValueZero** for Map/Set.
> - **Trap:** Object key coercion; prototype pollution; size O(n).

---

**Related:** [composite-key-strategies.md](./composite-key-strategies.md) · [map-vs-record-and-tuple.md](./map-vs-record-and-tuple.md) · [weakmap-memoize.md](./weakmap-memoize.md) · [ordered-map-insertion-order-quiz.md](./ordered-map-insertion-order-quiz.md) · [`07-arrays/array-dedup.md`](../07-arrays/array-dedup.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
