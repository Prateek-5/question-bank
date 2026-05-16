# Arrays

## Intuition first: what *is* a JS array, really?

> **Mental Model:** A JavaScript array is an **object that has been given superpowers for integer-keyed data**. It still behaves like an object (you can attach random properties, it has a prototype, it inherits methods), but the engine secretly recognizes "this object only has integer keys" and switches it onto a fast track — a contiguous chunk of memory, accessed by index in O(1). The moment you do something un-array-like (assign a non-integer key, leave gaps), the engine demotes you to a slower track.

If you've used C arrays, JS arrays will feel weird: they grow, they shrink, they can hold mixed types, they're not really arrays in the classical sense — they're hashmaps that *look* like arrays. The engine works hard to make them feel fast by detecting common shapes. Your job as a senior dev is to write code that lets the engine keep you on the fast path.

**Why does this concept exist with so many methods?** Because arrays are *the* primary data structure in JS — every API response, every database row set, every form submission turns into an array somewhere. Over 25 years, the language has accumulated 40+ array methods, in three eras: pre-ES5 (`push`, `slice`, `sort`), ES5 functional (`map`, `filter`, `reduce`), and modern (`flat`, `findLast`, `toSorted`, `groupBy`). An interview tests whether you reach for the *right* one without thinking.

### First-principles definition

> An array is a special object whose integer keys (`0, 1, 2, ...`) are stored in a packed buffer, and whose `length` property auto-updates as you assign or remove those keys. Everything else — `push`, `map`, `sort` — is built on top of "set/get the integer-indexed slot."

### Progressive examples — start trivial, end production-realistic

```js
// 1) Tiniest array — just data
const nums = [1, 2, 3];
nums[0];           // 1
nums.length;       // 3

// 2) Intermediate — transform without mutation
const doubled = nums.map(x => x * 2);   // [2, 4, 6]
nums;                                   // still [1, 2, 3]

// 3) Advanced — interview classic, group and aggregate
const records = [
  { region: "us", sales: 10 },
  { region: "eu", sales: 7 },
  { region: "us", sales: 5 },
];
const totals = records.reduce((acc, r) => {
  acc[r.region] = (acc[r.region] || 0) + r.sales;
  return acc;
}, {}); // { us: 15, eu: 7 }

// 4) Production-realistic — guarding against the shared-mutable bug
function getUsersCopy(cache) {
  return [...cache.users];  // shallow copy so caller can't mutate cache
}
```

If you can read all four examples and predict their output AND explain *why example 4 uses spread*, you're at interview-ready depth.

## Mental Model

> Imagine a row of numbered cubbies in a wall. Cubby 0, cubby 1, cubby 2, … and a sign at the end saying "length: 3." When you `push(4)`, the wall extends by one cubby and the sign becomes "length: 4." When you `pop()`, the last cubby is emptied and the sign decreases. When you do `arr[100] = 'x'`, the wall stretches to 101 cubbies with empty (hole) slots between — and the engine quietly demotes your array from "packed wall" to "sparse wall with index card lookup," which is much slower.

Every array operation is a story about cubbies. Mutating methods rearrange the cubbies of `this`. Non-mutating methods build a brand-new wall.

### Memory layout — packed vs holey

```
PACKED (fast path)               HOLEY (slow path)
┌──┬──┬──┬──┬──┐                 ┌──┬──┬  ┬  ┬──┐
│ 1│ 2│ 3│ 4│ 5│                 │ 1│  │  │  │ 5│   ← gaps
└──┴──┴──┴──┴──┘                 └──┴──┴──┴──┴──┘
length: 5                        length: 5
contiguous in memory             engine reads via hashmap-like lookup
SMI element kind (small ints)    once holey, often stays holey
```

Once an array goes holey, V8 doesn't transition it back automatically. So *avoid creating holes in hot paths.*

## Why interviewers care

Almost every machine-coding round is some flavor of "transform this array into that array." Interviewers want to see:

