# Streams (Node.js) + Async Iterators

> **Mentor's opening note** — Streams are the most misunderstood part of Node, and also the part that separates "I know JavaScript" from "I have run JavaScript in production." If you only ever process small request bodies and tiny files, you can avoid streams forever. The moment you touch a file you can't hold in RAM, a download that needs to start before it finishes, an upload from a 4G phone on a flaky train, or a CSV with 50 million rows — streams become the only sane primitive.
>
> Read this file in this order if you're learning it the first time:
> 1. The Intuitive Layer (bucket vs pipe).
> 2. TL;DR for the quick map.
> 3. Mental Model + common confusions + why interviewers care.
> 4. The cheat sheet, then worked examples — trace each one against the pipeline diagrams.
> 5. Edge cases, backend notes, and the 60-second cram.

## Intuitive layer — why do streams exist at all?

Imagine you need to move water from a reservoir to a faraway tank.

**The "bucket" approach** — fill a giant bucket at the reservoir, walk it to the tank, pour it in. Simple, but:
- You need a bucket as big as the water (memory).
- You can't pour until the bucket is full (no time-to-first-byte).
- If the bucket breaks mid-walk, you lose everything.

**The "pipe" approach** — lay a pipe from reservoir to tank. Water flows continuously. You need almost no storage at either end. The tank starts filling immediately. If the tank gets full, you close a valve — that *backpressure* propagates upstream, slowing the reservoir's release.

> **Buffer = bucket. Stream = pipe.** That's the entire conceptual leap. Buckets are easy to reason about; pipes are how real systems scale.

Three more analogies that are worth keeping handy:
- **Conveyor belt at a sushi restaurant.** Plates flow past you continuously. If you're slow, you stop taking plates — the belt jams and the chef knows to slow down. That's backpressure.
- **Assembly line.** Each station does one thing (cut, weld, paint) and hands off to the next. That's a `pipeline()`: Readable → Transform → Writable.
- **A garden hose.** Pressure (data) flows through. Kink it (slow consumer) and pressure builds upstream — the tap (producer) eventually has to throttle.

### Why this matters concretely — three forces

Streams exist because three constraints would otherwise destroy a Node service:

1. **Memory bounds.** A 50GB log file cannot fit in 8GB of RAM. Buffering = OOM. Streaming = constant memory regardless of input size.
2. **Time-to-first-byte.** HTTP clients expect a response to *start* fast. If you `JSON.parse` a 200MB body and *then* respond, you've added seconds of latency. Streaming starts responding immediately.
3. **Backpressure.** When the downstream system (disk, network, DB) is slower than the upstream producer, somebody has to slow down — otherwise an in-memory buffer grows until the process dies. Streams give you a built-in vocabulary for that conversation.

> **First-principles framing.** A stream is just a *protocol* between a producer and a consumer for negotiating: (a) chunks of data, (b) "I'm full, wait," (c) "I'm ready, send more," (d) "I'm done," (e) "Something broke." Everything else — Readable, Writable, Transform, Duplex, `pipe`, `pipeline`, `for await` — is sugar on top of that protocol.

## TL;DR
- A stream is an abstraction over data that arrives over time, in chunks. Four kinds: **Readable**, **Writable**, **Duplex** (both), **Transform** (Duplex that maps).
- **Backpressure** = the writer slows down when the reader can't keep up. `pipe()` handles it; `pipeline()` is the modern, error-safe wrapper.
- **Object mode** lets you push JS objects (not just Buffers/strings) through streams — used by DB cursors, CSV parsers.
- Async iterators (`for await...of`) + generators (`yield`) are the modern stream API: cleaner than `data`/`end` events.
- `highWaterMark` is the internal buffer size that triggers backpressure signals.

## Why interviewers care

If you can write `req.on('data', ...)` you've checked a box. If you can *explain* why `pipeline()` exists and what `write()` returning `false` actually means under the hood, you signal "I have built a real Node service and watched its memory graph." Streams questions filter for systems thinking: memory, latency, error paths, cancellation.

## Why backend interviewers care
- Streaming is how Node processes data larger than memory: log files, S3 multipart uploads, ETL, CSV/JSON ingest, HTTP chunked transfer.
- Missing backpressure is a top OOM killer in Node services.
- Senior roles often involve building pipelines (Kafka → transform → DB sink) where streams or async iterators are the right primitive.

## Common beginner confusion

