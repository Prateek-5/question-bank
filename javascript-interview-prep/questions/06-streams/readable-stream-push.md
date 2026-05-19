# Readable stream — `push(chunk)` / `push(null)`

> **Difficulty:** Medium-Senior   |   **Time:** ~15 min   |   **Prereqs:** [`concepts/streams.md`](../../concepts/streams.md), [backpressure-demo.md](./backpressure-demo.md)
>
> **Source:** Node `stream.Readable`. codedamn lab.

---

## 1. Problem statement

Build a custom `Readable` by subclassing. Implement `_read(size)` to push chunks; `push(null)` for EOF.

**Verification examples**

```js
const { Readable } = require('node:stream');

class RangeStream extends Readable {
  constructor(start, end) {
    super({ objectMode: true, highWaterMark: 4 });
    this.cursor = start;
    this.end = end;
  }
  _read() {
    while (this.cursor <= this.end) {
      if (!this.push(this.cursor++)) return;                              // respect backpressure
    }
    this.push(null);                                                       // EOF
  }
}

for await (const n of new RangeStream(1, 5)) console.log(n);              // 1, 2, 3, 4, 5
```

**Constraints**
- Subclass `Readable`; implement `_read(size)`.
- `push(chunk)` enqueues; returns `false` → stop pushing (backpressure).
- `push(null)` exactly once for EOF.
- `destroy(err)` for error propagation.
- Modern shortcut: `Readable.from(iterable)`.

---

## 2. Plain-English restatement

A Readable is pull-based — Node calls `_read(size)` when buffer is low. You call `this.push(chunk)` until the buffer fills (`push` returns `false`). Call `this.push(null)` once when source is exhausted.

---

## 3. Why this matters in interviews

Tests producer-side stream knowledge. Real backend: wrap DB cursor, paginated API, message queue as a stream.

---

## 4. Mental model

```
   class extends Readable:
     constructor() {
       super({ objectMode, highWaterMark });
       // internal state (cursor, source, etc.)
     }
     _read(size) {
       // Called by Node when internal buffer < highWaterMark.
       // Push chunks until buffer full OR source exhausted.
       while (haveMore && this.push(nextChunk));
       if (sourceExhausted) this.push(null);
     }
   }

   push(chunk):
     - Adds chunk to internal buffer.
     - Returns false when buffer ≥ highWaterMark (consumer's buffer full).
     - STOP pushing on false; Node will call _read again later.

   push(null):
     - EOF. Exactly once. Subsequent reads receive done.

   destroy(err):
     - Propagate error to consumer; emit 'error'; tear down.

   Modes:
     - Paused (default): consumer calls .read() or for await.
     - Flowing: 'data' listener attached or .resume() called.
     - objectMode: any JS value; highWaterMark = entry count.

   Shortcut: Readable.from(iterable | asyncIterable)
     - Auto-implements; no _read override needed.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `push(null)` do?
> 2. What happens if `push()` returns `false` but you keep pushing?
> 3. When would you NOT use `Readable.from()`?

---

## 6. Brute force — walked through

### Wrong attempt 1: emit 'data' manually via EventEmitter
Doesn't honor backpressure; doesn't integrate with pipe/pipeline.

### Wrong attempt 2: forget `push(null)`
Consumer hangs forever waiting for EOF.

### Wrong attempt 3: ignore push return value
Memory bloat — buffer overflows highWaterMark.

---

## 7. The unlocking insight

> **Subclass Readable; override `_read(size)`. Loop pushing chunks; stop on `push() === false`. `push(null)` once for EOF. `destroy(err)` for errors. Modern shortcut: `Readable.from(asyncGen)`.**

Three properties:

1. **`_read` is the pull hook** — Node calls when ready.
2. **`push` returns false** → stop pushing (backpressure).
3. **`push(null)`** = EOF, exactly once.

---

## 8. Solution (annotated)

```js
const { Readable } = require('node:stream');

class RangeStream extends Readable {
  constructor(start, end, opts = {}) {
    super({ objectMode: true, highWaterMark: 4, ...opts });
    this.cursor = start;
    this.end = end;
  }

  _read(/* size */) {
    while (this.cursor <= this.end) {                                    // step 1: push loop
      const v = this.cursor++;
      if (!this.push(v)) return;                                         // step 2: backpressure
    }
    this.push(null);                                                     // step 3: EOF
  }
}

// Async source wrapped as Readable
class PagedApiStream extends Readable {
  constructor(fetchPage, opts = {}) {
    super({ objectMode: true, ...opts });
    this.fetchPage = fetchPage;
    this.nextCursor = null;
    this.busy = false;
  }