1. **Method fluency** — do you reach for `.reduce` vs writing a manual loop? Do you know `.flat` exists?
2. **Mutating vs non-mutating awareness** — will your code silently corrupt a shared cache?
3. **Big-O reflexes** — do you know `shift` is O(n) and `push` is O(1)?
4. **The default-`.sort()` trap** — a quick sanity check that you've actually used JS, not just read about it.
5. **Idiomatic dedup/group/chunk** — bread and butter of backend work.

If you can ship clean, non-mutating, correctly-sorted, O(n) array transforms without thinking, you'll outperform 80% of candidates.

## Common beginner confusion

- "`[10, 1, 2].sort()` gave me `[1, 10, 2]` — is JS broken?" → No, `.sort()` stringifies by default. Always pass `(a, b) => a - b` for numbers.
- "Why doesn't `.forEach` let me `return` early?" → Because `forEach` is a function call per element; `return` only returns from the callback. Use `for...of` with `break`, or `some`/`every`.
- "I did `const a = b; a.push(1);` — why did `b` change?" → Because `a` and `b` are the same array. `const` only locks the binding, not the contents. Use `[...b]` to copy.
- "I tried `new Array(3).map(...)` and nothing happened." → `new Array(3)` creates three *holes*, not three undefineds, and `.map` skips holes. Use `Array.from({length:3}, (_, i) => i)` instead.
- "`reduce` is hard." → It's just a loop with one accumulator. If you can write the `for` loop equivalent, you can write the reduce.

## TL;DR
- JS arrays are **specialized objects** with integer keys + a `length`. V8 backs them with packed (`PACKED_SMI_ELEMENTS`), holey, or dictionary modes depending on use.
- **Mutating** methods change `this` in place (`push/pop/shift/unshift/splice/sort/reverse/fill/copyWithin`). **Non-mutating** return a new array (`map/filter/slice/concat/flat/flatMap`, ES2023 `toSorted/toReversed/toSpliced/with`).
- **`.sort()` stringifies by default** — `[10,2,1].sort()` → `[1, 10, 2]`. Always pass a comparator.
- **Sparse arrays** (holes) are slow and confusing — `[, , ,].length === 3`. Most methods skip holes; some don't.
- Big-O on common ops: `push/pop` O(1), `shift/unshift` O(n), `find/indexOf` O(n), `slice` O(k).

## Why backend interviewers care
- Almost every machine-coding round involves arrays — transforming records, grouping, dedup, top-K, reducers.
- Knowing mutating vs non-mutating prevents subtle bugs in API handlers (returning state someone else now mutates).
- Reduce/map/filter chains are the lingua franca of ETL and aggregation code.

## Core mental model

> **Bridge:** Now that you can picture cubbies and packed/holey walls, the V8 element-kind story below is just the engine's bookkeeping for the same idea.

V8 picks an element kind per array based on contents:
- `PACKED_SMI_ELEMENTS` — small ints only, no holes (fastest).
- `PACKED_DOUBLE_ELEMENTS` — numbers including floats, no holes.
- `PACKED_ELEMENTS` — anything, no holes.
- `HOLEY_*` variants — has holes (sparse).
- Beyond ~32MB or with non-int keys, it falls back to **dictionary mode** (hashmap-backed), much slower.

### Element-kind transition diagram

```
                    fastest ──────────────────── slowest
                       │                              │
   PACKED_SMI ──► PACKED_DOUBLE ──► PACKED ──► HOLEY_* ──► DICTIONARY
   (small ints)   (with floats)    (anything)  (with gaps) (hashmap)

   Transitions are ONE-WAY.
   • push("x") onto an int array → PACKED → no going back to SMI
   • arr[100] = … on a length-3 array → HOLEY → no going back to PACKED
   • huge or weird-keyed → DICTIONARY → real slow
```

