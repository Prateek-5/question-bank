# Holey vs Packed Arrays (V8 Element Kinds)

## Source / Origin
- V8 internals; "Elements Kinds in V8" Mathias Bynens blog (2017).
- Asked at: Cloudflare, Razorpay, Atlassian, V8-curious shops.
- Concept reference: `concepts/arrays.md`.

## Why this question matters in interviews
V8 tracks each array's "elements kind" — `PACKED_SMI`, `PACKED_DOUBLE`, `PACKED_ELEMENTS`, `HOLEY_SMI`, `HOLEY_DOUBLE`, `HOLEY_ELEMENTS`. Packed is faster than holey. Once an array transitions to holey, it never goes back. Senior bar: you avoid creating holes (`new Array(N)` is the canonical sin), keep numeric arrays homogeneous (all small ints or all doubles), and recognize the deoptimization patterns.

## Concepts involved

### Syntax to lock in
```js
// Creates packed SMI array
const a = [1, 2, 3];       // PACKED_SMI

// Creates HOLEY — even though all slots get filled, the initial state is holey
const b = new Array(3);    // HOLEY_SMI
b[0] = 1; b[1] = 2; b[2] = 3;   // still HOLEY_SMI; transition is permanent

// Skip an index → creates hole
const c = [];
c[3] = 1;                  // HOLEY_SMI
c.length;                  // 4

// Pre-allocate as packed
const d = Array.from({ length: 3 }, () => 0);   // PACKED_SMI

// Mix types → transitions to less efficient kind
const e = [1, 2, 3];       // PACKED_SMI
e.push(1.5);                // PACKED_DOUBLE (now)
e.push('x');                // PACKED_ELEMENTS (worst for numerics)
```

### Element kinds (most → least efficient)
| Kind | Description |
|---|---|
| `PACKED_SMI_ELEMENTS` | All slots = small ints (31-bit) |
| `PACKED_DOUBLE_ELEMENTS` | All slots = doubles |
| `PACKED_ELEMENTS` | Mixed types (objects, strings, etc.) |
| `HOLEY_SMI_ELEMENTS` | SMIs but with holes |
| `HOLEY_DOUBLE_ELEMENTS` | Doubles but with holes |
| `HOLEY_ELEMENTS` | Mixed + holes |

Once an array transitions, it doesn't go back. Holey → holey forever.

### Edge cases / traps
1. **`new Array(N)`** allocates *holes*, even if you fill them right after.
2. **`Array.from({length:N}, ...)`** creates packed (calls map fn so no actual hole).
3. **Sparse from gap**: `a[1000] = 1` on a short array → holes 0-999.
4. **`delete arr[i]`** creates a hole.
5. **Length increase via assignment**: `arr.length = 5` from length 0 — holes.
6. **`Array.prototype.fill(0)`** doesn't fill holes — they remain.
7. **Mixed types** — adding a string to a numeric array transitions to `PACKED_ELEMENTS`.
8. **Mixed SMI + double** transitions through `PACKED_DOUBLE`.
9. **Sorted** — `Array.prototype.sort` does not preserve element-kind optimization in all V8 versions.
10. **DevTools shows kind** — Chrome DevTools shows element kind under "memory" or via `%DebugPrint(arr)` with `--allow-natives-syntax` flag.

## Mental Model

```
   PACKED_SMI:  [1, 2, 3, 4, 5]
                ↓ push 1.5
   PACKED_DOUBLE: [1.0, 2.0, 3.0, 4.0, 5.0, 1.5]
                ↓ push 'x'
   PACKED_ELEMENTS: [1, 2, 3, 4, 5, 1.5, 'x']
                ↓ delete arr[2]
   HOLEY_ELEMENTS:  [1, 2, _, 4, 5, 1.5, 'x']

   transitions are ONE-WAY:
     packed → holey: never back
     SMI → double: never back
     anything → ELEMENTS: never back
```

## Why interviewers care

- **V8 perf intuition** — separates senior from mid.
- **Hot-loop optimization** — element kind affects unboxing.
- **Pattern recognition** — recognizing the `new Array(N)` antipattern.

## Common confusion

