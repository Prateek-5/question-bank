# TypedArray Basics

## Source / Origin
- ES2015 `Int8Array`, `Uint8Array`, `Int32Array`, etc. + `ArrayBuffer`.
- Asked at: Cloudflare, Razorpay, AWS — perf-focused roles.
- Concept reference: `concepts/arrays.md`.

## Why this question matters in interviews
Regular `Array` is a generic, heap-allocated, polymorphic container — slow for numeric work. `TypedArray` wraps a contiguous `ArrayBuffer` of bytes typed as a specific numeric type. Senior bar: you can list the 11 typed-array types, know the byte boundary (Uint8Array is byte-aligned, Int32 is 4-byte-aligned), and understand views (multiple typed-array views over one buffer).

## Concepts involved

### Syntax to lock in
```js
// Backing buffer
const buf = new ArrayBuffer(16);            // 16 bytes
const i32 = new Int32Array(buf);            // 4 elements (16/4)
i32[0] = 0x12345678;
const u8 = new Uint8Array(buf);             // 16 elements (same memory!)
u8[0]; u8[1]; u8[2]; u8[3];                  // 0x78 0x56 0x34 0x12 (little-endian)

// Without explicit buffer
const arr = new Int32Array(1024);            // also allocates 4 KB buffer
arr.length;                                  // 1024
arr.byteLength;                              // 4096
arr.buffer instanceof ArrayBuffer;           // true
```

### The 11 typed-array types
| Type | Bytes/elem | Range |
|---|---|---|
| `Int8Array` | 1 | -128..127 |
| `Uint8Array` | 1 | 0..255 |
| `Uint8ClampedArray` | 1 | 0..255 (clamped, not wrapped) |
| `Int16Array` | 2 | -32768..32767 |
| `Uint16Array` | 2 | 0..65535 |
| `Int32Array` | 4 | -2^31..2^31-1 |
| `Uint32Array` | 4 | 0..2^32-1 |
| `Float32Array` | 4 | IEEE 754 single |
| `Float64Array` | 8 | IEEE 754 double |
| `BigInt64Array` | 8 | -2^63..2^63-1 |
| `BigUint64Array` | 8 | 0..2^64-1 |

### Edge cases / traps
1. **No `.push`/`.pop`.** Fixed size. Use `.set()` or create new.
2. **Out-of-range writes silently wrap (or clamp for Uint8ClampedArray).** `u8[0] = 300` → `44`; `u8c[0] = 300` → `255`.
3. **Endianness**: typed-array views use host byte order. For network/file IO use `DataView` which lets you specify.
4. **`Uint8ClampedArray`** rounds floats to integers (for canvas image data).
5. **Shared buffer**: multiple views over one ArrayBuffer alias the same memory.
6. **`SharedArrayBuffer`** for cross-worker; requires `Atomics` for safe writes.
7. **Garbage collection**: views keep the buffer alive; orphaning a buffer doesn't release memory if any view exists.
8. **`subarray` vs `slice`** — `subarray` is a view over the same buffer (no copy); `slice` is a copy.
9. **Iteration**: typed arrays are iterable; `for..of` works.
10. **`Array.from(typedArr)`** copies to regular Array.

## Mental Model

```
   ArrayBuffer (16 bytes):
   ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐
   │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │  │
   └──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘
      0  1  2  3  4  5  6  7  8  9 ...

   Int32Array view:  [w0]   [w1]   [w2]   [w3]
                     0..3   4..7   8..11  12..15

   Uint8Array view:  [b0 b1 b2 b3 b4 b5 b6 b7 b8 b9 b10 b11 b12 b13 b14 b15]
                     same buffer, different lens
```

## Why interviewers care

- **Memory awareness** — heap vs typed.
- **Binary protocols** — file formats, network, WebGL.
- **Perf intuition** — typed arrays are 5-10× faster for numeric loops.

## Common confusion

- **"`Array` and `Int32Array` are interchangeable."** Typed arrays don't have `.push`, mutate via index, fixed size, numeric-only.
- **"Endian doesn't matter in JS."** Within one process, no. Across machines, yes — use DataView.
- **"`subarray` makes a copy."** It doesn't — view over same buffer.
- **"`Uint8Array` is bytes; `Buffer` is the same."** Node's `Buffer` extends `Uint8Array` but has more methods and historic baggage.

## Brute force

```js
const arr = new Array(1024).fill(0);
for (let i = 0; i < 1024; i++) arr[i] = i;
// works, but each element is a JS Number wrapper (typed nan-box / SMI / heapnumber)
```

