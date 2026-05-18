# Web Streams — ReadableStream Basics

## Source / Origin
- WHATWG Streams Standard; supported in modern browsers and Node 18+.
- Asked at: Cloudflare (Workers shop), Stripe, Atlassian.
- Concept reference: `concepts/streams.md`.

## Why this question matters in interviews
Node has historically used `node:stream`; the web standard is `ReadableStream` / `WritableStream` / `TransformStream`. They're now everywhere — fetch's `response.body`, Cloudflare Workers, Service Workers, Deno. Senior bar: you can construct a ReadableStream, distinguish push/pull, handle backpressure via the controller, and convert between Node streams and Web streams.

## Concepts involved

### Syntax to lock in
```js
// Pull-source (default — call pull when consumer wants more)
const rs = new ReadableStream({
  start(controller) {
    // optional: initial setup
  },
  pull(controller) {
    // called when consumer wants more; enqueue some data
    controller.enqueue('chunk');
    if (done) controller.close();
  },
  cancel(reason) {
    // consumer aborted; cleanup
  },
}, /* queuing strategy */ { highWaterMark: 1 });

// Consume
const reader = rs.getReader();
while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  console.log(value);
}

// Or via async iterator (Node 18+, modern browsers)
for await (const chunk of rs) console.log(chunk);
```

### Edge cases / traps
1. **`pull` is called when the queue is below highWaterMark.** Don't enqueue eagerly in `start`.
2. **`controller.enqueue(chunk)`** returns the amount of room remaining (or `0` if full — backpressure signal).
3. **`controller.close()`** marks end; further enqueue throws.
4. **`controller.error(reason)`** rejects all pending and future reads.
5. **Locked streams** — only one reader at a time. `getReader()` locks; `releaseLock()` unlocks.
6. **Async iteration consumes (drains)** the stream — can only iterate once.
7. **Backpressure** is honored if `pull` returns a Promise — the stream waits before next pull.
8. **Conversion to Node stream**: `Readable.fromWeb(rs)`. Reverse: `rs = Readable.toWeb(nodeStream)`.

## Mental Model

```
   ReadableStream
   ┌──────────────────────────────────────────┐
   │  internal queue: [chunk1, chunk2, ...]   │
   │  highWaterMark: 1 (or specified)         │
   │                                          │
   │  source.pull(controller) called when     │
   │  queue.size < highWaterMark              │
   │                                          │
   │  controller.enqueue(c) — adds to queue   │
   │  controller.close()   — end of stream    │
   │  controller.error(e)  — abort            │
   └──────────────────────────────────────────┘
              ↑                       │
              │ pull (when room)      │ read() (returns {value, done})
              │                       ▼
            source                  consumer
```

## Why interviewers care

- **Web Streams literacy** — standard everywhere now.
- **Backpressure understanding** — pull-based model.
- **Async iteration** — modern consumption pattern.

## Common confusion

- **"Web Streams are like Node Streams."** Similar concepts; very different API. Web is pull-based + Promise-friendly; Node is push-based + EventEmitter.
- **"`getReader()` is optional."** Once obtained, the stream is locked; release before re-using.
- **"`fetch` body is a Node stream."** It's a Web ReadableStream (in modern Node and browsers).
- **"`pull` runs continuously."** Only when queue has room.

## Brute force

```js
// Push everything into an array first
const all = [];
for await (const chunk of rs) all.push(chunk);
```

Loses streaming/backpressure benefits.

## Optimal approach

Use the stream as a pull-source; consume via async iteration; respect backpressure via Promise-returning pull.

## Solution

```js
// 1. Range producer
function rangeStream(start, end) {
  let i = start;
  return new ReadableStream({
    pull(controller) {
      if (i < end) controller.enqueue(i++);
      else controller.close();
    },
  });
}

for await (const n of rangeStream(1, 5)) console.log(n);   // 1 2 3 4

// 2. Async paginated fetch as a stream
function pageStream(url) {
  let cursor = null;
  return new ReadableStream({
    async pull(controller) {
      const res = await fetch(`${url}?cursor=${cursor ?? ''}`);
      const page = await res.json();
      for (const item of page.items) controller.enqueue(item);
      if (!page.next) controller.close();
      else cursor = page.next;
    },
  });
}

// 3. Consume fetch body as text chunks
const res = await fetch('https://example.com');
const decoder = new TextDecoder();
for await (const chunk of res.body) {
  console.log(decoder.decode(chunk, { stream: true }));
}

// 4. Backpressure-aware enqueue
const slowSource = new ReadableStream({
  async pull(controller) {
    const room = controller.desiredSize;       // negative if over-watermark
    if (room <= 0) return;                       // wait
    controller.enqueue(await produce());
  },
}, { highWaterMark: 4 });

// 5. Convert to/from Node stream (Node 18+)
import { Readable } from 'node:stream';
const nodeStream = Readable.fromWeb(webStream);
const webStream2 = Readable.toWeb(nodeStream);

// 6. Multiple readers via tee
const [s1, s2] = rs.tee();    // two independent readers (each sees full stream)
```

## Dry run

```
const rs = new ReadableStream({ pull(c) { c.enqueue('hi'); c.close(); } });
const reader = rs.getReader();
const { value, done } = await reader.read();   // 'hi', done=false
const next = await reader.read();              // undefined, done=true
```

```
async iteration:
for await (const chunk of rs) {}
  internally: reader = rs.getReader()
  loop: { value, done } = await reader.read()
  while !done → yield value
  done → reader.releaseLock()
```

## How to think aloud

> "ReadableStream — pull-based. `new ReadableStream({pull(controller) {...}})`. pull called when queue has room; controller.enqueue/close/error. Consume via getReader().read() (returns {value, done}) or for-await. Backpressure: respect desiredSize; have pull return a Promise to throttle. tee() for multiple readers. Convert to/from Node streams via Readable.fromWeb/toWeb. Modern fetch's response.body is Web ReadableStream."

## Important takeaways

- **Pull-based**: source's `pull` called when queue has room.
- **`controller.enqueue/close/error`** — three operations.
- **One reader at a time** — locks on `getReader`.
- **Async iteration** drains; can only consume once.
- **`tee()`** for two independent readers.
- **Backpressure** via `desiredSize` and Promise-returning pull.
- **Interop with Node**: `Readable.fromWeb/toWeb`.

## Variants

- **Byte streams** (`new ReadableStream({type: 'bytes'})`) — for efficient byte transfer (BYOB readers).
- **TransformStream** — pipe a writable side into a readable side; the JS pipeline primitive.
- **`pipeThrough`** / **`pipeTo`** — high-level composition.
- **Web sockets via Web Streams** — emerging.

## Revision notes

```
ReadableStream:
  new ReadableStream({ start, pull, cancel }, { highWaterMark })
  pull(controller): enqueue/close/error
  controller.desiredSize → backpressure

Consume:
  reader = rs.getReader(); await reader.read()
  for await (const c of rs) ...

KEY:
  - pull-based (called when queue has room)
  - locked once getReader (release explicitly)
  - tee() for two readers
  - backpressure via desiredSize + Promise return from pull
  - Node interop: Readable.fromWeb / toWeb

USES:
  - fetch().body
  - Cloudflare Workers I/O
  - Service Workers
  - Deno I/O
```
