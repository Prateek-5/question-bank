# `stream.pipeline` — proper error + cleanup semantics

## Source
- Node.js docs: https://nodejs.org/api/stream.html#streampipelinesource-transforms-destination-callback
- Node.js docs (promises): https://nodejs.org/api/stream.html#streampipelinepromisifiedsource-destination-options
- Standard senior Node.js screening question — appears at any company that ships a file-processing pipeline (data ingestion, ETL, file upload services).
- Background: `pipeline()` was added in Node 10 specifically because `.pipe()` chains leak descriptors on error.

## Why this question matters in interviews
This question separates engineers who copy-paste `.pipe()` chains from those who've actually shipped a Node server that didn't leak file descriptors over a weekend. The classic `readStream.pipe(transform).pipe(writeStream)` pattern is **broken on error**: a failure mid-chain doesn't destroy upstream sources, so file handles and sockets stay open until GC, which can be never under load. `pipeline()` fixes this by destroying every stream on first error and invoking your callback exactly once. Senior interviewers want to hear: "I don't use raw `.pipe()` chains anymore; I use `pipeline()` or `stream/promises`'s `pipeline`." Get this wrong and they assume your services have descriptor leaks.

## Concepts involved

### Syntax to lock in
```js
// callback form
const { pipeline } = require('stream');
pipeline(
  fs.createReadStream('input.txt'),
  zlib.createGzip(),
  fs.createWriteStream('input.txt.gz'),
  (err) => {
    if (err) console.error('pipeline failed:', err);
    else console.log('pipeline succeeded');
  }
);

// promise form (preferred)
const { pipeline } = require('stream/promises');
await pipeline(
  fs.createReadStream('input.txt'),
  zlib.createGzip(),
  fs.createWriteStream('input.txt.gz')
);
```

