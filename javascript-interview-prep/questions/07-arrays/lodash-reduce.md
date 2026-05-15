# Lodash-style `reduce` — Works on Arrays *and* Objects

## Source
- codedamn Lab: "Lodash _.reduce() Lab" — https://codedamn.com/problem/ApyKwJzkW0be4dtQpP3vK
- Lodash docs: https://lodash.com/docs/4.17.15#reduce
- Common follow-up after the standard `reduce` polyfill.

## Why this question matters in interviews
Once you've nailed the `Array.prototype.reduce` polyfill, the interviewer flips the question: **"now make it work on plain objects too — like lodash."** This single twist tests whether you know (a) how to detect "array-like vs plain object" in the wild, (b) `Object.keys` vs `Object.entries` vs `for...in` (with prototype-chain gotchas), and (c) how to design a function that handles two collection shapes without leaking abstractions. Backend engineers reduce over objects constantly — config trees, header maps, aggregated counters keyed by user. If you internalize this you'll stop reaching for the lodash dep for one-off folds.

## Concepts involved

### Lodash signature
```js
_.reduce(collection, iteratee, [accumulator]);
// iteratee(accumulator, value, key|index, collection)
```

Key differences from native:
1. **Accepts arrays *or* plain objects.** Iterates keys/values for objects.
2. **Iteratee's third arg is `key`** (string) for objects, `index` (number) for arrays.
3. **If no accumulator is provided**, uses the first element of the collection as the seed (same as native for arrays; for objects, "first" means the first key in iteration order).
4. **Empty collection + no accumulator** → returns `undefined` (lodash does NOT throw; native `reduce` does). Mention this divergence explicitly.

### Iteration order for objects
- `Object.keys(obj)` returns keys in the order: integer-like keys ascending, then string keys in insertion order, then Symbol keys (excluded by `Object.keys`). This is **deterministic** since ES2015 but candidates often think it's random.
- `for...in` walks the prototype chain too — that's why you guard with `hasOwnProperty` or just use `Object.keys`. The latter is safer.

### Detecting "what kind of collection"
- `Array.isArray(coll)` — the only reliable array check. `instanceof Array` fails across iframes/realms.
- Plain object: fall through. Lodash also accepts strings (iterates chars) and array-likes (objects with `length`); skip those unless the interviewer pushes.

### Mutating vs non-mutating
`reduce` is non-mutating regardless of collection. The accumulator may be mutated *by the iteratee* (common: `(acc, v) => { acc[v] = true; return acc; }`), but that's the caller's choice — the polyfill doesn't touch the input.

## Brute force approach
Two completely separate code paths, one calling `arr.reduce(...)` and one looping `Object.keys` — duplicated logic, no shared seed/empty-collection handling. Works, but reads like a junior PR. Refactor into a single function that branches on `Array.isArray` only for *choosing the key list*, then runs one unified loop.

## Optimal approach
Compute a `keys` list once — indices `[0..len-1]` for arrays, `Object.keys(obj)` for objects. Then run the standard reduce loop over `keys`, treating each `k` uniformly. The "no accumulator" branch picks the first key's value and starts iteration at the next key.

## Solution (JavaScript)

```js
/**
 * Lodash-style reduce that works on arrays AND plain objects.
 * @param {Array|Object} collection
 * @param {(acc:any, value:any, keyOrIndex:string|number, collection:any) => any} iteratee
 * @param {*} [accumulator]
 * @returns {*}
 */
function reduce(collection, iteratee, accumulator) {
  if (collection == null) return accumulator;
  if (typeof iteratee !== 'function') {
    throw new TypeError('iteratee is not a function');
  }

  const isArr = Array.isArray(collection);
  const keys = isArr
    ? collection.map((_, i) => i)        // [0..n-1]; preserves hole skipping via the loop guard below
    : Object.keys(collection);            // own enumerable keys, insertion order

  let i = 0;
  let acc;
  const hasInitial = arguments.length >= 3;

  if (hasInitial) {
    acc = accumulator;
  } else {
    // Skip leading holes for arrays
    if (isArr) {
      while (i < keys.length && !(keys[i] in collection)) i++;
    }
    if (i >= keys.length) return undefined;   // lodash: no throw on empty
    acc = collection[keys[i++]];
  }

  for (; i < keys.length; i++) {
    const k = keys[i];
    if (isArr && !(k in collection)) continue; // skip holes
    acc = iteratee(acc, collection[k], isArr ? k : String(k), collection);
  }
  return acc;
}
```

