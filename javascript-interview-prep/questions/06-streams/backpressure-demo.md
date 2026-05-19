# Backpressure — `writable.write()` returns `false`

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [`concepts/streams.md`](../../concepts/streams.md), [readable-stream-push.md](./readable-stream-push.md)
>
> **Source:** Node docs "Backpressuring in Streams". Every Node senior screen.

---

## 1. Problem statement

`writable.write(chunk)` returns `false` when the buffer hits `highWaterMark`. Producer must stop and wait for `'drain'` event.

**Verification examples**

```js
const fs = require('fs');
const out = fs.createWriteStream('big.txt', { highWaterMark: 16 * 1024 });

function produce() {
  let i = 0;
  function next() {
    let canContinue = true;
    while (i < 1e6 && canContinue) {
      const chunk = `line ${i}\n`;
      i++;
      if (i === 1e6) out.end(chunk);
      else canContinue = out.write(chunk);                                // false → stop
    }
    if (i < 1e6) out.once('drain', next);                                  // resume on drain
  }
  next();
}
```

**Constraints**
- `write()` returns `false` when buffer ≥ `highWaterMark`.
- Return value is **advisory** — chunk still queued.
- Ignoring it doesn't break correctness; breaks MEMORY (unbounded).
- Use `.once('drain')`, not `.on('drain')` — listener leak.

---

## 2. Plain-English restatement

Every Writable has an internal buffer. When you write faster than it drains, the buffer fills. `write()` returns `false` to tell you "I'm full — pause." If you ignore, the buffer grows unbounded and you OOM. `Readable.pipe(Writable)` does this automatically; manual loops don't.

---

## 3. Why this matters in interviews

The differentiator between "used streams" and "understands streams." Anyone touching file ingestion, log shipping, S3 uploads needs this.

---

## 4. Mental model

```
   Writable internal buffer:
   ┌──────────────────────────────────────┐
   │ [chunk1][chunk2][chunk3]...          │ ← size
   │                            ↑          │
   │                       highWaterMark   │
   └──────────────────────────────────────┘

   write(chunk):
     - Queues chunk in buffer (always).
     - Returns true if size < highWaterMark.
     - Returns false if size >= highWaterMark.
     - Return value is ADVISORY.

   Ignoring false:
     - Correctness: fine — chunks still queue.
     - Memory: BUG — buffer grows unbounded → OOM.

   Correct pattern:
     while (i < n && canContinue):
       canContinue = writable.write(chunk)
     if (i < n): writable.once('drain', resume)

   `Readable.pipe(Writable)`:
     - Built-in: handles backpressure.
     - When write returns false → pauses readable.
     - On drain → resumes.

   highWaterMark:
     - Byte streams: 16 KB default.
     - Object mode: 16 objects default. NOT bytes — entries!
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Does `write()` returning `false` mean the chunk was dropped?
> 2. What's the difference between `.on('drain')` and `.once('drain')`?
> 3. Why does `for (i = 0; i < n; i++) writable.write(...)` work in dev but die in prod?

---

## 6. Brute force — walked through

### Wrong attempt 1: `for` loop ignoring return
```js
for (let i = 0; i < 1e6; i++) writable.write(`line ${i}\n`);
```
Buffer grows unbounded; OOM at scale.

### Wrong attempt 2: `.on('drain')` instead of `.once`
Listener leak — `MaxListenersExceededWarning`.

### Wrong attempt 3: `setImmediate` to "yield"
Yields event loop but buffer still grows; backpressure ignored.

---

## 7. The unlocking insight

> **`write()` returns false → producer stops. `.once('drain')` to resume. Same producer-consumer with bounded queue. `pipe()` and `pipeline()` handle this automatically — manual loops don't.**

Three properties:

1. **Advisory return value** — chunk queued, just signal.
2. **`.once('drain')`** to resume.
3. **`pipe()` / `pipeline()`** handle automatically.

---

## 8. Solution (annotated)

```js
const fs = require('fs');

function streamLines(dest, count) {
  return new Promise((resolve, reject) => {
    let i = 0;
    dest.on('error', reject);
    dest.on('finish', resolve);

    function write() {
      let canContinue = true;
      while (i < count && canContinue) {                                  // step 1: tight loop
        const chunk = `line ${i}\n`;
        i++;
        if (i === count) {
          dest.end(chunk);                                                // step 2: last chunk via end
        } else {
          canContinue = dest.write(chunk);                                 // step 3: check return
        }
      }
      if (i < count) {
        dest.once('drain', write);                                         // step 4: resume on drain
      }
    }
    write();
  });
}

