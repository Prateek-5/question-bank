# Stream pipeline error handling & teardown

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [stream-pipeline-lab.md](./stream-pipeline-lab.md), [writable-stream-implementation.md](./writable-stream-implementation.md)
>
> **Source:** Node `stream.pipeline`, `stream.finished`. codedamn lab II.

---

## 1. Problem statement

What happens when a pipeline breaks? Propagate errors, destroy all streams, avoid `ERR_STREAM_PREMATURE_CLOSE` / `EPIPE` storms.

**Verification examples**

```js
const { pipeline, finished } = require('node:stream/promises');

// pipeline destroys all on error
try {
  await pipeline(src, transform, dst);
} catch (err) {
  console.error('one of them failed:', err);                            // all destroyed already
}

// single stream cleanup
await finished(res);                                                     // wait for 'end' or 'error'

// AbortSignal
const ac = new AbortController();
try {
  await pipeline(src, t, dst, { signal: ac.signal });
} catch (err) {
  if (err.name === 'AbortError') console.log('cancelled');
}
```

**Constraints**
- `pipe()` only forwards `end`, not `error` → fd leaks.
- `pipeline()` listens on all streams; destroys all on error.
- `AbortSignal` for user-triggered cancellation.
- `autoDestroy: true` (default Node 14+) — streams auto-destroy on end.

---

## 2. Plain-English restatement

`pipeline()` is the correct way to compose streams. It listens for errors on every stream and destroys all of them on the first error. `pipe()` doesn't — you'd leak file descriptors. `finished()` waits for a single stream's end or error.

---

## 3. Why this matters in interviews

Round 2 of streams. Tests operational depth — what happens when things break.

---

## 4. Mental model

```
   Error sources:
   - Source (Readable): ENOENT, network reset.
   - Transform: parse failure, exception in _transform.
   - Sink (Writable): ENOSPC, EPIPE, DB error.
   - Abort: user-triggered AbortController.abort().
   - Premature close: peer ends early.

   pipe() leaks:
     src.pipe(t).pipe(dst);
     dst.on('error', handler);  ← catches dst only
     src and t NOT destroyed → fd leak.

   pipeline() does it right:
     1. Wires pipe() between pairs.
     2. Listens 'error' on EVERY stream.
     3. On first error → destroy(err) all OTHERS.
     4. Invokes callback (or rejects promise) ONCE.

   finished() — single stream:
     await finished(stream);
     // resolves on 'end' or 'finish'
     // rejects on 'error'

   AbortSignal:
     pipeline(..., { signal });
     ac.abort() → destroys all with AbortError.

   autoDestroy (Node 14+ default):
     Streams auto-destroy on end/finish.
     Old advice "always destroy()" mostly obsolete inside pipeline.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why does `src.pipe(t).pipe(dst)` leak fds on error?
> 2. What's `stream.finished` good for?
> 3. How does `AbortSignal` interact with `pipeline`?

---

## 6. Brute force — walked through

### Wrong attempt 1: `.on('error')` on each stream manually
Easy to miss one; double-listener bugs; `EventEmitter` warns.

### Wrong attempt 2: `try/catch` around `src.pipe(t).pipe(dst)`
`pipe` doesn't throw; errors emit asynchronously.

### Wrong attempt 3: ignore `'error'`
Uncaught 'error' crashes process (or warning then crash in strict).

---

## 7. The unlocking insight

> **`pipeline()` is the only correct way to compose streams with error handling. `finished()` for single-stream cleanup. `AbortSignal` for user cancellation. `pipe()` is legacy and unsafe.**

Three properties:

1. **`pipeline` listens everywhere** + destroys on error.
2. **`finished` for single stream** end/error.
3. **`AbortSignal`** integrated cancellation.

---

## 8. Solution (annotated)

```js
const { pipeline, finished } = require('node:stream/promises');

// Composing with error propagation
async function gzipFile(src, dst) {
  try {
    await pipeline(                                                      // step 1: pipeline
      fs.createReadStream(src),
      zlib.createGzip(),
      fs.createWriteStream(dst),
    );
  } catch (err) {                                                         // step 2: single catch
    // All streams already destroyed.
    if (err.code === 'ENOENT') throw new Error(`source missing: ${src}`);
    throw err;
  }
}

// Single stream cleanup
async function readBody(res) {
  let body = '';
  res.on('data', (chunk) => body += chunk);
  await finished(res);                                                    // step 3: await end/error
  return body;
}

// AbortSignal — user-triggered cancellation
async function processWithTimeout(src, dst, timeoutMs) {
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), timeoutMs);
  try {
    await pipeline(src, dst, { signal: ac.signal });                     // step 4: signal
  } catch (err) {
    if (err.name === 'AbortError') {
      console.log('timed out');
    } else throw err;
  } finally {
    clearTimeout(timer);
  }
}

