# `Array.prototype.groupBy(fn)` — polyfill

> **Difficulty:** Foundation   |   **Time:** ~10 min   |   **Prereqs:** [`07-arrays/group-and-partition.md`](../07-arrays/group-and-partition.md), [`07-arrays/polyfill-reduce.md`](../07-arrays/polyfill-reduce.md)
>
> **Source:** LeetCode #2631. ES2024 `Object.groupBy` / `Map.groupBy`.

---

## 1. Problem statement

Group array items by a key function. Object output for string keys; Map for any key. Use null-prototype object for Object output.

**Verification examples**

```js
[1, 2, 3, 4].groupBy(n => n % 2 ? 'odd' : 'even');
// {odd: [1, 3], even: [2, 4]}

// ES2024 native
Object.groupBy([1, 2, 3, 4], n => n % 2 ? 'odd' : 'even');
Map.groupBy(items, item => item.refObject);   // object keys

// Prototype pollution safe
[].groupBy(() => '__proto__');                // works on null-proto object
```

**Constraints**
- Use `Object.create(null)` to avoid prototype pollution.
- Map version for non-string keys.
- Preserve insertion order within bucket.
- ES2024 native is the modern answer.

---

## 2. Plain-English restatement

For each item, derive a key; push into the bucket for that key. Initialize bucket if first occurrence.

---

## 3. Why this matters in interviews

Common backend data-shaping. Tests: choice of return container, prototype-pollution awareness, single-pass design. ES2024 native vs polyfill recognition.

---

## 4. Mental model

```
   Polyfill (object output):
     result = Object.create(null)
     for i, item in this:
       k = fn(item, i)
       (result[k] ??= []).push(item)
     return result
   
   Map version (non-string keys):
     result = new Map()
     for item in this:
       k = fn(item)
       if (!result.has(k)) result.set(k, [])
       result.get(k).push(item)
   
   ES2024 native:
     Object.groupBy(iter, keyFn) — string/symbol keys; null-prototype object.
     Map.groupBy(iter, keyFn)   — any key.
   
   Prototype pollution:
     fn returns '__proto__' → {} would mutate Object.prototype!
     Object.create(null) has no __proto__.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why `Object.create(null)`?
> 2. When use Map over Object?
> 3. Are keys coerced to strings in Object?

---

## 6. Brute force — walked through

```js
[1, 2, 3].reduce((acc, x) => {
  const k = fn(x);
  acc[k] = acc[k] || [];
  acc[k].push(x);
  return acc;
}, {});
```

Works, but `{}` is prototype-polluting if `fn` returns `'__proto__'`.

---

## 7. The unlocking insight

> **One pass: derive key, init bucket, push. Use `Object.create(null)` or `Map`. ES2024 native available.**

Three properties:

1. **Single pass** — O(n).
2. **`Object.create(null)`** or Map.
3. **`(acc[k] ??= []).push(item)`** idiom.

---

## 8. Solution (annotated)

```js
// Polyfill on Array.prototype (matches ES2024 Object.groupBy semantics)
if (!Array.prototype.groupBy) {
  Object.defineProperty(Array.prototype, 'groupBy', {
    enumerable: false,
    value: function (fn) {
      const result = Object.create(null);                                 // step 1: null-proto
      for (let i = 0; i < this.length; i++) {
        const k = fn(this[i], i);                                          // step 2: derive key
        (result[k] ??= []).push(this[i]);                                  // step 3: init+push
      }
      return result;
    },
  });
}

// Standalone helper
function groupBy(iter, fn) {
  const result = Object.create(null);
  let i = 0;
  for (const item of iter) {
    const k = fn(item, i++);
    (result[k] ??= []).push(item);
  }
  return result;
}

// Map version
function groupByMap(iter, fn) {
  const result = new Map();                                                // step 4: any key
  let i = 0;
  for (const item of iter) {
    const k = fn(item, i++);
    if (!result.has(k)) result.set(k, []);
    result.get(k).push(item);
  }
  return result;
}
```

**Try it yourself**

```js
[1, 2, 3, 4].groupBy(n => n % 2 ? 'odd' : 'even');
// {odd: [1, 3], even: [2, 4]}

const orders = [
  { id: 1, status: 'paid' },
  { id: 2, status: 'pending' },
  { id: 3, status: 'paid' },
];

groupBy(orders, o => o.status);
// {paid: [...], pending: [...]}

