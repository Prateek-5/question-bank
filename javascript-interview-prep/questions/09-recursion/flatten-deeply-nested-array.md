# Implement `flat(arr, depth)` — flatten deeply nested array up to `depth`

## Source
- LeetCode #2625 "Flatten Deeply Nested Array": https://leetcode.com/problems/flatten-deeply-nested-array/
- Mirror of codedamn "Flatten Deeply Nested Arrays" lab.
- Native counterpart: `Array.prototype.flat(depth)` (ES2019).

## Why this question matters in interviews
This is the single most common recursion warm-up at JS interviews. In ~15 lines you have to demonstrate four things at once: (1) a clean **base case / recursive case** split, (2) awareness that **V8 does NOT optimize tail calls** so deep recursion will blow the call stack, (3) the difference between `Array.isArray(x)` and `typeof x === 'object'`, and (4) you can write an **iterative variant with an explicit stack** when production safety matters. As a backend engineer you'll hit this when normalizing nested JSON from third-party APIs, MongoDB aggregation outputs, or recursive config trees.

## Concepts involved

### Syntax to lock in
```js
// Native — what we're re-implementing
[1, [2, [3, [4]]]].flat();        // [1, 2, [3, [4]]]   default depth = 1
[1, [2, [3, [4]]]].flat(2);       // [1, 2, 3, [4]]
[1, [2, [3, [4]]]].flat(Infinity); // [1, 2, 3, 4]
```

```js
// Recursion skeleton
function flat(arr, depth = 1) {
  const out = [];
  for (const item of arr) {
    if (Array.isArray(item) && depth > 0) {
      out.push(...flat(item, depth - 1));   // recursive case
    } else {
      out.push(item);                       // base case
    }
  }
  return out;
}
```

### Runtime / engine behavior
- **Call stack depth = nesting depth** of the input (not array length). V8's default stack ~10,000-15,000 frames. A 50,000-deep `[[[[...]]]]` blows up with `RangeError: Maximum call stack size exceeded`.
- **No TCO in V8.** Even if you write tail-recursive code, V8/Node will not optimize it. Only Safari's JSC optimizes proper tail calls. So "I'll just write it recursively" is wrong for adversarial input — use the iterative stack version.
- `Array.isArray` is the safe check. `instanceof Array` fails across iframes / realms. `typeof [] === 'object'` is useless (also matches `{}` and `null`).
- Spread `out.push(...flat(...))` creates an intermediate array per recursive call. For huge inputs prefer `for (const x of flat(...)) out.push(x)` or mutate in place.

### Edge cases (interview traps)
1. **`depth = 0`** — should return a shallow copy with **no flattening**. Many candidates always recurse one level.
2. **`depth = Infinity`** — full flatten. Make sure the recursive case keeps recursing (`depth - 1` stays > 0 against Infinity).
3. **Sparse arrays** (holes): `[1, , 3].flat()` returns `[1, 3]`. Native `flat` skips holes. If you use `for...of` you'll skip them too; if you use `for (let i=0; i<arr.length; i++)` you have to `if (i in arr)` to mimic native.
4. **Non-array iterables** — strings, Sets, Maps. `Array.isArray('ab')` is `false`, so strings stay intact. Good — match native behavior.
5. **Negative depth** — native treats it as 0. Don't recurse.
6. **`null` / `undefined` items** — they're not arrays, so they pass through as-is. Don't crash.
7. **Stack overflow on deep input** — switch to iterative with explicit stack.
8. **Mutating the input** — don't. Build a new array.

## Brute force approach
"Loop, and if I see an array, slice-and-concat it into the current array, and start over." This rescans the entire array on every found nested element → O(n²) or worse, and is painful to write correctly. Don't go here.

## Optimal approach
Walk each item. If it's an array AND depth budget remains, recurse with `depth - 1`. Otherwise push as-is. O(n) time over total leaves, O(d) stack space where d = nesting depth. For unbounded depth, switch to an **explicit stack** to keep call stack flat — same Big-O, but won't blow the engine stack.

## Solution (JavaScript)

```js
/**
 * Flatten a nested array up to `depth` levels.
 * @param {Array} arr
 * @param {number} [depth=1] — use Infinity for full flatten
 * @returns {Array}
 */
function flat(arr, depth = 1) {
  const out = [];
  for (let i = 0; i < arr.length; i++) {
    if (!(i in arr)) continue;          // skip holes like native flat
    const item = arr[i];
    if (Array.isArray(item) && depth > 0) {
      // Recursive case — depth budget shrinks by one
      const inner = flat(item, depth - 1);
      for (const x of inner) out.push(x);
    } else {
      // Base case
      out.push(item);
    }
  }
  return out;
}

/**
 * Iterative variant — safe for arbitrarily deep input.
 * Uses an explicit stack of [array, depth] frames so call stack stays at 1.
 */
function flatIterative(arr, depth = 1) {
  const out = [];
  // Push pairs of [item, remainingDepth]; reverse so order is preserved when we pop.
  const stack = arr.map((item) => [item, depth]).reverse();
  while (stack.length) {
    const [item, d] = stack.pop();
    if (Array.isArray(item) && d > 0) {
      // Push children back onto the stack with depth-1
      for (let i = item.length - 1; i >= 0; i--) {
        if (i in item) stack.push([item[i], d - 1]);
      }
    } else {
      out.push(item);
    }
  }
  return out;
}
```