// Manual stream — when pipeline isn't enough
async function processStreaming(req) {
  try {
    for await (const chunk of req) {                                     // step 5: for-await + try/catch
      await handle(chunk);
    }
  } catch (err) {
    req.destroy(err);
    throw err;
  }
}
```

**Try it yourself**

```js
// pipe() vs pipeline()
const src = fs.createReadStream('input.log');
const gzip = zlib.createGzip();
const dst = fs.createWriteStream('out.gz');

// BAD: leaks fds on error
src.pipe(gzip).pipe(dst);
dst.on('error', console.error);   // catches dst only — src and gzip stay open

// GOOD: cleans up all on error
await pipeline(src, gzip, dst);    // all destroyed on any failure

// Premature close
const incomplete = fs.createReadStream('input.log');
incomplete.on('data', (c) => {});
incomplete.destroy();              // peer closes early
// Without finished/pipeline: silent leak; with: 'close' event detected.
```

---

## 9. Step-by-step dry run

```
pipeline(src, gzip, dst):
  Wire src.pipe(gzip), gzip.pipe(dst).
  Attach 'error' listener to src, gzip, dst.

Normal flow:
  src reads → pushes to gzip → compresses → pushes to dst → writes.
  src emits 'end' → gzip emits 'end' → dst.end() → emits 'finish'.
  pipeline resolves.

Error scenario (gzip hits invalid data):
  gzip emits 'error'.
  pipeline's handler fires:
    1. Calls src.destroy(err) → src emits 'close'.
    2. Calls dst.destroy(err) → dst emits 'close'.
    3. gzip already destroyed.
    4. pipeline promise rejects with gzip's error.
  All fds closed.

vs naive src.pipe(gzip).pipe(dst):
  gzip emits 'error' → no listener (typically) → uncaughtException → process exit.
  Or: handler on gzip only → src and dst keep open → fd leak.

AbortSignal:
  ac.abort() during read:
    pipeline destroys all streams with AbortError.
    promise rejects with err.name === 'AbortError'.

finished(stream):
  Resolves when stream emits 'end' (Readable) or 'finish' (Writable).
  Rejects on 'error' or 'close' (premature).
```

---

## 10. Common confusion + traps

1. **`pipe()` for production** — leaks fds.
2. **Single error handler** — needs one per stream OR pipeline.
3. **Forget to await `pipeline`** — promise floats; errors lost.
4. **Multiple `pipe` to same dst** — undefined behavior.
5. **`destroy()` inside error handler** — pipeline handles it; you'd cause double-destroy.
6. **`'close'` vs `'end'`** — `close` always fires (incl. errors), `end`/`finish` only on success.
7. **`autoDestroy: false`** — manual destroy required.

---

## 11. Senior follow-ups & variants

### Variant 1 — `stream.finished()` for single stream
Waits for end/error; useful for HTTP req/res.

### Variant 2 — Custom error retry stage
Wrap a transform with retry-on-error logic.

### Variant 3 — Distinguish error types
`err.code === 'ENOENT'` vs `'EPIPE'` vs `AbortError`.

### Variant 4 — Graceful shutdown
SIGTERM → abort all in-flight pipelines.

### Variant 5 — Web Streams equivalent
`pipeTo()` + `pipeThrough()` + AbortSignal.

---

## 12. How to think aloud

> "`pipeline()` is the only correct way to compose streams with error handling. It does FOUR things: wires `pipe()` between consecutive pairs, listens for `'error'` on EVERY stream, on first error destroys all OTHERS, invokes callback (or rejects promise) ONCE. Naive `src.pipe(t).pipe(dst)` leaks fds because `pipe` doesn't forward errors — each stream needs its own handler. `finished(stream)` for single-stream cleanup — resolves on `end`/`finish`, rejects on `error`/premature `close`. `AbortSignal` (Node 16+) — pass to pipeline; `ac.abort()` destroys all with `AbortError`. `autoDestroy: true` (default Node 14+) — streams auto-destroy on end/finish; old 'always call destroy()' advice obsolete inside pipeline. For manual streams use `for await` with try/catch; on error, call `stream.destroy(err)`. Trap: `pipe()` in production (fd leak); missing error handler (uncaught); forgetting `await pipeline` (floating promise)."

---

## 13. 60-second revision

> - **`pipeline()` correct;** `pipe()` legacy/unsafe.
> - **`pipeline` listens all + destroys on error.**
> - **`finished(stream)` for single** — end or error.
> - **`AbortSignal`** via `{ signal }` option.
> - **`autoDestroy: true`** default — auto cleanup on end.
> - **Manual stream:** `for await` + try/catch + `stream.destroy(err)`.
> - **`'close'`** always fires; **`'end'`/`'finish'`** only on success.
> - **Trap:** pipe in prod (fd leak); missing handler; forget await.

---

**Related:** [stream-pipeline-lab.md](./stream-pipeline-lab.md) · [pipeline-error-propagation.md](./pipeline-error-propagation.md) · [writable-stream-implementation.md](./writable-stream-implementation.md) · [readable-stream-push.md](./readable-stream-push.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
