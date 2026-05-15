# Implement `Array.prototype.groupBy(fn)` — polyfill

## Source
- LeetCode #2631 "Group By" — https://leetcode.com/problems/group-by/
- ES2024 native: `Object.groupBy(iterable, keyFn)` and `Map.groupBy(iterable, keyFn)`.

## Why this question matters in interviews
Group-by is one of the **most common backend data-shaping primitives** — bucketing rows by user, status, day, region — yet for years JavaScript made you hand-roll it with `reduce`. The interviewer is checking whether you reach for `Array.prototype.reduce` cleanly, choose the right return container (object vs Map), and handle the **non-string-key** case. Now that ES2024 ships `Object.groupBy` / `Map.groupBy`, this is also a "what's new in the language" question. Bonus: senior engineers usually have an opinion on **why the spec returns objects with `null` prototype** (prototype pollution).

## Concepts involved

### Syntax to lock in
```js
// Polyfill on Array.prototype
Array.prototype.groupBy = function (fn) {
  const result = Object.create(null); // no inherited keys
  for (let i = 0; i < this.length; i++) {
    const key = fn(this[i], i);
    if (!result[key]) result[key] = [];
    result[key].push(this[i]);
  }
  return result;
};

// Usage
[1, 2, 3, 4].groupBy(n => n % 2 === 0 ? 'even' : 'odd');
// -> { odd: [1, 3], even: [2, 4] }

// ES2024 native (no Array.prototype mutation needed)
Object.groupBy([1, 2, 3, 4], n => n % 2 ? 'odd' : 'even');
Map.groupBy([{}, {}], obj => obj);  // keys can be objects!
```

### Runtime / engine behavior
- `Array.prototype.reduce` is the classic implementation primitive. `for` loop is faster (no function-call overhead per iteration) but the result is the same.
- `Object.create(null)` returns a **bare object** with no `__proto__`, no `toString`, no `hasOwnProperty`. Critical because if the user-supplied key function ever returns `"__proto__"` or `"toString"`, a regular `{}` would either be unsafe or polluted. The ES2024 spec mandates a null-prototype object for exactly this reason.
- Keys returned from `fn` are coerced to strings when stored in an object (`null` → `"null"`, objects → `"[object Object]"`). That's why `Map.groupBy` exists — it preserves key identity.
- `Object.groupBy` is in V8 ≥ 11.7 (Node 21+), Safari 17.4+, FF 119+. Polyfill needed for older runtimes.

