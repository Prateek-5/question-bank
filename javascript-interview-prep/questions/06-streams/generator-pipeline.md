# Generator pipeline — Unix pipes in JS

> **Difficulty:** Medium-Senior   |   **Time:** ~15 min   |   **Prereqs:** [fibonacci-generator.md](./fibonacci-generator.md), [custom-iterator.md](./custom-iterator.md)
>
> **Source:** ETL pipelines, functional Node. Modern alternative to `Array.prototype.map().filter().slice()` chains for large data.

---

## 1. Problem statement

Compose `function*` stages into a pipeline: source → filter → map → take → consumer. O(1) memory per stage.

**Verification examples**

```js
function* map(iter, fn)    { for (const x of iter) yield fn(x); }
function* filter(iter, fn) { for (const x of iter) if (fn(x)) yield x; }
function* take(iter, n)    { for (const x of iter) { if (n-- <= 0) return; yield x; } }

// Unix: cat log | grep ERROR | awk '{print $1}' | head -10
const pipeline = take(map(filter(readLines('log'), l => l.includes('ERROR')), l => l.split(' ')[0]), 10);
for (const ip of pipeline) console.log(ip);
```

**Constraints**
- Each stage is `function*`.
- No intermediate arrays — O(1) per stage.
- `for...of` drives pulls; `take` stops the chain.
- `try/finally` in source for resource cleanup.

---

## 2. Plain-English restatement

Generators chain like Unix pipes. Each stage yields one value at a time; the consumer pulls from the end, which pulls back through the chain. Memory is constant — one value in flight per stage.

---

## 3. Why this matters in interviews

Senior backend literacy. ETL, log processing, JSON Lines parsing. The mental model behind RxJS, Highland, Node streams.

---

## 4. Mental model

```
   Unix pipes in JS:
   
   cat log | grep ERROR | awk '{print $1}' | head -10
   
   becomes:
   
   take(map(filter(readLines('log'), isError), firstField), 10)
   ↑     ↑   ↑                                              ↑
   sink  stage stage                                       limit
   
   Pull model:
   - for...of drives pulls.
   - take pulls from map; map pulls from filter; filter pulls from source.
   - One value flows through pipeline per iteration.
   - Memory O(1) per stage.
   
   Backpressure FREE:
   - Downstream pulls when ready. If take stops at 10, upstream stops.
   - readLines never reads more source than needed.
   
   Cleanup:
   - Source uses try/finally to close fds on early termination.
   - for...of break → calls .return() on chain → propagates up.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why does `take(map(filter(source, p), f), 10)` not materialize the whole source?
> 2. What happens when consumer `break`s mid-loop?
> 3. Where do you put `try/finally` for resource cleanup?

---

## 6. Brute force — walked through

### Wrong attempt 1: chain array methods
`.filter().map().slice()` — each method materializes intermediate array; O(n) memory.

### Wrong attempt 2: spread between stages
`[...filter(...)]` defeats laziness.

### Wrong attempt 3: forget `try/finally`
Early break leaks file descriptor.

---

## 7. The unlocking insight

> **Each `function*` stage pulls from previous; composes via function calls. O(1) memory; backpressure free via pull model. `try/finally` in source for cleanup.**

Three properties:

1. **Pull model** — consumer drives.
2. **Lazy composition** — no work until pulled.
3. **Cleanup via `try/finally`** in source.

---

## 8. Solution (annotated)

```js
const fs = require('fs');

// Stage primitives
function* map(iter, fn)    { for (const x of iter) yield fn(x); }
function* filter(iter, fn) { for (const x of iter) if (fn(x)) yield x; }
function* take(iter, n)    { for (const x of iter) { if (n-- <= 0) return; yield x; } }
function* flatMap(iter, fn){ for (const x of iter) yield* fn(x); }

// Source with cleanup
function* readLinesSync(path) {
  const fd = fs.openSync(path, 'r');                                     // step 1: open
  try {
    const buf = Buffer.alloc(64 * 1024);
    let tail = '';
    let bytes;
    while ((bytes = fs.readSync(fd, buf, 0, buf.length, null)) > 0) {
      const text = tail + buf.toString('utf8', 0, bytes);
      const lines = text.split('\n');
      tail = lines.pop();
      for (const line of lines) yield line;                              // step 2: yield
    }
    if (tail.length) yield tail;
  } finally {
    fs.closeSync(fd);                                                    // step 3: ALWAYS close
  }
}

// Compose
const pipeline = take(
  map(
    filter(readLinesSync('access.log'), (l) => l.includes('ERROR')),
    (l) => l.split(' ')[0],
  ),
  10,
);

for (const ip of pipeline) console.log(ip);

