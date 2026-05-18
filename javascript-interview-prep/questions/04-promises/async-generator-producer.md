# Async Generator as a Producer (Pull-Based Streaming)

## Source / Origin
- ES2018 async generators + `for await...of`.
- Used in: Node `fs.createReadStream` async iter, Web Streams, RxJS bridges.
- Asked at: Cloudflare, Stripe, Atlassian.
- Concept reference: `concepts/streams.md`, sibling `concepts/promises.md`.

## Why this question matters in interviews
Async generators are the cleanest way to model "produce values over time, asynchronously, with backpressure." Each `yield` is a suspension point; the consumer's `next()` resumes it. The interview ask is usually: "Implement a paginated API reader as an async iterable" or "Wrap an event emitter as an async iterator." Senior bar: you grasp that backpressure is *automatic* (the producer only advances when the consumer pulls), and you handle cleanup via `return()`/`throw()` properly.

## Concepts involved

### Syntax to lock in
```js
// Simplest async generator
async function* range(start, end) {
  for (let i = start; i < end; i++) {
    yield i;          // suspend until consumer pulls
  }
}

// Paginated API as async iterable (cursor pattern)
async function* fetchPages(baseUrl, signal) {
  let cursor = null;
  while (true) {
    const url = cursor ? `${baseUrl}?cursor=${cursor}` : baseUrl;
    const res = await fetch(url, { signal });
    const page = await res.json();
    for (const item of page.items) yield item;
    if (!page.nextCursor) return;
    cursor = page.nextCursor;
  }
}

// Consumer
for await (const item of fetchPages('/users')) {
  await process(item);                    // backpressure: producer waits while we process
  if (shouldStop(item)) break;            // break triggers `return()` on the iterator → cleanup
}
```

### Edge cases / interview traps
1. **`break` calls `return()`** on the iterator — async generators give you a chance to `try { yield } finally { cleanup }`. Use it to release resources.
2. **Errors propagate.** `throw` inside a generator rejects the consumer's `next()`. The consumer's `for await` will re-throw.
3. **`return()` from outside** — if a consumer calls `iter.return()`, the next `await` inside the generator yields immediately (well, finishes its current suspension) and runs `finally`.
4. **Backpressure is implicit.** The generator's next `yield` only resolves when consumer calls `next()`. No buffering needed by default.
5. **Concurrency: NOT parallel.** Producer is single-flight. To parallelize, wrap N generators with `Promise.race` or use an async pool around it.
6. **Mixing async-iter with `Promise.all`** — feels wrong; you want sequential pull-based consumption.
7. **Memory leak via dangling iterators.** If consumer abandons without `break` or `return()`, the generator may hang. Always finalize with try/finally inside the gen, or break.
8. **Throwing into a generator from outside** — `iter.throw(err)` injects an error at the suspension point; useful for signaling cancellation without an AbortSignal.

## Mental Model

A **water tap controlled by the cup**:

```
   producer (async gen):  ┌──────────────────────────────┐
                          │ while (more):                │
                          │   page = await fetch(...)    │
                          │   for each item:             │
                          │      yield item   ────┐      │
                          └───────────────────────┘──────┘
                                                  │ suspended here until next()
                                                  │
   consumer (for await):  ┌──────────────────────────────┐
                          │ for await (item of iter):    │
                          │   await process(item)        │
                          │   (when done, next() called) │
                          └──────────────────────────────┘
```

The producer never runs ahead — it only computes the next value when the consumer asks. This is the opposite of an event emitter which pushes whether or not anyone is listening.

## Why interviewers care

- **Streaming + backpressure** in one primitive.
- **Resource lifecycle.** Try/finally inside the generator for cleanup.
- **API design.** Async iterables compose with `for await`, are easy to consume, support cancel.

## Common beginner confusion

