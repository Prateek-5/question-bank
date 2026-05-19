# Lodash-style `reduce` — arrays AND objects

> **Difficulty:** Medium   |   **Time:** ~12 min   |   **Prereqs:** [polyfill-reduce.md](./polyfill-reduce.md)
>
> **Source:** codedamn Lab. Lodash `_.reduce`. Standard followup to native polyfill.

---

## 1. Problem statement

Reimplement `_.reduce(collection, iteratee, [accumulator])` — works on **arrays OR plain objects**.

**Verification examples**

```js
reduce([1, 2, 3], (acc, v) => acc + v, 0);              // 6
reduce({a: 1, b: 2, c: 3}, (acc, v) => acc + v, 0);    // 6

reduce({a: 1, b: 2}, (acc, v, key) => { acc[key] = v * 2; return acc; }, {});
// {a: 2, b: 4}

reduce([], (a, b) => a + b);                            // undefined (lodash; native throws)
```

**Constraints**
- Detect array vs plain object via `Array.isArray`.
- Iteratee `(acc, value, key|index, collection)`.
- Object iteration: `Object.keys` (insertion order for strings, ints ascending).
- No accumulator + empty → `undefined` (NOT throw, unlike native).

---

## 2. Plain-English restatement

Like native reduce but handles plain objects too. For objects: iterate `Object.keys`, third arg is the string key.

---

## 3. Why this matters in interviews

Tests collection-shape detection, `Object.keys` semantics, prototype-chain awareness, ability to handle two shapes without leaking abstractions.

---

## 4. Mental model

```
   reduce(coll, iteratee, [acc]):
     keys = Array.isArray(coll) 
       ? Array.from({length: coll.length}, (_, i) => i)
       : Object.keys(coll)
     
     hasInit = arguments.length >= 3
     i = 0
     if hasInit:
       result = acc
     else:
       if keys.length === 0:
         return undefined            ← lodash divergence from native
       result = coll[keys[0]]
       i = 1
     
     while i < keys.length:
       k = keys[i]
       result = iteratee(result, coll[k], k, coll)
       i++
     return result
   
   Key iteration order:
     Object.keys: integer-like keys ascending, then string keys insertion order.
     for...in: WALKS PROTOTYPE — avoid.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Differences from native reduce?
> 2. Object iteration order guarantees?
> 3. Why use `Object.keys` not `for..in`?

---

## 6. Brute force — walked through

```js
function reduce(coll, fn, acc) {
  if (Array.isArray(coll)) return coll.reduce(fn, acc);
  let result = acc;
  for (const k in coll) result = fn(result, coll[k], k, coll);   // PROTO WALK
  return result;
}
```

Bug: `for..in` walks prototype chain. Use `Object.keys`.

---

## 7. The unlocking insight

> **Unified loop over a `keys` list. For arrays: `[0..len-1]`. For objects: `Object.keys`. Handle no-acc + empty as `undefined` (lodash).**

Three properties:

1. **Compute keys list once** — `[0..n-1]` or `Object.keys`.
2. **Lodash diverges:** empty + no init → `undefined`, not throw.
3. **`Object.keys`, not `for..in`** — avoid prototype.

---

## 8. Solution (annotated)

```js
function reduce(collection, iteratee, ...rest) {
  if (collection == null) return rest.length ? rest[0] : undefined;

  const keys = Array.isArray(collection)                                  // step 1: detect shape
    ? Array.from({ length: collection.length }, (_, i) => i)
    : Object.keys(collection);                                            // step 2: own enumerable keys

  const hasInit = rest.length >= 1;
  let result;
  let i = 0;

  if (hasInit) {
    result = rest[0];
  } else {
    if (keys.length === 0) return undefined;                              // step 3: lodash: undefined not throw
    result = collection[keys[0]];
    i = 1;
  }

  while (i < keys.length) {
    const k = keys[i];
    result = iteratee(result, collection[k], k, collection);              // step 4: iteratee
    i++;
  }
  return result;
}
```

**Try it yourself**

```js
// Array
reduce([1, 2, 3], (a, b) => a + b, 0);                       // 6
reduce([1, 2, 3], (a, b) => a + b);                          // 6 (no init)

// Object
reduce({a: 1, b: 2, c: 3}, (acc, v, k) => {
  acc[k] = v * 2;
  return acc;
}, {});
// {a: 2, b: 4, c: 6}

// Sum object values
reduce({a: 1, b: 2}, (acc, v) => acc + v, 0);                // 3

