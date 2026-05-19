# Map / Object — insertion-order quiz

> **Difficulty:** Foundation   |   **Time:** ~8 min   |   **Prereqs:** [object-vs-map-vs-set.md](./object-vs-map-vs-set.md)
>
> **Source:** ES2015 Map; ES2020 codified Object key ordering. Stripe, Razorpay, Atlassian output-prediction.

---

## 1. Problem statement

Predict iteration order of Map and Object. Map always insertion. Object: integer-like keys ascending, then string keys insertion, then symbol keys insertion.

**Verification examples**

```js
// Map: always insertion
const m = new Map();
m.set('b', 1); m.set('a', 2); m.set(3, 3);
[...m.keys()];                            // ['b', 'a', 3]

// Object: quirky
const o = {};
o.b = 1; o.a = 2; o['10'] = 3; o['2'] = 4;
Object.keys(o);                           // ['2', '10', 'b', 'a']

// Negative/non-integer numeric strings are string keys
Object.keys({'-1': 'a', '1.5': 'b', '1': 'c', '0': 'd'});
// ['0', '1', '-1', '1.5']
```

**Constraints**
- Map: insertion order for all key types.
- Object: integer-like keys ascending FIRST, then strings insertion, then Symbols insertion.
- "Integer-like": non-negative integer that stringifies back to same form.
- `Reflect.ownKeys(o)` includes Symbol keys.

---

## 2. Plain-English restatement

Map always preserves insertion order. Object reorders integer-like keys to ascending; non-integer string keys retain insertion order; Symbol keys retain insertion order, after strings.

---

## 3. Why this matters in interviews

"In what order are these keys iterated?" Common answer "no guarantee" is wrong post-ES2020. Senior bar: know the exact rules.

---

## 4. Mental model

```
   Map iteration order: ALWAYS insertion.
     map.keys() / values() / entries() / forEach / for..of map
     All in insertion order.
     Keys can be any value (no coercion).
   
   Object iteration order (Object.keys, for..in, JSON.stringify, spread):
     1. Integer-like keys ASCENDING (parsed as uint32, < 2^32 - 1):
        '0', '1', '2', '10' — converted, sorted, then iterated.
     2. Non-integer string keys in INSERTION order:
        'a', 'b', '-1', '1.5' (negative/decimal don't qualify).
     3. Symbol keys in INSERTION order.
        Only via Reflect.ownKeys / Object.getOwnPropertySymbols.
   
   "Integer-like" rule:
     ToString(ToUint32(key)) === key.
     'A non-negative integer canonical form'.
     '10' qualifies. '-1', '1.5', '01' don't.
   
   for..in:
     Same order as Object.keys.
     Walks prototype enumerable too (after own keys).
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. `Object.keys({b: 1, a: 2, '2': 3})` order?
> 2. Does `'-1'` count as integer-like?
> 3. Does `Map.keys` preserve insertion for numeric keys?

---

## 6. Brute force — walked through

Output-prediction problem; no algorithm to brute-force. The mental model IS the solution.

---

## 7. The unlocking insight

> **Map: always insertion. Object: integer-like ASC first, then strings/symbols insertion.**

Three properties:

1. **Map insertion** universal.
2. **Object integer-like ASC** first.
3. **Symbols last** (in `Reflect.ownKeys`).

---

## 8. Solution (annotated)

```js
// Map — always insertion order
const m = new Map();
m.set('z', 1);
m.set(1, 2);
m.set('a', 3);
[...m.keys()];                                                 // step 1: ['z', 1, 'a']

// Object — quirky
const o = {};
o.z = 1;
o[1] = 2;       // integer-like (string '1' under the hood)
o.a = 3;
o[100] = 4;
o[Symbol('s')] = 5;

Object.keys(o);                                                // step 2: ['1', '100', 'z', 'a']
Reflect.ownKeys(o);                                            // step 3: ['1', '100', 'z', 'a', Symbol(s)]
JSON.stringify(o);                                             // step 4: '{"1":2,"100":4,"z":1,"a":3}'

// Workaround: force string with leading char
const o2 = {};
o2['_1'] = 'a';
o2['_2'] = 'b';
o2['_10'] = 'c';
Object.keys(o2);                                               // ['_1', '_2', '_10'] (insertion!)

// Map preferred when order matters
const ordered = new Map();
ordered.set('first', 1);
ordered.set('second', 2);
[...ordered];                                                  // [['first', 1], ['second', 2]]
```

**Try it yourself**

```js
// Quiz examples
Object.keys({b: 1, a: 2});                                    // ['b', 'a']    string insertion
Object.keys({2: 'a', 1: 'b', 'x': 'c'});                      // ['1', '2', 'x']  int asc, then x
Object.keys({'-1': 'a', '1': 'b', '0.5': 'c'});               // ['1', '-1', '0.5']  '1' is int-like
Object.keys({'01': 'a', '1': 'b'});                           // ['1', '01']  '01' is NOT int-like