The misconceptions to flush out *before* you write any stream code.

1. **"`.pipe()` handles everything."** No — `pipe()` propagates *data* and *backpressure*, but **not errors**. An error on a middle stream silently leaks file handles and sockets. Use `pipeline()` instead.
2. **"Backpressure is automatic."** `pipe()`/`pipeline()` automate it. If you write manually with `.write()`, *you* must check the return value and pause; otherwise the buffer grows unbounded.
3. **"High water mark = max memory."** No — HWM is the threshold at which `write()` *signals* "I'd like a pause." If your code ignores the signal, memory keeps climbing. HWM is advisory, not enforcement.
4. **"Object mode chunks are big."** Object-mode HWM counts *objects*, not bytes — default 16. So 16 huge objects can blow memory even at default HWM.
5. **"`data` event and `for await` are the same."** They're alternatives. Mixing them double-consumes; the second listener sees nothing or fragments.
6. **"`stream.destroy()` immediately frees resources."** It schedules cleanup asynchronously; wait for `close` if you need certainty.
7. **"Streams are slow."** Streams have a small per-chunk overhead vs raw buffering — but for any data larger than RAM, "slow streaming" beats "instantly out of memory."

## Mental Model — the pipe and its valves

Before the existing "Core mental model" section, hold this picture in your head:

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│   PRODUCER          INTERNAL BUFFER             CONSUMER       │
│   (Readable)        (highWaterMark)             (Writable)     │
│                                                                │
│    ┌─────┐    push   ┌──────────────┐    pull    ┌─────┐       │
│    │ src │ ────────▶ │ ████░░░░░░░  │ ─────────▶ │ dst │       │
│    └─────┘           │ (16KB cap)   │            └─────┘       │
│       ▲              └──────────────┘                          │
│       │                    │                                   │
│       │   buffer full?     │                                   │
│       └───── pause ────────┘                                   │
│             (backpressure signal)                              │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

- **Producer** pushes chunks INTO the buffer.
- **Consumer** pulls chunks OUT of the buffer.
- When the buffer **fills** (reaches HWM), the producer is asked to **pause**.
- When the consumer **drains** the buffer, the producer is asked to **resume**.

That's the whole backpressure dance.

## Core mental model
A Readable emits chunks; a Writable consumes them. The producer should pause when the consumer's buffer fills — otherwise memory explodes.

**Two modes for Readables**:
- **Flowing**: chunks pushed to the consumer via `data` events. No backpressure unless you `.pause()`.
- **Paused**: consumer pulls via `.read()` or, modern, via `for await...of`.

A stream's `_read(size)` (Readable) and `_write(chunk, enc, cb)` (Writable) are the internal hooks. The buffer between them holds up to `highWaterMark` bytes (default 16KB) or objects (default 16 in object mode). When the buffer hits HWM, `write()` returns `false` → you should stop writing and wait for `drain`.

### The four stream types — when each shows up

```
┌──────────────────────────────────────────────────────────────────┐
│  READABLE   — data flows OUT.   Examples:                        │
│               fs.createReadStream, http.IncomingMessage,         │
│               process.stdin, DB cursor.                          │
│                                                                  │
│       (chunks) ───▶  ┌──────────┐                                │
│                      │ Readable │                                │
│                      └──────────┘                                │
│                                                                  │
│  WRITABLE   — data flows IN.    Examples:                        │
│               fs.createWriteStream, http.ServerResponse,         │
│               process.stdout, network socket.                    │
│                                                                  │
│                      ┌──────────┐                                │
│                      │ Writable │  ◀─── (chunks)                 │
│                      └──────────┘                                │
│                                                                  │
│  DUPLEX     — readable AND writable, but the two halves are      │
│               independent. Example: net.Socket (you read from    │
│               the peer, you write to the peer — different data). │
│                                                                  │
│             (peer chunks) ───▶ ┌─────────┐ ───▶ (echoed?)        │
│                                │ Duplex  │                       │
│             (your chunks) ───▶ └─────────┘ ───▶ (to peer)        │
│                                                                  │
│  TRANSFORM  — a Duplex where output is a FUNCTION OF input.      │
│               Examples: zlib.createGzip, crypto.createHash,      │
│               your CSV parser.                                   │
│                                                                  │
│       (in) ──▶ ┌───────────┐ ──▶ (transformed out)               │
│                │ Transform │                                     │
│                └───────────┘                                     │
└──────────────────────────────────────────────────────────────────┘
```

