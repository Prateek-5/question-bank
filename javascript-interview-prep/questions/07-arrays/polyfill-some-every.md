# Polyfill `Array.prototype.some` and `Array.prototype.every`

## Source
- Canonical polyfill interview problem (BFE.dev, GreatFrontEnd, codedamn).
- MDN spec references: [Array.prototype.some](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/some), [Array.prototype.every](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/every).
- ECMAScript spec: https://tc39.es/ecma262/#sec-array.prototype.some

## Why this question matters in interviews
`some` / `every` polyfills look trivial — three lines, right? Wrong. The interview signal here is whether you know the **three quirks no one remembers until they hit production**: short-circuit semantics, hole-skipping on sparse arrays, and `thisArg`. Backend candidates routinely fumble the "what does `[,,,].some(() => true)` return?" follow-up. Senior interviewers ask this to gauge spec literacy — do you actually understand the language or do you just use it? Same family as polyfill-map / filter / reduce, but the short-circuit twist makes it more diagnostic.

## Concepts involved

### Syntax to lock in
```js
// some — return true if ANY element passes
[1, 2, 3].some(x => x > 2);          // true
[].some(() => true);                  // false (vacuously)

// every — return true if ALL elements pass
[1, 2, 3].every(x => x > 0);          // true
[].every(() => false);                // true (vacuously!)
```

### Runtime / engine behavior
- Both iterate from index `0` to `length - 1`, **short-circuiting** the moment the result is decided.
- They skip **holes** in sparse arrays — `[,,,].some(() => true)` is `false`, not `true`. The predicate is never called on missing indices. This is checked with `i in this`, not `this[i] === undefined` (because explicit `undefined` is still a real element).
- `length` is read **once** at the start. Mutating the array during iteration (push/pop) does NOT extend or shorten the range — extra appended elements are not visited.
- `thisArg` is the second argument; it becomes `this` inside the predicate. With arrow functions it's ignored (arrows have lexical `this`).
- The predicate receives `(element, index, array)` — three args, not one.

### Edge cases (the interview traps)
1. **Empty array** — `[].some()` is `false`; `[].every()` is `true`. Vacuous truth. Half of candidates get `every([])` wrong.
2. **Sparse arrays / holes** — `new Array(3).some(() => true)` returns `false`. The slots are holes, not `undefined`. Use `i in this` to detect.
3. **Explicit `undefined` is NOT a hole** — `[undefined].some(() => true)` returns `true`. The slot exists.
4. **`thisArg` is the SECOND param** — many candidates forget it; spec mandates support.
5. **Mutation during iteration** — `length` is snapshotted; pushes after start are ignored, deletions create holes that get skipped.
6. **Coerce result to Boolean** — predicate returning `1` / `0` / `'yes'` must still produce a Boolean from `some`/`every`. Spec says "ToBoolean".
7. **Called on non-array (array-like)** — spec says `some` / `every` work on any object with `length` (e.g., `arguments`, NodeList). Use `Array.prototype.some.call(arrayLike, fn)`.

## Brute force approach
Naive: `arr.filter(fn).length > 0` for `some`, `arr.filter(fn).length === arr.length` for `every`. **Wrong on three counts**:
- No short-circuit — walks the whole array even after the answer is decided.
- Doesn't preserve hole-skip semantics correctly for `every`.
- O(n) memory for the intermediate filtered array. Polyfills must be O(1) extra space.

Drop this path immediately.

## Optimal approach
Classic `for` loop, index 0 to `length - 1`. Use `i in this` to skip holes. Apply `thisArg` via `.call(thisArg, element, i, array)`. Return early on the decisive value — `true` for `some`, `false` for `every`. If the loop completes without short-circuiting, return the fallback (`false` for `some`, `true` for `every`).

O(n) time, O(1) space. Same complexity as native, just slower because it's user-land JS.

## Solution (JavaScript)