## Step-by-step dry run

Input:
```js
flat([1, [2, [3, [4, [5]]]]], 2);
```

Recursive trace (depth budget shown):
- `flat([1, [2, [3, [4, [5]]]]], 2)` — start, `out=[]`
  - `i=0`, item=`1` → not array → `out=[1]`
  - `i=1`, item=`[2, [3, [4, [5]]]]` → array, depth=2>0 → recurse with depth=1
    - `flat([2, [3, [4, [5]]]], 1)` → `out₁=[]`
      - item=`2` → `out₁=[2]`
      - item=`[3, [4, [5]]]` → array, depth=1>0 → recurse with depth=0
        - `flat([3, [4, [5]]], 0)` → `out₂=[]`
          - item=`3` → `out₂=[3]`
          - item=`[4, [5]]` → array BUT depth=0 → push as-is → `out₂=[3, [4, [5]]]`
        - return `[3, [4, [5]]]`
      - extend → `out₁=[2, 3, [4, [5]]]`
    - return `[2, 3, [4, [5]]]`
  - extend → `out=[1, 2, 3, [4, [5]]]`
- return `[1, 2, 3, [4, [5]]]`

Call stack depth at peak: 3 frames. For input nested 100,000 deep with `depth=Infinity`, the recursive version dies; the iterative version uses heap memory for the stack array and keeps the JS engine stack at 1.

## Important takeaways

**Syntax to memorize**
- Base case: not-an-array OR depth exhausted → `push(item)`.
- Recursive case: `Array.isArray(item) && depth > 0` → recurse with `depth - 1`.
- `Array.isArray` — not `instanceof Array`, not `typeof`.
- Skip holes with `if (i in arr) continue;` to match native `flat`.

**Patterns to reuse**
- "Recurse with a shrinking budget" → also seen in tree traversal with max depth, JSON serializer with cycle guard counter, retry with backoff.
- "Explicit stack of `[node, state]` frames" is the universal recipe to convert any recursive walk into an iterative one. Reuse it for tree DFS, deep clone, JSON stringify.

**Common mistakes**
- Using `typeof item === 'object'` — matches `null` and plain objects, breaks the algorithm.
- Recursing without decrementing depth → infinite recursion for cyclic-ish structures (though arrays in JS rarely cycle, you'd hang on `Infinity` mistake).
- Forgetting `depth = 0` should be a **shallow copy**, not the input. Some candidates `return arr` and mutate caller's array later.
- Writing `out = out.concat(flat(item, ...))` instead of mutating `out` — works, but allocates O(n) intermediate arrays. Push-spread or for-loop is cheaper.
- Claiming the recursive version is fine for production. **It is not.** Mention V8's lack of TCO and offer the iterative variant unprompted.

**Related questions**
- `flatten(arr)` — fully flatten (this with `depth = Infinity`).
- `flattenSingleLevel(arr)` — only one level (this with `depth = 1`).
- Generator version that yields leaves one at a time (lazy, O(1) extra space if consumer pulls).

## Variants

1. **Mutate in place** — "Flatten without allocating a new array." Forces a Floyd-style two-pointer walk; messy, but interviewers love asking.

2. **Flatten objects, not just arrays** — `{ a: { b: 1, c: { d: 2 } } }` → `{ 'a.b': 1, 'a.c.d': 2 }`. Same recursion shape but keyed paths.

3. **Generator-based lazy flatten** — `function* flat(arr) { for (const x of arr) Array.isArray(x) ? yield* flat(x) : yield x; }`. See the `nested-array-generator-*` problems in this folder.

4. **Type-aware flatten** — strings stay strings, but iterate over Sets. Tests whether you know `Array.isArray` excludes Sets/strings/Maps.

## Revision notes

> **flat(arr, depth) — 60 second recap**
> - Base: not-array OR `depth <= 0` → push as-is.
> - Recursive: `Array.isArray && depth > 0` → recurse with `depth - 1`.
> - Use `Array.isArray`, not `typeof` or `instanceof`.
> - **V8 has no TCO** — recursive blows up for deeply nested input. Default to the iterative explicit-stack version in production.
> - Iterative recipe: stack of `[item, depthRemaining]`, reverse children when pushing to preserve order.
> - Match native: skip holes (`if (i in arr)`), `depth=0` = shallow copy, `depth=Infinity` = full flatten.
> - Time O(n leaves), space O(depth) for recursion / O(n) for iterative stack.
