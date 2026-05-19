# Transform stream — line-based parser

> **Difficulty:** Medium-Senior   |   **Time:** ~15 min   |   **Prereqs:** [readable-stream-push.md](./readable-stream-push.md), [writable-stream-implementation.md](./writable-stream-implementation.md)
>
> **Source:** Datadog, Splunk, observability vendors. Every NDJSON / log / CSV ingest path.

---

## 1. Problem statement

Build a Transform stream that splits bytes into lines, handling chunk boundaries correctly.

**Verification examples**

```js
const { Transform } = require('node:stream');

class LineParser extends Transform {
  constructor(opts = {}) {
    super({ ...opts, readableObjectMode: true });
    this._buffer = '';
  }
  _transform(chunk, enc, cb) {
    this._buffer += chunk.toString('utf8');
    const lines = this._buffer.split('\n');
    this._buffer = lines.pop();                                          // partial last
    for (const line of lines) this.push(line);
    cb();
  }
  _flush(cb) {                                                            // emit final partial
    if (this._buffer.length) this.push(this._buffer);
    this._buffer = '';
    cb();
  }
}
```

**Constraints**
- Lines split across chunks must reassemble.
- Buffer the trailing partial line.
- `_flush` emits final line (if no trailing `\n`).
- Handle `\r\n` (CRLF) for Windows logs.

---

## 2. Plain-English restatement

Chunks arrive at arbitrary sizes — one logical line might span multiple chunks. Buffer the trailing partial line; emit complete lines via `push`. On `_flush` (upstream `end`), emit whatever's left.

---

## 3. Why this matters in interviews

Stream Transform "hello world". Every framing problem (NDJSON, CSV, protocol) is conceptually this.

---

## 4. Mental model

```
   Chunks arrive:
   chunk1: "first\nsecond\nth"
   chunk2: "ird\nfourth"
   chunk3: "\nlast (no newline)"
   
   State machine:
   buffer = ''
   
   chunk1: buffer = 'first\nsecond\nth'
           split('\n') = ['first', 'second', 'th']
           pop → buffer = 'th'
           push('first'), push('second')
   
   chunk2: buffer = 'thi'+'rd\nfourth' = 'third\nfourth'
           split('\n') = ['third', 'fourth']
           pop → buffer = 'fourth'
           push('third')
   
   chunk3: buffer = 'fourth'+'\nlast (no newline)' = 'fourth\nlast (no newline)'
           split('\n') = ['fourth', 'last (no newline)']
           pop → buffer = 'last (no newline)'
           push('fourth')
   
   _flush:
     buffer = 'last (no newline)'
     push('last (no newline)')
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why does the trailing line need `_flush`?
> 2. What happens with `\r\n` Windows line endings?
> 3. What if a UTF-8 multi-byte character spans a chunk boundary?

---

## 6. Brute force — walked through

### Wrong attempt 1: per-chunk `split('\n')` without buffer
Drops lines split across chunks.

### Wrong attempt 2: no `_flush`
Last line (without trailing `\n`) silently dropped.

### Wrong attempt 3: `chunk.toString('utf8')` on partial UTF-8
Multi-byte split → replacement char. Use `StringDecoder`.

---

## 7. The unlocking insight

> **Buffer partial lines across chunks. Split on `\n`; emit all but last; keep last as buffer. `_flush` emits final partial. Use `StringDecoder` for UTF-8 safety.**

Three properties:

1. **Buffer the partial** — chunks don't align with lines.
2. **`_flush` for trailing line** — no final newline case.
3. **`StringDecoder` for UTF-8 safety** — multi-byte boundaries.

---

## 8. Solution (annotated)

```js
const { Transform } = require('node:stream');
const { StringDecoder } = require('node:string_decoder');

class LineParser extends Transform {
  constructor(opts = {}) {
    super({ ...opts, readableObjectMode: true });
    this._decoder = new StringDecoder('utf8');                          // step 1: UTF-8 safe
    this._buffer = '';
  }

  _transform(chunk, encoding, cb) {
    this._buffer += this._decoder.write(chunk);                          // step 2: handle partial UTF-8
    const lines = this._buffer.split(/\r?\n/);                           // step 3: handle CRLF
    this._buffer = lines.pop();                                          // partial last
    for (const line of lines) this.push(line);                           // step 4: emit complete
    cb();
  }

  _flush(cb) {
    this._buffer += this._decoder.end();                                 // step 5: flush decoder
    if (this._buffer.length) this.push(this._buffer);
    this._buffer = '';
    cb();
  }
}

// Usage with pipeline
const fs = require('node:fs');
const { pipeline } = require('node:stream/promises');