- **"Async iter is slow."** It's only slow if your producer is slow; the iter overhead per yield is microsecond-scale.
- **"I need a buffer."** No — backpressure is automatic. The producer waits for `next()`.
- **"How do I cancel?"** `break` from the loop (triggers iterator's `return()`), or thread an `AbortSignal` and check it before each `yield`.
- **"It's just a generator with await."** Almost — but the `next()` return type is `Promise<{value, done}>` instead of `{value, done}`. That changes everything composability-wise.
- **"`yield`s run in parallel."** No — sequential. Use `Promise.all` if you want parallel work *inside* one tick.

## Brute force approach

```js
// Eager fetch — load entire dataset into memory
async function fetchAll(baseUrl) {
  const all = [];
  let cursor = null;
  do {
    const page = await fetch(baseUrl + (cursor ? `?cursor=${cursor}` : '')).then(r => r.json());
    all.push(...page.items);
    cursor = page.nextCursor;
  } while (cursor);
  return all;
}
// consume:
const all = await fetchAll(url);
for (const item of all) await process(item);  // OOM on big datasets
```

## Optimal approach

Async generator that yields each item; consumer's `for await` provides natural backpressure. Resources (sockets, file handles) released via try/finally inside the generator.

## Solution (JavaScript)

```js
async function* fetchPagesIter(baseUrl, { signal, pageSize = 100 } = {}) {
  let cursor = null;
  let conn = await openConnection();        // example resource
  try {
    while (true) {
      if (signal?.aborted) throw signal.reason ?? new Error('Aborted');
      const url = `${baseUrl}?limit=${pageSize}${cursor ? `&cursor=${cursor}` : ''}`;
      const page = await conn.fetch(url);
      for (const item of page.items) {
        if (signal?.aborted) throw signal.reason ?? new Error('Aborted');
        yield item;
      }
      if (!page.nextCursor) return;
      cursor = page.nextCursor;
    }
  } finally {
    await conn.close();                     // ALWAYS releases — break, throw, return
  }
}

// Bridge an event emitter to an async iterator
async function* eventToIter(emitter, eventName, { signal } = {}) {
  const queue = [];
  let resolveNext;
  const push = (v) => { if (resolveNext) { resolveNext(v); resolveNext = null; } else { queue.push(v); } };
  emitter.on(eventName, push);
  try {
    while (true) {
      if (signal?.aborted) return;
      const v = queue.length ? queue.shift() : await new Promise(r => resolveNext = r);
      yield v;
    }
  } finally {
    emitter.off(eventName, push);
  }
}
```

## Step-by-step dry run

`fetchPagesIter`: cursor pagination with 3 pages, consumer breaks on item #5 of page 2.

```
gen.next()         → producer enters; conn opened
                   → fetch page1 (cursor=null) → items [1..4]; nextCursor='p2'
                   → yield 1 (suspend)
consumer gets 1, processes
gen.next()         → resume; yield 2 (suspend)
... yield 3, 4
gen.next()         → finished inner for; fetch page2 (cursor='p2') → items [5..8]
                   → yield 5 (suspend)
consumer sees item 5 → shouldStop → break
                   → for-await calls iter.return() → resumes generator with "abort"
                   → finally: conn.close()
                   → return { value: undefined, done: true }
```

Resource released regardless of when consumer bailed.

## How to think aloud in the interview

> "Async generator gives me pull-based streaming. Each `yield` suspends; the consumer's `next()` (or `for await`) resumes. Backpressure is automatic — producer doesn't run ahead. Resources go in try/finally inside the gen — `break` from the consumer triggers `return()`, which runs the finally. For paginated APIs: outer while loop on cursor, inner for-of on items, yield each. AbortSignal threaded — check before yields. For cancellable cancellation, `for await ... { if (cond) break; }` is idiomatic."

## Important takeaways

- **Backpressure is free.** `yield` suspends until consumer pulls.
- **Try/finally inside the generator** for cleanup on any exit (return, break, throw).
- **`break` triggers `iter.return()`** — that's how cleanup runs.
- **AbortSignal at each yield boundary** for cancellation.
- **Sequential by nature** — wrap with async pool if you need parallel.

## Variants

- **Buffered async generator** — buffer N items ahead (eager fetch one page while consumer processes the current). Trades latency for throughput.
- **Multi-source merge** — async-iter A, B, C → one merged stream. Use `Promise.race`.
- **Backpressure-aware emitter bridge** — pause the underlying EventEmitter when queue exceeds high-water mark.
- **Async-to-sync collect** — `for await ... { results.push(item) }` then return array (when total is small).

## Revision notes

```
async function* gen() { yield val }
for await (item of gen()): process(item)
  
  pull-based: producer waits for consumer's next()
  backpressure automatic
  try { yield } finally { cleanup } — runs on break/return/throw
  consumer break → iter.return() → triggers finally
  AbortSignal: check before each yield
  bridge emitter → queue + waiting Promise pattern
  not parallel; wrap with pool for fanout
```
