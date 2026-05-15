# Implement a Writable stream with `_write(chunk, enc, cb)` and backpressure

## Source
- codedamn "Stream Writable Lab": https://codedamn.com/problem/OHvS9lh7Ac_Ncg72qGorb
- Canonical Node.js docs: `stream.Writable`, `_write`, `_writev`, `_final`.

## Why this question matters in interviews
Writables are where backend engineers spend most of their stream time — every sink is a Writable: DB inserter, S3 uploader, log forwarder, websocket fan-out. The interview probe is always the same: "Implement `_write(chunk, encoding, callback)` for a [DB / queue / file] sink." The candidates who pass call `cb()` exactly once, signal backpressure properly, and override `_final` for graceful shutdown. The candidates who fail call `cb()` zero times (the pipeline hangs), twice (`ERR_MULTIPLE_CALLBACK`), or do async work without awaiting it inside `_write` (data loss). Nail this one and you've demonstrated mastery.

## Concepts involved

### The contract of `_write(chunk, encoding, callback)`
- `chunk`: the data Node is asking you to persist (Buffer or whatever in `objectMode`).
- `encoding`: the encoding of `chunk` if it's a string. Mostly ignorable in `objectMode`.
- `callback(err?)`: **MUST be called exactly once.**
  - Calling `cb()` with no arg → success, Node is free to send the next chunk.
  - Calling `cb(err)` → error, Node destroys the stream and the consumer sees `'error'`.
  - **Not calling it** → the Writable hangs forever, the producer eventually stalls due to backpressure. Most common bug.
  - **Calling twice** → throws `ERR_MULTIPLE_CALLBACK`.

### How backpressure actually works
1. Producer calls `writable.write(chunk)`.
2. Internally Node appends `chunk` to its buffer and calls `_write` if not already busy.
3. If buffer size ≥ `highWaterMark`, `write()` returns `false` — producer is supposed to pause.
4. When `_write`'s callback fires, Node pulls the next chunk from the buffer and calls `_write` again.
5. When the buffer drops below HWM, Node emits `'drain'` — producer can resume.

**Net effect:** the speed at which you call `cb()` controls how fast the producer can write. Slow `cb()` = natural rate limit.

### `_writev(chunks, cb)` — batched writes
If many `write()` calls queue up before `_write` finishes one, Node will batch them. Override `_writev(chunks, cb)` to receive them as an array — huge perf win for DB sinks (`INSERT ... VALUES (), (), ()` instead of N round trips).

### `_final(cb)` — graceful shutdown
Called once when the producer calls `writable.end()`. Your last chance to flush a buffer, COMMIT a transaction, close a DB connection. Always call `cb()`.

### `_destroy(err, cb)` — failure shutdown
Called on `destroy()` (manual or from `pipeline` error). Release resources unconditionally.

