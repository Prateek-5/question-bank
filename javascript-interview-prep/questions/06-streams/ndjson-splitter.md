# NDJSON Splitter

## Source / Origin
- Newline-delimited JSON — popular for streaming APIs (Stripe events, OpenAI streaming, logs).
- Asked at: Stripe, Cloudflare, Razorpay.
- Concept reference: `concepts/streams.md`, sibling `csv-parser-via-transform.md`.

## Why this question matters in interviews
NDJSON is simpler than CSV: one JSON value per line, separated by `\n`. Tests basic streaming + handling chunks that don't align on line boundaries. Senior bar: you parse correctly across chunk boundaries, handle the final line without trailing `\n`, and survive malformed lines without dying.

## Concepts involved

```js
function makeNdjsonSplitter() {
  let buf = '';
  return new TransformStream({
    transform(chunk, ctl) {
      buf += chunk;
      const lines = buf.split('\n');
      buf = lines.pop();        // last is partial
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

### Edge cases / traps
1. **Trailing newline vs no trailing newline.** `split('\n')` handles both; `pop()` saves the partial.
2. **Empty lines** (blank between records) — skip.
3. **Malformed JSON** — choose: throw (rare), emit error sentinel (common), skip silently (loose).
4. **Huge line** — buffer can grow if the line is bigger than expected; safer with line length limit.
5. **No `\r\n` issue** — NDJSON spec says LF only, but be lenient with CRLF.
6. **Encoding** — TextDecoderStream before splitter.

## Mental Model

```
   bytes → TextDecoderStream → ndjsonSplitter → JSON value per line → consumer
   buf accumulates partial line across chunks
   split('\n') → all complete lines + one partial → keep partial in buf
```

## Solution

```js
// Compose
const res = await fetch('/events.ndjson');
const piped = res.body
  .pipeThrough(new TextDecoderStream())
  .pipeThrough(makeNdjsonSplitter());

for await (const event of piped) {
  if (event.__error) console.warn('skip malformed', event);
  else handleEvent(event);
}

// As async generator (alternative)
async function* ndjsonGen(url, { signal } = {}) {
  const res = await fetch(url, { signal });
  const dec = new TextDecoder();
  let buf = '';
  for await (const chunk of res.body) {
    buf += dec.decode(chunk, { stream: true });
    const lines = buf.split('\n');
    buf = lines.pop();
    for (const line of lines) {
      if (line.trim()) yield JSON.parse(line);
    }
  }
  if (buf.trim()) yield JSON.parse(buf);
}

for await (const event of ndjsonGen('/events.ndjson')) console.log(event);
```

## Dry run

`'{"a":1}\n{"b":2}\n{"c":3}'` in two chunks: `'{"a":1}\n{"b":2'`, `'}\n{"c":3}'`.

```
chunk 1: buf = '{"a":1}\n{"b":2'
  split → ['{"a":1}', '{"b":2']
  pop → buf = '{"b":2'; complete=['{"a":1}']
  yield {a:1}

chunk 2: buf = '{"b":2' + '}\n{"c":3}' = '{"b":2}\n{"c":3}'
  split → ['{"b":2}', '{"c":3}']
  pop → buf = '{"c":3}'; complete=['{"b":2}']
  yield {b:2}

stream ends:
  buf = '{"c":3}' → yield {c:3}
```

## How to think aloud

> "Accumulate bytes through TextDecoder. Split by `\n`; the last piece is partial — save in buf. Emit JSON.parse of each complete line; on flush, emit the saved buf if non-empty. Decide error policy: emit `{__error, line}` sentinels so consumers see all lines, or throw to stop. For huge files, add a length guard so a runaway line doesn't OOM."

## Important takeaways

- **`split('\n')` + `pop()`** keeps trailing partial line.
- **Flush emits saved partial** at end.
- **Skip empty lines.**
- **Error policy**: sentinel object or throw.
- **TextDecoderStream first** for byte safety.

## Variants

- **JSON-array streaming** — different format; needs a JSON-aware streaming parser (e.g., `oboe.js`).
- **Length-prefixed framing** — alternative to newline-delimited.
- **Compression**: `DecompressionStream` upstream.
- **Bounded line size** — reject lines over N MB.

## Revision notes

```
NDJSON splitter:
  buf = ''
  transform(chunk):
    buf += chunk
    lines = buf.split('\n')
    buf = lines.pop()
    for each line: yield JSON.parse(line)
  flush:
    if buf: yield JSON.parse(buf)

error policy:
  emit {__error, line} sentinels (lenient)
  or throw (strict)

compose: res.body → TextDecoderStream → splitter → consumer
```
