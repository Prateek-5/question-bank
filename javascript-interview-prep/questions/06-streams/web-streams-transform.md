# Web Streams — TransformStream

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [web-streams-readable.md](./web-streams-readable.md), [transform-line-parser.md](./transform-line-parser.md)
>
> **Source:** WHATWG Streams. Browsers, Node 18+, Cloudflare Workers, Deno.

---

## 1. Problem statement

Build a `TransformStream` — bytes/chunks in, chunks out. Compose via `pipeThrough`.

**Verification examples**

```js
const upper = new TransformStream({
  transform(chunk, controller) {
    controller.enqueue(chunk.toUpperCase());
  },
  flush(controller) { /* called once at end */ },
});

const result = new Response('hello world').body
  .pipeThrough(new TextDecoderStream())
  .pipeThrough(upper);
for await (const c of result) console.log(c);                            // HELLO WORLD
```

**Constraints**
- `transform(chunk, controller)` — process each chunk.
- `flush(controller)` — emit final state.
- Async transform supported.
- `pipeThrough(transform)` returns the readable side.

---

## 2. Plain-English restatement

A TransformStream sits in the middle of a pipe. `transform` runs per chunk; `flush` runs once at end. Compose with `pipeThrough`. Backpressure flows naturally.

---

## 3. Why this matters in interviews

Cross-platform stream transform. Cloudflare Workers, fetch streaming, browser file handling.

---

## 4. Mental model

```
   new TransformStream({
     transform(chunk, controller) {
       // Called once per upstream chunk.
       // Can enqueue 0..N chunks.
       controller.enqueue(transformed);
     },
     flush(controller) {
       // Called once at end (after upstream closes).
       // Emit any buffered remainder.
     },
   }, writableStrategy, readableStrategy);

   Composition:
     readable.pipeThrough(transform).pipeTo(writable);
     readable.pipeThrough(t1).pipeThrough(t2).pipeTo(writable);

   Backpressure flows automatically through Transform.
   
   Built-in transforms:
   - TextDecoderStream — Uint8Array → string.
   - TextEncoderStream — string → Uint8Array.
   - CompressionStream — gzip/deflate.
   - DecompressionStream — gunzip/inflate.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Can `transform` enqueue more than one chunk per input?
> 2. What does `flush` do?
> 3. How does TransformStream propagate errors?

---

## 6. Brute force — walked through

### Wrong attempt 1: forget `flush`
Drops buffered partial line (in line parser).

### Wrong attempt 2: throw in `transform`
Use `controller.error(err)` or rethrow — both propagate; controller.error preferred.

### Wrong attempt 3: ignore `pipeThrough` chain
Manual `getReader/write` is verbose.

---

## 7. The unlocking insight

> **`transform(chunk, controller)` per chunk; `flush(controller)` once at end. Compose with `pipeThrough`. Backpressure flows automatically.**

Three properties:

1. **`transform` per chunk** — multiple enqueues allowed.
2. **`flush` at end** — emit final state.
3. **`pipeThrough` chains** — readable.pipeThrough(t).pipeTo(w).

---

## 8. Solution (annotated)

```js
// Line splitter
const lineSplitter = new TransformStream({
  start() { this.buf = ''; },                                            // not standard; use closure
  transform(chunk, ctl) {
    this.buf += chunk;
    const lines = this.buf.split('\n');
    this.buf = lines.pop();
    for (const line of lines) ctl.enqueue(line);
  },
  flush(ctl) {
    if (this.buf) ctl.enqueue(this.buf);
  },
});

// Closure-based variant (more portable)
function makeLineSplitter() {
  let buf = '';
  return new TransformStream({
    transform(chunk, ctl) {                                              // step 1: per chunk
      buf += chunk;
      const lines = buf.split('\n');
      buf = lines.pop();
      for (const line of lines) ctl.enqueue(line);                       // step 2: multiple enqueues
    },
    flush(ctl) {                                                          // step 3: final partial
      if (buf) ctl.enqueue(buf);
      buf = '';
    },
  });
}

// Async transform
const asyncFetch = new TransformStream({
  async transform(url, ctl) {
    const data = await fetch(url).then((r) => r.json());                  // step 4: async OK
    ctl.enqueue(data);
  },
});

// Composition
const result = sourceStream
  .pipeThrough(new TextDecoderStream())                                  // step 5: built-in
  .pipeThrough(makeLineSplitter())
  .pipeThrough(asyncFetch);

for await (const data of result) console.log(data);
```

**Try it yourself**

```js
// CompressionStream / DecompressionStream
const compressed = await new Response(input)
  .body
  .pipeThrough(new CompressionStream('gzip'));

