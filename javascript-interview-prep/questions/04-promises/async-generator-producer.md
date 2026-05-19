# Async generator as a producer — pull-based streaming with backpressure

> **Difficulty:** Medium-Hard   |   **Time:** ~30 min   |   **Prereqs:** [`concepts/promises.md`](../../concepts/promises.md), [sequential-vs-parallel-async-map.md](./sequential-vs-parallel-async-map.md)
>
> **Source:** ES2018 async generators + `for await...of`. Used in Node `fs.createReadStream` async iter, Web Streams, RxJS bridges.

---

## 1. Problem statement

**Signature**
```ts
async function* fetchPages(baseUrl: string, signal?: AbortSignal): AsyncGenerator<Item>;
async function* eventToIter(emitter, eventName: string, opts?: { signal?: AbortSignal }): AsyncGenerator<any>;
```

**Input / Output examples**

| Setup                                                          | Behaviour                                              |
|----------------------------------------------------------------|---------------------------------------------------------|
| Paginated API → async generator                                | yields one item at a time; cursor advanced lazily      |
| `for await (item of gen) { await process(item) }`              | backpressure: producer waits while consumer is busy    |
| `break` from `for await`                                       | triggers `iter.return()` → runs `try/finally` cleanup  |
| Event emitter → async iterator                                  | buffers when consumer is slow; drains on idle          |
| Producer awaiting long fetch + consumer dies                    | resources released via `finally`                       |

**Constraints**
- Backpressure is **automatic** — producer only advances on consumer `next()`.
- Cleanup via `try { yield } finally { ... }` runs on `break`, `return`, or `throw`.
- Sequential by nature; wrap with pool for parallel.
- Thread `AbortSignal` at every yield boundary for cancellation.

---

## 2. Plain-English restatement

An async generator (`async function*`) is a function that yields values over time. Each `yield` suspends the function until the consumer calls `next()` (typically via `for await...of`). This gives you **automatic backpressure**: if the consumer is slow processing each item, the producer doesn't run ahead. Perfect for paginated APIs, event emitters, streaming reads — anywhere you want to consume values one at a time without buffering them all in memory.

---

## 3. Why this matters in interviews

Async generators are the cleanest way to model "produce values over time, asynchronously, with backpressure." Each `yield` is a suspension point; the consumer's `next()` resumes it. The interview ask is usually: "Implement a paginated API reader as an async iterable" or "Wrap an event emitter as an async iterator." Senior bar: you grasp that backpressure is *automatic* (the producer only advances when the consumer pulls), and you handle cleanup via `return()`/`throw()` properly.

---

## 4. Mental model

A **water tap controlled by the cup**:

```
   producer (async gen):
   ┌──────────────────────────────┐
   │ while (more):                │
   │   page = await fetch(...)    │
   │   for each item:             │
   │      yield item   ────┐      │
   └───────────────────────┘──────┘
                            │ suspended here until next()

   consumer (for await):
   ┌──────────────────────────────┐
   │ for await (item of iter):    │
   │   await process(item)        │
   │   (when done, next() called) │
   └──────────────────────────────┘
```

The producer never runs ahead — it only computes the next value when the consumer asks. This is the **opposite** of an event emitter, which pushes whether or not anyone is listening.

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. If the consumer breaks out of `for await` early, how does the producer's `try/finally` get a chance to run?
> 2. Does the producer fetch the next page eagerly or lazily?
> 3. How do you cancel an async generator mid-flight?

---

## 6. Brute force — walked through

### Wrong attempt 1: eager fetch all pages
```js
async function fetchAll(url) {
  const all = [];
  let cursor = null;
  do {
    const page = await fetch(url + (cursor ? `?cursor=${cursor}` : '')).then(r => r.json());
    all.push(...page.items);
    cursor = page.nextCursor;
  } while (cursor);
  return all;
}
```

Loads everything into memory. OOM on big datasets. Use async generator for streaming.

### Wrong attempt 2: no try/finally
Producer holds a DB connection / file handle. Consumer `break`s. Resource never released. Leak.

### Wrong attempt 3: forget AbortSignal
Long-running fetch cannot be cancelled. Consumer aborts but generator keeps producing.

---

## 7. The unlocking insight

> **`async function*` + `yield` = pull-based streaming with automatic backpressure. `try { yield } finally { cleanup }` runs on any exit path. Thread `AbortSignal` at each yield boundary for cancellation.**

Three properties:

1. **Backpressure free** — `yield` suspends until consumer `next()`. No buffering by default.
2. **`break` triggers `iter.return()`** — async generators give you a chance to `try { yield } finally { cleanup }`.
3. **AbortSignal at each yield boundary** — check `signal.aborted` before each `yield` for cancellation.

---

## 8. Solution (annotated)

