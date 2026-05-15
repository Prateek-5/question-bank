# Polyfill `Array.prototype.find` and `Array.prototype.findIndex`

## Source
- Canonical ES6 polyfill interview problem (BFE.dev #46, GreatFrontEnd, codedamn).
- MDN: [Array.prototype.find](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/find), [Array.prototype.findIndex](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/findIndex).
- ECMAScript spec: https://tc39.es/ecma262/#sec-array.prototype.find

## Why this question matters in interviews
`find` / `findIndex` look like clones of `some` / `every` but **diverge on one spec rule** that interviewers love: they do **NOT skip holes**. They iterate every index including missing ones and call the predicate with `undefined`. This is a deliberate spec choice (ES6 cleanup) that catches even mid-level candidates off guard. The question tests: do you know the difference between "ES5 hole-skipping iterators" and "ES6+ non-skipping iterators"? Backend candidates often dismiss this as trivia until they realize `find` and `some` produce different results on sparse arrays — and they've shipped a bug because of it.

## Concepts involved

### Syntax to lock in
```js
// find — returns the first ELEMENT that passes predicate
[1, 2, 3].find(x => x > 1);          // 2
[1, 2, 3].find(x => x > 99);          // undefined

// findIndex — returns the first INDEX that passes predicate
[1, 2, 3].findIndex(x => x > 1);     // 1
[1, 2, 3].findIndex(x => x > 99);    // -1
```

### Runtime / engine behavior
- Iterate `0` to `length - 1`, short-circuit on first truthy predicate.
- **No hole-skipping.** Predicate is called with `undefined` for missing indices. This is the headline difference vs `some`/`every`/`map`/`filter`.
- `length` is snapshotted once at start.
- `thisArg` supported (second param).
- `find` returns the **element** (or `undefined` if none); `findIndex` returns the **index** (or `-1` if none).
- ES2023 added `findLast` / `findLastIndex` (same semantics, reverse iteration).

### Edge cases (the interview traps)
1. **Holes are visited** — `[,,,3].find(x => true)` returns `undefined` (the first hole, called as `undefined`, satisfies `true`). This is the canonical interview trap.
2. **Distinguishing "not found" from "found undefined"** — `find` returning `undefined` is ambiguous; that's why `findIndex` exists. If you need to know whether the element exists, use `findIndex !== -1`.
3. **Empty array** — `[].find()` → `undefined`; `[].findIndex()` → `-1`. No vacuous-truth twist (unlike `every`).
4. **`thisArg` is the second arg** — same as `some`/`every`.
5. **Predicate signature** — `(element, index, array)`, three args.
6. **Mutation during iteration** — length is snapshotted, but already-passed indices reflect mutations (per spec). Don't mutate.
7. **Strict equality NOT used** — these are predicate-driven, not value-driven (unlike `indexOf` which uses `===`).

## Brute force approach
Some candidates reach for `arr.filter(fn)[0]` for `find`. Three problems:
- No short-circuit — full pass even after match.
- O(n) memory for intermediate array.
- `filter` **skips holes**, so behavior diverges from native `find` on sparse arrays.

Avoid this. The polyfill must be a hand-written loop.

## Optimal approach
For loop from `0` to `length - 1`. No `i in this` check — visit every index. Call predicate with `(O[i], i, O)` (where `O[i]` is `undefined` for holes). Short-circuit on truthy result: return `O[i]` from `find`, `i` from `findIndex`. Fall through with `undefined` / `-1`.

O(n) time, O(1) space.

## Solution (JavaScript)

```js
// ---- find ----
Array.prototype.myFind = function (predicate, thisArg) {
  if (this == null) throw new TypeError('myFind called on null or undefined');
  if (typeof predicate !== 'function') {
    throw new TypeError(`${predicate} is not a function`);
  }

  const O = Object(this);
  const len = O.length >>> 0;

  for (let i = 0; i < len; i++) {
    // NOTE: no `i in O` check — find visits holes
    const value = O[i];
    if (predicate.call(thisArg, value, i, O)) {
      return value;
    }
  }
  return undefined;
};

// ---- findIndex ----
Array.prototype.myFindIndex = function (predicate, thisArg) {
  if (this == null) throw new TypeError('myFindIndex called on null or undefined');
  if (typeof predicate !== 'function') {
    throw new TypeError(`${predicate} is not a function`);
  }

  const O = Object(this);
  const len = O.length >>> 0;

  for (let i = 0; i < len; i++) {
    // NOTE: no `i in O` check
    if (predicate.call(thisArg, O[i], i, O)) {
      return i;
    }
  }
  return -1;
};
```

## Step-by-step dry run

Input 1 — normal case:
```js
const users = [{ id: 1 }, { id: 2 }, { id: 3 }];
users.myFind(u => u.id === 2);       // → { id: 2 }
users.myFindIndex(u => u.id === 2);  // → 1
```

Trace:
- `len = 3`. `i=0`: predicate(`{id:1}`, 0) → false. `i=1`: predicate(`{id:2}`, 1) → true → return `{id:2}` (or `1` for findIndex).

Input 2 — the sparse-array gotcha:
```js
const sparse = [, , 3];   // holes at 0 and 1
sparse.myFind(v => true);       // → undefined (the first hole)
sparse.myFindIndex(v => true);  // → 0
```

Compare with `some`:
```js
sparse.mySome(v => true);   // → true (skips holes, hits the 3)
```

Same predicate, opposite-feeling results. **This is the diagnostic question** on this polyfill.

Input 3 — not-found:
```js
[1, 2, 3].myFind(x => x > 99);       // undefined
[1, 2, 3].myFindIndex(x => x > 99);  // -1
```

## Important takeaways

**Syntax to memorize**
- `O = Object(this)`, `len = O.length >>> 0` — boilerplate.
- **No `i in O` check** — this is the differentiator.
- Return value: element for `find`, index for `findIndex`.
- Fallback: `undefined` for `find`, `-1` for `findIndex`.

**Patterns to reuse**
- The "ES6 iterator family" (find / findIndex / fill / copyWithin / includes) does NOT skip holes — they treat sparse slots as `undefined`. This was a deliberate ES6 cleanup.
- The "ES5 iterator family" (forEach / map / filter / some / every / reduce) DOES skip holes — legacy compatibility.
- When asked "what's the difference between `some` and `find`?", the answer is: short-circuit return semantics (boolean vs element) AND hole-skipping (yes vs no).

**Common mistakes**
- Adding `i in O` — turns your `find` into `some` semantically. Fails the sparse-array spec test.
- Returning `null` instead of `undefined` for not-found — wrong fallback.
- Returning `0` instead of `-1` from `findIndex` — fails the "did we find anything?" check (`0` is a valid index!).
- Using `===` instead of calling a predicate — that's `indexOf`, not `find`.

**Related questions**
- Polyfill `Array.prototype.some` / `every` (skip holes).
- Polyfill `Array.prototype.findLast` / `findLastIndex` (ES2023, reverse iteration).
- Polyfill `Array.prototype.indexOf` (uses `===`, not predicate; skips holes per ES5).
- `Array.prototype.includes` vs `indexOf` (includes uses SameValueZero, finds NaN).

## Variants

1. **findLast / findLastIndex** — "Now write the reverse-iteration versions." Trivial twist: loop `i = len - 1; i >= 0; i--`. Same no-hole-skip rule.

2. **findKey / findEntry for objects** — "What about for plain objects?" Pivot to `Object.entries(obj).find(([k, v]) => predicate(v, k, obj))`. Tests object iteration knowledge.

3. **Async find** — "Find the first element where an async predicate resolves truthy, short-circuiting." This is genuinely hard — Promise.all loses short-circuit; sequential `for...of` with `await` is correct but slow; the elegant answer uses an AbortController to race + cancel.

4. **find with default value** — "Add a third param `defaultValue` returned when no match." Easy to add but tests whether you can extend cleanly.

## Revision notes

> **find / findIndex — 60 second recap**
> - `find` → first matching ELEMENT or `undefined`.
> - `findIndex` → first matching INDEX or `-1`.
> - Short-circuit on first truthy predicate.
> - **DO NOT skip holes** — opposite of `some`/`every`/`map`/`filter`.
> - Predicate signature `(value, index, array)`, supports `thisArg`.
> - **Trap:** `[,,].find(() => true)` returns `undefined`, not the hole — but it DID call the predicate.
> - **Family:** ES6 iterators (find / findIndex / includes / fill) skip nothing. ES5 iterators (forEach / map / etc.) skip holes.
