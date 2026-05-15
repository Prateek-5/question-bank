# Chunk an Array — `chunk(arr, size)`

## Source
- LeetCode #2677 "Chunk Array" — https://leetcode.com/problems/chunk-array/
- Lodash `_.chunk(arr, size)` — https://lodash.com/docs/4.17.15#chunk
- Appears on codedamn, BFE.dev, and almost every "build a paginator/batch processor" round.

## Why this question matters in interviews
Chunking is the one-liner that proves you can think in **batches** — paginating API results, splitting BigQuery insert rows into 500-row groups, breaking a webhook fan-out into rate-limited windows, streaming N records at a time to a worker pool. Interviewers love it because there are two clean solutions (functional `Array.from` vs imperative `for` loop), both correct, with different readability/performance tradeoffs. They'll also probe your awareness that `arr.slice(start, end)` is **O(k)** (copies the window), so total work is O(n) — not O(n²) as some candidates fear. The follow-ups (lazy iterator, balanced chunks, fixed-count instead of fixed-size) test how flexibly you compose primitives.

## Concepts involved

### Syntax to lock in
```js
chunk([1,2,3,4,5], 2);   // [[1,2], [3,4], [5]]
chunk([1,2,3,4], 2);     // [[1,2], [3,4]]
chunk([], 3);            // []
chunk([1,2,3], 0);       // [] (treat non-positive size as empty)
```

### Two canonical implementations
**Functional (one-liner):**
```js
Array.from({ length: Math.ceil(arr.length / size) },
           (_, i) => arr.slice(i * size, (i + 1) * size));
```
Elegant. Pre-computes the bucket count; `Array.from` with a length+mapper produces a dense array. Easy to misuse if you forget `Math.ceil`.

**Imperative (loop):**
```js
const out = [];
for (let i = 0; i < arr.length; i += size) {
  out.push(arr.slice(i, i + size));
}
```
Equally O(n); some engineers find it more readable, and it generalises cleanly to a generator (lazy chunking, see Variants).

### Slice semantics
`arr.slice(start, end)` is non-mutating, returns a shallow copy, accepts an `end` larger than `arr.length` (just clips to the end). That's why the last chunk being shorter "just works" — no special-case needed.

### Edge cases that earn points
1. `size <= 0` or non-integer `size` → return `[]` (lodash behavior) or throw. **Clarify with interviewer.**
2. `arr` empty → return `[]`. Both implementations naturally handle this.
3. Very large `size` (greater than `arr.length`) → returns `[[...arr.slice()]]` — one chunk containing a shallow copy.
4. **Sparse arrays** — `slice` preserves holes. If interviewer hands you `[1, , 3]`, the chunk containing index 1 will still be sparse. Mention this; offer to densify with `.filter(() => true)` if asked.
5. **Mutation safety** — chunks are shallow copies of the *array*; nested object refs are shared. Document this.

### Big-O
- Time: O(n) — every element copied into exactly one chunk.
- Space: O(n) for output + O(1) overhead.
- `slice` per chunk is O(k); summed across `⌈n/size⌉` chunks → O(n). Not O(n²).

## Brute force approach
Push elements one by one into the "current" sub-array, opening a new one every `size` items:
```js
const out = [];
arr.forEach((v, i) => {
  if (i % size === 0) out.push([]);
  out[out.length - 1].push(v);
});
```
Correct, but creates extra array writes and ignores holes the same way `forEach` does (silently). The `slice` approach is cleaner and engine-optimized.

## Optimal approach
Use `arr.slice(i, i + size)` inside a stepped loop (or `Array.from` with a computed bucket count). Both are O(n) and idiomatic. Pick the imperative version if you want to extend later (early exit, async, generator); pick the functional one for a clean one-liner.

## Solution (JavaScript)

```js
/**
 * Split `arr` into contiguous sub-arrays of length `size`. Last chunk may be shorter.
 * @param {Array} arr
 * @param {number} size  positive integer
 * @returns {Array<Array>}
 */
function chunk(arr, size) {
  if (!Array.isArray(arr)) throw new TypeError('arr must be an array');
  if (!Number.isInteger(size) || size <= 0) return [];

  // Imperative — generalises easily to lazy/async variants.
  const out = [];
  for (let i = 0; i < arr.length; i += size) {
    out.push(arr.slice(i, i + size));
  }
  return out;
}

// One-liner alternative — keep both in your head:
const chunkFn = (arr, size) =>
  size > 0
    ? Array.from({ length: Math.ceil(arr.length / size) },
                 (_, i) => arr.slice(i * size, (i + 1) * size))
    : [];
```

