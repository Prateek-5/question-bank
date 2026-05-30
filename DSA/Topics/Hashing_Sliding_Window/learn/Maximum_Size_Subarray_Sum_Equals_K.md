# Maximum Size Subarray Sum Equals K — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Maximum_Size_Subarray_Sum_Equals_K.md`](../Maximum_Size_Subarray_Sum_Equals_K.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/maximum-size-subarray-sum-equals-k/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/maximum-size-subarray-sum-equals-k/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. This is **the "length variant" of Subarray Sum Equals K** — the data structure is the same (prefix sum + hashmap), but the **value stored** in the hashmap changes from "count of occurrences" to "first occurrence index." That difference matters. **Read [`Subarray_Sum_Equals_K.md`](./Subarray_Sum_Equals_K.md) first** if you haven't — this file assumes the prefix-sum + complement-lookup foundation.

**Map of this file (9 short sections):**

1. Read the problem
2. Why this differs from Subarray Sum Equals K (count vs length)
3. The pivot — prefix sum and the complement
4. Why "first occurrence" instead of "count"
5. The seed `first[0] = -1` and why
6. Code
7. Trace it
8. Common pitfalls
9. The shape — first-occurrence storage for maximization

---

## 1. Read the problem

You're given an integer array `nums` (possibly with negatives) and an integer `k`. Find the **length of the longest contiguous subarray** whose sum equals `k`. Return 0 if no such subarray exists.

**Example 1:** `nums = [1, -1, 5, -2, 3]`, `k = 3`.

Possible subarrays summing to 3:

- `[1, -1, 5, -2]`: sum = `1 - 1 + 5 - 2 = 3`. Length 4.
- `[5, -2]`: sum = 3. Length 2.
- `[3]`: sum = 3. Length 1.

Longest: **4**.

**Example 2:** `nums = [-2, -1, 2, 1]`, `k = 1`.

- `[-1, 2]`: sum = 1. Length 2.
- `[1]`: sum = 1. Length 1.

Longest: **2**.

---

## 2. Why this differs from Subarray Sum Equals K (count vs length)

