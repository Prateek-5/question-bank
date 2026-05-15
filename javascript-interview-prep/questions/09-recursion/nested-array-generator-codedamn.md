# Generator yielding leaves of a nested array (inorder)

## Source
- codedamn "Nested Array Inorder Traversal Generator": https://codedamn.com/problem/tfvPxjt4OJyqSruK5bNav
- Conceptually identical to LeetCode #2649 "Nested Array Generator".

## Why this question matters in interviews
This is a **two-for-one** question: it tests recursion comfort AND your knowledge of **generators** (`function*`, `yield`, `yield*`). It's the cleanest possible demonstration of why generators exist — three lines of code lazily produce an arbitrarily deep traversal that you can drive with `for ... of`, consume one value at a time, or stop early. Senior JS engineers are expected to reach for `yield*` instinctively here. As a backend engineer you'll see this when streaming results from a recursive store-walk (filesystem, S3 prefixes, recursive DB CTEs) without materializing the whole tree in memory.

## Concepts involved

### Syntax to lock in
```js
function* inorder(arr) {
  for (const item of arr) {
    if (Array.isArray(item)) {
      yield* inorder(item);   // delegate to the inner generator — the magic
    } else {
      yield item;
    }
  }
}

// Drive it:
for (const x of inorder([1, [2, [3, 4]], 5])) console.log(x);
// 1, 2, 3, 4, 5
```

### Runtime / engine behavior
- `function*` returns a **generator object** when called. The body doesn't execute until you call `.next()` or iterate.
- `yield` pauses execution and returns `{ value, done: false }`. The generator resumes on the next `.next()` call.
- `yield*` delegates to another iterable: it consumes that iterable's values and yields each one. **It is the recursion mechanic for generators.** Without `yield*`, you'd have to manually `for (const x of inner) yield x;` — same thing, slightly more typing.
- Generators are **iterable**: they have a `[Symbol.iterator]()` method that returns themselves, so `for ... of` works directly.
- **Memory**: generators don't materialize the flattened array. They hold one stack-of-iterators (one per `yield*` level) in memory. For a million-deep input you still hit the call stack limit (the generator function itself is recursive), but for a million-WIDE input with shallow nesting, memory stays O(d) where d is depth.
- `for ... of` on a generator calls `.next()` until `done: true`, then implicitly calls `.return()` if the loop breaks early — useful for cleanup.

### Edge cases (interview traps)
1. **Empty arrays / sub-arrays** — `inorder([])` yields nothing. `inorder([[], []])` yields nothing. Make sure your generator doesn't yield `undefined`.
2. **Deeply nested input** — `yield*` is recursive in spirit. Each `yield*` adds a frame, so a 10k-deep input still blows the call stack. Same V8-no-TCO trap as plain recursion.
3. **Non-array iterables inside the array** — strings, Maps, Sets. Does the spec say to recurse into them? Usually no — only `Array.isArray` qualifies. Match the prompt.
4. **`null` and `undefined`** — they're not arrays. Yield them as-is. Don't accidentally crash with `Array.isArray(null)` (it returns `false` — safe).
5. **Stopping early** — `for (const x of gen) { if (x > 5) break; }` works fine; the generator is paused mid-walk and GC'd later. Good for "find the first leaf matching X".
6. **Reusing a generator** — generators are one-shot. Once exhausted, `.next()` returns `{value: undefined, done: true}` forever. If you need multiple passes, recreate the generator each time.
7. **Manual `.next()` driving** — interviewer may ask "show me the values one at a time without `for...of`." `const g = inorder(arr); g.next();` repeatedly. Be ready.

## Brute force approach
"Flatten the array eagerly, then iterate." Defeats the whole purpose. You allocate O(n leaves) memory for a flat array you may not consume entirely. Tell the interviewer this and move on.

## Optimal approach
A 3-line `function*` with `yield*` to recurse. O(leaves) time amortized over full iteration, O(depth) memory for the implicit chain of paused generators.

## Solution (JavaScript)

```js
/**
 * Generator that yields the leaves of a nested array in inorder.
 * @param {Array} arr — arbitrarily nested array of primitives
 * @yields {*} each non-array leaf in left-to-right order
 */
function* inorder(arr) {
  for (const item of arr) {
    if (Array.isArray(item)) {
      yield* inorder(item);     // delegate — yields every value from the inner gen
    } else {
      yield item;
    }
  }
}

// --- Manual iterator-protocol equivalent (no generator sugar) ---
// Demonstrates what the runtime does for you. Useful if the interviewer asks
// "implement this without `function*`."
function inorderIter(arr) {
  // Explicit stack: each frame is { items, index }
  const stack = [{ items: arr, index: 0 }];

  return {
    [Symbol.iterator]() { return this; },
    next() {
      while (stack.length) {
        const top = stack[stack.length - 1];
        if (top.index >= top.items.length) {
          stack.pop();
          continue;
        }
        const item = top.items[top.index++];
        if (Array.isArray(item)) {
          stack.push({ items: item, index: 0 });
        } else {
          return { value: item, done: false };
        }
      }
      return { value: undefined, done: true };
    },
  };
}
```