A handy rule: if you find yourself wanting to "read a stream, do something per chunk, and emit a new stream" — you want a Transform. If you find yourself wanting to "produce data lazily from some source" — you want a Readable (or `Readable.from(asyncGen)`). If you want to consume into something (file, DB, socket) — you want a Writable.

### Pause/Resume mechanics — step-by-step diagram

Suppose `src.pipe(dst)` is running and the destination is slow. Let's watch the buffer over time. Each `█` is one chunk in the buffer; HWM = 4 chunks for illustration.

```
t=0   src ─▶ [░░░░] ─▶ dst        (empty, all systems go)

t=1   src ─▶ [█░░░] ─▶ dst        (chunk 1 queued)

t=2   src ─▶ [██░░] ─▶ dst        (chunk 2 queued; dst still on chunk 1)

t=3   src ─▶ [███░] ─▶ dst        (chunk 3 queued; dst processing slowly)

t=4   src ─▶ [████] ─▶ dst        (HWM reached!)
              ▲
              │  write() returns FALSE — backpressure signal fired.
              │  src.pause() is called automatically by pipe().
              │  No new chunks pushed.

t=5   src ░  [███░] ─▶ dst        (dst finished one chunk, buffer drains)
       (paused)

t=6   src ░  [██░░] ─▶ dst

t=7   src ░  [█░░░] ─▶ dst

t=8   src ░  [░░░░] ─▶ dst        (buffer fully drained → 'drain' event fires)
       (paused)
              │
              ▼
        src.resume() called automatically — producer wakes up.

t=9   src ─▶ [█░░░] ─▶ dst        (back to normal flow)
```

This pulse — *fill, signal, pause, drain, resume* — is the heartbeat of a healthy pipeline. When you build it manually with `.write()` and `'drain'`, you're recreating this dance by hand. When you use `pipe()` or `pipeline()`, the library does it for you.

```js
function copy(src, dst) {
  src.on("data", chunk => {
    const ok = dst.write(chunk);
    if (!ok) src.pause();
  });
  dst.on("drain", () => src.resume());
  src.on("end", () => dst.end());
  src.on("error", err => dst.destroy(err));
}
// Or: pipeline(src, dst, err => ...)
```

### Progressive examples — simplest → interview-ready

**Level 1 — read a file by chunks, count bytes.** The hello-world of streams.
```js
let bytes = 0;
fs.createReadStream("big.log")
  .on("data", chunk => bytes += chunk.length)
  .on("end",  () => console.log("size:", bytes));
```

**Level 2 — same, with `for await`** (modern, cleaner, error-friendly):
```js
let bytes = 0;
for await (const chunk of fs.createReadStream("big.log")) bytes += chunk.length;
console.log("size:", bytes);
```

**Level 3 — compose a pipeline.** Read → gzip → write. This is where streams justify their existence: a 10GB log compresses with ~64KB of memory.
```js
await pipelineP(
  fs.createReadStream("big.log"),
  zlib.createGzip(),
  fs.createWriteStream("big.log.gz"),
);
```

**Level 4 — custom Transform with backpressure honored** (e.g. a CSV parser, JSON line filter, batcher). See the cheat sheet's `csvParser`.

**Interview expectation:** you should write Level 3 without thinking. You should be able to *explain* why `pipeline` is better than `pipe().pipe().pipe()` in one sentence (error propagation + cleanup). And you should reach for `for await` over `.on('data')` whenever it works.

### Pipeline composition — the assembly line

A `pipeline()` is just an assembly line of stages: data flows through each in order.

```
┌──────────┐    ┌────────────┐    ┌────────────┐    ┌──────────┐
│ Readable │──▶ │ Transform1 │──▶ │ Transform2 │──▶ │ Writable │
│ (source) │    │ (parse)    │    │ (filter)   │    │  (sink)  │
└──────────┘    └────────────┘    └────────────┘    └──────────┘
   ▲ slow?                                                ▲
   │                                                      │
   └──── backpressure propagates upstream ◀───────────────┘
```

The killer property: **backpressure flows backward through the entire chain.** A slow Writable causes Transform2's buffer to fill, which causes Transform1's buffer to fill, which causes the Readable to pause. The producer slows down all by itself. You did not write that logic. The pipeline did.

**Transform** streams plug into pipelines: receive chunks, output transformed chunks (possibly fewer/more/different).

