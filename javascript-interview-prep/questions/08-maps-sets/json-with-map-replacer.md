# JSON with Map/Set — replacer & reviver

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [convert-object-to-json-string.md](./convert-object-to-json-string.md), [object-vs-map-vs-set.md](./object-vs-map-vs-set.md)
>
> **Source:** ES5 `JSON.stringify` replacer / `JSON.parse` reviver. Stripe, Razorpay, Atlassian.

---

## 1. Problem statement

JSON natively can't round-trip Map/Set/Date/BigInt/undefined. Use replacer + reviver with tagged objects to preserve.

**Verification examples**

```js
const obj = {
  m: new Map([[1, 'a']]),
  s: new Set([1, 2]),
  d: new Date('2024-01-01'),
  n: 100n,
  u: undefined,
};

const json = JSON.stringify(obj, replacer);
const back = JSON.parse(json, reviver);

back.m instanceof Map;                    // true
back.m.get(1);                            // 'a'
back.s instanceof Set;                    // true
back.d instanceof Date;                   // true
typeof back.n;                            // 'bigint'
```

**Constraints**
- Replacer called for each value before serialization.
- Reviver called for each value after parse.
- Tag scheme: `{__type: 'Map', value: [...]}`.
- undefined in objects: dropped; in arrays: null.

---

## 2. Plain-English restatement

JSON has no concept of Map/Set/Date. Tag them as objects with `__type` discriminator. Replacer encodes; reviver decodes. Round-trip-safe.

---

## 3. Why this matters in interviews

Common backend pain: log/cache/store data with Map/Set/Date and lose information silently. Tests serialization + JSON hooks awareness.

---

## 4. Mental model

```
   Native JSON:
     Map     → {}          (LOSES)
     Set     → {}
     Date    → ISO string  (loses type)
     BigInt  → throws
     undefined → dropped (obj) / null (arr)
     RegExp  → {}
     Function → dropped
   
   Replacer (encode):
     called per key/value (before child recursion).
     Return wrapped object for special types.
     {__type: 'Map', value: [...entries]}.
   
   Reviver (decode):
     called per key/value (after child parsed).
     If value is tagged object, return reconstructed.
   
   Both round-trip:
     parse(stringify(x)) === structurally === x.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `JSON.stringify(new Map([[1, 'a']]))` return natively?
> 2. When is the replacer called?
> 3. Why use a `__type` tag?

---

## 6. Brute force — walked through

```js
// Naive: stringify ignores Map
JSON.stringify({m: new Map([[1, 'a']])});   // '{"m":{}}'  ← lost data
```

---

## 7. The unlocking insight

> **Replacer transforms before serialize; reviver reverses on parse. Tag with `__type` discriminator for round-trip.**

Three properties:

1. **Replacer** encodes special types.
2. **Reviver** decodes tagged objects.
3. **`__type` tag** disambiguates.

---

## 8. Solution (annotated)

```js
function replacer(key, value) {
  if (value instanceof Map) {                                              // step 1: Map
    return { __type: 'Map', value: [...value.entries()] };
  }
  if (value instanceof Set) {
    return { __type: 'Set', value: [...value] };
  }
  if (value instanceof Date) {                                             // step 2: Date
    return { __type: 'Date', value: value.toISOString() };
  }
  if (typeof value === 'bigint') {
    return { __type: 'BigInt', value: value.toString() };
  }
  if (value instanceof RegExp) {
    return { __type: 'RegExp', source: value.source, flags: value.flags };
  }
  return value;                                                            // step 3: passthrough
}

function reviver(key, value) {
  if (value && typeof value === 'object' && '__type' in value) {           // step 4: tagged
    switch (value.__type) {
      case 'Map':    return new Map(value.value);
      case 'Set':    return new Set(value.value);
      case 'Date':   return new Date(value.value);
      case 'BigInt': return BigInt(value.value);
      case 'RegExp': return new RegExp(value.source, value.flags);
    }
  }
  return value;
}

// Use
const obj = {
  m: new Map([[1, 'a'], [2, 'b']]),
  s: new Set(['x', 'y']),
  d: new Date('2024-01-01'),
  n: 100n,
};

const json = JSON.stringify(obj, replacer);                                // serialize
const back = JSON.parse(json, reviver);                                    // deserialize
```

**Try it yourself**

```js
// Round-trip
const orig = new Map([[1, 'a'], [2, 'b']]);
const round = JSON.parse(JSON.stringify(orig, replacer), reviver);
round.get(1);                                                 // 'a'

// Nested
const nested = {
  users: new Map([
    ['u1', { name: 'A', tags: new Set(['admin']) }],
    ['u2', { name: 'B', tags: new Set(['user']) }],
  ]),
};
const json = JSON.stringify(nested, replacer);
const back = JSON.parse(json, reviver);
back.users.get('u1').tags.has('admin');                       // true