```js
// Paginated API as async iterable
async function* fetchPagesIter(baseUrl, { signal, pageSize = 100 } = {}) {
  let cursor = null;
  let conn = await openConnection();                       // step 1: resource
  try {
    while (true) {
      if (signal?.aborted) throw signal.reason ?? new Error('Aborted');
      const url = `${baseUrl}?limit=${pageSize}${cursor ? `&cursor=${cursor}` : ''}`;
      const page = await conn.fetch(url);
      for (const item of page.items) {
        if (signal?.aborted) throw signal.reason ?? new Error('Aborted');
        yield item;                                          // step 2: suspend until next()
      }
      if (!page.nextCursor) return;
      cursor = page.nextCursor;
    }
  } finally {
    await conn.close();                                      // step 3: cleanup on ANY exit
  }
}

// Bridge an event emitter to an async iterator
async function* eventToIter(emitter, eventName, { signal } = {}) {
  const queue = [];
  let resolveNext;
  const push = (v) => {
    if (resolveNext) { resolveNext(v); resolveNext = null; }
    else queue.push(v);
  };
  emitter.on(eventName, push);
  try {
    while (true) {
      if (signal?.aborted) return;
      const v = queue.length
        ? queue.shift()
        : await new Promise((r) => resolveNext = r);
      yield v;
    }
  } finally {
    emitter.off(eventName, push);                           // listener cleanup
  }
}
```

**Try it yourself**

```js
const ac = new AbortController();
setTimeout(() => ac.abort(), 5000);

for await (const item of fetchPagesIter('/api/users', { signal: ac.signal })) {
  await process(item);                                       // backpressure
  if (shouldStop(item)) break;                              // triggers finally cleanup
}
```

---

## 9. Step-by-step dry run

```
gen.next()         → producer enters; conn opened
                   → fetch page1 → items [1..4]; nextCursor='p2'
                   → yield 1 (suspend)
consumer gets 1, processes (1s)
gen.next()         → resume; yield 2 (suspend)
... yield 3, 4
gen.next()         → fetch page2 (cursor='p2') → items [5..8]
                   → yield 5 (suspend)
consumer sees item 5 → shouldStop → break
                   → for-await calls iter.return() → resumes generator
                   → finally: conn.close()
                   → return { value: undefined, done: true }
```

Resource released regardless of when consumer bailed.

---

## 10. Common confusion + traps

1. **"Async iter is slow"** — overhead is microsecond-scale; only slow if producer is slow.
2. **"I need a buffer"** — backpressure is automatic; producer waits for `next()`.
3. **"How do I cancel?"** — `break` triggers cleanup; or thread `AbortSignal`.
4. **"It's just a generator with await"** — `next()` returns `Promise<{value, done}>` not `{value, done}`.
5. **"`yield`s run in parallel"** — sequential; wrap with pool for fanout.
6. **No try/finally** → resource leaks on break/throw.
7. **No `AbortSignal` checks** → can't cancel mid-flight.

---

## 11. Senior follow-ups & variants

### Variant 1 — Buffered async generator
Buffer N items ahead (eager fetch one page while consumer processes). Trades latency for throughput.

### Variant 2 — Multi-source merge
Async-iter A, B, C → one merged stream. Use `Promise.race` of pending `next()` calls.

### Variant 3 — Backpressure-aware emitter bridge
Pause underlying emitter when queue exceeds high-water mark.

### Variant 4 — Async-to-sync collect
`for await ... { results.push(item) }` then return array (when total is small).

---

## 12. How to think aloud

> "Async generator gives me pull-based streaming. Each `yield` suspends; the consumer's `next()` (or `for await`) resumes. Backpressure is automatic — producer doesn't run ahead. Resources go in try/finally inside the gen — `break` from the consumer triggers `return()`, which runs the finally. For paginated APIs: outer while loop on cursor, inner for-of on items, yield each. AbortSignal threaded — check before yields. For cancellable cancellation, `for await ... { if (cond) break; }` is idiomatic."

---

## 13. 60-second revision

> - **Backpressure is free.** `yield` suspends until consumer pulls.
> - **`try { yield } finally { cleanup }`** runs on any exit (break, return, throw).
> - **`break` triggers `iter.return()`** — that's how cleanup runs.
> - **AbortSignal at each yield boundary** for cancellation.
> - **Sequential by nature** — wrap with async pool for parallel.
> - **Bridge event emitter** via internal queue + waiting Promise pattern.
> - **Family:** Node streams, Web Streams, RxJS observables, paginated APIs.
> - **Trap:** no try/finally → resource leaks; no AbortSignal check → can't cancel.

---

**Related:** [`concepts/streams.md`](../../concepts/streams.md) · [`06-streams/async-iterator-pagination.md`](../06-streams/async-iterator-pagination.md) · [`06-streams/generator-pipeline.md`](../06-streams/generator-pipeline.md) · [abortcontroller-fanout.md](./abortcontroller-fanout.md)

**Concept primer:** [`concepts/promises.md`](../../concepts/promises.md)
