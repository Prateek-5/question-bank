# NestedIterator class — `next()` / `hasNext()` API

> **Difficulty:** Medium   |   **Time:** ~12 min   |   **Prereqs:** [nested-array-generator-codedamn.md](./nested-array-generator-codedamn.md), [`06-streams/custom-iterator.md`](../06-streams/custom-iterator.md)
>
> **Source:** LeetCode #2649. Sibling to #341 "Flatten Nested List Iterator."

---

## 1. Problem statement

Class with `next()` returning next leaf and `hasNext()` returning boolean. Stateful across calls.

**Verification examples**

```js
const it = new NestedIterator([1, [2, [3, 4]], 5]);
while (it.hasNext()) console.log(it.next());           // 1 2 3 4 5

it.hasNext();                                           // false at end
```

**Constraints**
- `next()` and `hasNext()` methods.
- State explicit (not implicit via generator).
- `hasNext` may need to peek-and-advance (lazy "skip past arrays").
- LeetCode contract: nested list of `NestedInteger` objects.

---

## 2. Plain-English restatement

OO sibling of generator. Maintain stack of iterators or pre-flatten. `hasNext` must skip past empty arrays to determine if any leaf remains.

---

## 3. Why this matters in interviews

OO interview: build Iterator Protocol by hand. Tests: protocol literacy, state mgmt, lazy vs eager tradeoff.

---

## 4. Mental model

```
   Two implementations:
   
   (A) Eager pre-flatten:
     constructor: flatten to leaves array; index = 0.
     next(): return leaves[index++].
     hasNext(): index < leaves.length.
     Pros: simple. Cons: O(n) construction memory.
   
   (B) Lazy stack of indices:
     stack = [{list, idx}]
     hasNext(): advance until top has unflat leaf or empty.
       If current item is array, push frame, recurse.
       If leaf, return true (peeked).
       If frame exhausted, pop.
     next(): return peeked leaf; advance.
     Pros: O(depth) memory. Cons: trickier.
   
   (C) Generator delegate:
     constructor: build generator.
     next/hasNext wrap buffered next.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why not just generator?
> 2. Lazy vs eager tradeoff?
> 3. What does `hasNext` need to handle?

---

## 6. Brute force — walked through

```js
// Eager
class Eager {
  constructor(nested) {
    this.leaves = [];
    (function flatten(arr) {
      for (const x of arr) Array.isArray(x) ? flatten(x) : leaves.push(x);
    })(nested);
    this.i = 0;
  }
}
```

Works; O(n) memory upfront.

---

## 7. The unlocking insight

> **Eager pre-flatten OR lazy stack of iterators. Generator wraps cleanly. `hasNext` may need to advance past empty arrays.**

Three properties:

1. **Eager flatten** simple.
2. **Lazy stack** O(depth).
3. **Generator wrap** cleanest.

---

## 8. Solution (annotated)

```js
// (A) Eager
class NestedIteratorEager {
  constructor(nestedList) {
    this.leaves = [];
    this.i = 0;
    this._flatten(nestedList);                                              // step 1: flatten once
  }
  _flatten(list) {
    for (const x of list) {
      if (Array.isArray(x)) this._flatten(x);
      else this.leaves.push(x);
    }
  }
  hasNext() { return this.i < this.leaves.length; }
  next() { return this.leaves[this.i++]; }
}

// (B) Lazy stack of iterators
class NestedIteratorLazy {
  constructor(nestedList) {
    this.stack = [{ list: nestedList, idx: 0 }];                             // step 2: explicit stack
  }
  hasNext() {
    while (this.stack.length) {
      const frame = this.stack[this.stack.length - 1];
      if (frame.idx >= frame.list.length) {
        this.stack.pop();                                                    // step 3: exhausted
        continue;
      }
      const item = frame.list[frame.idx];
      if (Array.isArray(item)) {
        frame.idx++;
        this.stack.push({ list: item, idx: 0 });                             // step 4: descend
      } else {
        return true;                                                         // step 5: leaf available
      }
    }
    return false;
  }
  next() {
    if (!this.hasNext()) return undefined;
    const frame = this.stack[this.stack.length - 1];
    return frame.list[frame.idx++];
  }
}

// (C) Generator delegate (cleanest)
function* leaves(arr) {
  for (const x of arr) {
    if (Array.isArray(x)) yield* leaves(x);
    else yield x;
  }
}

class NestedIteratorGen {
  constructor(nestedList) {
    this.iter = leaves(nestedList);
    this._next = this.iter.next();                                           // step 6: buffer next
  }
  hasNext() { return !this._next.done; }
  next() {
    const v = this._next.value;
    this._next = this.iter.next();                                           // step 7: advance buffer
    return v;
  }
  // Optional: make iterable
  [Symbol.iterator]() { return this; }
}
```

**Try it yourself**

```js
const it = new NestedIteratorLazy([1, [2, [3, 4]], 5]);
while (it.hasNext()) console.log(it.next());                  // 1 2 3 4 5

