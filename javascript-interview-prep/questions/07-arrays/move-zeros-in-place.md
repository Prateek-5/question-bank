# Move all zeros to end (in-place, preserve order)

## Source
- LeetCode #283 "Move Zeroes": https://leetcode.com/problems/move-zeroes/
- Canonical two-pointer interview problem (every level).
- BFE.dev / GreatFrontEnd variants.

## Why this question matters in interviews
Move-zeros is the **two-pointer technique gateway problem**. Backend interviewers use it as a 10-minute warm-up before harder array problems (3Sum, rainwater, sliding window). The trap: candidates instinctively reach for `arr.filter(x => x !== 0).concat(arr.filter(x => x === 0))` — clean, but **not in-place**, allocates O(n) memory, and ignores the central constraint. The interviewer wants to see: (1) the **two-pointer write-index pattern**, (2) understanding of **in-place mutation vs functional**, (3) **off-by-one awareness**, and (4) the alternative **swap-based** version with its trade-offs. It's the "do you know array-mutation idioms?" filter.

## Concepts involved

### Syntax to lock in
```js
const arr = [0, 1, 0, 3, 12];
moveZeros(arr);
// arr is now [1, 3, 12, 0, 0]   (mutated in place)
```

### Runtime / engine behavior
- "In-place" means O(1) extra memory — only a couple of index variables, no auxiliary arrays.
- Two pointers: a **read pointer** scans the array; a **write pointer** advances only when a non-zero is written. The gap between them grows as zeros pile up.
- Order of non-zero elements must be preserved (stable). Some problem variants (LeetCode #75 "Sort Colors") drop this constraint and allow swaps for unstable but in-place sort.
- V8's array storage: dense small-integer arrays use a packed representation (SMI). Writing zeros at the end is cheap. Mutating an element to a different "shape" (e.g., zero → string) can deopt the array to dictionary mode. Not usually a concern.
- The "filter + concat" or "two filters" approach is O(n) time but O(n) **memory** and not in-place. Mention it as a non-solution.

### Edge cases (the interview traps)
1. **All zeros** — `[0,0,0]` → no non-zero, write index stays at 0, final fill writes 0s back. No-op effectively. Don't crash.
2. **No zeros** — `[1,2,3]` → write index walks alongside read, the trailing fill loop doesn't execute (`w === n`).
3. **Single element** — `[0]` or `[5]` — both should work without index errors.
4. **Empty array** — `[]` — the loops just don't execute. Return immediately or naturally fall through.
5. **In-place mutation expectation** — the caller's array reference must be the modified one. Don't return a new array unless asked.
6. **Off-by-one on the fill loop** — `while (w < n) arr[w++] = 0` is correct; `while (w <= n)` writes past the end and grows the array.
7. **Swap-based alternative vs overwrite** — swap preserves elements but does up to 2× the writes for the same algorithm. Overwrite is faster but destroys the original zero positions (which we don't care about — we're overwriting them with zeros anyway).
8. **Sparse arrays / holes** — `[1, , 3]`. A hole is NOT zero. Should it stay a hole or become a zero? Spec it — most candidates default to "treat hole as falsy" which is wrong (`arr[1] === undefined`, not `0`).

## Brute force approach

**Approach A — two filters:**
```js
function moveZerosNaive(arr) {
  const nonZeros = arr.filter(x => x !== 0);
  const zeros    = arr.filter(x => x === 0);
  return [...nonZeros, ...zeros];   // NOT in-place
}
```
O(n) time, O(n) space, **returns a new array** — fails the in-place constraint.

**Approach B — repeated splice:**
```js
function moveZerosSplice(arr) {
  for (let i = arr.length - 1; i >= 0; i--) {
    if (arr[i] === 0) {
      arr.splice(i, 1);
      arr.push(0);
    }
  }
}
```
In-place but O(n²) — each splice shifts elements. Junior tell.

Both are wrong answers in different ways. Move past them.

## Optimal approach

**Two-pointer overwrite** — single pass with write index:

1. `w = 0` (write pointer).
2. Scan `r` from `0` to `n - 1`. If `arr[r] !== 0`, write `arr[w++] = arr[r]`.
3. After the scan, fill `arr[w..n-1]` with zeros.

O(n) time, O(1) extra space, single pass + trivial tail fill. The total writes are exactly `n` in the worst case (all non-zero) and `(#non-zeros) + (#zeros)` overall — same as a copy.

**Two-pointer swap** — alternative:

1. `w = 0`. Scan `r`. If `arr[r] !== 0`, `[arr[w], arr[r]] = [arr[r], arr[w]]; w++`.
2. No tail fill needed — the swap moves each zero to the rear naturally.

Same complexity, but does swaps even when `w === r` (wasted work). Slightly more elegant; ever-so-slightly slower in practice.

## Solution (JavaScript)

```js
/**
 * Move all zeros to the end, preserving non-zero order.
 * Mutates the input array in place. O(n) time, O(1) space.
 */
function moveZeros(arr) {
  const n = arr.length;
  let w = 0;                       // write index

  // Pass 1: pack non-zeros to the front
  for (let r = 0; r < n; r++) {
    if (arr[r] !== 0) {
      arr[w++] = arr[r];
    }
  }

  // Pass 2: fill the tail with zeros
  while (w < n) {
    arr[w++] = 0;
  }
}

/**
 * Swap-based alternative — single loop, no tail fill.
 * Same O(n) / O(1). Slightly more writes in worst case.
 */
function moveZerosSwap(arr) {
  let w = 0;
  for (let r = 0; r < arr.length; r++) {
    if (arr[r] !== 0) {
      if (w !== r) {
        [arr[w], arr[r]] = [arr[r], arr[w]];
      }
      w++;
    }
  }
}
```

## Step-by-step dry run

Input: `[0, 1, 0, 3, 12]`, `n = 5`.

**Pass 1 (pack non-zeros):**
| r | arr[r] | non-zero? | write? | w after | arr after |
|---|---|---|---|---|---|
| 0 | 0  | no  | —              | 0 | `[0, 1, 0, 3, 12]` |
| 1 | 1  | yes | `arr[0] = 1`   | 1 | `[1, 1, 0, 3, 12]` |
| 2 | 0  | no  | —              | 1 | `[1, 1, 0, 3, 12]` |
| 3 | 3  | yes | `arr[1] = 3`   | 2 | `[1, 3, 0, 3, 12]` |
| 4 | 12 | yes | `arr[2] = 12`  | 3 | `[1, 3, 12, 3, 12]` |

After pass 1: `w = 3`, array is `[1, 3, 12, 3, 12]`. Indices 3 and 4 are "stale" — they hold leftover non-zeros that we already copied to the front.

**Pass 2 (zero-fill tail):**
| w | action | arr after |
|---|---|---|
| 3 | `arr[3] = 0` | `[1, 3, 12, 0, 12]` |
| 4 | `arr[4] = 0` | `[1, 3, 12, 0, 0]` |
| 5 | loop ends (`w === n`) | done |

Final: `[1, 3, 12, 0, 0]`. Three non-zeros at front in original order, two zeros at end. Correct.

**Swap variant trace** for same input:
- `r=0`: `arr[0]=0`, skip.
- `r=1`: `arr[1]=1` non-zero, swap with `arr[0]`. Array `[1,0,0,3,12]`. `w=1`.
- `r=2`: `arr[2]=0`, skip.
- `r=3`: `arr[3]=3` non-zero, swap with `arr[1]`. Array `[1,3,0,0,12]`. `w=2`.
- `r=4`: `arr[4]=12` non-zero, swap with `arr[2]`. Array `[1,3,12,0,0]`. `w=3`.
- Same result, four swaps performed.

## Important takeaways

**Syntax to memorize**
- Two-pointer write index: `let w = 0; for (let r = 0; r < n; r++) if (cond) arr[w++] = arr[r];`. Universal "compact in place" idiom.
- Tail fill: `while (w < n) arr[w++] = 0;`. Off-by-one is `w <= n` which writes past the end.
- Swap: `[arr[w], arr[r]] = [arr[r], arr[w]];`. Destructuring swap, no temp variable.

**Patterns to reuse**
- **Write-index two-pointer** — same pattern for: "remove duplicates from sorted array" (LeetCode #26), "remove element" (#27), "compress array" (#443), "sort colors" (#75 with three pointers).
- **Filter-in-place** — the general shape `let w = 0; for r: if (keep) arr[w++] = arr[r]; arr.length = w;` (truncate variant) drops elements rather than zero-filling them. Different problem, same skeleton.
- **In-place vs functional** — `filter` allocates; `splice` is O(n) per call. Two-pointer is the in-place workhorse.

**Common mistakes**
- Using `filter + concat` and not reading the "in-place" constraint. Interview-killer.
- Using `splice` in a loop — O(n²).
- Off-by-one in the tail fill (`while (w <= n)`).
- Swapping unconditionally even when `w === r` — wasteful but harmless.
- Treating sparse holes as zeros — `[1, , 3]` should preserve the hole unless spec'd otherwise.
- Forgetting to handle empty / single-element arrays (usually the natural loops do, but state it).

**Related questions**
- LeetCode #26 — remove duplicates from sorted array (same two-pointer skeleton).
- LeetCode #27 — remove element (same skeleton with a different predicate).
- LeetCode #75 — sort colors (Dutch National Flag; three pointers).
- LeetCode #88 — merge sorted array in place (two pointers from the END).
- `polyfill-filter` (allocating variant of the same predicate).

## Variants

1. **Return count of non-zeros** — LeetCode #27 ("Remove Element") asks for `w` itself as the new "logical length." Then `arr.length = w` truncates if you want the array shorter.

2. **Move zeros to the FRONT instead** — mirror the algorithm: scan right-to-left with write index from the end. Same skeleton, reversed direction.

3. **Move negatives / specific value / predicate** — generalize: `moveToEnd(arr, predicate)`. The two-pointer pattern is predicate-agnostic.

4. **Dutch National Flag (sort 3 values in place)** — LeetCode #75. Three pointers: `low`, `mid`, `high`. Classic interview escalation from move-zeros.

5. **Stable swap variant** — "Why might you choose swap over overwrite?" Swap is more general (works when you can't overwrite, e.g., custom equality on objects). Overwrite is faster when destination doesn't matter.

## Revision notes

> **move-zeros — 60 second recap**
> - Two-pointer: `w` (write) and `r` (read). Walk `r` left to right.
> - If `arr[r] !== 0` → `arr[w++] = arr[r]`. Else skip.
> - After scan, `while (w < n) arr[w++] = 0`. Off-by-one trap.
> - O(n) time, O(1) space, in-place.
> - **Alternative:** swap-based — `[arr[w], arr[r]] = [arr[r], arr[w]]; w++` when non-zero. No tail fill needed; more writes.
> - **Trap:** `filter + concat` is NOT in-place, allocates O(n) memory.
> - **Family:** write-index two-pointer is the skeleton for #26, #27, #75, #283, #443.
