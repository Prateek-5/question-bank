# Generate Fibonacci sequence with a generator (`function*`)

## Source
- LeetCode 2648 "Generate Fibonacci Sequence": https://leetcode.com/problems/generate-fibonacci-sequence/
- Canonical generator interview problem.

## Why this question matters in interviews
This is the canonical 5-minute generator question and a perfect concept-check. A senior backend engineer should be able to explain: (1) `function*` returns an **iterator** that's also iterable, (2) `yield` pauses execution and resumes on the next `.next()` call, (3) **infinite sequences are fine** because evaluation is lazy — only the next value is computed, memory stays O(1), (4) `.return()` and `.throw()` exist for graceful termination. If you can articulate those four points and write 5 lines of code, you've signaled understanding of every modern Node primitive (async iterators, async generators, `Readable.from`).

## Concepts involved

### `function*` vs regular function
```js
function* gen() {
  yield 1;
  yield 2;
}
const it = gen();        // does NOT execute the body yet
it.next();               // { value: 1, done: false }   — runs until first yield
it.next();               // { value: 2, done: false }
it.next();               // { value: undefined, done: true }
```
- Body runs lazily, suspending at each `yield`.
- Returns an object that implements **both** the iterator protocol (`.next()`) and the iterable protocol (`[Symbol.iterator]() { return this; }`).
- `return` statement inside the generator → `{ value: <return val>, done: true }`.

### `yield` is bidirectional
```js
function* echo() {
  const x = yield 'first';   // x is whatever .next(arg) passed in
  yield x;
}
const it = echo();
it.next();          // { value: 'first', done: false }
it.next('hello');   // { value: 'hello', done: false }   — 'hello' became x
```
Used by libraries like `co`, `redux-saga`. Modern code rarely needs this (async/await is cleaner), but interviewers love to ask.

### `.return(v)` and `.throw(err)`
- `it.return(value)` → forces the generator to end; the next pending `yield` resolves and a `try/finally` inside the generator runs.
- `it.throw(err)` → injects an exception at the current `yield`. If the generator has a `try/catch`, it can recover.
- Both are why `for ... of` over a generator inside a `break`'d loop or a thrown body cleans up properly.

### Lazy infinite sequences (the killer feature)
```js
function* nats() { let n = 0; while (true) yield n++; }
```
This is fine. `while (true)` is fine. **Memory is O(1).** The function only computes a value when someone pulls. Combine with `take(N)`-style consumers to get bounded output. This trick is impossible with arrays.

### `yield*` — delegation
```js
function* inner() { yield 1; yield 2; }
function* outer() { yield 0; yield* inner(); yield 3; }
[...outer()];   // [0, 1, 2, 3]
```
`yield*` flattens another iterable into this generator. Useful for tree traversal recursion without manual recursion overhead.

## Brute force approach
Pre-compute fibonacci up to N into an array, then return values from the array. Wastes memory when caller might only want a few values, and breaks completely for "give me numbers until predicate X" patterns where you don't know N upfront.

## Optimal approach
Generator with two local variables `a, b` that swap on each iteration. Yields one value, then advances. O(1) memory, O(1) per step. The body is 4 lines.

## Solution (JavaScript)

```js
'use strict';

/**
 * Infinite Fibonacci generator. O(1) memory.
 * @returns {Generator<number, void, unknown>}
 */
function* fibonacci() {
  let a = 0, b = 1;
  while (true) {
    yield a;
    [a, b] = [b, a + b];           // tuple swap; no temp var needed
  }
}

// LeetCode-style: produce the first n terms.
function* fibFirstN(n) {
  let i = 0;
  for (const v of fibonacci()) {
    if (i++ >= n) return;          // generator return → done:true
    yield v;
  }
}

// Bonus: cleanup-aware variant with try/finally.
function* fibWithCleanup() {
  console.log('start');
  try {
    yield* fibonacci();            // delegate; cleanup still runs on .return()
  } finally {
    console.log('cleanup');        // runs on .return() / break / throw
  }
}

// Consumption patterns ------------------------------------------------------

// (1) for ... of with manual break
for (const n of fibonacci()) {
  if (n > 100) break;              // for...of calls .return() under the hood
  console.log(n);
}

// (2) Iterator helpers (stable in 2025+)
const firstFive = fibonacci().take(5).toArray();   // [0, 1, 1, 2, 3]

// (3) Spread with a take wrapper (works in older runtimes too)
function take(iter, n) {
  const out = [];
  for (const v of iter) {
    if (out.length >= n) break;
    out.push(v);
  }
  return out;
}
console.log(take(fibonacci(), 7));  // [0, 1, 1, 2, 3, 5, 8]
```

LeetCode signature variant:
```js
/**
 * @return {Generator<number>}
 */
var fibGenerator = function*() {
  let a = 0, b = 1;
  while (true) {
    yield a;
    [a, b] = [b, a + b];
  }
};
```

