# Custom iterator — `Symbol.iterator`, `next()`, lazy chains

> **Difficulty:** Medium   |   **Time:** ~15 min   |   **Prereqs:** [fibonacci-generator.md](./fibonacci-generator.md), [`03-prototype/symbol-iterator-on-class.md`](../03-prototype/symbol-iterator-on-class.md)
>
> **Source:** ECMAScript Iterator and Iterable protocols. codedamn iterator lab.

---

## 1. Problem statement

Build a custom iterable with `Symbol.iterator`. Bonus: lazy `map`/`filter`/`take` chain without intermediate arrays.

**Verification examples**

```js
function range(start, end) {
  return { [Symbol.iterator]() {
    let i = start;
    return { next() { return i < end ? {value: i++, done: false} : {value: undefined, done: true} } };
  }};
}

for (const n of range(1, 4)) console.log(n);                              // 1, 2, 3
[...range(1, 4)];                                                         // [1, 2, 3]
const [a, b] = range(10, 13);                                             // a=10, b=11
```

**Constraints**
- Two protocols: **iterable** (has `[Symbol.iterator]()`), **iterator** (has `next()` returning `{value, done}`).
- Self-iterable iterator: `[Symbol.iterator]() { return this; }`.
- Lazy chains: each operator wraps the previous — no intermediate arrays.
- `return()` hook for cleanup on early termination.

---

## 2. Plain-English restatement

JS's iteration protocol underlies `for...of`, spread, destructuring, `Promise.all`, `Map`/`Set` construction. **Iterable**: has `[Symbol.iterator]()` returning an iterator. **Iterator**: has `next()` returning `{value, done}`. Generators auto-implement both.

---

## 3. Why this matters in interviews

Tests well-known symbols + protocol + lazy chaining. Iterator helpers (TC39 stage-4) build on this.

---

## 4. Mental model

```
   Iterable: { [Symbol.iterator](): Iterator }
   Iterator: { next(): {value, done} }

   for...of obj:
     it = obj[Symbol.iterator]()
     while (true):
       {value, done} = it.next()
       if done break
       body with value

   Self-iterable iterator:
     iterator.[Symbol.iterator] = function() { return this }
     ← lets you pass the iterator directly to for...of

   Lazy chain (map/filter/take):
     Each op returns NEW iterable wrapping previous.
     Nothing executes until consumer pulls.
     Memory O(1); safe over infinite sources.

   return(v) hook:
     Called when consumer break's or throw's mid-iteration.
     Release file handles, DB cursors, etc.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What's the difference between iterable and iterator?
> 2. When is `return()` called on an iterator?
> 3. Why is `range(0, Infinity).filter(...).map(...).take(5)` safe?

---

## 6. Brute force — walked through

### Wrong attempt 1: store in array
O(n) memory; can't iterate infinite source.

### Wrong attempt 2: string key `"iterator"`
`for...of` won't find it; must be `Symbol.iterator`.

### Wrong attempt 3: return `{value, done: true}` with real value
`for...of` ignores value when done.

---

## 7. The unlocking insight

> **Iterable returns iterator. Iterator's `next()` returns `{value, done}`. Lazy chains wrap previous iterables — no intermediate arrays. Use generators for cleanest implementation.**

Three properties:

1. **Two protocols** — iterable + iterator.
2. **Self-iterable trick** — iterator's `[Symbol.iterator]()` returns `this`.
3. **Lazy wrapping** — composable without materialization.

---

## 8. Solution (annotated)

```js
// Manual iterator
class LinkedList {
  constructor(head) { this.head = head; }
  [Symbol.iterator]() {                                                  // step 1: iterable
    let node = this.head;
    return {                                                              // step 2: iterator
      next() {
        if (!node) return {value: undefined, done: true};
        const v = node.value;
        node = node.next;
        return {value: v, done: false};
      },
      [Symbol.iterator]() { return this; },                               // step 3: self-iterable
      return(v) {                                                          // step 4: cleanup hook
        node = null;
        return {value: v, done: true};
      },
    };
  }
}

// Lazy chainable iterables
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

function range(start, end, step = 1) {
  return makeIterable(function* () {
    for (let i = start; i < end; i += step) yield i;
  });
}

// Infinite + chain = safe
range(0, Infinity)
  .filter((n) => n % 2 === 0)
  .map((n) => n * n)
  .take(5)
  .toArray();                                                              // [0, 4, 16, 36, 64]
```

**Try it yourself**

```js
// for...of with break runs return() automatically
const list = new LinkedList({value:'a', next:{value:'b', next:{value:'c', next:null}}});
for (const v of list) {
  console.log(v);
  if (v === 'b') break;                                                   // return() called → node=null released
}