- **"`new Array(N)` is fine because I fill it."** It creates holes immediately, transitions to holey, never goes back.
- **"`delete arr[i]` removes the element."** Creates a hole; length unchanged.
- **"Mixed types are fine."** True in correctness; bad for perf if array is hot.
- **"`forEach`, `map`, etc. don't care about holes."** They skip holes (don't call callback) — subtly wrong if you wanted to fill them.

## Brute force / naive

```js
const arr = new Array(1000);          // HOLEY_SMI immediately
for (let i = 0; i < 1000; i++) arr[i] = i;   // still HOLEY (transition permanent)
```

## Optimal

```js
// Packed alternatives
const arr = Array.from({ length: 1000 }, (_, i) => i);    // PACKED_SMI
// or
const arr = [];
for (let i = 0; i < 1000; i++) arr.push(i);               // PACKED_SMI

// Typed array — even faster for numerics
const arr = new Int32Array(1000);
for (let i = 0; i < 1000; i++) arr[i] = i;
```

## Solution

```js
// Anti-pattern → fix table
//   const arr = new Array(N);             → Array.from({length: N}, () => 0) OR []
//   arr[100] = 1; arr.length=0..99 holes  → fill explicit 0s, or push
//   delete arr[i]                          → arr.splice(i, 1)
//   push 1, then 1.5                      → keep homogeneous types
//   mix numbers + strings                  → use separate arrays or objects

// Inspect element kind (Chrome with --allow-natives-syntax)
// %DebugPrint(arr) prints kind info
%DebugPrint([1,2,3]);                   // PACKED_SMI_ELEMENTS

// Hot loop benchmark
function sumPacked() {
  const arr = Array.from({ length: 1e6 }, (_, i) => i);
  let s = 0;
  for (let i = 0; i < arr.length; i++) s += arr[i];
  return s;
}
function sumHoley() {
  const arr = new Array(1e6);
  for (let i = 0; i < 1e6; i++) arr[i] = i;     // still HOLEY_SMI
  let s = 0;
  for (let i = 0; i < arr.length; i++) s += arr[i];
  return s;
}
// sumPacked is typically 20-50% faster
```

## Dry run

```js
const a = [];                 // PACKED_SMI (empty packed)
a.push(1);                    // PACKED_SMI
a.push(2.5);                  // PACKED_DOUBLE (SMI → DOUBLE)
a.push('hello');              // PACKED_ELEMENTS (DOUBLE → ELEMENTS)
delete a[1];                  // HOLEY_ELEMENTS (delete makes hole)
```

```js
const b = new Array(3);       // HOLEY_SMI
b[0] = 1; b[1] = 2; b[2] = 3; // STILL HOLEY_SMI — the alloc state is sticky
```

## How to think aloud

> "V8 tracks element kind per array. Packed > holey; SMI > double > elements. Transitions are one-way. Anti-patterns: `new Array(N)` (holey at birth), `delete arr[i]` (creates hole), mixing types (transitions kind). Prefer `Array.from({length:N}, fn)` for pre-allocation, `splice` instead of `delete`, separate arrays per type. For numeric hot loops, typed arrays bypass this entirely. Inspect via `%DebugPrint` with --allow-natives-syntax."

## Important takeaways

- **6 element kinds**: PACKED/HOLEY × SMI/DOUBLE/ELEMENTS.
- **Transitions are one-way.**
- **Anti-patterns**: `new Array(N)`, `delete arr[i]`, mixing types.
- **Prefer `Array.from({length:N}, fn)`**, `splice`, homogeneous types.
- **TypedArrays bypass** the issue entirely for numerics.
- **Inspect via `%DebugPrint`** with --allow-natives-syntax.

## Variants

- **`Float64Array` / `Int32Array`** for numeric work.
- **Pre-sized objects** instead of pre-sized arrays for sparse data.
- **`Map` for sparse keyed data** instead of large holey array.
- **Multiple arrays** instead of one mixed-type array.

## Revision notes

```
Element Kinds (most → least efficient):
  PACKED_SMI > PACKED_DOUBLE > PACKED_ELEMENTS > HOLEY_SMI > HOLEY_DOUBLE > HOLEY_ELEMENTS

ONE-WAY transitions; never reverse

ANTI-PATTERNS:
  new Array(N)              → HOLEY_SMI at birth
  arr[1000] = 1 (sparse)    → HOLEY
  delete arr[i]              → HOLEY
  arr.push(1.5) then 'x'    → SMI → DOUBLE → ELEMENTS

FIXES:
  Array.from({length:N}, () => 0)    → PACKED
  [].push() in loop                  → PACKED
  splice instead of delete           → no hole
  homogeneous types                  → keep SMI/DOUBLE
  TypedArray for numerics            → bypass element kinds

INSPECT:
  node/d8 --allow-natives-syntax → %DebugPrint(arr)
```