// Cycle — JSON doesn't handle; throws
const c = {}; c.self = c;
try { JSON.stringify(c, replacer); } catch (e) { /* circular */ }

// Functions — still dropped (no Function constructor from JSON)
JSON.stringify({fn: () => 1}, replacer);                      // '{}'  ← fn dropped natively

// Conflicting __type key — by-design ambiguity
JSON.stringify({__type: 'NotReal', value: 1}, replacer);
// Reviver will treat as tagged; corrupts. Use a less-likely sentinel like `__jstype__`.

// SuperJSON / devalue libraries do this with proper namespacing.
```

---

## 9. Step-by-step dry run

```
JSON.stringify({m: new Map([[1, 'a']])}, replacer):

Native traversal:
  Top-level call: replacer('', root) → returns root (not a Map).
  Then traverse keys:
    key='m', value=Map.
    Replacer('m', Map) → {__type: 'Map', value: [[1, 'a']]}.
    Serialize this object normally.
  Output: '{"m":{"__type":"Map","value":[[1,"a"]]}}'.

JSON.parse('{"m":{"__type":"Map","value":[[1,"a"]]}}', reviver):

Native parse builds bottom-up:
  Innermost: '[1,"a"]' parsed as [1, 'a'].
  reviver(0, 1) → 1 (no tag).
  reviver(1, 'a') → 'a'.
  Then object {__type, value}:
    reviver('__type', 'Map') → 'Map'.
    reviver('value', [[1, 'a']]) → [[1, 'a']].
  Then top object's value: reviver('m', {__type:'Map', value:[[1,'a']]}):
    Has __type and is 'Map' → new Map(value.value) = new Map([[1, 'a']]).
    Return Map.
  Top: reviver('', {m: Map}) → return as-is.

Final: {m: Map{1 => 'a'}}.

Cycle:
  JSON.stringify with circular ref → TypeError "Converting circular".
  Replacer doesn't help.
  Use structuredClone or custom serializer for cycles.
```

---

## 10. Common confusion + traps

1. **Replacer called multiple times** — once per key/value.
2. **`__type` collision** with real data — pick a namespaced sentinel.
3. **Reviver bottom-up** — children revived before parent.
4. **`undefined` in objects** — replacer can't preserve; JSON drops.
5. **Functions** — never serializable.
6. **Cycles** — JSON throws regardless.
7. **TypedArrays** — special handling needed (toBase64 etc).

---

## 11. Senior follow-ups & variants

### Variant 1 — SuperJSON / devalue
Libraries that automate this with cycle support.

### Variant 2 — Custom toJSON method
Add to classes for default behavior.

### Variant 3 — Schema-aware (Protobuf, MessagePack)
Binary + schema; faster than JSON.

### Variant 4 — `structuredClone`
For in-memory cloning; not serialization.

### Variant 5 — `JSON.stringify` replacer array
Filter to specific keys.

---

## 12. How to think aloud

> "JSON natively serializes only object/array/string/number/boolean/null. Map, Set, Date (becomes ISO string but loses type), BigInt (throws), undefined (dropped in objects, null in arrays), RegExp, Function are lost. Use the replacer hook in `JSON.stringify(value, replacer)` and reviver in `JSON.parse(text, reviver)` with a tagged-object scheme. Replacer: called per key/value (before child recursion), returns a wrapped `{__type: 'Map', value: [...entries]}` for special types. Reviver: called per key/value (after child parsed — bottom-up), if it sees a tagged object reconstructs the type. Tag pick: `__type` is ambiguous if real data has that key — production code uses `__jstype__` or a Symbol-namespaced approach (SuperJSON, devalue libraries handle this professionally). Cycles: JSON throws regardless of replacer; use structuredClone or custom serializer with WeakSet cycle detection. Custom classes: add `toJSON()` method — JSON calls it first and replacer never sees the original. Variants: SuperJSON/devalue for production; schema-aware formats (Protobuf, MessagePack) for performance. Trap: `__type` collision; replacer per-key (not per object); cycles not handled; functions never serializable; undefined silently dropped."

---

## 13. 60-second revision

> - **Replacer:** encode per key/value before serialize.
> - **Reviver:** decode bottom-up after parse.
> - **`{__type: 'Map', value: [...]}` tag.**
> - **Map/Set/Date/BigInt/RegExp** all need replacer.
> - **`undefined`/Function** never serializable.
> - **Cycles** throw regardless.
> - **`__type` collision risk** — use namespaced sentinel.
> - **SuperJSON / devalue** for production.
> - **Trap:** tag collision; replacer per-key not per-object; cycles.

---

**Related:** [convert-object-to-json-string.md](./convert-object-to-json-string.md) · [object-vs-map-vs-set.md](./object-vs-map-vs-set.md) · [`07-arrays/structured-clone-vs-spread.md`](../07-arrays/structured-clone-vs-spread.md) · [`09-recursion/deep-clone-with-cycles.md`](../09-recursion/deep-clone-with-cycles.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