## Step-by-step dry run

`const it = fibonacci();`

| Call | Internal state before | Action | Returns | State after |
| --- | --- | --- | --- | --- |
| (creation) | none | body not executed | iterator object | a=undef, b=undef (uninitialized) |
| `it.next()` | enters body, a=0, b=1, hits `yield a` | suspends at yield | `{value: 0, done: false}` | a=0, b=1, paused after yield |
| `it.next()` | resumes, swap → a=1, b=1, loop, hits `yield a` | suspends | `{value: 1, done: false}` | a=1, b=1 |
| `it.next()` | swap → a=1, b=2, yield 1 | suspends | `{value: 1, done: false}` | a=1, b=2 |
| `it.next()` | swap → a=2, b=3, yield 2 | suspends | `{value: 2, done: false}` | a=2, b=3 |
| `it.next()` | swap → a=3, b=5, yield 3 | suspends | `{value: 3, done: false}` | a=3, b=5 |
| `it.return(99)` | currently paused | forces end | `{value: 99, done: true}` | terminated; further `.next()` always returns `{done: true}` |

Note we *never* execute past a yield until someone calls `.next()` again. **The infinite loop is bounded by demand**, not by code. Memory is exactly 2 numbers regardless of how many values you pull.

With `fibWithCleanup` and a consumer that breaks early:
```js
const it = fibWithCleanup();
for (const v of it) {
  if (v > 5) break;        // calls it.return() implicitly
}
// Output: "start" once, "cleanup" once — try/finally honored.
```

## Important takeaways

**Syntax to memorize**
- `function* name() { yield x; }` — note the asterisk and the keyword `yield`.
- Arrow functions **cannot** be generators. `const f = *() => {}` is a syntax error.
- Generators can be methods: `{ *gen() { yield 1; } }` or class members: `class C { *gen() {} }`.
- `yield*` delegates to another iterable.
- Returns an object with `next`, `return`, `throw`, and `[Symbol.iterator]` → self-iterable.

**Patterns to reuse**
- Infinite sequences: nats, fibonacci, primes (sieve), exponential backoff delays.
- Tree traversal: recursive `function* inorder(node) { if (node.left) yield* inorder(node.left); yield node.value; if (node.right) yield* inorder(node.right); }`.
- State machines: each `yield` represents waiting on the next event.
- Coroutines for cooperative scheduling (rare in modern Node, but interview-worthy).

**Common mistakes**
- Calling the generator function expecting it to run — it doesn't. You get an iterator; you must call `.next()` (or iterate) to advance.
- Forgetting that `yield` only pauses inside a `function*`, **not** inside nested callbacks. `function* g() { arr.forEach(x => yield x) }` is a syntax error — `yield` is unreachable from inside the arrow.
- Treating generators as async. They're synchronous unless you make them async (`async function*`).
- Using arrays where a generator would be cleaner — e.g. computing a full 10⁶-element fibonacci array when you only need the first 20.
- Calling `.next()` on a finished iterator and expecting an error — it just returns `{ value: undefined, done: true }` forever.

**Related**
- `custom-iterator.md` — the underlying protocol that `function*` implements for you.
- `async-iterator-pagination.md` — `async function*` for I/O-bound sources.
- `readable-stream-push.md` — `Readable.from(generator())` wraps a generator as a Node stream.

## Variants

1. **`function*` returning a value** — modify so `fibFirstN(5)` ends with `return 'done'`; the consumer gets `{ value: 'done', done: true }` on the final `.next()`. Note: `for ... of` discards the return value; only manual `.next()` callers see it.

2. **`async function*` for I/O** — yield page results from a paginated API. Each `await` inside the generator pauses the consumer. This is the modern way to wrap REST/GraphQL pagination — see the async-iterator file.

3. **`yield*` for tree traversal** — write a generator that yields every leaf of an arbitrarily nested array. The recursive case is one line: `yield* flatten(item)`. Compare against a manual stack-based iterator — far cleaner.

## Revision notes

> **fibonacci generator — 60 second recap**
> - `function*` returns an iterator that is also iterable. Body runs lazily.
> - `yield` suspends; `.next()` resumes. Bidirectional: `.next(arg)` passes `arg` back into the generator.
> - Infinite sequences are FINE because lazy → memory O(1), only next value computed.
> - `yield*` delegates to another iterable; great for tree traversal.
> - `.return(v)` and `.throw(err)` force termination; `try/finally` inside the generator still runs → use it for cleanup.
> - `for ... of` calls `.return()` on `break`/`throw` → resources released.
> - Arrow functions cannot be generators. `yield` only works inside `function*`, not inside nested callbacks.
> - Modern pull-with-take: iterator helpers `gen().take(n).toArray()` (TC39 stage-4).
> - Trap: calling the generator function and expecting it to run — you got an iterator; iterate it.
