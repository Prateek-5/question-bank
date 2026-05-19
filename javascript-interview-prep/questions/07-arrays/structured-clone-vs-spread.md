# `structuredClone` vs spread / `Object.assign`

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [`05-event-loop/structured-clone-cost.md`](../05-event-loop/structured-clone-cost.md), [`09-recursion/deep-clone-with-cycles.md`](../09-recursion/deep-clone-with-cycles.md)
>
> **Source:** ES2022 `structuredClone()`. Stripe, Razorpay, Atlassian.

---

## 1. Problem statement

Choose the right deep-clone strategy. Know what each preserves and breaks.

**Verification examples**

```js
const o = { a: 1, b: { c: 2 }, d: new Date(), e: new Map([[1, 'x']]) };

// Shallow
const s1 = { ...o };                    // s1.b === o.b (shared)
s1.b.c = 999; o.b.c;                    // 999 — same reference!

// JSON trick (lossy)
const j = JSON.parse(JSON.stringify(o));
j.d instanceof Date;                    // false — string
j.e;                                     // {} — empty object

// structuredClone (deep + faithful)
const c = structuredClone(o);
c.b !== o.b;                            // true (deep)
c.d instanceof Date;                    // true
c.e instanceof Map;                     // true
c.e.get(1);                              // 'x'
```

**Constraints**
- Spread/Object.assign: shallow only.
- JSON trick: lossy (Date→string, Map→{}, fn dropped, undefined dropped, cycles throw).
- `structuredClone`: deep, handles cycles, Date/Map/Set, but no functions/DOM nodes/Symbols.
- Lodash `_.cloneDeep`: customizable; heaviest.

---

## 2. Plain-English restatement

`{...obj}` copies one level. `JSON.parse(JSON.stringify())` is deep but lossy. `structuredClone` (ES2022) is deep + faithful for structured types. Lodash if you need custom or older Node.

---

## 3. Why this matters in interviews

"Deep-clone this object" — staple. Senior bar: list 4 strategies with tradeoffs.

---

## 4. Mental model

```
   Comparison:
   
   Method           | Depth   | Date/Map/Set | Cycles | Fns      | Speed
   -----------------+---------+--------------+--------+----------+-----------
   {...obj}         | shallow | preserve     | n/a    | preserve | fastest
   Object.assign    | shallow | preserve     | n/a    | preserve | fastest
   JSON.parse(JSON) | deep    | LOSE         | THROW  | DROP     | fast
   structuredClone  | deep    | preserve     | OK     | THROW    | medium
   _.cloneDeep      | deep    | preserve     | OK     | preserve | slowest
   
   structuredClone:
     Uses the Structured Clone Algorithm (also used by postMessage, IndexedDB).
     Handles: Date, RegExp, Map, Set, ArrayBuffer, TypedArrays, Blob, File, ImageData.
     Cycles: detected and preserved.
     Does NOT handle: functions, DOM nodes (except Image/ImageData), Symbol keys, Error.cause (until ES2022).
   
   Cost:
     structuredClone is sync; copy in main thread.
     For huge objects (MB-scale), blocks event loop.
     postMessage with transferList for ArrayBuffer = zero-copy.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does spread copy?
> 2. What does JSON trick drop?
> 3. Does `structuredClone` handle cycles?

---

## 6. Brute force — walked through

```js
// Spread misses
const orig = { a: { b: 1 } };
const c = { ...orig };
c.a.b = 2;
orig.a.b;                                // 2 — shared

// JSON misses
const o = { d: new Date() };
JSON.parse(JSON.stringify(o)).d;         // string, not Date
```

---

## 7. The unlocking insight

> **`structuredClone` (ES2022) is the modern correct answer for deep cloning structured data. Spread/Object.assign are shallow. JSON trick is lossy.**

Three properties:

1. **Shallow:** spread / Object.assign.
2. **Deep + lossy:** JSON.
3. **Deep + faithful:** structuredClone (no fns).

---

## 8. Solution (annotated)

```js
// 1. Shallow clone (one-level)
const s1 = { ...obj };
const s2 = Object.assign({}, obj);
// nested refs SHARED.

// 2. JSON trick — legacy fallback
function deepCloneJson(obj) {
  return JSON.parse(JSON.stringify(obj));                                 // step 1: lossy
}
// LOSES: Date→ISO string, Map/Set→empty, fn/undefined dropped.
// THROWS on circular reference.

// 3. structuredClone — modern default
const c = structuredClone(obj);                                           // step 2: deep + faithful
// Preserves: Date, RegExp, Map, Set, ArrayBuffer, TypedArrays, cycles.
// Throws on: functions, DOM nodes, Symbol keys.

// 4. Custom hand-rolled — when stringifying is too lossy and structuredClone unavailable
function deepClone(value, seen = new WeakMap()) {                         // step 3: cycle-safe
  if (value === null || typeof value !== 'object') return value;
  if (seen.has(value)) return seen.get(value);                            // step 4: cycle detect
  if (value instanceof Date) return new Date(value);
  if (value instanceof RegExp) return new RegExp(value.source, value.flags);
  if (value instanceof Map) {
    const m = new Map();
    seen.set(value, m);
    for (const [k, v] of value) m.set(deepClone(k, seen), deepClone(v, seen));
    return m;
  }
  if (Array.isArray(value)) {
    const arr = [];
    seen.set(value, arr);
    for (const v of value) arr.push(deepClone(v, seen));
    return arr;
  }
  const out = Object.create(Object.getPrototypeOf(value));
  seen.set(value, out);
  for (const k of Reflect.ownKeys(value)) {
    out[k] = deepClone(value[k], seen);
  }
  return out;
}
```

**Try it yourself**

```js
// Cycles
const o = { name: 'a' };
o.self = o;
JSON.stringify(o);                                            // throws "Converting circular"
structuredClone(o).self === structuredClone(o);              // false (independent clones)
structuredClone(o).self === structuredClone(o); // both clones have their own cycle

