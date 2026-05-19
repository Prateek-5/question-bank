# Stream → Buffer with size limit

> **Difficulty:** Medium-Senior   |   **Time:** ~10 min   |   **Prereqs:** [web-streams-readable.md](./web-streams-readable.md), [fetch-response-async-iter.md](./fetch-response-async-iter.md)
>
> **Source:** HTTP body parsing defensive coding. Stripe, Cloudflare, Atlassian.

---

## 1. Problem statement

Read a stream into a Buffer/Uint8Array but enforce a max size. Reject and cancel if exceeded.

**Verification examples**

```js
async function streamToBuffer(stream, { maxBytes = 1024 * 1024, signal } = {}) {
  const reader = stream.getReader();
  const chunks = [];
  let bytes = 0;
  try {
    while (true) {
      if (signal?.aborted) throw new Error('Aborted');
      const { value, done } = await reader.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > maxBytes) {
        await reader.cancel('size limit exceeded');
        throw new Error(`Body too large: ${bytes} > ${maxBytes}`);
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const out = new Uint8Array(bytes);
  let off = 0;
  for (const c of chunks) { out.set(c, off); off += c.byteLength; }
  return out;
}
```

**Constraints**
- Track running byte count.
- On exceed: cancel reader + throw.
- AbortSignal for external cancellation.
- `reader.releaseLock()` in finally.

---

## 2. Plain-English restatement

Buffering an unbounded body is a DOS vector (malicious 10GB upload). Accumulate chunks with running count; abort and reject if exceeded.

---

## 3. Why this matters in interviews

Defensive coding for HTTP / file upload. Senior backend essential.

---

## 4. Mental model

