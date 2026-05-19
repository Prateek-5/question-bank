# Build a file-transfer pipeline (Readable → gzip Transform → Writable)

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [readable-stream-push.md](./readable-stream-push.md), [writable-stream-implementation.md](./writable-stream-implementation.md)
>
> **Source:** Node `stream/promises#pipeline`. codedamn lab.

---

## 1. Problem statement

Compose three streams: read file → gzip → write file. Use `pipeline` (not `pipe`) for error propagation.

**Verification examples**

```js
const fs = require('node:fs');
const zlib = require('node:zlib');
const { pipeline } = require('node:stream/promises');

await pipeline(
  fs.createReadStream('big.log'),                                       // source
  zlib.createGzip(),                                                    // transform
  fs.createWriteStream('big.log.gz'),                                   // sink
);
```

**Constraints**
- Use `pipeline` (callback or promise form), NOT `pipe`.
- `pipeline` auto-destroys all streams on error.
- Backpressure flows end-to-end through the chain.
- For huge files, never `fs.readFileSync + gzipSync`.

---

## 2. Plain-English restatement

Compose stream stages with `stream/promises#pipeline`. It wires `pipe` between consecutive stages, listens for errors on every stream, and on the first error destroys all the others. Backpressure propagates automatically.

---

## 3. Why this matters in interviews

The most common "do you understand Node streams" question. Naive `src.pipe(gzip).pipe(dest)` leaks file descriptors on error.

---

## 4. Mental model

```
   Four stream types:
   - Readable   _read(size)               fs.createReadStream
   - Writable   _write(chunk, enc, cb)    fs.createWriteStream
   - Duplex     _read + _write            TCP socket
   - Transform  _transform(chunk, enc, cb) zlib.createGzip
   
   pipeline(...streams):
     1. Wires pipe() between consecutive streams.
     2. Listens for 'error' on EVERY stream.
     3. On first error → destroys all streams.
     4. Resolves/rejects the promise once.
   
   pipe vs pipeline:
     src.pipe(t).pipe(dst):
       Wires data forwarding.
       On error: only ONE stream destroyed; others leak fds.
       Bad for production.
     
     pipeline(src, t, dst):
       All errors caught.
       All streams destroyed on error.
       Use this.
   
   Backpressure (built-in):
     dst.write() returns false → pipe pauses src.
     dst emits 'drain' → pipe resumes src.
     End-to-end through Transform.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why is `pipeline` better than chained `pipe()`?
> 2. Why is `fs.readFileSync + gzipSync` bad for 5GB files?
> 3. What happens to upstream streams when downstream errors with `pipe`?

---

## 6. Brute force — walked through

### Wrong attempt 1: `fs.readFileSync('big.log')`
Loads entire file into memory; OOM on large.

### Wrong attempt 2: `src.pipe(gzip).pipe(dst)`
On error, only one stream destroyed; others leak fds.

### Wrong attempt 3: missing error handler
Uncaught error event crashes process.

---

## 7. The unlocking insight

> **Use `stream/promises#pipeline` to compose stages. Auto-destroys all streams on error. Backpressure flows end-to-end. Default `highWaterMark` is 16 KB byte / 16 objects.**

Three properties:

1. **`pipeline` handles errors** — not `pipe`.
2. **Backpressure end-to-end** through Transform.
3. **Promise form** for async/await.

---

## 8. Solution (annotated)

```js
const fs = require('node:fs');
const zlib = require('node:zlib');
const { pipeline } = require('node:stream/promises');

async function gzipFile(srcPath, destPath) {
  await pipeline(
    fs.createReadStream(srcPath),                                        // step 1: source
    zlib.createGzip(),                                                   // step 2: transform
    fs.createWriteStream(destPath),                                      // step 3: sink
  );
}

// Usage
try {
  await gzipFile('big.log', 'big.log.gz');
  console.log('done');
} catch (err) {
  console.error('failed:', err);                                         // any stage's error
}
```

**Try it yourself**

```js
// AbortSignal support (Node 16+)
const ac = new AbortController();
setTimeout(() => ac.abort(), 5000);

try {
  await pipeline(src, gzip, dst, { signal: ac.signal });
} catch (err) {
  if (err.name === 'AbortError') console.log('cancelled');
}

// Async iterable as source
const { Readable } = require('node:stream');
await pipeline(
  Readable.from(async function* () {
    for (let i = 0; i < 1000; i++) yield `line ${i}\n`;
  }()),
  zlib.createGzip(),
  fs.createWriteStream('out.gz'),
);

// Async function as transform
await pipeline(
  fs.createReadStream('input.log'),
  async function* (source) {
    for await (const chunk of source) yield chunk.toString().toUpperCase();
  },
  fs.createWriteStream('output.log'),
);
```

