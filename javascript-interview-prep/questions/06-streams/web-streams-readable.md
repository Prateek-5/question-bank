# Web Streams — ReadableStream basics

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [readable-stream-push.md](./readable-stream-push.md), [`concepts/streams.md`](../../concepts/streams.md)
>
> **Source:** WHATWG Streams Standard. Browsers, Node 18+, Cloudflare Workers, Deno.

---

## 1. Problem statement

Build a `ReadableStream` (Web Streams API). Distinguish push vs pull. Handle backpressure via controller.

**Verification examples**

```js
const rs = new ReadableStream({
  start(controller) { /* setup */ },
  pull(controller) {                                                     // called when consumer wants more
    controller.enqueue('chunk');
    if (done) controller.close();
  },
  cancel(reason) { /* cleanup */ },
}, { highWaterMark: 1 });

// Consume
for await (const chunk of rs) console.log(chunk);
```

**Constraints**
- `start`, `pull`, `cancel` methods.
- `controller.enqueue()`, `controller.close()`, `controller.error()`.
- Default is PULL source (`pull` called on demand).
- Backpressure: `controller.desiredSize` indicates how many to enqueue.

---

## 2. Plain-English restatement

Web ReadableStream is the cross-platform standard (browsers, Node 18+, Cloudflare Workers, Deno). Provide `pull(controller)` to produce chunks on demand; `controller.enqueue(chunk)` to push; `controller.close()` for EOF.

---

## 3. Why this matters in interviews

Cross-platform; same shape as Node Readable but standardized. Cloudflare/Stripe/Atlassian use it.

---

## 4. Mental model

```
   new ReadableStream(underlyingSource, queuingStrategy):
     underlyingSource:
       start(controller)  — initial setup; called once.
       pull(controller)   — called when desiredSize > 0; produce data.
       cancel(reason)     — called when consumer cancels; cleanup.
     
     controller methods:
       enqueue(chunk)     — add chunk to internal queue.
       close()            — end of stream.
       error(err)         — propagate error to consumer.
       desiredSize        — how many more chunks the consumer wants.
     
     queuingStrategy:
       { highWaterMark, size } — threshold + size calculator per chunk.

   Consumption:
     const reader = rs.getReader();
     while (true) {
       const { value, done } = await reader.read();
       if (done) break;
       use(value);
     }
     reader.releaseLock();
   
   Or via async iter (Node 18+, modern browsers):
     for await (const chunk of rs) ...
   
   Methods on the stream:
     rs.tee()         — split into two parallel readables.
     rs.pipeTo(ws)    — pipe to writable; returns Promise.
     rs.pipeThrough(transform) — chain through transform.
     rs.cancel(reason) — signal cancellation.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. When is `pull(controller)` called?
> 2. How does backpressure work in Web Streams?
> 3. What's the difference between Node Readable and Web ReadableStream?

---

## 6. Brute force — walked through

### Wrong attempt 1: ignore `desiredSize`
Enqueue forever; memory bloat (no backpressure).

### Wrong attempt 2: forget `close()`
Consumer hangs forever.

### Wrong attempt 3: throw in `pull`
Use `controller.error(err)` to propagate.

---

## 7. The unlocking insight

> **`pull(controller)` called on consumer demand. Enqueue until `desiredSize <= 0`. `close()` for EOF; `error(err)` for failure. Backpressure via `desiredSize`.**

Three properties:

1. **Pull-driven** by default.
2. **`controller.desiredSize`** indicates capacity.
3. **`close()` + `error()`** for end states.

---

## 8. Solution (annotated)

```js
// Range stream
function rangeStream(start, end) {
  let i = start;
  return new ReadableStream({
    pull(controller) {                                                   // step 1: producer
      if (i < end) {
        controller.enqueue(i++);                                          // step 2: enqueue
      } else {
        controller.close();                                              // step 3: EOF
      }
    },
  });
}

// Async source
function pagedApiStream(fetchPage) {
  let cursor = null;
  return new ReadableStream({
    async pull(controller) {
      try {
        const { items, nextCursor } = await fetchPage(cursor);
        for (const item of items) {
          controller.enqueue(item);
          if (controller.desiredSize <= 0) break;                        // step 4: backpressure
        }
        cursor = nextCursor;
        if (!cursor) controller.close();
      } catch (err) {
        controller.error(err);                                            // step 5: propagate
      }
    },
    cancel(reason) {
      cleanupResources();                                                  // step 6: cleanup
    },
  });
}

// Consume
for await (const item of rangeStream(1, 5)) console.log(item);            // 1, 2, 3, 4

