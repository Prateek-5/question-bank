# Nested Iterator class — `next()` / `hasNext()` API over nested array

## Source
- LeetCode #2649 "Nested Array Generator": https://leetcode.com/problems/nested-array-generator/
- Classic Iterator-protocol companion to LeetCode #341 "Flatten Nested List Iterator".

## Why this question matters in interviews
This is the "OO interview" sibling of the `function*` version. The interviewer wants to see whether you can build the **Iterator Protocol by hand** — `next()` and `hasNext()` methods on a class, with internal state. It tests three things: (1) understanding that the iterator protocol is just `{ next(): {value, done} }` plus optional `[Symbol.iterator]`, (2) ability to convert a naturally recursive walk into stored state, and (3) awareness of the **lazy** vs **eager** trade-off. Backend parallels: building a paginated cursor over a B-tree, implementing a streaming reader over an LSM SST file, exposing a "next batch" API over a recursive query.

## Concepts involved

### Syntax to lock in
```js
// LeetCode API
class NestedIterator {
  constructor(nestedList) { /* setup */ }
  next() { /* return next leaf */ }
  hasNext() { /* return boolean */ }
}

const it = new NestedIterator([1, [2, [3, 4]], 5]);
while (it.hasNext()) console.log(it.next());  // 1 2 3 4 5
```

```js
// JS-native equivalent (Symbol.iterator) — same algorithm
class NestedIterator {
  constructor(nestedList) { /* ... */ }
  [Symbol.iterator]() { return this; }
  next() {
    if (!this.hasNext()) return { value: undefined, done: true };
    return { value: this._next(), done: false };
  }
  hasNext() { /* ... */ }
}
```

### Runtime / engine behavior
- The iterator must be **stateful between `next()` calls**. Unlike a generator (where state is implicit in the paused frame), here you carry the state explicitly as instance fields.
- **Two implementation styles:**
  - **Eager**: flatten the input in the constructor, then `next()` is just `O(1)` array indexing. Simple but uses O(n leaves) memory upfront.
  - **Lazy**: store a stack of iterators / positions, advance one step at a time. O(d) memory where d = nesting depth, but constructor is O(1).
- `hasNext()` is often called multiple times before `next()` — make it **idempotent**. A common idiom: `hasNext()` advances the stack to the next leaf, leaving it ready; `next()` consumes it.
- The "advance to next leaf" routine pops empty frames and pushes nested-array frames until the top of the stack is a primitive ready to consume.
- Generator-based shortcut: wrap a generator inside the class and call `.next()` on it. The class becomes a 5-line adapter. Mention this for bonus points — it shows you know both layers.

### Edge cases (interview traps)
1. **Empty input** — `new NestedIterator([])` then `hasNext()` should be `false`, not throw.
2. **All-empty nested** — `[[], [[]], []]` should also yield `false` from `hasNext()`. Requires `hasNext()` to drill through empties.
3. **Multiple `hasNext()` calls without `next()`** — must be idempotent. Don't advance position on `hasNext()`.
4. **Calling `next()` past the end** — LeetCode tests don't usually exercise this, but defensive code returns a sentinel or throws clearly.
5. **Deeply nested input** — eager flatten = call stack risk. Lazy stack-of-iterators = safe.
6. **Mixed nesting** — `[1, [2], 3, [[4]]]`. Make sure the algorithm handles arrays appearing at any position, not just trailing.
7. **Mutation during iteration** — out of spec; don't worry unless asked.

## Brute force approach
Eager flatten in the constructor, then index into a flat array with a cursor. Works, passes LeetCode tests, but loses the "lazy / streaming" point of the problem. If asked "why is this approach worse?", say: memory upfront, can't be used over an infinite-feeling generator, can't short-circuit.

## Optimal approach
**Lazy** iterator with an explicit stack of `{ items, index }` frames. `hasNext()` drains empty frames and dives into nested arrays until the top frame points at a primitive. `next()` returns that primitive and advances. O(1) amortized per `next()`, O(depth) memory.

