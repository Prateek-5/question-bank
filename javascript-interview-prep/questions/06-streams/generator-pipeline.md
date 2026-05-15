# Build a sync data pipeline with generators

## Source
- MDN Generators: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/function*
- "Generators in 2018" by Eric Elliott (still the cleanest write-up on pipelines via `yield`).
- Comes up in functional-leaning Node interviews and ETL roles — anyone who's used Python's `itertools.chain` style coding asks for the JS equivalent.

## Why this question matters in interviews
Generators are the "I know JS deeply" signal. Most candidates use `map`/`filter`/`reduce` and stop. Senior backend engineers — especially those dealing with large CSV/log/JSON-lines files — pull out generators because they avoid materializing intermediate arrays. A 100 MB log file processed with `arr.filter(...).map(...)` peaks at ~300 MB of allocations. The same pipeline with generators peaks at one record. The interviewer is checking: can you compose `function*` stages like Unix `cat file | grep ERROR | awk '{print $1}' | head -10`? Bonus: it sets up the natural follow-up about async generators, which become full-featured streams.

## Concepts involved

### Syntax to lock in
```js
function* take(iter, n) {
  for (const x of iter) {
    if (n-- <= 0) return;
    yield x;
  }
}

function* map(iter, fn)    { for (const x of iter) yield fn(x); }
function* filter(iter, fn) { for (const x of iter) if (fn(x)) yield x; }

// compose
const lines    = readLines('access.log');          // function*
const errors   = filter(lines, l => l.includes('ERROR'));
const ips      = map(errors, l => l.split(' ')[0]);
const firstTen = take(ips, 10);

for (const ip of firstTen) console.log(ip);
```

### Runtime / engine behavior
- A generator function (`function*`) returns a **Generator** object: an iterator AND an iterable. It has a `.next()` method and also `[Symbol.iterator]()` returning itself.
- Each `.next()` runs the generator body until the next `yield` (or `return`), then suspends. Returns `{ value, done }`.
- **Lazy by construction.** `map(iter, fn)` doesn't run `fn` on anything until the consumer calls `.next()` on the resulting generator.
- Composition is just function calling: `take(map(filter(source, ...), ...), 10)`. Each wrapper is itself a generator.
- `for...of` calls `.next()` until `{ done: true }`. `break` triggers the generator's `.return()` method, which runs `try/finally` blocks — your cleanup hook.
- **Memory: O(1) per stage.** Only one value flows through the pipeline at a time. No intermediate arrays.
- **Backpressure is natural.** Downstream pulls when ready. If `take(iter, 10)` stops after 10 items, upstream stops being driven — `readLines` never reads more than ~10 lines worth of source.
- Generators are sync — for I/O you'd reach for **async** generators (`async function*` + `for await`), which is the natural follow-up.

### Edge cases (interview traps)
1. **Cleanup on `break`.** If `readLines` opens a file descriptor, you must `try/finally` inside the generator to close it. Otherwise, breaking out of a `for...of` loop early leaks the fd.
2. **`return value` semantics.** A generator can `return v` — that `v` shows up as `{ value: v, done: true }`. `for...of` ignores the value when `done`. So don't rely on consumers seeing `return` values.
3. **Generators are single-use.** Once exhausted, calling `.next()` returns `{ done: true }` forever. Can't reset. If you need re-iteration, wrap in a function and call it fresh.
4. **No parallelism.** Generators are sequential. If a stage is expensive, the pipeline stalls. For CPU-heavy work you'd want worker threads; for I/O you'd want async generators.
5. **`yield*` delegates** — `yield* otherGen()` flattens another generator inline. Equivalent to `for (const x of otherGen()) yield x;`, slightly cleaner.
6. **Spreading is dangerous.** `[...generator]` materializes the entire output — defeats the streaming benefit. Use only when you know the output is small.
7. **Errors mid-pipeline.** If a stage throws, the exception propagates up through `for...of`. The generator is then marked done. Downstream stages never see the value that caused the throw.
8. **`.throw(err)`** lets a consumer inject an exception into the generator at the suspended `yield`. Used by frameworks; ordinary code rarely calls it.