// Map
const m2 = new Map([[2, 'a'], [1, 'b'], ['x', 'c']]);
[...m2.keys()];                                                // [2, 1, 'x']   insertion order

// JSON
JSON.stringify({2: 'a', 1: 'b'});                              // '{"1":"a","2":"b"}'  int asc

// Spread
const o3 = {2: 'a', 1: 'b', x: 'c'};
const o4 = {...o3};
Object.keys(o4);                                               // ['1', '2', 'x']

// for..in
for (const k in {2: 'a', 1: 'b'}) console.log(k);             // '1', '2'

// -0 is treated as 0 in Object keys
Object.keys({[-0]: 'a'});                                      // ['0']
```

---

## 9. Step-by-step dry run

```
const o = {};
o.b = 1;      // own keys: ['b']
o.a = 2;      // own keys: ['b', 'a']
o['10'] = 3;  // '10' is integer-like → goes to head of int section.
              // V8 internally: integer-keys (sorted) + string-keys (insertion).
              // own keys order: ['10', 'b', 'a']
o['2'] = 4;   // '2' int-like, inserted into int section sorted: ['2', '10'].
              // overall: ['2', '10', 'b', 'a']

Object.keys(o);  // ['2', '10', 'b', 'a']

Why '01' is NOT int-like:
  ToUint32('01') = 1. ToString(1) = '1'. '1' !== '01'. Not canonical.
  → '01' is a regular string key.

Why '-1' is NOT int-like:
  ToUint32('-1') = 4294967295 (max - 1) due to modular wrap.
  ToString(4294967295) = '4294967295'. !== '-1'. Not canonical.
  → '-1' is a regular string key.

Why Map preserves number keys:
  Map keys are stored as-is; no coercion.
  Insertion order = the order set() was called.

JSON.stringify:
  Uses Object.keys order internally.
  Output reflects: int-like first sorted, then strings insertion, NO SYMBOLS.
```

---

## 10. Common confusion + traps

1. **"No order guarantee"** — wrong since ES2020.
2. **"Map preserves" but treated like Object** — different rules.
3. **`'01'` int-like** — no; not canonical.
4. **Negative numeric strings** — string keys.
5. **Symbol keys missed** — `Object.keys` excludes; use `Reflect.ownKeys`.
6. **`for..in` walks prototype** — own then inherited.
7. **`Object.assign` preserves order** of source iteration.

---

## 11. Senior follow-ups & variants

### Variant 1 — `Reflect.ownKeys`
All own keys including symbols.

### Variant 2 — `Object.getOwnPropertyNames`
Own string keys (including non-enumerable).

### Variant 3 — `Object.getOwnPropertySymbols`
Symbol keys only.

### Variant 4 — Force string keys
Prefix with `_` or `#` to avoid integer ordering.

### Variant 5 — Map for ordered data
Always preferred when order matters semantically.

---

## 12. How to think aloud

> "Map iteration order is always insertion — keys can be any value (no coercion), `keys()`, `values()`, `entries()`, `forEach`, `for..of map` all preserve insertion. Object iteration is quirky: integer-like keys ASCENDING first, then non-integer string keys in INSERTION order, then Symbol keys in INSERTION order (Symbols only visible via `Reflect.ownKeys` or `Object.getOwnPropertySymbols`). 'Integer-like' means `ToString(ToUint32(k)) === k` — a canonical non-negative-integer form. `'10'` qualifies; `'-1'`, `'1.5'`, `'01'` don't (negative becomes huge after Uint32 wrap; decimal isn't integer; leading-zero isn't canonical). `for..in` follows same order, then walks prototype enumerable. `JSON.stringify` uses Object.keys order. `Object.assign` and spread preserve iteration order. Practical advice: use Map when order matters semantically; if you must use Object for numeric-like keys and need insertion order, prefix with `_` or `#` to force them into the string-keys section. Trap: 'no order guarantee' (wrong since ES2020); '01' int-like; negative numeric int-like; Symbol keys missed by Object.keys."

---

## 13. 60-second revision

> - **Map: ALWAYS insertion.**
> - **Object:** int-like ASC, then strings insertion, then Symbols.
> - **Int-like:** `ToString(ToUint32(k)) === k` (non-negative canonical).
> - **`'01'`, `'-1'`, `'1.5'`** — not int-like.
> - **`for..in`** = Object.keys order + prototype.
> - **`JSON.stringify`** uses same order.
> - **`Reflect.ownKeys`** includes Symbols.
> - **Workaround:** prefix `_` for force-string.
> - **Trap:** "no guarantee" myth; misjudge int-like.

---

**Related:** [object-vs-map-vs-set.md](./object-vs-map-vs-set.md) · [composite-key-strategies.md](./composite-key-strategies.md) · [lru-cache-with-map.md](./lru-cache-with-map.md) · [`07-arrays/holey-vs-packed-arrays.md`](../07-arrays/holey-vs-packed-arrays.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
