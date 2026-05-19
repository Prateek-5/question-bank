# TypedArray basics

> **Difficulty:** Senior   |   **Time:** ~10 min   |   **Prereqs:** [holey-vs-packed-arrays.md](./holey-vs-packed-arrays.md)
>
> **Source:** ES2015. Cloudflare, Razorpay, AWS — perf-focused roles.

---

## 1. Problem statement

`ArrayBuffer` + TypedArray views. Why fixed-type contiguous storage beats `Array` for numeric work. Views over shared buffer.

**Verification examples**

```js
const buf = new ArrayBuffer(16);
const i32 = new Int32Array(buf);                  // 4 elems × 4 bytes
i32[0] = 0x12345678;
const u8 = new Uint8Array(buf);                   // 16 elems × 1 byte (same memory)
u8[0]; u8[1]; u8[2]; u8[3];                       // 0x78 0x56 0x34 0x12 (little-endian)

// Without explicit buffer
const arr = new Int32Array(1024);
arr.byteLength;                                    // 4096
arr.buffer instanceof ArrayBuffer;                 // true
```

**Constraints**
- 11 TypedArray types; differ in element size and signedness.
- Multiple views over same buffer share memory.
- Default endianness is little (platform).
- TypedArray sort is NUMERIC by default (vs Array.sort lex default).
- No holes possible — always packed.

---

## 2. Plain-English restatement

`ArrayBuffer` is raw bytes. TypedArray (Int32Array, Float32Array, etc.) is a typed view over those bytes — contiguous, fixed type, fast numeric ops.

---

## 3. Why this matters in interviews

Generic `Array` is heap-allocated, polymorphic, slow for numerics. TypedArray is contiguous, fixed-type, much faster — and the underlying primitive for WebGL, audio, crypto, networking.

---

## 4. Mental model

```
   ArrayBuffer:  raw bytes; no methods to read/write directly.
   TypedArray:   typed view over an ArrayBuffer.
   DataView:     manual endian + offset control over an ArrayBuffer.
   
   11 TypedArray types:
   Int8Array      1 byte   -128..127
   Uint8Array     1 byte   0..255
   Uint8ClampedArray 1 byte 0..255 (clamps overflow; for canvas)
   Int16Array     2 byte   -32k..32k
   Uint16Array    2 byte   0..65k
   Int32Array     4 byte   ±2^31
   Uint32Array    4 byte   0..2^32
   Float32Array   4 byte   IEEE single
   Float64Array   8 byte   IEEE double
   BigInt64Array  8 byte   ±2^63 (BigInt-backed)
   BigUint64Array 8 byte   0..2^64
   
   Views over same buffer share memory:
     const buf = new ArrayBuffer(8);
     new Int32Array(buf)[0] = 1;
     new Uint8Array(buf)[0]; // 0x01 (little endian byte 0)
   
   Endianness:
     TypedArrays use PLATFORM endianness (almost always little).
     DataView lets you specify per read/write.
   
   Differences from Array:
     fixed length (cannot push/splice).
     fixed type (writes coerce, not throw).
     numeric default sort.
     no holes.
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Can you push to a TypedArray?
> 2. What does `int32[0] = 1.5` do?
> 3. Why use `DataView` instead of TypedArray?

---

## 6. Brute force — walked through

```js
// Generic Array for byte work — slow
const bytes = [];
for (let i = 0; i < 1_000_000; i++) bytes.push(0);
```

Polymorphic Array; slow numerics. Use `new Uint8Array(1_000_000)`.

---

## 7. The unlocking insight

> **TypedArray = ArrayBuffer + typed view. Fixed length, fixed type, contiguous. Multiple views over one buffer share memory.**

Three properties:

1. **`ArrayBuffer`** raw bytes.
2. **TypedArray view** — typed access.
3. **Multiple views** share memory.

---

## 8. Solution (annotated)

```js
// Allocation
const buf = new ArrayBuffer(16);                                          // step 1: 16 bytes raw
const i32 = new Int32Array(buf);                                           // step 2: view as 4 int32
i32[0] = 0x12345678;

const u8 = new Uint8Array(buf);                                            // step 3: same memory, byte view
console.log(u8[0]);                                                        // 0x78 (little-endian)
console.log(u8[1]);                                                        // 0x56

// Type coercion on write (no throw)
i32[0] = 1.7;                                                              // truncates to 1
i32[0] = '5';                                                              // coerces to 5
i32[0] = NaN;                                                              // 0 (int)
new Uint8Array(1)[0] = 300;                                                // 300 % 256 = 44 (wraps)
new Uint8ClampedArray(1)[0] = 300;                                         // 255 (clamps)

// Implicit buffer allocation
const arr = new Int32Array(1024);                                          // step 4: buffer auto-allocated
arr.length;                                                                // 1024
arr.byteLength;                                                            // 4096

// Slicing & views
const slice = arr.subarray(100, 200);                                      // step 5: view, shares buffer
slice[0] = 99;
arr[100];                                                                  // 99 — shared

const copy = arr.slice(100, 200);                                          // step 6: copy
copy[0] = 88;
arr[100];                                                                  // 99 — independent