## Brute force approach
"I'll just chain array methods: `arr.filter(...).map(...).slice(0, 10)`." Works for small data but:
- Each method materializes a new array. `filter` builds the full filtered array even if you only `take(10)`.
- Memory peak is sum of all intermediates.
- For a generator-style source (e.g., reading from disk lazily), you'd have to `[...gen]` first — converting your O(1) memory pipeline to O(n).
- The interviewer specifically wants to see that you understand lazy composition.

## Optimal approach
Define each stage as `function*` taking the previous iterable as input. Compose by function calls: each call is O(1) (returns the generator object); no work happens until a consumer calls `.next()`. The for-loop at the end drives the entire pipeline one value at a time. Memory is constant in the size of the pipeline (one value in flight per stage).

## Solution (JavaScript)

```js
const fs = require('fs');

/* ============================================================
   stage primitives — generic, reusable
   ============================================================ */

function* map(iter, fn) {
  for (const x of iter) yield fn(x);
}

function* filter(iter, fn) {
  for (const x of iter) if (fn(x)) yield x;
}

function* take(iter, n) {
  for (const x of iter) {
    if (n-- <= 0) return;
    yield x;
  }
}

function* flatMap(iter, fn) {
  for (const x of iter) yield* fn(x);
}

function reduce(iter, fn, init) {
  let acc = init;
  for (const x of iter) acc = fn(acc, x);
  return acc;
}

/* ============================================================
   source — synchronous line reader with cleanup
   ============================================================ */

function* readLinesSync(path) {
  // toy synchronous reader; in real code use a buffered stream
  const fd = fs.openSync(path, 'r');
  try {
    const buf = Buffer.alloc(64 * 1024);
    let tail = '';
    let bytesRead;
    while ((bytesRead = fs.readSync(fd, buf, 0, buf.length, null)) > 0) {
      const text = tail + buf.toString('utf8', 0, bytesRead);
      const lines = text.split('\n');
      tail = lines.pop();
      for (const line of lines) yield line;
    }
    if (tail.length) yield tail;
  } finally {
    fs.closeSync(fd);  // runs even if consumer breaks early — fd is safe
  }
}

/* ============================================================
   compose a pipeline — Unix pipes in JS
   ============================================================ */

// equivalent of:   cat access.log | grep ERROR | awk '{print $1}' | head -10
const pipeline = take(
  map(
    filter(readLinesSync('access.log'), l => l.includes('ERROR')),
    l => l.split(' ')[0]
  ),
  10
);

for (const ip of pipeline) console.log(ip);
```

If you prefer left-to-right reading, you can define a helper:

```js
function pipe(source, ...stages) {
  return stages.reduce((iter, stage) => stage(iter), source);
}

const result = pipe(
  readLinesSync('access.log'),
  iter => filter(iter, l => l.includes('ERROR')),
  iter => map(iter, l => l.split(' ')[0]),
  iter => take(iter, 10),
);
```

## Step-by-step dry run

`access.log` has 1,000,000 lines. 50,000 contain `"ERROR"`. We want the first 10 ERROR IPs.

