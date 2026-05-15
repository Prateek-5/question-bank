# Implement `flat(arr, depth)` — recursive AND iterative

## Source
- codedamn "Flatten Deeply Nested Arrays" lab: https://codedamn.com/problem/nM6u_iLTYEQxUl_yFC890
- LeetCode #2625 "Flatten Deeply Nested Array".
- Native: `Array.prototype.flat(depth)` (ES2019).

## Why this question matters in interviews
This is the **mid-tier** flatten question — interviewers ask it after the single-level warm-up to test whether you can (a) generalize, (b) reason about call stack depth, and (c) ship a production-safe iterative variant. A candidate who only writes the recursive version and shrugs about deep input gets a "junior" sticker. A candidate who proactively offers the iterative stack-based version and explains **V8 doesn't optimize tail calls** signals senior maturity. Practical use: parsing arbitrarily-nested JSON trees, flattening recursive RPC payloads, normalizing nested CSV exports.

## Concepts involved

### Syntax to lock in
```js
[1, [2, [3, [4]]]].flat(1);         // [1, 2, [3, [4]]]
[1, [2, [3, [4]]]].flat(2);         // [1, 2, 3, [4]]
[1, [2, [3, [4]]]].flat(Infinity);  // [1, 2, 3, 4]
```

```js
// Recursive shell — the elegant version
function flat(arr, depth = 1) {
  return depth > 0
    ? arr.reduce((acc, x) =>
        acc.concat(Array.isArray(x) ? flat(x, depth - 1) : x), [])
    : arr.slice();
}
```

### Runtime / engine behavior
- **Recursive version uses O(d) call stack frames** where d = min(input nesting depth, depth parameter). V8 throws `RangeError: Maximum call stack size exceeded` past ~10-15k frames.
- **V8 does NOT do tail-call optimization.** It was specced in ES2015 but only Safari/JSC actually ships it. Node, Chrome, Firefox all run frame-by-frame. So writing your recursion "tail-style" buys you nothing on the server.
- **Iterative version uses heap memory** (a JS array as the stack) — heap is much bigger than the call stack. You can flatten a million-deep array safely.
- `Array.isArray` is preferred over `instanceof Array` (cross-realm safe).
- `arr.reduce(...).concat(...)` allocates a new array per element → O(n²). Push-loop is O(n).

### Edge cases (interview traps)
1. **`depth = 0`** — return shallow copy with no flattening. Don't return the input by reference.
2. **`depth = Infinity`** — full recursive flatten. `depth - 1` against Infinity stays Infinity (no decrement). That's fine; recursion still terminates because eventually you hit non-arrays.
3. **Negative depth** — native treats as 0. Coerce: `depth = Math.max(0, depth)`.
4. **Non-integer depth** — native floors it. `flat([], 1.9)` behaves like `flat([], 1)`. Coerce: `depth = Math.floor(depth)`.
5. **Sparse arrays / holes** — native skips. Skip with `if (i in arr)`.
6. **Cycles** — input arrays don't usually self-reference, but if they do, recursion stack-overflows. Mention this if asked.
7. **Top-level non-array argument** — `flat(5, 1)` would crash. Validate or coerce.
8. **Very deep input + `Infinity`** — the recursive version dies. **You must offer the iterative variant.**

## Brute force approach
"Run single-level flatten in a loop until no array remains." Works but redoes work — each pass scans the entire current array. O(n × maxDepth) time, painful for `Infinity`. Use it as a stepping-stone in interview if you're stuck, then move on.

## Optimal approach
Two solutions side by side:
- **Recursive** — elegant, mirrors the data shape, but stack-bounded. Use for shallow input.
- **Iterative with explicit stack** — push `[item, depthRemaining]` pairs. Pop, decide, push children back. Same Big-O; safe for arbitrary depth. **This is what you ship to production.**

Both are O(total leaves) time. Recursive is O(d) stack. Iterative is O(n) heap.

## Solution (JavaScript)