```js
// ---- some ----
Array.prototype.mySome = function (predicate, thisArg) {
  if (this == null) {
    throw new TypeError('mySome called on null or undefined');
  }
  if (typeof predicate !== 'function') {
    throw new TypeError(`${predicate} is not a function`);
  }

  const O = Object(this);
  const len = O.length >>> 0;   // ToUint32, like spec

  for (let i = 0; i < len; i++) {
    if (i in O) {                              // skip holes
      if (predicate.call(thisArg, O[i], i, O)) {
        return true;                           // short-circuit
      }
    }
  }
  return false;
};

// ---- every ----
Array.prototype.myEvery = function (predicate, thisArg) {
  if (this == null) {
    throw new TypeError('myEvery called on null or undefined');
  }
  if (typeof predicate !== 'function') {
    throw new TypeError(`${predicate} is not a function`);
  }

  const O = Object(this);
  const len = O.length >>> 0;

  for (let i = 0; i < len; i++) {
    if (i in O) {                              // skip holes
      if (!predicate.call(thisArg, O[i], i, O)) {
        return false;                          // short-circuit
      }
    }
  }
  return true;                                 // vacuous true for []
};
```

## Step-by-step dry run

Input:
```js
const calls = [];
const spy = (x, i) => { calls.push(i); return x > 5; };

[1, 2, 6, 10].mySome(spy);
```

Trace:
- `len = 4`. `thisArg = undefined`.
- `i=0`: `0 in O` is true. `spy(1, 0, O)` → push 0, return `false`. Continue.
- `i=1`: `spy(2, 1, O)` → push 1, return `false`. Continue.
- `i=2`: `spy(6, 2, O)` → push 2, return `true`. **Short-circuit, return `true`**.
- Loop never visits index 3.

Result: `calls = [0, 1, 2]`. Index 3 was never visited — this is the test for whether your polyfill short-circuits.

Sparse-array trace:
```js
const a = [1, , 3];          // hole at index 1
a.mySome((v) => v === undefined);  // → false (hole is skipped)
[undefined, 2, 3].mySome((v) => v === undefined);  // → true (real undefined)
```

## Important takeaways

**Syntax to memorize**
- `O = Object(this)` first — protects against primitive `this`.
- `len = this.length >>> 0` — spec's ToUint32 coercion (turns negatives / floats / `NaN` into safe uint32).
- `i in O` — the hole check. NEVER use `O[i] !== undefined`.
- `predicate.call(thisArg, O[i], i, O)` — three args, plus `thisArg`.

**Patterns to reuse**
- The hole-skip + thisArg + length-snapshot trio is the **same pattern** for `forEach`, `map`, `filter`, `some`, `every`. Memorize once, reuse everywhere. `find` and `findIndex` are the **exceptions** — they don't skip holes.
- Short-circuit return is the differentiator for `some`/`every`/`find`/`findIndex` vs the full-iteration siblings.

**Common mistakes**
- Returning the predicate's raw value instead of a Boolean — spec says coerce.
- Forgetting `thisArg` — fails the spec test suite immediately.
- Using `O[i] !== undefined` to detect holes — fails the explicit-undefined case.
- Reading `O.length` inside the loop — must snapshot once, otherwise mutation breaks iteration semantics.
- `every([])` returning `false` — classic vacuous-truth fumble.

**Related questions**
- Polyfill `Array.prototype.filter` / `map` / `forEach` (same skeleton, no short-circuit).
- Polyfill `find` / `findIndex` (short-circuit, but **no hole-skip**).
- Polyfill `reduce` (short-circuit doesn't apply; initial-value edge case dominates).

## Variants

1. **Async some / every** — "Implement `asyncSome(arr, asyncPredicate)` that short-circuits as soon as the first predicate resolves truthy." Tests Promise + AbortController combo; can't just `Promise.all` because that loses short-circuit.

2. **Polyfill on array-likes** — "Make your `mySome` work on `arguments` and NodeList." Tests that you wrote `Object(this)` and `length >>> 0`, not `Array.isArray` guards.

3. **TypedArray compatibility** — "Will your polyfill work on `Uint8Array`?" Trick: TypedArrays have no holes (every index is initialized to 0), so `i in O` is always true. Polyfill still works but the hole-skip is a no-op.

## Revision notes

> **some / every — 60 second recap**
> - `some`: return `true` on first truthy predicate result; `false` if loop completes. `[].some()` → `false`.
> - `every`: return `false` on first falsy result; `true` if loop completes. `[].every()` → `true` (vacuous).
> - **Skip holes** with `i in this` — never `this[i] !== undefined`.
> - Snapshot `length >>> 0` once; respect `thisArg` (second param).
> - Predicate is called with `(value, index, array)` and `this = thisArg`.
> - **Trap:** `new Array(3).some(() => true)` → `false` (all holes).
> - **Family:** map/filter/forEach skip holes; find/findIndex DO NOT.
