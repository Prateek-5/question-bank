# Build a custom iterator (`Symbol.iterator`, `next()`, `done`)

## Source
- codedamn "JavaScript Iterator Lab": https://codedamn.com/problem/LxpOdwQJevoLk9XxtlD1p
- Canonical ECMAScript spec: Iterator and Iterable protocols.

## Why this question matters in interviews
Iterators are the substrate of every modern JS feature: `for ... of`, spread `[...x]`, destructuring `[a, b] = x`, `Promise.all`, `Map`/`Set` construction, generators, async generators, even Node streams (`for await`). When an interviewer asks "make this object iterable," they're checking whether you understand the **protocol** behind all that syntax sugar. Senior backend engineers will write custom iterators when wrapping a paginated API, a linked list, a tree traversal, or a DB cursor — anywhere "produce values on demand" is the right mental model. Bonus: implementing iterator chaining (map/filter as iterators) is the foundation of TC39 Iterator Helpers (stable in 2025+).

## Concepts involved

### The two protocols
**Iterator protocol** — an object with a `.next()` method that returns `{ value, done }`.
```js
const iter = {
  next() { return { value: 42, done: false }; }
};
```
**Iterable protocol** — an object with a `[Symbol.iterator]()` method that returns an iterator.
```js
const iterable = {
  [Symbol.iterator]() { return iter; }
};
for (const v of iterable) { /* ... */ }
```

### Built-ins that are iterable
`Array`, `String`, `Map`, `Set`, `TypedArray`, `arguments`, `NodeList`. Plain objects are **not** — you have to add `[Symbol.iterator]` yourself.

### What `for ... of` actually does
```js
for (const x of obj) { body }
// equivalent to:
const it = obj[Symbol.iterator]();
while (true) {
  const { value, done } = it.next();
  if (done) break;
  const x = value;
  body;
}
```

### Iterator helpers (TC39 stage-4, stable in 2025+)
Iterators now have `.map`, `.filter`, `.take`, `.drop`, `.reduce`, `.toArray`. So `range(1, 100).filter(x => x % 2).take(5).toArray()` works on any iterator without intermediate arrays. Worth mentioning.

### Lazy evaluation
The big advantage over arrays: an iterator computes one value at a time. Memory is O(1), and you can iterate over an *infinite* sequence safely as long as you stop pulling.

### Iterator can be self-iterable
A common pattern: an iterator's `[Symbol.iterator]()` returns `this`. That makes it usable in `for ... of` *and* re-consumable from the saved iterator state.

## Brute force approach
"I'll just put the values in an array." Fine for 10 items. For 10 million items, or for an infinite sequence, you OOM the process. Also defeats the purpose if the data is generated lazily (DB cursor, paginated API).

## Optimal approach
Define `[Symbol.iterator]()` returning an object with `next()`. Encapsulate state in closure variables or in a class. For composability, make the iterator self-iterable. For chaining (map/filter), each operation returns a new lazy iterator that wraps the previous one.

## Solution (JavaScript)

```js
'use strict';

/**
 * Build a lazy, chainable iterator over an integer range.
 * Demonstrates Symbol.iterator + lazy map/filter/take that compose without
 * allocating intermediate arrays.
 */
function range(start, end, step = 1) {
  return makeIterable(function* () {
    for (let i = start; i < end; i += step) yield i;
  });
}

/**
 * Wrap a generator-fn (or any factory returning an iterator) into a
 * chainable iterable with .map / .filter / .take / .toArray.
 */
function makeIterable(factory) {
  return {
    [Symbol.iterator]() { return factory(); },

    map(fn) {
      const self = this;
      return makeIterable(function* () {
        for (const x of self) yield fn(x);
      });
    },

    filter(pred) {
      const self = this;
      return makeIterable(function* () {
        for (const x of self) if (pred(x)) yield x;
      });
    },

    take(n) {
      const self = this;
      return makeIterable(function* () {
        let i = 0;
        for (const x of self) {
          if (i++ >= n) return;
          yield x;
        }
      });
    },

    toArray() { return [...this]; },
  };
}

// Manual (no-generator) iterator — show you can do it without `function*`.
class LinkedListIterable {
  constructor(head) { this.head = head; }
  [Symbol.iterator]() {
    let node = this.head;
    return {
      next() {
        if (!node) return { value: undefined, done: true };
        const value = node.value;
        node = node.next;
        return { value, done: false };
      },
      [Symbol.iterator]() { return this; },     // self-iterable
      return(value) {                            // called when consumer bails early
        node = null;                             // release reference
        return { value, done: true };
      },
    };
  }
}

// Demo
const result = range(0, Infinity)              // INFINITE source — safe because lazy
  .filter((n) => n % 2 === 0)
  .map((n) => n * n)
  .take(5)
  .toArray();
console.log(result);  // [0, 4, 16, 36, 64]

const list = new LinkedListIterable({ value: 'a', next: { value: 'b', next: null } });
for (const v of list) console.log(v);   // 'a', 'b'
```