Element kind transitions are **one-way** (packed → holey, smi → double → any). Once you assign `arr[1000] = ...` on a length-3 array, you get holes. Once you `arr.push("str")` on an int array, you lose SMI fast path.

```js
const a = [1, 2, 3];          // PACKED_SMI
a[100] = 5;                   // HOLEY_SMI — many holes
a.push("x");                  // HOLEY_ELEMENTS
```

#### Line-by-line walkthrough

1. `const a = [1, 2, 3];` — V8 inspects the literal: three small ints, no holes → tags the array `PACKED_SMI_ELEMENTS`. Allocates a tight 3-slot buffer.
2. `a[100] = 5;` — V8 sees an out-of-bounds index. Length jumps to 101. Slots 3..99 are holes. The element kind transitions to `HOLEY_SMI_ELEMENTS`. Internally the storage may now be a different layout.
3. `a.push("x");` — pushing a string. Not an SMI anymore. Element kind transitions to `HOLEY_ELEMENTS` (anything goes, including holes). All future ops are slower than the original packed-SMI form.

For perf in hot paths: pre-allocate, push in order, keep types homogeneous.

`length` is writable: `arr.length = 0` truncates in place.

### Big-O quick reference

| Operation         | Where      | Time | Notes                                                |
|-------------------|------------|------|------------------------------------------------------|
| `arr[i]` read     | any index  | O(1) | direct slot access (packed) or hashmap (dictionary)  |
| `push(x)`         | end        | O(1) | amortized; occasional buffer resize                  |
| `pop()`           | end        | O(1) | no shifting needed                                   |
| `shift()`         | front      | O(n) | every element slides left by 1                       |
| `unshift(x)`      | front      | O(n) | every element slides right by 1                      |
| `splice(i, k)`    | middle     | O(n) | elements after `i` slide                             |
| `indexOf` / `find`| any        | O(n) | linear scan                                          |
| `slice(a, b)`     | range      | O(k) | copies `k = b - a` elements                          |
| `concat`          | combine    | O(n + m)| new array allocated                               |
| `sort`            | full       | O(n log n)| stable since ES2019                              |
| `reverse`         | full       | O(n) | in place                                             |
| `Array.from(it)`  | iterable   | O(n) | materializes                                         |

## Syntax cheat sheet

> **Bridge:** Now that you understand WHY there are mutating vs non-mutating methods (one rearranges the cubbies in place; the other builds a new wall), the encyclopedia below organizes itself: anything ending in -ed/-ing that returns an array is usually non-mutating; anything verb-like that says "do" is usually mutating.

```js
// Creation
const a = [];
const b = [1, 2, 3];
const c = new Array(3);              // length 3, all holes
const d = Array.of(3);               // [3]
const e = Array.from({length: 3}, (_, i) => i); // [0,1,2]
const f = Array.from("abc");          // ['a','b','c']

// Mutating (return value varies)
b.push(4, 5);                         // length, mutates
b.pop();                              // removed item
b.unshift(0);                         // length
b.shift();                            // removed item
b.splice(1, 2, 'a', 'b');             // removed items array
b.sort((x, y) => x - y);              // sorted self
b.reverse();
b.fill(0, 1, 3);                      // fill range
b.copyWithin(0, 2);                   // copy block

// Non-mutating (return new array)
b.slice(1, 3);                        // shallow copy of [start,end)
b.concat([4,5]);
b.map(x => x * 2);
b.filter(x => x > 0);
b.flat(Infinity);
b.flatMap(x => [x, x]);
b.reduce((acc, x) => acc + x, 0);
b.reduceRight((acc, x) => acc + x, 0);
b.join(",");
b.toSorted((x, y) => x - y);          // ES2023 — new sorted array
b.toReversed();                       // ES2023
b.toSpliced(1, 1, 'x');               // ES2023
b.with(0, 99);                         // ES2023 — copy with index replaced

// Search
b.indexOf(2);                          // -1 if not found, uses ===
b.lastIndexOf(2);
b.includes(2);                         // works with NaN; indexOf doesn't
b.find(x => x > 1);                    // value or undefined
b.findIndex(x => x > 1);
b.findLast(x => x > 1);                // ES2023
b.findLastIndex(x => x > 1);

// Predicates
b.some(x => x > 0);                    // OR
b.every(x => x > 0);                   // AND

// Iteration
for (const x of b) {}
b.forEach(x => {});                    // can't break/return
b.entries(); b.keys(); b.values();

// Spread / destructure
const [first, ...rest] = b;
const merged = [...a, ...b];

// Typed arrays — fixed length, single numeric type, no holes
const ta = new Uint8Array([1, 2, 3]);
const buf = new ArrayBuffer(16);
const view = new Int32Array(buf);     // 4 i32s

// Array.isArray (cross-realm safe; instanceof Array isn't)
Array.isArray([]);                     // true

// Holes
const sparse = [1, , 3];               // length 3, hole at 1
sparse.map(x => x * 2);                // [2, <hole>, 6] — hole preserved
sparse.forEach(x => console.log(x));   // logs 1 and 3 only
sparse.indexOf(undefined);             // -1 (skips holes)
sparse.includes(undefined);            // true (doesn't skip)

// Length tricks
arr.length = 0;                        // truncate
arr.length = 10;                       // extend with holes
```