// Edge: leading empty array
const it2 = new NestedIteratorLazy([[], [1, []]]);
const all = [];
while (it2.hasNext()) all.push(it2.next());
all;                                                           // [1]

// LeetCode passes [NestedInteger] not raw arrays
// NestedInteger has .isInteger() and .getList() — adapt accordingly.

// Use as iterable (with Symbol.iterator)
const it3 = new NestedIteratorGen([1, [2, [3]]]);
[...it3];                                                      // [1, 2, 3]

// Compare to generator
const gen = leaves([1, [2, [3]]]);
[...gen];                                                      // [1, 2, 3] — same
```

---

## 9. Step-by-step dry run

```
NestedIteratorLazy([1, [2, []], 3]):

constructor: stack = [{list:[1,[2,[]],3], idx:0}].

hasNext():
  Top frame idx=0, item=1. Not array. Return true.

next():
  hasNext peeked. frame.idx++ → 1. Return 1.

hasNext():
  Top idx=1, item=[2,[]]. Array. frame.idx++=2. Push {list:[2,[]], idx:0}.
  Top idx=0, item=2. Not array. Return true.

next():
  Return 2. Top idx=1.

hasNext():
  Top idx=1, item=[]. Array. idx++=2. Push {list:[], idx:0}.
  Top idx=0, frame.idx=0 ≥ list.length=0 → exhausted. POP.
  Back to {list:[2,[]], idx:2}. idx=2 ≥ length=2 → exhausted. POP.
  Back to outer {list:[1,[2,[]],3], idx:2}. item=3. Not array. Return true.

next(): Return 3.

hasNext():
  Top idx=3 ≥ length=3 → exhausted. POP.
  Stack empty. Return false.

Loop exit.

Key insight: hasNext must advance through empty arrays / arrays-of-arrays
to determine if a leaf actually remains. It mutates state — peeking by
positioning the stack to point at the next leaf.
```

---

## 10. Common confusion + traps

1. **`hasNext` doesn't advance** — returns true forever if leaves exhausted but arrays remain.
2. **Generator without buffer** — `hasNext` peek hard.
3. **`next()` without `hasNext`** check — returns undefined at end.
4. **Strings as iterable** — beware string yielding chars.
5. **Mutate input** — class methods should not mutate.
6. **Symbol.iterator** missing — can't use for-of on instance.
7. **LeetCode NestedInteger** API — different from raw arrays.

---

## 11. Senior follow-ups & variants

### Variant 1 — Eager flatten
Simple; O(n) memory.

### Variant 2 — Lazy stack of indices
O(depth) memory.

### Variant 3 — Generator wrap
Cleanest.

### Variant 4 — Bidirectional iterator
Add `prev()`.

### Variant 5 — Iterator over object tree
Same idea, for object children.

---

## 12. How to think aloud

> "OO iterator over nested array. Three implementations: (A) Eager — flatten once in constructor; O(n) memory; next/hasNext are array index ops. (B) Lazy — stack of `{list, idx}` frames; `hasNext()` advances by popping exhausted frames and pushing into nested arrays until top is a leaf or stack empty; `next()` calls `hasNext()` to position then returns and advances; O(depth) memory. (C) Generator wrap — define `function* leaves(arr)` with `yield*`, store generator + buffered next in instance; cleanest. `hasNext()` MUST advance internal state past empty arrays / nested-empty-arrays — peeking is stateful. Optionally `[Symbol.iterator]() { return this; }` to enable `for..of` and spread. LeetCode #2649 / #341 pass `NestedInteger` objects with `.isInteger()` and `.getList()` instead of raw arrays — same algorithm. Trap: `hasNext` that doesn't advance through empty arrays (returns true forever); calling `next()` without `hasNext()` check; missing Symbol.iterator (can't spread)."

---

## 13. 60-second revision

> - **Eager flatten** simple; O(n).
> - **Lazy stack** O(depth).
> - **Generator wrap** cleanest.
> - **`hasNext` advances** state.
> - **`Symbol.iterator`** for spread.
> - **LeetCode `NestedInteger`** wraps integers.
> - **Trap:** non-advancing hasNext; no Symbol.iterator; strings iterable.

---

**Related:** [nested-array-generator-codedamn.md](./nested-array-generator-codedamn.md) · [flatten-array-simple.md](./flatten-array-simple.md) · [`06-streams/custom-iterator.md`](../06-streams/custom-iterator.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md), [`concepts/streams.md`](../../concepts/streams.md)
