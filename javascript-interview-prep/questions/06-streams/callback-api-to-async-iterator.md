# Callback API → async iterator

> **Difficulty:** Medium-Senior   |   **Time:** ~15 min   |   **Prereqs:** [async-iterator-pagination.md](./async-iterator-pagination.md), [custom-iterator.md](./custom-iterator.md)
>
> **Source:** AWS S3 list, GitHub API. Wrapping legacy callback or paginated APIs as `for await`.

---

## 1. Problem statement

Wrap a callback-style API as an async iterable so callers use `for await...of`.

**Verification examples**

```js
// Legacy callback API:
function pull(cb) { /* eventually calls cb(err, value, done) */ }

// Wrapped as async iterable
const iter = {
  [Symbol.asyncIterator]() {
    return {
      next() {
        return new Promise((resolve, reject) => {
          pull((err, value, done) => err ? reject(err) : resolve({value, done}));
        });
      },
      return() { return Promise.resolve({done: true}); },               // cleanup
    };
  },
};

for await (const item of iter) console.log(item);
```

**Constraints**
- `[Symbol.asyncIterator]()` returns iterator.
- `next()` returns `Promise<{value, done}>`.
- `return()` for cleanup on early break.
- Use `async function*` whenever possible — much cleaner.

---

## 2. Plain-English restatement

Wrap a callback-based "pull next" API so consumers can write `for await (const x of api)`. Each `next()` triggers one callback invocation and resolves with the result.

---

## 3. Why this matters in interviews

Senior backend pattern. Old SDKs use callbacks; modern code wants `for await`. Tests `Symbol.asyncIterator` protocol literacy.

---

## 4. Mental model

```
   Callback API: pull(cb) → eventually cb(err, value, done).
   
   Wrap as iterator:
     next() returns Promise.
     Inside promise: call pull, resolve/reject based on cb args.
   
   Three approaches:
   1. Manual: implement Symbol.asyncIterator + next() directly.
   2. Promisify pull then async function*:
        async function* iter() {
          while (true) {
            const {value, done} = await new Promise(r => pull((e,v,d) => r({err:e,value:v,done:d})));
            if (done) return;
            yield value;
          }
        }
   3. EventEmitter: events.on(emitter, 'data') (built-in Node).

   AbortSignal:
     pass signal to underlying API; abort rejects pending pull.
   
   Cleanup:
     for await break → iterator.return() called → release resources.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why is `async function*` cleaner than manual `Symbol.asyncIterator`?
> 2. What does `iterator.return()` do?
> 3. How do you propagate `AbortSignal` to a callback API?

---

## 6. Brute force — walked through

### Wrong attempt 1: collect all into array first
Defeats laziness; OOM on large.

### Wrong attempt 2: manual Symbol.asyncIterator everywhere
Verbose; `async function*` does it in 5 lines.

### Wrong attempt 3: no cleanup on break
Resource leak.

---

## 7. The unlocking insight

> **Wrap callback's pull in a Promise inside `async function*`. Yield values as they arrive; loop until `done`. Cleanup via `try/finally`.**

Three properties:

1. **Promisify the pull** — one promise per `next()`.
2. **`async function*`** for clean syntax.
3. **`try/finally`** for cleanup on break.

---

## 8. Solution (annotated)

```js
// Manual class
const cbApiIterable = {
  [Symbol.asyncIterator]() {                                            // step 1: protocol
    let closed = false;
    return {
      next() {
        return new Promise((resolve, reject) => {
          if (closed) return resolve({value: undefined, done: true});
          pullApi((err, value, done) => {                                // step 2: callback
            if (err) reject(err);
            else if (done) { closed = true; resolve({value: undefined, done: true}); }
            else resolve({value, done: false});
          });
        });
      },
      return() {                                                          // step 3: cleanup
        closed = true;
        return Promise.resolve({done: true});
      },
    };
  },
};

// Cleaner: async function*
async function* cbApiGenerator() {
  try {
    while (true) {
      const {value, done} = await new Promise((res, rej) => {
        pullApi((e, v, d) => e ? rej(e) : res({value: v, done: d}));
      });
      if (done) return;
      yield value;
    }
  } finally {
    cleanupResources();                                                   // step 4: try/finally
  }
}

