# NDJSON splitter

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [transform-line-parser.md](./transform-line-parser.md)
>
> **Source:** Stripe events, OpenAI streaming, log pipelines. Asked at Stripe, Cloudflare, Razorpay.

---

## 1. Problem statement

Parse NDJSON (newline-delimited JSON) from a byte stream. Each line is a JSON value.

**Verification examples**

```js
// Input bytes (across chunks):
// '{"a":1}\n{"b":2}\n{"c":3}\n'

// Output: stream of parsed JS values:
// {a: 1}
// {b: 2}
// {c: 3}
```

| Edge case                          | Behaviour                                              |
|------------------------------------|---------------------------------------------------------|
| Trailing newline                   | works                                                  |
| No trailing newline                | works via `_flush`                                     |
| Empty lines (blank)                | skip                                                   |
| Malformed JSON                     | emit error sentinel or rethrow                         |
| Huge line                          | buffer grows; bound for safety                         |
| CRLF                               | be lenient (spec says LF only)                        |
| Multi-byte UTF-8 across chunks     | use StringDecoder                                      |

**Constraints**
- Simpler than CSV — no embedded newlines in JSON line.
- Buffer the partial line across chunks.
- `JSON.parse` each complete line.
- `_flush` for final partial.

---

## 2. Plain-English restatement

NDJSON = one JSON value per line, `\n`-separated. Stream-parse without loading entire payload. Buffer the partial line; on each chunk, split, parse complete lines, save partial.

---

## 3. Why this matters in interviews

Common framing question for log pipelines + AI streaming. Simpler than CSV but tests the same chunk-boundary skill.

---

## 4. Mental model

```
   bytes → TextDecoderStream → ndjsonSplitter → JSON value per line → consumer
   
   ndjsonSplitter state:
     buf accumulates partial line across chunks.
     
     _transform(chunk):
       buf += chunk
       lines = buf.split('\n')
       buf = lines.pop()        ← LAST is partial (or empty if trailing \n)
       for line in lines:
         if !line.trim(): skip  ← empty lines
         try emit JSON.parse(line)
         catch: emit error sentinel or rethrow
     
     _flush:
       if buf.trim(): try parse; emit.

   Simpler than CSV:
   - JSON values can't contain literal newlines (only escaped \n).
   - So \n is unambiguous separator.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why is NDJSON simpler than CSV?
> 2. What happens to the final line if there's no trailing `\n`?
> 3. How to handle a malformed JSON line?

---

## 6. Brute force — walked through

### Wrong attempt 1: per-chunk JSON.parse
Chunks split lines; fails.

### Wrong attempt 2: load full payload
OOM on large.

### Wrong attempt 3: no `_flush`
Drops final line if no trailing `\n`.

---

## 7. The unlocking insight

> **Buffer partial line across chunks. Split on `\n`, pop last (partial), JSON.parse each. `_flush` emits final. Malformed JSON: pick policy — throw, skip, or sentinel.**

Three properties:

1. **Buffer partial** across chunks.
2. **JSON.parse per line** — simpler than CSV (no embedded newlines).
3. **`_flush` for final partial**.

---

## 8. Solution (annotated)

```js
const { Transform } = require('node:stream');

function makeNdjsonSplitter() {
  let buf = '';
  return new Transform({
    readableObjectMode: true,
    transform(chunk, enc, cb) {                                          // step 1: chunk handler
      buf += chunk.toString('utf8');
      const lines = buf.split('\n');
      buf = lines.pop();                                                 // step 2: partial last
      for (const line of lines) {
        if (!line.trim()) continue;                                      // step 3: skip empty
        try {
          this.push(JSON.parse(line));                                   // step 4: parse + emit
        } catch (e) {
          this.push({ __error: e.message, line });                       // step 5: error sentinel
        }
      }
      cb();
    },
    flush(cb) {                                                          // step 6: final partial
      if (buf.trim()) {
        try { this.push(JSON.parse(buf)); }
        catch (e) { this.push({ __error: e.message, line: buf }); }
      }
      buf = '';
      cb();
    },
  });
}

// Web Streams variant
function ndjsonTransformWeb() {
  let buf = '';
  return new TransformStream({
    transform(chunk, ctl) {
      buf += chunk;
      const lines = buf.split('\n');
      buf = lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        try { ctl.enqueue(JSON.parse(line)); }
        catch (e) { ctl.enqueue({ __error: e.message, line }); }
      }
    },
    flush(ctl) {
      if (buf.trim()) {
        try { ctl.enqueue(JSON.parse(buf)); }
        catch (e) { ctl.enqueue({ __error: e.message, line: buf }); }
      }
    },
  });
}
```

**Try it yourself**

```js
const fs = require('node:fs');
const { pipeline } = require('node:stream/promises');

