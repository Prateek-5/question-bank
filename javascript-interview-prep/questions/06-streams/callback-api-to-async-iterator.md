# Convert a callback-based API to an async iterator

## Source
- Symbol.asyncIterator spec: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol/asyncIterator
- Async iteration proposal: https://github.com/tc39/proposal-async-iteration
- `events.on(emitter, name)` (the inverse — events to iterator): https://nodejs.org/api/events.html#eventsonemitter-eventname-options
- Common at companies with paginated REST APIs (Stripe, Shopify, GitHub) and at AWS-heavy shops (S3 ListObjects, DynamoDB Scan).

## Why this question matters in interviews
Modern Node.js code uses `for await ... of` everywhere — but most third-party APIs (Node-style `cb(err, data)`, paginated REST, EventEmitters) predate it. Senior backend engineers are expected to adapt callback / pagination APIs into async iterables so callers can write idiomatic `for await` loops. Knowing this is the difference between a junior who buries their pagination inside one function and a senior who exposes a clean, lazy, cancellable iterator that composes with `pipeline()`, `stream.pipeline`, and `Readable.from`. The question doubles as a `Symbol.asyncIterator` protocol probe — most candidates have never written one by hand.

## Concepts involved

### Syntax to lock in
```js
// the protocol
const iter = {
  [Symbol.asyncIterator]() {
    return {
      next() {
        return new Promise((resolve, reject) => {
          underlyingPullFn((err, value, done) => {
            if (err) reject(err);
            else resolve({ value, done });
          });
        });
      },
      return() { /* optional: cleanup on break/throw */ return Promise.resolve({ done: true }); }
    };
  }
};

for await (const item of iter) {
  // ...
}
```

### Runtime / engine behavior
- `for await...of` calls `obj[Symbol.asyncIterator]()` once, then repeatedly awaits `.next()` until `{ done: true }`.
- `.next()` must return a `Promise<{ value, done }>`. Each call is a "pull" — the iterator must not produce more than one result at a time.
- `.return()` is invoked when the consumer breaks out of the loop (or throws). This is your **cleanup hook**: close connections, abort in-flight requests, free buffers. Forgetting `return()` is a leak.
- `.throw()` (rare) lets the consumer inject an error into the iterator. Mostly used by transpilers; you can usually skip implementing it.
- Async iterators **don't buffer ahead** by default. Each `next()` is awaited before the next is called. This means an iterator backed by a paginated API only fetches a page when the consumer is ready — natural backpressure.
- An async generator function (`async function*`) auto-implements the protocol — it's the easiest way to build one. But for wrapping a callback API, the hand-rolled object form is often clearer.
- `Readable.from(asyncIterable)` (Node 12+) converts any async iterable into a Readable stream — so once you have the iterator, it plugs into `pipeline()`.

### Edge cases (interview traps)
1. **Re-entrant `.next()`.** If two consumers call `.next()` simultaneously, both will trigger an underlying pull. For most callback APIs this is a bug — track in-flight state.
2. **Cleanup on `break`.** Consumers do `for await (const x of iter) { if (cond) break; }`. The runtime calls `iter.return()`. If you don't implement it, in-flight requests leak.
3. **Errors mid-iteration.** If `next()` rejects, the `for await` loop throws. Subsequent `next()` calls should keep returning `{ done: true }` — don't reset.
4. **Empty iteration.** First `next()` returns `{ done: true }` → the `for await` body never runs. Make sure your pagination handles "no results" cleanly.
5. **AbortSignal support.** Modern callers will want `pageIterator(opts, { signal })`. Hook signal into both your in-flight pull AND your `return()` cleanup.
6. **Backpressure naturally works.** Don't pre-fetch the next page in the background "to be helpful" unless asked — you defeat lazy iteration and may fetch pages the consumer never reads.
7. **`done` semantics.** `{ value: x, done: true }` means "this is the last value AND we're done." Most generators emit `{ value: x, done: false }` then `{ value: undefined, done: true }`. Either works — pick one and stick with it.
8. **Promise.resolve in synchronous path.** If your callback fires synchronously (uncommon but possible), you still want to return a Promise — wrap in `new Promise(...)` always, or use `async`.

