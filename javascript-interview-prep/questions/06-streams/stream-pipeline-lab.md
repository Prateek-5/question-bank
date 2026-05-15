## Source
- codedamn "Node.js Stream Pipeline Lab": https://codedamn.com/problem/ru5OH8OPupFFpOY0AGoMD
- Canonical Node.js docs pattern (`stream.pipeline` / `node:zlib` / `node:fs`).

# Build a file-transfer pipeline (Readable → gzip Transform → Writable)

## Why this question matters in interviews
This is the most common "do you actually understand Node streams" question for backend engineers. The naive answer is `src.pipe(gzip).pipe(dest)` — which is wrong in production because errors on any step leak the other handles and the file descriptors stay open. Interviewers want to see you reach for **`stream.pipeline`** (callback or `promises` form) which propagates errors and auto-destroys every stream in the chain. It also tests whether you know that **gzip is a Transform stream** (Readable+Writable in one), that backpressure flows end-to-end through `pipe`/`pipeline`, and that file I/O in Node is stream-first.

## Concepts involved

### The four stream types — mental model
| Type | Direction | Override | Real example |
| --- | --- | --- | --- |
| Readable | source / out | `_read(size)` | `fs.createReadStream`, HTTP request body |
| Writable | sink / in | `_write(chunk, enc, cb)` | `fs.createWriteStream`, HTTP response |
| Duplex | both, independent | `_read` + `_write` | TCP socket |
| Transform | both, in→out mapped | `_transform(chunk, enc, cb)` | `zlib.createGzip`, crypto cipher |

### `pipeline` vs `pipe` — why `pipeline` wins
```js
// BAD — old style: leaks on error
src.pipe(gzip).pipe(dest);
// If `dest` errors, `src` and `gzip` are NOT destroyed → FD leak.

// GOOD — pipeline auto-destroys all on error
const { pipeline } = require('node:stream');
pipeline(src, gzip, dest, (err) => { /* one error callback */ });

// BEST — promise form for async/await
const { pipeline } = require('node:stream/promises');
await pipeline(src, gzip, dest);
```

### Backpressure (the #1 backend concept)
- **Definition (plain words):** "Downstream consumer signals 'I'm full, slow down'; the producer must pause until drained."
- **Mechanically:** `writable.write(chunk)` returns `false` when its internal buffer crosses `highWaterMark`. The producer should stop pushing until the writable emits `'drain'`.
- `pipe`/`pipeline` does this automatically — that's the whole point of streams. If you manually shuttle data with `on('data')` + `dest.write`, **you** have to handle backpressure.

### `highWaterMark`
- Default 16 KiB (16384 bytes) for byte streams.
- Default 16 *objects* when `objectMode: true`.
- It's a threshold, not a hard cap — `.write()` accepts the chunk and returns `false` to ask you to pause.

## Brute force approach
Read entire file into a Buffer with `fs.readFileSync`, gzip it with `zlib.gzipSync`, then write with `fs.writeFileSync`. Works for 1 MB files. For 5 GB files it OOMs the process. Also blocks the event loop the entire time. Streams exist precisely to avoid this.

## Optimal approach
Compose three streams with `stream/promises#pipeline`:
1. `fs.createReadStream(srcPath)` — Readable, chunked file read.
2. `zlib.createGzip()` — Transform that compresses chunks in place.
3. `fs.createWriteStream(destPath)` — Writable, chunked file write.

Memory stays at ~`highWaterMark × 2` regardless of file size. Errors anywhere collapse the whole chain cleanly. Bonus: an `AbortSignal` can cancel mid-flight.

## Solution (JavaScript)

```js
'use strict';
const fs = require('node:fs');
const zlib = require('node:zlib');
const { pipeline } = require('node:stream/promises');

/**
 * Compress a file using a streaming pipeline.
 * Memory footprint stays O(highWaterMark), not O(fileSize).
 * @param {string} src  path to plain file
 * @param {string} dst  path to .gz output
 * @param {AbortSignal} [signal]  optional cancellation signal
 */
async function gzipFile(src, dst, signal) {
  await pipeline(
    fs.createReadStream(src),         // Readable — emits Buffer chunks
    zlib.createGzip({ level: 6 }),    // Transform — gzip each chunk
    fs.createWriteStream(dst),        // Writable — flushes to disk
    { signal },                       // pipeline destroys all on abort
  );
}

// Usage
(async () => {
  const ac = new AbortController();
  setTimeout(() => ac.abort(), 30_000);     // 30s hard cap
  try {
    await gzipFile('./big.log', './big.log.gz', ac.signal);
    console.log('done');
  } catch (err) {
    // err.code === 'ABORT_ERR' if aborted; otherwise underlying I/O error
    console.error('pipeline failed:', err.code, err.message);
  }
})();
```