### Mutating vs non-mutating at a glance

```
MUTATING (modify this)            NON-MUTATING (return new)
─────────────────────             ──────────────────────────
push, pop                         slice, concat
shift, unshift                    map, filter, flat, flatMap
splice                            reduce, reduceRight, join
sort, reverse                     find, findIndex, findLast
fill, copyWithin                  some, every, includes, indexOf
                                  toSorted, toReversed, toSpliced, with
```

Memory trick: the ES2023 "to-" prefixed methods are explicitly the non-mutating counterparts of the older mutating ones. `sort` mutates; `toSorted` doesn't.

## Edge cases & interview traps
1. **`[10, 1, 2].sort()` → `[1, 10, 2]`** — stringifies. Always pass `(a,b) => a-b`.
2. **`.sort` mutates** and returns the same array; **`.toSorted` is non-mutating** (ES2023).
3. **`map` skips holes** but produces holes in output; **`Array.from({length:3}, fn)` fills them**.
4. **`forEach` cannot be broken out of** — use `for...of` with `break`, or `some`/`every`.
5. **`reduce` on empty array with no initial → TypeError** — always provide initial.
6. **`new Array(3)` creates a 3-hole array** — `.map` does nothing useful on it.
7. **`Array(3).fill(0).map(...)`** — common idiom because fill replaces holes with values.
8. **`arr.length = N` truncates** without notifying anything (no GC trigger for held values).
9. **`splice(start, deleteCount, ...items)`** is overloaded — easy to fumble.
10. **`indexOf` uses `===`** — NaN never found. Use `includes` or `findIndex(Number.isNaN)`.
11. **Spread copies are shallow** — `[...a]` shares object refs with `a`.
12. **Sparse arrays serialize weirdly**: `JSON.stringify([1,,3])` → `"[1,null,3]"`.
13. **`Array.from` is the only way to convert iterables (Set, Map, NodeList) cleanly**.
14. **`flat(Infinity)`** is O(n) total; not magic.
15. **Mutating during iteration**: `for (const x of arr) arr.push(...)` infinite loops; `.forEach` won't visit appended items.
16. **`Array.isArray` vs `instanceof Array`**: cross-realm (iframe, vm context), use `Array.isArray`.
17. **Typed arrays don't expand** — fixed length; no `push`.
18. **`[].concat(x)` doesn't spread if x isn't array-like** — gotcha for nested arrays.
    ```js
    [].concat([1, 2]);     // [1, 2]   — spreads array
    [].concat({a: 1});     // [{a:1}]  — does NOT spread plain object
    ```

## Interview worked examples