## Solution (JavaScript)

```js
/**
 * LeetCode-style nested iterator.
 * Lazy: explicit stack of { items, index } frames.
 */
class NestedIterator {
  /**
   * @param {Array<*>} nestedList — arbitrarily nested array of primitives
   */
  constructor(nestedList) {
    // Each frame: { items: Array, index: number }
    this.stack = [{ items: nestedList, index: 0 }];
  }

  /**
   * Returns true if there's still a primitive leaf to yield.
   * Idempotent: safe to call multiple times in a row.
   * Side effect: advances the stack until the top frame is at a primitive
   * (so next() can read it in O(1)).
   */
  hasNext() {
    while (this.stack.length) {
      const top = this.stack[this.stack.length - 1];
      // Frame exhausted — pop it.
      if (top.index >= top.items.length) {
        this.stack.pop();
        continue;
      }
      const item = top.items[top.index];
      if (Array.isArray(item)) {
        // Dive in. Consume slot in parent first to avoid re-entry.
        top.index++;
        this.stack.push({ items: item, index: 0 });
      } else {
        // Top of stack is now sitting on a primitive — ready for next().
        return true;
      }
    }
    return false;
  }

  /**
   * Returns the next primitive leaf and advances.
   * Caller should have verified hasNext() first.
   * @returns {*} the next leaf value
   */
  next() {
    if (!this.hasNext()) return undefined;     // or: throw
    const top = this.stack[this.stack.length - 1];
    return top.items[top.index++];
  }

  // JS-native iteration sugar so `for ... of` works directly.
  [Symbol.iterator]() {
    return {
      next: () => this.hasNext()
        ? { value: this.next(), done: false }
        : { value: undefined, done: true },
    };
  }
}

/**
 * Generator-adapter alternative — shows mastery of both layers.
 * The class becomes a thin shim over a generator.
 */
class NestedIteratorGen {
  constructor(nestedList) {
    function* walk(arr) {
      for (const item of arr) {
        if (Array.isArray(item)) yield* walk(item);
        else yield item;
      }
    }
    this._gen = walk(nestedList);
    this._peeked = null;            // 1-slot lookahead so hasNext() is non-destructive
  }
  hasNext() {
    if (this._peeked !== null) return true;
    const { value, done } = this._gen.next();
    if (done) return false;
    this._peeked = { value };
    return true;
  }
  next() {
    if (this._peeked !== null) {
      const v = this._peeked.value;
      this._peeked = null;
      return v;
    }
    return this._gen.next().value;
  }
}
```

## Step-by-step dry run

Input: `new NestedIterator([1, [2, [3, 4]], 5])`.

Initial: `stack = [{items: [1,[2,[3,4]],5], index: 0}]`.

1. `hasNext()`:
   - Top: index 0, items[0]=`1` (primitive) → return `true`. Stack unchanged.
2. `next()` → reads `1`, advances index to 1. Returns `1`. Stack: `[{items:[1,[2,[3,4]],5], index:1}]`.
3. `hasNext()`:
   - Top: items[1]=`[2,[3,4]]` (array) → bump parent index to 2, push frame. Stack: `[{...,index:2}, {items:[2,[3,4]],index:0}]`.
   - Top: items[0]=`2` (primitive) → return `true`.
4. `next()` → reads `2`, advances. Returns `2`. Stack top: `{items:[2,[3,4]],index:1}`.
5. `hasNext()`:
   - Top: items[1]=`[3,4]` (array) → bump parent to 2, push. Stack: `[{...idx2}, {idx2}, {items:[3,4],index:0}]`.
   - Top: items[0]=`3` (primitive) → `true`.
6. `next()` → `3`. Top frame index→1.
7. `hasNext()`:
   - Top: items[1]=`4` (primitive) → `true`.
