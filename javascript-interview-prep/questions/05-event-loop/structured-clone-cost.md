# Structured Clone — Cost, Pitfalls, Transferables

## Source / Origin
- HTML5 structured clone algorithm; `structuredClone(value)` global since 2022.
- Asked at: Razorpay, Atlassian, Stripe (browser-perf interviews).
- Concept reference: `concepts/event-loop.md`, sibling `postmessage-roundtrip.md`.

## Why this question matters in interviews
Every `postMessage` between worker/iframe/window, every `BroadcastChannel.postMessage`, every IndexedDB `put`, every `structuredClone()` call serializes data using the same algorithm. A naïve `worker.postMessage(hugeObject)` can stall the main thread for 100s of ms doing deep clone. Senior bar: (1) you know what structured clone can and can't handle; (2) you reach for transferables for large binary; (3) you understand it's *synchronous* on the sender; (4) you can name better strategies (transferable, shared memory, off-thread parse).

## Concepts involved

### Syntax to lock in
```js
// 1. Deep clone — replaces ad-hoc JSON.parse(JSON.stringify(x))
const original = { a: 1, b: new Date(), c: new Map([[1, 'x']]), d: new Uint8Array([1,2,3]) };
const copy = structuredClone(original);
copy !== original;       // true
copy.c !== original.c;   // true, but copy.c is a Map

// 2. Transferring (zero-copy) instead of cloning
const buf = new ArrayBuffer(10 * 1024 * 1024);  // 10 MB
worker.postMessage({ buf }, [buf]);              // 2nd arg = transfer list
// buf is now detached in main; cannot read it anymore
// buf.byteLength === 0
```

