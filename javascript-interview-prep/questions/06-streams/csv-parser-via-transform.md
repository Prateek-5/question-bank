# CSV parser via TransformStream

> **Difficulty:** Medium-Senior   |   **Time:** ~15 min   |   **Prereqs:** [transform-line-parser.md](./transform-line-parser.md)
>
> **Source:** Cloudflare, Stripe, Razorpay (data-heavy roles). Production-grade lib: `csv-parser`, `papaparse`.

---

## 1. Problem statement

Stream-parse CSV without loading into memory. Handle quoted fields, embedded commas, embedded newlines, CRLF.

**Verification examples**

```js
// Input:
// name,age,note
// "alice",30,"contains, comma"
// "bob",25,"multi
// line"

// Output (stream of rows):
// ['name', 'age', 'note']
// ['alice', '30', 'contains, comma']
// ['bob', '25', 'multi\nline']
```

| Edge case                                | Behaviour                                              |
|------------------------------------------|---------------------------------------------------------|
| Quoted field with comma                  | comma is data, not separator                            |
| Quoted field with newline                | newline is data, not row terminator                    |
| Escaped quote (`""`)                     | literal `"` in field                                    |
| CRLF                                     | treat `\r\n` as one line break                          |
| Final line without `\n`                  | emit via flush                                          |

**Constraints**
- Two-level state machine: line splitter (quote-aware) + field splitter (quote-aware).
- Quoted fields can span chunks AND lines.
- `_flush` handles final partial.

---

## 2. Plain-English restatement

CSV is tricky: commas inside quoted fields aren't separators; newlines inside quoted fields aren't row terminators. Need a state machine tracking "inside quotes" across chunks. Two transforms: one splits into rows (newline-aware, quote-aware); one splits row into fields (comma-aware, quote-aware).

---

## 3. Why this matters in interviews

Stream composition + state machine + practical CSV quirks. Senior bar: handle quoted fields with embedded delimiters.

---

## 4. Mental model

```
   Two-stage pipeline:
   bytes → TextDecoder → CSVLineSplitter (quote-aware) → CSVRowParser → rows
   
   CSVLineSplitter state:
     buf, inQuotes
     for each char:
       if quote: toggle inQuotes
       if newline AND !inQuotes: emit line, reset buf
       else: append to buf
     flush: emit buf if non-empty.

   CSVRowParser (per line):
     fields = [], cur = '', inQuotes
     for each char:
       if inQuotes:
         if char === '"' and next === '"': cur += '"', skip next  (escaped quote)
         else if char === '"': inQuotes = false
         else: cur += char
       else:
         if char === ',': push cur, reset
         else if char === '"': inQuotes = true
         else: cur += char
     push cur (last field).
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why split CSV at the line level FIRST, then split fields?
> 2. What does `""` (two double-quotes) mean inside a quoted field?
> 3. Can newlines appear inside a CSV field?

---

## 6. Brute force — walked through

### Wrong attempt 1: split on `\n` then on `,`
Breaks for `"alice","x,y"` (comma inside quotes) and `"alice","x\ny"` (newline inside quotes).

### Wrong attempt 2: regex
Fragile; CSV grammar isn't regular due to escaping.

### Wrong attempt 3: load entire CSV into memory
OOM on large files.

---

## 7. The unlocking insight

> **Two state machines: line splitter (quote-aware so embedded newlines don't split) + field splitter (quote-aware so embedded commas don't split). Handle `""` as escaped quote.**

Three properties:

1. **Two-stage** — line split, then field split.
2. **Quote-aware at both stages** — embedded delimiters.
3. **`""` = literal `"`** inside quoted field.

---

## 8. Solution (annotated)

```js
const { Transform } = require('node:stream');

class CSVLineSplitter extends Transform {                               // step 1: quote-aware line split
  constructor(opts = {}) {
    super({ ...opts, readableObjectMode: true });
    this._buf = '';
    this._inQuotes = false;
  }
  _transform(chunk, enc, cb) {
    const text = chunk.toString('utf8');
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (c === '"') this._inQuotes = !this._inQuotes;
      if (c === '\n' && !this._inQuotes) {
        this.push(this._buf.replace(/\r$/, ''));                         // step 2: strip CRLF
        this._buf = '';
      } else {
        this._buf += c;
      }
    }
    cb();
  }
  _flush(cb) {
    if (this._buf) this.push(this._buf);
    cb();
  }
}

function parseCsvRow(line) {                                            // step 3: quote-aware field split
  const fields = [];
  let cur = '', inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (inQuotes) {
      if (c === '"' && line[i + 1] === '"') { cur += '"'; i++; }       // step 4: escaped quote
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

class CSVRowParser extends Transform {                                  // step 5: row → fields
  constructor(opts = {}) {
    super({ ...opts, writableObjectMode: true, readableObjectMode: true });
  }
  _transform(line, enc, cb) {
    this.push(parseCsvRow(line));
    cb();
  }
}

// Use
const fs = require('node:fs');
const { pipeline } = require('node:stream/promises');

await pipeline(
  fs.createReadStream('data.csv'),
  new CSVLineSplitter(),
  new CSVRowParser(),
  async function* (rows) {
    let header;
    for await (const row of rows) {
      if (!header) { header = row; continue; }
      yield Object.fromEntries(header.map((h, i) => [h, row[i]]));
    }
  },
  writableSink,
);
```

