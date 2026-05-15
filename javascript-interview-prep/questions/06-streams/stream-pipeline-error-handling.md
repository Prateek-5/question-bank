# Stream Pipeline Error Handling & Teardown

## Source
- codedamn "Node.js Stream Pipeline Lab II": https://codedamn.com/problem/3KceNguv5qrbVJ27tnKd3
- Canonical Node.js docs: `stream.pipeline`, `stream.finished`, `Readable.destroy`.

## Why this question matters in interviews
Round 1 of streams is "build a pipeline." Round 2 is **"what happens when it breaks?"** — and that's where most candidates fall apart. As a backend engineer you'll write code that copies S3 objects, gunzips uploads, parses NDJSON, and writes to Postgres COPY. If one stage errors, you must (a) propagate the error to your caller, (b) destroy every other stream so file descriptors / DB connections / sockets aren't leaked, and (c) avoid the dreaded `Error [ERR_STREAM_PREMATURE_CLOSE]` and `EPIPE` storm. This question separates engineers who *use* streams from engineers who *operate* them.

## Concepts involved

### Where errors come from
- **Source error** (Readable): `ENOENT`, `EACCES`, network reset.
- **Transform error**: invalid gzip data, parse failure, exception thrown inside `_transform`.
- **Sink error** (Writable): `ENOSPC` (disk full), `EPIPE` (peer closed), DB write failure.
- **Abort**: user-triggered `AbortController.abort()`.
- **Premature close**: a stream `end`s before its peer expects it.

### Why `.pipe()` leaks
```js
src.pipe(t).pipe(dst);
dst.on('error', (e) => console.error(e));  // catches dst error only
// src and t are NOT destroyed → src keeps reading, file descriptor leaks
// until GC kicks in (which may be never under load).
```
`pipe()` only forwards `end` — not `error`. Each stream needs its own listener.

### Why `pipeline` is correct
`stream.pipeline(...streams, cb)` does four things:
1. Wires up `pipe()` between consecutive pairs.
2. Listens for `error` on **every** stream.
3. On the first error, calls `destroy(err)` on **all** other streams.
4. Invokes the callback (or rejects the promise) exactly once with that error.

### `stream.finished` — single-stream cleanup
When you only have one stream (e.g. an HTTP response), use:
```js
const { finished } = require('node:stream/promises');
await finished(res);          // resolves on 'end' / 'finish', rejects on 'error'
```
Saves you from manually wiring `'end'` / `'error'` / `'close'`.

### `AbortSignal` integration (Node 16+)
`pipeline(src, t, dst, { signal })` — abort destroys all streams with `AbortError` (`err.code === 'ABORT_ERR'`).

### `autoDestroy` (default `true` since Node 14)
Streams now auto-destroy on `end`/`finish`. Old advice "always call `destroy()`" is mostly obsolete inside `pipeline`. You still need it when you bail out manually.

## Brute force approach
Attach `.on('error', ...)` to every stream by hand, and inside each handler call `.destroy()` on the others. Works, but you'll forget one, the listeners might fire twice, and `EventEmitter` will warn about "possible memory leak detected." Don't do this in production.

## Optimal approach
Use `stream.pipeline` (promise form). Wrap in `try/catch`. Inspect `err.code` to react differently to `ABORT_ERR` vs I/O errors. For long-running pipelines, attach an `AbortSignal` driven by a timeout or external cancel.

## Solution (JavaScript)

```js
'use strict';
const fs = require('node:fs');
const zlib = require('node:zlib');
const { pipeline } = require('node:stream/promises');
const { setTimeout: delay } = require('node:timers/promises');

/**
 * Gunzip a file with full error handling + cancellation.
 * @param {string} src      path to .gz file
 * @param {string} dst      output path
 * @param {object} [opts]
 * @param {number} [opts.timeoutMs]
 * @param {AbortSignal} [opts.signal]
 * @returns {Promise<{ ok: true } | { ok: false, reason: string, code?: string }>}
 */
async function safeGunzip(src, dst, { timeoutMs = 30_000, signal } = {}) {
  const ac = new AbortController();

  // Compose external signal with internal timeout.
  if (signal) signal.addEventListener('abort', () => ac.abort(signal.reason));
  const timer = setTimeout(() => ac.abort(new Error('timeout')), timeoutMs);

  try {
    await pipeline(
      fs.createReadStream(src),
      zlib.createGunzip(),
      fs.createWriteStream(dst),
      { signal: ac.signal },
    );
    return { ok: true };
  } catch (err) {
    // Classify the failure for the caller.
    if (err.code === 'ABORT_ERR') return { ok: false, reason: 'aborted', code: err.code };
    if (err.code === 'ENOENT')    return { ok: false, reason: 'source missing', code: err.code };
    if (err.code === 'ENOSPC')    return { ok: false, reason: 'disk full', code: err.code };
    if (err.code === 'Z_DATA_ERROR') return { ok: false, reason: 'corrupt gzip', code: err.code };
    return { ok: false, reason: err.message, code: err.code };
  } finally {
    clearTimeout(timer);
  }
}

// Demo: bad gzip header should be classified, not crash.
(async () => {
  await fs.promises.writeFile('./bad.gz', Buffer.from('not actually gzip'));
  const result = await safeGunzip('./bad.gz', './out.txt');
  console.log(result); // { ok: false, reason: 'corrupt gzip', code: 'Z_DATA_ERROR' }
})();
```