### Edge cases / interview traps
1. **Not everything clones.** Functions, DOM nodes, classes' prototypes, Symbols (in older engines), Error.cause (some engines) — throw or strip.
2. **Cyclic refs are supported.** `structuredClone({a: x, b: x})` preserves shared identity; `JSON` doesn't.
3. **Synchronous and blocking.** A 100MB clone freezes main for hundreds of ms.
4. **Maps, Sets, Date, RegExp, ArrayBuffer, TypedArray, ImageBitmap, Blob, File, FileList all supported.** Plain JSON doesn't handle these.
5. **Transferables: ArrayBuffer, MessagePort, ImageBitmap, OffscreenCanvas, ReadableStream, WritableStream, TransformStream.** Sender loses access.
6. **You can mix:** `postMessage({meta: {...}, payload: buf}, [buf])` — clone the wrapper, transfer the buffer.
7. **Cross-realm prototype loss.** A `MyClass` instance in main becomes a plain object in the worker (worker's MyClass is different).
8. **Performance.** Roughly O(size). Big nested objects = big cost.

## Mental Model

Three ways to move data across a worker boundary:

```
   1. Structured clone (default):
      sender ─[deep serialize]─▶ buffer ─[deep deserialize]─▶ receiver
              (slow, O(size))                                   (slow, O(size))
              both copies coexist

   2. Transferable:
      sender ─[hand off pointer]─▶ receiver
              (microseconds; sender loses access)
              one copy exists

   3. Shared (SharedArrayBuffer):
      sender writes ─▶ memory ◀── receiver reads
              (no copy; needs Atomics for ordering)
              one copy; both can access concurrently
```

Choose based on size and access pattern:

```
   small data (< 1 MB):           clone is fine
   big binary (> 1 MB):           transferable
   tight back-and-forth coordination:  shared + Atomics
```

## Why interviewers care

- **Performance instinct** — they want to see you reach for transferables on big data.
- **API knowledge** — knowing what structured clone supports vs JSON.
- **Boundary awareness** — main thread blocks on a big clone; sender's responsibility.

## Common beginner confusion

- **"`JSON.parse(JSON.stringify(x))` is the same."** No — JSON loses Date, Map, Set, undefined, functions; structured clone keeps Map/Set/Date/RegExp/typed arrays.
- **"Clone is async."** It's not — synchronous and blocking on the sender's thread.
- **"Transferable is a copy."** It's a move; sender loses access.
- **"Workers share memory by default."** No — strictly isolated until SharedArrayBuffer + COOP/COEP.
- **"Functions can be cloned."** No — they're not in the spec. You'd have to serialize to string and `eval` on the other side (insecure).

## Brute force approach

```js
// 10MB JSON serialize on main thread → 200ms freeze
const big = makeBigObject();
worker.postMessage(JSON.parse(JSON.stringify(big)));
// or even worse:
worker.postMessage(big);   // structuredClone runs anyway, just slightly cheaper
```

## Optimal approach

For large binary, allocate as `ArrayBuffer` (or `Uint8Array.buffer`) and *transfer* it. For data already structured (objects), prefer to construct in a worker (no main → worker hop) or pass IDs and let the worker fetch.

## Solution (JavaScript)

```js
// Pattern 1: pass big buffer zero-copy
async function processImage(file) {
  const buf = await file.arrayBuffer();        // ~10MB
  return rpc.call('processBuffer', { buf, width: 200 }, { transfer: [buf] });
}

// Pattern 2: stream chunks instead of one giant clone
async function* chunks(file, size = 1 << 16) {
  const stream = file.stream().getReader();
  while (true) {
    const { value, done } = await stream.read();
    if (done) return;
    yield value;
  }
}
for await (const chunk of chunks(file)) {
  worker.postMessage(chunk.buffer, [chunk.buffer]);
}

// Pattern 3: cost-measure
function measureCloneCost(obj) {
  const start = performance.now();
  structuredClone(obj);
  return performance.now() - start;
}
console.log(measureCloneCost(big10MB));     // e.g., 80ms

// Pattern 4: choose by size
function send(worker, payload) {
  const size = JSON.stringify(payload).length;       // rough proxy
  if (payload?.buf instanceof ArrayBuffer && size > 1e6) {
    worker.postMessage(payload, [payload.buf]);
  } else {
    worker.postMessage(payload);                      // clone is fine
  }
}
```

## Step-by-step dry run

10MB ArrayBuffer transfer:

```
main thread:
t=0   buf = new ArrayBuffer(10 * 1024 * 1024)
t=0   buf is owned by main; main can read/write
t=0   worker.postMessage({buf}, [buf])
       → engine detaches buf from main (buf.byteLength becomes 0)
       → ownership transferred to worker
       → main resumes immediately (no copy)

worker thread:
t=~1ms onmessage fires with { buf }
       new Uint8Array(buf) → can read/write
       buf is owned by worker now
```

Compare with clone (no transfer list):

```
t=0   worker.postMessage({buf})  — no transfer list
t=0   structured clone serializes 10MB → main thread blocks ~80ms
t=80  main resumes; buf still readable in main (still owned)
t=80  worker thread deserializes 10MB → ~80ms (worker's main loop blocked)
t=160 worker.onmessage fires with deep-copied buf
```

160ms total vs ~1ms.

## How to think aloud in the interview

> "Structured clone is the algorithm behind every postMessage. It's deep, synchronous, blocking on the sender. Supports Map/Set/Date/RegExp/TypedArray/cyclic refs — JSON doesn't. For >1MB binary, use transferables: ArrayBuffer/MessagePort/ImageBitmap; pass them in the second argument; sender loses access; zero-copy. For tight coordination, SharedArrayBuffer + Atomics. Always measure with `performance.now()` before optimizing — a 100KB clone is microseconds."

## Important takeaways

- **Synchronous and blocking** on sender.
- **Supports more than JSON** (Map, Set, Date, TypedArray, cyclic refs).
- **Does NOT support functions, DOM nodes, class prototypes.**
- **Transferables for >1MB binary.** Zero-copy.
- **Shared memory for tight loops.**
- **`performance.now()` to measure.**

## Variants

- **`structuredClone(value, { transfer: [buf] })`** — transfer within the clone call (zero-copy without going to a worker).
- **OffscreenCanvas transfer** — move rendering off main thread.
- **ReadableStream transfer** — pipe from worker to worker.
- **Lazy transfer** — pass an IDB key; worker fetches when needed.
- **MessagePort transferred** — opens a private channel between two contexts.

## Revision notes

```
Structured Clone (postMessage default):
  Deep, synchronous, blocking on sender
  Supports: Map, Set, Date, RegExp, TypedArray, ArrayBuffer, cyclic refs
  Does NOT: functions, DOM nodes, class prototypes, Symbol (older)
  Cost: O(size)
  
  Alternatives by size:
  - small (<1 MB): clone is fine
  - big binary: transferable (ArrayBuffer, MessagePort, ImageBitmap, OffscreenCanvas, Streams)
       postMessage(obj, [buf])
       sender loses access; zero-copy
  - tight coordination: SharedArrayBuffer + Atomics
  
  TRAPS:
  - JSON loses Date/Map/Set/undefined; clone keeps them
  - sender blocks during clone
  - prototype lost cross-realm
  - functions throw
```
