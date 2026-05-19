# Holey vs packed arrays — V8 element kinds

> **Difficulty:** Senior   |   **Time:** ~10 min   |   **Prereqs:** [polyfill-map.md](./polyfill-map.md), [typed-array-basics.md](./typed-array-basics.md)
>
> **Source:** V8 internals. Mathias Bynens 2017 blog. Cloudflare, Razorpay.

---

## 1. Problem statement

V8 tracks each array's "elements kind." Packed is faster than holey; once holey, never packed again. Avoid creating holes.

**Verification examples**

```js
[1, 2, 3];                              // PACKED_SMI_ELEMENTS
new Array(3);                           // HOLEY_SMI_ELEMENTS (even after fill!)
Array.from({length: 3}, () => 0);       // PACKED_SMI_ELEMENTS

const a = [];
a[3] = 1;                                // HOLEY — sparse index

const b = [1, 2, 3];                    // PACKED_SMI
b.push(1.5);                             // → PACKED_DOUBLE
b.push('x');                             // → PACKED_ELEMENTS (slowest numeric)
```

**Constraints**
- `new Array(N)` creates HOLEY even if filled.
- Transitions are one-way (packed → holey, SMI → double → elements).
- Pre-allocate via `Array.from({length}, () => init)` for PACKED.

---

## 2. Plain-English restatement

V8 specializes array storage by content. Six element kinds form a lattice; transitions are one-way to less-efficient. Performance-sensitive numeric code stays homogeneous and packed.

---

## 3. Why this matters in interviews

V8 internals signal. Senior bar: avoid `new Array(N)`, keep numeric arrays homogeneous, recognize deoptimization.

---

## 4. Mental model

```
   Element kinds (most → least efficient):
   PACKED_SMI         all 31-bit ints       (fastest)
   PACKED_DOUBLE      all doubles
   PACKED_ELEMENTS    mixed
   HOLEY_SMI          ints with holes
   HOLEY_DOUBLE       doubles with holes
   HOLEY_ELEMENTS     mixed with holes      (slowest)
   
   Transitions:
     PACKED_SMI → PACKED_DOUBLE on push(1.5)
     PACKED_SMI → PACKED_ELEMENTS on push('x')
     PACKED_* → HOLEY_* on delete arr[i] or arr[N] = x where N > length
   
   One-way: never goes back.
   
   Why holey slow:
     Iterator must check `i in arr` at each step.
     Accesses fall back to prototype chain lookup.
     `[].constructor.prototype[0]` etc. become live.
   
   Pre-allocate without holes:
     Array.from({length: N}, () => 0)
     Array.from({length: N}, (_, i) => fn(i))
     new Array(N).fill(0)              ← fills BUT initial state was holey
                                          (some engines optimize this; not guaranteed)
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why is `new Array(3)` holey even after filling?
> 2. Can a holey array become packed again?
> 3. What's the fastest way to pre-allocate N zeros?

---

## 6. Brute force — walked through

```js
// Common deopt patterns
const arr = new Array(N);            // HOLEY_SMI
for (let i = 0; i < N; i++) arr[i] = compute(i);
// Even though now fully populated, kind never resets.
```

---

## 7. The unlocking insight

> **Element kinds form one-way lattice. Avoid `new Array(N)`; use `Array.from({length}, init)`. Keep numeric arrays homogeneous.**

Three properties:

1. **One-way transitions** — never go back.
2. **`Array.from({length}, init)`** pre-allocates packed.
3. **Homogeneous types** — all SMI or all double.

---

## 8. Solution (annotated)

```js
// Fast pre-allocation (PACKED_SMI)
function preAllocatePacked(n) {
  return Array.from({ length: n }, () => 0);                              // step 1: PACKED_SMI
}

// Slow pre-allocation (HOLEY_SMI)
function preAllocateHoley(n) {
  const arr = new Array(n);                                                // step 2: HOLEY immediately
  for (let i = 0; i < n; i++) arr[i] = 0;                                  // never recovers
  return arr;
}

// Faster numeric for typed-int arrays
function preAllocateTyped(n) {
  return new Int32Array(n);                                                // step 3: TypedArray
}

// Avoid type mixing
const counters = [];                                                       // PACKED_SMI after first push
function inc() {
  counters.push(0);                                                        // stays PACKED_SMI
}
// vs:
counters.push('initial');                                                  // → PACKED_ELEMENTS (perm)
```

**Try it yourself**

```js
// Benchmark: holey vs packed iteration (roughly 2-5x difference)
function sumPacked(arr) {
  let s = 0;
  for (let i = 0; i < arr.length; i++) s += arr[i];
  return s;
}

const packed = Array.from({ length: 100_000 }, (_, i) => i);
const holey = new Array(100_000);
for (let i = 0; i < 100_000; i++) holey[i] = i;
// Both functionally [0..99999] but holey is measurably slower in V8.

