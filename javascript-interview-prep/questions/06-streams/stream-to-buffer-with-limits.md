# Stream → Buffer with Size Limit

## Source / Origin
- HTTP body parsing; defensive coding.
- Asked at: Stripe, Cloudflare, Atlassian.
- Concept reference: `concepts/streams.md`.

## Why this question matters in interviews
"Read this request body into memory" — without a limit, a malicious 10GB upload DOS's your server. Senior bar: you accumulate with a running byte count, abort and reject if it exceeds the limit, and use AbortController to actually cancel the underlying read.

## Concepts involved

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

### Edge cases / traps
1. **Always release reader lock** in finally.
2. **Cancel the underlying stream** when over limit — `reader.cancel(reason)` propagates upstream.
3. **`byteLength` not `length`** — for `Uint8Array`, `length` works too but `byteLength` is universal.
4. **Allocate once at the end** to avoid quadratic copy. `new Uint8Array(totalBytes)` then `set` each.
5. **Concat chunks early** — wasteful with intermediate copies.
6. **Throw early** — don't wait for `done` if already exceeded.

## Mental Model

```
   stream → [chunk, chunk, chunk, ...]
              accumulate byteLength
              if exceeds → cancel + throw
              else continue
   at end:  allocate final Uint8Array(bytes); copy each chunk in
```

## Solution

```js
async function readBoundedBody(req, limit) {
  return streamToBuffer(req.body, { maxBytes: limit });
}

app.post('/upload', async (req, res) => {
  try {
    const body = await readBoundedBody(req, 1024 * 1024);   // 1 MB
    // process body...
    res.json({ size: body.byteLength });
  } catch (e) {
    if (e.message.startsWith('Body too large')) res.status(413).json({ error: 'payload too large' });
    else res.status(400).json({ error: e.message });
  }
});

// Streaming JSON parse with limit
async function readJsonBody(req, limit) {
  const buf = await streamToBuffer(req.body, { maxBytes: limit });
  return JSON.parse(new TextDecoder().decode(buf));
}

// With AbortController
const ac = new AbortController();
setTimeout(() => ac.abort(), 30_000);
const body = await streamToBuffer(req.body, { maxBytes: 1 << 20, signal: ac.signal });
```

## Dry run

`limit=10 bytes`, chunks of 4, 4, 4:

```
read chunk1 (4 bytes); bytes=4; ok; push
read chunk2 (4 bytes); bytes=8; ok; push
read chunk3 (4 bytes); bytes=12; > 10; cancel upstream; throw
```

Underlying socket gets the cancel signal — server-side connection can be reset.

## How to think aloud

> "Read incrementally, track total bytes, cancel and throw if over limit. Pre-allocate the final Uint8Array once (sum of chunk byteLengths) and copy each chunk in — avoids quadratic concat. Always release reader lock in finally. For body parsing, expose a `limit` parameter — default to a sane value like 1MB. Translate the error to HTTP 413 in the handler."

## Important takeaways

- **Track byte count cumulatively.**
- **Cancel upstream** with `reader.cancel(reason)` on overflow.
- **Pre-allocate** final Uint8Array; `set()` each chunk.
- **Always `releaseLock()` in finally.**
- **AbortSignal** for cancel.
- **HTTP: 413 Payload Too Large** on overflow.

## Variants

- **Stream-to-string** — wrap with `new TextDecoder().decode(buf)`.
- **Stream-to-JSON** — decode then `JSON.parse`.
- **Stream-to-disk** — pipe to writable file stream with same size check.
- **Stream-to-DB blob** — chunked insert.

## Revision notes

```
streamToBuffer(stream, {maxBytes, signal}):
  reader = stream.getReader()
  chunks=[], bytes=0
  loop:
    read chunk; bytes += chunk.byteLength
    if bytes > max: reader.cancel; throw
    chunks.push(chunk)
  finally reader.releaseLock()
  allocate Uint8Array(bytes); copy chunks; return

USES: HTTP body parse, file upload, JSON parse
LIMIT TO 413 in HTTP
ALWAYS releaseLock + propagate cancel
```