> **How to use this section:** For each example, predict the output first. Then read "How to think aloud" as the internal monologue, and "I'd say" as the script for the interviewer. The "common candidate mistake" notes are the traps to dodge.

### Example 1 — Sort numbers correctly
**Asked as:** "Sort `[10, 1, 5, 100, 2]` ascending. What's the gotcha?"

**How to think aloud:** "The instant I see `.sort()` on numbers, my brain flags 'comparator required.' Default sort coerces to strings — '10' compares as less than '2' because '1' < '2' lexicographically. Pass `(a, b) => a - b`. Negative result means a goes first."

I'd say: "Default `sort()` stringifies — '10' < '2' lexicographically — so you get nonsense. Always pass a numeric comparator. Returning a negative means 'a comes first', positive means 'b first', zero means equal."

```js
[10, 1, 5, 100, 2].sort();              // [1, 10, 100, 2, 5] — wrong
[10, 1, 5, 100, 2].sort((a, b) => a - b); // [1, 2, 5, 10, 100] — correct
```

**Common candidate mistake:** Writing `(a, b) => a > b` — that returns a boolean, which coerces to 0 or 1 and gives partially-wrong order in some engines. Always subtract.

**What the interviewer is testing:** Awareness of the default stringify-sort trap.
**Sharp follow-up they often ask:** "Is `sort` stable?" → Yes since ES2019. Earlier engines varied; today you can rely on stability.

### Example 2 — Dedupe with `Set`
**Asked as:** "Remove duplicates from an array of primitives."

**How to think aloud:** "Dedup → uniqueness → Set. For primitives, this is one line. For objects, Set uses reference identity, so `{a:1}` and `{a:1}` are distinct — I need a Map keyed by a derived field like `id`."

I'd say: "`new Set(arr)` is the one-liner — Set keeps only unique values by SameValueZero equality. Spread back to an array. For arrays of objects, this doesn't work because objects use identity equality — switch to a Map keyed by a derived key."

```js
const arr = [1, 2, 2, 3, 3, 3, 4];
[...new Set(arr)];                     // [1, 2, 3, 4]

// Objects: dedupe by id
const objs = [{id:1},{id:2},{id:1}];
[...new Map(objs.map(o => [o.id, o])).values()]; // [{id:1},{id:2}]
```

**Common candidate mistake:** Writing `arr.filter((x, i) => arr.indexOf(x) === i)` — works but is O(n²). Set is O(n).

**What the interviewer is testing:** Knowing Set semantics + the object-identity caveat.
**Sharp follow-up they often ask:** "Preserve first-seen order?" → Set already does (insertion order); same for the Map trick.

### Example 3 — Reduce into a grouping
**Asked as:** "Group an array of records by a field."

**How to think aloud:** "Group → bucket → reduce with an object accumulator. Each record: figure out its bucket key, push into `acc[key]`. Use `??=` so the bucket auto-initializes to `[]` the first time. Mention `Object.groupBy` for bonus points."

I'd say: "Single-pass reduce with an accumulator object. Use `??=` (logical-nullish-assignment) to initialize the bucket lazily. In modern engines, `Object.groupBy(arr, fn)` (ES2024) does this natively."

```js
const items = [
  { type: "fruit", name: "apple" },
  { type: "veg",   name: "kale"  },
  { type: "fruit", name: "pear"  },
];
const byType = items.reduce((acc, x) => {
  (acc[x.type] ??= []).push(x);
  return acc;
}, {});
// { fruit: [apple, pear], veg: [kale] }

// Modern:
Object.groupBy(items, x => x.type);
```

**Common candidate mistake:** Forgetting to `return acc` inside the reducer — next iteration receives `undefined` as accumulator and you get a TypeError.

**What the interviewer is testing:** Reduce idiom; awareness of newer `groupBy`.
**Sharp follow-up they often ask:** "What if keys are objects, not strings?" → use `Map.groupBy(items, fn)`.

