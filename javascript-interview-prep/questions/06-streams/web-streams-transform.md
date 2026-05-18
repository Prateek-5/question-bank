# Web Streams — TransformStream

## Source / Origin
- WHATWG Streams Standard; Node 18+, browsers, Cloudflare Workers.
- Asked at: Cloudflare, Stripe.
- Concept reference: `concepts/streams.md`, sibling `web-streams-readable.md`.

## Why this question matters in interviews
A TransformStream sits in the middle of a pipe: bytes/chunks in → bytes/chunks out. It's the Web Streams equivalent of `node:stream` `Transform`. Senior bar: you can build one, understand `transform(chunk, controller)` semantics, and use `pipeThrough` to compose.

## Concepts involved

```js
const upper = new TransformStream({
  transform(chunk, controller) {
    controller.enqueue(chunk.toUpperCase());
  },
  flush(controller) { /* called once at end */ },
});

// Use
const source = new Response('hello world').body;
const piped = source.pipeThrough(new TextDecoderStream()).pipeThrough(upper);
for await (const c of piped) console.log(c);   // HELLO WORLD
```

### Edge cases / traps
1. **`transform` may enqueue 0..N chunks per input.** Buffer/split as needed.
2. **`flush(controller)`** runs once at end — emit any buffered remainder.
3. **Async transform** — return a Promise; pipeline waits.
4. **Errors**: throw or `controller.error(e)`; both propagate.
5. **`pipeThrough(transform)`** returns the readable side.
6. **`pipeTo(writable)`** is the terminus — returns a Promise.
7. **Backpressure** flows naturally — slow consumer slows producer.

## Mental Model

```
   ReadableStream → TransformStream → ReadableStream → WritableStream
                          ↓
              transform(chunk, controller) per input
              flush(controller) once at end
```

## Why interviewers care

- **Pipeline composition** literacy.
- **Cross-runtime** (browser + Node + Workers).
- **Backpressure-aware** composition.

## Common confusion

- **"transform must enqueue exactly one chunk."** It can enqueue zero (filter), one (map), many (split).
- **"flush is for cleanup."** Yes — but also for emitting buffered remainder (e.g., final line without trailing `\n`).
- **"pipeThrough returns the transform."** It returns the *readable side* of it.

## Optimal approach

`new TransformStream({transform, flush})` plus `pipeThrough`/`pipeTo`. Pure data flow; backpressure free.

## Solution

```js
// 1. Map
const upper = new TransformStream({
  transform(c, ctl) { ctl.enqueue(c.toUpperCase()); }
});

// 2. Filter
const nonEmpty = new TransformStream({
  transform(c, ctl) { if (c.trim()) ctl.enqueue(c); }
});

// 3. Split (one input → many outputs) — newline splitter
const lineSplitter = (() => {
  let buf = '';
  return new TransformStream({
    transform(chunk, ctl) {
      buf += chunk;
      const lines = buf.split('\n');
      buf = lines.pop();           // last is partial
      for (const line of lines) ctl.enqueue(line);
    },
    flush(ctl) { if (buf) ctl.enqueue(buf); },
  });
})();

// Compose
const piped = fetch('/big.txt')
  .then(r => r.body)
  .then(body => body.pipeThrough(new TextDecoderStream()).pipeThrough(lineSplitter));
for await (const line of await piped) console.log(line);

// 4. Async transform (rate-limited fetch lookup)
const enrich = new TransformStream({
  async transform(id, ctl) {
    const data = await fetch(`/api/items/${id}`).then(r => r.json());
    ctl.enqueue(data);
  },
});
```

## Dry run

`"hello\nworld\nfoo"` through lineSplitter:

```
transform("hello\nworld\nfoo"):
  buf = "" + "hello\nworld\nfoo"
  lines = ["hello", "world", "foo"]
  buf = "foo" (pop last)
  enqueue "hello"; enqueue "world"
flush():
  buf = "foo" → enqueue "foo"
```

## How to think aloud

> "TransformStream: chunk in, 0..N chunks out via controller.enqueue. flush at end for trailing buffer. Compose with pipeThrough; terminate with pipeTo. Backpressure automatic. Async transform supported — pipeline awaits. For text: TextDecoderStream + custom transform for split/filter/map."

## Important takeaways

- **`transform(chunk, controller)`** — map/filter/split per input.
- **`flush(controller)`** — emit buffered remainder.
- **`pipeThrough` returns readable side.**
- **Async transform supported.**
- **Compose**: `body.pipeThrough(decode).pipeThrough(split).pipeTo(writable)`.

## Variants

- **TextDecoderStream / TextEncoderStream** — built-in.
- **CompressionStream / DecompressionStream** (browser) — gzip/deflate.
- **Identity** — passthrough with side effects (logging).

## Revision notes

```
new TransformStream({ transform(c, ctl), flush(ctl) })
pipeThrough → readable side
pipeTo → Promise (terminus)
async transform supported
backpressure automatic
```