await pipeline(
  fs.createReadStream('input.log'),
  new LineParser(),                                                     // bytes → lines
  async function* (lines) {                                              // process lines
    for await (const line of lines) {
      yield JSON.parse(line);
    }
  },
  writableSink,
);
```

**Try it yourself**

```js
// Test with split chunks
const parser = new LineParser();
parser.write('first\nsec');                                              // partial 'sec'
parser.write('ond\nthird');                                              // 'second' complete; 'third' partial
parser.end('\nfourth');                                                  // 'third', 'fourth' (via _flush)

parser.on('data', (line) => console.log(line));
// Output:
// first
// second
// third
// fourth

// Alternative: built-in readline
const { createInterface } = require('node:readline');
const rl = createInterface({ input: fs.createReadStream('log'), crlfDelay: Infinity });
for await (const line of rl) console.log(line);
```

---

## 9. Step-by-step dry run

```
Input: "first\nsecond\nth" / "ird\nfourth" / "\nlast"

LineParser state:

_transform("first\nsecond\nth", _, cb):
  buffer = 'first\nsecond\nth'
  split('\n') = ['first', 'second', 'th']
  pop → buffer = 'th'
  push('first'), push('second')
  cb()

_transform("ird\nfourth", _, cb):
  buffer = 'th' + 'ird\nfourth' = 'third\nfourth'
  split('\n') = ['third', 'fourth']
  pop → buffer = 'fourth'
  push('third')
  cb()

_transform("\nlast", _, cb):
  buffer = 'fourth' + '\nlast' = 'fourth\nlast'
  split('\n') = ['fourth', 'last']
  pop → buffer = 'last'
  push('fourth')
  cb()

upstream.end() → triggers _flush(cb):
  buffer = 'last'
  push('last')
  cb()

Consumer receives: 'first', 'second', 'third', 'fourth', 'last'.
```

---

## 10. Common confusion + traps

1. **No buffer** — drops cross-chunk lines.
2. **No `_flush`** — drops final line if no trailing `\n`.
3. **UTF-8 multi-byte split** — replacement char; use StringDecoder.
4. **CRLF (Windows)** — split on `/\r?\n/` not just `\n`.
5. **`push` return value** — usually fine for line parser; back-pressure handled naturally.
6. **Throw in `_transform`** — uncaught; call `cb(err)`.
7. **Forget `readableObjectMode`** — each push emits as one chunk vs bytes.

---

## 11. Senior follow-ups & variants

### Variant 1 — `readline.createInterface`
Built-in; same behavior.

### Variant 2 — NDJSON parser
Same shape; `JSON.parse(line)` in transform.

### Variant 3 — Protocol framer
Length-prefixed bytes (e.g., 4 bytes length + payload).

### Variant 4 — Backpressure across Transform
Backpressure flows downstream → upstream automatically.

### Variant 5 — `StringDecoder`
Buffers partial UTF-8 sequences across chunks.

---

## 12. How to think aloud

> "Transform = Readable + Writable wired together. Override `_transform(chunk, encoding, callback)` (called once per upstream `write`) and `_flush(callback)` (called once on upstream `end`). Chunks arrive at arbitrary sizes — a logical line might span multiple chunks. Buffer the trailing partial line, split complete lines, push them. `_flush` emits whatever's still in the buffer (handles the 'file ends without trailing newline' case — classic bug). For UTF-8 safety, use `StringDecoder` to buffer partial multi-byte sequences across chunks (raw `toString('utf8')` on a chunk ending mid-codepoint produces replacement char). Handle CRLF with `/\r?\n/`. `readableObjectMode: true` so each `push(line)` emits one chunk vs bytes. Built-in alternative: `readline.createInterface({ input, crlfDelay: Infinity })`. Backpressure flows downstream → upstream automatically. Trap: no buffer (drops cross-chunk lines); no _flush (drops trailing line); UTF-8 split (replacement char); ignore CRLF."

---

## 13. 60-second revision

> - **Subclass `Transform`; override `_transform` + `_flush`.**
> - **Buffer partial line** across chunks.
> - **`_flush` emits final** partial (no trailing newline case).
> - **`StringDecoder`** for UTF-8 multi-byte safety.
> - **`/\r?\n/`** for CRLF (Windows).
> - **`readableObjectMode: true`** for line-per-chunk emit.
> - **Built-in alt:** `readline.createInterface`.
> - **Trap:** no buffer; no _flush; UTF-8 split; ignore CRLF.

---

**Related:** [readable-stream-push.md](./readable-stream-push.md) · [writable-stream-implementation.md](./writable-stream-implementation.md) · [ndjson-splitter.md](./ndjson-splitter.md) · [csv-parser-via-transform.md](./csv-parser-via-transform.md) · [file-line-reader-with-backpressure.md](./file-line-reader-with-backpressure.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
