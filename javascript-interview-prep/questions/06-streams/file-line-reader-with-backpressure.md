# File line reader with backpressure

> **Difficulty:** Medium   |   **Time:** ~10 min   |   **Prereqs:** [async-iterator-pagination.md](./async-iterator-pagination.md), [backpressure-demo.md](./backpressure-demo.md)
>
> **Source:** Razorpay, Atlassian, Cloudflare. Classic "tail this 10GB log" question.

---

## 1. Problem statement

Read a large log file line by line without OOMing. Slow consumer must throttle reader.

**Verification examples**

```js
const { createReadStream } = require('node:fs');
const { createInterface } = require('node:readline');

async function* readLines(path) {
  const stream = createReadStream(path, { encoding: 'utf8' });
  const rl = createInterface({ input: stream, crlfDelay: Infinity });
  for await (const line of rl) yield line;
}

for await (const line of readLines('/var/log/big.log')) {
  await process(line);                                                    // slow consumer; backpressure
}
```

**Constraints**
- Memory O(line size), not O(file size).
- Slow consumer slows reader via `for await` backpressure.
- `crlfDelay: Infinity` handles CRLF as one break.
- `for await` cleanup closes stream on early break.

---

## 2. Plain-English restatement

`fs.createReadStream` reads bytes; `readline.createInterface` splits into lines. `for await` consumes one line at a time, awaiting each. Slow consumer naturally throttles the reader.

---

## 3. Why this matters in interviews

Practical backend skill — log tail, NDJSON ingest, CSV processing. Tests `readline` + async iteration + backpressure literacy.

---

## 4. Mental model

```
   File on disk
   ↓
   fs.createReadStream (Node Readable)
     chunks at highWaterMark (default 64KB)
   ↓
   readline.createInterface (line emitter)
     splits chunks on \n (and \r\n with crlfDelay: Infinity)
   ↓
   for await (line of rl)
     consumer awaits per line
     SLOW consumer → readline pauses → readStream pauses
   ↓
   await process(line)
     network call, DB write, etc.

   Backpressure END-TO-END:
   - process(line) takes 100ms.
   - readline only emits next line when consumer awaits.
   - readStream only reads next chunk when readline drains.
   - Disk reads paced by consumer.
   
   Cleanup:
   - for await break → close readline → close readStream → close fd.
   - throw → same.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Does `for await` automatically apply backpressure?
> 2. Why `crlfDelay: Infinity`?
> 3. What happens to the file descriptor if you `break` mid-iteration?

---

## 6. Brute force — walked through

### Wrong attempt 1: `readFileSync('big.log').split('\n')`
OOM on 10GB file.

### Wrong attempt 2: `readStream.on('data')` accumulating
Manual buffering; harder to apply backpressure.

### Wrong attempt 3: ignore `crlfDelay`
Windows files: `\r` in line content.

---

## 7. The unlocking insight

> **`for await` over `readline.createInterface` gives line-by-line iteration with automatic backpressure. Slow consumer slows reader. `crlfDelay: Infinity` for CRLF safety. Cleanup automatic on break/throw.**

Three properties:

1. **`readline` over `fs.createReadStream`** — line emitter.
2. **`for await` auto backpressure** — consumer drives pace.
3. **`crlfDelay: Infinity`** for CRLF treatment.

---

## 8. Solution (annotated)

```js
const { createReadStream } = require('node:fs');
const { createInterface } = require('node:readline');

async function* readLines(path, { signal } = {}) {                      // step 1: generator wrapper
  const stream = createReadStream(path, { encoding: 'utf8' });
  const rl = createInterface({
    input: stream,
    crlfDelay: Infinity,                                                  // step 2: CRLF as one break
    signal,                                                               // step 3: AbortSignal support
  });
  for await (const line of rl) yield line;                                 // step 4: forward + auto cleanup
}

// Usage
for await (const line of readLines('/var/log/big.log')) {
  await processLine(line);                                                 // step 5: slow consumer throttles
}

// With cancellation
const ac = new AbortController();
setTimeout(() => ac.abort(), 30_000);

try {
  for await (const line of readLines('/var/log/big.log', { signal: ac.signal })) {
    await processLine(line);
  }
} catch (err) {
  if (err.name === 'AbortError') console.log('cancelled');
  else throw err;
}
```

**Try it yourself**

```js
// Aggregate count
let errorCount = 0;
for await (const line of readLines('/var/log/app.log')) {
  if (line.includes('ERROR')) errorCount++;
}
console.log('errors:', errorCount);

