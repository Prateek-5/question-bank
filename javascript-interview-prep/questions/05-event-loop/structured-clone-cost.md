# Structured Clone — cost, pitfalls, transferables

> **Difficulty:** Medium-Senior   |   **Time:** ~15 min   |   **Prereqs:** [postmessage-roundtrip.md](./postmessage-roundtrip.md), [`10-machine-coding-patterns/deep-clone-with-cycles.md`](../10-machine-coding-patterns/deep-clone-with-cycles.md)
>
> **Source:** HTML5 structured-clone algorithm. `structuredClone(value)` global (Node 17+, all modern browsers).

---

## 1. Problem statement

What does the structured clone algorithm handle, what's its cost on large payloads, when do you reach for transferables or `SharedArrayBuffer`?

**Verification examples**

| Operation                                | Behaviour                                              |
|------------------------------------------|---------------------------------------------------------|
| `structuredClone({a: new Date()})`        | clones; Date preserved                                  |
| `structuredClone(cyclic)`                 | preserves cycle (vs JSON throws)                       |
| `structuredClone(fn)`                     | DataCloneError                                          |
| `worker.postMessage(huge)`                | structured-clones; synchronous on sender (blocks main) |
| `worker.postMessage({buf}, [buf])`        | transfers; zero-copy; original detached                 |
| `SharedArrayBuffer` between threads       | shared memory; mutation visible via `Atomics`          |

**Constraints**
- Synchronous on sender — large payloads stall main thread.
- Handles cycles, Date, RegExp, Map, Set, TypedArrays, ArrayBuffer.
- Throws on functions, DOM nodes, class prototypes.
- Transferables (`ArrayBuffer`, `MessagePort`, `ImageBitmap`) move ownership.

---

## 2. Plain-English restatement

The algorithm that backs `structuredClone()`, `postMessage`, `BroadcastChannel`, IndexedDB. Handles most data types except functions/DOM nodes. **Cost matters**: copying a 100MB object takes ~100ms. For large binaries, use transferables (move ownership, zero-copy) or `SharedArrayBuffer` (shared memory).

---

## 3. Why this matters in interviews

Every `postMessage` uses this. Naive `worker.postMessage(hugeObject)` stalls main thread. Senior bar: reach for transferables.

---

## 4. Mental model

```
   structuredClone deep-copies, with full type fidelity:
   ┌──────────────────────────────────────────────┐
   │ Date, RegExp, Map, Set, ArrayBuffer,         │
   │ TypedArrays, Blob, FileList, RegExp,          │
   │ basic objects, arrays, primitives             │
   │ CYCLES preserved.                             │
   │                                                │
   │ THROWS: functions, DOM nodes, class proto,   │
   │ Symbol keys (some engines), WeakMap/WeakSet  │
   └──────────────────────────────────────────────┘

   Cost: O(n) bytes copied. Synchronous on sender.

   Three strategies for big payloads:
   1. structured clone (copy)        ← default postMessage
   2. transferList (zero-copy move)  ← ownership transfers
   3. SharedArrayBuffer (shared)     ← both see same memory
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Does `structuredClone` preserve a cycle?
> 2. What happens to `buf.byteLength` after `postMessage({buf}, [buf])`?
> 3. Can you `postMessage` a function?

---

## 6. Brute force — walked through

### Wrong attempt 1: `JSON.parse(JSON.stringify(x))`
Throws on cycles. Stringifies Date. Drops fn/undefined. Lossy.

### Wrong attempt 2: `postMessage` huge binary without transferList
Copies all bytes. Synchronous on sender. Stalls main thread.

### Wrong attempt 3: assume `structuredClone` is free
O(n) bytes, synchronous. ~100ms for 100MB.

---

## 7. The unlocking insight

> **Structured clone is O(n) synchronous on sender. For large binaries: `postMessage(data, [transferList])` transfers ownership (zero-copy, ArrayBuffer detached on sender). For continuous sharing: `SharedArrayBuffer` + `Atomics` — same memory visible to both threads.**

Three properties:

1. **Synchronous on sender** — large payload = main-thread stall.
2. **Transferables** = zero-copy ownership move.
3. **SharedArrayBuffer** = shared memory; needs `Atomics` for safe mutation.

---

## 8. Solution (annotated)

```js
// Deep clone with full type fidelity
const original = { a: 1, b: new Date(), c: new Map([[1, 'x']]), d: new Uint8Array([1,2,3]) };
const copy = structuredClone(original);
copy !== original;             // true
copy.c instanceof Map;          // true (vs JSON would be {})

// Cycle preservation
const cyclic = { a: 1 };
cyclic.self = cyclic;
const cyclicCopy = structuredClone(cyclic);
cyclicCopy.self === cyclicCopy; // true

