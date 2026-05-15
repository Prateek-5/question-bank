# Demonstrate backpressure — when `writable.write()` returns `false`

## Source
- Node.js docs: https://nodejs.org/api/stream.html#buffering
- Node.js "Backpressuring in Streams" guide: https://nodejs.org/en/learn/modules/backpressuring-in-streams
- Canonical Node interview question — appears in every Node.js senior screen (Pluralsight, NodeSchool, BFE-node).

## Why this question matters in interviews
Backpressure is *the* differentiator between a junior who has "used streams" and a senior who actually understands them. Every backend role that touches file ingestion, log shipping, S3 uploads, CSV import, or proxying responses asks some flavor of this. The candidate either says "you write to the stream and it just works" (junior) or names `highWaterMark`, the `false` return value from `.write()`, and the `'drain'` event (senior). Get this wrong and the team assumes you'll OOM the box the first time a slow consumer hits production. As a backend engineer this question maps directly to: "what happens when our DB writer is slower than our HTTP upload reader?"

## Concepts involved

### Syntax to lock in
```js
const fs = require('fs');
const writable = fs.createWriteStream('out.txt', { highWaterMark: 16 * 1024 });

function produce() {
  let i = 0;
  function next() {
    let ok = true;
    while (i < 1e6 && ok) {
      const last = i === 1e6 - 1;
      // .write() returns false once internal buffer >= highWaterMark
      ok = writable.write(`line ${i}\n`, 'utf8', last ? writable.end.bind(writable) : undefined);
      i++;
    }
    if (i < 1e6) {
      // back off; resume when consumer has drained
      writable.once('drain', next);
    }
  }
  next();
}
produce();
```

### Runtime / engine behavior
- Every Writable stream has an internal buffer measured against `options.highWaterMark` (default 16 KB for byte streams, 16 *objects* for objectMode).
- `writable.write(chunk)` **always queues** the chunk and returns a boolean. Return value is purely advisory:
  - `true` → buffer is below `highWaterMark`, keep going.
  - `false` → buffer is at or above `highWaterMark`. **You should stop and wait for `'drain'`.**
- `'drain'` is emitted once the buffer has been flushed below `highWaterMark`.
- Ignoring the `false` return is **not a correctness bug** — Node keeps buffering — it's a **memory bug**. A 5 MB/s producer feeding a 1 MB/s consumer can grow the buffer unbounded until the process OOMs.
- On `Readable.pipe(Writable)`, Node wires this up automatically: when the dest writable returns `false`, the source readable is paused; on `'drain'`, it resumes. The pipe machinery *is* backpressure.

### Edge cases (interview traps)
1. **Object-mode `highWaterMark` is in object count, not bytes.** A buffer of 16 entries can still be gigabytes if each entry is huge. Mention this.
2. **`.write()` returning `false` does NOT mean the write failed.** The chunk is still in the buffer. Beginners assume it dropped — they'd then retry, causing duplicates. Correct: just stop calling `write` until `drain`.
3. **The producer must use `.once('drain', ...)`, not `.on('drain', ...)`** — otherwise listeners pile up across iterations and you'll hit `MaxListenersExceededWarning`.
4. **Synchronous tight loop with `.write()` will exceed `highWaterMark` immediately** — that's exactly the scenario this question is testing. The first iteration may return true, the next 200 return false, and a naive impl just ignores all of them.
5. **`writable.end()` flushes and closes** — calling `.write()` after `.end()` throws `ERR_STREAM_WRITE_AFTER_END`.
6. **`cork()/uncork()`** intentionally batches small writes. Different mechanism, sometimes confused with backpressure — clarify if asked.
7. **`'drain'` won't fire if you never exceeded `highWaterMark`** — if your producer is naturally slow, you'll never see it. That's fine.

## Brute force approach
"Just call `writable.write()` in a loop." This is the wrong answer. The code *works* for small inputs because Node buffers everything. It catastrophically fails when input scale > `highWaterMark`: memory grows unbounded, GC thrashes, latency spikes, eventually OOMKilled. Many candidates write this then say "it works on my machine." The point of the question is precisely this gap.

## Optimal approach
Treat the wrapper as a **two-state producer**: writing-mode and waiting-mode. Wrap the write loop in a function. After each `.write()`, check the return value. If `false`, attach a one-shot `'drain'` listener that re-enters the loop, and return immediately. The internal buffer becomes the natural rate-limiter, with `highWaterMark` as the throttle setpoint. O(1) extra memory beyond the buffer itself.

## Solution (JavaScript)

