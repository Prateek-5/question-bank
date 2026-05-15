# Async iterator over a paginated API (`Symbol.asyncIterator` + `for await`)

## Source
- Canonical Node.js / TC39 pattern (used by AWS SDK v3 paginators, MongoDB cursors, Kafka consumers).
- LeetCode-style follow-up to "Generate Fibonacci Sequence" but I/O-bound.

## Why this question matters in interviews
This is THE async-iteration question for backend engineers. Every modern Node service touches a paginated source: S3 `ListObjectsV2`, DynamoDB `Scan`, Github API `?page=`, internal REST endpoints with `nextCursor`. The interview test: "Wrap a paginated REST API so the consumer can write `for await (const item of api) { ... }` without thinking about pages." Done right, the answer demonstrates: (a) `Symbol.asyncIterator` + `next()` returning a Promise, (b) lazy fetching — pages are pulled on demand, not pre-loaded, (c) memory stays O(pageSize), (d) clean integration with `Readable.from(...)` and `pipeline`. Bonus points for `AbortSignal` and error propagation.

## Concepts involved

### The async-iterator protocol
Just like sync, but `next()` returns a Promise of `{ value, done }`.
```js
const asyncIter = {
  async next() { return { value: x, done: false }; }
};
const asyncIterable = {
  [Symbol.asyncIterator]() { return asyncIter; }
};
for await (const x of asyncIterable) { /* awaits each next() */ }
```

### `for await ... of` desugar
```js
for await (const x of obj) { body }
// equivalent to:
const it = obj[Symbol.asyncIterator]();
while (true) {
  const { value, done } = await it.next();
  if (done) break;
  body;
}
```
Crucially, `await it.next()` means each iteration pauses for I/O — perfect for paginated fetches.

### `async function*` — the sugar
You almost never write `Symbol.asyncIterator` by hand any more. Use an async generator:
```js
async function* paginate(url) {
  let cursor = null;
  do {
    const { items, nextCursor } = await fetchPage(url, cursor);
    for (const item of items) yield item;
    cursor = nextCursor;
  } while (cursor);
}
for await (const item of paginate('https://api.example.com')) { /* ... */ }
```
This is what the AWS SDK v3 generates for every paginated operation.

### Node streams as async iterables
Every `Readable` in Node 12+ is already an async iterable. That's why `for await (const chunk of fs.createReadStream(...))` works. Conversely, `Readable.from(asyncGenerator())` converts your async generator into a full Node stream — so it plugs into `pipeline`.

### Errors propagate through `await`
If the API call throws, the `await` inside the generator rejects, which bubbles out of `for await` as a normal exception. Use try/catch around the loop.

### Cancellation with `AbortSignal`
Pass `signal` into your `fetch` call. The consumer can abort, which rejects the in-flight `await`, which bubbles out as `AbortError`.

## Brute force approach
Loop and `push` all pages into an array, then iterate the array. Defeats the entire point — for a 1M-item dataset you OOM. Also blocks the consumer until *every* page is fetched, instead of overlapping consumption with the next fetch.

## Optimal approach
Implement `[Symbol.asyncIterator]()` returning an object whose `next()` fetches the next page lazily and serves items from a local buffer. Or — cleaner — use `async function*` and `yield` items one at a time. Both have identical semantics; the async generator is 8 lines, the manual class is 30.

## Solution (JavaScript)

```js
'use strict';

/**
 * Wrap a cursor-paginated API as an async iterable.
 * Items are fetched one page at a time, on demand. Memory: O(pageSize).
 *
 * @param {(cursor: string|null, signal?: AbortSignal) => Promise<{items: T[], nextCursor: string|null}>} fetchPage
 * @param {{ signal?: AbortSignal }} [opts]
 * @returns {AsyncIterable<T>}
 */
function paginate(fetchPage, { signal } = {}) {
  return {
    [Symbol.asyncIterator]() {
      let buffer = [];
      let cursor = null;
      let done = false;

      return {
        async next() {
          while (buffer.length === 0 && !done) {
            signal?.throwIfAborted();
            const page = await fetchPage(cursor, signal);
            buffer = page.items;
            cursor = page.nextCursor;
            if (!cursor) done = true;
          }
          if (buffer.length === 0) return { value: undefined, done: true };
          return { value: buffer.shift(), done: false };
        },
        async return(value) {        // called on `break` / `throw` in for-await
          done = true;
          buffer = [];
          return { value, done: true };
        },
      };
    },
  };
}

// Generator equivalent — same semantics, 1/4 the code.
async function* paginateGen(fetchPage, { signal } = {}) {
  let cursor = null;
  do {
    signal?.throwIfAborted();
    const { items, nextCursor } = await fetchPage(cursor, signal);
    for (const item of items) yield item;
    cursor = nextCursor;
  } while (cursor);
}

// ---- Demo with a fake paginated API ---------------------------------------
async function fakeApi(cursor /* , signal */) {
  const pages = {
    null: { items: [1, 2, 3], nextCursor: 'p2' },
    p2:   { items: [4, 5, 6], nextCursor: 'p3' },
    p3:   { items: [7, 8, 9], nextCursor: null  },
  };
  await new Promise((r) => setTimeout(r, 20));   // simulate latency
  return pages[cursor ?? 'null'];
}

(async () => {
  const ac = new AbortController();
  setTimeout(() => ac.abort(new Error('timeout')), 1000);

  try {
    for await (const item of paginateGen(fakeApi, { signal: ac.signal })) {
      console.log(item);            // 1, 2, 3, 4, 5, 6, 7, 8, 9
      if (item === 5) break;        // consumer can bail early — generator cleanup runs
    }
  } catch (err) {
    if (err.name === 'AbortError') console.log('cancelled');
    else throw err;
  }
})();

// Bonus: plug into a Node pipeline.
const { Readable } = require('node:stream');
const { pipeline } = require('node:stream/promises');
const { Writable } = require('node:stream');

await pipeline(
  Readable.from(paginateGen(fakeApi)),    // async iterable → Node Readable
  new Writable({
    objectMode: true,
    write(item, _enc, cb) { console.log('got', item); cb(); },
  }),
);
```

