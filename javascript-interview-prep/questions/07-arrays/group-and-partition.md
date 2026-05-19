# `Array.groupBy` and Partition

> **Difficulty:** Foundation   |   **Time:** ~8 min   |   **Prereqs:** [polyfill-reduce.md](./polyfill-reduce.md), [`08-maps-sets/group-by.md`](../08-maps-sets/group-by.md)
>
> **Source:** ES2024 `Object.groupBy` / `Map.groupBy`. Lodash. Stripe, Razorpay, Atlassian.

---

## 1. Problem statement

Group array items by a key function (multi-bucket) or split into two via predicate.

**Verification examples**

```js
// ES2024
Object.groupBy([1, 2, 3, 4], n => n % 2 ? 'odd' : 'even');
// { odd: [1, 3], even: [2, 4] }

Map.groupBy([1, 2, 3, 4], n => n % 2 ? 'odd' : 'even');
// Map(2) { 'odd' => [1, 3], 'even' => [2, 4] }

// Partition
partition([1, 2, 3, 4], x => x % 2 === 0);
// [[2, 4], [1, 3]]
```

**Constraints**
- `Object.groupBy` requires string/symbol keys (coerced).
- `Map.groupBy` allows any key.
- Insertion order preserved within bucket.
- Partition returns exactly two buckets `[truthy, falsy]`.

---

## 2. Plain-English restatement

`groupBy(arr, fn)` returns object/Map keyed by `fn(item)`, values are arrays of items. `partition(arr, pred)` returns `[truthy, falsy]` — binary split.

---

## 3. Why this matters in interviews

"Group these orders by status." 90% of data wrangling. Senior bar: know ES2024 native, the polyfill, the partition variant.

---

## 4. Mental model

```
   Object.groupBy(arr, fn):
     Coerces fn(item) → string/symbol.
     Returns plain object: { k: [items], ... }.
     null-prototype (no inherited properties).
   
   Map.groupBy(arr, fn):
     Allows ANY key (including object refs).
     Returns Map<key, items[]>.
   
   Both preserve insertion order within each bucket.
   
   Polyfill (single pass):
     for each item:
       k = fn(item)
       (acc[k] ??= []).push(item)
   
   Partition (binary):
     for each item:
       (pred(item) ? truthy : falsy).push(item)
     Return [truthy, falsy].
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Difference between `Object.groupBy` and `Map.groupBy`?
> 2. Order preservation in buckets?
> 3. Polyfill via reduce?

---

## 6. Brute force — walked through

```js
arr.reduce((acc, x) => {
  const k = fn(x);
  acc[k] = acc[k] || [];
  acc[k].push(x);
  return acc;
}, {});
```

Works. Subtle: `Object.create(null)` avoids prototype pollution risk if `fn` returns 'constructor' / '__proto__'.

---

## 7. The unlocking insight

> **One pass, `(acc[k] ??= []).push(item)`. ES2024: Object.groupBy / Map.groupBy. Partition = binary groupBy.**

Three properties:

1. **One pass** — O(n).
2. **`acc[k] ??= []`** — short-circuit init.
3. **Map for non-string keys**.

---

## 8. Solution (annotated)

```js
// Polyfill: groupBy → object (string keys)
function groupBy(arr, fn) {
  const out = Object.create(null);                                       // step 1: no prototype
  for (const item of arr) {
    const k = fn(item);                                                  // step 2: derive key
    (out[k] ??= []).push(item);                                          // step 3: init+push
  }
  return out;
}

// Polyfill: Map version (any key)
function groupByMap(arr, fn) {
  const out = new Map();
  for (const item of arr) {
    const k = fn(item);
    if (!out.has(k)) out.set(k, []);
    out.get(k).push(item);
  }
  return out;
}

// Partition — binary split
function partition(arr, pred) {
  const truthy = [];
  const falsy = [];
  for (const item of arr) {
    (pred(item) ? truthy : falsy).push(item);                            // step 4: ternary push
  }
  return [truthy, falsy];
}
```

**Try it yourself**

```js
// Native ES2024 (Node 21+, modern browsers)
const orders = [
  {id:1, status:'paid'}, {id:2, status:'pending'}, {id:3, status:'paid'}
];

Object.groupBy(orders, o => o.status);
// { paid: [{id:1,...}, {id:3,...}], pending: [{id:2,...}] }

// Map.groupBy with non-string keys
const events = [{ts: '2024-01-01', kind: 'A'}, ...];
const byMonth = Map.groupBy(events, e => new Date(e.ts).getMonth());
byMonth.get(0);  // January