// DataView for endian control
const dv = new DataView(buf);
dv.setUint32(0, 0x12345678, /* littleEndian */ true);                      // step 7: explicit endian
dv.getUint32(0, false);                                                    // read as big-endian
```

**Try it yourself**

```js
// Read a binary file (Node)
const fs = require('node:fs');
const buffer = fs.readFileSync('image.bin');                              // Node Buffer
const view = new DataView(buffer.buffer, buffer.byteOffset, buffer.byteLength);
const width = view.getUint32(0, true);
const height = view.getUint32(4, true);

// Float32 audio sample
const audio = new Float32Array(44100);   // 1 sec @ 44.1kHz
for (let i = 0; i < 44100; i++) {
  audio[i] = Math.sin(2 * Math.PI * 440 * i / 44100);  // 440Hz tone
}

// Cross-thread transfer (zero-copy)
const big = new Float32Array(1_000_000);
worker.postMessage(big, [big.buffer]);    // ownership transferred; original now empty

// Sort is numeric by default
new Int32Array([10, 1, 5]).sort();        // [1, 5, 10]  — vs Array [1, 10, 5]

// Sum vs Array (typed arrays often 2-5x faster on V8)
function sumTyped(arr) {
  let s = 0;
  for (let i = 0; i < arr.length; i++) s += arr[i];
  return s;
}
```

---

## 9. Step-by-step dry run

```
const buf = new ArrayBuffer(8);
const i32 = new Int32Array(buf);     // 2 elems
const u8 = new Uint8Array(buf);      // 8 elems
i32[0] = 0x12345678;

Memory layout (little-endian):
  byte 0: 0x78  ← LSB
  byte 1: 0x56
  byte 2: 0x34
  byte 3: 0x12  ← MSB
  byte 4-7: 0  (unused)

u8[0] = 0x78. u8[1] = 0x56. u8[2] = 0x34. u8[3] = 0x12.

Modify via u8:
  u8[0] = 0xFF.
  i32[0] = ?  Now bytes 0xFF 0x56 0x34 0x12 = 0x123456FF.

DataView for big-endian:
  dv.setInt32(0, 0x12345678, false);   // big-endian
  Memory: 0x12 0x34 0x56 0x78.
  i32[0] (little) reads bytes as 0x78563412.

Type coercion writes:
  Int32 [0] = 1.5 → 1 (truncate).
  Uint8 [0] = 300 → 44 (wrap mod 256).
  Uint8Clamped [0] = 300 → 255 (saturate).
```

---

## 10. Common confusion + traps

1. **`push` / `pop`** — not available on TypedArray (fixed length).
2. **Float assigned to Int** — truncates silently.
3. **Overflow** — wraps for Uint (mod 256), clamps for Uint8Clamped.
4. **Endianness** — TypedArray uses platform (little); DataView is explicit.
5. **`slice` vs `subarray`** — slice copies; subarray shares buffer.
6. **Sort is numeric** by default (different from Array).
7. **No holes possible** — assignment to large index throws RangeError if beyond length.

---

## 11. Senior follow-ups & variants

### Variant 1 — `DataView` for explicit endian
Required for network protocols, file formats.

### Variant 2 — `SharedArrayBuffer`
Across workers; needs Atomics for safety.

### Variant 3 — Zero-copy transfer
`postMessage(typed, [typed.buffer])`.

### Variant 4 — WebGL / WebGPU
TypedArrays are the buffer format.

### Variant 5 — Node Buffer
Subclass of Uint8Array; same memory model + extra methods.

---

## 12. How to think aloud

> "TypedArrays are typed views over `ArrayBuffer` (raw bytes). 11 types: Int8/16/32, Uint8/16/32, Uint8Clamped, Float32/64, BigInt64/Uint64. Each has fixed element size — Int32Array elements are 4 bytes. Multiple views over the same buffer share memory: `new Int32Array(buf)[0] = 1; new Uint8Array(buf)[0]` reads byte 0 (0x01 little-endian). Differences from Array: fixed length (no push/pop), fixed type (writes coerce silently — 1.5 → 1, 300 → 44 for Uint8 via wrap, 255 for Uint8Clamped via saturation), no holes possible, numeric default sort (`[10,1,5].sort()` → `[1,5,10]` — different from Array's lex default). Performance: contiguous memory, no polymorphism, 2-5× faster numeric loops in V8. Endianness: TypedArrays use platform (almost always little-endian); for explicit control (network protocols, file formats) use `DataView` which takes endian parameter per read/write. `subarray` returns view sharing buffer; `slice` copies. Zero-copy cross-thread: `postMessage(typed, [typed.buffer])` transfers ownership; original empty after. Use cases: binary protocols, WebGL buffers, audio samples, crypto, file parsers, Node Buffer."

---

## 13. 60-second revision

> - **`ArrayBuffer`** = raw bytes; TypedArray = typed view.
> - **11 types** — Int8/16/32, Uint, Float32/64, BigInt64.
> - **Fixed length + type** — no push, coerces writes.
> - **Multiple views** share buffer.
> - **`subarray` shares, `slice` copies.**
> - **Numeric sort default** (not lex).
> - **Endianness:** TypedArray = platform; DataView = explicit.
> - **Zero-copy transfer** via `postMessage` + transferList.
> - **Trap:** assume push; truncation on Int; overflow wrap vs clamp.

---

**Related:** [holey-vs-packed-arrays.md](./holey-vs-packed-arrays.md) · [`05-event-loop/structured-clone-cost.md`](../05-event-loop/structured-clone-cost.md) · [`06-streams/web-streams-readable.md`](../06-streams/web-streams-readable.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