> **Bridge: classic streams ↔ async iterators.** Node's stream API was born in 2010; async iterators landed in 2018. They are *not* competing — they coexist. Any Readable is an async-iterable, meaning the most modern code looks like a `for await` loop while still using the classic stream plumbing underneath. New code should prefer `for await` and async generators for readability; reach for Transform classes when you need event emissions, custom `_flush`, or sync hot loops.

Async iterators wrap all this: any Readable is async-iterable.

```js
for await (const chunk of fs.createReadStream("big.log")) {
  process(chunk);
}
```

Generators (`function*`) and async generators (`async function*`) let you *build* streams declaratively — `Readable.from(asyncGen())`.

> **Read the cheat sheet as a vocabulary list.** Every line is a phrase you should be able to deploy in conversation. After reading, close the file and try to write each snippet from memory — that's the only way to make these muscle-memory by interview day.

## Syntax cheat sheet
```js
const fs = require("node:fs");
const { pipeline, Readable, Writable, Transform } = require("node:stream");
const { pipeline: pipelineP } = require("node:stream/promises");

// Read file as stream
const r = fs.createReadStream("in.txt", { highWaterMark: 64 * 1024 });
const w = fs.createWriteStream("out.txt");

// Old-school pipe (handles backpressure, NOT errors well)
r.pipe(w);

// Modern: pipeline (propagates errors, cleans up)
await pipelineP(
  fs.createReadStream("in.txt"),
  zlib.createGzip(),
  fs.createWriteStream("out.gz"),
);

// Async iteration
for await (const chunk of r) console.log(chunk.length);

// Custom Readable (object mode)
const src = new Readable({
  objectMode: true,
  read() {
    this.push({ id: 1 });
    this.push({ id: 2 });
    this.push(null); // EOF
  },
});

// Custom Writable
const sink = new Writable({
  objectMode: true,
  write(obj, enc, cb) {
    console.log("got", obj);
    cb(); // call when done with this chunk
  },
});

// Transform: uppercase
const upper = new Transform({
  transform(chunk, enc, cb) {
    cb(null, chunk.toString().toUpperCase());
  },
});

// Generator → Readable
async function* gen() {
  for (let i = 0; i < 1e6; i++) yield `row ${i}\n`;
}
const r2 = Readable.from(gen());

// Pipeline with async generator as transform (Node 16+)
await pipelineP(
  source,
  async function* (src) {
    for await (const x of src) if (x.ok) yield x;
  },
  sink,
);

// Backpressure-aware write loop
async function writeAll(stream, items) {
  for (const item of items) {
    if (!stream.write(item)) await new Promise(r => stream.once("drain", r));
  }
  stream.end();
}

// HTTP response is a Writable; request is a Readable
http.createServer((req, res) => {
  pipeline(req, res, (err) => err && console.error(err)); // echo
});

// CSV stream (using a library, but conceptually)
fs.createReadStream("data.csv")
  .pipe(csvParser())
  .on("data", row => insert(row));

// Convert Readable to buffer (small files only)
async function toBuffer(r) {
  const chunks = [];
  for await (const c of r) chunks.push(c);
  return Buffer.concat(chunks);
}
```

> **Bridge from cheat sheet to traps.** The snippets above show the happy path. The traps below show the unhappy paths — error leaks, OOM, hangs, double-consumption. Each is a real production incident pattern. Memorize the *symptom → cause* map.

## Edge cases & interview traps
1. **`data` listener flips the stream to flowing mode immediately** — bytes start arriving even if you haven't attached `error`.
2. **`.pipe()` does NOT forward errors** — must add `.on('error', ...)` to BOTH ends. Use `pipeline()`.
3. **Backpressure ignored = OOM** — `write` returning `false` is a *request*, not an enforcement.
4. **Object mode chunks are counted, not byte-sized** — HWM of 16 means 16 objects.
5. **Calling `.push(null)` ends a Readable** — forgetting it hangs the pipeline.
6. **Mixing `data` events and `for await`** double-consumes; pick one.
7. **`stream.destroy(err)` is async** — listen for `close` to confirm.
8. **`autoDestroy` defaults true** in Node 14+ — streams clean up on end/error.
9. **`pipeline` returns a Promise via `stream/promises`** — older callback form needs explicit error handling.
10. **`Readable.from(iter)` with sync iter returns chunks in object mode by default**.
11. **HTTP request body is a stream** — if you don't consume it, the socket stalls under load.
12. **Transform's `_transform` cb signature** — `cb(error, data)`; passing data is optional (you can `this.push` instead).
13. **`_flush(cb)`** runs at end — flush remaining buffered data (last partial line in CSV parsing).
14. **`AbortSignal` support**: `pipeline(..., { signal })` cancels mid-flight.
15. **High HWM doesn't speed things up** — it just delays the backpressure signal; can hide bugs.
16. **`zlib.createGzip()` is CPU-heavy** — runs on libuv threadpool (UV_THREADPOOL_SIZE), can starve other I/O.
    ```js
    // 4 concurrent gzip requests can fill the default threadpool (size 4),
    // delaying ALL other fs/dns/crypto work. Bump UV_THREADPOOL_SIZE=16 in prod.
    ```