// Iterator helpers (TC39 stage-4, 2025+)
function* nats() { let n = 0; while (true) yield n++; }
nats().take(5).filter(x => x % 2).map(x => x * 10).toArray();             // [10, 30] (when available)
```

---

## 9. Step-by-step dry run

```
range(0, Infinity).filter(n => n%2 === 0).map(n => n*n).take(5).toArray()

Build phase (NO execution):
  range = wraps factory* yielding 0..Infinity.
  .filter wraps range.
  .map wraps filter.
  .take wraps map.
  .toArray triggers [...this] on take.

Execution (pull-driven):
  Iteration 1:
    take.next() → asks map.next() → asks filter.next() → asks range.next() → yields 0.
    filter: 0 % 2 === 0 → yields 0 to map.
    map: 0 * 0 = 0 → yields 0 to take.
    take: counter 0 < 5 → yields 0.
    result: [0].
  
  Iteration 2:
    range.next() → 1.
    filter: 1 % 2 ≠ 0 → skip. range.next() → 2.
    filter: yield 2 to map.
    map: 4 → take → yields 4.
    result: [0, 4].
  
  ... continues. range yields 0,1,2,3,4,5,6,7,8. filter passes evens. map squares. take stops at 5.
  
  After 5 takes: take returns done. Iteration ends.
  result: [0, 4, 16, 36, 64].

Memory: O(1). Only one value flows through pipeline at a time.
Range NEVER materializes infinite values.
```

---

## 10. Common confusion + traps

1. **Iterator vs iterable** — separate protocols.
2. **String key `"iterator"`** — must be `Symbol.iterator`.
3. **`done: true` with value** — `for...of` ignores value.
4. **Forget `return()` on resource-holders** — fd/cursor leaks.
5. **Mutate during iteration** — undefined behavior.
6. **Spread infinite iterable** — `[...infiniteGen]` hangs.
7. **Self-iterable trick** — iterator's `[Symbol.iterator]() { return this }` for `for...of` convenience.

---

## 11. Senior follow-ups & variants

### Variant 1 — `zip(a, b)`
Pull from two iterators in lockstep; stop on first done.

### Variant 2 — `groupBy(iter, keyFn)`
Yield sub-iterators of consecutive equal-key items.

### Variant 3 — Async + sync interop
Expose both `Symbol.iterator` and `Symbol.asyncIterator`.

### Variant 4 — Iterator helpers (TC39)
`.map`, `.filter`, `.take`, `.toArray` native on iterators (stage-4).

### Variant 5 — `for...of` over Map/Set
Built-ins already implement protocol; same shape.

---

## 12. How to think aloud

> "Two protocols. Iterable: has `[Symbol.iterator]()` returning an iterator. Iterator: has `next()` returning `{value, done}`. `for...of`, spread, destructuring, `Promise.all`, `Map`/`Set` construction all call `[Symbol.iterator]()` to get a fresh iterator. Generators (`function*`) auto-implement both — prefer them. Self-iterable iterator: include `[Symbol.iterator]() { return this; }` so the iterator itself can be passed to `for...of`. Lazy chaining (map/filter/take): each op returns a new iterable wrapping the previous; nothing executes until consumer pulls. Memory O(1); safe over infinite sources. `return(v)` hook is called when `for...of` breaks or throws — release file handles, DB cursors. Trap: iterator vs iterable confusion; string key `'iterator'`; `done: true` with value (ignored); forgetting return() on resource holders; spreading infinite iterables."

---

## 13. 60-second revision

> - **Iterable:** `obj[Symbol.iterator]()` → iterator.
> - **Iterator:** `iter.next()` → `{value, done}`.
> - **Self-iterable trick:** `iter[Symbol.iterator]() { return this }`.
> - **Generators auto-implement** both — prefer.
> - **Lazy chaining:** wrap previous; no intermediate arrays; safe for infinite.
> - **`return(v)` hook** for cleanup on `break`/`throw`.
> - **Iterator helpers** (TC39 stage-4): `.map`, `.filter`, `.take`, `.toArray`.
> - **Trap:** protocol confusion; string key; done+value; forget return().

---

**Related:** [fibonacci-generator.md](./fibonacci-generator.md) · [generator-pipeline.md](./generator-pipeline.md) · [async-iterator-pagination.md](./async-iterator-pagination.md) · [`03-prototype/symbol-iterator-on-class.md`](../03-prototype/symbol-iterator-on-class.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
