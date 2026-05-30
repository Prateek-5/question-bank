# Longest Increasing Subsequence — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Longest_Increasing_Subsequence.md`](../Longest_Increasing_Subsequence.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/longest-increasing-subsequence/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/longest-increasing-subsequence/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **The lesson: TWO solutions — `f(i)` = LIS ending at i (O(n²) DP) AND the PATIENCE SORTING / TAILS array (O(n log n) via binary search). The tails trick is gorgeous and worth committing to memory.**

**Map of this file (10 sections):**

1. Read the problem
2. The O(n²) DP — `f(i)` = LIS ending at i
3. Why O(n²) is wasteful
4. Patience sorting intuition
5. The `tails` array trick
6. Strict vs non-decreasing — lower_bound vs upper_bound
7. Code (both versions)
8. Trace it
9. Common pitfalls
10. The shape — subsequence DP

---

## 1. Read the problem

Given integer array `nums`, find the length of the LONGEST STRICTLY INCREASING SUBSEQUENCE. (Subsequence = drop elements, keep relative order; not necessarily contiguous.)

**Example:** `[10, 9, 2, 5, 3, 7, 101, 18]` → LIS `[2, 3, 7, 18]` or `[2, 3, 7, 101]` → **4**.

---

## 2. The O(n²) DP — `f(i)` = LIS ending at i

> **Mini-refresher: fix one endpoint of the subsequence.**
>
> `f(i)` = length of LIS that ENDS at index i.
>
> Transition: `f(i) = 1 + max(f(j))` over all `j < i` with `nums[j] < nums[i]`. If no such j, `f(i) = 1`.
>
> Answer: `max(f(i))` over all i.

```
f = [1] * n
for i in range(n):
    for j in range(i):
        if nums[j] < nums[i]:
            f[i] = max(f[i], f[j] + 1)
return max(f)
```

O(n²) time. Easy to code, easy to verify.

---

## 3. Why O(n²) is wasteful

At each i, we scan ALL previous indices. Most of that work is searching for "best LIS so far with last value < nums[i]." Sorting that info smarter would let us answer in O(log n).

---

## 4. Patience sorting intuition