## Step-by-step dry run

`for await (const item of paginateGen(fakeApi))` — fake API has 3 pages of 3 items.

| Tick | Generator state | Network | Consumer sees |
| --- | --- | --- | --- |
| 1 | enters body, cursor=null, awaits `fetchPage(null)` | request page 1 | — |
| 2 | resolves `{ items:[1,2,3], next:'p2' }`. Loops over items, yields 1 | — | 1 |
| 3 | next iter pull → yields 2 | — | 2 |
| 4 | next iter pull → yields 3 | — | 3 |
| 5 | for-loop done, outer do-while continues. cursor='p2', awaits next page | request page 2 | — |
| 6 | yields 4, 5, 6 | — | 4, 5, 6 |
| 7 | cursor='p3', awaits next page | request page 3 | — |
| 8 | yields 7, 8, 9 | — | 7, 8, 9 |
| 9 | cursor=null → loop exits → generator returns | — | done |

**Critical:** only 1 page (3 items) sits in memory at a time. Network calls are interleaved with consumption. If the consumer is slow, the next fetch is held back.

**If consumer `break`s on item 5:** the `for await` loop calls `return()` on the generator. The generator runs any `try/finally` and terminates. No 3rd page is fetched — bandwidth saved.

**If abort fires after item 5:** the in-flight `fetchPage(p2)` rejects with `AbortError`, the generator rejects, the `for await` rejects → caught by our try/catch.

## Important takeaways

**Syntax to memorize**
- `[Symbol.asyncIterator]()` — note the lowercase `asyncIterator`, not `AsyncIterator`.
- `async function*` — combine the two modifiers in this exact order.
- `for await (const x of obj)` — only valid inside async functions (or top-level await in ESM).
- `Readable.from(asyncIterable)` — instant bridge to Node streams.

**Patterns to reuse**
- Wrapping any cursor source: DynamoDB `Scan`, MongoDB `find()`, Postgres cursor, Kafka consumer, GitHub/Linear/Notion REST pagination.
- Streaming aggregations: `for await (const row of paginate(api)) { agg.add(row); }` — process unbounded data in O(1) memory.
- Bridging async-iter ↔ Node streams via `Readable.from` and `for await` directly on streams.

**Common mistakes**
- Pre-fetching all pages into an array — defeats laziness, OOMs on large datasets.
- Returning `done: true` *with* a non-null value — `for await ... of` ignores it. Only `.return()`-style callers see it.
- Forgetting `return()` cleanup — if the consumer breaks, you may keep fetching pages in the background. With `async function*` this is automatic (the generator gets `return()` for free); with manual classes you have to write it.
- Mixing in microtasks: `for await` awaits each iteration, so a slow consumer naturally throttles the source. Don't `Promise.all` the body unless you want unbounded concurrency.
- Forgetting that errors inside `next()` reject the for-await loop — wrap in try/catch.
- Not threading `AbortSignal` through to the underlying fetch — abort doesn't cancel an in-flight network call without it.

**Related**
- `fibonacci-generator.md` — the sync cousin (`function*`).
- `custom-iterator.md` — the underlying iterator protocol.
- `readable-stream-push.md` — Node streams ARE async iterables; you can also produce them from an async generator.
- `stream-pipeline-lab.md` — wire a paginated source into a transform/sink chain.

## Variants

1. **Concurrent pagination (controlled prefetch)** — instead of strict "fetch next page on demand," prefetch the next page while the consumer drains the current. Useful when network latency > consumption time. Implement with a small queue + a semaphore. Watch out: abort semantics get harder.

2. **`.toArray()` / `.take(n)` helpers** — TC39 has Iterator Helpers stable in 2025; AsyncIterator Helpers are stage-3 (`AsyncIterator.prototype.toArray`, `.take`, `.map`, etc). Mention this if asked "how would you make this chainable?" — runtime-dependent but landing soon.

3. **Resumable pagination** — accept a `startCursor` so the iterator can resume after a crash. Combine with checkpoint-after-batch in your consumer for at-least-once processing semantics.

## Revision notes

> **async iterator pagination — 60 second recap**
> - Protocol: `[Symbol.asyncIterator]()` returns iter whose `next()` returns `Promise<{value, done}>`.
> - Sugar: `async function*` — yields one item at a time, `await` inside is allowed.
> - `for await (const x of asyncIterable)` consumes; one-at-a-time backpressure for free.
> - Memory: O(pageSize), not O(totalItems). Pages are pulled on demand.
> - Node streams ARE async iterables — and `Readable.from(asyncIterable)` works in reverse.
> - Errors thrown inside the generator reject the `for await`; catch with try/catch.
> - Pass `AbortSignal` through to fetch + `signal?.throwIfAborted()` inside the loop.
> - Consumer `break` → `.return()` runs → generator's `try/finally` cleans up.
> - Trap: pre-loading all pages. Trap: forgetting to thread `signal`. Trap: ignoring early-exit cleanup.