---

## 9. Step-by-step dry run

```
pipeline(src, gzip, dst):

Setup:
  Wire src.pipe(gzip), gzip.pipe(dst).
  Attach 'error' handler to all three.

Data flow:
  src reads 16KB chunk → pushes to gzip.
  gzip._transform compresses → pushes to dst.
  dst._write writes to disk → calls cb() when fsync done.
  Continues until src emits 'end'.
  gzip.end() → flushes final compressed chunk.
  dst.end() → flushes to disk → emits 'finish'.
  pipeline promise resolves.

Backpressure:
  dst.write() returns false (disk slow).
  pipe pauses gzip → pauses src.
  dst emits 'drain' → resume gzip → resume src.

Error scenario:
  zlib hits invalid data → emits 'error'.
  pipeline destroys src + gzip + dst.
  All file descriptors closed.
  pipeline promise rejects with zlib's error.

vs naive src.pipe(gzip).pipe(dst):
  zlib errors → 'error' on gzip only.
  src not destroyed → keeps reading → fd leak.
  dst not destroyed → fd leak.
  Promise never resolves; consumer hangs.
```

---

## 10. Common confusion + traps

1. **`fs.readFileSync`** — OOM on large files.
2. **`pipe` instead of `pipeline`** — fd leaks on error.
3. **Missing error handler** — uncaught 'error' crashes process.
4. **`highWaterMark` ignored** — accept default; tune only if needed.
5. **Mix sync + async transform** — pick one; async function* is modern.
6. **AbortSignal not threaded** — abort doesn't cancel mid-stream.
7. **Multiple `pipeline` on same stream** — only one consumer per Readable.

---

## 11. Senior follow-ups & variants

### Variant 1 — AbortSignal cancellation
`pipeline(..., { signal: ac.signal })`. Abort destroys all streams.

### Variant 2 — Async function as Transform
`pipeline(src, async function*(source) { for await (...) yield x }, dst)`.

### Variant 3 — Multiple Transforms
`pipeline(src, parse, filter, format, dst)` for ETL.

### Variant 4 — HTTP request body → file
`pipeline(req, fs.createWriteStream(uploadPath))`.

### Variant 5 — Browser equivalent
Web Streams: `readableStream.pipeThrough(transform).pipeTo(writableStream)`.

---

## 12. How to think aloud

> "Compose stream stages with `stream/promises#pipeline`. Three stages: `fs.createReadStream` (Readable) → `zlib.createGzip()` (Transform) → `fs.createWriteStream` (Writable). `pipeline` does FOUR things: wires `pipe` between stages, attaches `'error'` handler to every stream, destroys all streams on first error, resolves/rejects promise once. Naive `src.pipe(t).pipe(dst)` leaks file descriptors on error — only one stream destroyed; others keep reading and writing. Backpressure flows END-TO-END through Transform automatically. For huge files NEVER use `readFileSync + gzipSync` — OOMs. AbortSignal support (Node 16+): `pipeline(..., { signal })`. Async iterables: `Readable.from(asyncGen)` to wrap. Async function as transform: `pipeline(src, async function*(source) { ... }, dst)`. Web equivalent: `pipeThrough` + `pipeTo`. Trap: pipe vs pipeline; readFileSync for large; missing error handler; multiple consumers on one Readable."

---

## 13. 60-second revision

> - **`stream/promises#pipeline(src, ...transforms, dst)`** — modern composition.
> - **Auto-destroys all streams** on first error.
> - **Backpressure end-to-end** through Transform.
> - **`AbortSignal`** via `{ signal }` option.
> - **Async iterables** via `Readable.from(asyncGen)`.
> - **Async transform** via `async function*(source) { ... }`.
> - **Browser:** `readable.pipeThrough(t).pipeTo(writable)`.
> - **Trap:** pipe vs pipeline; readFileSync OOM; missing error handler.

---

**Related:** [readable-stream-push.md](./readable-stream-push.md) · [writable-stream-implementation.md](./writable-stream-implementation.md) · [stream-pipeline-error-handling.md](./stream-pipeline-error-handling.md) · [pipeline-error-propagation.md](./pipeline-error-propagation.md) · [transform-line-parser.md](./transform-line-parser.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