> **Mini-refresher: patience sorting (card game).**
>
> Deal cards one by one. Place each card on the LEFTMOST pile whose top is ≥ the new card (so the pile's top is REPLACED, smaller-side-up). If no such pile, START a new pile to the right.
>
> Claim: **number of piles = LIS length.**

Why? Two short arguments:

- (LIS ≤ piles) Cards on the same pile are placed in DECREASING order — so any STRICTLY INCREASING subsequence picks at most one card per pile.
- (LIS ≥ piles) Each new pile's first card was placed BECAUSE no earlier pile's top accommodated it (i.e., it's > all previous piles' tops). So tracing one card per pile in placement order yields a strictly increasing subsequence of length = number of piles.

---

## 5. The `tails` array trick

> **Mini-refresher: only track each pile's TOP card.**
>
> Maintain `tails`, where `tails[k]` = top of pile (k+1). KEY INVARIANT: `tails` is always sorted ascending.
>
> For each `x` in nums:
> - Find leftmost index p with `tails[p] >= x` (use `lower_bound`).
> - If p == len(tails): push x (new pile).
> - Else: replace `tails[p] = x` (update that pile's top, making it smaller — leaves more room for future cards).
>
> At the end: `LIS length = len(tails)`.

Each operation is O(log n) via binary search → **O(n log n)** total.

NOTE: `tails` itself is NOT the LIS. It's a bookkeeping structure. (The values in `tails` at any moment might not form a valid subsequence of the input — only the LENGTH matches.)

---

## 6. Strict vs non-decreasing — lower_bound vs upper_bound

- **Strictly increasing** (this problem): use `lower_bound` (first index with `tails[i] >= x`). Replaces equal values.
- **Non-decreasing**: use `upper_bound` (first index with `tails[i] > x`). Allows equals to extend.

Get this wrong and the answer is off by the count of duplicates.

---

## 7. Code (both versions)

**C++ — O(n²) DP:**

```cpp
int lengthOfLIS_n2(vector<int>& nums) {
    int n = nums.size();
    vector<int> f(n, 1);
    int best = 1;
    for (int i = 1; i < n; ++i) {
        for (int j = 0; j < i; ++j) {
            if (nums[j] < nums[i]) f[i] = max(f[i], f[j] + 1);
        }
        best = max(best, f[i]);
    }
    return best;
}
```

**C++ — O(n log n) tails:**

```cpp
int lengthOfLIS(vector<int>& nums) {
    vector<int> tails;
    for (int x : nums) {
        auto it = lower_bound(tails.begin(), tails.end(), x);
        if (it == tails.end()) tails.push_back(x);
        else *it = x;
    }
    return tails.size();
}
```

**Python — tails:**

```python
from bisect import bisect_left
def lengthOfLIS(nums):
    tails = []
    for x in nums:
        p = bisect_left(tails, x)
        if p == len(tails):
            tails.append(x)
        else:
            tails[p] = x
    return len(tails)
```

Complexity: O(n²) or **O(n log n)** time. O(n) space.

---

## 8. Trace it

`nums = [10, 9, 2, 5, 3, 7, 101, 18]`.

```
x=10: tails empty → push. tails = [10].
x=9:  lower_bound(tails, 9) = 0 (10 ≥ 9). replace. tails = [9].
x=2:  lower_bound = 0. replace. tails = [2].
x=5:  lower_bound = 1 (past end). push. tails = [2, 5].
x=3:  lower_bound(tails, 3) = 1 (5 ≥ 3). replace. tails = [2, 3].
x=7:  lower_bound = 2 (past end). push. tails = [2, 3, 7].
x=101: lower_bound = 3 (past end). push. tails = [2, 3, 7, 101].
x=18: lower_bound(tails, 18) = 3 (101 ≥ 18). replace. tails = [2, 3, 7, 18].

len(tails) = 4.  ✓
```

Final `tails = [2, 3, 7, 18]` HAPPENS to be a valid LIS, but in general that's coincidence — `tails` is just a length-tracker.

---

## 9. Common pitfalls

1. **Returning `tails` as the LIS itself.** It's just bookkeeping — the LENGTH is correct, but the contents aren't generally a valid LIS.
2. **Using `upper_bound` for strictly increasing.** Wrong — duplicates would extend the LIS. Use `lower_bound`.
3. **For strictly increasing: missing the "equal" case.** With duplicates, `[1, 1, 1]` should give LIS = 1 (strict). `lower_bound` correctly REPLACES 1s without growing.
4. **Reconstructing actual LIS without parent pointers.** The tails array can't reconstruct directly. If asked for the sequence, augment with `parent[i]` during the placement step.
5. **Confusing with longest INCREASING SUBARRAY.** Subarray = contiguous, different (and easier) problem.

---

## 10. The shape — subsequence DP

The pattern: **dp[i] = best subsequence ending at i, defined by some monotonicity / property.**

| Problem | Property at i |
|---|---|
| **This problem (LIS)** | strictly increasing |
| Longest Non-Decreasing Subsequence | non-strict increasing |
| Longest Decreasing Subsequence | strictly decreasing (negate + LIS) |
| Longest Common Subsequence | LCS — different shape (2D) |
| Russian Doll Envelopes | 2D LIS with clever sort |
| Maximum Height by Stacking Cuboids | 3D LIS |
| Longest Arithmetic Subsequence | dp[i][diff] (3D) |

**Pattern to internalize:**

> "For LIS-like problems: O(n²) is `dp[i] = 1 + max(dp[j])` over valid j. O(n log n) is patience sorting with a `tails` array + binary search. Strict → `lower_bound`; non-strict → `upper_bound`."

---

> **Self-check — the question to ask next time.**
>
> When the problem says "longest subsequence with property X":
>
> > **"Define dp[i] = best ending at i. For O(n log n), can I maintain a sorted 'tails' array with binary search? Strict or non-strict? lower vs upper_bound."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Longest_Increasing_Subsequence.md`](../Longest_Increasing_Subsequence.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Triangle.md`](./Triangle.md), [`Maximum_Subarray.md`](./Maximum_Subarray.md).
  - Coming next: [`Longest_Arithmetic_Subsequence.md`](./Longest_Arithmetic_Subsequence.md), [`Russian_Doll_Envelopes.md`](./Russian_Doll_Envelopes.md), [`Longest_Common_Subsequence.md`](./Longest_Common_Subsequence.md).
