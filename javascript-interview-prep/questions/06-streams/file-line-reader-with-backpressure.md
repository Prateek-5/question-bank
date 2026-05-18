# File Line Reader with Backpressure

## Source / Origin
- Classic "read this big log file line by line" question.
- Asked at: Razorpay, Atlassian, Cloudflare.
- Concept reference: `concepts/streams.md`, sibling `ndjson-splitter.md`.

## Why this question matters in interviews
Read a 10 GB log file without OOMing and with throttling-aware processing. Senior bar: you use Node's `readline.createInterface` *or* an async generator over `fs.createReadStream`, handle backpressure (slow consumer doesn't blow buffer), and use `for await` for clean integration.

## Concepts involved

```js
import { createReadStream } from 'node:fs';
import { createInterface } from 'node:readline';

async function* readLines(path) {
  const stream = createReadStream(path, { encoding: 'utf8' });
  const rl = createInterface({ input: stream, crlfDelay: Infinity });
  for await (const line of rl) yield line;
}

for await (const line of readLines('/var/log/big.log')) {
  await process(line);   // pipeline awaits → backpressure
}
```

### Edge cases / traps
1. **`crlfDelay: Infinity`** — treats CR-LF as one line break (not two).
2. **`for await` honors backpressure** — slow consumer slows reader.
3. **Encoding**: `utf8` decodes; binary mode if you need raw bytes.
4. **Open file descriptors** — `for await` cleanup closes the stream; `break`/`throw` also closes.
5. **Stream pause/resume** automatic via `for await`.
6. **Large lines** — readline buffers entire line in memory; bound if untrusted input.
7. **Error handling** — wrap in try/catch; `for await` rethrows.
8. **Cancellation** — AbortSignal supported in modern Node (`createInterface({ input, signal })`).

## Mental Model

```
   file → fs.ReadStream (Node Readable) → readline.Interface (line emitter)
   for await (line of rl) — pulls one line at a time, pauses underlying read when consumer is busy
```

## Solution

```js
import { createReadStream } from 'node:fs';
import { createInterface } from 'node:readline';

async function processFile(path, fn) {
  const rl = createInterface({
    input: createReadStream(path, { encoding: 'utf8' }),
    crlfDelay: Infinity,
  });
  let lineNo = 0;
  try {
    for await (const line of rl) {
      lineNo++;
      await fn(line, lineNo);
    }
  } catch (e) {
    e.lineNo = lineNo;
    throw e;
  } finally {
    rl.close();
  }
}

// Usage
await processFile('/var/log/big.log', async (line, n) => {
  if (line.includes('ERROR')) await sendAlert(line);
});

// With AbortController (Node 17+)
import { setTimeout as sleep } from 'node:timers/promises';
const ac = new AbortController();
setTimeout(() => ac.abort(), 60_000);
try {
  const rl = createInterface({ input: createReadStream(path), signal: ac.signal, crlfDelay: Infinity });
  for await (const line of rl) await handle(line);
} catch (e) {
  if (e.name === 'AbortError') console.log('cancelled');
  else throw e;
}

// Backpressure demo: slow consumer
async function* readBatched(path, batchSize = 100) {
  let batch = [];
  for await (const line of readLines(path)) {
    batch.push(line);
    if (batch.length === batchSize) { yield batch; batch = []; }
  }
  if (batch.length) yield batch;
}

for await (const batch of readBatched('/big.log', 1000)) {
  await bulkInsertDb(batch);
  // backpressure: reader pauses while we await bulkInsertDb
}
```

## Dry run

```
file: "line1\nline2\nline3"
fs.ReadStream → readline → emits "line1", "line2", "line3"
for await: process line1 (await 50ms) → readline pauses underlying read
50ms later: pull "line2" → process → pause
...
EOF: loop ends; rl.close()
```

Memory stays O(line length), not O(file size).

## How to think aloud

> "Use `readline.createInterface` over `fs.createReadStream`. `for await` on the interface gives line-by-line iteration with backpressure — slow consumer paces the reader. `crlfDelay: Infinity` for CR-LF safety. Try/finally to close the interface even on error. For batching, accumulate N lines and yield batches. AbortSignal for cancellation in modern Node."

## Important takeaways

- **`createInterface` + `for await`** = clean, backpressure-aware.
- **`crlfDelay: Infinity`** for CR-LF.
- **Backpressure automatic** via `for await`.
- **Always close in finally.**
- **Batch for downstream efficiency** (DB inserts, API sends).
- **AbortSignal** in modern Node.

## Variants

- **Custom splitter via `stream.Transform`** — for non-newline delimiters.
- **Reverse-read** for log tailing — read from end of file.
- **`tail -f` semantics** — watch for appends.
- **Compressed input** — pipe through `zlib.createGunzip()` before readline.

## Revision notes

```
readline-based line reader:
  rl = createInterface({input: createReadStream(path), crlfDelay: Infinity})
  for await (const line of rl): await fn(line)
  finally rl.close()

backpressure: for await pauses upstream when consumer awaits
batching: accumulate N lines per batch

cancel: AbortSignal in createInterface (Node 17+)
encoding: utf8 in ReadStream options
memory: O(line length), not O(file size)
```