// Functions throw in structuredClone
structuredClone({ fn: () => 1 });                             // DataCloneError

// Performance: shallow is 100x+ faster
const big = { /* many fields */ };
performance.now();
const c1 = { ...big };  // ns
const c2 = structuredClone(big);  // ms for large
const c3 = JSON.parse(JSON.stringify(big));  // ms

// Use case: immutable update
function update(state, key, value) {
  return { ...state, [key]: value };                          // shallow enough for top-level
}
function deepUpdate(state, path, value) {
  // structuredClone + walk + assign — convenient but slow
}
```

---

## 9. Step-by-step dry run

```
const o = { a: 1, b: { c: 2 } };

s1 = { ...o }:
  Copy own enumerable properties one level.
  s1.a = 1, s1.b = o.b (same reference).
  s1.b.c = 999 → o.b.c = 999 (shared).

s2 = JSON.parse(JSON.stringify(o)):
  stringify: '{"a":1,"b":{"c":2}}'.
  parse: new object {a:1, b:{c:2}}.
  s2.b is a NEW object.

const o2 = { d: new Date('2024-01-01') };
JSON.parse(JSON.stringify(o2)):
  stringify: '{"d":"2024-01-01T00:00:00.000Z"}'.
  parse: {d: "2024-01-01T..."} — string, NOT Date.

const o3 = { name: 'a' }; o3.self = o3;
JSON.stringify(o3):
  Encounters o3 inside o3 → "circular" → throw.

structuredClone(o3):
  Walks the graph. Encounters o3 again → reuses already-cloned reference.
  Result: { name: 'a', self: <self> } — cycle preserved.

structuredClone({ fn: () => 1 }):
  Cannot clone function → DataCloneError.
```

---

## 10. Common confusion + traps

1. **Spread is shallow** — nested refs shared.
2. **JSON drops Date/Map/Set/fn/undefined**.
3. **JSON throws on cycles**.
4. **structuredClone throws on functions**.
5. **structuredClone is sync** — blocks event loop for large.
6. **Mutating original** after clone — independent (both versions).
7. **WeakMap for cycle detection** in hand-rolled.

---

## 11. Senior follow-ups & variants

### Variant 1 — `postMessage` zero-copy
Transfer ArrayBuffer via transferList; receiver gets ownership.

### Variant 2 — Immer / Immutable
Structural sharing; only changed paths copied.

### Variant 3 — Custom serializer
SuperJSON, devalue — handle Date/Map for JSON-like.

### Variant 4 — Async clone via worker
Offload large structuredClone to worker.

### Variant 5 — Spread vs Object.assign
Different prototype handling; spread uses own enumerable; assign reads getters.

---

## 12. How to think aloud

> "Four deep-clone strategies with tradeoffs: (1) Spread `{...obj}` / `Object.assign({}, obj)` — shallow only; nested refs shared; fastest. (2) `JSON.parse(JSON.stringify(obj))` — deep but lossy: Date becomes ISO string, Map/Set become empty `{}`, functions/undefined dropped, cycles throw. (3) `structuredClone(obj)` (ES2022) — uses the Structured Clone Algorithm (same one postMessage and IndexedDB use); deep, preserves Date/RegExp/Map/Set/TypedArrays, handles cycles correctly; but throws on functions, DOM nodes (mostly), Symbol keys; sync so blocks event loop for large objects. (4) Lodash `_.cloneDeep` — most flexible (handles fns and custom types), slowest, requires lib. Hand-rolled needs `WeakMap` for cycle detection. Use case decisions: top-level state update → spread is fine; need to deep-clone arbitrary structured data → structuredClone; need to clone functions → cloneDeep or shallow + manual; cross-thread transfer of ArrayBuffer → postMessage with transferList (zero-copy). Trap: spread thinking it's deep; JSON dropping Date silently; structuredClone on fn (DataCloneError); blocking event loop on huge clone."

---

## 13. 60-second revision

> - **Spread/Object.assign:** shallow; nested refs shared.
> - **JSON trick:** deep but lossy (Date→string, Map→{}, cycles throw).
> - **`structuredClone` (ES2022):** deep + faithful for structured types; cycles OK; throws on fn.
> - **Lodash `_.cloneDeep`:** most flexible, slowest.
> - **`structuredClone` is sync** — blocks for large.
> - **`postMessage` + transferList** for zero-copy ArrayBuffer.
> - **WeakMap** for cycle detection in custom.
> - **Trap:** spread=deep assumption; JSON Date loss; structuredClone+fn; blocking.

---

**Related:** [`05-event-loop/structured-clone-cost.md`](../05-event-loop/structured-clone-cost.md) · [`09-recursion/deep-clone-with-cycles.md`](../09-recursion/deep-clone-with-cycles.md) · [`09-recursion/deep-merge-with-cycles.md`](../09-recursion/deep-merge-with-cycles.md) · [`08-maps-sets/object-deep-diff.md`](../08-maps-sets/object-deep-diff.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md), [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
