# Async-Iterating a `fetch` Response Body

## Source / Origin
- `Response.body` is a Web ReadableStream; modern fetch.
- Asked at: Stripe, Cloudflare, Razorpay.
- Concept reference: `concepts/streams.md`, sibling `web-streams-readable.md`.

## Why this question matters in interviews
For huge downloads or streaming JSON/SSE you can't `await res.json()` — that buffers the entire response. `Response.body` is a `ReadableStream<Uint8Array>` you can iterate. Senior bar: you handle TextDecoder properly across multi-byte boundaries, parse SSE/NDJSON correctly, and pair with AbortController.

## Concepts involved

```js
const res = await fetch('/big.ndjson');
const decoder = new TextDecoder();
let buf = '';
for await (const chunk of res.body) {
  buf += decoder.decode(chunk, { stream: true });
  let nl;
  while ((nl = buf.indexOf('\n')) >= 0) {
    const line = buf.slice(0, nl);
    buf = buf.slice(nl + 1);
    handleJson(JSON.parse(line));
  }
}
if (buf) handleJson(JSON.parse(buf));
```

### Edge cases / traps
1. **Multi-byte UTF-8 chunks.** A 2/3/4-byte sequence may split across chunks. `TextDecoder({stream:true})` buffers half-characters.
2. **`for await` locks `res.body`** — can iterate only once.
3. **AbortController** — pass `signal` to fetch; cancellation propagates to the stream.
4. **Browser support** — async iteration on response.body lands in modern browsers and Node 18+.
5. **Backpressure** — fetch waits for consumer (you can't drink faster than the body sends).
6. **`.body.getReader()`** is the lower-level alternative if you need explicit pull control.
7. **SSE** has its own framing — events terminated by `\n\n`; field lines like `data: ...`. Parse accordingly.

## Mental Model

```
   fetch(...) → Response
   res.body : ReadableStream<Uint8Array>
   for await (chunk of res.body): chunk is a Uint8Array

   decode incrementally with TextDecoder({stream:true})
   parse lines/events from the accumulated string
```

## Why interviewers care

- **Streaming awareness** — separates senior from mid.
- **TextDecoder usage** — non-obvious for those who never streamed.
- **Cancellation** integration.

## Common confusion

- **"Use `decoder.decode(chunk)` without stream:true."** Then half-characters at chunk boundaries become replacement chars.
- **"`res.text()` is the same."** That buffers everything in memory.
- **"You can iterate body twice."** Only once; clone via `res.clone()` for two consumers.
- **"AbortController cancels after stream open."** It does — fetch cancellation propagates to body.

## Solution

```js
async function* ndjsonStream(url, { signal } = {}) {
  const res = await fetch(url, { signal });
  if (!res.body) throw new Error('No body');
  const decoder = new TextDecoder();
  let buf = '';
  for await (const chunk of res.body) {
    buf += decoder.decode(chunk, { stream: true });
    let nl;
    while ((nl = buf.indexOf('\n')) >= 0) {
      const line = buf.slice(0, nl);
      buf = buf.slice(nl + 1);
      if (line) yield JSON.parse(line);
    }
  }
  buf += decoder.decode();   // flush
  if (buf.trim()) yield JSON.parse(buf);
}

// SSE
async function* sseStream(url, { signal } = {}) {
  const res = await fetch(url, { signal, headers: { Accept: 'text/event-stream' } });
  const dec = new TextDecoder();
  let buf = '';
  for await (const chunk of res.body) {
    buf += dec.decode(chunk, { stream: true });
    let sep;
    while ((sep = buf.indexOf('\n\n')) >= 0) {
      const ev = buf.slice(0, sep);
      buf = buf.slice(sep + 2);
      const data = ev.split('\n').filter(l => l.startsWith('data:')).map(l => l.slice(5).trim()).join('\n');
      if (data) yield JSON.parse(data);
    }
  }
}

// Progress / abort
const ac = new AbortController();
setTimeout(() => ac.abort(), 30_000);
try {
  for await (const event of ndjsonStream('/feed', { signal: ac.signal })) console.log(event);
} catch (e) {
  if (e.name === 'AbortError') console.log('cancelled');
  else throw e;
}
```

## Dry run

Server sends `"a\nb\nc"` in two chunks: `"a\nb"`, `"\nc"`.

```
chunk 1: "a\nb"
  buf = "a\nb"; find \n at 1 → line="a", buf="b"; yield JSON.parse("a")
  no more \n; loop

chunk 2: "\nc"
  buf = "b\nc"; find \n at 1 → line="b", buf="c"; yield JSON.parse("b")
  no more \n

stream ends:
  buf="c"; flush decode (no extra bytes)
  yield JSON.parse("c")
```

## How to think aloud

> "Response.body is a Web ReadableStream of Uint8Array. for-await iterates chunks. Decode incrementally with TextDecoder({stream:true}) to handle multi-byte UTF-8 split across chunks. Parse line-by-line for NDJSON; double-newline-delimited events for SSE. Pair with AbortController for timeout/cancel. Backpressure is automatic — fetch slows if I'm slow."

## Important takeaways

- **`res.body` is ReadableStream<Uint8Array>.**
- **`TextDecoder({stream:true})`** for multi-byte safety.
- **Iterate once** — clone if needed.
- **AbortController** integration.
- **Backpressure automatic.**

## Variants

- **`res.body.pipeThrough(TextDecoderStream())`** for higher-level decode.
- **Reader API**: `res.body.getReader()` for manual pull.
- **SSE via EventSource** — different API; auto-reconnect.

## Revision notes

```
for await (const chunk of res.body): chunk is Uint8Array
decoder.decode(chunk, { stream: true })  ← essential for multi-byte
parse line by line for NDJSON
parse \n\n-delimited for SSE
AbortController.signal → cancellation
backpressure automatic (fetch waits)
once iterated; clone() for two consumers
```