// Avoid delete
const a = [1, 2, 3];
delete a[1];                                                  // → HOLEY_SMI permanently
a.length;                                                      // 3 (still!)
1 in a;                                                        // false (hole)
a;                                                             // [1, <empty>, 3]

// Avoid sparse assignment
const b = [];
b[1000] = 1;                                                  // huge sparse → dictionary mode (slowest)
```

---

## 9. Step-by-step dry run

```
const a = [1, 2, 3]:
  V8: PACKED_SMI_ELEMENTS.
  Element storage: contiguous int slots.

a.push(1.5):
  Transition: PACKED_SMI → PACKED_DOUBLE.
  V8 re-allocates as double array; existing ints stored as doubles.

a.push('x'):
  Transition: PACKED_DOUBLE → PACKED_ELEMENTS.
  Now polymorphic; each access is a tagged-pointer check.

const b = new Array(3):
  V8: HOLEY_SMI_ELEMENTS (immediately holey).
  Slots all uninitialized.

b[0] = 1; b[1] = 2; b[2] = 3:
  All slots filled. STILL HOLEY_SMI.
  Why: V8 doesn't auto-recover; would need to scan.

delete b[1]:
  HOLEY_SMI (already holey).
  Access pattern: `i in b` returns false at 1.

Holey iteration cost:
  for (let i = 0; i < arr.length; i++) ...
  V8 emits prototype-walk fallback for holes.
  Prototype walk is expensive.
```

---

## 10. Common confusion + traps

1. **`new Array(N)` then fill** — still holey.
2. **`delete arr[i]`** — creates hole; never recovers.
3. **`arr.length = N`** larger than current — creates holes.
4. **Sparse assignment** `arr[10000] = 1` on small — dictionary mode.
5. **Mix ints and doubles** — PACKED_DOUBLE; OK for numerics, slower than SMI.
6. **Mix numerics and objects** — PACKED_ELEMENTS; slowest for math.
7. **Performance assumptions** — measure; differences often small.

---

## 11. Senior follow-ups & variants

### Variant 1 — Dictionary mode
Very sparse arrays become hash maps. Detected by `arr.length` vs actual element count.

### Variant 2 — TypedArrays
`Int32Array` etc. — fixed type; contiguous; no holes possible.

### Variant 3 — `Array.from(length, mapper)`
Built-in packed pre-allocation.

### Variant 4 — Engine differences
SpiderMonkey, JSC have similar but not identical optimizations.

### Variant 5 — `--allow-natives-syntax`
V8 debug flag exposes `%DebugPrint(arr)` to inspect element kind.

---

## 12. How to think aloud

> "V8 tracks 'elements kinds' per array: PACKED_SMI (all small ints), PACKED_DOUBLE (all doubles), PACKED_ELEMENTS (mixed), and HOLEY_* variants. They form a one-way lattice — transitions go to less-efficient kinds and never back. `new Array(N)` creates HOLEY_SMI immediately, even if you fill every slot, because V8 doesn't scan to detect re-packing. `delete arr[i]` creates a hole that's permanent. Sparse assignment `arr[10000]=1` can transition to dictionary mode (hash map storage — slowest). For perf-sensitive code: pre-allocate via `Array.from({length: N}, () => init)` to get PACKED; keep numeric arrays homogeneous (all SMI or all double); avoid pushing strings into numeric arrays. For real numeric work, TypedArrays (`Int32Array`, `Float64Array`) — contiguous, fixed type, no holes possible, often 2-5× faster. Holey iteration cost: V8 checks `i in arr` per step, walks the prototype chain on holes. Measure with `--allow-natives-syntax` + `%DebugPrint(arr)`. Trap: `new Array(N)` then fill (still holey); delete (permanent); sparse assignment (dictionary mode); assuming kind transitions reverse."

---

## 13. 60-second revision

> - **Element kinds:** PACKED_SMI > PACKED_DOUBLE > PACKED_ELEMENTS > HOLEY variants.
> - **One-way transitions** — never reverse.
> - **`new Array(N)`** = HOLEY (perm).
> - **`Array.from({length}, init)`** = PACKED.
> - **`delete arr[i]`** → HOLEY (perm).
> - **Sparse assignment** → dictionary mode (slowest).
> - **Homogeneous types** — all SMI or all double.
> - **TypedArrays** for serious numeric.
> - **Measure with `%DebugPrint`** (`--allow-natives-syntax`).
> - **Trap:** `new Array(N)`; delete; mix types.

---

**Related:** [typed-array-basics.md](./typed-array-basics.md) · [polyfill-map.md](./polyfill-map.md) · [polyfill-flat.md](./polyfill-flat.md)

**Concept primer:** [`concepts/arrays.md`](../../concepts/arrays.md)