// Multi-consume via tee
const [a, b] = sourceStream.tee();
const [hash, parsed] = await Promise.all([processA(a), processB(b)]);
```

**Try it yourself**

```js
// From an iterable
const fromArray = ReadableStream.from([1, 2, 3]);                        // modern; Node 20+

// Pipe to writable
const ws = new WritableStream({
  write(chunk) { console.log(chunk); },
});
await rangeStream(1, 5).pipeTo(ws);

// Cross-Node/Web conversion
const { Readable } = require('node:stream');
const nodeStream = Readable.fromWeb(webStream);                          // Node ↔ Web
const webStream2 = Readable.toWeb(nodeStream);

// With AbortSignal
const ac = new AbortController();
await webStream.pipeTo(ws, { signal: ac.signal });
```

---

## 9. Step-by-step dry run

```
const rs = rangeStream(1, 5);
for await (const n of rs):
  reader = rs.getReader() (under the hood).
  
  reader.read():
    Internal: queue empty → call pull(controller).
    pull(controller):
      i=1, i<5 → enqueue(1). desiredSize was 1, now 0.
    pull returns. read() resolves to {value: 1, done: false}.
  
  Body: log 1.
  
  reader.read():
    Queue empty → pull().
    enqueue(2). desiredSize 0 again.
    resolve {value: 2, done: false}.
  
  ... continues 3, 4.
  
  reader.read():
    Queue empty → pull().
    i=5, i<5 false → controller.close().
    resolve {value: undefined, done: true}.

Loop exits. for await automatically releases the lock.

Backpressure: pull only called when desiredSize > 0.
If consumer slow: desiredSize stays 0 between reads; pull not called.
```

---

## 10. Common confusion + traps

1. **Ignore `desiredSize`** — unbounded memory.
2. **Forget `close()`** — consumer hangs.
3. **Throw in `pull`** — use `controller.error(err)`.
4. **Iterate stream twice** — locked to first reader.
5. **Confuse with Node Readable** — same idea, different API.
6. **Sync `pull` blocking** — make it async for I/O.
7. **`pipeTo` and consume in parallel** — locked.

---

## 11. Senior follow-ups & variants

### Variant 1 — `ReadableStream.from(iterable)`
Bridge iterable → stream (Node 20+).

### Variant 2 — Tee for multi-consume
`rs.tee()` returns `[ReadableStream, ReadableStream]`.

### Variant 3 — Cross conversion
`Readable.fromWeb`, `Readable.toWeb` in Node.

### Variant 4 — `pipeThrough(transform)`
Chain TransformStream.

### Variant 5 — Cloudflare Workers
Cloudflare uses Web Streams; not Node streams.

---

## 12. How to think aloud

> "Web ReadableStream is the WHATWG standard — works in browsers, Node 18+, Cloudflare Workers, Deno. `new ReadableStream(underlyingSource)` where underlyingSource has `start`, `pull(controller)`, `cancel` methods. `controller.enqueue(chunk)`, `controller.close()`, `controller.error(err)`. Default is PULL — `pull` called when consumer wants more (`desiredSize > 0`). Respect `desiredSize` for backpressure — stop enqueuing when ≤ 0. Consume via `getReader().read()` or `for await`. `tee()` splits into two parallel readables. `pipeTo(writable)` pipes to a WritableStream; `pipeThrough(transform)` chains through a TransformStream. `Readable.fromWeb(webStream)` / `Readable.toWeb(nodeStream)` bridge in Node. `ReadableStream.from(iterable)` in Node 20+. Trap: ignore desiredSize; forget close; throw in pull (use controller.error); iterate twice (locked)."

---

## 13. 60-second revision

> - **`new ReadableStream({ start, pull, cancel })`**.
> - **`controller.enqueue / close / error`**.
> - **Pull-driven; respect `desiredSize`** for backpressure.
> - **`getReader().read()`** or **`for await`** to consume.
> - **`tee()`** for multi-consume.
> - **`pipeTo` / `pipeThrough`** for composition.
> - **`Readable.fromWeb / toWeb`** bridges Node ↔ Web.
> - **`ReadableStream.from(iterable)`** (Node 20+).
> - **Trap:** ignore desiredSize; no close; throw vs controller.error; double consume.

---

**Related:** [readable-stream-push.md](./readable-stream-push.md) · [web-streams-transform.md](./web-streams-transform.md) · [fetch-response-async-iter.md](./fetch-response-async-iter.md) · [stream-to-buffer-with-limits.md](./stream-to-buffer-with-limits.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