**Try it yourself**

```js
// Test edge cases
parseCsvRow('"alice",30,"x,y"');                                        // ['alice', '30', 'x,y']
parseCsvRow('"al""ice",30');                                            // ['al"ice', '30']    (escaped quote)
parseCsvRow('a,,b');                                                    // ['a', '', 'b']      (empty field)
parseCsvRow('"alice"');                                                 // ['alice']

// Multi-line quoted field
// Input: '"alice","multi\nline"\nbob,42'
// CSVLineSplitter emits TWO logical lines (embedded newline preserved):
// 1: '"alice","multi\nline"'
// 2: 'bob,42'
```

---

## 9. Step-by-step dry run

```
Input chunks:
chunk1: 'name,age\n"al'
chunk2: 'ice",30\n"x,y","emb'
chunk3: 'edded\nnewline",42\n'

CSVLineSplitter:
  chunk1: 'name,age\n"al'
    'n','a','m','e' → buf='name'
    ',','a','g','e' → buf='name,age'
    '\n' & !inQuotes → push('name,age'), buf=''
    '"' → inQuotes=true, buf='"'
    'a','l' → buf='"al'
  
  chunk2: 'ice",30\n"x,y","emb'
    'i','c','e' → buf='"alice'
    '"' → inQuotes=false, buf='"alice"'
    ',','3','0' → buf='"alice",30'
    '\n' & !inQuotes → push('"alice",30'), buf=''
    '"' → inQuotes=true, buf='"'
    'x',',','y' → buf='"x,y'   ← comma inside quotes preserved
    '"' → inQuotes=false, buf='"x,y"'
    ',','"' → buf='"x,y","', inQuotes=true
    'e','m','b' → buf='"x,y","emb'
  
  chunk3: 'edded\nnewline",42\n'
    'e','d','d','e','d' → buf='"x,y","embedded'
    '\n' & inQuotes → buf='"x,y","embedded\n'   ← newline inside quotes preserved
    'n','e','w','l','i','n','e' → buf='"x,y","embedded\nnewline'
    '"' → inQuotes=false, buf='"x,y","embedded\nnewline"'
    ',','4','2' → buf='...,"embedded\nnewline",42'
    '\n' & !inQuotes → push('"x,y","embedded\nnewline",42')

CSVRowParser receives each line, splits into fields with quote-aware logic.
Output:
  ['name', 'age']
  ['alice', '30']
  ['x,y', 'embedded\nnewline', '42']
```

---

## 10. Common confusion + traps

1. **Split on `\n` then `,`** — breaks for embedded delimiters.
2. **Regex** — fragile.
3. **Forget escaped quote** `""` — literal `"`.
4. **No CRLF handling** — Windows files.
5. **No `_flush`** — drops final line.
6. **OOM on large CSV** — must stream.
7. **Headers** — handle separately or via async iter.

---

## 11. Senior follow-ups & variants

### Variant 1 — Production libs
`csv-parser`, `papaparse` — battle-tested edge cases.

### Variant 2 — Streaming aggregation
`for await (const row of rows) { agg.add(row) }`.

### Variant 3 — TSV / other delimiters
Parametric delimiter argument.

### Variant 4 — Web Streams equivalent
`TransformStream` instead of Node's `Transform`.

### Variant 5 — Backpressure all the way
Pipeline already handles; consumer slowness propagates.

---

## 12. How to think aloud

> "CSV is tricky because commas inside quoted fields aren't separators and newlines inside quoted fields aren't row terminators. Two-stage pipeline: first a quote-aware LINE splitter (tracks `inQuotes` boolean across chunks; only splits on `\n` when not in quotes), then a quote-aware FIELD splitter (per-line; handles `""` as escaped quote). State must survive chunk boundaries — the line splitter's `inQuotes` flag is the key. `_flush` emits the final line if no trailing newline. CRLF: strip trailing `\r`. Pipeline composition: bytes → CSVLineSplitter → CSVRowParser → header-binding async generator → sink. For production use battle-tested libs (`csv-parser`, `papaparse`) — the edge cases are surprisingly nasty. Trap: naive split on `\n` then `,`; regex; forgetting escaped quote; missing _flush; CRLF; OOM on large files."

---

## 13. 60-second revision

> - **Two-stage:** quote-aware line splitter + quote-aware field splitter.
> - **`inQuotes` flag** survives chunk boundaries.
> - **`""`** = literal `"` (escaped).
> - **CRLF:** strip trailing `\r`.
> - **`_flush`** emits final line.
> - **Stream — don't load** entire CSV.
> - **Production libs:** `csv-parser`, `papaparse`.
> - **Trap:** naive split; regex; escaped quote; missing _flush.

---

**Related:** [transform-line-parser.md](./transform-line-parser.md) · [ndjson-splitter.md](./ndjson-splitter.md) · [web-streams-transform.md](./web-streams-transform.md) · [stream-pipeline-lab.md](./stream-pipeline-lab.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
