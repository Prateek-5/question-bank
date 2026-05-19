# `stream.pipeline` — proper error + cleanup

> **Difficulty:** Senior   |   **Time:** ~10 min   |   **Prereqs:** [stream-pipeline-lab.md](./stream-pipeline-lab.md), [stream-pipeline-error-handling.md](./stream-pipeline-error-handling.md)
>
> **Source:** Node 10+ added `stream.pipeline` to fix `.pipe()` chain fd leaks. Senior Node screening.

---

## 1. Problem statement

Use `stream.pipeline` (or `stream/promises#pipeline`) to compose streams with proper error propagation and cleanup.

**Verification examples**

```js
// Callback form
const { pipeline } = require('node:stream');
pipeline(src, gzip, dst, (err) => {
  if (err) console.error('failed:', err);
  else console.log('done');
});

// Promise form (preferred)
const { pipeline } = require('node:stream/promises');
await pipeline(src, gzip, dst);
```

**Constraints**
- `pipe()` chains LEAK file descriptors on error.
- `pipeline` listens for errors on every stream + destroys all on first error.
- Callback invoked exactly once.
- Promise form supports `await` + AbortSignal.

---

## 2. Plain-English restatement

`pipeline()` wires `pipe` between consecutive streams, listens for errors on every stream, destroys ALL on the first error, and invokes callback (or rejects promise) exactly once. `pipe()` chains don't do any of this — they leak fds on failure.

---

## 3. Why this matters in interviews

THE difference between "shipped streams" and "shipped streams that didn't leak fds over a weekend." Top-tier senior signal.

---

## 4. Mental model

```
   pipeline(s1, s2, ..., sN, cb?):
     For each pair: pipe (s_i, s_{i+1}).
     For each stream: listen 'error'.
     On first error:
       1. Call destroy(err) on ALL streams.
       2. Invoke cb(err) ONCE.
       3. Suppress further errors.
     On natural end:
       cb() — no error.
   
   Two forms:
   - Callback: pipeline(s1, ..., cb).
   - Promise: const { pipeline } = require('stream/promises'); await pipeline(...).
   
   AbortSignal (Node 16+):
     await pipeline(s1, ..., { signal });
     ac.abort() → destroy all with AbortError.

   vs .pipe() chains:
     src.pipe(t).pipe(dst);
     dst.on('error', handler);   ← only handles dst
     src and t NOT destroyed → fd leak.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why does `src.pipe(t).pipe(dst)` leak fds on error?
> 2. How many times can `pipeline`'s callback fire?
> 3. What does AbortSignal do to a running pipeline?

---

## 6. Brute force — walked through

### Wrong attempt 1: `.pipe()` chain
Leaks fds when error mid-chain.

### Wrong attempt 2: `.on('error')` on each stream manually
Easy to miss one; double-listener bugs.

### Wrong attempt 3: ignore error event
Uncaught 'error' crashes process.

---

## 7. The unlocking insight

> **`pipeline()` listens on all + destroys all on first error + callback once. Promise form for async/await. AbortSignal for user cancellation. Replace `.pipe()` chains.**

Three properties:

1. **Listen + destroy all** on error.
2. **Callback fires once** — first error or success.
3. **Promise form + AbortSignal** for modern code.

---

## 8. Solution (annotated)

```js
const fs = require('node:fs');
const zlib = require('node:zlib');
const { pipeline } = require('node:stream/promises');

async function gzipFile(src, dst) {
  await pipeline(                                                        // step 1: composed stages
    fs.createReadStream(src),
    zlib.createGzip(),
    fs.createWriteStream(dst),
  );
}

// With AbortSignal
async function gzipWithTimeout(src, dst, ms) {
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), ms);
  try {
    await pipeline(                                                      // step 2: signal
      fs.createReadStream(src),
      zlib.createGzip(),
      fs.createWriteStream(dst),
      { signal: ac.signal },
    );
  } finally {
    clearTimeout(t);
  }
}

// Callback form (legacy)
const { pipeline: pipelineCb } = require('node:stream');
pipelineCb(src, gzip, dst, (err) => {
  if (err) console.error('failed:', err);
  else console.log('done');
});
```

**Try it yourself**

```js
// Pipe vs pipeline comparison
// BAD: pipe chain
src.pipe(zlib.createGzip()).pipe(dst);
dst.on('error', (e) => console.error(e));   // catches dst only
// If gzip errors → src and dst stay open → fd leak.

