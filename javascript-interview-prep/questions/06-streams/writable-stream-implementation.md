# Writable stream — `_write(chunk, enc, cb)` + backpressure

> **Difficulty:** Senior   |   **Time:** ~15 min   |   **Prereqs:** [`concepts/streams.md`](../../concepts/streams.md), [backpressure-demo.md](./backpressure-demo.md)
>
> **Source:** Node `stream.Writable`. Every backend stream sink (DB inserter, S3 uploader, log forwarder) is a Writable.

---

## 1. Problem statement

Subclass `Writable` and implement `_write(chunk, encoding, callback)`. Optional: `_writev` for batch, `_final` for graceful shutdown, `_destroy` for cleanup.

**Verification examples**

```js
const { Writable } = require('node:stream');

class DbBatchWriter extends Writable {
  constructor(opts = {}) {
    super({ objectMode: true, highWaterMark: 100, ...opts });
  }
  async _write(record, enc, cb) {
    try {
      await db.insert(record);
      cb();                                                              // EXACTLY once
    } catch (err) {
      cb(err);                                                            // propagate
    }
  }
  _writev(chunks, cb) {                                                  // batch
    const records = chunks.map((c) => c.chunk);
    db.bulkInsert(records).then(() => cb()).catch(cb);
  }
  _final(cb) {                                                            // graceful close
    db.commit().then(() => cb()).catch(cb);
  }
}
```

**Constraints**
- `callback` MUST be called exactly once.
- Not calling → stream hangs forever.
- Calling twice → `ERR_MULTIPLE_CALLBACK`.
- `_writev` for batched writes (DB INSERT VALUES).
- `_final` for graceful shutdown.

---

## 2. Plain-English restatement

A Writable consumes chunks. Override `_write(chunk, encoding, callback)`; do your async work; call `callback()` exactly once on success or `callback(err)` on failure. The speed of `callback` controls how fast the producer writes — natural backpressure.

---

## 3. Why this matters in interviews

Most stream time on backend is on the Writable side. Interview probe: "Implement `_write` for a DB sink." Pass = `cb()` once + backpressure + `_final`.

---

## 4. Mental model

```
   class extends Writable:
     super({ objectMode, highWaterMark });
     
     _write(chunk, encoding, callback):
       // Do async work. Call callback exactly ONCE.
       doAsync()
         .then(() => callback())          ← success
         .catch(err => callback(err));    ← failure
     
     _writev(chunks, callback):           ← batch optimization
       // Receive array of chunks queued while previous _write was busy.
       // Useful for DB: INSERT INTO t VALUES (), (), () instead of N round trips.
     
     _final(callback):                    ← graceful shutdown (.end())
       // Flush buffers, commit transactions, close connections.
     
     _destroy(err, callback):              ← failure shutdown
       // Release resources unconditionally.

   Backpressure:
     - Producer calls writable.write(chunk).
     - Internal buffer grows.
     - If buffer ≥ highWaterMark, write() returns false.
     - Producer should pause until 'drain'.
     - SPEED of callback controls producer rate.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What happens if you forget to call `callback`?
> 2. What does `_writev` give you over `_write`?
> 3. Where do you commit a transaction — `_write`, `_writev`, or `_final`?

---

## 6. Brute force — walked through

### Wrong attempt 1: synchronous push to array
Ignores backpressure; OOM on large input.

### Wrong attempt 2: forget to call cb
Stream hangs; producer eventually stalls due to backpressure.

### Wrong attempt 3: call cb twice
`ERR_MULTIPLE_CALLBACK` thrown.

---

## 7. The unlocking insight

> **`_write` must call callback exactly once. Speed of callback = backpressure. `_writev` for batch; `_final` for graceful close; `_destroy` for cleanup.**

Three properties:

1. **Exactly-one callback** — never zero, never twice.
2. **`_writev` batches** for DB sinks.
3. **`_final` for graceful flush**.

---

## 8. Solution (annotated)

```js
const { Writable } = require('node:stream');

class DbBatchWriter extends Writable {
  constructor({ batchSize = 100, ...opts } = {}) {
    super({ objectMode: true, highWaterMark: batchSize, ...opts });
    this.batchSize = batchSize;
  }

  async _write(record, enc, cb) {                                       // step 1: single write
    try {
      await db.insert(record);
      cb();                                                              // step 2: success
    } catch (err) {
      cb(err);                                                            // step 3: error
    }
  }

  async _writev(chunks, cb) {                                            // step 4: batch write
    const records = chunks.map((c) => c.chunk);
    try {
      await db.bulkInsert(records);
      cb();
    } catch (err) {
      cb(err);
    }
  }

  async _final(cb) {                                                      // step 5: graceful close
    try {
      await db.commit();
      await db.close();
      cb();
    } catch (err) {
      cb(err);
    }
  }

