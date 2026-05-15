# Build a Readable stream with `push(chunk)` / `push(null)`

## Source
- codedamn "Stream Readable Push Lab": https://codedamn.com/problem/hCvvVJhuO-Y_a1SxA6P2y
- Canonical Node.js docs: `stream.Readable`, "Implementing a Readable stream."

## Why this question matters in interviews
Most candidates can *consume* a stream but freeze when asked to *produce* one. Building a Readable is the cleanest test of whether you understand the engine: chunks live in an internal buffer; `_read(size)` is called by Node when that buffer drops below `highWaterMark`; `push(chunk)` enqueues; `push(null)` signals EOF. Backend engineers hit this when wrapping a non-stream source (paginated API, DB cursor, message queue) as a stream so it can plug into existing pipelines. It's also a perfect stepping stone to async iterators.

## Concepts involved

### The pull model
A Readable is **pull-based** in paused mode, **push-based** in flowing mode. Either way:
- Node calls `_read(size)` when it wants more data.
- You call `this.push(chunk)` zero or more times to add data.
- You call `this.push(null)` exactly once when there is no more data ever.
- If `push()` returns `false`, stop pushing — the consumer is full. Node will call `_read` again when it's ready.

### Modes
- **Paused (default):** consumer must call `.read()` or attach `for await ... of`.
- **Flowing:** triggered by attaching a `.on('data')` listener or by `.resume()`. Data is pushed at the consumer; you can't slow it down except via backpressure.
- **objectMode:** `push` accepts any JS value (not just Buffer/string). `highWaterMark` counts *objects*, not bytes.

### `Readable.from(iterable)` — the shortcut
For most "wrap an iterable as a stream" cases you don't write `_read` at all:
```js
const { Readable } = require('node:stream');
Readable.from(asyncGenerator());     // turns any (async)iterable into a Readable
```
But interviewers want you to demonstrate the lower-level skill first.

### Encoding gotcha
By default chunks are Buffers. `stream.setEncoding('utf8')` switches to strings. In `objectMode` neither applies.

## Brute force approach
"I'll just emit `'data'` events myself with `new EventEmitter`." That builds a fake stream that doesn't honor backpressure, doesn't integrate with `pipe`/`pipeline`, doesn't support `for await ... of`, and ignores `highWaterMark`. Reject this — the whole point is to compose with the stream ecosystem.

## Optimal approach
Subclass `Readable` (or pass `read` in the options bag). Maintain internal state (a counter, an iterator, a connection cursor). In `_read`, produce one or more chunks via `this.push`, and stop when `push` returns `false`. When the source is exhausted, call `this.push(null)`.

## Solution (JavaScript)

```js
'use strict';
const { Readable } = require('node:stream');

/**
 * A Readable that emits integers from `start` to `end` (inclusive).
 * Demonstrates: _read, push(chunk), push(null), backpressure, objectMode.
 */
class RangeStream extends Readable {
  constructor(start, end, opts = {}) {
    super({ objectMode: true, highWaterMark: 4, ...opts });
    this.cursor = start;
    this.end = end;
  }

  _read(/* size */) {
    // Produce in a loop, but BAIL OUT when push returns false (backpressure).
    while (this.cursor <= this.end) {
      const value = this.cursor++;
      const canContinue = this.push(value);
      if (!canContinue) return;        // consumer's buffer is full → stop
    }
    this.push(null);                   // EOF — call exactly once
  }
}

// Async source variant — wrap a paginated API as a Readable.
class PagedApiStream extends Readable {
  constructor(fetchPage, opts = {}) {
    super({ objectMode: true, ...opts });
    this.fetchPage = fetchPage;        // async (cursor) => { items, nextCursor }
    this.nextCursor = null;
    this.busy = false;
  }

  async _read() {
    if (this.busy) return;             // _read can be called re-entrantly
    this.busy = true;
    try {
      const { items, nextCursor } = await this.fetchPage(this.nextCursor);
      for (const item of items) {
        if (!this.push(item)) break;   // honor backpressure
      }
      this.nextCursor = nextCursor;
      if (!nextCursor) this.push(null); // last page → EOF
    } catch (err) {
      this.destroy(err);               // propagate to consumer
    } finally {
      this.busy = false;
    }
  }
}

// Consume with the modern async-iterator idiom.
(async () => {
  const rs = new RangeStream(1, 5);
  for await (const n of rs) console.log(n);  // 1, 2, 3, 4, 5
})();
```