// EventEmitter → async iter (built-in)
const { on } = require('node:events');
for await (const [data] of on(emitter, 'data')) {                        // step 5: events.on
  console.log(data);
}
```

**Try it yourself**

```js
// AWS S3 ListObjectsV2 paginator (modern SDK already provides this)
async function* listObjects(s3, bucket) {
  let token;
  do {
    const resp = await s3.listObjectsV2({ Bucket: bucket, ContinuationToken: token });
    for (const obj of resp.Contents ?? []) yield obj;
    token = resp.NextContinuationToken;
  } while (token);
}

for await (const obj of listObjects(s3, 'mybucket')) {
  console.log(obj.Key);
}

// With AbortSignal
async function* withSignal(asyncIter, signal) {
  for await (const item of asyncIter) {
    if (signal.aborted) throw new Error('Aborted');
    yield item;
  }
}
```

---

## 9. Step-by-step dry run

```
for await (const item of cbApiGenerator()):
  iter = cbApiGenerator()[Symbol.asyncIterator]()
  
  iter.next():
    Enter generator body.
    Loop iter 1: await new Promise → calls pullApi(cb).
    pullApi async work; eventually cb(null, 'item1', false).
    Promise resolves to {value:'item1', done:false}.
    yield 'item1'. PAUSE.
    Return {value:'item1', done:false} from next().
  
  Consumer processes 'item1'; calls iter.next() again.
  
  iter.next():
    Resume after yield. Loop iter 2.
    await pullApi → cb(null, 'item2', false).
    yield 'item2'. PAUSE.
  
  ... continues until cb(null, undefined, true).
  
  iter.next():
    await → resolves to {done: true}.
    if done: return. Generator returns.
    finally runs → cleanupResources.
  
  Loop exits.

Early break:
  consumer breaks at item2.
  iter.return() called → generator's finally runs → cleanup.
  pullApi may still resolve once more (no listener) — that's the trap.
```

---

## 10. Common confusion + traps

1. **Manual protocol when `async function*` works** — much cleaner.
2. **No `try/finally`** — resource leak on break.
3. **Promise per pull** but underlying cb may be re-called — should debounce.
4. **EventEmitter → for-await** without `on(emitter)` helper — manual is painful.
5. **`for await` over emitter with `'error'`** — also use `events.on` with abort.
6. **Abort doesn't reach callback** — thread signal explicitly.
7. **Mixing pull and push** — async iter is pull; emitter is push.

---

## 11. Senior follow-ups & variants

### Variant 1 — `events.on(emitter, 'event')`
Built-in Node helper; yields `[data]` arrays.

### Variant 2 — Backpressure mismatch
Push source faster than consumer pulls → buffer/drop.

### Variant 3 — `Readable.from(asyncGen)`
Bridge to Node stream pipeline.

### Variant 4 — `Symbol.asyncIterator` with retry
Retry pull on transient error before yielding.

### Variant 5 — Cancellation via AbortSignal
Pass signal to underlying API; signal.aborted → throw in generator.

---

## 12. How to think aloud

> "Wrap callback-style pull in a Promise inside `async function*`. Each iteration: `const {value, done} = await new Promise(r => pullApi((e,v,d) => e ? rej(e) : r({value:v, done:d}))); if (done) return; yield value;`. Cleaner than manual Symbol.asyncIterator. `try/finally` in generator for resource cleanup on early break. For EventEmitter sources, use built-in `events.on(emitter, 'event')` — yields `[data]` arrays. AWS SDK v3 provides paginators; older callback-style APIs need manual wrapping. AbortSignal: thread to underlying API; signal.aborted check in loop. Mismatch between pull (async iter) and push (emitter): push sources may overrun; consider bounded queue. `Readable.from(asyncGen)` bridges to Node stream pipeline. Trap: manual protocol when async function* works; no try/finally; abort not threaded; push/pull mismatch."

---

## 13. 60-second revision

> - **`async function*`** = cleanest wrapper.
> - **Per `next()`:** await new Promise wrapping the callback.
> - **`try/finally`** for resource cleanup.
> - **`events.on(emitter, 'event')`** for EventEmitter → for-await.
> - **AbortSignal** threaded to underlying API.
> - **`Readable.from(asyncGen)`** bridges to streams.
> - **Trap:** manual protocol; no cleanup; push/pull mismatch; abort not threaded.

---

**Related:** [async-iterator-pagination.md](./async-iterator-pagination.md) · [fetch-response-async-iter.md](./fetch-response-async-iter.md) · [custom-iterator.md](./custom-iterator.md) · [`04-promises/promisify-node-callback.md`](../04-promises/promisify-node-callback.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md), [`concepts/promises.md`](../../concepts/promises.md)