// Or left-to-right
function pipe(source, ...stages) {
  return stages.reduce((iter, stage) => stage(iter), source);
}
const result = pipe(
  readLinesSync('access.log'),
  (iter) => filter(iter, (l) => l.includes('ERROR')),
  (iter) => map(iter, (l) => l.split(' ')[0]),
  (iter) => take(iter, 10),
);
```

**Try it yourself**

```js
// Compose tree traversal via yield*
function* inorder(node) {
  if (!node) return;
  yield* inorder(node.left);
  yield node.value;
  yield* inorder(node.right);
}

const tree = { value: 2, left: { value: 1 }, right: { value: 3 } };
[...inorder(tree)];                                                       // [1, 2, 3]

// Composes with for await for async sources
async function* fetchLines(url) { /* yield lines from chunked HTTP */ }
async function* asyncMap(iter, fn) { for await (const x of iter) yield fn(x); }
```

---

## 9. Step-by-step dry run

```
Pipeline: take(map(filter(readLinesSync('log'), isError), firstField), 10)
Source has 1M lines, 50k contain ERROR.

for (const ip of pipeline):
  Iteration 1:
    pipeline.next() → take.next()
    take asks map.next() → asks filter.next() → asks readLinesSync.next()
    readLinesSync yields line 1.
    filter: line 1 has ERROR? no. asks again. line 2. ... line 247 has ERROR.
    filter yields line 247.
    map: line.split(' ')[0] = '10.0.0.5'. yields to take.
    take: counter 10 → 9. yields '10.0.0.5' to for..of.
    Print '10.0.0.5'.
  
  ... continues until take counter hits 0.
  
After take counter 0: take returns. Chain unwinds. readLinesSync still suspended with fd open.
When pipeline gets GC'd OR for...of calls .return() on early exit, readLinesSync's finally runs → fs.closeSync(fd).

Total source reads: ~10k lines (depending on ERROR distribution), not 1M.
Memory: O(1) per stage.
```

---

## 10. Common confusion + traps

1. **Materialize between stages** — `[...filter(...)]` kills laziness.
2. **Array methods** — eager; allocate intermediates.
3. **Forget `try/finally`** in source — fd leak on early break.
4. **Reuse exhausted generator** — always done.
5. **Mix sync + async** — sync `function*` can't `await`.
6. **`yield` outside `function*`** — syntax error.
7. **Throwing in stage** — propagates; downstream sees `done`.

---

## 11. Senior follow-ups & variants

### Variant 1 — Async generator pipeline
`async function*` + `for await` for I/O sources.

### Variant 2 — Push-based (observers)
Pull (generators) gives backpressure for free; push requires explicit buffering.

### Variant 3 — `pipe(source, ...stages)` helper
Left-to-right composition via reduce.

### Variant 4 — `Readable.from(gen())`
Lift generator into Node stream for `pipeline()` integration.

### Variant 5 — Iterator helpers (TC39 stage-4)
`source().filter().map().take().toArray()` natively.

---

## 12. How to think aloud

> "Generators chain like Unix pipes. Each stage is a `function*` that pulls from the previous iterable and yields transformed values. `take(map(filter(source, p), f), 10)` reads bottom-up at construction (no work yet); execution happens when consumer pulls. `for...of` at the sink drives pulls back through the chain. Memory O(1) per stage — only one value in flight. Source `try/finally` for cleanup (close file descriptor, DB cursor). For...of's `break` triggers `.return()` on chain — propagates up. For I/O-bound sources, switch to `async function*` + `for await...of` — same shape, async semantics. Compose with `Readable.from(asyncGen)` to plug into Node `stream.pipeline`. Trap: materializing intermediates (`[...filter(...)]`); using array methods (eager); forgetting try/finally; reusing exhausted generators."

---

## 13. 60-second revision

> - **`function*` stages** chain like Unix pipes.
> - **Pull model:** consumer drives; backpressure free.
> - **O(1) memory** per stage — no intermediate arrays.
> - **`try/finally` in source** for resource cleanup.
> - **`for...of` break** → `.return()` → cleanup propagates.
> - **`yield*` delegates** (tree traversal).
> - **Lift to async:** `async function*` + `for await`.
> - **`Readable.from(gen())`** for Node streams.
> - **Trap:** spread between stages; array methods; forget try/finally.

---

**Related:** [fibonacci-generator.md](./fibonacci-generator.md) · [custom-iterator.md](./custom-iterator.md) · [async-iterator-pagination.md](./async-iterator-pagination.md) · [transform-line-parser.md](./transform-line-parser.md) · [pipeline-error-propagation.md](./pipeline-error-propagation.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