### Example 4 — Flatten to depth N
**Asked as:** "Flatten `[1, [2, [3, [4]]]]` to depth 2."

**How to think aloud:** "Built-in: `arr.flat(2)`. They'll probably ask me to implement it. Recursion: for each element, if it's an array AND we still have depth budget, recurse with depth-1; else push as-is."

I'd say: "Use `arr.flat(depth)` — `Infinity` for full flatten. For an interview, also be ready to implement it recursively: if an element is an array AND we have depth left, recurse; else push."

```js
[1, [2, [3, [4]]]].flat(2);     // [1, 2, 3, [4]]
[1, [2, [3, [4]]]].flat(Infinity); // [1, 2, 3, 4]

// Manual:
function flat(arr, d = 1) {
  return arr.reduce((acc, x) =>
    acc.concat(Array.isArray(x) && d > 0 ? flat(x, d - 1) : x), []);
}
```

**Common candidate mistake:** Recursing without a depth budget — `flat(Infinity)` is fine for *built-in*, but in your recursive impl, infinite recursion on a deeply-nested input can blow the stack. Always parameterize depth.

**What the interviewer is testing:** Recursion + array methods + handling depth.
**Sharp follow-up they often ask:** "Make it iterative." → use an explicit stack and depth tracker, push children with `depth - 1`.

### Example 5 — Sparse array hole skipping
**Asked as:** "Predict the output of `[1, , 3].map(x => x * 2)` and `[1, , 3].forEach(...)`."

**How to think aloud:** "Holes are NOT the same as undefined. Most iteration methods (`map`, `filter`, `forEach`, `reduce`) skip holes. But `map` preserves the hole position in the output. `Array.from` is the exception — it materializes holes as `undefined` and DOES visit them."

I'd say: "Most array methods (`map`, `forEach`, `filter`, `reduce`, `some`, `every`) skip holes — they're not the same as `undefined`. `map` preserves the hole in the output. `forEach` doesn't visit the hole index. `Array.from` with a mapFn treats holes as undefined and DOES visit them."

```js
[1, , 3].map(x => x * 2);          // [2, <empty>, 6]
[1, , 3].forEach(x => console.log(x)); // logs 1 then 3 only
Array.from([1, , 3], x => x * 2);  // [2, NaN, 6] — undefined * 2
JSON.stringify([1, , 3]);          // "[1,null,3]"
```

**Common candidate mistake:** Treating `[1, , 3]` and `[1, undefined, 3]` as identical. They're not — the first has a hole at index 1; the second has an `undefined` value at index 1. `forEach` visits index 1 in the second but skips it in the first.

**What the interviewer is testing:** Sparse arrays + which methods skip holes.
**Sharp follow-up they often ask:** "How do you 'normalize' the holes to undefined?" → `Array.from(arr)` materializes holes as `undefined`.

### Example 6 — Move zeros (in-place vs non-mutating)
**Asked as:** "Move all zeros to the end while keeping non-zero order. Discuss mutating vs returning a new array."

**How to think aloud:** "Two pointers. Read-pointer scans, write-pointer marks next non-zero slot. When read hits a non-zero, copy it to the write slot and advance write. After the scan, fill the tail with zeros. O(n) time, O(1) space. Then offer the elegant non-mutating one-liner with two filters."

I'd say: "Two-pointer in-place: a write-pointer marks the next slot for a non-zero; iterate, swap or assign when non-zero, then fill remaining slots with zero. O(n) time, O(1) space. The non-mutating version is `arr.filter(x => x).concat(arr.filter(x => !x))` — clean but allocates."

```js
// In-place
function moveZeros(arr) {
  let w = 0;
  for (let r = 0; r < arr.length; r++) {
    if (arr[r] !== 0) { arr[w++] = arr[r]; }
  }
  while (w < arr.length) arr[w++] = 0;
  return arr;
}
moveZeros([0, 1, 0, 3, 12]); // [1, 3, 12, 0, 0]

// Non-mutating
const moveZeros2 = arr => [...arr.filter(x => x), ...arr.filter(x => !x)];
```