## Interview worked examples

> **How to use this section as a learner.**
> 1. Cover the code. Read the prompt. Sketch the pipeline on paper (boxes + arrows + buffer indicators).
> 2. Read the "I'd say" sentence — that's your spoken answer.
> 3. Trace the code mentally with one tiny chunk going through it.
> 4. Predict the follow-up before you read it.
>
> **Interview storytelling tip.** When a streams question lands, your opening should *always* hit three beats: (a) "I'll use `pipeline` so errors propagate and resources close." (b) "Memory will stay constant because backpressure handles itself." (c) "Here's the shape: source → transforms → sink." That framing alone sets you apart from candidates who jump into `req.on('data', ...)` callbacks.

### Example 1 — File → gzip → file via pipeline
**Asked as:** "Compress a large file using streams, propagating errors and cleanup."

I'd say: "I'll use `pipeline` from `stream/promises` — it wires backpressure, error propagation, and resource cleanup automatically. Three stages: a Readable file stream, a gzip Transform, a Writable file stream. Memory stays constant regardless of file size."

```js
const { pipeline } = require("node:stream/promises");
const fs = require("node:fs");
const zlib = require("node:zlib");

await pipeline(
  fs.createReadStream("big.log"),
  zlib.createGzip(),
  fs.createWriteStream("big.log.gz"),
);
```

**What the interviewer is testing:** Use of `pipeline` over manual `pipe` chains; awareness of backpressure.
**Sharp follow-up they often ask:** "What's wrong with `.pipe().pipe().pipe()`?" → No error propagation; errors on intermediate streams leak; resources may not close.

> **Visualize Example 1's pipeline.**
> ```
> ┌──────────┐    ┌────────────┐    ┌────────────┐
> │  big.log │──▶ │ gzip       │──▶ │ big.log.gz │
> │ Readable │    │ Transform  │    │ Writable   │
> └──────────┘    └────────────┘    └────────────┘
>   16KB buf       16KB buf in       16KB buf
>                  16KB buf out
> ```
> Memory ceiling = sum of buffers ≈ ~64KB regardless of input size.

### Example 2 — CSV line-parser Transform
**Asked as:** "Build a Transform that turns byte chunks into objects, one per CSV line."

I'd say: "Buffer incoming chunks as a string, split on newline, push completed rows as parsed objects, keep the trailing partial line for the next chunk. Override `_flush` to emit the final partial line at EOF. Object-mode for the output side."

```js
const { Transform } = require("node:stream");

function csvParser(headers) {
  let buf = "";
  return new Transform({
    readableObjectMode: true,
    transform(chunk, _, cb) {
      buf += chunk.toString();
      const lines = buf.split("\n");
      buf = lines.pop();                          // partial trailing line
      for (const line of lines) {
        const cols = line.split(",");
        this.push(Object.fromEntries(headers.map((h, i) => [h, cols[i]])));
      }
      cb();
    },
    flush(cb) {
      if (buf) {
        const cols = buf.split(",");
        this.push(Object.fromEntries(headers.map((h, i) => [h, cols[i]])));
      }
      cb();
    },
  });
}
```

**What the interviewer is testing:** Transform internals (`_transform`, `_flush`), buffering across chunks.
**Sharp follow-up they often ask:** "What if a CSV field contains a quoted newline?" → discuss state machine + escape handling, or use `csv-parse`.

### Example 3 — Consume an HTTP response with `for await`
**Asked as:** "Stream the response of an HTTP request without buffering it all."