Single-stream cleanup with `finished`:
```js
const { finished } = require('node:stream/promises');
const res = await fetch(url);                     // Response with body stream
try {
  await finished(res.body);                       // wait for clean end
} catch (err) {
  // network reset, premature close, etc.
}
```

## Step-by-step dry run

Input: `./bad.gz` contains 17 bytes of plain ASCII (not a gzip header).

| Step | Event | What happens |
| --- | --- | --- |
| 1 | `pipeline` starts | All three streams open. FD count +2 (read + write). |
| 2 | Readable emits first chunk | 17 bytes flow into Gunzip. |
| 3 | Gunzip's native decoder sees bad header | Emits `error` event with `code: 'Z_DATA_ERROR'`. |
| 4 | `pipeline` catches it | Calls `destroy(err)` on Readable and Writable. |
| 5 | Both other streams close | FDs released. No `EPIPE` because pipeline destroyed both ends. |
| 6 | Promise rejects | Our `catch` classifies: `'corrupt gzip'`. |
| 7 | `finally` runs | `clearTimeout(timer)` — important, else timer keeps event loop alive 30s. |

Contrast with raw `.pipe()`: step 4 wouldn't happen. The Readable would keep pumping bytes; the Writable might still be open; you'd see `Unhandled 'error' event` and the process would die.

## Important takeaways

**Syntax to memorize**
- `pipeline(...streams, { signal })` from `node:stream/promises`. Always `await`.
- `err.code` is your friend: `ABORT_ERR`, `ENOENT`, `ENOSPC`, `EPIPE`, `Z_DATA_ERROR`, `ERR_STREAM_PREMATURE_CLOSE`.
- `finished(stream)` for one-stream waits.

**Patterns to reuse**
- "Classify error by code, return structured result" — better than letting raw errors leak across layers.
- Compose internal timeout `AbortController` with the caller's `signal`. This is the Node-idiomatic cancellation pattern.
- Always put `clearTimeout` in `finally`. Forgetting it leaks an active handle.

**Common mistakes**
- `src.pipe(t).pipe(dst)` with a single `.on('error')` — leaks the other two streams.
- Not awaiting `pipeline` → the surrounding `try/catch` doesn't see the rejection; it becomes an unhandled rejection that crashes Node (in 2026 defaults).
- Calling `.destroy()` from inside an error handler that you wired manually — easy to call it twice, which triggers `ERR_MULTIPLE_CALLBACK`.
- Forgetting that `EPIPE` from a Writable usually means the *peer* (Readable or downstream) closed — fix the *cause*, don't swallow it.
- Returning success when a Writable's `'finish'` event hasn't fired. `pipeline` only resolves after `'finish'`; manual code often resolves on `'end'` of the source — that's wrong.

**Related**
- `stream-pipeline-lab.md` — the happy-path version.
- `writable-stream-implementation.md` — `_write(chunk, enc, cb)` and the dreaded "double callback" error.

## Variants

1. **Retry transient failures** — wrap `pipeline` in a retry loop that re-runs on `EPIPE` or `ECONNRESET` with exponential backoff. The trick: each retry must reopen the source stream from scratch — streams are not re-usable after destroy.

2. **Fan-in (multiple sources → one sink)** — `pipeline` only takes a linear chain. For fan-in you spawn N pipelines into a `PassThrough` and pipe that into the sink. Make sure to only `end()` the PassThrough after all sources finish — otherwise the sink closes early.

3. **Custom finalizer / metrics** — wrap `pipeline` so that on both success and failure you log byte counts, duration, and the stage that failed. Test: which stage was destroyed first? Use `pre-error` listeners on each stage to attribute the failure.

## Revision notes

> **pipeline error handling — 60 second recap**
> - `pipe()` leaks on error; `pipeline()` doesn't.
> - `pipeline` destroys every stream on the first error → no FD leaks.
> - Always `await` the promise form; always wrap in `try/catch`.
> - Classify by `err.code`: `ABORT_ERR`, `ENOENT`, `ENOSPC`, `EPIPE`, `Z_DATA_ERROR`.
> - Compose external `AbortSignal` with internal timeout via a new `AbortController`.
> - `clearTimeout` in `finally` — else the process won't exit.
> - `finished(stream)` for single-stream waits (HTTP response, fs read).
> - Trap: pipe + one error listener; not awaiting pipeline; calling destroy twice manually.