## Brute force approach
"I'll just fetch all pages first, then iterate over the array." This loads the entire dataset into memory — defeats the purpose. For a paginated API with 10,000 pages of 100 items each, you'd buffer a million records. Async iteration's whole value is **streaming consumption**: pull one page at a time, process, discard.

Another anti-pattern: "I'll emit each item via an EventEmitter and the consumer subscribes." Works but inverts control — consumers can't apply backpressure, they can only `pause/resume`. Not idiomatic in 2024+.

## Optimal approach
Hand-roll an object with `[Symbol.asyncIterator]()` returning an iterator object. The iterator holds:
- A cursor / page token (state across calls).
- An in-flight flag (or queue) for safety.
- A `done` flag to short-circuit after exhaustion or error.
- A `return()` method that aborts any in-flight call and marks done.

Each `next()`: if done, resolve `{ done: true }`. Else, await one pull from the underlying API, advance the cursor, resolve `{ value, done: false }`. When the underlying API signals "no more pages," set done and resolve `{ done: true }`.

## Solution (JavaScript)

```js
/**
 * Turn a paginated callback API into an async iterable.
 *
 * Underlying API shape (assumed):
 *   fetchPage(cursor, (err, { items, nextCursor }) => {})
 *   where nextCursor === null means "no more pages"
 *
 * @param {(cursor: string|null, cb: (err: Error|null, page?: {items: any[], nextCursor: string|null}) => void) => void} fetchPage
 * @returns {AsyncIterable<any>}
 */
function paginate(fetchPage) {
  return {
    [Symbol.asyncIterator]() {
      let cursor = null;
      let buffer = [];      // items from the latest page not yet yielded
      let done = false;
      let inflight = null;  // current pending pull, for cleanup

      const pullNextPage = () => new Promise((resolve, reject) => {
        fetchPage(cursor, (err, page) => {
          if (err) return reject(err);
          buffer = page.items.slice();
          cursor = page.nextCursor;
          if (cursor === null && buffer.length === 0) done = true;
          resolve();
        });
      });

      return {
        async next() {
          if (done) return { value: undefined, done: true };

          // refill buffer if empty
          while (buffer.length === 0 && !done) {
            inflight = pullNextPage();
            try {
              await inflight;
            } finally {
              inflight = null;
            }
            if (cursor === null && buffer.length === 0) {
              done = true;
              return { value: undefined, done: true };
            }
          }
          return { value: buffer.shift(), done: false };
        },

        async return() {
          // consumer broke out — mark done and let in-flight resolve naturally
          done = true;
          buffer = [];
          // (if your underlying API supports cancellation, call it here)
          return { value: undefined, done: true };
        },
      };
    },
  };
}

// usage with a fake paginated API
function fakeFetchPage(cursor, cb) {
  setTimeout(() => {
    const page = Number(cursor ?? 0);
    if (page >= 3) return cb(null, { items: [], nextCursor: null });
    cb(null, {
      items: [`p${page}-a`, `p${page}-b`],
      nextCursor: String(page + 1),
    });
  }, 10);
}

(async () => {
  for await (const item of paginate(fakeFetchPage)) {
    console.log(item);
    // backpressure: next page only fetched after each yield is consumed
  }
})();
```

## Step-by-step dry run

Using `fakeFetchPage` above, which has 3 pages of 2 items each.

- `for await` calls `[Symbol.asyncIterator]()`. Returns iterator with `cursor=null, buffer=[], done=false`.
- **next() #1**: buffer empty, not done. `pullNextPage()` with `cursor=null` → after 10 ms, `items=['p0-a','p0-b'], nextCursor='1'`. buffer becomes `['p0-a','p0-b']`. Shift `'p0-a'`. Return `{value: 'p0-a', done: false}`.
- Consumer logs `'p0-a'`.
- **next() #2**: buffer has `['p0-b']`. Shift. Return `{value: 'p0-b', done: false}`.
- Consumer logs `'p0-b'`.
- **next() #3**: buffer empty. Pull with `cursor='1'` → `items=['p1-a','p1-b'], nextCursor='2'`. Shift `'p1-a'`. Return.
- ... continues for page 1 and page 2 ...
- After yielding `'p2-b'`, **next() #7**: buffer empty. Pull with `cursor='3'` → `items=[], nextCursor=null`. Buffer stays empty. `done=true`. Return `{value: undefined, done: true}`.
- `for await` exits.

