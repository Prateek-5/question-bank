# Streams (Node.js) + Async Iterators

## TL;DR
- A stream is an abstraction over data that arrives over time, in chunks. Four kinds: **Readable**, **Writable**, **Duplex** (both), **Transform** (Duplex that maps).
- **Backpressure** = the writer slows down when the reader can't keep up. `pipe()` handles it; `pipeline()` is the modern, error-safe wrapper.
- **Object mode** lets you push JS objects (not just Buffers/strings) through streams — used by DB cursors, CSV parsers.
- Async iterators (`for await...of`) + generators (`yield`) are the modern stream API: cleaner than `data`/`end` events.
- `highWaterMark` is the internal buffer size that triggers backpressure signals.

## Why backend interviewers care
- Streaming is how Node processes data larger than memory: log files, S3 multipart uploads, ETL, CSV/JSON ingest, HTTP chunked transfer.
- Missing backpressure is a top OOM killer in Node services.
- Senior roles often involve building pipelines (Kafka → transform → DB sink) where streams or async iterators are the right primitive.

## Core mental model
A Readable emits chunks; a Writable consumes them. The producer should pause when the consumer's buffer fills — otherwise memory explodes.

**Two modes for Readables**:
- **Flowing**: chunks pushed to the consumer via `data` events. No backpressure unless you `.pause()`.
- **Paused**: consumer pulls via `.read()` or, modern, via `for await...of`.

A stream's `_read(size)` (Readable) and `_write(chunk, enc, cb)` (Writable) are the internal hooks. The buffer between them holds up to `highWaterMark` bytes (default 16KB) or objects (default 16 in object mode). When the buffer hits HWM, `write()` returns `false` → you should stop writing and wait for `drain`.

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

**Transform** streams plug into pipelines: receive chunks, output transformed chunks (possibly fewer/more/different).

Async iterators wrap all this: any Readable is async-iterable.

```js
for await (const chunk of fs.createReadStream("big.log")) {
  process(chunk);
}
```

Generators (`function*`) and async generators (`async function*`) let you *build* streams declaratively — `Readable.from(asyncGen())`.

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
HTTP is streaming end-to-end in Node — `req` is a Readable, `res` a Writable. You can stream a 10GB file response without loading it into memory:
```js
fs.createReadStream(big).pipe(res);
```
For uploads, parse multipart with a streaming parser (`busboy`, `formidable`) — never `req.body = JSON.parse(...)` for large bodies.

Database drivers expose **cursors** as object-mode streams (Mongo `.find().stream()`, pg `pg-query-stream`). Iterate with `for await` to process millions of rows constant-memory.

**Backpressure across the network**: TCP windows handle byte-level backpressure automatically. But if you `for await` a slow consumer and produce to a fast Kafka, the producer needs internal queueing.

Beware **zlib/crypto streams** running on libuv threadpool (default size 4). Bump `UV_THREADPOOL_SIZE` if you have many concurrent compressed responses.

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