## Step-by-step dry run

`range(0, Infinity).filter(n => n % 2 === 0).map(n => n * n).take(5).toArray()`

The chain creates 4 nested iterables. **Nothing executes** until `toArray` triggers `[...this]`, which calls `Symbol.iterator` on the outermost (`take`).

| Pull # | take.next() asks map | map.next() asks filter | filter.next() asks range | yields |
| --- | --- | --- | --- | --- |
| 1 | requests next | requests next | yields 0 → pred(0)=true → forwards 0 | map → 0 → take yields 0 |
| 2 | requests next | requests next | yields 1 → pred=false; yields 2 → pred=true | map → 4 → take yields 4 |
| 3 | ... | ... | yields 3 (skip) → yields 4 | map → 16 |
| 4 | ... | ... | yields 5 (skip) → yields 6 | map → 36 |
| 5 | ... | ... | yields 7 (skip) → yields 8 | map → 64 |
| 6 | take's counter hits 5 → `return` | — | — | done |

**Key observation:** we never materialized the infinite range. We pulled exactly 10 items from `range` (the odd numbers got rejected, the even numbers got squared), produced 5 results, and stopped. Memory: O(1). This is the entire point of iterators.

Manual iterator (no generator) — `for (const v of list)`:
1. `for...of` calls `list[Symbol.iterator]()` → returns `{ next, return, [Symbol.iterator]: this }`.
2. `next()` → `{ value: 'a', done: false }`. `node` advances.
3. `next()` → `{ value: 'b', done: false }`. `node` advances to null.
4. `next()` → `{ value: undefined, done: true }`. Loop exits.

If the consumer `break`s early, `for...of` calls `return()` on the iterator — that's where you release references. Forgetting `return` = subtle memory leak.

## Important takeaways

**Syntax to memorize**
- Iterable: `obj[Symbol.iterator]() { return iterator; }`
- Iterator: `{ next() { return { value, done }; } }`
- Self-iterable iterator: also include `[Symbol.iterator]() { return this; }` — lets you pass the iterator itself to `for ... of`.
- `Symbol.iterator` is the well-known symbol — you can't use a string key.

**Patterns to reuse**
- Generators (`function*`) **always** produce iterators that are also iterable. Use them instead of writing `next()` by hand whenever possible.
- Lazy chaining: each operator returns a new iterable that pulls from the previous one. Zero intermediate arrays.
- DB cursors / paginated APIs / tree traversals are all natural iterators.

**Common mistakes**
- Returning `{ value, done: true }` with a real `value` — `done: true` means "the loop exits"; whatever `value` is there is ignored by `for ... of`. Use `done: true, value: undefined` unless you specifically want a generator's `return value`.
- Using a property key `"iterator"` instead of `Symbol.iterator` — `for ... of` won't find it.
- Mutating the iterable in-place during iteration — undefined behavior for most cases; for arrays, indices shift and you get duplicates / skips.
- Forgetting `return()` on iterators that hold resources — leaks file handles, DB cursors.
- Confusing iterator with iterable. `[1,2,3]` is iterable; `[1,2,3][Symbol.iterator]()` is the iterator.

**Related**
- `fibonacci-generator.md` — generators (`function*`) are sugar over this protocol.
- `async-iterator-pagination.md` — async cousin: `Symbol.asyncIterator` + `for await`.
- `readable-stream-push.md` — Node streams are async iterables under the hood.

## Variants

1. **`zip(iterA, iterB)`** — produce pairs `[a, b]` until either runs out. Tests that you can pull from two iterators in lockstep and stop on the first `done: true`.

2. **`groupBy(iter, fn)`** — yield sub-iterators of consecutive equal-key items, lazily. Subtle because each sub-iterator must not pre-consume the next group.

3. **Async + sync interop** — make an iterable that exposes both `Symbol.iterator` and `Symbol.asyncIterator`. The async one might do I/O between values; the sync one might just iterate cached results. Bonus: how do you handle errors differently in each path?

## Revision notes

> **custom iterator — 60 second recap**
> - Iterable: `obj[Symbol.iterator]() { return iterator; }`
> - Iterator: object with `next()` returning `{ value, done }`.
> - `for ... of`, spread, destructuring, `Promise.all` — all use this protocol.
> - Self-iterable trick: iterator's `[Symbol.iterator]() { return this; }`.
> - Generators (`function*`) auto-implement both protocols — prefer them.
> - Lazy chaining: each operator wraps the previous iterable. No intermediate arrays. Safe over infinite sources.
> - `return(value)` is called when the consumer bails early — release resources here.
> - Iterator Helpers (TC39 stage-4, 2025+): `.map/.filter/.take/.toArray` natively on iterators.
> - Trap: `done: true` with a value — the value is ignored by `for ... of`.
> - Trap: string key `"iterator"` instead of `Symbol.iterator`.
