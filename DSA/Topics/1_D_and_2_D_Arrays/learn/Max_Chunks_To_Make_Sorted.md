# Max Chunks To Make Sorted — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Max_Chunks_To_Make_Sorted.md`](../Max_Chunks_To_Make_Sorted.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/max-chunks-to-make-sorted/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/max-chunks-to-make-sorted/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. The problem teaches **the running-max invariant** — a single-pass observation that turns an algorithmically "wide" question (how do I partition this array?) into a one-line check. The technique transfers to many "can I split this thing into pieces?" problems.

**Map of this file (10 short sections):**

1. Read the problem
2. Tiny cases by hand
3. The natural first approach (and why it's vague)
4. The pivot — when CAN a chunk end?
5. The running-max invariant
6. Why running-max-equals-index is the EXACT condition
7. Code
8. Trace it
9. Common pitfalls
10. The shape — running-max invariants elsewhere

---

## 1. Read the problem

You're given an array `arr` that is a **permutation of `[0, 1, 2, ..., n-1]`** (every integer from 0 to n-1 appears exactly once, in some order).

You want to split `arr` into **contiguous chunks** such that, if you sort each chunk individually and then **concatenate** the sorted chunks in order, you get the fully sorted array `[0, 1, 2, ..., n-1]`.

Return the **maximum** number of chunks you can split it into.

> **Mini-refresher: what "permutation of 0..n-1" means.**
>
> A permutation is a rearrangement. The array contains each of the integers `0, 1, 2, ..., n−1` exactly once, but in any order. No duplicates, no missing values, no values outside `[0, n−1]`.
>
> Examples of permutations of `0..4`: `[0, 1, 2, 3, 4]`, `[4, 3, 2, 1, 0]`, `[1, 0, 2, 3, 4]`, `[2, 0, 4, 1, 3]`.
>
> Not a permutation of `0..4`: `[0, 1, 2, 3]` (missing 4), `[0, 1, 1, 2, 3]` (duplicate), `[1, 2, 3, 4, 5]` (contains 5).

**Example 1:** `arr = [1, 0, 2, 3, 4]`.

Try splitting into 4 chunks: `[1, 0] | [2] | [3] | [4]`.

- Sort each chunk: `[0, 1] | [2] | [3] | [4]`.
- Concatenate: `[0, 1, 2, 3, 4]`. ✓ That's the sorted array. So 4 chunks works.

Can we do 5? That would mean 5 singleton chunks: `[1] | [0] | [2] | [3] | [4]`. Sorting each leaves them unchanged. Concatenated: `[1, 0, 2, 3, 4]` — same as the input, NOT sorted. So 5 chunks doesn't work.

Answer: **4**.

**Example 2:** `arr = [4, 3, 2, 1, 0]`. No matter how we split, until everything is in one chunk we can't get the smallest values to the front. Answer: **1**.

**Example 3:** `arr = [0, 1, 2, 3, 4]` (already sorted). Each element is in the right place; we can use 5 singleton chunks. Answer: **5**.

---

## 2. Tiny cases by hand

Let me work a few more to build intuition.

**`arr = [0, 2, 1]`:**

- `[0] | [2, 1]`: sort → `[0] | [1, 2]` → `[0, 1, 2]`. ✓ 2 chunks.
- Could we get 3? `[0] | [2] | [1]`. Sort each: same. Concatenated: `[0, 2, 1]`. Not sorted. So 3 chunks doesn't work.

Answer: 2.

**`arr = [1, 2, 0, 3]`:**

- `[1, 2, 0] | [3]`. Sort each: `[0, 1, 2] | [3]`. → `[0, 1, 2, 3]`. ✓ 2 chunks.
- Could we get 3? Try `[1] | [2, 0] | [3]`. Sort: `[1] | [0, 2] | [3]`. → `[1, 0, 2, 3]`. Not sorted.
- Try `[1, 2] | [0] | [3]`. Sort: `[1, 2] | [0] | [3]`. → `[1, 2, 0, 3]`. Not sorted.

Answer: 2.

**`arr = [0, 3, 1, 2, 4]`:**

- `[0] | [3, 1, 2] | [4]`. Sort: `[0] | [1, 2, 3] | [4]`. → `[0, 1, 2, 3, 4]`. ✓ 3 chunks.

Notice in every case: the chunk boundary appears at indices where "everything seen so far" fills out the prefix of the sorted result.

In `[1, 0, 2, 3, 4]`, the elements `{1, 0}` together fill `{0, 1}` — the first two positions of the sorted result. So the chunk `[1, 0]` can be sorted and placed at indices 0-1. Then `[2]` at index 2, etc.

This is the structural property we need to encode.

---

## 3. The natural first approach (and why it's vague)

If I asked you to write code right now, you might say: "try every possible split, check which gives the most chunks." Pseudocode:

```
For each way to split arr into chunks:
    sort each chunk
    concatenate
    if result == sorted(arr):
        chunks_count = number of chunks
        track max

Return max
```

That's correct but **disastrously slow** — there are 2^(n-1) ways to insert/skip splits in an n-element array. Exponential time.

Even more concerning: we don't have an obvious **structural rule** for when a split is valid. The brute force checks each split by simulation; we should be able to determine validity in O(1) per candidate split.

**Pivot question:** what's the EXACT condition for a chunk to "end" at index `j`?

---

## 4. The pivot — when CAN a chunk end?

Imagine arr split into chunks. Look at the **first chunk** — say it's `arr[0..j]`. After we sort it, the result should fill positions `0..j` of the final sorted array.

The sorted array is `[0, 1, 2, ..., n-1]`, so positions `0..j` of it are `[0, 1, 2, ..., j]`.

**Therefore: the first chunk `arr[0..j]` must contain exactly the values `{0, 1, ..., j}`.**

Why exactly those values? Because:

- The chunk has `j + 1` elements (positions `0..j` inclusive).
- After sorting, it fills positions `0..j` of the result.
- Those positions must hold the smallest `j + 1` values from the array (the values that belong there in sorted order).
- The smallest `j + 1` values of `arr` are `0, 1, ..., j` (since `arr` is a permutation of `0..n-1`).

So chunk `arr[0..j]` works iff `arr[0..j] = {0, 1, ..., j}` (as a set).

Same logic applies recursively for the second chunk, third chunk, etc. — each chunk must contain exactly the consecutive integers it'll be placed onto in the sorted result.

> **The pivot question, answered:**
>
> A chunk can end at index `j` if and only if `arr[0..j]` (or, for later chunks, the elements since the previous chunk-end) **is exactly the set of consecutive integers** that should land at those positions in the sorted output.

For the first chunk, that's `arr[0..j] = {0, 1, ..., j}`.

Now: how do we **check** "is `arr[0..j]` equal to `{0, 1, ..., j}` as a set" quickly? Computing a set takes O(j) per index — O(n²) over all indices.

There's a much cheaper check. Read on.

---

## 5. The running-max invariant

Suppose `arr[0..j]` does equal `{0, 1, ..., j}`. What can we say about its **max**?

- The max of `{0, 1, ..., j}` is `j` itself.
- So **`max(arr[0..j]) = j`**.

That's an O(1) check per index, given a running max!

Conversely (this is the subtle part — we'll prove it in the next section): if `max(arr[0..j]) = j` for an array that's a permutation of `0..n-1`, then **`arr[0..j]` MUST equal `{0, 1, ..., j}`**.

So:

> **The condition "chunk can end at index `j`" reduces to the O(1) check `max(arr[0..j]) == j`.**

The algorithm:

```
max_so_far = -1
chunks = 0
for i = 0 .. n-1:
    max_so_far = max(max_so_far, arr[i])
    if max_so_far == i:
        chunks++         # a chunk can end here
return chunks
```

Single pass with a running max. **O(n) time, O(1) space.** Done.

But before we celebrate, let me prove the "reverse direction" — that `max(arr[0..j]) == j` really does imply `arr[0..j] = {0, 1, ..., j}`.

---

## 6. Why running-max-equals-index is the EXACT condition

**Claim:** for an array `arr` that's a permutation of `0..n-1`, the following are **equivalent**:

(a) `arr[0..j]` is exactly the set `{0, 1, ..., j}`.

(b) `max(arr[0..j]) == j`.

**Direction (a) ⇒ (b).** If `arr[0..j]` is `{0, ..., j}`, its largest element is `j`. ✓

**Direction (b) ⇒ (a).** This is the subtle direction. Here's a careful argument.

Suppose `max(arr[0..j]) == j`. We want to show `arr[0..j] = {0, 1, ..., j}`.

Facts we have:

1. `arr` is a permutation of `0..n-1`, so all values in `arr[0..j]` are distinct integers in `{0, 1, ..., n-1}`.
2. `arr[0..j]` contains `j + 1` elements (positions 0 through j, inclusive).
3. The max of `arr[0..j]` is `j`. So every value in `arr[0..j]` is `≤ j`.

From (1) and (3): the values in `arr[0..j]` are distinct integers in `{0, 1, ..., j}`.

How many integers are in `{0, 1, ..., j}`? Exactly `j + 1`.

From (2): we have `j + 1` distinct integers, all from a set of size `j + 1`. By pigeonhole, **they must be EXACTLY that set** — `arr[0..j] = {0, 1, ..., j}`. ✓

> **Mini-refresher: pigeonhole-flavored set equality.**
>
> If a set `S` is a subset of `T`, and `|S| = |T|` (same size), then `S = T`. There's no room for `S` to omit any element of `T` — they have the same count.
>
> Applied here: `arr[0..j]` is a subset of `{0, 1, ..., j}` (every value is in that set), and both have size `j + 1`. So they're equal.

So the running-max-equals-index test is **necessary AND sufficient** for "chunk can end here." There are no false positives and no false negatives.

---

## 7. Code

```cpp
int maxChunksToSorted(vector<int>& arr) {
    int maxSoFar = -1;          // sentinel: no elements seen yet
    int chunks = 0;
    for (int i = 0; i < (int)arr.size(); i++) {
        maxSoFar = max(maxSoFar, arr[i]);
        if (maxSoFar == i) {
            chunks++;            // a chunk can end at index i
        }
    }
    return chunks;
}
```

Six lines.

**Python:**

```python
def maxChunksToSorted(arr):
    max_so_far = -1
    chunks = 0
    for i, x in enumerate(arr):
        max_so_far = max(max_so_far, x)
        if max_so_far == i:
            chunks += 1
    return chunks
```

**JavaScript:**

```javascript
function maxChunksToSorted(arr) {
    let maxSoFar = -1, chunks = 0;
    for (let i = 0; i < arr.length; i++) {
        maxSoFar = Math.max(maxSoFar, arr[i]);
        if (maxSoFar === i) chunks++;
    }
    return chunks;
}
```

All three: single pass, O(n) time, O(1) space. The simplicity is the point.

---

## 8. Trace it

**`arr = [1, 0, 2, 3, 4]`:**

```
max_so_far = -1, chunks = 0

i = 0, arr[0] = 1:  max_so_far = max(-1, 1) = 1.  1 == 0?  No.   chunks = 0.
i = 1, arr[1] = 0:  max_so_far = max(1, 0) = 1.   1 == 1?  YES.  chunks = 1.
i = 2, arr[2] = 2:  max_so_far = max(1, 2) = 2.   2 == 2?  YES.  chunks = 2.
i = 3, arr[3] = 3:  max_so_far = max(2, 3) = 3.   3 == 3?  YES.  chunks = 3.
i = 4, arr[4] = 4:  max_so_far = max(3, 4) = 4.   4 == 4?  YES.  chunks = 4.

Return 4.  ✓
```

The chunk boundaries are at indices 1, 2, 3, 4 — meaning chunks are `[1, 0]`, `[2]`, `[3]`, `[4]`. Matches our hand-analysis from §1.

**`arr = [4, 3, 2, 1, 0]`:**

```
i = 0:  max = 4.  4 == 0?  No.
i = 1:  max = 4.  4 == 1?  No.
i = 2:  max = 4.  4 == 2?  No.
i = 3:  max = 4.  4 == 3?  No.
i = 4:  max = 4.  4 == 4?  YES.  chunks = 1.

Return 1.  ✓
```

The running max sits stuck at 4 until index 4 catches up. One chunk only.

**`arr = [0, 3, 1, 2, 4]`:**

```
i = 0:  max = 0.  0 == 0?  YES.  chunks = 1.
i = 1:  max = 3.  3 == 1?  No.
i = 2:  max = 3.  3 == 2?  No.
i = 3:  max = 3.  3 == 3?  YES.  chunks = 2.
i = 4:  max = 4.  4 == 4?  YES.  chunks = 3.

Return 3.  ✓  (Chunks: [0], [3, 1, 2], [4].)
```

---

## 9. Common pitfalls

1. **Initializing `max_so_far = 0`.** If `arr[0] = 0`, then `max_so_far` would already be 0 before reading anything, and you'd accidentally count a chunk before processing index 0. Use `-1` (or `INT_MIN`) as the sentinel.

2. **Assuming `arr` may NOT be a permutation of `0..n-1`.** The running-max trick crucially depends on this assumption. For the general version (LeetCode 768 — "Max Chunks to Make Sorted II"), arrays can have duplicates and arbitrary values. There the algorithm is different (use a monotonic stack — different problem).

3. **Using `>` instead of `==` in the chunk-boundary check.** The condition is strictly `max_so_far == i`. `max_so_far > i` (which can't happen if we're walking a permutation in this prefix) wouldn't mean anything different — but `max_so_far < i` is impossible because we've seen `i + 1` distinct non-negative values in `arr[0..i]`, so the max is at least... wait, the max is just `max_so_far` and could be less than `i` in principle. Actually for a permutation of `0..n-1`, `max(arr[0..i])` could be less than `i` if some larger values come after — e.g., `arr = [0, 1, 2]`, at `i = 0`, max is 0; at `i = 1`, max is 1; at `i = 2`, max is 2. Always equal. In general the running max is always `≥ i`? Hmm, not for `[2, 0, 1]`: at `i = 0` max is 2 > 0; at `i = 1` max is 2 > 1; at `i = 2` max is 2 = 2. So `max ≥ i` here, but not necessarily for non-permutations. For permutations, `max ≥ i` is the natural state, with `max == i` being the special "frontier matches" moment.

4. **Forgetting that "chunks" counts boundaries, not gaps.** A chunk ending at index `i` means we COULD split here. If we always split when we can, we maximize the chunk count. The algorithm increments `chunks` exactly when the boundary IS valid.

5. **Trying to be too clever with sorting.** Some candidates immediately think "sort and compare" — but that's O(n log n) and misses the elegant O(n) running-max insight. The trick is structural, not computational.

---

## 10. The shape — running-max invariants elsewhere

The "scan and track an invariant that flips when the array passes a structural checkpoint" pattern shows up in many problems. The checkpoint varies, but the technique is the same.

| Problem | Running invariant | Action at checkpoint |
|---|---|---|
| **This problem** (Max Chunks I) | `max(arr[0..i]) == i` for permutation | count chunks |
| **Max Chunks II** (LC #768) | monotonic stack of segment maxes | merge segments if violation |
| **Longest Mountain in Array** | "currently ascending" / "currently descending" | record mountain length on flip |
| **Best Time to Buy and Sell Stock** | min price so far | compute profit at each day |
| **Container With Most Water** | running max area while two-pointer walks | record best |
| **Maximum Subarray (Kadane)** | running sum (reset on negative) | record best |
| **Sliding Window Maximum** | deque of running max indices | output deque's front per step |

**Pattern to internalize:**

> "Walk the array left-to-right. At each step, update a small invariant (running max, running min, running sum, etc.). When the invariant satisfies some structural condition, record a result. Single pass, O(1) extra state."

The trick is **figuring out what invariant to track**. That's problem-specific, but the SHAPE — single pass + running invariant + checkpoint detection — is universal.

---

> **Self-check — the question to ask next time.**
>
> When a problem asks you to **partition / split / break / count groups** in an array, before reaching for nested loops or recursion, ask:
>
> > **"Is there a running invariant (max, min, sum, count) that I can check at each index? Does the invariant being in some specific state mean a partition boundary can occur here?"**
>
> If yes, you've turned a "consider all splits" problem (exponential) into a "single pass with checkpoint detection" problem (linear).

---

## Cross-references

- **Reference card (post-mastery):** [`../Max_Chunks_To_Make_Sorted.md`](../Max_Chunks_To_Make_Sorted.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Running_Sum_of_1D_Array.md`](./Running_Sum_of_1D_Array.md) (different running-invariant: running sum)
  - [`Richest_Customer_Wealth.md`](./Richest_Customer_Wealth.md) (running-max as a way to find the best)
  - Coming later in Stack topic: Largest Rectangle in Histogram (monotonic stack — Max Chunks II uses the same technique)