// GOOD: pipeline
await pipeline(src, zlib.createGzip(), dst);
// All errors caught; all streams destroyed; promise resolves once.

// Async iterable as source
const { Readable } = require('node:stream');
await pipeline(
  Readable.from(asyncGenerator()),
  transformStream,
  dst,
);

// Async function as transform stage
await pipeline(
  src,
  async function* (source) {
    for await (const chunk of source) yield chunk.toString().toUpperCase();
  },
  dst,
);
```

---

## 9. Step-by-step dry run

```
await pipeline(src, gzip, dst):

Setup:
  pipe src → gzip, gzip → dst.
  Listen 'error' on src, gzip, dst.

Normal path:
  src reads → gzip compresses → dst writes.
  Each step's backpressure respected.
  src emits 'end' → gzip ends → dst ends → 'finish'.
  pipeline resolves.

Error scenario: gzip emits 'error' (invalid input).
  pipeline's handler fires:
    1. src.destroy(err) — close fd.
    2. gzip already destroyed (it emitted error).
    3. dst.destroy(err) — close fd.
  Promise rejects with err.
  Subsequent errors on src/dst SUPPRESSED (already handled).

vs raw .pipe() chain:
  gzip emits 'error':
    src and dst NOT notified.
    src keeps reading → fd leak.
    dst keeps waiting → fd leak.
    'error' on gzip with no listener → uncaughtException → crash.

AbortSignal:
  ac.abort() during read:
    pipeline destroys all with AbortError.
    Promise rejects with err.name === 'AbortError'.
```

---

## 10. Common confusion + traps

1. **`.pipe()` for production** — leaks fds.
2. **Forget `await pipeline`** — floating promise; errors silently swallowed.
3. **Callback form fires twice** — never; designed to fire once.
4. **Multiple `pipeline` on same stream** — undefined.
5. **`autoDestroy: false`** — manual cleanup required.
6. **Mix `pipe` and `pipeline`** — confusing; pick one.
7. **Async transform errors** — generator throws → pipeline rejects.

---

## 11. Senior follow-ups & variants

### Variant 1 — Async iterable / generator stages
`pipeline(asyncGenerator, async function*(src) { ... }, dst)`.

### Variant 2 — `stream.finished`
Single stream cleanup; not for pipeline composition.

### Variant 3 — AbortController
User cancellation via `{ signal }`.

### Variant 4 — Web Streams equivalent
`readable.pipeThrough(t).pipeTo(writable)` — same idea.

### Variant 5 — Custom error transformation
Wrap pipeline call to translate error types.

---

## 12. How to think aloud

> "`pipeline()` is the only correct way to compose streams in production. It wires `pipe` between consecutive pairs, attaches `'error'` listener to every stream, on first error calls `destroy(err)` on all streams (closing fds), and invokes callback (or rejects promise) exactly once. `.pipe()` chains LEAK fds on error because `pipe` only forwards `end`, not `error` — a failure mid-chain leaves upstream readers and downstream writers open. Promise form (`stream/promises#pipeline`) for `async/await`. AbortSignal (Node 16+) via `{ signal }` option — `ac.abort()` destroys all with `AbortError`. Modern code can put `Readable.from(asyncGenerator)` as a source or use `async function*(source) { for await ... yield }` as a transform stage. `stream.finished(stream)` is the single-stream version (await end/error/close). Trap: `.pipe()` for production (fd leak); forgetting `await` (floating promise); manual `.on('error')` on each (miss one and crash); mixing pipe and pipeline."

---

## 13. 60-second revision

> - **`pipeline()` correct;** `.pipe()` chains leak fds.
> - **Listens 'error' on all** + destroys all on first.
> - **Callback fires once** — error or success.
> - **Promise form for async/await:** `stream/promises#pipeline`.
> - **`{ signal }`** for AbortSignal.
> - **Async iterables/generators** as stages.
> - **`stream.finished`** for single stream.
> - **Trap:** `.pipe()` prod; forget await; mix pipe/pipeline.

---

**Related:** [stream-pipeline-lab.md](./stream-pipeline-lab.md) · [stream-pipeline-error-handling.md](./stream-pipeline-error-handling.md) · [writable-stream-implementation.md](./writable-stream-implementation.md) · [readable-stream-push.md](./readable-stream-push.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
