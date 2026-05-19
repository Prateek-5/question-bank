# Async-iterating a `fetch` response body

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [web-streams-readable.md](./web-streams-readable.md), [ndjson-splitter.md](./ndjson-splitter.md)
>
> **Source:** Modern fetch streaming. Stripe, Cloudflare, Razorpay.

---

## 1. Problem statement

Stream a large/incremental HTTP response (NDJSON, SSE, downloads) without `await res.json()` buffering.

**Verification examples**

```js
const res = await fetch('/big.ndjson');
const decoder = new TextDecoder();
let buf = '';
for await (const chunk of res.body) {                                   // chunk is Uint8Array
  buf += decoder.decode(chunk, { stream: true });                       // multi-byte safe
  let nl;
  while ((nl = buf.indexOf('\n')) >= 0) {
    const line = buf.slice(0, nl);
    buf = buf.slice(nl + 1);
    handleJson(JSON.parse(line));
  }
}
if (buf) handleJson(JSON.parse(buf));
```

**Constraints**
- `res.body` is `ReadableStream<Uint8Array>`.
- `TextDecoder({stream: true})` buffers multi-byte across chunks.
- `for await` locks `res.body` — single consumer.
- AbortController for cancellation.

---

## 2. Plain-English restatement

`fetch` returns a `Response` whose `body` is a Web ReadableStream of Uint8Array chunks. `for await` iterates chunks. Decode with `TextDecoder({stream: true})` to handle UTF-8 multi-byte boundaries.

---

## 3. Why this matters in interviews

Modern API; SSE/NDJSON/large downloads. Tests Web Streams + TextDecoder + AbortSignal.

---

## 4. Mental model

```
   const res = await fetch(url, { signal });
   res.body  → ReadableStream<Uint8Array>
   
   for await (const chunk of res.body):
     chunk is Uint8Array (raw bytes).
     decoder.decode(chunk, {stream: true}):
       Buffers partial multi-byte sequence across chunks.
     Process decoded text (split lines, parse JSON, etc.).
   
   AbortController:
     pass signal to fetch.
     ac.abort() → in-flight read rejects with AbortError.
   
   Locks:
     for await calls res.body.getReader() internally.
     Body locked to that reader; can't be re-iterated.
     For multi-consume: res.body.tee() returns two streams.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Can you iterate `res.body` twice?
> 2. Why pass `{stream: true}` to `TextDecoder.decode`?
> 3. How do you cancel a long-running fetch stream?

---

## 6. Brute force — walked through

### Wrong attempt 1: `await res.json()` / `await res.text()`
Buffers entire response; OOM on huge.

### Wrong attempt 2: `decoder.decode(chunk)` without `{stream: true}`
Multi-byte char split across chunks → replacement char.

### Wrong attempt 3: iterate twice
Body locked; second iter throws.

---

## 7. The unlocking insight

> **`res.body` is a Web ReadableStream of Uint8Array. `for await` iterates chunks. `TextDecoder({stream: true})` for UTF-8 safety. AbortController threads cancellation.**

Three properties:

1. **`res.body` is async-iterable** (modern browsers + Node 18+).
2. **`TextDecoder({stream: true})`** for chunk-boundary safety.
3. **AbortSignal** for cancellation.

---

## 8. Solution (annotated)

```js
async function streamNdjson(url, { signal } = {}) {
  const res = await fetch(url, { signal });                              // step 1: with signal
  if (!res.ok) throw new Error(`HTTP ${res.status}`);

  const decoder = new TextDecoder();
  let buf = '';

  for await (const chunk of res.body) {                                  // step 2: iterate body
    buf += decoder.decode(chunk, { stream: true });                      // step 3: multi-byte safe
    let nl;
    while ((nl = buf.indexOf('\n')) >= 0) {
      const line = buf.slice(0, nl);
      buf = buf.slice(nl + 1);
      if (line.trim()) yield JSON.parse(line);
    }
  }
  buf += decoder.decode();                                                // step 4: flush decoder
  if (buf.trim()) yield JSON.parse(buf);                                  // step 5: final partial
}

// Usage
const ac = new AbortController();
setTimeout(() => ac.abort(), 30_000);

try {
  for await (const event of streamNdjson('/events.ndjson', { signal: ac.signal })) {
    handle(event);
  }
} catch (err) {
  if (err.name === 'AbortError') console.log('cancelled');
}
```

**Try it yourself**

```js
// SSE (Server-Sent Events) framing
async function* parseSSE(url) {
  const res = await fetch(url);
  const decoder = new TextDecoder();
  let buf = '';
  for await (const chunk of res.body) {
    buf += decoder.decode(chunk, { stream: true });
    let evt;
    while ((evt = buf.indexOf('\n\n')) >= 0) {                          // SSE events end with \n\n
      const event = buf.slice(0, evt);
      buf = buf.slice(evt + 2);
      const fields = {};
      for (const line of event.split('\n')) {
        const i = line.indexOf(':');
        if (i > 0) fields[line.slice(0, i).trim()] = line.slice(i + 1).trim();
      }
      yield fields;
    }
  }
}