### Runtime / engine behavior
- `pipeline(s1, s2, ..., sN, cb?)` wires each pair with the equivalent of `.pipe()` but also installs an `'error'` listener on every stream.
- **First error wins.** As soon as any stream emits `'error'`, pipeline calls `destroy(err)` on every stream in the chain (including the ones that haven't errored yet) and fires the callback **once**.
- All other errors after the first are swallowed (or, in newer Node versions, surfaced via `'unhandledError'`). This is by design — you only want one callback invocation.
- `destroy(err)` on a stream emits `'close'`, releases resources (file descriptor, socket), and prevents further data flow. This is the part `.pipe()` does NOT do for upstream streams on a downstream error.
- The promise form returns a `Promise<void>` that resolves on success and rejects on the first error — same semantics, modern syntax.
- Backpressure: pipeline respects backpressure between adjacent pairs (each is internally piped). End-to-end backpressure works.
- Pipeline supports async iterables, generators, async generators, and Readable/Writable streams as members since Node 12+ — extremely composable.

### Edge cases (interview traps)
1. **Why `.pipe()` leaks.** `a.pipe(b).pipe(c)`. If `c` errors, Node closes `c`, but `a` keeps reading and `a.pipe(b)` keeps writing to `b`. The `'unpipe'` event isn't enough; `a` is never destroyed. The file descriptor for `a` lives until GC.
2. **Pipeline still requires you to handle the error.** It doesn't *suppress* errors, it just consolidates them into one callback. Forgetting `if (err) ...` → silent failure.
3. **Callback is called exactly once, regardless of how many streams error.** Don't write code that assumes a callback per stream.
4. **`process.on('uncaughtException')` doesn't fire** for stream errors handled by pipeline — pipeline catches them. New devs think their error logging is working when it isn't because they only log in `uncaughtException`.
5. **Async generators in the middle.** Pipeline accepts `async function*` as a stage since Node 12.10+. Errors thrown inside the generator propagate just like stream errors. Very useful for ad-hoc transforms.
6. **`AbortSignal` support.** `pipeline(s1, s2, dest, { signal })` aborts the whole chain when the signal fires. Use this for request-cancellation in HTTP servers.
7. **`pipeline()` doesn't return the streams.** If you need a handle on, say, the gzip stream for stats, capture it before passing it in.
8. **Errors before pipeline starts.** If a stream is already destroyed when passed in, pipeline calls cb synchronously with the error. Don't assume async.

## Brute force approach
The naive answer is `a.pipe(b).pipe(c); c.on('error', cb)`. Wrong on multiple counts:
1. Only `c`'s error reaches your handler. Errors on `a` or `b` will crash the process via `uncaughtException`.
2. If `c` errors, `a` and `b` are not destroyed — descriptor leak.
3. You'd need to install `'error'` on every stream and manually destroy the others. That code is ~40 lines and always has bugs.

Some candidates "fix" this with `.on('error', err => { a.destroy(); b.destroy(); cb(err); })` for each stream. It works for 3 streams but doesn't generalize, you'll double-call cb, and you'll forget one stream. **`pipeline()` is the right answer.**

## Optimal approach
Use `stream.pipeline` (callback form) or `stream/promises`.`pipeline` (Promise form). One call, automatic error propagation, automatic destruction, automatic cleanup. You write the failure handler once, at the call site, instead of N error handlers across N streams.

## Solution (JavaScript)

```js
const fs = require('fs');
const zlib = require('zlib');
const { pipeline } = require('stream/promises');
const { Transform } = require('stream');

/**
 * Gzip a file with a "no secrets" filter that throws on a banned token.
 * Demonstrates pipeline's cleanup on Transform error.
 */
async function safeGzip(input, output) {
  const redactor = new Transform({
    transform(chunk, enc, cb) {
      if (chunk.includes('SECRET')) {
        // throwing here triggers pipeline cleanup
        return cb(new Error('Refusing to encode chunk containing SECRET'));
      }
      cb(null, chunk);
    },
  });

  try {
    await pipeline(
      fs.createReadStream(input),
      redactor,
      zlib.createGzip(),
      fs.createWriteStream(output)
    );
    console.log('gzipped successfully');
  } catch (err) {
    // pipeline has already destroyed every stream and unlinked all FDs.
    // Just decide policy: log, alert, cleanup partial output.
    console.error('pipeline failed:', err.message);
    await fs.promises.unlink(output).catch(() => {}); // remove partial .gz
    throw err;
  }
}

safeGzip('input.txt', 'input.txt.gz').catch(() => process.exitCode = 1);
```

For comparison — the broken `.pipe()` version:

```js
// DO NOT DO THIS — leaks file descriptors on error
const r = fs.createReadStream('input.txt');
const t = zlib.createGzip();
const w = fs.createWriteStream('input.txt.gz');
r.pipe(t).pipe(w);
w.on('error', (err) => console.error(err)); // misses r and t errors entirely
```

## Step-by-step dry run

Input: `input.txt` contains 1 MB of text. At offset 500 KB, the chunk includes the word `"SECRET"`. The redactor will throw.

- `pipeline()` starts the chain. `r` begins reading 64 KB chunks.
- Chunks 1-7 flow through `r → redactor → gzip → w`. Each is gzipped and written.
- Chunk 8 contains `"SECRET"`. `redactor._transform` calls `cb(new Error('Refusing...'))`.
- Stream emits `'error'`. Pipeline catches it.
- Pipeline calls `r.destroy(err)` — `r`'s file descriptor for `input.txt` is closed.
- Pipeline calls `redactor.destroy(err)`.
- Pipeline calls `gzip.destroy(err)` — releases the zlib state.
- Pipeline calls `w.destroy(err)` — closes the file descriptor for `input.txt.gz`. (The 7 chunks already written remain in `input.txt.gz` — it's a half-gzipped file. That's why we `unlink` it in the catch.)
- Pipeline rejects its returned Promise with the error.
- Our `catch` runs: unlinks the partial output, logs, rethrows.

Net: zero leaked file descriptors. With `.pipe()`, `r` would have stayed open until GC because `r` was never notified that `redactor` errored.

## Important takeaways

**Syntax to memorize**
- `const { pipeline } = require('stream/promises'); await pipeline(s1, s2, ..., sN);`
- The order is `source, ...transforms, destination`. Last arg in callback form is the cb.
- Pass `{ signal }` as final options arg to support abort.

**Patterns to reuse**
- Pipeline + async generator in the middle is the modern "shell pipe" in Node: `pipeline(readStream, async function* (src) { for await (const c of src) yield transform(c); }, writeStream)`. Composable, cancellable, leak-free.
- Wrap pipeline in a function that does cleanup on failure (delete partial output, release locks). That's the "transactional stream" pattern.

**Common mistakes**
- Using `.pipe()` chains in production code. The leak is real, just slow enough that you discover it during incidents.
- Installing `'error'` only on the last stream. Misses upstream errors → `uncaughtException`.
- Calling pipeline twice with the same writable stream → second call errors because the writable is already ended.
- Forgetting that on success the destination stream is **closed** by pipeline. Can't reuse it.
- Confusing `pipeline()` with `pipe()` in code review — the one-character difference hides a major semantic gap.

**Related questions**
- `backpressure-demo` — pipeline respects backpressure end-to-end automatically.
- `transform-line-parser` — natural middle stage in a pipeline.
- `callback-API-to-async-iterator` — async iterables compose with pipeline directly.

## Variants

1. **With AbortController** — "Cancel the pipeline if the user disconnects from the HTTP request." `pipeline(req, parser, processor, { signal: req.signal })`. Tests knowledge of cancellation propagation.

2. **Multi-tee** — "What if I need to write the same data to two destinations?" Pipeline is linear; you'd `pipeline(source, transformThatDuplicates)` and have the duplicator push to two writers, or use a `PassThrough` + manual pipes. Discuss trade-offs.

3. **Reimplement a minimal pipeline** — "Don't use Node's pipeline. Write `myPipeline(...streams, cb)` yourself." Tests deeper understanding: iterate adjacent pairs, attach `'error'` to all, on first error call `destroy(err)` on all and cb-once. ~20 lines, classic senior whiteboard.

## Revision notes

> **pipeline-error-propagation — 60 second recap**
> - `stream.pipeline(s1, ..., sN, cb)` — or `await require('stream/promises').pipeline(...)`.
> - On first error: destroys **every** stream, calls cb **once** with the error. Cleanup is automatic.
> - `.pipe()` chains DO NOT do this — they leak file descriptors / sockets when downstream errors.
> - Always prefer `pipeline()` over `.pipe()` in production.
> - Promise form is the modern syntax — composes with `try/catch` and `await`.
> - Supports async generators as stages; supports `{ signal }` for cancellation.
> - **Trap:** partial output files survive failure — clean them up in `catch`.
> - **Trap:** `.pipe()` + `'error'` on last stream silently misses upstream errors.
