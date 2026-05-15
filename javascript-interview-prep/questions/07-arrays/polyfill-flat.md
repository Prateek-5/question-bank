# Polyfill `Array.prototype.flat(depth)`

## Source
- Canonical interview classic. Variants on LeetCode #2625 "Flatten Deeply Nested Array" — https://leetcode.com/problems/flatten-deeply-nested-array/
- codedamn labs: "Flatten Array", "Flatten Deeply Nested Arrays".
- MDN: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/flat

## Why this question matters in interviews
`flat` is **the** array problem interviewers reach for when they want to see if you understand **stack vs heap**, **recursion limits**, and **depth tracking**. The "wrong but works" answer is two lines of recursion. The "right" answer is iterative with an explicit work stack — because the recursive version blows the JS call stack on deeply nested arrays (think 10k levels deep, which happens with adversarial input or pathological data). The follow-up — "now do it with a depth parameter, defaulting to 1, with `Infinity` flattening fully" — tests whether you can carry per-item depth alongside each entry on the stack. Backend engineers see this in config trees, AST flattening, nested JSON normalization, and any place a recursive walk might hit `RangeError`.

## Concepts involved

### Spec signature
```js
arr.flat();              // depth defaults to 1
arr.flat(2);             // flatten two levels
arr.flat(Infinity);      // flatten completely
[1, [2, [3]]].flat(0);   // [1, [2, [3]]] — depth 0 is a clone (single level copy)
```

### Spec details
1. **`depth` default is `1`** — not `Infinity`. Constantly missed.
2. **`Infinity` flattens fully.** Use it as a sentinel; in the loop, compare with `>` (depth still decreases each level).
3. **Holes are removed.** `[1, , 2].flat()` → `[1, 2]`. This is *different* from `map`/`filter` — `flat` drops them entirely.
4. **Non-mutating.** Returns a new array. Source untouched.
5. **Only flattens arrays** — not array-likes, not iterables. `flat` checks `Array.isArray`. A nested `Set` or `arguments` object stays as-is.
6. **Result is dense.**

### Recursive (avoid in production)
```js
const flat = (arr, depth = 1) =>
  depth > 0
    ? arr.reduce((acc, v) =>
        acc.concat(Array.isArray(v) ? flat(v, depth - 1) : v), [])
    : arr.slice();
```
Pretty. Blows the stack on inputs like `[1, [2, [3, [4, ...]]]]` with 10k+ levels. Call frames cost ~100 bytes each; V8's default stack is ~1MB → roughly 10k frames before `RangeError`. **Don't ship this when depth might be unbounded.**

### Iterative (production-grade)
Use an explicit work stack of `[element, remainingDepth]` pairs. Walk the input from end to start, push each item with its depth onto a stack; pop and either push children (with `depth - 1`) or append to output. No recursion → no stack-overflow risk.

A cleaner two-stack variant (preferred for interview): seed `stack = [...arr]` with reverse order, but encode depth alongside. Below in the solution.

### Holes
`flat` is the one method where you actively want to drop holes. `Array.isArray(undefined)` is false, so a hole naturally falls into the "not an array, append it" branch. But you also have to **skip holes** before appending — the spec drops them entirely. Use `i in arr` to skip.

## Brute force approach
- Concat with `[].concat(...arr)` — only flattens one level, ignores depth, doesn't skip holes correctly.
- Recursive reduce (above) — correct semantics for small depth, but stack-overflows on deep input. Mention you know it, then upgrade.

## Optimal approach
Iterative with a work stack of `[node, depth]` pairs. Loop:
- Pop a `[node, d]` pair.
- If `Array.isArray(node) && d > 0`, push all of `node`'s entries onto the stack with `d - 1` (skip holes).
- Else, append `node` to the result.

To preserve order, walk the input back-to-front when seeding the stack (so the stack pops front-to-back). O(total elements). No recursion, constant stack depth in the JS sense.

## Solution (JavaScript)

```js
Object.defineProperty(Array.prototype, 'myFlat', {
  value: function (depth = 1) {
    // Coerce per spec: ToIntegerOrInfinity. Negative/NaN → 0.
    depth = Number(depth);
    if (Number.isNaN(depth)) depth = 0;
    if (depth < 0) depth = 0;

    const result = [];
    // Stack of [value, remainingDepth]. Seed in reverse so we pop in original order.
    const stack = [];
    const len = this.length >>> 0;
    for (let i = len - 1; i >= 0; i--) {
      if (i in this) stack.push([this[i], depth]);   // skip holes
    }

    while (stack.length > 0) {
      const [node, d] = stack.pop();
      if (Array.isArray(node) && d > 0) {
        const n = node.length >>> 0;
        for (let i = n - 1; i >= 0; i--) {
          if (i in node) stack.push([node[i], d - 1]);  // skip nested holes too
        }
      } else {
        result.push(node);
      }
    }
    return result;
  },
  writable: true,
  configurable: true,
  enumerable: false,
});
```

## Step-by-step dry run

Input:
```js
const arr = [1, [2, [3, [4]]], 5];
arr.myFlat(2);
```