Net: 4 underlying `fetchPage` calls, 6 items yielded, memory never holds more than one page at a time. Backpressure works because page 1 isn't fetched until page 0 is fully consumed.

## Important takeaways

**Syntax to memorize**
- `[Symbol.asyncIterator]() { return { next() { ... }, return() { ... } } }`.
- `.next()` returns `Promise<{ value, done }>`. Always a Promise.
- `.return()` is the cleanup hook — implement it whenever your iterator holds resources.

**Patterns to reuse**
- This converts **any** pull-based callback API into something compatible with `for await`, `Readable.from`, `stream.pipeline`, and async generator composition. Paginated REST, AWS SDK v2 cursors, MongoDB cursors, DB result streams.
- The buffer + cursor + in-flight skeleton is the same shape as a fetch-ahead reader, a producer-consumer queue, or any pull-based protocol.
- Once you have an async iterable, `async function*` lets you trivially compose transforms: `async function* upper(iter) { for await (const x of iter) yield x.toUpperCase(); }`.

**Common mistakes**
- Forgetting `return()` → resources leak on `break`.
- Pre-fetching the next page eagerly in the background → defeats lazy iteration and can over-fetch when consumer breaks early.
- Forgetting to set `done = true` after the last page → infinite loop hitting the API forever.
- Returning `{ done: true }` with the last *value* in the same step — confuses some consumers. Stick to the "yield then `{ done: true }`" pattern.
- Using `async function*` syntax sugar without realizing you need explicit `return()` semantics for cancellable cleanup (the generator's `try/finally` handles it, but only if you use one).

**Related questions**
- `transform-line-parser` — its output is consumable via `for await`, same protocol.
- `generator-pipeline` — sync version of the same idea.
- `pipeline-error-propagation` — async iterables plug into `stream.pipeline` as stages.

## Variants

1. **Async generator form** — "Rewrite using `async function*`." Much shorter:
   ```js
   async function* paginate(fetchPage) {
     let cursor = null;
     while (true) {
       const { items, nextCursor } = await new Promise((res, rej) =>
         fetchPage(cursor, (err, p) => err ? rej(err) : res(p)));
       yield* items;
       if (nextCursor === null) return;
       cursor = nextCursor;
     }
   }
   ```
   The `try/finally` inside the generator becomes the cleanup hook automatically.

2. **EventEmitter to async iterator** — wrap `emitter.on('data', ...)` into a pull iterator. Tricky because events are push-based — you need a queue + a pending-resolver. Node provides `events.on(emitter, name)` for this exact case.

3. **AbortSignal-aware** — accept `{ signal }`, abort the in-flight pull on `signal.aborted`, and reject `next()` with `AbortError`. Required for HTTP-server-side iteration where the client may disconnect.

## Revision notes

> **callback-API-to-async-iterator — 60 second recap**
> - Implement `[Symbol.asyncIterator]() { return { next, return } }`.
> - `next()` returns `Promise<{ value, done }>` — one pull per call.
> - `return()` is the cleanup hook called on `break` / `throw`.
> - Backpressure is built-in: next page fetched only when consumer requests next item.
> - Easier with `async function*` — `yield*` items, `return` to end.
> - Use case: paginated REST, callback-style DB cursors, AWS SDK v2.
> - **Trap:** forget `return()` → leak on early break.
> - **Trap:** pre-fetching ahead → over-fetch on early break.
> - **Trap:** don't set `done = true` after last → infinite loop.
> - Composes with `Readable.from(asyncIterable)` and `stream.pipeline`.
