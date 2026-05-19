# Generator yielding leaves of nested array (inorder)

> **Difficulty:** Foundation-Medium   |   **Time:** ~10 min   |   **Prereqs:** [flatten-array-simple.md](./flatten-array-simple.md), [`06-streams/custom-iterator.md`](../06-streams/custom-iterator.md)
>
> **Source:** codedamn Lab. LeetCode #2649 (different API).

---

## 1. Problem statement

`function*` that yields each leaf of a nested array, recursively. Use `yield*` for delegation.

**Verification examples**

```js
function* inorder(arr) {
  for (const item of arr) {
    if (Array.isArray(item)) yield* inorder(item);
    else yield item;
  }
}

[...inorder([1, [2, [3, 4]], 5])];        // [1, 2, 3, 4, 5]
[...inorder([])];                          // []
[...inorder([[], [1, []]])];               // [1]
```

**Constraints**
- `yield*` delegates to inner generator.
- Lazy — values yielded on `.next()` not all at once.
- Recursion depth = nesting depth; V8 stack limits.
- Early break works via `for..of`.

---

## 2. Plain-English restatement

Lazy flatten: instead of building output array, yield each leaf as visited. Consumer can stop early.

---

## 3. Why this matters in interviews

Two-for-one: recursion + generators. `yield*` is the magic. Senior signal: reach for `yield*` instinctively.

---

## 4. Mental model

```
   function* inorder(arr):
     for item of arr:
       if Array.isArray(item):
         yield* inorder(item)       ← delegates; recursive
       else:
         yield item                  ← leaf
   
   yield* semantics:
     consumes another iterable; yields each of its values.
     Equivalent to: for (const x of inner) yield x.
   
   Lazy:
     Generator object returned by inorder(arr).
     Body doesn't run until .next() called.
     Each .next() resumes until next yield.
   
   Early break:
     for..of break → iterator.return() called → generator finally clause runs.
   
   Memory:
     One stack of iterators (one per yield* level).
     For deeply-nested input: V8 stack limit applies.
     For shallow-but-wide: constant memory.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What's the difference between `yield` and `yield*`?
> 2. When does the body of `function*` actually run?
> 3. Memory cost vs eager flatten?

---

## 6. Brute force — walked through

```js
function eagerFlatten(arr) {
  const out = [];
  for (const item of arr) {
    if (Array.isArray(item)) out.push(...eagerFlatten(item));
    else out.push(item);
  }
  return out;
}
// for (const x of eagerFlatten(arr)) ...
```

Materializes whole list; memory O(n). For huge inputs or early break, generator is better.

---

## 7. The unlocking insight

> **`function*` + `yield*` for clean recursive lazy traversal. Body runs on demand. Early break free via `for..of`.**

Three properties:

1. **`yield*` delegates** — clean recursion.
2. **Lazy** — body runs on demand.
3. **Early break** via for..of.

---

## 8. Solution (annotated)

```js
function* inorder(arr) {
  for (const item of arr) {
    if (Array.isArray(item)) {
      yield* inorder(item);                                                // step 1: delegate
    } else {
      yield item;                                                          // step 2: leaf
    }
  }
}

// Drive
for (const x of inorder([1, [2, [3, 4]], 5])) console.log(x);

// Iterative (no recursion — depth-safe)
function* inorderIter(arr) {
  const stack = [{ items: arr, index: 0 }];                                 // step 3: explicit stack
  while (stack.length) {
    const frame = stack[stack.length - 1];
    if (frame.index >= frame.items.length) {
      stack.pop();
      continue;
    }
    const item = frame.items[frame.index++];
    if (Array.isArray(item)) {
      stack.push({ items: item, index: 0 });
    } else {
      yield item;                                                          // step 4: yield leaf
    }
  }
}

// LeetCode #2649 — class with next/hasNext
class NestedIterator {
  constructor(nested) {
    this.iter = inorderIter(nested);                                       // step 5: delegate to generator
    this._buf = this.iter.next();
  }
  hasNext() { return !this._buf.done; }
  next() {
    const v = this._buf.value;
    this._buf = this.iter.next();
    return v;
  }
}
```

**Try it yourself**

```js
// Eager array
[...inorder([1, [2, [3, 4]], 5])];                            // [1, 2, 3, 4, 5]

// Early break
const gen = inorder([1, [2, [3, 4]], 5]);
let count = 0;
for (const x of gen) {
  console.log(x);
  if (++count === 3) break;                                    // stops after 3
}
// Generator's finally clause runs on break (cleanup).