## Brute force approach
"I'll just push every chunk into an array and `console.log` at end." Works, but ignores backpressure (you'll buffer infinite memory), ignores async I/O, and skips `_final`. Reject this for any real sink.

## Optimal approach
Subclass `Writable` (or pass `write` in options). In `_write`, kick off the async I/O and call `cb` only after it completes (or rejects). Override `_writev` for batching. Override `_final` for flush logic. Override `_destroy` to release resources on error/abort.

## Solution (JavaScript)

```js
'use strict';
const { Writable } = require('node:stream');

/**
 * A Writable sink that simulates a batched DB inserter.
 * Buffers up to `batchSize` records, then flushes asynchronously.
 * Honors backpressure: cb() fires only after the flush completes.
 */
class BatchInsertStream extends Writable {
  /**
   * @param {(rows: object[]) => Promise<void>} flushFn
   */
  constructor(flushFn, { batchSize = 100, ...opts } = {}) {
    super({ objectMode: true, highWaterMark: batchSize * 2, ...opts });
    this.flushFn = flushFn;
    this.batchSize = batchSize;
    this.buffer = [];
  }

  // Called once per chunk in objectMode.
  _write(chunk, _encoding, cb) {
    this.buffer.push(chunk);
    if (this.buffer.length >= this.batchSize) {
      this._flush().then(() => cb(), cb);     // cb(err) on rejection
    } else {
      cb();                                   // accepted, not yet flushed
    }
  }

  // Optimization: receive the whole pending batch in one call.
  _writev(chunks, cb) {
    for (const { chunk } of chunks) this.buffer.push(chunk);
    if (this.buffer.length >= this.batchSize) {
      this._flush().then(() => cb(), cb);
    } else {
      cb();
    }
  }

  // Called on .end() — flush remainder.
  _final(cb) {
    this._flush().then(() => cb(), cb);
  }

  // Called on .destroy(err) or pipeline error — discard buffer.
  _destroy(err, cb) {
    this.buffer.length = 0;
    cb(err);
  }

  async _flush() {
    if (this.buffer.length === 0) return;
    const batch = this.buffer;
    this.buffer = [];
    await this.flushFn(batch);
  }
}

// Usage with pipeline
const { pipeline } = require('node:stream/promises');
const { Readable } = require('node:stream');

async function fakeInsert(rows) {
  await new Promise((r) => setTimeout(r, 50));   // simulate DB latency
  console.log(`inserted ${rows.length} rows`);
}

(async () => {
  const source = Readable.from(
    (function* () { for (let i = 0; i < 250; i++) yield { id: i }; })(),
  );
  await pipeline(source, new BatchInsertStream(fakeInsert, { batchSize: 100 }));
  // logs: "inserted 100 rows", "inserted 100 rows", "inserted 50 rows"
})();
```

## Step-by-step dry run

Source emits 250 objects, batchSize=100, HWM=200.

| Tick | Producer state | Buffer | DB | Notes |
| --- | --- | --- | --- | --- |
| 1 | wrote 1..100 | 100 rows queued | idle | `_write` fires for each. At chunk 100, buffer hits batchSize → kick off async flush, hold `cb` until DB returns. |
| 2 | producer paused | 100 rows in DB flush | flushing... | `write()` returned `false` for chunk 200, producer waits for `'drain'`. |
| 3 | flush completes (50ms) | empty | "inserted 100 rows" | `cb()` fires → Node pulls next chunk. Eventually buffer fills again. |
| 4 | wrote 101..200 | 100 rows | idle | Second flush kicks off. |
| 5 | source emits 201..250 then EOF | 50 rows | flushing 101..200 | `writable.end()` is called. |
| 6 | second flush done | 50 rows | "inserted 100 rows" | Node calls `_final(cb)`. |
| 7 | `_final` flushes remainder | empty | "inserted 50 rows" | `cb()` → emits `'finish'` → pipeline resolves. |

**Critical observation:** the producer is naturally rate-limited by DB latency. 250 rows × 50ms per 100-row batch = 3 flushes ≈ 150ms total. No queue grew unbounded; no row was lost; no chunk was double-inserted.

**What goes wrong without `_final`:** the last 50 rows sit in `this.buffer` forever. Pipeline resolves successfully but data is lost. Silent bug.

## Important takeaways

**Syntax to memorize**
- `super({ objectMode, highWaterMark })` in constructor.
- `_write(chunk, encoding, cb)` — call `cb()` **exactly once**.
- `_writev(chunks, cb)` for batching (chunks is `[{ chunk, encoding }, ...]`).
- `_final(cb)` for graceful shutdown.
- `_destroy(err, cb)` for failure / abort shutdown.

**Patterns to reuse**
- "Buffer N, flush async" is the universal sink pattern: log shippers, metrics aggregators, Postgres COPY, ES `_bulk`, Kafka batch producer.
- `.then(() => cb(), cb)` — concise way to convert a promise into a node-style callback.
- Pair `_final` with a `_destroy` that *discards* the buffer; on error you don't want to half-commit.

**Common mistakes**
- Calling `cb` synchronously after kicking off async work — defeats backpressure, producer races ahead.
- Calling `cb` twice (e.g. once in `.then` and again in error handler) → `ERR_MULTIPLE_CALLBACK`.
- Throwing from `_write` — wrap in try/catch and pass to `cb(err)`.
- Forgetting `_final` → lost data on `end()`.
- Setting `highWaterMark` too low for the I/O latency: e.g. HWM=1 with 50ms-per-write means 20 rows/sec max. Make HWM ≥ batch size.
- `pipeline(src, dst)` where `dst._write` never calls `cb` → pipeline hangs with no error. Worst kind of bug.

**Related**
- `readable-stream-push.md` — building the producer.
- `stream-pipeline-error-handling.md` — what happens when `cb(err)` fires.
- `stream-pipeline-lab.md` — putting Readable + Transform + your Writable together.

## Variants

1. **Concurrent flushes** — instead of waiting for each flush before the next, allow up to `concurrency` flushes in flight. Use a semaphore in `_write`; in `_final`, await all in-flight before calling `cb`. Common for high-throughput sinks but harder to get right (order is no longer guaranteed).

2. **Retry on transient error** — wrap `flushFn` with a retry loop with exponential backoff. Only call `cb(err)` after final retry fails. Be careful: holding `cb` for long means the producer stalls — that's often what you want, but mention the tradeoff.

3. **`Writable.toWeb()` / Web Streams interop** — modern Node exposes `Writable.toWeb()` returning a `WritableStream` from the Web Streams spec. Useful for code that needs to run in browsers, Cloudflare Workers, Deno. Mention this as a 2026 awareness item.

## Revision notes

> **Writable from scratch — 60 second recap**
> - Subclass `Writable`, set `{ objectMode, highWaterMark }`.
> - `_write(chunk, encoding, cb)` — call `cb()` EXACTLY ONCE. Async work? Call `cb` only after it finishes.
> - `cb()` = success → Node sends next chunk. `cb(err)` = fail → stream destroyed.
> - `.write()` returns `false` when buffer ≥ HWM → producer should pause.
> - Override `_writev` for batched writes (DB INSERTs, S3 multipart).
> - Override `_final(cb)` for flush-on-end. Skipping this = silent data loss.
> - Override `_destroy(err, cb)` for failure cleanup — discard buffer, close handles.
> - Trap: calling cb twice → `ERR_MULTIPLE_CALLBACK`. Forgetting cb → hang.