```
   Accumulate chunks with bounded total:
     bytes = 0
     loop reader.read():
       if aborted → throw.
       if done → break.
       bytes += chunk.byteLength.
       if bytes > maxBytes:
         cancel reader (release underlying source).
         throw (reject promise).
       chunks.push(chunk)
     assemble Uint8Array of size bytes.
   
   Why getReader (not for await):
     Need explicit cancel() control.
     for await would not let us cancel reader.
   
   Cleanup:
     try/finally releaseLock() — even on throw.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why use `getReader` instead of `for await`?
> 2. What does `reader.cancel()` do?
> 3. Why is unbounded body parsing dangerous?

---

## 6. Brute force — walked through

### Wrong attempt 1: `await res.arrayBuffer()` / `res.text()`
No limit; OOM on huge body.

### Wrong attempt 2: count without canceling
Buffers all chunks before throwing; OOM.

### Wrong attempt 3: forget `releaseLock`
Stream stays locked.

---

## 7. The unlocking insight

> **Track running byte count; on exceed, call `reader.cancel()` to release underlying source and throw. `releaseLock()` in finally for cleanup.**

Three properties:

1. **Running count** — bail early.
2. **`reader.cancel()`** releases underlying source.
3. **`releaseLock()` in finally** — always.

---

## 8. Solution (annotated)

```js
async function streamToBuffer(stream, opts = {}) {
  const { maxBytes = 1024 * 1024, signal } = opts;
  const reader = stream.getReader();
  const chunks = [];
  let bytes = 0;

  try {
    while (true) {
      if (signal?.aborted) throw new Error('Aborted');                  // step 1: abort check
      const { value, done } = await reader.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > maxBytes) {                                            // step 2: limit check
        await reader.cancel('size limit exceeded');                      // step 3: release source
        throw new Error(`Body too large: ${bytes} > ${maxBytes}`);
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();                                                // step 4: always release
  }

  // Assemble
  const out = new Uint8Array(bytes);
  let off = 0;
  for (const c of chunks) { out.set(c, off); off += c.byteLength; }
  return out;
}

// Usage with fetch
const res = await fetch('/api', { signal });
if (!res.ok) throw new Error('HTTP error');
const body = await streamToBuffer(res.body, { maxBytes: 5 * 1024 * 1024, signal });
```

**Try it yourself**

```js
// Express-like middleware
async function readBody(req, maxBytes) {
  const reader = req.body.getReader();      // assuming Web Streams adapter
  const chunks = [];
  let bytes = 0;
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > maxBytes) {
        await reader.cancel();
        throw createHttpError(413, 'payload too large');
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  return Buffer.concat(chunks.map(c => Buffer.from(c)));
}

// Streaming JSON parse with limit (best of both)
async function readJsonLimited(stream, maxBytes) {
  const buf = await streamToBuffer(stream, { maxBytes });
  return JSON.parse(new TextDecoder().decode(buf));
}
```

---

## 9. Step-by-step dry run

```
streamToBuffer(stream, { maxBytes: 100 }):
  reader = stream.getReader().
  chunks = []. bytes = 0.
  
  Iter 1: read() → {value: Uint8Array(50), done: false}.
    bytes += 50 → 50. 50 ≤ 100. Push.
  
  Iter 2: read() → {value: Uint8Array(40), done: false}.
    bytes = 90. Push.
  
  Iter 3: read() → {value: Uint8Array(20), done: false}.
    bytes = 110. 110 > 100. 
    cancel('size limit') → releases underlying source.
    throw 'Body too large'.
  
  finally: releaseLock().
  Promise rejects.

vs naive: buffer all chunks, then check size:
  Could buffer 10GB before checking → OOM. Bad.

Normal completion:
  reader.read() → {done: true}. break.
  Assemble Uint8Array of total bytes.
  finally: releaseLock.
  Return Uint8Array.
```

---

## 10. Common confusion + traps

1. **No limit** — OOM/DOS.
2. **Check size after buffering all** — defeats purpose.
3. **Forget `cancel()`** — underlying source keeps reading.
4. **Forget `releaseLock`** — lock leaked.
5. **No `signal` thread** — can't external abort.
6. **`Buffer.concat` vs Uint8Array** — Node Buffer vs Web Uint8Array.
7. **`for await` for this case** — can't easily cancel reader.

---

## 11. Senior follow-ups & variants

### Variant 1 — Streaming parse without buffer
NDJSON line-by-line; never buffer entire body.

### Variant 2 — Per-request limit by content type
JSON 1MB, file uploads 50MB.

### Variant 3 — Stream → string
Like buffer but decode UTF-8.

### Variant 4 — Node Readable stream version
Use `for await (const chunk of nodeReadable)` + length check + `stream.destroy()`.

### Variant 5 — `body-parser` lib
Express middleware that does this.

---

## 12. How to think aloud

> "Buffering an unbounded body is a DOS vector — malicious 10GB upload OOMs your server. Accumulate chunks with running byte count; on exceed, call `reader.cancel()` to release the underlying source and throw. Use `stream.getReader()` (not `for await`) because you need explicit `cancel()` control. `try/finally` to `releaseLock()` — even on throw. Thread `AbortSignal` for external cancellation. After loop, assemble final `Uint8Array` of exact size. Express-like middleware: throw HTTP 413 'payload too large'. For streaming parse (NDJSON), don't buffer at all — process line by line. Per-route limits make sense: JSON 1MB, file upload 50MB. Trap: no limit; buffering then checking (defeats purpose); forgetting cancel/releaseLock; no signal threading."

---

## 13. 60-second revision

> - **Running count** — bail early on exceed.
> - **`reader.cancel('reason')`** — release underlying source.
> - **`releaseLock()` in finally** — always.
> - **`getReader` over `for await`** — for cancel control.
> - **AbortSignal threading** for external cancel.
> - **HTTP 413 for limit exceeded.**
> - **Per-route limits** — JSON small, files larger.
> - **Trap:** no limit; check after buffer; forget cancel/releaseLock.

---

**Related:** [web-streams-readable.md](./web-streams-readable.md) · [fetch-response-async-iter.md](./fetch-response-async-iter.md) · [throttled-stream.md](./throttled-stream.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