### Edge cases (these are the interview traps)
1. **Non-string keys** — `fn` returns `42` → coerced to `"42"`. Returns `null` → `"null"`. Returns `{}` → `"[object Object]"` (all distinct objects collide). If you need object keys, use **`Map.groupBy`**.
2. **`fn` returns `undefined`** — coerced to the string `"undefined"`. Items are still grouped. Some interviewers want them filtered; ask.
3. **Prototype pollution** — `fn(x) === '__proto__'` on a plain `{}` either silently fails or pollutes `Object.prototype`. Always `Object.create(null)`.
4. **Empty input** — return `Object.create(null)` (empty), not `{}` — to be consistent. Or just return `{}`; LeetCode accepts both.
5. **Mutating `Array.prototype`** — the question literally asks for this, but in real code adding to built-ins is **forbidden** (breaks `for...in`, conflicts with future spec additions). Mention it.
6. **Index in keyFn** — spec passes `(element, index)`. Don't forget the index parameter; some interviewers test it.
7. **Stable order within groups** — guaranteed because you iterate left-to-right and push. Don't accidentally reorder.
8. **Sparse arrays** — `[,,1].groupBy(...)` should skip holes (native `Object.groupBy` doesn't — it treats holes as `undefined`). Match the spec.

## Brute force approach
Two passes: first collect unique keys, then for each key filter the array. O(n × k). Don't.

## Optimal approach
Single pass with `reduce` (or `for` loop). Build an accumulator object/Map keyed by `fn(x)`, push `x` into the bucket. O(n) time, O(n) space.

For object-identity keys (function returns objects/numbers/NaN), use a `Map` accumulator instead.

## Solution (JavaScript)

```js
/**
 * Polyfill Array.prototype.groupBy(fn).
 * Returns an object keyed by stringified fn(el, i) -> array of elements.
 * Uses a null-prototype object to avoid prototype pollution.
 */
Array.prototype.groupBy = function (fn) {
  if (typeof fn !== 'function') {
    throw new TypeError('groupBy: callback is not a function');
  }
  const result = Object.create(null);
  for (let i = 0; i < this.length; i++) {
    const el = this[i];
    const key = fn(el, i);                        // key coerced to string
    if (result[key] === undefined) result[key] = [];
    result[key].push(el);
  }
  return result;
};

/**
 * Map-based variant — key identity preserved (objects, NaN, etc. all distinct).
 * Mirrors ES2024 Map.groupBy(iterable, keyFn).
 */
function mapGroupBy(iterable, keyFn) {
  const result = new Map();
  let i = 0;
  for (const el of iterable) {
    const key = keyFn(el, i++);
    const bucket = result.get(key);
    if (bucket) {
      bucket.push(el);
    } else {
      result.set(key, [el]);
    }
  }
  return result;
}
```

## Step-by-step dry run

Input:
```js
const users = [
  { name: 'Ada',  role: 'admin' },
  { name: 'Bob',  role: 'user'  },
  { name: 'Cici', role: 'admin' },
  { name: 'Dee',  role: 'user'  },
];

const byRole = users.groupBy(u => u.role);
```

Trace (i, key, accumulator):
- `i=0`, el=`{Ada,admin}`, key=`'admin'`. `result.admin` is undefined → create `[]`. Push Ada. `result = { admin: [Ada] }`.
- `i=1`, el=`{Bob,user}`, key=`'user'`. `result.user` is undefined → create `[]`. Push Bob. `result = { admin: [Ada], user: [Bob] }`.
- `i=2`, el=`{Cici,admin}`, key=`'admin'`. Exists → push Cici. `result = { admin: [Ada, Cici], user: [Bob] }`.
- `i=3`, el=`{Dee,user}`, key=`'user'`. Exists → push Dee. `result = { admin: [Ada, Cici], user: [Bob, Dee] }`.

Return that object (with null prototype).

Counter-example showing why **null-prototype matters**:
```js
[1].groupBy(() => '__proto__');
// With Object.create(null):  { __proto__: [1] }   (correct, safe)
// With {}                  :  {} but ({}).__proto__ is now [1]  — POLLUTED
```

## Important takeaways

**Syntax to memorize**
- `Object.create(null)` — never `{}` — for the accumulator.
- `for` loop + `if (!result[key]) result[key] = []; result[key].push(el)`.
- Map-based variant for object/NaN keys: `result.get(key) ?? (...)`.

**Patterns to reuse**
- "Reduce-into-accumulator" — same skeleton as `countBy`, `keyBy`, `partition`, `indexBy`, histogram.
- `Object.create(null)` whenever **user input** decides keys — defends against `__proto__` / `constructor` pollution.

**Common mistakes**
- Using `{}` and being silently vulnerable to `__proto__` pollution.
- Using `Array.prototype.reduce` with `result[key] || []` — works but allocates a new empty array every iteration (the `||` evaluates both sides on the first hit only, so it's fine, actually — but the `result[key] || (result[key] = [])` shortcut idiom trips many candidates).
- Forgetting that `null`, `undefined`, `NaN`, objects all coerce to strings on object keys — `Map.groupBy` exists for that exact reason.
- Reordering elements inside a group. Always push left-to-right.

**Related questions**
- `Object.fromEntries(Object.entries(o).map(...))`
- `partition` — split into two arrays by predicate.
- `countBy(arr, fn)` — same shape, value is a count.
- `indexBy(arr, fn)` — same shape but expects unique key (value is the element, not array).

## Variants

1. **`countBy(arr, fn)`** — same skeleton, but `result[key] = (result[key] || 0) + 1`. Returns `{ key: number }`.

2. **`Map.groupBy` (ES2024)** — like `Object.groupBy` but returns a `Map` so keys can be any value (object identity, NaN, etc.). Useful for grouping by reference, e.g., `Map.groupBy(orders, o => o.user)` keyed by user objects directly.

3. **Async groupBy** — keyFn returns a Promise. Use `Promise.all(arr.map(keyFn))` first, then group synchronously. Common in real backends where the key is a derived async lookup.

## Revision notes

> **groupBy — 60 second recap**
> - One pass: for each `el`, compute `key = fn(el, i)`, push into `result[key]`.
> - Use `Object.create(null)` — defends against `__proto__` pollution.
> - Object/NaN keys → use `Map.groupBy` (ES2024) or a hand-rolled Map version.
> - Native `Object.groupBy(arr, fn)` exists in Node 21+ / modern browsers.
> - **Trap:** `fn` returns `'__proto__'` and you used `{}` → pollutes `Object.prototype`. Always `Object.create(null)`.
> - Family: `countBy`, `keyBy`, `partition` — same reduce-into-accumulator skeleton.