// Find first match — no need to flatten whole tree
function findFirst(arr, pred) {
  for (const x of inorder(arr)) {
    if (pred(x)) return x;
  }
  return undefined;
}
findFirst([1, [2, [3, 4]], 5], x => x > 2);                   // 3 (no need to walk past 3)

// Class API (LeetCode #2649)
const it = new NestedIterator([1, [2, [3, 4]], 5]);
while (it.hasNext()) console.log(it.next());                  // 1 2 3 4 5

// Map/Set inside arrays — usually not recursed
[...inorder([1, new Set([2, 3]), 4])];                        // [1, Set{2,3}, 4]
// Use Symbol.iterator check to extend if needed.
```

---

## 9. Step-by-step dry run

```
inorder([1, [2, [3]], 4]):

Call: returns generator object G.
G.next() (first):
  Body starts. for (const item of arr).
  item=1: not array → yield 1.
  PAUSE. Return {value: 1, done: false}.

G.next() (second):
  Resume. for-loop next iter.
  item=[2, [3]]: array → yield* inorder([2, [3]]):
    Body of inner gen starts.
    item=2: yield 2.
    PAUSE. Outer yields {value: 2, done: false} (propagated).

G.next() (third):
  Resume inner generator.
  item=[3]: yield* inorder([3]):
    item=3: yield 3.
    PAUSE.
    {value: 3, done: false}.

G.next() (fourth):
  Resume innermost.
  innermost.next() → {done: true}. yield* loop ends.
  Back to middle gen.
  middle.next() → done.
  Back to outer.
  item=4: yield 4.
  PAUSE.
  {value: 4, done: false}.

G.next() (fifth):
  Outer loop ends. Return.
  {value: undefined, done: true}.

Generator object kept ~3-4 paused frames (one per yield* level).
For 100k-deep input: 100k paused frames → V8 stack? Actually call frames are popped on return; only the suspended frame at each level remains. Memory O(depth).
```

---

## 10. Common confusion + traps

1. **`yield` vs `yield*`** — yield one value vs delegate iterable.
2. **Body doesn't run** until `.next()` called.
3. **Calling generator function without `()`** — returns function, not gen.
4. **`for..of` swallows return value** of generator.
5. **Strings are iterable** — would `yield*` chars; usually not desired.
6. **Recursion depth** — V8 limit on deeply nested.
7. **Closure traps** — gen captures outer state.

---

## 11. Senior follow-ups & variants

### Variant 1 — Iterative stack
Depth-safe via explicit stack.

### Variant 2 — Class with next/hasNext (LeetCode #2649)
OO API over generator.

### Variant 3 — Tree generator (children array)
Same idea for tree nodes.

### Variant 4 — Async generator
For async leaves (streams).

### Variant 5 — `yield*` with custom iterables
Sets, Maps — depends on spec.

---

## 12. How to think aloud

> "Lazy nested array traversal: `function* inorder(arr) { for (const item of arr) { if (Array.isArray(item)) yield* inorder(item); else yield item; } }`. `yield*` delegates to another iterable — equivalent to manual `for (const x of inner) yield x` but cleaner; it's the recursion mechanic for generators. The generator body doesn't run when you call `inorder(arr)` — that returns a generator object; body runs lazily on `.next()`. Each `.next()` resumes execution until the next `yield`. Memory: one suspended frame per `yield*` level (O(depth)), not the materialized leaves. Early break: `for..of break` calls the generator's `return()`, runs `finally` clauses for cleanup. Iterative variant for depth safety: explicit stack of `{items, index}` frames; advance index per yield; push child arrays as nested frames. LeetCode #2649 wants a class with `next()` and `hasNext()` — wrap the generator: buffer next value, hasNext checks `!buf.done`. Trap: confusing `yield` and `yield*`; forgetting `()` to invoke; strings iterable (would yield chars); deep recursion blowing V8 stack."

---

## 13. 60-second revision

> - **`function*` + `yield*`** for lazy recursive.
> - **`yield*` delegates** another iterable.
> - **Body runs on `.next()`**, not on call.
> - **Memory O(depth)** of yield* stack.
> - **Early break** via for..of (calls return()).
> - **Iterative variant** for depth safety.
> - **LeetCode #2649** class wraps gen.
> - **Trap:** `yield` vs `yield*`; missing `()`; strings iterable.

---

**Related:** [flatten-array-simple.md](./flatten-array-simple.md) · [nested-array-generator-leetcode.md](./nested-array-generator-leetcode.md) · [`06-streams/custom-iterator.md`](../06-streams/custom-iterator.md) · [`06-streams/generator-pipeline.md`](../06-streams/generator-pipeline.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md), [`concepts/streams.md`](../../concepts/streams.md)