  _destroy(err, cb) {                                                     // step 6: failure cleanup
    db.rollback().finally(() => cb(err));
  }
}
```

**Try it yourself**

```js
const { pipeline } = require('node:stream/promises');
const { Readable } = require('node:stream');

await pipeline(
  Readable.from(asyncRecordSource()),                                    // producer
  new DbBatchWriter(),                                                    // sink
);
// All errors propagated; all streams destroyed on failure.

// Without _writev: 1000 records → 1000 INSERT statements.
// With _writev: 1000 records batched into ~10 bulk INSERTs.

// Forgetting cb() test
class Hanging extends Writable {
  _write(chunk, enc, cb) {
    // forgot cb()!
  }
}
// Pipeline hangs forever waiting for cb.
```

---

## 9. Step-by-step dry run

```
new DbBatchWriter() with batchSize 100:

Producer calls writable.write(record1):
  Node appends to internal buffer; calls _write(record1, _, cb).
  _write awaits db.insert (e.g., 5ms).
  cb() fires → Node pulls next chunk.

If producer is fast and calls write() many times before _write completes:
  Node queues chunks in buffer.
  Once buffer ≥ highWaterMark (100), write() returns false.
  Producer should pause.

When previous _write's cb fires:
  If multiple chunks queued, Node CALLS _writev with batch.
  _writev does db.bulkInsert. Faster than N _writes.

Producer calls writable.end():
  Buffer drains via _write/_writev.
  After buffer empty, _final(cb) called.
  _final commits + closes.
  cb() → emit 'finish'.

If _write errors (cb(err)):
  Node destroys writable.
  Emit 'error'.
  _destroy(err, cb) called for cleanup.
  pipeline rejects.

If you forget cb():
  Stream waits forever. Producer eventually stalls (buffer never drains).
  No error emitted. Diagnostically painful.

If you call cb twice:
  ERR_MULTIPLE_CALLBACK thrown. Crashes process unless caught.
```

---

## 10. Common confusion + traps

1. **Forget `cb()`** — hangs forever.
2. **Call `cb` twice** — `ERR_MULTIPLE_CALLBACK`.
3. **Async work without await** — data loss.
4. **Skip `_writev`** — N round trips instead of batch.
5. **Skip `_final`** — no graceful commit/close.
6. **Throw in `_write`** — uncaught.
7. **Use `_destroy` for normal close** — `_final` for graceful, `_destroy` for failure.

---

## 11. Senior follow-ups & variants

### Variant 1 — Object mode for record streams
HWM = entry count; tune to DB batch size.

### Variant 2 — `cork()`/`uncork()` for explicit batching
Different from `_writev`; producer-side batching.

### Variant 3 — TCP socket as Writable
Same `_write` shape; `cb` after `socket.write` completes.

### Variant 4 — Backpressure across TCP
Network is slow consumer; same mechanism end-to-end.

### Variant 5 — Test with `pipeline()`
Modern way to wire producer → sink with error propagation.

---

## 12. How to think aloud

> "Subclass Writable; override `_write(chunk, encoding, callback)`. Do async work; call `callback()` EXACTLY once — success no arg, error `cb(err)`. Not calling → stream hangs forever (most common bug). Calling twice → `ERR_MULTIPLE_CALLBACK`. SPEED of callback controls backpressure naturally. For batch sinks (DB INSERT VALUES (), (), ()), override `_writev(chunks, cb)` — Node delivers all queued chunks as an array. For graceful shutdown (commit transaction, close connection), override `_final(cb)` — runs once on `.end()`. For failure cleanup (rollback on error), override `_destroy(err, cb)`. With `pipeline()`, errors propagate and all streams destroyed automatically. Trap: forget cb; double cb; async work without await; skip _writev (perf); throw in _write (uncaught)."

---

## 13. 60-second revision

> - **Subclass `Writable`; override `_write(chunk, enc, cb)`.**
> - **`cb()` EXACTLY once** — never zero, never twice.
> - **Speed of `cb`** controls producer rate (backpressure).
> - **`_writev(chunks, cb)`** for batch sinks (DB bulk INSERT).
> - **`_final(cb)`** for graceful shutdown.
> - **`_destroy(err, cb)`** for failure cleanup.
> - **Object mode** for record streams; HWM = entry count.
> - **Use `pipeline()`** for error propagation.
> - **Trap:** forget cb (hang); double cb (throw); skip _writev (perf); throw (uncaught).

---

**Related:** [readable-stream-push.md](./readable-stream-push.md) · [backpressure-demo.md](./backpressure-demo.md) · [stream-pipeline-lab.md](./stream-pipeline-lab.md) · [stream-pipeline-error-handling.md](./stream-pipeline-error-handling.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