Modern async-iterator equivalent (when you need a custom transform inline):
```js
const { pipeline } = require('node:stream/promises');
const { Readable } = require('node:stream');

await pipeline(
  fs.createReadStream(src),
  async function* (source) {                 // async generator = Transform
    for await (const chunk of source) {
      yield chunk.toString().toUpperCase();
    }
  },
  fs.createWriteStream(dst),
);
```

## Step-by-step dry run

Suppose `big.log` is 64 KiB, `highWaterMark` is 16 KiB.

| Tick | Readable buffer | Gzip buffer | Writable buffer | Action |
| --- | --- | --- | --- | --- |
| 1 | 16 KiB pushed | empty | empty | Readable hits HWM, pauses `_read`. |
| 2 | 16 KiB consumed by gzip | 16 KiB raw in, ~5 KiB compressed out | empty | Gzip emits compressed chunk to dest. |
| 3 | another 16 KiB pushed | flushing | 5 KiB queued | `dest.write()` returns `true` (under HWM). |
| ... | ... | ... | ... | Cycle repeats until EOF. |
| N | EOF (`push(null)`) | flush + `end` | drain + `finish` | `pipeline` resolves. |

If `dest` errors at tick 3 (disk full):
- `pipeline` calls `destroy(err)` on **all three** streams.
- The Readable closes its FD. The Gzip releases its native gzip context.
- The promise rejects with the original `EIO` / `ENOSPC` error.

With raw `pipe`, only `dest` would close — the Readable would sit open until GC, leaking the FD.

## Important takeaways

**Syntax to memorize**
- `const { pipeline } = require('node:stream/promises')` — always reach for the promise form in 2026.
- Stream constructors are factories: `fs.createReadStream`, `fs.createWriteStream`, `zlib.createGzip`, `crypto.createCipheriv`. None take `new`.
- An `async function*` is automatically a valid `Transform` inside `pipeline` — no `Transform` subclass needed.

**Patterns to reuse**
- Encrypt-at-rest: `read → cipher → write`.
- Log shipping: `read → newline-split Transform → JSON.parse Transform → batch Writable`.
- HTTP proxy with compression: `req → gzip → res`.

**Common mistakes**
- Using `.pipe()` with no error listener — uncaught `error` emits crash the process.
- Forgetting `await` on `pipeline(...)` — the function returns but the pipeline is still running, and exceptions become unhandled rejections.
- Treating gzip as Writable-only. It's a Transform — it has both ends.
- Setting `highWaterMark: 1` "for safety". You just made the loop 16384× slower.

**Related**
- `stream-pipeline-error-handling.md` — what to do *when* it fails.
- `readable-stream-push.md` — building a Readable from scratch.
- `writable-stream-implementation.md` — building a Writable with backpressure.

## Variants

1. **Add encryption** — slot `crypto.createCipheriv('aes-256-gcm', key, iv)` between gzip and write. Now you have an at-rest-encrypted compressed file. Show that Transform streams compose linearly.

2. **HTTP upload streaming** — replace `fs.createReadStream` with `req` (an `IncomingMessage`, which is a Readable) and `fs.createWriteStream` with an S3 multipart-upload Writable. The pipeline shape is identical; only the endpoints change.

3. **Tee / multi-sink** — gzip the file *and* compute its SHA-256 in parallel. Requires `PassThrough` plus two separate pipelines reading from a shared source, or a custom Transform that updates a hash while passing the chunk through.

## Revision notes

> **stream pipeline — 60 second recap**
> - Four types: Readable / Writable / Duplex / Transform.
> - Always use `pipeline` (callback or `node:stream/promises`) — never raw `.pipe()` in prod.
> - `pipeline` auto-destroys every stream on error → no FD leaks.
> - Backpressure: downstream returns `false` from `write()`, producer pauses until `'drain'`. `pipe`/`pipeline` handles this for you.
> - `highWaterMark` default = 16 KiB bytes / 16 objects (`objectMode: true`).
> - Async generator (`async function*`) is a drop-in Transform inside `pipeline`.
> - `AbortSignal` cancels the whole chain.
> - Trap: forgetting `await` on `pipeline` → silent failure.
