# Async iterator — paginated API via `Symbol.asyncIterator`

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [custom-iterator.md](./custom-iterator.md), [fibonacci-generator.md](./fibonacci-generator.md)
>
> **Source:** AWS SDK v3, MongoDB cursors, Kafka consumers. Canonical Node async-iteration question.

---

## 1. Problem statement

Wrap a cursor-paginated API as an async iterable. Consumer uses `for await...of`. Pages fetched lazily; memory O(pageSize).

**Verification examples**

```js
async function* paginate(fetchPage, { signal } = {}) {
  let cursor = null;
  do {
    signal?.throwIfAborted();
    const { items, nextCursor } = await fetchPage(cursor, signal);
    for (const item of items) yield item;
    cursor = nextCursor;
  } while (cursor);
}

for await (const item of paginate(api)) {
  console.log(item);
  if (item === 5) break;                                                  // generator cleanup runs
}
```

**Constraints**
- `[Symbol.asyncIterator]()` returns iterator whose `next()` returns Promise.
- `async function*` is the cleanest implementation.
- Pages fetched on demand — memory O(pageSize).
- Thread `AbortSignal` through fetch.

---

## 2. Plain-English restatement

`for await...of` lets consumers iterate one item at a time, awaiting each `next()`. Wrap a paginated API so callers don't think about pages. Backpressure for free — next page fetches when consumer is ready.

---

## 3. Why this matters in interviews

THE async-iteration question for backend. Every modern Node service touches paginated sources.

---

## 4. Mental model

```
   Async iterable: obj[Symbol.asyncIterator]() returns async iterator.
   Async iterator: next() returns Promise<{value, done}>.
   
   `for await (const x of obj) body`:
     it = obj[Symbol.asyncIterator]()
     while (true):
       {value, done} = await it.next()
       if done break
       body with value
   
   async function* paginate(fetchPage):
     let cursor = null;
     do {
       const page = await fetchPage(cursor);
       for (const item of page.items) yield item;
       cursor = page.nextCursor;
     } while (cursor);
   
   Memory: O(pageSize) — only one page in memory at a time.
   Backpressure: consumer's await throttles next fetch.
   
   Error propagation:
     fetchPage rejects → await throws → for await sees rejection.
   
   Cancellation:
     pass signal to fetchPage.
     consumer break → for await calls iterator.return() → finally runs in generator.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Is `Symbol.asyncIterator` different from `Symbol.iterator`?
> 2. Does `for await` await each `next()`?
> 3. What happens to in-flight fetch on consumer `break`?

---

## 6. Brute force — walked through

### Wrong attempt 1: preload all pages
OOM on large datasets.

### Wrong attempt 2: manual class with `[Symbol.asyncIterator]`
Works but verbose; `async function*` is 8 lines.

### Wrong attempt 3: ignore AbortSignal
Long-running fetches can't be cancelled.

---

## 7. The unlocking insight

> **`async function*` + `for await...of` = lazy paginated iteration. Each `await fetchPage` is one network call; `yield item` emits items one at a time. Memory O(pageSize). Pass `AbortSignal` for cancellation.**

Three properties:

1. **`async function*`** = clean implementation.
2. **`for await` awaits each `next()`** — natural backpressure.
3. **Errors propagate** via promise rejection.

---

## 8. Solution (annotated)

```js
async function* paginate(fetchPage, { signal } = {}) {                  // step 1: async generator
  let cursor = null;
  do {
    signal?.throwIfAborted();                                            // step 2: abort check
    const { items, nextCursor } = await fetchPage(cursor, signal);       // step 3: lazy fetch
    for (const item of items) yield item;                                 // step 4: yield one-by-one
    cursor = nextCursor;
  } while (cursor);
}

// Use
const ac = new AbortController();
setTimeout(() => ac.abort(new Error('timeout')), 5000);

try {
  for await (const item of paginate(fetchPage, { signal: ac.signal })) {
    console.log(item);
    if (item === stopValue) break;                                        // step 5: cleanup auto
  }
} catch (err) {
  if (err.name === 'AbortError') console.log('cancelled');
  else throw err;
}

// Plug into Node pipeline
const { Readable } = require('node:stream');
const { pipeline } = require('node:stream/promises');

await pipeline(
  Readable.from(paginate(fetchPage)),                                    // async iterable → stream
  transformStream,
  writableSink,
);
```

**Try it yourself**

```js
// Fake API
async function fakeApi(cursor) {
  const pages = {
    null: { items: [1, 2, 3], nextCursor: 'p2' },
    p2:   { items: [4, 5, 6], nextCursor: 'p3' },
    p3:   { items: [7, 8, 9], nextCursor: null },
  };
  await new Promise((r) => setTimeout(r, 100));
  return pages[cursor ?? 'null'];
}