  async _read() {
    if (this.busy) return;                                                // step 4: reentrancy guard
    this.busy = true;
    try {
      const { items, nextCursor } = await this.fetchPage(this.nextCursor);
      for (const item of items) {
        if (!this.push(item)) break;
      }
      this.nextCursor = nextCursor;
      if (!nextCursor) this.push(null);
    } catch (err) {
      this.destroy(err);                                                  // step 5: error propagation
    } finally {
      this.busy = false;
    }
  }
}

// Consume
(async () => {
  const rs = new RangeStream(1, 5);
  for await (const n of rs) console.log(n);                               // 1, 2, 3, 4, 5
})();
```

**Try it yourself**

```js
// Modern shortcut: Readable.from
const { Readable } = require('node:stream');
const stream = Readable.from(async function* () {
  for (let i = 1; i <= 5; i++) yield i;
}());

for await (const x of stream) console.log(x);                             // 1..5
// No _read override needed.

// Error propagation
class FlakyStream extends Readable {
  constructor() { super({ objectMode: true }); this.count = 0; }
  _read() {
    if (this.count > 3) return this.destroy(new Error('boom'));
    this.push(this.count++);
  }
}
try {
  for await (const x of new FlakyStream()) console.log(x);
} catch (err) {
  console.log('error:', err.message);                                     // 'error: boom'
}
```

---

## 9. Step-by-step dry run

```
new RangeStream(1, 10), highWaterMark 4, consumed by for await:

Iteration start → Node calls _read():
  cursor=1: push(1) → true. cursor=2.
  push(2) → true. cursor=3.
  push(3) → true. cursor=4.
  push(4) → false (buffer at HWM 4). Return.
  state: cursor=5, buffer=[1,2,3,4].

Consumer awaits → drains 1 → buffer=[2,3,4].
Buffer drops below HWM → Node calls _read() again.
  push(5) → true. cursor=6.
  push(6) → true. cursor=7.
  push(7) → true. cursor=8.
  push(8) → false. Return.
  state: cursor=9.

Consumer drains. _read called.
  push(9), push(10), then push(null) (EOF).
  state: cursor=11.

Consumer drains. for await sees done. Stream emits 'end', auto-destroys.

Without push(null): consumer hangs forever.
Without checking push return: memory blows up past HWM.
```

---

## 10. Common confusion + traps

1. **Forget `push(null)`** — consumer hangs.
2. **`push(null)` twice** — throws.
3. **Ignore `push()` return** — memory bloat.
4. **Re-entrant `_read`** with async work → duplicate work; use busy flag.
5. **Throw in `_read`** instead of `destroy(err)` — uncaught.
6. **`objectMode: true` for bytes** — defeats optimization.
7. **`Readable.from` everywhere** — fine, but loses control over `'pause'`/`'resume'` events if needed.

---

## 11. Senior follow-ups & variants

### Variant 1 — `Readable.from(asyncGenerator())`
One-liner; same behavior.

### Variant 2 — Rate-limited Readable
`setTimeout` in `_read`; carefully don't block.

### Variant 3 — Resumable Readable
Accept `startCursor`; reconnect after crash.

### Variant 4 — Object mode vs byte
Choose based on consumer needs.

### Variant 5 — Multiple Readables piped/merged
`merge`/`zip` Readables for stream composition.

---

## 12. How to think aloud

> "Subclass Readable; override `_read(size)`. Node calls `_read` when its internal buffer drops below `highWaterMark`. Push chunks via `this.push(chunk)`; `push` returns `false` when consumer's buffer is full — STOP pushing and return; Node calls `_read` again later. `push(null)` exactly once signals EOF. `destroy(err)` for errors. For async sources, guard against re-entrant `_read` with a `busy` flag (Node may call `_read` again before your previous fetch resolves). Modern shortcut: `Readable.from(iterable | asyncIterable)` handles everything — no `_read` override needed. Use the manual form when you need finer control (preflight handshake, custom backpressure logic, reacting to `'pause'`/`'resume'` events). Trap: forgetting push(null) (consumer hangs); ignoring push() return (memory bloat); throwing instead of destroy(); objectMode for byte data."

---

## 13. 60-second revision

> - **Subclass `Readable`; override `_read(size)`.**
> - **`this.push(chunk)`** enqueues; returns false → STOP.
> - **`this.push(null)`** = EOF; exactly once.
> - **`this.destroy(err)`** propagates error.
> - **Async `_read`** needs reentrancy guard (`busy` flag).
> - **Modern shortcut:** `Readable.from(iterable | asyncIterable)`.
> - **Object mode:** any JS value; HWM = entry count.
> - **Trap:** forget push(null) hangs consumer; ignore push return → bloat; re-entrant fetch.

---

**Related:** [writable-stream-implementation.md](./writable-stream-implementation.md) · [backpressure-demo.md](./backpressure-demo.md) · [async-iterator-pagination.md](./async-iterator-pagination.md) · [stream-pipeline-lab.md](./stream-pipeline-lab.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
