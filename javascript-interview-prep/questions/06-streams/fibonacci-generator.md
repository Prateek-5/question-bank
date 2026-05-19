# Fibonacci with a generator (`function*`)

> **Difficulty:** Easy   |   **Time:** ~10 min   |   **Prereqs:** [`concepts/streams.md`](../../concepts/streams.md), [custom-iterator.md](./custom-iterator.md)
>
> **Source:** [LeetCode 2648 — Generate Fibonacci Sequence](https://leetcode.com/problems/generate-fibonacci-sequence/). Canonical generator interview.

---

## 1. Problem statement

Generator that yields fibonacci numbers infinitely. Memory O(1).

**Verification examples**

```js
function* fibonacci() {
  let a = 0, b = 1;
  while (true) {
    yield a;
    [a, b] = [b, a + b];
  }
}

const it = fibonacci();
it.next();                                                                // {value: 0, done: false}
it.next();                                                                // {value: 1, done: false}
it.next();                                                                // {value: 1, done: false}
[...take(fibonacci(), 7)];                                                // [0, 1, 1, 2, 3, 5, 8]
```

**Constraints**
- Infinite via `while (true)` — fine because lazy.
- O(1) memory regardless of pulls.
- `yield` pauses; `.next()` resumes.
- `.return()` and `.throw()` for graceful termination.

---

## 2. Plain-English restatement

`function*` returns an iterator (also iterable). `yield` pauses execution; the next `.next()` resumes. Infinite sequences work because evaluation is lazy — only the next value is computed.

---

## 3. Why this matters in interviews

5-minute concept-check. Senior bar: articulate lazy evaluation + memory + `.return()`/`.throw()` for cleanup.

---

## 4. Mental model

```
   function* fibonacci() {
     let a = 0, b = 1;
     while (true) {
       yield a;                      ← pause, return {value:a, done:false}
       [a, b] = [b, a + b];          ← resumed by .next()
     }
   }

   const it = fibonacci();           ← body NOT executed yet
   it.next();                        ← runs until first yield
                                       returns {value: 0, done: false}
   it.next();                        ← resumes; computes swap; yields again
                                       returns {value: 1, done: false}

   Lazy: while(true) is fine — only ONE pull at a time.
   Memory: 2 numbers regardless of how many pulls.

   yield* gen() = delegate (flatten another iterable inline).
   .return(v) forces end; try/finally cleanup runs.
   .throw(err) injects exception at current yield.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Does `function*` body execute when you call it?
> 2. Why can `while(true)` be safe in a generator?
> 3. What does `it.return('done')` do to a paused generator?

---

## 6. Brute force — walked through

### Wrong attempt 1: pre-compute array
Wastes memory for partial use.

### Wrong attempt 2: arrow function generator
Arrows can't be generators — SyntaxError.

### Wrong attempt 3: `yield` inside `.forEach` callback
Arrow inside forEach can't yield (yield must be in `function*`).

---

## 7. The unlocking insight

> **`function*` lazily yields one value per `.next()`. Infinite loops are fine — memory O(1). `yield*` delegates; `try/finally` for cleanup on early termination.**

Three properties:

1. **Lazy execution** — bodies pause at `yield`.
2. **Self-iterable** — iterator also has `[Symbol.iterator]() { return this; }`.
3. **Cleanup via `.return()`** — `try/finally` runs.

---

## 8. Solution (annotated)

```js
function* fibonacci() {                                                  // step 1: generator function
  let a = 0, b = 1;
  while (true) {
    yield a;                                                              // step 2: pause + emit
    [a, b] = [b, a + b];                                                  // step 3: tuple swap
  }
}

// take(n) helper
function* take(iter, n) {
  let i = 0;
  for (const v of iter) {
    if (i++ >= n) return;
    yield v;
  }
}

[...take(fibonacci(), 7)];                                                // [0, 1, 1, 2, 3, 5, 8]

// Cleanup-aware variant
function* fibWithCleanup() {
  try {
    yield* fibonacci();                                                   // step 4: delegate
  } finally {
    console.log('cleanup');                                               // runs on early break
  }
}
```

**Try it yourself**

```js
// for...of with break runs .return() automatically → finally runs
for (const n of fibWithCleanup()) {
  if (n > 100) break;
}
// 'cleanup' logged once.

// Manual termination
const it = fibonacci();
it.next();                                                                // {value: 0, done: false}
it.return(99);                                                            // {value: 99, done: true}
it.next();                                                                // {value: undefined, done: true} (done forever)

// Bidirectional yield
function* echo() {
  const x = yield 'first';                                                // .next(arg) passes arg back
  yield x;
}
const e = echo();
e.next();                                                                 // {value: 'first', done: false}
e.next('hello');                                                          // {value: 'hello', done: false}
```

---

## 9. Step-by-step dry run

```
const it = fibonacci();
  // body NOT executed; iterator object created.
  // internal state: undefined a, b (uninitialized).

it.next():
  Enter body. a=0, b=1.
  while(true): yield a (=0). PAUSE.
  Return {value: 0, done: false}.

it.next():
  Resume after yield.
  [a, b] = [b, a + b] = [1, 1]. a=1, b=1.
  Loop. yield a (=1). PAUSE.
  Return {value: 1, done: false}.

it.next():
  [a, b] = [1, 2]. yield 1. Return {value: 1, done: false}.

it.next():
  [a, b] = [2, 3]. yield 2. Return {value: 2, done: false}.

...

it.return(99):
  Force end. Any pending try/finally runs.
  Return {value: 99, done: true}.

it.next():
  Already done. Return {value: undefined, done: true}.

Memory: never holds more than 2 numbers (a, b). Even after 1M pulls.
```

---

## 10. Common confusion + traps

1. **Body executes on call** — no, lazy until `.next()`.
2. **Arrow generators** — SyntaxError.
3. **`yield` in nested callback** — SyntaxError; yield only in `function*` body.
4. **Generators are async** — sync unless `async function*`.
5. **Reuse exhausted iterator** — always done; recreate.
6. **`return v` ignored** — `for...of` discards return value.
7. **No backpressure for sync** — `for...of` drains as fast as possible.

---

## 11. Senior follow-ups & variants

### Variant 1 — `function*` returning a value
`function* g() { yield 1; return 'done' }` — manual `.next()` sees value on done.

### Variant 2 — `async function*` for I/O
Yield page results from paginated API.

### Variant 3 — `yield*` tree traversal
`function* inorder(node) { if (node.left) yield* inorder(node.left); yield node.value; if (node.right) yield* inorder(node.right); }`.

### Variant 4 — Iterator helpers (TC39)
`fibonacci().take(5).toArray()` (stage-4, 2025+).

### Variant 5 — `Readable.from(gen())`
Wraps generator as Node Readable stream.

---

## 12. How to think aloud

> "`function*` returns an iterator that's ALSO iterable (has `[Symbol.iterator]() { return this; }`). Body runs LAZILY — `yield` pauses execution; `.next()` resumes. Infinite sequences via `while(true)` are fine because only the NEXT value is computed — memory O(1). Bidirectional: `.next(arg)` passes arg back to the paused yield expression (used by `co`, `redux-saga`). `.return(v)` forces termination — any `try/finally` inside runs. `.throw(err)` injects exception at current yield; generator can `catch` and recover. `yield* gen()` delegates — flattens another iterable inline (great for tree recursion). `for...of` calls `.return()` on `break`/`throw` — cleanup hook. Trap: arrow functions can't be generators (SyntaxError); `yield` only inside `function*` body, NOT nested callbacks; calling the generator function doesn't execute body — you get an iterator, must call `.next()`."

---

## 13. 60-second revision

> - **`function* fn() { yield x }`** — lazy iterator + iterable.
> - **Body runs on `.next()`**, not on function call.
> - **`while(true)` SAFE** — only computes one value per pull.
> - **Memory O(1)** regardless of pulls.
> - **`.return(v)`** forces end + runs `try/finally`.
> - **`yield* gen()`** delegates (tree traversal).
> - **Arrow generators illegal.**
> - **`Readable.from(gen())`** bridges to Node streams.
> - **Trap:** body doesn't run on call; arrow generator; yield in nested cb.

---

**Related:** [custom-iterator.md](./custom-iterator.md) · [generator-pipeline.md](./generator-pipeline.md) · [async-iterator-pagination.md](./async-iterator-pagination.md) · [readable-stream-push.md](./readable-stream-push.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