// Multi-consume via tee
const [a, b] = res.body.tee();
const [hash, parsed] = await Promise.all([hashStream(a), parseStream(b)]);

// Lower-level getReader
const reader = res.body.getReader();
try {
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    process(value);
  }
} finally {
  reader.releaseLock();
}
```

---

## 9. Step-by-step dry run

```
streamNdjson('/events'):
  res = await fetch('/events') → Response.
  res.body: ReadableStream<Uint8Array>.
  
  Iteration 1: chunk1 = first 4096 bytes (might split a UTF-8 char).
    decoder.decode(chunk1, {stream: true}):
      Decodes bytes. If last bytes are partial multi-byte, BUFFER them; decoded text excludes the partial.
    buf += decoded.
    indexOf('\n') in buf → find complete lines, parse each, remove from buf.
  
  Iteration 2: chunk2 = next bytes.
    decoder.decode(chunk2, {stream: true}):
      Concatenates with buffered partial; decodes.
    buf += decoded.
    More complete lines parsed.
  
  ...
  
  After last chunk:
    decoder.decode() (no chunk, flushes): emits any final partial (replacement char if invalid).
    Final buf may have partial line → parse if non-empty.

AbortController:
  ac.abort() while await fetch in flight → fetch rejects with AbortError.
  Or while iterating body → reader.read() rejects.
  for await throws AbortError; cleanup releases reader.

vs await res.json():
  Buffers all bytes into single string.
  Then parses once. OOM on 10GB.
```

---

## 10. Common confusion + traps

1. **`await res.json()` for huge response** — OOM.
2. **`decoder.decode(chunk)`** without `{stream: true}` — multi-byte split.
3. **Iterate body twice** — locked to first reader.
4. **Forget `decoder.decode()` flush** — drops final partial bytes.
5. **No AbortSignal** — long-running fetch can't cancel.
6. **`response.body.tee()`** without consuming both — backpressure stalls.
7. **SSE framing** — `\n\n` separator, not `\n`.

---

## 11. Senior follow-ups & variants

### Variant 1 — SSE parsing
`\n\n` framing; `data:` field prefix.

### Variant 2 — `body.tee()` for multi-consume
Tee splits into two streams; consume in parallel.

### Variant 3 — `getReader()` for explicit control
Pull-based reads; manual `releaseLock()`.

### Variant 4 — Node 18+ vs browsers
Async iteration on `res.body` is universal now.

### Variant 5 — Backpressure
Fetch waits for consumer; can't drink faster than network sends.

---

## 12. How to think aloud

> "Modern `fetch` returns a Response whose `body` is a Web `ReadableStream<Uint8Array>`. `for await (const chunk of res.body)` iterates raw bytes. Decode with `new TextDecoder()` — pass `{stream: true}` to `decode(chunk, {stream: true})` so it buffers partial multi-byte sequences across chunks. After the loop, call `decoder.decode()` (no chunk) to flush any final partial bytes. Don't use `await res.json()` for huge responses — buffers everything → OOM. `res.body` is locked when iterated; for multi-consume use `res.body.tee()`. Cancellation: pass `signal: AbortSignal` to fetch; `ac.abort()` rejects in-flight reads with `AbortError`. SSE has its own framing (`\n\n` between events, `data:` fields). Lower-level: `res.body.getReader()` with manual `read()` + `releaseLock()`. Trap: `await res.json()` for huge; decoder without `{stream: true}`; iterating body twice (locked); SSE framing mistake."

---

## 13. 60-second revision

> - **`res.body`** = `ReadableStream<Uint8Array>` (modern fetch).
> - **`for await (const chunk of res.body)`** yields bytes.
> - **`new TextDecoder({stream: true})`** for UTF-8 safety across chunks.
> - **`decoder.decode()` (no args)** at end to flush.
> - **AbortSignal** via `fetch(url, { signal })`.
> - **`body.tee()`** for multi-consume.
> - **`getReader()`** for low-level pull.
> - **SSE framing:** `\n\n` events, `data:` fields.
> - **Trap:** `res.json()` for huge; decoder without `{stream}`; double iteration.

---

**Related:** [web-streams-readable.md](./web-streams-readable.md) · [web-streams-transform.md](./web-streams-transform.md) · [ndjson-splitter.md](./ndjson-splitter.md) · [stream-to-buffer-with-limits.md](./stream-to-buffer-with-limits.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
