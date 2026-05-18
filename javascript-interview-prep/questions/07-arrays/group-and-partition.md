# `Array.groupBy` and Partition

## Source / Origin
- ES2024 `Object.groupBy` / `Map.groupBy`; lodash `groupBy` / `partition`.
- Asked at: Stripe, Razorpay, Atlassian (data-shape questions).
- Concept reference: `concepts/arrays.md`.

## Why this question matters in interviews
"Group these orders by status." 90% of data wrangling. Senior bar: you know the modern `Object.groupBy` / `Map.groupBy`, the polyfill, and the partition variant (group into exactly two buckets).

## Concepts involved

```js
// ES2024
Object.groupBy([1,2,3,4], n => n % 2 ? 'odd' : 'even');
// { odd: [1,3], even: [2,4] }

Map.groupBy([1,2,3,4], n => n % 2 ? 'odd' : 'even');
// Map(2) { 'odd' => [1,3], 'even' => [2,4] }

// Polyfill (manual)
function groupBy(arr, fn) {
  const out = Object.create(null);
  for (const x of arr) {
    const k = fn(x);
    (out[k] ??= []).push(x);
  }
  return out;
}

// Partition (binary split)
function partition(arr, predicate) {
  const truthy = [], falsy = [];
  for (const x of arr) (predicate(x) ? truthy : falsy).push(x);
  return [truthy, falsy];
}
```

### Edge cases / traps
1. **`Object.groupBy` requires string/symbol keys.** Non-strings get coerced. For object keys use `Map.groupBy`.
2. **Polyfill with plain `{}`** has `__proto__` collision risk. Use `Object.create(null)`.
3. **Sort within groups** is a separate step.
4. **Multi-group**: a single item can be in many buckets — needs different shape (Array of buckets).
5. **Browser support** — modern only; ship with polyfill for older targets.
6. **`Map.groupBy`** preserves insertion order of group keys.

## Mental Model

```
   [a, b, c, d, e]  --fn-->  k1, k2, k1, k3, k2
                                  ↓
                            { k1: [a, c], k2: [b, e], k3: [d] }
```

## Why interviewers care

- **Idiomatic data shaping.**
- **Modern API awareness** (ES2024).
- **Polyfill skill.**

## Common confusion

- **"`groupBy` returns array of groups."** It returns an object/Map keyed by group.
- **"`Object.groupBy` accepts objects as keys."** No — coerces to string. Use Map.
- **"Reduce is the same."** Yes, but verbose:
  ```js
  arr.reduce((acc, x) => { (acc[fn(x)] ??= []).push(x); return acc; }, Object.create(null));
  ```

## Solution

```js
// Group orders by status
const groups = Object.groupBy(orders, o => o.status);
// { paid: [...], pending: [...], cancelled: [...] }

// Partition into eligible/ineligible
const [eligible, ineligible] = partition(users, u => u.age >= 18);

// Map.groupBy with object key (e.g., date object)
const byDay = Map.groupBy(events, e => new Date(e.ts).toDateString());

// Multi-key group (composite)
const byStatusAndCountry = Object.groupBy(orders, o => `${o.status}|${o.country}`);

// Top-N per group
function topNPerGroup(arr, groupFn, sortFn, n) {
  const groups = Object.groupBy(arr, groupFn);
  for (const k in groups) groups[k] = groups[k].sort(sortFn).slice(0, n);
  return groups;
}

// Polyfill for older runtimes
if (!Object.groupBy) {
  Object.groupBy = (arr, fn) => {
    const out = Object.create(null);
    for (const x of arr) {
      const k = fn(x);
      (out[k] ??= []).push(x);
    }
    return out;
  };
}
```

## Dry run

```js
const items = [{ t: 'a', n: 1 }, { t: 'b', n: 2 }, { t: 'a', n: 3 }];

Object.groupBy(items, i => i.t)
// { a: [{t:'a',n:1}, {t:'a',n:3}], b: [{t:'b',n:2}] }

partition(items, i => i.n > 1)
// [[{t:'b',n:2},{t:'a',n:3}], [{t:'a',n:1}]]
```

## How to think aloud

> "ES2024 gives Object.groupBy and Map.groupBy. Object.groupBy stringifies keys; Map.groupBy keeps them as-is — use Map for object keys. Polyfill with reduce or for-loop. Partition is the binary version. Multi-group needs a different shape; composite key with a separator works for naive cases. For older runtimes I'd polyfill."

## Important takeaways

- **`Object.groupBy(arr, fn)`** — string keys.
- **`Map.groupBy(arr, fn)`** — object keys, preserves order.
- **Polyfill** with reduce or for-loop.
- **`partition(arr, pred)`** for binary split.
- **`Object.create(null)`** to avoid `__proto__` collision.
- **Composite key** with delimiter for multi-field grouping.

## Variants

- **Streaming groupBy** — async iterator; flush per group when key changes (sorted input).
- **Counting (not collecting)** — `Object.fromEntries(arr.map(...))` for histogram.
- **`groupByKey` (deprecated)** — older Stage 2 name.

## Revision notes

```
ES2024:
  Object.groupBy(arr, fn) → {key: arr[]}   (string keys)
  Map.groupBy(arr, fn)   → Map<key, arr[]> (any key)

polyfill:
  arr.reduce((acc, x) => ((acc[fn(x)] ??= []).push(x), acc), Object.create(null))

partition (binary):
  function partition(arr, pred) {
    const t=[], f=[]
    for x of arr: (pred(x) ? t : f).push(x)
    return [t, f]
  }

TRAPS:
  - Object key coercion (use Map for object keys)
  - {} has __proto__ collision; use Object.create(null)
  - multi-group needs different shape
```