// Browser: pipe fetch → decompress → text decode
const text = await fetch('/data.gz')
  .then((r) => r.body)
  .pipeThrough(new DecompressionStream('gzip'))
  .pipeThrough(new TextDecoderStream())
  .text?.();  // or read manually

// Error propagation
const failing = new TransformStream({
  transform(chunk, ctl) {
    if (chunk === 'bad') ctl.error(new Error('boom'));
    else ctl.enqueue(chunk);
  },
});

// Manual control: get the readable/writable sides
const t = new TransformStream({/* ... */});
sourceStream.pipeTo(t.writable);
t.readable.pipeTo(destStream);
```

---

## 9. Step-by-step dry run

```
new Response('hello\nworld').body.pipeThrough(new TextDecoderStream()).pipeThrough(makeLineSplitter()):

source body emits Uint8Array chunks.
TextDecoderStream: decodes to string with multi-byte safety.
makeLineSplitter:
  chunk1: 'hello\nworld' (single chunk for small input).
    buf = 'hello\nworld'.
    split('\n') = ['hello', 'world'].
    pop → buf = 'world'.
    enqueue('hello').
  upstream closes → flush:
    enqueue('world').

Consumer sees: 'hello', 'world'.

Cross-chunk example:
  chunk1: 'hello\nwor' → buf='wor', enqueue 'hello'.
  chunk2: 'ld\nfoo' → buf='wor'+'ld\nfoo'='world\nfoo'.
    split=['world', 'foo']. pop buf='foo'. enqueue 'world'.
  chunk3: '\n' → buf='foo\n'. split=['foo', '']. pop buf=''. enqueue 'foo'.
  flush: buf empty → no emit.

Backpressure:
  if consumer slow, transform pauses (await ctl.ready or controller backpressure).
  pipeThrough handles this.
```

---

## 10. Common confusion + traps

1. **Forget `flush`** — drops final partial.
2. **Throw in transform** — propagates; `controller.error(err)` is cleaner.
3. **State on `this` in object literal** — may not work; use closure.
4. **Multiple consumers** — readable locked once used.
5. **`pipeTo` blocks** — returns Promise; await it.
6. **Async transform errors not caught** — wrap in try/catch + controller.error.
7. **Confuse with Node Transform** — different API; similar idea.

---

## 11. Senior follow-ups & variants

### Variant 1 — Built-in transforms
TextDecoderStream, TextEncoderStream, CompressionStream, DecompressionStream.

### Variant 2 — Async transform
`async transform(chunk, ctl)` — pipeline waits.

### Variant 3 — Error propagation
`controller.error(err)` cleaner than throw.

### Variant 4 — Cross-platform
Same code works in browser, Node 18+, Cloudflare, Deno.

### Variant 5 — Node interop
`Readable.fromWeb(webStream)` to bridge.

---

## 12. How to think aloud

> "TransformStream is the Web Streams middle-stage primitive. Constructor takes `{ transform(chunk, controller), flush(controller) }`. `transform` is called per upstream chunk; can `controller.enqueue(chunk)` zero or many times. `flush` is called once after upstream closes — emit any buffered remainder (critical for line parsers; classic 'no trailing newline' bug). Async transform supported — pipeline waits. Compose via `pipeThrough(transform)` which returns the readable side. Chain: `source.pipeThrough(t1).pipeThrough(t2).pipeTo(writable)`. `controller.error(err)` propagates errors cleaner than throwing. Built-in transforms: TextDecoderStream, TextEncoderStream, CompressionStream, DecompressionStream — Cloudflare Workers ship these. Cross-platform: same code in browser, Node 18+, Cloudflare, Deno. Bridge to Node: `Readable.fromWeb(webStream)`. Trap: forget flush (drop final); throw in transform (use controller.error); state on `this` in object literal (use closure); pipeTo blocks (await)."

---

## 13. 60-second revision

> - **`new TransformStream({ transform, flush })`**.
> - **`transform(chunk, ctl)`** per chunk; 0..N enqueues.
> - **`flush(ctl)`** at end — final state.
> - **Async transform OK** — pipeline waits.
> - **`pipeThrough(t).pipeTo(w)`** for chaining.
> - **Built-ins:** TextDecoder/Encoder, Compression/Decompression Streams.
> - **`controller.error(err)`** > throw.
> - **`Readable.fromWeb / toWeb`** Node interop.
> - **Trap:** forget flush; throw not error; state on `this`; pipeTo not awaited.

---

**Related:** [web-streams-readable.md](./web-streams-readable.md) · [transform-line-parser.md](./transform-line-parser.md) · [csv-parser-via-transform.md](./csv-parser-via-transform.md) · [ndjson-splitter.md](./ndjson-splitter.md) · [throttled-stream.md](./throttled-stream.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