// Early termination
for await (const line of readLines('/var/log/big.log')) {
  console.log(line);
  if (lineMatchesSomething(line)) break;                                  // closes stream automatically
}

// Pipeline composition
const { pipeline } = require('node:stream/promises');
const { Readable } = require('node:stream');

await pipeline(
  Readable.from(readLines('/var/log/app.log')),
  async function* (lines) {
    for await (const line of lines) {
      if (line.includes('ERROR')) yield line;
    }
  },
  fs.createWriteStream('errors.log'),
);
```

---

## 9. Step-by-step dry run

```
const lines = readLines('big.log');

for await (line of lines):
  Internally:
    iter = lines[Symbol.asyncIterator]()
    while:
      {value, done} = await iter.next()
      if done break
      // body with line
      await processLine(line)    ← 100ms; this is what throttles upstream

readline emits line:
  fs.createReadStream reads chunk (~64KB).
  readline splits on \n.
  Emits line via 'line' event (under the hood).
  async iter wraps this.

Backpressure chain:
  processLine awaits 100ms.
  for await pauses → iter.next() promise unresolved.
  readline waits → no more 'line' emissions.
  fs.createReadStream pauses → no disk reads.

When processLine resolves:
  for await calls iter.next() again.
  readline checks: buffered lines? yes → emit next.
  If buffer empty → fs reads next chunk → readline splits → emits.

Early break:
  for await calls iter.return().
  readline closes interface.
  fs.createReadStream destroyed; fd released.

Throw inside loop:
  same as break + error propagated.

Total memory:
- Current line in flight.
- ~64KB buffer in readStream.
- Constant regardless of file size.
```

---

## 10. Common confusion + traps

1. **`readFileSync.split('\n')`** — OOM on large files.
2. **No `crlfDelay`** — Windows file `\r` in line content.
3. **Manual `data` handler** — easy to mess up backpressure.
4. **Forget `for await`** for backpressure — `forEach` is eager.
5. **Promise.all inside loop** — defeats throttling.
6. **Large lines** — readline buffers entire line; bound for safety.
7. **No AbortSignal threading** — can't cancel mid-read.

---

## 11. Senior follow-ups & variants

### Variant 1 — Tail follow
`fs.createReadStream(path, { start: position })`; re-read on `'change'`.

### Variant 2 — Multi-file
Sequentially `for await` over each file.

### Variant 3 — Compressed file
`pipeline(createReadStream, zlib.createGunzip(), readline)`.

### Variant 4 — Parallel processing
`p-limit` semaphore inside loop (careful — concurrency 1 keeps backpressure).

### Variant 5 — Web Streams
`new ReadableStream` + `pipeThrough(LineSplitter)`.

---

## 12. How to think aloud

> "`fs.createReadStream` is a Node Readable; `readline.createInterface({ input, crlfDelay: Infinity })` is a line emitter built on top. `for await` over the readline interface gives line-by-line iteration with AUTOMATIC backpressure: each iteration awaits — if `process(line)` takes 100ms, readline only emits the next line when the consumer is ready, which means `fs.createReadStream` only reads the next chunk when readline's buffer drains. Backpressure flows end-to-end. Memory: O(line size + chunk buffer), not O(file size). `crlfDelay: Infinity` treats CRLF as one line break (Windows files have `\r\n`). Cleanup automatic on break or throw — `for await` calls `.return()` on the async iterator, which closes the readline interface, which destroys the read stream, which releases the file descriptor. AbortSignal support via `createInterface({ signal })` — abort throws AbortError out of the for-await. Trap: `readFileSync.split` (OOM); manual `data` handler (backpressure broken); `Promise.all` inside loop (defeats throttling); huge lines (readline buffers entire line)."

---

## 13. 60-second revision

> - **`fs.createReadStream` + `readline.createInterface`** — line emitter.
> - **`for await (line of rl)`** — auto backpressure.
> - **`crlfDelay: Infinity`** for CRLF.
> - **Memory O(line size)** — not O(file size).
> - **`break`/`throw`** auto-closes fd.
> - **`AbortSignal`** via `createInterface({ signal })`.
> - **Compose with pipeline** for filter/transform stages.
> - **Trap:** readFileSync.split (OOM); manual data handler; Promise.all inside loop.

---

**Related:** [async-iterator-pagination.md](./async-iterator-pagination.md) · [backpressure-demo.md](./backpressure-demo.md) · [transform-line-parser.md](./transform-line-parser.md) · [stream-pipeline-lab.md](./stream-pipeline-lab.md)

**Concept primer:** [`concepts/streams.md`](../../concepts/streams.md)
