# Transform stream — line-based parser

## Source
- Node.js docs: https://nodejs.org/api/stream.html#class-streamtransform
- Canonical machine-coding problem from Node.js interviews at log-pipeline-heavy shops (Datadog, Splunk, observability vendors, any company that ingests NDJSON/CSV).
- Built-in equivalent: `readline.createInterface({ input })` — but the *interview wants you to build it*.

## Why this question matters in interviews
Line-based parsing is the "hello world" of stream Transforms. Every NDJSON ingest path, every log tail, every CSV importer, every protocol framer is conceptually this question. It tests whether you understand the **chunk-boundary problem**: Node delivers bytes in whatever sizes libuv decides — a single logical "line" can arrive split across 3 chunks, or 5 lines can arrive in one chunk. Candidates who don't get this write code that drops or splits lines randomly under load. Beyond correctness, the question probes `_transform` vs `_flush`, push-vs-callback, and back-pressure propagation through a Transform.

## Concepts involved

### Syntax to lock in
```js
const { Transform } = require('stream');

class LineParser extends Transform {
  constructor(options = {}) {
    super({ ...options, readableObjectMode: true });
    this._buffer = '';
  }

  _transform(chunk, encoding, callback) {
    this._buffer += chunk.toString('utf8');
    const lines = this._buffer.split('\n');
    this._buffer = lines.pop();      // last (possibly partial) line stays in buffer
    for (const line of lines) this.push(line);
    callback();
  }

  _flush(callback) {
    if (this._buffer.length) this.push(this._buffer);
    this._buffer = '';
    callback();
  }
}
```

### Runtime / engine behavior
- A Transform is both a Readable and a Writable wired together. Bytes go in via `_transform`, parsed records come out via `push()`.
- `_transform(chunk, encoding, callback)` is called **once per upstream `write`**. Don't loop over chunks — Node does that for you.
- `callback(err?, data?)` signals "I'm done with this chunk." If you call `callback` with a value, that value is also `push`ed (sugar). Most people just `push(...)` then `callback()`.
- `_flush(callback)` is called **once** when the upstream signals `end()`. This is your last chance to emit anything still in the buffer. Without `_flush`, the trailing line (no final `\n`) is silently dropped — a classic bug.
- `readableObjectMode: true` means "downstream consumers receive whole objects, not bytes," so each `push(line)` is delivered as one chunk to `data` listeners.
- Backpressure: if `push()` returns `false`, downstream is full. You're allowed to keep pushing (Node buffers), but for very fast producers you should respect it. In a line parser this rarely matters — the next `_transform` won't be called until the consumer drains.

### Edge cases (interview traps)
1. **Multi-byte UTF-8 split across chunks.** `chunk.toString('utf8')` on a chunk that ends mid-codepoint produces a replacement char. Fix: use `new StringDecoder('utf8').write(chunk)` which buffers partial sequences. Mention this for senior bonus.
2. **`\r\n` line endings.** Windows logs use CRLF. Split on `\n` then `.replace(/\r$/, '')`, or split on `/\r?\n/`. Forgetting this fails CI on Windows machines.
3. **No trailing newline.** A file ending mid-line without `\n` would lose the last line if `_flush` doesn't push the buffer. This is the most common bug.
4. **Empty lines.** `"a\n\nb".split('\n')` → `['a', '', 'b']`. Decide whether you emit the empty string or filter it. Either is defensible; just be consistent.
5. **Huge single line.** Adversarial input: a 1 GB chunk with no `\n`. Your `_buffer` grows unbounded. Real-world parsers add a `maxLineLength` and error if exceeded. Mention as production-hardening.
6. **`encoding` parameter.** It's the encoding the upstream `.write(chunk, encoding)` declared. If upstream is in binary mode, `encoding === 'buffer'`. Don't trust it — just call `chunk.toString('utf8')`.
7. **Object mode confusion.** If you set `writableObjectMode: true`, `_transform` receives objects, not buffers. For a line parser you want **only `readableObjectMode`** — input is bytes, output is strings.
8. **Calling callback twice.** Crashes. Make sure every code path calls it exactly once.

## Brute force approach
"I'll just split the whole stream on `\n` once at the end." That requires buffering the entire file in memory — defeats the purpose of streams. Some candidates write `let all = ''; stream.on('data', c => all += c); stream.on('end', () => all.split('\n').forEach(...))`. Works for 1 MB files, OOMs for 10 GB log files. The whole point of a streaming parser is **constant memory**.

## Optimal approach
Maintain a tiny string `_buffer` carrying only the trailing partial line between chunks. On each `_transform`: append chunk, split on `\n`, push every complete line, retain the last segment as the new buffer. On `_flush`: emit any non-empty buffer. Memory is O(longest line), CPU is O(n) over the input.

## Solution (JavaScript)