```js
const fs = require('fs');

/**
 * Stream `count` lines into `dest` while respecting backpressure.
 * @param {import('stream').Writable} dest
 * @param {number} count
 * @returns {Promise<void>}
 */
function streamLines(dest, count) {
  return new Promise((resolve, reject) => {
    let i = 0;
    dest.on('error', reject);
    dest.on('finish', resolve);

    function write() {
      let canContinue = true;
      while (i < count && canContinue) {
        const chunk = `line ${i}\n`;
        i++;
        if (i === count) {
          // last chunk — pass via end() so finish fires after flush
          dest.end(chunk);
        } else {
          // .write() returns false when buffer >= highWaterMark
          canContinue = dest.write(chunk);
        }
      }
      if (i < count) {
        // producer too fast — wait for buffer to drain, then resume
        dest.once('drain', write);
      }
    }
    write();
  });
}

// usage
const out = fs.createWriteStream('big.txt', { highWaterMark: 16 * 1024 });
streamLines(out, 1_000_000).then(() => console.log('done'));
```

## Step-by-step dry run

Setup: a slow consumer (writes to disk at ~5 MB/s) with `highWaterMark: 16384` (16 KB), producer wants to push 1M lines averaging 10 bytes each (~10 MB total).

- **Iteration 0..1638**: `.write()` returns `true`. Loop tight-iterates. ~16 KB buffered.
- **Iteration 1639**: buffer now at `highWaterMark`. `.write()` returns `false`. `canContinue = false`. Loop exits.
- `i < count`, so we attach `'drain'` once-listener. The function returns. Event loop is free.
- libuv flushes the buffer to disk over several ms.
- Once buffer < `highWaterMark`, the Writable emits `'drain'`.
- `write()` re-enters from iteration 1639. The loop resumes from where it stopped.
- This cycle repeats ~600 times until `i === count`. The last chunk goes through `.end()`, which flushes + emits `'finish'`, which resolves the Promise.

Net: memory stays bounded at ~16 KB instead of buffering all 10 MB. Throughput is identical (still disk-bound), but the process is stable.

## Important takeaways

**Syntax to memorize**
- The `while (i < n && canContinue)` skeleton — tight loop until `.write()` returns false.
- `dest.once('drain', write)` — **once, not on**. Re-entrant producer.
- The last chunk goes through `.end(chunk)`, not `.write(chunk) + .end()` — saves an event loop tick and guarantees `'finish'` fires after the final flush.

**Patterns to reuse**
- Same "produce-until-buffer-full, wait-for-signal, resume" pattern is how `Readable.pipe(Writable)` works internally. Knowing the manual form means you can debug pipe stalls.
- It also generalizes: TCP socket `.write()` returns `false` under network congestion → wait for `'drain'`. HTTP response objects are Writables → exactly the same.
- Producer-consumer with a bounded queue. Same as a Go channel with capacity, or a Rust `mpsc::sync_channel(N)`.

**Common mistakes**
- Calling `.write()` in a `for (let i = 0; i < n; i++)` loop and ignoring the return. Works in dev with 100 items, dies in prod with 10M.
- Using `.on('drain', ...)` instead of `.once('drain', ...)`. Listener leak.
- Using `setImmediate` or `process.nextTick` to "yield" between writes instead of `'drain'`. You yield to the loop, but the buffer can still grow unbounded because you never check it.
- Confusing `highWaterMark` (advisory threshold) with a hard cap. It's not a cap; writes still succeed past it. It just flips the boolean.

**Related questions**
- `stream.pipeline` error propagation (same family — pipeline encodes backpressure correctly)
- Transform stream — line parser (downstream backpressure flows up through Transform)
- Readable in flowing vs paused mode

## Variants

1. **Async iterator producer** — "Rewrite using `for await` over an async generator piped into the writable." Forces you to use `stream.pipeline(asyncGenerator, writable)` and confirm pipeline honors backpressure for AsyncIterables (it does, since Node 16).

2. **Backpressure across a TCP socket** — "Same problem but `dest` is a TCP socket and the network is the slow consumer." Identical code; the conceptual win is recognizing that backpressure is **end-to-end** when sockets are involved.

3. **Measure the buffer** — "How would you log a warning if the buffer ever hits 2× `highWaterMark`?" Inspect `writable.writableLength` and `writable.writableHighWaterMark` on each write. Demonstrates introspection knowledge.

## Revision notes

> **backpressure — 60 second recap**
> - `writable.write(chunk)` returns `false` when internal buffer >= `highWaterMark`.
> - That's **advisory** — chunk is still queued. Bug = ignoring it, leading to unbounded memory.
> - Producer must stop and `.once('drain', resumeFn)` until buffer drains below `highWaterMark`.
> - `Readable.pipe(Writable)` does this automatically. `stream.pipeline` too. Manual `.write()` loops don't.
> - **Trap:** `.on('drain')` leaks listeners. Use `.once`.
> - **Trap:** ignoring `false` doesn't break correctness, breaks memory. OOM in prod, fine in dev.
> - Object-mode `highWaterMark` counts entries, not bytes.