**Subarray Sum Equals K** (LeetCode #560) asks for the COUNT of subarrays with sum `k`.

**This problem** (LeetCode #325 / variants) asks for the LENGTH of the LONGEST subarray with sum `k`.

The setup is identical:

- Both use prefix sums.
- Both use a hashmap of "prefix sum → some value."

What changes is the **value stored**:

| Problem | Hashmap stores | Purpose |
|---|---|---|
| Subarray Sum Equals K | `{prefix-sum → count of occurrences}` | sum up counts of complement matches |
| **This problem** | `{prefix-sum → FIRST index where it occurred}` | compute longest subarray when complement matches |

We'll see in section 4 why "first occurrence" is the right thing to store for maximizing length.

> **Mini-refresher: prefix sums (in case you skipped Subarray Sum Equals K).**
>
> Define `prefix[i]` as `nums[0] + nums[1] + ... + nums[i-1]`. So `prefix[0] = 0` (empty prefix).
>
> The sum of `nums[l..r]` (inclusive, both 0-indexed) is `prefix[r+1] − prefix[l]`. Hence "subarray summing to k" means "two prefix sums differing by k" — formally `prefix[r+1] − prefix[l] = k`, or equivalently `prefix[l] = prefix[r+1] − k`.

---

## 3. The pivot — prefix sum and the complement

Walk forward through `nums`. At each position `r`, we've computed `current_prefix = prefix[r+1] = nums[0] + ... + nums[r]`.

The question "is there a subarray ending at position `r` summing to `k`?" becomes: **"Is `current_prefix − k` a value that has appeared as an earlier prefix sum (`prefix[l]` for some `l ≤ r`)?"**

If yes, and the earliest such `l` is `first[current_prefix − k]`, then the subarray from index `l` to `r` sums to `k`, with length `r − l + 1`, but since we store `first[value] = l − 1` (the "index of `prefix[l]`"), actually we have...

OK let me be very careful with the indexing. Let me re-state cleanly.

If we DEFINE `first` to map `prefix sum value → index r at which that prefix first appeared while walking nums` (i.e., the index in `nums` at which the running sum became this value):

- When we walk position `r` of nums and update `current_prefix`, we're saying `current_prefix` is the sum from `nums[0]` to `nums[r]`.
- We check `complement = current_prefix − k`. If this was first seen at some earlier `r' < r` (meaning the running sum reached `complement` after processing `nums[0..r']`), then `nums[r'+1..r]` sums to `current_prefix − complement = k`. Length: `r − r'`.

So the recipe:

```
seed first[0] = -1                # the empty prefix "sum 0" is conceptually at index -1
current_prefix = 0
best = 0

for r in 0..n-1:
    current_prefix += nums[r]
    complement = current_prefix - k

    if complement is in first:
        candidate_length = r - first[complement]
        best = max(best, candidate_length)

    if current_prefix not in first:
        first[current_prefix] = r       # store FIRST occurrence only

return best
```

Two distinguishing details:

1. **`if current_prefix not in first`** — we only store the FIRST occurrence (next section).
2. **`first[0] = -1`** — the empty-prefix seed (section 5).

---

## 4. Why "first occurrence" instead of "count"

Suppose the same prefix sum value `v` occurs at indices 0 and 5. When we later encounter `complement = v` at index 9, which match gives the LONGEST subarray?

- If we use the index 0 match: length = `9 - 0 = 9`.
- If we use the index 5 match: length = `9 - 5 = 4`.

The earlier match gives a longer subarray. So we want **the FIRST occurrence**.

This is why we only insert a prefix sum into `first` if it's NOT already there — preserving the earliest position.

Contrast with Subarray Sum Equals K, where we want the COUNT of subarrays summing to `k`. There, each occurrence of `complement` gives a DIFFERENT starting position, so we count them all → increment per occurrence.

> **Pattern:** For COUNT problems → store frequency (increment per occurrence). For LONGEST-LENGTH problems → store first occurrence (don't overwrite). For SHORTEST-LENGTH problems → store latest occurrence (always overwrite).

---

## 5. The seed `first[0] = -1` and why

The seed handles subarrays that START at index 0.

Example: `nums = [3, 4, ...]`, `k = 7`. The subarray `[3, 4]` sums to 7. Walking:

```
r = 0: current_prefix = 3. complement = -4. Not in first. Don't record.
       first[3] = 0.
r = 1: current_prefix = 7. complement = 0. Is 0 in first?
       If we seeded first[0] = -1: YES. candidate length = 1 - (-1) = 2.  ✓
       If we DIDN'T seed: NO. We'd miss this subarray.   ✗
       first[7] = 1.
```

The seed represents "the empty prefix has sum 0, conceptually at position −1 (just before index 0)."

When the complement matches the seed, the subarray starts at index 0. Without the seed, we'd miss all such subarrays.

> **Mini-refresher: why `−1` and not `0` for the seed index?**
>
> The "empty prefix" is the prefix BEFORE processing any elements. If `first[0] = 0`, then when we match at index `r`, we'd compute `r − 0 = r`, but the actual subarray is from index 0 to r, inclusive, which has length `r + 1`. Off by one.
>
> By using `−1`, the formula `r − first[complement]` gives `r − (−1) = r + 1` — the correct length of `nums[0..r]`.

---

## 6. Code

**C++:**

```cpp
int maxSubArrayLen(vector<int>& nums, int k) {
    unordered_map<long long, int> first;
    first[0] = -1;                              // seed: empty prefix at "index -1"

    long long current_prefix = 0;
    int best = 0;

    for (int r = 0; r < (int)nums.size(); r++) {
        current_prefix += nums[r];

        long long complement = current_prefix - k;
        auto it = first.find(complement);
        if (it != first.end()) {
            best = max(best, r - it->second);   // length = r - first[complement]
        }

        // Only store the FIRST occurrence
        if (first.find(current_prefix) == first.end()) {
            first[current_prefix] = r;
        }
    }

    return best;
}
```

`long long` is used for `current_prefix` and `complement` to avoid overflow when sums exceed `int` range.

**Python:**

```python
def maxSubArrayLen(nums, k):
    first = {0: -1}                              # seed
    current_prefix = 0
    best = 0
    for r, x in enumerate(nums):
        current_prefix += x
        complement = current_prefix - k
        if complement in first:
            best = max(best, r - first[complement])
        if current_prefix not in first:          # first occurrence only
            first[current_prefix] = r
    return best
```

**JavaScript:**

```javascript
function maxSubArrayLen(nums, k) {
    const first = new Map([[0, -1]]);
    let current_prefix = 0, best = 0;
    for (let r = 0; r < nums.length; r++) {
        current_prefix += nums[r];
        const complement = current_prefix - k;
        if (first.has(complement)) {
            best = Math.max(best, r - first.get(complement));
        }
        if (!first.has(current_prefix)) {
            first.set(current_prefix, r);
        }
    }
    return best;
}
```

All O(n) time, O(n) space.

---

## 7. Trace it

**`nums = [1, -1, 5, -2, 3]`, `k = 3`:**

```
first = {0: -1}. current_prefix = 0. best = 0.

r = 0, nums[0] = 1:
    current_prefix = 1.
    complement = 1 - 3 = -2. Not in first.
    Add first[1] = 0.

r = 1, nums[1] = -1:
    current_prefix = 0.
    complement = 0 - 3 = -3. Not in first.
    0 is already in first (at -1). Don't overwrite.

r = 2, nums[2] = 5:
    current_prefix = 5.
    complement = 2. Not in first.
    Add first[5] = 2.

r = 3, nums[3] = -2:
    current_prefix = 3.
    complement = 0. IN first at -1.
    candidate length = 3 - (-1) = 4. best = 4.   ← longest so far
    Add first[3] = 3.

r = 4, nums[4] = 3:
    current_prefix = 6.
    complement = 3. IN first at 3.
    candidate length = 4 - 3 = 1. best still 4.
    Add first[6] = 4.

Return 4.  ✓
```

The key match happened at `r = 3`: the seed `first[0] = -1` matched with `complement = 0`, giving the longest subarray (from index 0 to 3, length 4).

**`nums = [-2, -1, 2, 1]`, `k = 1`:**

```
first = {0: -1}. current_prefix = 0.

r=0 (-2): cp=-2. comp=-3. miss. first[-2]=0.
r=1 (-1): cp=-3. comp=-4. miss. first[-3]=1.
r=2 (2):  cp=-1. comp=-2. HIT at 0. best = 2-0=2. first[-1]=2.
r=3 (1):  cp=0.  comp=-1. HIT at 2. best = max(2, 3-2)=2. cp=0 already in first, don't overwrite.

Return 2.  ✓
```

Subarray `nums[1..2] = [-1, 2]` sums to 1, length 2. Verified.

---

## 8. Common pitfalls

1. **Storing later occurrences (overwriting `first[v]` if `v` repeats).** This gives shorter subarrays, not longer. For length problems: **store only the first**.

2. **Forgetting the seed `first[0] = -1`.** Misses subarrays starting at index 0. Always seed.

3. **Confusing this with Subarray Sum Equals K.** Both use prefix sum + hashmap. Different problems:
   - Sum Equals K (count): hashmap value = frequency; accumulate counts.
   - Length variant (this): hashmap value = first index; track max length.

4. **Off-by-one in the length formula.** The length is `r - first[complement]`. Some candidates write `r - first[complement] + 1` thinking it's an inclusive count — but the seed `−1` already accounts for the `+1`, so the simple subtraction is correct.

5. **Using `int` instead of `long long` for the running sum.** For LeetCode constraints, sums can exceed `int` range. Cast to `long long`. (Same issue mentioned in Subarray Sum Equals K — easy to miss.)

6. **Initialization edge cases.** If `nums` is empty, return 0. The loop simply doesn't execute, so `best = 0` is correct without explicit guard.

---

## 9. The shape — first-occurrence storage for maximization

The "store first occurrence" trick generalizes to many "longest contiguous subarray with property X" problems:

| Problem | What's stored at first-occurrence | What property X |
|---|---|---|
| **This problem** (sum equals k) | `prefix-sum → first index` | sum = k |
| Largest Subarray With 0 Sum | `prefix-sum → first index` | sum = 0 |
| Longest Subarray Sums Divisible by K | `prefix-sum mod K → first index` | sum % k = 0 |
| Contiguous Array (equal 0s and 1s) | `running_difference → first index` (0 counted as -1, 1 as +1) | counts equal |
| Longest Substring Without Repeating Characters | `char → last index` (slightly different, but related) | no repeats in window |
| Longest substring with at most K distinct characters | (sliding window) | bounded distinct |

**Pattern to internalize:**

> "For **longest subarray with sum property**, use prefix-sum + hashmap with **first-occurrence storage**. The first occurrence pairs with the current position to give the longest possible matching subarray."
>
> The trio is:
> - **Count** problem → hashmap stores frequency.
> - **Longest length** problem → hashmap stores first occurrence (don't overwrite).
> - **Shortest length** problem → hashmap stores latest occurrence (always overwrite).

Knowing which to choose is the key skill — the data structure machinery is otherwise identical.

---

> **Self-check — the question to ask next time.**
>
> When you face a problem asking for the **LONGEST** subarray satisfying a sum-based property, before writing nested loops, ask:
>
> > **"Can I express this as 'two prefix sums in some relationship,' build a hashmap of prefix-sum → FIRST INDEX, and at each position check if the complement exists?"**
>
> If yes, you've turned O(n²) into O(n).

---

## Cross-references

- **Reference card (post-mastery):** [`../Maximum_Size_Subarray_Sum_Equals_K.md`](../Maximum_Size_Subarray_Sum_Equals_K.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Subarray_Sum_Equals_K.md`](./Subarray_Sum_Equals_K.md) — prereq; the count variant.
  - [`Largest_Subarray_With_0_Sum.md`](./Largest_Subarray_With_0_Sum.md) — same algorithm with `k = 0`.
  - Coming later: Continuous Subarray Sum (divisible by k) — uses `prefix mod k` instead of `prefix`.