// Empty cases
reduce([], (a, b) => a + b);                                  // undefined (lodash)
reduce({}, (a, b) => a + b);                                  // undefined
reduce([], (a, b) => a + b, 99);                              // 99
reduce(null, fn, 5);                                          // 5

// Inheritance: Object.keys excludes inherited
class Foo { constructor() { this.a = 1; } }
Foo.prototype.b = 2;
reduce(new Foo(), (acc, v, k) => { acc[k] = v; return acc; }, {});
// {a: 1}   ← b excluded

// Object key order quirk
reduce({2: 'a', 1: 'b', x: 'c'}, (acc, v, k) => acc + k + v, '');
// '1b2ax' (integer-like keys first, then string keys in insertion order)
```

---

## 9. Step-by-step dry run

```
reduce({a: 1, b: 2, c: 3}, (acc, v, k) => acc + v, 0):
  Array.isArray → false. keys = ['a', 'b', 'c'].
  hasInit = true. result = 0. i = 0.
  
  i=0: k='a'. result = fn(0, 1, 'a', coll) = 1.
  i=1: k='b'. result = fn(1, 2, 'b', coll) = 3.
  i=2: k='c'. result = fn(3, 3, 'c', coll) = 6.
  Return 6.

reduce({}, fn):
  keys = []. hasInit = false.
  keys.length === 0 → return undefined. (lodash divergence)

reduce({2: 'a', 1: 'b', x: 'c'}, (acc, v, k) => acc + k, ''):
  Object.keys order: '1', '2' (integer-like ascending), then 'x' (insertion).
  i=0: k='1', acc = '' + '1' = '1'.
  i=1: k='2', acc = '1' + '2' = '12'.
  i=2: k='x', acc = '12' + 'x' = '12x'.
  Return '12x'.

reduce(new Foo(), fn, {}):
  Object.keys returns OWN enumerable only.
  Foo.prototype.b is on prototype → excluded.
```

---

## 10. Common confusion + traps

1. **`for..in` walks prototype** — use `Object.keys`.
2. **Empty + no init throws** — lodash returns undefined, not throw.
3. **String keys for objects** — third arg type differs.
4. **`Object.keys` order** — integer keys ascending first, then strings insertion.
5. **Symbols excluded** — `Object.getOwnPropertySymbols` for those.
6. **Map/Set as collection** — lodash skips; document.
7. **Null coll** — lodash returns acc; document.

---

## 11. Senior follow-ups & variants

### Variant 1 — Support Map / Set
Iterate via `for..of` if `Symbol.iterator`.

### Variant 2 — `forEach`-style
Iterate without folding.

### Variant 3 — `reduceRight`
Object: `Object.keys().reverse()`.

### Variant 4 — Strings as collection
Lodash iterates char-by-char.

### Variant 5 — Inheriting properties
Switch to `for..in` + `hasOwnProperty` for parity (default off).

---

## 12. How to think aloud

> "Lodash `_.reduce` works on arrays AND plain objects. Unified implementation: compute a `keys` list once based on `Array.isArray(coll)` — `[0..len-1]` for arrays, `Object.keys(coll)` for objects. Then loop over keys, calling iteratee with `(acc, coll[k], k, coll)` — third arg is key (string for objects, number for arrays). Use `Object.keys`, NOT `for..in` — for..in walks the prototype chain. `Object.keys` returns own enumerable keys with this order: integer-like keys ascending, then string keys in insertion order. Critical lodash divergence from native: empty collection without accumulator returns `undefined`, NOT throw. Variants: support Map/Set via `Symbol.iterator`; reduceRight reverses keys; strings iterate char-by-char in lodash. Trap: for..in (proto walk); throwing on empty (wrong); ignoring string keys for objects; Symbol keys (excluded by Object.keys)."

---

## 13. 60-second revision

> - **Unified loop** over `keys` list.
> - **Array.isArray** to detect shape.
> - **`Object.keys`** not `for..in`.
> - **3rd iteratee arg** = key (string) or index (number).
> - **Empty + no init → `undefined`** (lodash divergence).
> - **Key order:** ints ascending, then strings insertion.
> - **Own enumerable only** — excludes proto.
> - **Trap:** for..in proto walk; throw on empty; null/Symbol keys.

---

**Related:** [polyfill-reduce.md](./polyfill-reduce.md) · [polyfill-map.md](./polyfill-map.md) · [`08-maps-sets/group-by.md`](../08-maps-sets/group-by.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md), [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