## Step-by-step dry run

Input:
```js
chunk([10, 20, 30, 40, 50], 2);
```

Trace:
- `Array.isArray` → true. `size=2`, valid.
- `i=0`: `arr.slice(0, 2)` → `[10, 20]`. `out = [[10, 20]]`.
- `i=2`: `arr.slice(2, 4)` → `[30, 40]`. `out = [[10, 20], [30, 40]]`.
- `i=4`: `arr.slice(4, 6)` → `[50]` (slice clips end at length 5). `out = [[10, 20], [30, 40], [50]]`.
- `i=6`: loop exits (`6 < 5` false).
- Return `[[10, 20], [30, 40], [50]]`.

Edge run — `chunk([], 3)`:
- Loop condition fails immediately. Return `[]`.

Edge run — `chunk([1, 2], 5)`:
- `i=0`: `arr.slice(0, 5)` → `[1, 2]`. Return `[[1, 2]]`. One chunk, shorter than `size`.

Edge run — `chunk([1, 2, 3], 0)`:
- `Number.isInteger(0) && 0 <= 0` → return `[]`. Avoids infinite loop.

## Important takeaways

**Syntax to memorize**
- `arr.slice(i, i + size)` — the workhorse. Auto-clips at array length.
- `Array.from({ length: N }, (_, i) => ...)` — produces a dense array; the `length` property is enough.
- `Math.ceil(n / size)` — bucket count. Off-by-one if you forget the `ceil`.

**Patterns to reuse**
- Chunking is the foundation of paginators, batchers, rate limiters, and parallel uploaders. `for await` over `chunk(rows, 500)` is the typical "bulk insert" pattern.
- The "stepped `for` loop" (`i += size`) is the same skeleton as a sliding window — just change the slice bounds.

**Common mistakes**
- Forgetting `Math.ceil` in the functional version → drops the last partial chunk.
- Guarding `size > 0` AFTER the loop starts → infinite loop on `size = 0`.
- Assuming `slice` is O(1). It's O(k) per call, O(n) total — but never O(n²).
- Mutating the source array (e.g., `arr.splice(0, size)` inside a loop). Works, but destroys input. Bad form.

**Related questions**
- `unchunk(chunks)` — `chunks.flat()` or `[].concat(...chunks)`.
- `chunkInto(arr, count)` — split into a fixed number of chunks instead of a fixed size. Different math.
- Lazy `chunk` via generator (see Variants).

## Variants

1. **Lazy chunk (generator)** — yields chunks on demand instead of allocating the full output. Crucial when `arr` is huge or backed by a stream of pages. `function* chunkLazy(it, size) { let buf=[]; for (const v of it) { buf.push(v); if (buf.length===size) { yield buf; buf=[]; } } if (buf.length) yield buf; }`. Works on any iterable, not just arrays.
2. **`chunkInto(arr, n)`** — produce exactly `n` near-equal chunks. Compute `size = Math.ceil(arr.length / n)` then chunk; or distribute remainder one-per-bucket for "as balanced as possible." Common follow-up.
3. **Async chunk-and-process** — `for (const c of chunk(arr, 50)) await processBatch(c);` — sequential throttling, no extra library needed. Mention it; interviewers love seeing it applied.

## Revision notes

> **chunk(arr, size) — 60 second recap**
> - `arr.slice(i, i + size)` inside `for (i=0; i<n; i+=size)`. Last chunk auto-shortens.
> - Functional alt: `Array.from({length: Math.ceil(n/size)}, (_,i) => arr.slice(i*size,(i+1)*size))`.
> - Guard non-positive / non-integer `size` → return `[]`.
> - Time O(n), space O(n). `slice` is O(k) per call; total still O(n).
> - Non-mutating; chunks are **shallow** copies — nested objects shared.
> - Sparse-array holes survive `slice` — densify with `.filter(() => true)` if asked.
> - For huge data, prefer a **generator** version that yields chunks lazily.
> - **Trap:** forgetting `Math.ceil` drops the tail. `size=0` without guard → infinite loop.