`Int32Array` for the same task: 4× less memory, ~5-10× faster numeric loop.

## Optimal approach

For numeric work or binary IO: pick the typed array type that fits the data; use `DataView` for endian-explicit access.

## Solution

```js
// 1. Numeric loop
const samples = new Float32Array(48000);     // 1 second of audio @ 48kHz
for (let i = 0; i < samples.length; i++) samples[i] = Math.sin(i * 0.01);

// 2. Binary protocol with DataView (endian explicit)
const buf = new ArrayBuffer(8);
const view = new DataView(buf);
view.setUint32(0, 0xDEADBEEF, false);        // big-endian
view.getUint8(0);                            // 0xDE

// 3. Aliasing for type punning
function floatToBits(x) {
  const buf = new ArrayBuffer(4);
  new Float32Array(buf)[0] = x;
  return new Uint32Array(buf)[0];
}
floatToBits(1.0);                            // 1065353216 (IEEE 754 single representation)

// 4. Zero-copy transfer to worker
const data = new Uint8Array(1024 * 1024 * 10);   // 10 MB
worker.postMessage(data.buffer, [data.buffer]);   // transferable; sender loses access
data.byteLength;                                  // 0 after transfer

// 5. Subarray vs slice
const big = new Int32Array(100);
const sub = big.subarray(0, 10);                  // view (shares memory)
const cpy = big.slice(0, 10);                     // copy (own buffer)
sub[0] = 99; big[0];                              // 99 (shared)
cpy[0] = 77; big[0];                              // 99 (independent)

// 6. Wrap vs clamp
const u8 = new Uint8Array(1);
u8[0] = 300; u8[0];                               // 44 (wrap, 300 % 256)
const u8c = new Uint8ClampedArray(1);
u8c[0] = 300; u8c[0];                             // 255 (clamp)
```

## Dry run

```
const buf = new ArrayBuffer(8);     // 8 bytes, all zero
const u8  = new Uint8Array(buf);
const u32 = new Uint32Array(buf);   // 2 elements

u8[0] = 0xFF;  // buf: [FF 00 00 00 00 00 00 00]
u32[0];        // 0x000000FF on little-endian, 0xFF000000 on big-endian
                // (V8 is little-endian on common architectures)

u32[1] = 0xDEADBEEF;
u8[4..7];       // [EF BE AD DE] (little-endian)
```

## How to think aloud

> "TypedArray is a view over an ArrayBuffer with a specific numeric type. Fixed size, no push/pop, numeric only. Faster than Array for numeric loops because elements are unboxed contiguous memory. Multiple views can overlay the same buffer for type punning. DataView lets you specify endian — use for binary protocols and file formats. Uint8ClampedArray clamps, others wrap. For zero-copy across workers, transfer the underlying buffer."

## Important takeaways

- **11 types**: Int/Uint 8/16/32, Float 32/64, BigInt 64.
- **Fixed size, numeric only.**
- **Views over ArrayBuffer**; multiple views alias same memory.
- **`subarray` is a view; `slice` copies.**
- **DataView for endian-explicit IO.**
- **`Uint8ClampedArray` clamps; others wrap.**
- **Transferables for cross-worker zero-copy.**

## Variants

- **`SharedArrayBuffer`** + Atomics — cross-worker shared memory.
- **`DataView`** — endian-explicit, byte-granular access.
- **Node `Buffer`** — extends Uint8Array, has additional methods (`writeUInt32BE`, etc.).
- **WebGL/WebAssembly memory** — directly typed-array backed.
- **`SharedArrayBuffer` + COOP/COEP** — browsers require headers.

## Revision notes

```
typed arrays:
  Int8/Uint8/Uint8Clamped, Int16/Uint16, Int32/Uint32, Float32/Float64, BigInt64/BigUint64
  view over ArrayBuffer; fixed size; numeric only

ArrayBuffer:
  raw bytes; multiple views alias same memory

DataView:
  endian-explicit access (getUint32(off, littleEndian))

subarray vs slice:
  subarray → view (shares buffer)
  slice    → copy (new buffer)

clamp vs wrap:
  Uint8ClampedArray → 300 → 255
  other Uint        → 300 → wrap

USES:
  numeric loops (5-10× faster)
  binary protocols (DataView)
  WebGL/WebAssembly
  zero-copy worker transfer (postMessage transferable)
  type punning (alias buffer with different views)

NOT FOR: heterogeneous data, dynamic-size lists, non-numeric
```