I'd say: "Node's IncomingMessage is async-iterable. `for await` pulls chunks one at a time, naturally applying backpressure — the socket pauses if your consumer is slow. Constant memory regardless of payload size."

```js
const http = require("node:http");

http.get("http://example.com/big.json", async (res) => {
  let totalBytes = 0;
  for await (const chunk of res) {
    totalBytes += chunk.length;
    // process chunk...
  }
  console.log("downloaded", totalBytes);
});
```

**What the interviewer is testing:** Modern stream consumption pattern; understanding that Readables are async-iterable.
**Sharp follow-up they often ask:** "What if I throw inside the loop?" → the socket is auto-destroyed; wrap with try/finally to clean up explicit state.

### Example 4 — Paginated REST API → async iterator
**Asked as:** "Wrap a paginated API as an async iterator so callers can `for await` over all rows."

I'd say: "Async generators (`async function*`) are the cleanest tool. The generator owns the cursor state; each `yield` pauses until the consumer asks for more. Pagination becomes invisible to the caller."

```js
async function* paginate(url) {
  let next = url;
  while (next) {
    const res = await fetch(next).then(r => r.json());
    for (const item of res.items) yield item;
    next = res.nextCursor ? `${url}?cursor=${res.nextCursor}` : null;
  }
}

for await (const item of paginate("/api/orders")) {
  process(item);
}
```

**What the interviewer is testing:** Async generators; lazy pull-based iteration.
**Sharp follow-up they often ask:** "Convert this to a Readable stream." → `Readable.from(paginate(url))`.

> **Visualize Example 5's manual backpressure loop.** Each tick is one `.write()` call.
> ```
> tick 1:  write("row1") → true   ✓ (buffer has room)
> tick 2:  write("row2") → true   ✓
> ...
> tick N:  write("rowN") → FALSE  ✗  (HWM hit → STOP)
>          await once(ws, "drain")
>          ──────────── waiting ────────────▶
>          drain event fires when buffer empties
> tick N+1: write("rowN+1") → true ✓  (resume)
> ```
> Ignoring the `false` return is the textbook OOM pattern: producers write at memory speed, consumers write at disk speed, the delta lives in heap.

### Example 5 — Manual backpressure with `.write()` + `'drain'`
**Asked as:** "Write 1M rows to a Writable without OOM."

I'd say: "Check `.write()`'s return value. If it returns `false`, the internal buffer is full — stop writing and wait for the `'drain'` event before continuing. Async/await + `once('drain')` makes the pattern clean."

```js
const { once } = require("node:events");

async function writeAll(ws, rows) {
  for (const row of rows) {
    if (!ws.write(row + "\n")) {
      await once(ws, "drain");
    }
  }
  ws.end();
}
await writeAll(fs.createWriteStream("out.txt"), rows);
```

**What the interviewer is testing:** Understanding that `write` returning false is advisory and you MUST cooperate.
**Sharp follow-up they often ask:** "What happens if you ignore the return value?" → buffer grows unbounded; process RSS climbs; eventually OOM.

### Example 6 — Async-generator transform inside pipeline
**Asked as:** "Filter and map a stream using an async generator instead of a Transform class."

I'd say: "Since Node 16, `pipeline` accepts async generators as transform stages. Cleaner than subclassing Transform when the logic is straightforward. Backpressure still works — generators are pull-based."

```js
const { pipeline } = require("node:stream/promises");

await pipeline(
  source,                                  // Readable
  async function* (src) {
    for await (const row of src) {
      if (row.status === "active") yield { ...row, processed: true };
    }
  },
  sink,                                    // Writable
);
```

**What the interviewer is testing:** Comfort with the most modern stream idioms; trade-off between Transform class vs async-gen.
**Sharp follow-up they often ask:** "When would you choose a Transform class over an async generator?" → When you need event emissions, sync `_transform` for max perf, or custom `_flush` logic.

> **Bridge from worked examples to patterns.** The examples above are each "one stream challenge in isolation." Real machine-coding combines several: read a CSV, validate rows, batch into 1000-row chunks, upsert to Postgres, on failure write to a DLQ — all without blowing memory. The patterns below are the named building blocks you compose.

## Common machine-coding patterns
- **Line-by-line file read** — when used: log processing, big NDJSON. Sketch:
  ```js
  const rl = readline.createInterface({ input: fs.createReadStream(path) });
  for await (const line of rl) handle(JSON.parse(line));
  ```