**Common candidate mistake:** Using `filter(x => x)` to filter out zeros — works for the number `0`, but ALSO filters out empty strings, `false`, `null`, `undefined`, `NaN`. If your array might contain those non-zero falsy values, use `filter(x => x !== 0)` explicitly.

**What the interviewer is testing:** Two-pointer technique + mutation trade-offs.
**Sharp follow-up they often ask:** "Which would you ship in a Node service?" → Non-mutating if the array is shared/cached (immutability prevents aliasing bugs); in-place if memory-critical and you own the array.

## Common machine-coding patterns
- **Group by key (reduce)** — when used: aggregation. Sketch:
  ```js
  const byKey = arr.reduce((acc, x) => ((acc[x.k] ??= []).push(x), acc), {});
  // ES2024: Object.groupBy(arr, x => x.k)
  ```
- **Dedup (Set)** — `const u = [...new Set(arr)];`
- **Chunking** —
  ```js
  const chunk = (a, n) => Array.from({length: Math.ceil(a.length/n)}, (_, i) => a.slice(i*n, i*n+n));
  ```
- **Flatten n levels** — `arr.flat(Infinity)` or manual recursion (interview classic).
  ```js
  const flat = (a) => a.reduce((acc, x) => acc.concat(Array.isArray(x) ? flat(x) : x), []);
  ```
- **Top-K** — sort & slice (O(n log n)) or a min-heap (O(n log k)). Heap impl for large n.
- **Reduce-based pipeline** — when used: replace 3 maps + filter with 1 pass for perf.
- **Range** — `Array.from({length: n}, (_, i) => i)`.
- **Transpose 2D array** —
  ```js
  const T = m => m[0].map((_, i) => m.map(r => r[i]));
  ```

## Backend-specific notes
For batch inserts and aggregations on hot endpoints, prefer typed-loop patterns over `.map().filter().reduce()` chains if memory and allocations matter — each chain step allocates a new array. For O(10k+) records per request, switch to a single `for` loop or use lazy iterators / generators.

When returning arrays from a service layer, ensure callers can't mutate your cache — `[...cached]` shallow copy, or `Object.freeze`. Returning the internal array is the classic "cache poisoning" bug.

For very large data, don't load into memory at all — use streams (see streams.md) or DB cursors. `array.length` of 50M strings each 200 bytes will OOM a 4GB pod.

`JSON.stringify` on big arrays blocks the event loop — for >1MB payloads, consider streaming JSON or a binary format.

## 60-second revision (day-before)
```text
┌──────────────────────────────────────────────────────────┐
│ ARRAYS — DAY-BEFORE CRAM                                 │
├──────────────────────────────────────────────────────────┤
│ • sort() stringifies — ALWAYS pass comparator            │
│ • Mutating: push/pop/shift/unshift/splice/sort/reverse   │
│ • Non-mut: map/filter/slice/concat/flat/flatMap/toSorted │
│ • reduce(empty, no-init) → TypeError                     │
│ • forEach can't break; use for...of                      │
│ • indexOf uses ===, NaN-blind; includes is NaN-aware     │
│ • new Array(3) → 3 holes; fill before map                │
│ • Array.from({length:n}, (_,i)=>...) → ranges            │
│ • [...new Set(arr)] → dedup                              │
│ • shift/unshift O(n); push/pop O(1)                      │
│ • Spread = shallow copy                                  │
│ • Sparse → JSON.stringify nulls them                     │
│ • V8 element kinds: keep packed + same type for speed    │
│ • ES2023 toSorted/toReversed/toSpliced/with = immutable  │
│ • Object.groupBy / Map.groupBy (ES2024)                  │
│ • Typed arrays: fixed length, single numeric type        │
└──────────────────────────────────────────────────────────┘
```