Trace:
- `depth = 2`. Seed stack from `arr` in reverse:
  - push `[5, 2]`, `[[2, [3, [4]]], 2]`, `[1, 2]`. Stack top → bottom: `[[1,2], [[2,[3,[4]]],2], [5,2]]`.
- Pop `[1, 2]` → not array → `result = [1]`.
- Pop `[[2, [3, [4]]], 2]` → array, depth>0. Push entries reversed with `d=1`: `[[3,[4]], 1]`, `[2, 1]`.
- Pop `[2, 1]` → not array → `result = [1, 2]`.
- Pop `[[3, [4]], 1]` → array, depth>0. Push reversed with `d=0`: `[[4], 0]`, `[3, 0]`.
- Pop `[3, 0]` → not array → `result = [1, 2, 3]`.
- Pop `[[4], 0]` → array, **but depth=0** → not flattened. `result = [1, 2, 3, [4]]`.
- Pop `[5, 2]` → not array → `result = [1, 2, 3, [4], 5]`.
- Stack empty. Return `[1, 2, 3, [4], 5]`. Matches native `arr.flat(2)`.

Edge run — `Infinity`:
- `arr.myFlat(Infinity)` → every `d > 0` is true forever (since `Infinity - 1 === Infinity`). Result: `[1, 2, 3, 4, 5]`.

Edge run — depth default:
- `[1, [2, [3]]].myFlat()` → depth=1. Inner `[3]` stays as-is. Result: `[1, 2, [3]]`.

Edge run — holes:
- `[1, , 2, [3, , 4]].myFlat()` → seeding skips index 1; inside the nested array, also skips its hole. Result: `[1, 2, 3, 4]`.

Edge run — depth=0:
- `[1, [2]].myFlat(0)` → depth=0 means "no flattening, just clone." First pop: `[[2], 0]`, array but `d>0` false → appended as-is. Result: `[1, [2]]`. Equivalent to a shallow `slice`.

## Important takeaways

**Syntax to memorize**
- `Array.isArray(x)` — only reliable check, works across realms.
- `depth = 1` default; `Infinity` is fine to compare with `>` and `- 1`.
- Stack pair: `[node, remainingDepth]`. Push children with `depth - 1`.

**Patterns to reuse**
- **"Replace recursion with an explicit stack"** is a general technique for any tree/graph walk that might exceed JS's call-stack limit. Same pattern for deep clone, deep equality, JSON walkers, AST traversal.
- Seeding the stack in reverse so pop order matches array order is a classic iterative-DFS trick — burn it in.

**Common mistakes**
- Recursive reduce — fails on deeply nested input. Acceptable as a "first pass" if you announce the limitation; never as the final answer.
- Treating `depth=0` as "no-op return input directly" — it's actually a **shallow clone** (cloning is the whole point of `flat(0)`).
- Forgetting that holes are dropped, not preserved.
- Using `concat(...node)` inside the loop — spreads the array as args, which has the same blow-up risk as `Math.max(...arr)` on huge nested arrays. Stick with the explicit push loop.
- Missing the depth coercion: `flat('2')` → depth becomes 2 after `Number('2')`. `flat(NaN)` and `flat(-1)` → depth becomes 0 per spec.

**Related questions**
- `flatMap` — equivalent to `map` then `flat(1)`. Common immediate follow-up.
- Generator-based deep flatten — `function* flatten(arr) { for (const v of arr) yield* Array.isArray(v) ? flatten(v) : [v]; }`. Lazy, but recursive — same stack risk.
- Deep clone with cycle handling — different problem, same "iterative stack instead of recursion" insight.

## Variants

1. **`flat(Infinity)` shortcut** — interviewers may ask for "fully flatten only." Acceptable to skip the depth coercion and assume Infinity. Reduces code but breaks API parity.
2. **Generator flatten** — `function* flat(arr, depth=Infinity)`. Lazy: yields one leaf at a time. Pairs well with the recursion bucket. Caveat: still recursive (uses `yield*`); doesn't solve the stack problem.
3. **Custom predicate** — flatten only when `predicate(node)` returns true, otherwise treat as leaf. Useful for "flatten arrays but leave Sets / Maps / typed arrays intact."

## Revision notes

> **flat polyfill — 60 second recap**
> - Default `depth = 1`. `Infinity` for full flatten. `0` is a shallow clone.
> - Spec coercion: non-numeric → 0; negative → 0.
> - **Use an iterative stack** of `[node, remainingDepth]` pairs. Recursive `reduce/concat` blows the JS call stack on deep input (~10k frames).
> - Seed stack in **reverse** so pops preserve original order.
> - Only flatten `Array.isArray(node)` — other iterables stay as-is.
> - **Drop holes** (`flat` is unique here — `map`/`filter` skip but don't necessarily drop). Use `i in arr`.
> - Non-mutating; returns a fresh dense array.
> - Attach via `Object.defineProperty(..., { enumerable: false })`.
> - **Trap:** assuming default depth is `Infinity`. It's `1`.
> - **Trap:** recursive version is pretty but fragile — name-drop the iterative approach to win the round.
> - Family: `flatMap` = `map` then `flat(1)`.