- **Transform stream** — when used: filter/map a stream. Sketch:
  ```js
  const filterErrors = new Transform({
    objectMode: true,
    transform(obj, _, cb) { if (obj.level === "error") this.push(obj); cb(); },
  });
  ```
- **Async generator pipeline** — when used: clean ETL. Sketch:
  ```js
  await pipelineP(
    src,
    async function* (s) { for await (const x of s) yield transform(x); },
    sink,
  );
  ```
- **Backpressure-aware producer** — sketch above (`writeAll`).
- **CSV → DB batch insert** — when used: ingest. Combine stream with a chunker:
  ```js
  let batch = [];
  for await (const row of csvStream) {
    batch.push(row);
    if (batch.length >= 1000) { await db.insertMany(batch); batch = []; }
  }
  if (batch.length) await db.insertMany(batch);
  ```
- **S3 multipart upload** — stream parts to S3, never load full file. Use AWS SDK's `Upload` which accepts a Readable.

## Backend-specific notes

> **Why this section matters.** Backend interviews don't test "did you read the docs," they test "have you fought a streaming bug at 2am." The notes below are the operational lore: TCP backpressure, libuv threadpool starvation, when to bump `UV_THREADPOOL_SIZE`. If you can drop a phrase like "we got `EAI_AGAIN` because all four threadpool slots were busy gzipping" — you're talking like a senior.

HTTP is streaming end-to-end in Node — `req` is a Readable, `res` a Writable. You can stream a 10GB file response without loading it into memory:
```js
fs.createReadStream(big).pipe(res);
```
For uploads, parse multipart with a streaming parser (`busboy`, `formidable`) — never `req.body = JSON.parse(...)` for large bodies.

Database drivers expose **cursors** as object-mode streams (Mongo `.find().stream()`, pg `pg-query-stream`). Iterate with `for await` to process millions of rows constant-memory.

**Backpressure across the network**: TCP windows handle byte-level backpressure automatically. But if you `for await` a slow consumer and produce to a fast Kafka, the producer needs internal queueing.

Beware **zlib/crypto streams** running on libuv threadpool (default size 4). Bump `UV_THREADPOOL_SIZE` if you have many concurrent compressed responses.

## Wrap-up: senior mentor's parting advice

If you take only three things from this file:

1. **Streams are a protocol for backpressure between producer and consumer.** Everything — Readable, Writable, Transform, `pipe`, `pipeline`, `for await` — is sugar on top of that protocol. Internalize the pipe-with-valve metaphor.
2. **Use `pipeline()` and `for await`, not `pipe()` and `.on('data')`.** The modern APIs propagate errors, clean up resources, integrate with async/await, and support `AbortSignal`. The classic APIs are how prod incidents start.
3. **Memory + latency + error-propagation are the three constants you're optimizing for.** Whenever you write stream code, ask: "Is my memory bounded? Is my time-to-first-byte short? Will an error in the middle stage close the file handle at the end stage?" If you can't answer yes to all three, you have a bug waiting.

The remaining mastery — object mode, custom `_flush`, async-gen transforms, `UV_THREADPOOL_SIZE` — are *additions*. Get the protocol-thinking right first.

## 60-second revision (day-before)
```text
┌──────────────────────────────────────────────────────────┐
│ STREAMS — DAY-BEFORE CRAM                                │
├──────────────────────────────────────────────────────────┤
│ • Types: Readable, Writable, Duplex, Transform           │
│ • Backpressure: write() === false → wait 'drain'         │
│ • pipeline() > pipe() — error propagation + cleanup      │
│ • for await...of on any Readable                         │
│ • Readable.from(asyncGen()) — declarative streams        │
│ • HWM = buffer size (bytes), or obj count in obj mode    │
│ • push(null) → EOF on Readable                           │
│ • Transform: _transform(chunk, enc, cb)                  │
│ • Object mode for parsed objects (CSV, JSON, DB rows)    │
│ • HTTP req=Readable, res=Writable; pipe req→res = echo   │
│ • zlib/crypto on libuv threadpool — bump UV_THREADPOOL   │
│ • Cursors: db.find().stream() → for await constant mem   │
│ • Batch in async-gen: accumulate N, flush, repeat        │
│ • pipeline accepts AbortSignal for cancel                │
│ • Never JSON.parse req.body for large uploads — stream   │
└──────────────────────────────────────────────────────────┘
```