await pipeline(
  fs.createReadStream('events.ndjson'),
  makeNdjsonSplitter(),
  async function* (events) {
    for await (const event of events) {
      if (event.__error) {
        console.error('parse error:', event.__error);
        continue;
      }
      yield processEvent(event);
    }
  },
  writableSink,
);

// HTTP streaming (OpenAI-style)
const response = await fetch('https://api.openai.com/v1/chat/completions', { /* ... */ });
const reader = response.body.pipeThrough(new TextDecoderStream()).pipeThrough(ndjsonTransformWeb());
for await (const event of reader) {
  console.log(event);
}
```

---

## 9. Step-by-step dry run

```
Input: '{"a":1}\n{"b":2}\n{"c":3}\n'

chunks: ['{"a":1}\n{"', 'b":2}\n{"c":3', '}\n']

ndjsonSplitter state:

chunk1: '{"a":1}\n{"'
  buf = '{"a":1}\n{"'
  split('\n') = ['{"a":1}', '{"']
  pop → buf = '{"'
  parse '{"a":1}' → emit {a:1}

chunk2: 'b":2}\n{"c":3'
  buf = '{"' + 'b":2}\n{"c":3' = '{"b":2}\n{"c":3'
  split('\n') = ['{"b":2}', '{"c":3']
  pop → buf = '{"c":3'
  parse '{"b":2}' → emit {b:2}

chunk3: '}\n'
  buf = '{"c":3' + '}\n' = '{"c":3}\n'
  split('\n') = ['{"c":3}', '']
  pop → buf = ''
  parse '{"c":3}' → emit {c:3}

upstream.end() → _flush:
  buf is empty → skip.

Output: {a:1}, {b:2}, {c:3}.

Without trailing \n:
  Final chunk: '{"c":3}' (no \n).
  buf = '{"c":3}'.
  upstream.end() → _flush: buf.trim() truthy → parse → emit.
```

---

## 10. Common confusion + traps

1. **Per-chunk parse** — fails on cross-chunk lines.
2. **No `_flush`** — drops final line.
3. **Malformed JSON policy** — pick: throw, skip, or sentinel.
4. **CRLF** — be lenient (spec is LF only).
5. **UTF-8 multi-byte split** — use `StringDecoder`.
6. **Empty lines** — skip.
7. **Huge line** — buffer can grow; consider bounded reader.

---

## 11. Senior follow-ups & variants

### Variant 1 — Web Streams TransformStream
Same logic; browser + modern Node.

### Variant 2 — Streaming API (OpenAI, Stripe events)
HTTP `Transfer-Encoding: chunked` + NDJSON.

### Variant 3 — Error recovery
Continue past bad lines vs abort on first error.

### Variant 4 — Backpressure
Pipeline propagates; consumer slowness slows reader.

### Variant 5 — Line-size limit
Reject lines larger than N bytes for safety.

---

## 12. How to think aloud

> "NDJSON is simpler than CSV: one JSON value per line, separated by `\n`. JSON spec doesn't allow literal newlines inside values (only escaped `\n`), so `\n` is unambiguous separator. State machine: buffer the partial line across chunks. Per chunk: append, split on `\n`, pop the last (partial), `JSON.parse` each complete line, push to output. `_flush` emits final partial (handles 'no trailing newline' case). Malformed JSON: pick policy — emit sentinel `{__error, line}` for downstream filter, OR rethrow to abort pipeline. Spec says LF only but be lenient with CRLF (`split(/\r?\n/)`). For UTF-8 safety across chunks use `StringDecoder` (raw `toString('utf8')` on partial multi-byte produces replacement char). Web Streams version uses `TransformStream` — same logic. Use cases: OpenAI streaming responses, Stripe events feed, application logs. Trap: per-chunk parse; no _flush; ignoring malformed; huge unbounded lines."

---

## 13. 60-second revision

> - **One JSON value per `\n`-delimited line.**
> - **Buffer partial** across chunks.
> - **`JSON.parse` each complete line.**
> - **`_flush` emits final** (no trailing `\n` case).
> - **Malformed policy:** sentinel, skip, or throw.
> - **CRLF lenient;** UTF-8 via StringDecoder.
> - **Web Streams** version available.
> - **Use:** OpenAI streaming, Stripe events, logs.
> - **Trap:** per-chunk parse; no _flush; unbounded line size.

---

**Related:** [transform-line-parser.md](./transform-line-parser.md) · [csv-parser-via-transform.md](./csv-parser-via-transform.md) · [fetch-response-async-iter.md](./fetch-response-async-iter.md) · [web-streams-transform.md](./web-streams-transform.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