for await (const item of paginate(fakeApi)) {
  console.log(item);                                                      // 1, 2, 3, 4, 5, 6, 7, 8, 9
}
// 3 network calls total; one page (3 items) in memory at a time.

// Aggregation
let total = 0;
for await (const order of paginate(fetchOrders)) {
  total += order.amount;
}
// Streaming reduce; memory O(1).
```

---

## 9. Step-by-step dry run

```
for await (const item of paginate(fakeApi)):

t=0    Enter generator body. cursor=null. await fetchPage(null) → suspended.
t=100  fetchPage resolves {items:[1,2,3], nextCursor:'p2'}.
       for-loop: yield 1.
       Consumer receives 1, processes, awaits next.
       yield 2. yield 3. inner loop done.
       cursor='p2'. await fetchPage('p2') → suspended.
t=200  resolves {items:[4,5,6], nextCursor:'p3'}.
       yield 4, 5, 6.
       cursor='p3'. await fetchPage('p3') → suspended.
t=300  resolves {items:[7,8,9], nextCursor:null}.
       yield 7, 8, 9.
       cursor=null. do-while exits. Generator returns.
       for await sees done.

Memory: at most ONE page (3 items) at a time.
Network: 3 calls total, sequenced.

Consumer break (e.g., at item 5):
  for await calls iterator.return() on generator.
  Generator's try/finally (if any) runs.
  In-flight await fetchPage rejects with AbortError (if signal threaded).
  Subsequent pages NOT fetched. Bandwidth saved.

Abort scenario:
  ac.abort() at t=150 (while fetching p2).
  fetchPage(p2) rejects with AbortError.
  await throws → generator rejects.
  for await receives rejection. catch handles.
```

---

## 10. Common confusion + traps

1. **Preload all pages** — OOM.
2. **`Symbol.iterator` vs `Symbol.asyncIterator`** — different protocols.
3. **`done: true` with value** — ignored.
4. **Forget `.return()` cleanup** — manual class only; async generator handles automatically.
5. **No AbortSignal threading** — abort doesn't cancel in-flight fetch.
6. **`Promise.all` inside loop** — unbounded concurrency; defeats backpressure.
7. **Mix sync and async iter** — different protocols; can't share.

---

## 11. Senior follow-ups & variants

### Variant 1 — Prefetching with concurrency
Maintain a queue; fetch next page in background while consumer drains current.

### Variant 2 — Async iterator helpers (TC39 stage-3)
`AsyncIterator.prototype.toArray()`, `.take(n)`, `.map`.

### Variant 3 — Resumable pagination
Accept `startCursor` for resume after crash.

### Variant 4 — `Readable.from(asyncIterable)`
Bridge to Node stream pipeline.

### Variant 5 — Node streams ARE async iterables
`for await (const chunk of fs.createReadStream(...))` works.

---

## 12. How to think aloud

> "Async iteration protocol: `[Symbol.asyncIterator]()` returns iter whose `next()` returns `Promise<{value, done}>`. `for await (const x of obj)` awaits each `next()` — natural backpressure (slow consumer throttles fetches). Sugar: `async function*` — `await` inside is allowed; `yield` emits items. For pagination: loop fetching pages with cursor, yield items one-by-one, exit when nextCursor is null. Memory O(pageSize); 100k items × 100/page = 100 fetches sequenced. Pass `AbortSignal` to fetch so consumer can cancel — `for await` then receives AbortError. Consumer `break` automatically calls `.return()` on async generator → `try/finally` cleanup runs. Node streams ARE async iterables (since v12) and `Readable.from(asyncIterable)` bridges back. Trap: preloading pages (OOM); forgetting AbortSignal; Promise.all inside loop (unbounded concurrency); confusing sync vs async iterator protocols."

---

## 13. 60-second revision

> - **`async function*`** + `for await...of` = lazy pagination.
> - **`Symbol.asyncIterator`** (separate from `Symbol.iterator`).
> - **`next()` returns `Promise<{value, done}>`**.
> - **Memory O(pageSize)** — one page at a time.
> - **Backpressure free** — consumer's await throttles fetches.
> - **`AbortSignal` thread-through** for cancellation.
> - **Consumer `break`** auto-calls `.return()` → cleanup.
> - **Node streams ARE async iterables;** `Readable.from(asyncIterable)` bridges.
> - **Trap:** preload pages; no signal; Promise.all (unbounded).

---

**Related:** [custom-iterator.md](./custom-iterator.md) · [fibonacci-generator.md](./fibonacci-generator.md) · [callback-api-to-async-iterator.md](./callback-api-to-async-iterator.md) · [fetch-response-async-iter.md](./fetch-response-async-iter.md) · [readable-stream-push.md](./readable-stream-push.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md), [`concepts/promises.md`](../../concepts/promises.md)