// Transferring (zero-copy)
const buf = new ArrayBuffer(10 * 1024 * 1024);                       // 10MB
worker.postMessage({ buf }, [buf]);                                   // step 1: transferList
buf.byteLength;                                                       // 0 — DETACHED in sender

// Shared memory
const sab = new SharedArrayBuffer(8);
const view = new Int32Array(sab);
worker.postMessage({ sab });                                           // step 2: handle copy; memory shared
Atomics.add(view, 0, 1);                                               // step 3: safe shared mutation
```

**Try it yourself**

```js
// Bad: copies 100MB synchronously, stalls main thread ~100ms
worker.postMessage({ huge: new Uint8Array(100_000_000) });

// Good: transfers ownership, ~free
const buf = new ArrayBuffer(100_000_000);
worker.postMessage({ buf }, [buf]);
// After: buf is detached in main; worker owns it.

// Throws: functions don't clone
worker.postMessage({ fn: () => 42 });  // DataCloneError
```

---

## 9. Step-by-step dry run

```
postMessage with copy (no transferList):
  sender: traverse value, deep-clone via algorithm
    O(n) bytes copied → new allocation
    synchronous; sender's main thread BLOCKED for ~10ms per MB
  receiver: receives the clone in a 'message' event (next macrotask)

postMessage with transferList:
  sender: take ownership of listed objects
    no byte copy — pointer transfer
    sender's reference is DETACHED (e.g., ArrayBuffer.byteLength → 0)
  receiver: receives transferred objects in 'message' event

SharedArrayBuffer:
  sender: postMessage({sab}) → algorithm clones handle, NOT bytes
  both: have a view of the SAME memory
  mutation visible to both, IF you use Atomics for safety
  no event needed — just read memory anytime
```

---

## 10. Common confusion + traps

1. **`structuredClone` is free** — O(n) synchronous.
2. **`postMessage` huge data** — copies; use transferList.
3. **Transferable after postMessage** — DETACHED in sender.
4. **`SharedArrayBuffer` without Atomics** — race; silent corruption.
5. **`SharedArrayBuffer` available everywhere** — cross-origin-isolation headers required in browsers.
6. **Functions clone** — they don't; throws.
7. **`structuredClone` vs `Object.assign`** — Object.assign is shallow; structuredClone is deep.

---

## 11. Senior follow-ups & variants

### Variant 1 — Off-thread parse
Parse JSON in a worker (`JSON.parse` is synchronous and CPU-bound). Move bytes via transferList.

### Variant 2 — `MessageChannel` with transfer
Use ports as transferables to set up dedicated lanes between workers.

### Variant 3 — Cross-origin isolation
Browsers require `Cross-Origin-Opener-Policy: same-origin` + `Cross-Origin-Embedder-Policy: require-corp` for SAB.

### Variant 4 — IndexedDB uses structured clone
Stores use the same algorithm — write/read symmetric.

### Variant 5 — Schemas for hot paths
For high-throughput RPC, define a schema (Protobuf, MessagePack) and skip structured clone overhead.

---

## 12. How to think aloud

> "Structured clone is the algorithm behind `structuredClone()`, `postMessage`, `BroadcastChannel`, IndexedDB. Deep-clones with full type fidelity — Date, RegExp, Map, Set, TypedArrays, cycles. Throws on functions, DOM nodes. **Synchronous on the sender — O(n) bytes**, so 100MB stalls main thread ~100ms. For large binaries, use `postMessage(data, [transferList])` to move ownership (zero-copy; sender's ArrayBuffer detached). For continuous sharing, `SharedArrayBuffer` + `Atomics` — both threads see same memory. Browser SAB requires cross-origin isolation headers. Trap: thinking clone is free; postMessage huge data; SAB without Atomics."

---

## 13. 60-second revision

> - **`structuredClone(x)`** = deep clone with type fidelity (Date, Map, Set, cycles).
> - **Synchronous on sender** — O(n) bytes. Large payload stalls main thread.
> - **Throws** on functions, DOM nodes, class prototypes.
> - **Transferables:** `postMessage(data, [transferList])` zero-copy; sender detached.
> - **`SharedArrayBuffer`** + Atomics for shared memory (cross-origin-iso headers in browser).
> - **IndexedDB** uses same algorithm.
> - **Trap:** clone-is-free; copy huge data via postMessage; SAB without Atomics.

---

**Related:** [postmessage-roundtrip.md](./postmessage-roundtrip.md) · [worker-threads-vs-event-loop.md](./worker-threads-vs-event-loop.md) · [`10-machine-coding-patterns/deep-clone-with-cycles.md`](../10-machine-coding-patterns/deep-clone-with-cycles.md) · [atomics-wait-notify-intuition.md](./atomics-wait-notify-intuition.md)

**Concept primer:** [`concepts/event-loop.md`](../../concepts/event-loop.md)
