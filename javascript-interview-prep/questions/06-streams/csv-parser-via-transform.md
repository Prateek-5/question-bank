# CSV Parser via TransformStream

## Source / Origin
- Common stream-parsing question.
- Asked at: Cloudflare, Stripe, Razorpay (data-heavy roles).
- Concept reference: `concepts/streams.md`, sibling `web-streams-transform.md`.

## Why this question matters in interviews
Parse a CSV without loading it into memory. Tests stream composition + CSV quirks (quoted fields, embedded commas, embedded newlines, CRLF). Senior bar: you handle quoted-field state machine cleanly and compose two transforms: one for lines (newline-aware), one for fields (quote-aware).

## Concepts involved

```js
// Line-by-line transform (CSV-aware: respect quoted fields containing \n)
class CSVLineSplitter extends TransformStream {
  constructor() {
    let buf = '', inQuotes = false;
    super({
      transform(chunk, ctl) {
        for (const c of chunk) {
          if (c === '"') inQuotes = !inQuotes;
          if (c === '\n' && !inQuotes) {
            ctl.enqueue(buf.replace(/\r$/, ''));
            buf = '';
          } else {
            buf += c;
          }
        }
      },
      flush(ctl) { if (buf) ctl.enqueue(buf); },
    });
  }
}

function parseCsvRow(line) {
  const fields = [];
  let cur = '', inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (inQuotes) {
      if (c === '"' && line[i+1] === '"') { cur += '"'; i++; }
      else if (c === '"') inQuotes = false;
      else cur += c;
    } else {
      if (c === ',') { fields.push(cur); cur = ''; }
      else if (c === '"') inQuotes = true;
      else cur += c;
    }
  }
  fields.push(cur);
  return fields;
}
```

### Edge cases / traps
1. **Quoted fields can contain commas and newlines.** Naive `.split(',')` and `.split('\n')` both fail.
2. **Escaped quote**: `""` inside a quoted field is one `"`.
3. **CRLF line endings** — strip `\r` at end.
4. **No header line** — caller decides; parser doesn't.
5. **Empty fields** — `a,,b` → ['a', '', 'b'].
6. **BOM** at start — strip.
7. **Encoding** — assume UTF-8 via TextDecoder.
8. **Field count mismatch** — strict mode throws; lenient mode emits with null padding.

## Mental Model

```
   bytes → TextDecoderStream → CSVLineSplitter → row strings → parseCsvRow → arrays
   
   line splitter: state = {buf, inQuotes}
   field parser: per-char state machine
```

## Why interviewers care

- **State machine fluency.**
- **Streaming + correctness.**
- **CSV trickier than it looks.**

## Solution

```js
async function* csvRows(stream) {
  const decoded = stream.pipeThrough(new TextDecoderStream());
  let header = null;
  let buf = '', inQuotes = false;
  for await (const chunk of decoded) {
    for (const c of chunk) {
      if (c === '"') inQuotes = !inQuotes;
      if (c === '\n' && !inQuotes) {
        const row = parseCsvRow(buf.replace(/\r$/, ''));
        buf = '';
        if (!header) { header = row; continue; }
        yield Object.fromEntries(header.map((h, i) => [h, row[i]]));
      } else {
        buf += c;
      }
    }
  }
  if (buf) {
    const row = parseCsvRow(buf);
    if (header) yield Object.fromEntries(header.map((h, i) => [h, row[i]]));
  }
}

// Usage with fetch
const res = await fetch('/data.csv');
for await (const row of csvRows(res.body)) {
  console.log(row.name, row.email);
}
```

## Dry run

```
input: "name,email\nalice,a@x.com\n\"bob, jr.\",b@y.com\n"
chunk 1: "name,email\nalice,"
  parse chars; on \n (not inQuotes): line "name,email" → header=['name','email']; buf=""
  buf="alice,"
chunk 2: "a@x.com\n\"bob, jr.\",b@y.com\n"
  parse chars; on \n (not inQuotes): line "alice,a@x.com" → row=['alice','a@x.com'] → yield {name:'alice', email:'a@x.com'}
  then enter quotes at "; comma inside quotes preserved
  on closing "; comma outside; on \n: line "\"bob, jr.\",b@y.com" → row=['bob, jr.', 'b@y.com'] → yield ...
```

## How to think aloud

> "CSV has two state machines: one for line splitting (newlines outside quotes are real), one for field splitting (commas outside quotes are real). I split into a streaming line splitter and a per-line field parser. Stream the bytes through TextDecoder, accumulate, split. Handle CRLF by stripping `\r`. Handle escaped quote via lookahead `""`. Use header row to emit objects; for CSV without headers, emit arrays."

## Important takeaways

- **Two state machines**: line (newline-aware), field (quote-aware).
- **Quoted fields**: commas and newlines allowed inside.
- **Escape**: `""` inside quotes = `"`.
- **CRLF**: strip `\r`.
- **Use TextDecoderStream** + custom transform.

## Variants

- **`csv-parse` / `papaparse`** libraries — production-grade.
- **TSV** — same shape, different delimiter.
- **Streaming row writes** to DB with batched inserts.
- **Validation** — Zod schema per row.

## Revision notes

```
streaming CSV:
  line splitter (newline-aware): state {buf, inQuotes}; only \n outside quotes splits
  field parser (quote-aware): per-char state machine
  escaped quote: ""

handle:
  CRLF: strip \r at end of line
  empty fields: a,,b → ['a','','b']
  BOM: strip at start
  encoding: TextDecoderStream

compose:
  res.body → TextDecoderStream → lineSplitter → parseCsvRow → object
```
