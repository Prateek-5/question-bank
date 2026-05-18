# JSON with Map/Set — Replacer & Reviver

## Source / Origin
- ES5 `JSON.stringify(value, replacer)`, `JSON.parse(text, reviver)`.
- Asked at: Stripe, Razorpay, Atlassian.
- Concept reference: `concepts/maps-sets.md`.

## Why this question matters in interviews
JSON natively serializes `{}`, `[]`, `string`, `number`, `boolean`, `null`. Map, Set, Date, BigInt, undefined are lost or wrong. The replacer/reviver hooks let you serialize them faithfully. Senior bar: you implement a round-trippable encode/decode with a tagged-object scheme.

## Concepts involved

```js
function replacer(key, value) {
  if (value instanceof Map) return { __type: 'Map', value: [...value.entries()] };
  if (value instanceof Set) return { __type: 'Set', value: [...value] };
  if (value instanceof Date) return { __type: 'Date', value: value.toISOString() };
  if (typeof value === 'bigint') return { __type: 'BigInt', value: value.toString() };
  return value;
}

function reviver(key, value) {
  if (value && typeof value === 'object' && '__type' in value) {
    switch (value.__type) {
      case 'Map':    return new Map(value.value);
      case 'Set':    return new Set(value.value);
      case 'Date':   return new Date(value.value);
      case 'BigInt': return BigInt(value.value);
    }
  }
  return value;
}

const obj = { m: new Map([[1, 'a']]), s: new Set([1, 2]), d: new Date(), n: 100n };
const json = JSON.stringify(obj, replacer);
const back = JSON.parse(json, reviver);
```

### Edge cases / traps
1. **`undefined` in objects** is dropped by JSON; in arrays becomes `null`.
2. **`Symbol` keys** are skipped silently.
3. **Functions** are dropped.
4. **Circular refs** throw `TypeError`.
5. **`NaN`, `Infinity`** become `null` in JSON; reviver can't see them.
6. **`__type` collision** — pick a key unlikely to clash with user data, or namespace (`__$jsType$`).
7. **`toJSON` method** on objects overrides the default serialization (Date uses this).
8. **Order of replacer** — runs *bottom-up* during stringify; for parse, reviver runs *post-order* on parsed tree.

## Mental Model

```
   stringify(obj, replacer):
     walk obj; for each key/value, call replacer
     if returns undefined → omit
     if returns plain object → recurse
     output JSON string

   parse(text, reviver):
     parse JSON into JS value
     walk post-order; call reviver(key, value); replace if return differs
```

## Solution

```js
const TAG = '__$type$';

function encodeReplacer(key, value) {
  if (value instanceof Map)  return { [TAG]: 'Map',  data: [...value] };
  if (value instanceof Set)  return { [TAG]: 'Set',  data: [...value] };
  if (value instanceof Date) return { [TAG]: 'Date', data: value.toISOString() };
  if (typeof value === 'bigint') return { [TAG]: 'BigInt', data: value.toString() };
  if (value === undefined) return { [TAG]: 'Undefined' };
  if (value !== value) return { [TAG]: 'NaN' };
  if (value === Infinity) return { [TAG]: 'Infinity' };
  if (value === -Infinity) return { [TAG]: '-Infinity' };
  return value;
}

function decodeReviver(key, value) {
  if (value && typeof value === 'object' && TAG in value) {
    switch (value[TAG]) {
      case 'Map':    return new Map(value.data);
      case 'Set':    return new Set(value.data);
      case 'Date':   return new Date(value.data);
      case 'BigInt': return BigInt(value.data);
      case 'Undefined': return undefined;
      case 'NaN':    return NaN;
      case 'Infinity':  return Infinity;
      case '-Infinity': return -Infinity;
    }
  }
  return value;
}

function encode(obj) { return JSON.stringify(obj, encodeReplacer); }
function decode(str) { return JSON.parse(str, decodeReviver); }

// Round-trip test
const original = {
  m: new Map([['k', 'v']]),
  s: new Set([1, 2]),
  d: new Date('2024-01-01'),
  big: 10n ** 18n,
  nan: NaN,
};
const json = encode(original);
const recovered = decode(json);
recovered.m instanceof Map;   // true
recovered.big === original.big; // true
isNaN(recovered.nan);          // true
```

## Dry run

```js
JSON.stringify({ m: new Map([[1,'a']]) }, replacer)
  walk: key='', value={m: Map}
  → not Map; return value
  walk: key='m', value=Map
  → return { __type: 'Map', value: [[1,'a']] }
  output: '{"m":{"__type":"Map","value":[[1,"a"]]}}'

JSON.parse(json, reviver)
  parse → {m: {__type:'Map', value:[[1,'a']]}}
  reviver(key='', value=parent) ← runs LAST (post-order)
  reviver(key='m', value={__type:'Map',...}) → new Map([[1,'a']])
  reviver(key='', value=parent with m replaced)
  return {m: Map(1)}
```

## How to think aloud

> "Tag non-JSON types with a sentinel key. Replacer at stringify, reviver at parse. Map → entries array, Set → values array, Date → ISO, BigInt → string. For NaN/Infinity/undefined, use special tags. Choose a tag key unlikely to collide. Reviver runs post-order so it sees children before parents. For circular refs, use a separate cycle-detecting serializer like flatted; JSON.stringify throws."

## Important takeaways

- **Replacer at stringify, reviver at parse.**
- **Tag scheme** with `__type` (or namespaced).
- **Map/Set/Date/BigInt/undefined/NaN/Infinity** all need explicit handling.
- **Circular refs throw** — use `flatted` or similar for cycles.
- **`toJSON` method** wins over replacer for that object.
- **Functions and Symbol-keys are silently dropped.**

## Variants

- **`flatted`** — handles cyclic structures.
- **`devalue`** (svelte/devalue) — small, secure, supports many types.
- **`superjson`** — extends with TypedArrays, RegExp, etc.
- **CBOR / MessagePack** — binary alternatives that natively support these types.

## Revision notes

```
replacer (stringify):
  (key, value) => transform
  return same value → keep as-is
  return undefined → omit

reviver (parse):
  (key, value) => transform
  post-order: children processed before parent

types to handle:
  Map → entries array
  Set → values array
  Date → ISO string
  BigInt → string
  undefined / NaN / Infinity / -Infinity → tagged

TRAPS:
  - circular → use flatted
  - Symbol keys silently dropped
  - functions silently dropped
  - toJSON method wins
```