## Step-by-step dry run

Input: `[1, [2, [3, 4]], 5]`.

Drive: `for (const x of inorder(arr)) console.log(x);`

Generator execution trace:
1. Enter `inorder([1, [2, [3, 4]], 5])`. Loop. item=`1`. Not array → `yield 1`. **Pause.** Consumer logs `1`, calls `.next()`.
2. Resume. item=`[2, [3, 4]]`. Array → `yield* inorder([2, [3, 4]])`. Delegation begins.
   - Enter inner gen. item=`2`. Not array → `yield 2`. **Pause.** Consumer logs `2`, calls `.next()`.
   - Resume. item=`[3, 4]`. Array → `yield* inorder([3, 4])`.
     - Enter innermost gen. item=`3`. → `yield 3`. **Pause.** Log `3`.
     - Resume. item=`4`. → `yield 4`. **Pause.** Log `4`.
     - Resume. Loop exits. Generator returns `{done: true}`.
   - Inner `yield*` finishes. Loop continues in inner gen. Loop exits. Returns `{done: true}`.
3. Outer `yield*` finishes. Loop continues. item=`5`. → `yield 5`. **Pause.** Log `5`.
4. Resume. Loop exits. Outer gen returns `{done: true}`. `for...of` terminates.

Final output: `1 2 3 4 5`.

Notice: at any pause point, the only state in memory is the chain of paused generators (one per nesting level) and the current item. **No intermediate flat array allocated.**

## Important takeaways

**Syntax to memorize**
- `function* name() { ... yield x; ... yield* iter; ... }` — the three operators.
- `yield*` delegates to **any iterable** (generator, array, Set, Map, string, custom iterator). It is the generator's recursion primitive.
- Manual iterator protocol: `{ [Symbol.iterator]() { return this; }, next() { return { value, done }; } }`.

**Patterns to reuse**
- "Recursive walk via `yield*`" — same shape for tree traversal: `yield* walk(node.left); yield node.value; yield* walk(node.right);` (BST inorder).
- "Lazy producer + early termination" — generators pair beautifully with `break` and `take(n)` / `find` style consumers.
- "Generator as stream" — many Node libraries (e.g. `readline`) expose async iterators; the same `for await ... of` consumer pattern applies.

**Common mistakes**
- Writing `yield inorder(item)` instead of `yield* inorder(item)` — yields the **generator object**, not its values. Output becomes `[1, <Generator>, 5]`.
- Forgetting that generators are one-shot. Re-iterating an exhausted generator yields nothing.
- Trying to `return` a value from a generator and expecting `for...of` to surface it. `for...of` ignores the final `{value, done: true}` value. Use `.next()` manually if you care.
- Recursing on strings: `Array.isArray('abc')` is `false`, good. But `typeof 'abc' === 'object'` would be `false` too — be precise; use `Array.isArray`.
- Believing generators avoid stack overflow. They don't — `yield*` adds a JS stack frame per level. Deeply nested input still RangeErrors.

**Related questions**
- LeetCode "Nested Array Generator" — same problem with class-based API (see `nested-array-generator-leetcode.md`).
- Tree BFS/DFS generator — generalizes to non-array trees.
- Infinite generators: `function* naturals() { let n = 1; while (true) yield n++; }`. Drive with `take(n)`.
- Async generators: `async function*` + `for await ... of` for paginated APIs.

## Variants

1. **Generator on Array.prototype** — `Array.prototype.values()` already exists; add `Array.prototype.deepValues()` returning this generator. Mutating built-in prototypes is rude but interviewers like to ask.

2. **Class-based iterator (no generator syntax)** — see `nested-array-generator-leetcode.md`. The LeetCode variant typically requires a class with `next()` / `hasNext()`.

3. **Inorder + path** — yield `{value, path: [i, j, k]}` so the consumer knows where each leaf came from. Useful for diff/patch operations on nested config.

4. **Filter + map fused in** — `function* inorderMap(arr, fn) { for (const item of arr) Array.isArray(item) ? yield* inorderMap(item, fn) : yield fn(item); }`. Lazy `map` over nested structure.

5. **Two-way iteration** — yield values both forward and backward. Requires materializing or running the recursion twice. Trade-off discussion.

## Revision notes

> **Nested-array generator — 60 second recap**
> - `function* gen(arr) { for (const x of arr) Array.isArray(x) ? yield* gen(x) : yield x; }`
> - `yield*` delegates to any iterable — it is the generator recursion primitive.
> - Lazy: no intermediate flat array. Consumer pulls one value at a time.
> - **Trap:** `yield gen(item)` (yields the generator object) vs `yield* gen(item)` (yields its values).
> - Generators are one-shot. Recreate to re-iterate.
> - Stack depth = nesting depth — V8 has no TCO, so deeply nested input still RangeErrors.
> - Same recipe drives tree DFS, paginated async iterators, infinite sequences.