// Non-string key — must use Map
const usersByCompany = groupByMap(users, u => u.company);   // company is object ref
usersByCompany.get(acme).length;

// Prototype pollution test
const evil = [{}, {}].groupBy(() => '__proto__');
// Polyfill: {__proto__: [{}, {}]} — own key, safe.
// Naive `{}`: {} (mutates Object.prototype) — VERY BAD.

// ES2024 native (Node 21+)
Object.groupBy([1, 2, 3], n => n > 1 ? 'big' : 'small');

Map.groupBy(employees, e => e.department);   // department is object → use Map
```

---

## 9. Step-by-step dry run

```
[1, 2, 3, 4].groupBy(n => n % 2 ? 'odd' : 'even'):
  result = null-proto {}.
  i=0 n=1: k='odd'. result['odd'] ??= [] → []. push 1. result = {odd: [1]}.
  i=1 n=2: k='even'. result['even'] ??= [] → []. push 2. result = {odd:[1], even:[2]}.
  i=2 n=3: k='odd'. existing. push 3. result = {odd:[1,3], even:[2]}.
  i=3 n=4: k='even'. existing. push 4. result = {odd:[1,3], even:[2,4]}.
  Return.

Order:
  Keys appear in result in FIRST-occurrence order.
  Values within bucket: insertion order.

Pollution:
  arr.groupBy(() => '__proto__'):
    With Object.create(null): result['__proto__'] = [...] (own key). Safe.
    With {}: {}.__proto__ === Object.prototype. Assigning to it walks setters; can replace Object.prototype. BAD.

  ES2024 spec explicitly uses null-proto for this reason.
```

---

## 10. Common confusion + traps

1. **`{}` for output** — prototype pollution risk.
2. **Coercion** — Object keys become strings; for non-strings use Map.
3. **`Object.fromEntries(map)`** to convert Map → plain object (when safe).
4. **Mutate input** — groupBy must NOT mutate.
5. **Symbol keys** — Object.groupBy supports symbol keys; Object.keys does not enumerate.
6. **Stable bucket order** — insertion order preserved.
7. **`fn` throws** — propagates; group state lost.

---

## 11. Senior follow-ups & variants

### Variant 1 — Aggregated groupBy
Avoid arrays — fold per group (count/sum).

### Variant 2 — Multi-key groupBy
Composite key (`${a}|${b}`) or array key with Map.

### Variant 3 — `Map.groupBy` for object refs
Native ES2024.

### Variant 4 — `partition` (binary)
`[truthy, falsy]`.

### Variant 5 — Lazy groupBy
Generator yielding `[key, items]` after each new key first seen.

---

## 12. How to think aloud

> "groupBy: single pass, derive key, init bucket if needed, push. ES2024 native: `Object.groupBy(iter, keyFn)` for string keys (returns null-prototype object), `Map.groupBy` for any key (returns Map with original key identity preserved). Polyfill: use `Object.create(null)` to avoid prototype pollution — if `keyFn` returns `'__proto__'` or `'toString'`, a regular `{}` could either mutate `Object.prototype` (catastrophic) or have weird behavior. The `(result[k] ??= []).push(item)` idiom is the cleanest init-and-push. Map version when keys aren't strings/symbols (object refs, Map keys, etc.). Insertion order: bucket order = first-occurrence of key; within-bucket order = input order. Variants: aggregated (count/sum without arrays), multi-key (composite string or array-key Map), partition (binary), lazy generator. Trap: `{}` output (prototype pollution); string coercion of non-string keys; mutating input."

---

## 13. 60-second revision

> - **One pass:** `(acc[k] ??= []).push(item)`.
> - **`Object.create(null)`** for safe object output.
> - **Map version** for non-string keys.
> - **ES2024:** `Object.groupBy` / `Map.groupBy`.
> - **Insertion order** preserved.
> - **Prototype pollution risk** with `{}`.
> - **Partition** = binary special case.
> - **Aggregated variant** — fold instead of array.
> - **Trap:** `{}`; coercion; mutate input.

---

**Related:** [`07-arrays/group-and-partition.md`](../07-arrays/group-and-partition.md) · [multiset-counter.md](./multiset-counter.md) · [group-anagrams.md](./group-anagrams.md) · [composite-key-strategies.md](./composite-key-strategies.md)

**Concept primer:** [`concepts/maps-sets.md`](../../concepts/maps-sets.md)