8. `next()` → `4`. Top frame index→2.
9. `hasNext()`:
   - Top: index 2 >= length 2 → pop. Stack: `[{idx2}, {idx2}]`.
   - New top: index 2 >= length 2 → pop. Stack: `[{idx2}]`.
   - New top: items[2]=`5` (primitive) → `true`.
10. `next()` → `5`. Top frame index→3.
11. `hasNext()`:
    - Top: 3 >= 3 → pop. Stack empty.
    - Return `false`.

Output sequence: `1, 2, 3, 4, 5`. Total leaves yielded with O(1) amortized cost per call.

## Important takeaways

**Syntax to memorize**
- Iterator protocol: `next() → {value, done}`. LeetCode's API is `next()/hasNext()` — both styles are common.
- Eager-flatten constructor + cursor is the easy answer; explicit stack of frames is the lazy answer.
- `hasNext()` must be **idempotent**: multiple calls without intervening `next()` should yield the same answer.
- "Dive into nested array" idiom: increment parent's index FIRST, then push child. Prevents double-visiting.

**Patterns to reuse**
- "Stack of `{items, index}` frames" is the explicit conversion of any depth-first recursion into iterative form. Use it for AST walks, tree DFS, deep clone with depth limit.
- "Peek-buffer adapter" (1-slot lookahead) turns any `next()`-only iterator into a `hasNext()/peek()` iterator. Useful when wrapping native generators.
- The class-over-generator pattern (`NestedIteratorGen`) is the production way to expose iterator state with a richer API while keeping the algorithm declarative.

**Common mistakes**
- `hasNext()` advances the position even when called twice → `next()` skips values. Fix with idempotent dive logic OR with a peek buffer.
- Pushing the child frame before bumping the parent's index → on re-entry you re-visit the same nested array forever.
- Eager-flattening in the constructor and forgetting that it allocates O(n) memory upfront — fine for small inputs, awful for large or unknown-size streams.
- Forgetting to handle `[[], []]` style empty nesting — `hasNext()` should loop and drain those empty frames, not return `true` once and then crash in `next()`.
- Calling `Array.isArray` on `null` and worrying it'll crash — it won't, returns `false`. Cite this to look polished.

**Related questions**
- Generator version (`function*` + `yield*`) — see `nested-array-generator-codedamn.md`.
- LeetCode #341 "Flatten Nested List Iterator" — same algorithm, with `NestedInteger` interface.
- BST iterator with `next()/hasNext()` — same stack-of-frames pattern over a tree.
- Two-pointer merge of two iterators.

## Variants

1. **`peek()` method** — return next leaf without advancing. Implement with a 1-slot buffer.

2. **Bidirectional** — `prev()` as well. Requires storing visited values in an array (you've lost the laziness benefit).

3. **`takeWhile(pred)` / `skipWhile(pred)`** — typical functional combinators built on top of the basic iterator.

4. **Async version** — items themselves are Promises that resolve to nested arrays. `async next() { ... }`, drive with `for await ... of`.

5. **Pluggable predicate** — yield only leaves matching `pred`. Or yield arrays too (interview twist).

## Revision notes

> **NestedIterator (next/hasNext) — 60 second recap**
> - Iterator protocol: `next()` returns `{value, done}`; LeetCode wants explicit `next()` + `hasNext()`.
> - Lazy implementation: explicit stack of `{items, index}` frames.
> - `hasNext()` drains empty frames and dives into nested arrays until top frame is at a primitive. **Idempotent.**
> - `next()` reads the primitive at top frame and advances.
> - Dive idiom: bump parent index FIRST, then push child frame. Avoids re-entry.
> - O(1) amortized per call, O(depth) memory.
> - Bonus: wrap a `function*` generator + 1-slot peek buffer to make a 10-line implementation.
> - **Trap:** non-idempotent `hasNext()` skips values; eager flatten loses laziness.