// Polyfill
groupBy([1, 2, 3, 4], n => n % 2 ? 'odd' : 'even');
// { odd: [1, 3], even: [2, 4] }

partition([1, 2, 3, 4, 5], x => x > 2);
// [[3, 4, 5], [1, 2]]

// Combined: groupBy then transform
const summary = Object.fromEntries(
  Object.entries(groupBy(orders, o => o.status))
    .map(([k, v]) => [k, v.length])
);
// { paid: 2, pending: 1 }
```

---

## 9. Step-by-step dry run

```
groupBy([1,2,3,4], n => n%2?'odd':'even'):
  out = null-proto {}.
  item=1: k='odd'. out['odd'] ??= [] → []. push 1 → ['odd':[1]].
  item=2: k='even'. out['even'] ??= [] → []. push 2 → {'odd':[1], 'even':[2]}.
  item=3: k='odd'. out['odd'] exists → push 3 → ['odd':[1,3]].
  item=4: k='even'. push 4 → ['even':[2,4]].
  Return {odd:[1,3], even:[2,4]}.

Insertion order preserved: 'odd' bucket sees 1 before 3; 'even' sees 2 before 4.
Object key order: 'odd' appears before 'even' (first occurrence wins).

partition([1,2,3,4], x=>x%2===0):
  item=1: pred false → falsy.push(1) → [[], [1]].
  item=2: pred true → truthy.push(2) → [[2], [1]].
  item=3: false → falsy → [[2], [1,3]].
  item=4: true → truthy → [[2,4], [1,3]].
  Return [[2,4], [1,3]].
```

---

## 10. Common confusion + traps

1. **`Object.groupBy` coerces keys to string** — non-string lost detail.
2. **Prototype pollution** — `fn` returns `'__proto__'` → bug. Use `Object.create(null)` or Map.
3. **`acc[k] = acc[k] || []`** — fine, but `??=` cleaner.
4. **Partition return shape** — `[truthy, falsy]` standard; lodash returns same.
5. **In-place mutation** — groupBy doesn't mutate input.
6. **Stable order within bucket** — preserved; relies on for-of iteration.
7. **`reduce` polyfill** — works; for-of clearer.

---

## 11. Senior follow-ups & variants

### Variant 1 — Multi-key groupBy
Composite key: `${a}|${b}` (or array key with Map).

### Variant 2 — Aggregated groupBy (sum, count)
Avoid building arrays — fold in-place.

### Variant 3 — `groupBy` returning Map for non-string keys
ES2024 `Map.groupBy`.

### Variant 4 — Lazy groupBy
Generator yielding `[key, items[]]` after each new key first seen.

### Variant 5 — SQL analogy
GROUP BY with HAVING — filter post-group.

---

## 12. How to think aloud

> "groupBy is the core data-shape primitive — 90% of wrangling reduces to 'group by key, transform per group'. ES2024 ships `Object.groupBy(arr, fn)` (string keys, coerced) and `Map.groupBy(arr, fn)` (any key including object refs). Polyfill: single pass, `(out[k] ??= []).push(item)`. Use `Object.create(null)` to avoid `__proto__` key pollution. Map version for non-string keys. Partition is the binary special case: `[truthy, falsy]`. Both preserve insertion order within buckets. Variants: multi-key (composite or Map with array key); aggregated (count/sum in-place — don't build arrays); SQL HAVING (filter buckets post-group). Trap: prototype pollution; `Object.groupBy` coercing non-string keys; expecting Map ordering with Object keys."

---

## 13. 60-second revision

> - **ES2024:** `Object.groupBy` (string keys), `Map.groupBy` (any key).
> - **Polyfill:** `(out[k] ??= []).push(item)` in one pass.
> - **`Object.create(null)`** to avoid prototype pollution.
> - **Partition:** binary `[truthy, falsy]`.
> - **Order preserved** within bucket.
> - **Aggregated variant** — fold instead of pushing.
> - **SQL analogy** — GROUP BY + HAVING.
> - **Trap:** `__proto__` pollution; string-coerce keys; mutate input.

---

**Related:** [polyfill-reduce.md](./polyfill-reduce.md) · [polyfill-filter.md](./polyfill-filter.md) · [`08-maps-sets/group-by.md`](../08-maps-sets/group-by.md) · [`08-maps-sets/multiset-counter.md`](../08-maps-sets/multiset-counter.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