## Step-by-step dry run

`new RangeStream(1, 10)` with `highWaterMark: 4` consumed by `for await ... of`.

| Step | Event | State |
| --- | --- | --- |
| 1 | Iterator starts, Node calls `_read()` | cursor=1, buffer=[] |
| 2 | Loop: push(1) → true. push(2) → true. push(3) → true. push(4) → false | cursor=5, buffer=[1,2,3,4]. We `return`. |
| 3 | Consumer awaits 1 → buffer drops to 3 items | Node calls `_read()` again. |
| 4 | Loop: push(5) → true... push(8) → false | cursor=9, buffer fills. |
| 5 | Consumer drains | `_read` called. |
| 6 | push(9), push(10), then `push(null)` | EOF signaled. |
| 7 | `for await` loop exits | Stream emits `'end'`, auto-destroys. |

**Why `if (!canContinue) return;` matters:** without it, in flowing mode the stream pushes the entire range into memory before the consumer reads anything — exactly the OOM streams are meant to prevent.

**Without `push(null)`:** the consumer hangs forever waiting for EOF. Common bug.

## Important takeaways

**Syntax to memorize**
- `super({ objectMode, highWaterMark })` in the constructor — set these once.
- `_read(size)` — Node-internal; `size` is the *hint* of how many bytes/objects it wants. You may push more or less.
- `this.push(chunk)` returns `false` → STOP pushing.
- `this.push(null)` → EOF, exactly once.
- `this.destroy(err)` → propagate an error and tear down.

**Patterns to reuse**
- Wrapping a DB cursor (`pg`'s `Cursor`, `mongodb`'s `cursor.next()`) as a Readable — same shape as `PagedApiStream`.
- Wrapping `kafka`/`sqs` consumers as object-mode Readables → plug into a `pipeline` with a parse Transform and a DB-write Writable.
- For most cases just use `Readable.from(asyncGenerator())` — but know the manual version for the cases where you need fine control (e.g. preflight handshake).

**Common mistakes**
- Forgetting `push(null)` → consumer hangs.
- Calling `push(null)` more than once → throws.
- Ignoring `push()`'s return value → memory bloat (you're now a brute-force EventEmitter).
- Doing async work inside `_read` without a reentrancy guard → `_read` can be called again before your previous fetch resolved, leading to duplicate work.
- Throwing from `_read` instead of `this.destroy(err)` → uncaught exception.
- Using `objectMode: true` for byte data — defeats internal optimization.

**Related**
- `writable-stream-implementation.md` — the other side of the pipe.
- `async-iterator-pagination.md` — same pagination pattern, without subclassing.
- `stream-pipeline-lab.md` — how to plug your Readable into a chain.

## Variants

1. **Async generator → Readable (one-liner)** — show `Readable.from(async function*() { yield 1; yield 2; }())`. Same behavior with one line of code. Interviewer might ask: "When would you NOT use `Readable.from`?" Answer: when you need to react to internal events (`'pause'`, `'resume'`) or pre-buffer state before yielding.

2. **Rate-limited Readable** — emit at most N items per second. Use `setTimeout` inside `_read`, but be careful to not block — push what you have, then schedule the next batch.

3. **Resumable Readable** — accept a `startCursor` so consumers can restart after a crash. Common pattern for log-tailing or event-replay streams.

## Revision notes

> **Readable from scratch — 60 second recap**
> - Subclass `Readable`, set `{ objectMode, highWaterMark }` in `super()`.
> - Override `_read(size)`; Node calls it when buffer dips below HWM.
> - `this.push(chunk)` enqueues; returns `false` → STOP pushing.
> - `this.push(null)` exactly once = EOF. Forgetting it = consumer hangs forever.
> - `this.destroy(err)` to propagate failure.
> - Modern shortcut: `Readable.from(iterable | asyncIterable)`.
> - Consume with `for await (const x of stream)` — handles end + error implicitly.
> - Trap: re-entrant `_read` calls during async fetch → use a `busy` flag.
> - Trap: ignoring push's return value → loses backpressure.