- `for (const ip of pipeline)` calls `pipeline.next()` (which is `take`'s generator).
- `take.next()` calls `for (const x of iter)` → `map.next()`.
- `map.next()` calls `filter.next()`.
- `filter.next()` calls `readLinesSync.next()` → reads buffer 1, yields line 1.
- `filter` checks `line.includes('ERROR')` → most lines false. It calls `readLinesSync.next()` again, again, again — driving the source — until it finds an ERROR line at, say, line 247.
- Yields line 247 to `map`.
- `map` calls `line.split(' ')[0]` → `"10.0.0.5"`. Yields to `take`.
- `take` decrements counter (10 → 9), yields `"10.0.0.5"` to `for...of`.
- `console.log('10.0.0.5')`.
- Loop iterates. Each iteration drives the source until one more ERROR line is found.
- After 10 ERROR lines have been emitted, `take`'s counter hits 0. `take` calls `return`, which terminates the `take` generator.
- The `for...of` loop exits. The `take` generator's cleanup runs (none here).
- Critically: `readLinesSync` is suspended mid-read with the file descriptor open. When the `take` generator is garbage-collected (or when the consumer triggers `.return()` via early exit), the **`finally` block** in `readLinesSync` runs and closes the fd.

Net: we read maybe ~10,000 source lines (depending on ERROR distribution), not 1,000,000. Memory is O(1). The file descriptor is correctly closed via `try/finally`.

## Important takeaways

**Syntax to memorize**
- `function*` declares a generator. `yield x` produces a value. `yield* gen()` delegates.
- Generators implement both `Iterator` AND `Iterable` (their `[Symbol.iterator]()` returns themselves). They plug into `for...of`, spread, destructuring.
- Stage helpers: `map`, `filter`, `take`, `flatMap` — all four-liners.
- `try/finally` inside the generator is your cleanup hook. Critical for resource-holding sources.

**Patterns to reuse**
- "Unix pipes in JS" — same mental model. Each stage is a process, each `yield` is a pipe.
- This pattern naturally lifts to **async generators** (`async function*`, `for await`) for I/O-bound pipelines. Same shape, async semantics.
- The same composed-iterable pattern powers RxJS-lite, Highland.js, and Node's `readable.iterator()`.
- Once you have a generator pipeline, `Readable.from(gen)` (or `Readable.from(asyncGen)`) lifts it into a Node stream that plugs into `stream.pipeline`.

**Common mistakes**
- Materializing intermediates with `[...]` or `Array.from(...)` between stages — destroys the memory benefit.
- Forgetting `try/finally` in the source generator — leaks file descriptors, DB connections, etc. on early `break`.
- Using array methods (`.map`, `.filter`) for huge data sources — same logic but eager and array-allocating.
- Trying to reuse an exhausted generator. Always returns `{ done: true }`. Wrap in a thunk if needed.
- Mixing sync generators with async I/O — you'll get sync-but-blocking code or hit "yield can't await." For async I/O, use `async function*`.

**Related questions**
- `callback-API-to-async-iterator` — async generator version of source stage.
- `transform-line-parser` — same line-splitting idea as a Node Transform stream.
- `pipeline-error-propagation` — `pipeline(asyncGen, transform, dest)` is the async-stream analog.

## Variants

1. **Async generator pipeline** — "Make every stage `async function*` so the source can do async I/O (HTTP, DB queries)." Same skeleton; `for...of` becomes `for await...of`. Composes with `stream.pipeline` since Node 12.

2. **Reverse direction — push-based observers** — "Build the same pipeline but with push semantics (observer pattern)." Contrast: pull (generators) gives backpressure for free; push (observers) requires explicit buffering. Pull wins for data pipelines, push wins for events.

3. **Implement `pipe(source, ...stages)`** — "Write the left-to-right composition helper." 3-liner with `reduce` (shown above). Demonstrates functional fluency.

## Revision notes

> **generator-pipeline — 60 second recap**
> - `function*` + `yield` = lazy iterator. `for...of` drives it one value at a time.
> - Stage primitives: `map(iter, fn)`, `filter(iter, fn)`, `take(iter, n)`, `flatMap(iter, fn)`.
> - Compose by function calling: `take(map(filter(source, p), f), 10)`. Or use a `pipe()` helper for left-to-right.
> - Memory: O(1) per stage. Source isn't fully read if `take` ends early.
> - **Trap:** `[...gen]` materializes everything — kills the streaming benefit.
> - **Trap:** No `try/finally` in source = fd leak on `break`.
> - Generators are single-use, sequential, sync. For I/O, lift to `async function*` + `for await`.
> - Composes with `Readable.from(gen)` to plug into Node `stream.pipeline`.
> - Mental model: **Unix pipes in JS**.