```js
const { Transform } = require('stream');
const { StringDecoder } = require('string_decoder');

class LineParser extends Transform {
  /**
   * @param {{ maxLineLength?: number, stripCR?: boolean }} [options]
   */
  constructor(options = {}) {
    // bytes in, strings out
    super({ readableObjectMode: true });
    this._decoder = new StringDecoder('utf8');  // handles split codepoints
    this._buffer = '';
    this._max = options.maxLineLength ?? 1_000_000;
    this._stripCR = options.stripCR ?? true;
  }

  _transform(chunk, encoding, callback) {
    try {
      this._buffer += this._decoder.write(chunk);
      let newlineIdx;
      while ((newlineIdx = this._buffer.indexOf('\n')) !== -1) {
        let line = this._buffer.slice(0, newlineIdx);
        this._buffer = this._buffer.slice(newlineIdx + 1);
        if (this._stripCR && line.endsWith('\r')) line = line.slice(0, -1);
        this.push(line);
      }
      if (this._buffer.length > this._max) {
        return callback(new Error(`Line exceeds maxLineLength=${this._max}`));
      }
      callback();
    } catch (err) {
      callback(err);
    }
  }

  _flush(callback) {
    // emit trailing partial line (file without final newline)
    const tail = this._buffer + this._decoder.end();
    if (tail.length) {
      const line = this._stripCR && tail.endsWith('\r') ? tail.slice(0, -1) : tail;
      this.push(line);
    }
    this._buffer = '';
    callback();
  }
}

// usage
const fs = require('fs');
const { pipeline } = require('stream/promises');

(async () => {
  await pipeline(
    fs.createReadStream('access.log'),
    new LineParser(),
    async function* (source) {
      for await (const line of source) {
        if (line.includes('ERROR')) yield line + '\n';
      }
    },
    fs.createWriteStream('errors.log')
  );
})();
```

## Step-by-step dry run

Input file `access.log` with content `"GET /\nPOST /api\nDELETE"` (no trailing newline), delivered by libuv as three chunks: `"GET /\nPOS"`, `"T /api\nDELE"`, `"TE"`.

- **Chunk 1** `"GET /\nPOS"`: buffer becomes `"GET /\nPOS"`. Find `\n` at idx 5. Push `"GET /"`. Buffer becomes `"POS"`. No more newlines. callback().
- **Chunk 2** `"T /api\nDELE"`: buffer becomes `"POST /api\nDELE"`. Find `\n` at idx 9. Push `"POST /api"`. Buffer becomes `"DELE"`. callback().
- **Chunk 3** `"TE"`: buffer becomes `"DELETE"`. No newline. callback().
- **end()** → `_flush`. Buffer `"DELETE"` is non-empty. Push `"DELETE"`. callback().

Downstream receives three discrete objects: `"GET /"`, `"POST /api"`, `"DELETE"`. Exactly correct, despite libuv's arbitrary chunk boundaries. Memory peak was ~14 chars (longest line + buffered partial).

## Important takeaways

**Syntax to memorize**
- `class LineParser extends Transform` with `super({ readableObjectMode: true })`.
- The `_buffer += chunk; const lines = buffer.split('\n'); buffer = lines.pop();` idiom — that `.pop()` is the trick. The last element is always the partial trailing line (or empty string if chunk ended with `\n`).
- `_flush` exists for one reason: emit the final partial line.

**Patterns to reuse**
- Any framing protocol is this same skeleton: length-prefixed messages, JSON-NL, COBS, even HTTP/1 header parsing. Swap the delimiter, swap the split.
- The "carry-state-across-chunks" pattern generalizes to any stateful Transform: gzip decompression, sax-style XML, anything stateful over bytes.
- Coupled with an async generator (as in the usage example), you get a fully composable streaming pipeline that respects backpressure end-to-end.

**Common mistakes**
- Forgetting `_flush` → drops the last line of files without trailing newline.
- Not handling `\r\n` → emits lines with stray `\r` that break downstream `JSON.parse` etc.
- Calling `chunk.toString('utf8')` instead of `StringDecoder.write(chunk)` → garbled multi-byte chars on chunk boundaries.
- Calling `callback()` twice (once in try, once in catch) — crashes the stream.
- Setting `writableObjectMode: true` by accident → suddenly `_transform` receives whole objects, splits fail.

**Related questions**
- `backpressure-demo` — pushes from `_transform` propagate backpressure upstream automatically.
- `pipeline-error-propagation` — pair this Transform with `pipeline()` to see cleanup semantics.
- `callback-API-to-async-iterator` — alternative way to produce a "line iterator" without a Transform class.

## Variants

1. **CSV row parser** — same skeleton but the delimiter is `\n` *and* the output is split on commas (handling quoted fields). The interviewer is testing whether you can extend the skeleton; the line-buffer logic doesn't change.

2. **NDJSON parser** — emit parsed JS objects, not strings: `this.push(JSON.parse(line))`. Bonus: skip malformed lines vs error — make it a constructor flag.

3. **Length-prefixed binary framing** — instead of `\n`, frames are `[uint32 length][bytes...]`. Same `_buffer` pattern but with `Buffer.concat` and `readUInt32BE`. Demonstrates the line parser was just one instance of a more general framing problem.

## Revision notes

> **transform-line-parser — 60 second recap**
> - `class extends Transform`; `super({ readableObjectMode: true })`.
> - `_transform(chunk, enc, cb)`: append to buffer, split on `\n`, push complete lines, **`buffer = lines.pop()`** retains partial tail.
> - `_flush(cb)`: emit trailing buffer (handles files without final newline).
> - Use `StringDecoder` to survive multi-byte UTF-8 split across chunks.
> - Handle `\r\n` (strip trailing `\r`).
> - Cap line length to prevent adversarial unbounded buffer growth.
> - **Trap:** no `_flush` → last line dropped silently.
> - **Trap:** `chunk.toString('utf8')` corrupts emojis at chunk boundaries.
> - Same skeleton applies to CSV, NDJSON, length-prefixed framing.
