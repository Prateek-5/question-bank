# Map / Object — Insertion Order Quiz

## Source / Origin
- ES2015 Map; ES2020 codified Object key ordering.
- Asked at: Stripe, Razorpay, Atlassian — output-prediction.
- Concept reference: `concepts/maps-sets.md`.

## Why this question matters in interviews
"In what order are these keys iterated?" Most JS devs say "no guarantee" — wrong since ES2020. Senior bar: you know the exact spec rules — Map preserves insertion; Object orders integer-like keys ascending, then string keys in insertion order, then Symbol keys in insertion order.

## Concepts involved

```js
// Map — always insertion order
const m = new Map();
m.set('b', 1); m.set('a', 2); m.set(3, 3);
[...m.keys()];     // ['b', 'a', 3]

// Object — quirky
const o = {};
o.b = 1; o.a = 2; o['10'] = 3; o['2'] = 4; o[Symbol('s')] = 5;
Object.keys(o);    // ['2', '10', 'b', 'a']  — integer-like first, then insertion
Reflect.ownKeys(o);// ['2', '10', 'b', 'a', Symbol(s)]

// Negative or non-integer numeric strings act like strings
const o2 = { '-1': 'a', '1.5': 'b', '1': 'c', '0': 'd' };
Object.keys(o2);   // ['0', '1', '-1', '1.5']  — integer-like first, others insertion order
```

### Edge cases / traps
1. **"Integer-like" key** — a non-negative integer that, when stringified back, matches. `'10'` qualifies; `'-1'`, `'1.5'`, `'01'` don't.
2. **`-0`** is treated as `0`.
3. **Map preserves insertion order for ALL key types** including numbers.
4. **`for...in`** iterates own + inherited enumerable; same ordering rules apply.
5. **`JSON.stringify`** of an object uses `Object.keys()` order — integer-like first.
6. **Spread `{...o}` and `Object.assign`** copy in iteration order; integer-like first.
7. **`Map.prototype.entries`, `keys`, `values`, `forEach`, `for...of`** all use insertion order.
8. **Map keys can be any value**; Object keys coerce to string (except Symbol).

## Mental Model

```
   Object key iteration order:
     1. integer-like (non-negative int that round-trips), ascending
     2. other string keys, insertion order
     3. Symbol keys, insertion order

   Map iteration order:
     insertion order, for all keys
```

## Why interviewers care

- **Spec-level knowledge** — codified in ES2020.
- **Predictability** of JSON output.
- **Common bug source** — `{1:'a', 0:'b'}` is *not* in source order.

## Common confusion

- **"Object key order is unspecified."** Specified since ES2020.
- **"Maps and Objects iterate the same."** They don't — integer-like quirk for Object only.
- **"`for...in` and `Object.keys` differ."** They don't (modulo `for...in` walking the prototype chain for inherited enumerable).
- **"`Map` is slower than Object."** Not for large keysets; often faster, especially with non-string keys.

## Solution

```js
// Force insertion order on an Object — use Map instead
const m = new Map();
m.set('z', 1); m.set('1', 2); m.set('a', 3);
[...m];           // [['z',1], ['1',2], ['a',3]]

// JSON-stringify with stable key order
function stableStringify(obj) {
  const keys = Object.keys(obj).sort();
  return '{' + keys.map(k => JSON.stringify(k) + ':' + stableStringify(obj[k])).join(',') + '}';
}
// (recurse properly for nested)

// Map → Object preserves intent but loses Map's insertion-order property
function mapToObj(m) {
  return Object.fromEntries(m);   // integer-like keys reordered!
}

// Map → JSON (preserving order)
function mapToJson(m) {
  return JSON.stringify([...m]);    // array of [key, value] pairs
}
```

## Dry run

```js
const o = {};
o.x = 1;
o['10'] = 2;
o.y = 3;
o['2'] = 4;
o['-1'] = 5;
Object.keys(o);
//   integer-like sort: '2', '10'
//   then strings in insertion: 'x', 'y', '-1'
//   result: ['2', '10', 'x', 'y', '-1']
```

```js
const m = new Map();
m.set('x', 1);
m.set('10', 2);
m.set('y', 3);
m.set('2', 4);
[...m.keys()];     // ['x', '10', 'y', '2']  — insertion order
```

## How to think aloud

> "Object key iteration: integer-like keys ascending first, then string keys in insertion order, then Symbol keys in insertion order. Integer-like means non-negative int that round-trips through `String(parseInt(k))`. Map: pure insertion order, all key types. If iteration order matters for app logic, use Map. For JSON stability, sort keys. Spread, Object.assign, JSON.stringify all use this order."

## Important takeaways

- **Object: integer-like first (ascending), then strings (insertion), then Symbols (insertion).**
- **Map: pure insertion order.**
- **`{1: 'a', 0: 'b'}` iterates as `0` then `1`.**
- **For deterministic insertion order, use Map.**
- **`stableStringify`** = sort keys at every level.

## Variants

- **`Object.keys` vs `Reflect.ownKeys`** — Reflect includes Symbol and non-enumerable.
- **`for...in`** walks prototype chain too.
- **`JSON.stringify(obj, keys[])`** — pass array of keys to control order.

## Revision notes

```
Object iteration order (ES2020+):
  1. integer-like keys: ascending
     (non-neg int, String(parseInt(k)) === k)
  2. other string keys: insertion order
  3. Symbol keys: insertion order

Map iteration order:
  insertion order, ALL keys

TRAPS:
  {1:'a', 0:'b'}  iterates 0, 1
  Object.fromEntries([...m]) — REORDERS integer-like
  spread, Object.assign, JSON.stringify all use Object order

USE MAP when insertion order matters
```