```js
/**
 * Recursive — elegant, but bounded by V8 call stack.
 */
function flat(arr, depth = 1) {
  depth = Math.max(0, Math.floor(depth));
  if (depth === 0) return arr.slice();

  const out = [];
  for (let i = 0; i < arr.length; i++) {
    if (!(i in arr)) continue;          // match native: skip holes
    const item = arr[i];
    if (Array.isArray(item)) {
      // Recursive case — depth budget shrinks
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
 * Iterative — production-safe, no call stack growth.
 * Uses an explicit stack of [item, depthRemaining].
 */
function flatIterative(arr, depth = 1) {
  depth = Math.max(0, Math.floor(depth));
  const out = [];
  // Seed: reverse so popping yields left-to-right order
  const stack = [];
  for (let i = arr.length - 1; i >= 0; i--) {
    if (i in arr) stack.push([arr[i], depth]);
  }
  while (stack.length) {
    const [item, d] = stack.pop();
    if (Array.isArray(item) && d > 0) {
      // Push children back (reverse so output stays left-to-right)
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

Input: `flatIterative([1, [2, [3, [4]]]], 2)`.

Stack notation: `[item, depthRemaining]`. Top of stack is rightmost.

- Seed (reversed): `stack = [[[2,[3,[4]]], 2], [1, 2]]` ← top
- Pop `[1, 2]` → not array → `out=[1]`
- Pop `[[2,[3,[4]]], 2]` → array, d=2 > 0 → push children reversed with d=1
  - `stack = [[[3,[4]], 1], [2, 1]]` ← top
- Pop `[2, 1]` → not array → `out=[1, 2]`
- Pop `[[3,[4]], 1]` → array, d=1 > 0 → push children reversed with d=0
  - `stack = [[[4], 0], [3, 0]]` ← top
- Pop `[3, 0]` → not array → `out=[1, 2, 3]`
- Pop `[[4], 0]` → array BUT d=0 → push as-is → `out=[1, 2, 3, [4]]`
- Stack empty.

Return `[1, 2, 3, [4]]`. Matches `[1, [2, [3, [4]]]].flat(2)`.

The recursive version produces the same output with peak call stack depth of 3 frames; here the JS engine stack stays at 1 frame regardless of input depth.

## Important takeaways

**Syntax to memorize**
- Base case: `!Array.isArray(item) || depth === 0` → push item.
- Recursive case: `Array.isArray(item) && depth > 0` → recurse with `depth - 1`.
- Iterative recipe: stack of `[item, depthRemaining]`, reverse children when pushing to maintain order.
- Coerce depth: `Math.max(0, Math.floor(depth))`.

**Patterns to reuse**
- "Recursion with a shrinking depth budget" is the same skeleton as tree DFS with a maxDepth limit, JSON stringify with a recursion guard, retry-with-max-attempts.
- "Explicit `[node, state]` stack" is the universal recursive-to-iterative conversion. You'll use it for tree DFS, deep clone, AST walks.
- Reversed-children push trick: enqueue children in reverse order so popping yields them in original order. Same trick in tree iterative DFS.

**Common mistakes**
- Only writing the recursive version and not knowing it'll explode on deep input. Always mention V8's lack of TCO unprompted.
- Returning `arr` directly when `depth === 0` — caller can mutate your input. Return `arr.slice()`.
- Using `arr.reduce((a, b) => a.concat(...), [])` — clean but O(n²) due to concat re-allocation.
- Forgetting to floor / clamp depth. `flat([], -1)` shouldn't recurse forever.
- Pushing children in forward order in iterative version → output comes out reversed. Mistake-debug: always test with `[1, [2, 3]]` and check whether you get `[1, 2, 3]` or `[1, 3, 2]`.

**Related questions**
- Single-level flatten (`flat(arr, 1)` — see `flatten-array-simple.md`).
- Full recursive flatten (`flat(arr, Infinity)` — see `flatten-deeply-nested-array.md`).
- Generator-based flatten (see `nested-array-generator-*.md`) — lazy, zero intermediate alloc.
- Polyfill `Array.prototype.flat` (use this exact algorithm but `this`-bound).

## Variants

1. **Polyfill on Array.prototype** — Same logic but `function flat(depth = 1) { ... this ... }` and `Array.prototype.flat = flat`. Be defensive: check `if (!Array.prototype.flat)` so you don't clobber native.

2. **flatMap** — `arr.flatMap(fn)` is `arr.map(fn).flat(1)` but single-pass. Tests whether you can fuse two operations.

3. **Async flatten** — items may be Promises that resolve to arrays. `await` each, then flatten. Tests interaction of recursion with async.

4. **Mutate-in-place flatten** — flatten without allocating. Two-pointer trick, messy but interviewers like to push for it once they've seen the clean version.

## Revision notes

> **flat(arr, depth) — 60 second recap**
> - Two implementations: recursive (elegant, stack-bounded) and iterative-with-stack (production-safe).
> - **V8 has no TCO** — for adversarial or unbounded depth, ship the iterative version.
> - Base case: not-array OR depth ≤ 0 → push. Recursive case: array AND depth > 0 → recurse with `depth - 1`.
> - Iterative stack frames are `[item, depthRemaining]`. Reverse children on push to keep output order.
> - Coerce depth: `Math.max(0, Math.floor(depth))`.
> - Match native: skip holes (`if (i in arr)`), return shallow copy on `depth = 0`.
> - O(n leaves) time. Space: O(d) call stack OR O(n) heap stack.