## Step-by-step dry run

**Array input:**
```js
reduce([1, 2, 3], (acc, v, i) => acc + v * i, 0);
// iterations: (0,1,0)→0, (0,2,1)→2, (2,3,2)→8 → 8
```
- `isArr=true`, `keys=[0,1,2]`, `hasInitial=true`, `acc=0`.
- `i=0`: `acc = 0 + 1*0 = 0`. `i=1`: `acc = 0 + 2*1 = 2`. `i=2`: `acc = 2 + 3*2 = 8`.
- Return `8`.

**Object input — sum values:**
```js
reduce({ a: 10, b: 20, c: 30 }, (acc, v) => acc + v, 0);
// → 60
```
- `isArr=false`, `keys=['a','b','c']`. `acc=0`.
- iter: 10, 30, 60. Return `60`.

**Object input — no accumulator (uses first value as seed):**
```js
reduce({ x: 5, y: 7, z: 11 }, (acc, v) => acc * v);
// keys = ['x','y','z']; acc=5; then 5*7=35; 35*11=385.
```

**Empty collection + no accumulator:**
```js
reduce({}, (a,b)=>a+b);          // undefined (lodash) — NOT throw (native does throw)
reduce([], (a,b)=>a+b);          // undefined
reduce([], (a,b)=>a+b, 0);       // 0
```

**`null` collection — lodash safety:**
```js
reduce(null, fn, 42);    // 42
reduce(undefined, fn);    // undefined
```

## Important takeaways

**Syntax to memorize**
- `Array.isArray(coll)` is the **only** reliable array check.
- `Object.keys(obj)` for own enumerable keys, in deterministic order (integer-like ascending, then strings in insertion order).
- `arguments.length >= 3` for "did caller pass an accumulator?" — same trick as native `reduce`.

**Patterns to reuse**
- "Compute the key list, then loop uniformly" is the lodash pattern for `forEach`, `map`, `filter`, `every`, `some`, `find` — all of them dispatch on `Array.isArray` exactly once.
- Treating arrays as objects-with-numeric-keys is a useful mental model when writing generic data utilities.

**Common mistakes**
- Using `for...in` on `collection` — walks the prototype chain, picks up inherited props, and on arrays gives string keys (`"0"`, `"1"`) not numbers.
- Forgetting that lodash *doesn't* throw on empty + no accumulator. If you ship the native-style throw, lodash users will be surprised.
- Not handling `null`/`undefined` `collection`. Lodash's defensive style here is part of the appeal — replicate it.
- Calling `Object.entries` and destructuring inside the loop — works, but allocates an extra `[k,v]` array per iteration. Fine for small data; flag as a perf note for large objects.

**Related questions**
- Lodash `_.map`, `_.filter`, `_.forEach` on objects — same dispatch pattern.
- `_.groupBy(coll, iteratee)` — built as a reduce.
- `_.keyBy(coll, iteratee)` — also a reduce.

## Variants

1. **`reduceRight` over keys** — for objects, reverse the `Object.keys` array. For arrays, walk indices descending. Useful for right-folds (e.g., function composition: `compose = fns => x => fns.reduceRight((acc, f) => f(acc), x)`).
2. **Support array-likes** — objects with `length` (e.g., `arguments`, `NodeList`). Detect via `typeof coll.length === 'number'`. Lodash does this; native `reduce` doesn't.
3. **Iteratee shorthand** — lodash accepts strings (`'name'` → `obj => obj.name`) and objects (`{ active: true }` → predicate). Build an `iteratee` resolver that wraps the user input. Common follow-up to test design taste.

## Revision notes

> **lodash _.reduce — 60 second recap**
> - Works on **arrays** and **plain objects**. Dispatch on `Array.isArray`.
> - Key list: `[0..n-1]` for arrays, `Object.keys(obj)` for objects.
> - Iteratee args: `(acc, value, keyOrIndex, collection)`. Key is string for objects, number for arrays.
> - No accumulator → seed with first element/value; for arrays, skip leading holes first.
> - Empty + no accumulator → **return `undefined`** (lodash quirk; native `reduce` throws).
> - `null`/`undefined` collection → return the accumulator (or `undefined`). Defensive by design.
> - Detect "initial passed" via `arguments.length >= 3`, never `=== undefined`.
> - Skip array holes with `i in collection` inside the loop.
> - **Trap:** using `for...in` — walks prototype chain. Use `Object.keys`.
> - **Trap:** forgetting that lodash doesn't throw on empty; align with the library's convention.