// Usage
const out = fs.createWriteStream('big.txt', { highWaterMark: 16 * 1024 });
streamLines(out, 1_000_000).then(() => console.log('done'));
```

**Try it yourself**

```js
// Pipe handles backpressure automatically
const src = fs.createReadStream('big-source.txt');
const dst = fs.createWriteStream('out.txt');
src.pipe(dst);                                                            // auto backpressure

// pipeline() — modern, error-handling included
const { pipeline } = require('node:stream/promises');
await pipeline(src, dst);

// Async iterable as source
const { Readable } = require('node:stream');
await pipeline(
  Readable.from(asyncGenerator()),                                        // async iter → Readable
  transformStream,
  dst,
);

// Monitor buffer
console.log('current:', writable.writableLength,
            'limit:', writable.writableHighWaterMark);
```

---

## 9. Step-by-step dry run

```
streamLines(out, 1e6) with highWaterMark 16KB:

Iter 0..1638:
  write(chunk) returns true. Loop tight-iterates.
  ~16 KB buffered.

Iter 1639:
  write(chunk) returns FALSE (buffer at HWM).
  canContinue = false. Loop exits.

i < count (still 998361 to write):
  once('drain', write) attached. Function returns. Event loop free.

libuv flushes buffer to disk over ~ms.
Buffer drops below HWM → emits 'drain'.

write() re-enters at iter 1639:
  while loop tight-iterates again. Until next 'false'.

Cycle ~600 times until i === count.
Last chunk via end() — fires 'finish' after flush.
Promise resolves.

Net: memory bounded at ~16 KB instead of buffering all 10 MB.
Throughput identical (disk-bound either way).

Failure case (no backpressure):
  for (let i = 0; i < 1e6; i++) out.write(`line ${i}\n`);
  Buffer grows: 1MB, 10MB, 100MB...
  Process OOM-killed eventually.
```

---

## 10. Common confusion + traps

1. **`write() === false` means chunk dropped** — no; queued.
2. **`.on('drain')` not `.once`** — listener leak.
3. **`setImmediate` between writes** — yields loop but doesn't check buffer.
4. **`highWaterMark` is a hard cap** — advisory threshold only.
5. **Object mode HWM = bytes** — no, entry count.
6. **`end(chunk)` after `write(chunk)`** — fine; chunk before close.
7. **`pipe()` doesn't handle errors** — yes-ish; `pipeline()` is better.

---

## 11. Senior follow-ups & variants

### Variant 1 — Async iterator producer
`pipeline(asyncGenerator, writable)` honors backpressure.

### Variant 2 — TCP socket dest
Same code; network is slow consumer; backpressure end-to-end.

### Variant 3 — Measure buffer
`writable.writableLength`, `writable.writableHighWaterMark`.

### Variant 4 — `cork()`/`uncork()` batching
Different mechanism — explicit batching, not backpressure.

### Variant 5 — `pipeline()` error handling
Modern alternative; propagates errors from any stage.

---

## 12. How to think aloud

> "Every Writable has an internal buffer. `write(chunk)` always queues the chunk; the BOOLEAN return is purely advisory — `true` if buffer below `highWaterMark`, `false` if at or above. Ignoring `false` doesn't break correctness (chunks still queue) but breaks MEMORY: buffer grows unbounded → OOM in prod. Correct pattern: `while (i < n && canContinue) { canContinue = writable.write(chunk); }` then `writable.once('drain', resumeFn)`. Use `.once` not `.on` — otherwise listener leak. `Readable.pipe(Writable)` and `pipeline()` handle this automatically. Object-mode `highWaterMark` is entry count, not bytes — be careful with large objects. TCP sockets and HTTP responses are Writables; same backpressure semantics. Trap: ignoring false return; `.on` instead of `.once`; thinking HWM is a hard cap; assuming object-mode HWM is bytes."

---

## 13. 60-second revision

> - **`write()` returns `false`** when buffer ≥ `highWaterMark`.
> - **Advisory** — chunk still queued.
> - **Ignoring** → unbounded memory → OOM.
> - **Pattern:** loop until false; `.once('drain', resume)`.
> - **`.once` not `.on`** — listener leak.
> - **`pipe()` / `pipeline()`** handle automatically.
> - **Object mode HWM = entries**, not bytes.
> - **`writable.writableLength`** for introspection.
> - **Trap:** ignore false; .on; HWM as hard cap.

---

**Related:** [readable-stream-push.md](./readable-stream-push.md) · [writable-stream-implementation.md](./writable-stream-implementation.md) · [stream-pipeline-error-handling.md](./stream-pipeline-error-handling.md) · [file-line-reader-with-backpressure.md](./file-line-reader-with-backpressure.md) · [throttled-stream.md](./throttled-stream.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
