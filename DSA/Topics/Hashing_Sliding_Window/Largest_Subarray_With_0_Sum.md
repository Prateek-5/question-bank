# Largest Subarray With 0 Sum

**Problem Link:**
<a href="https://www.geeksforgeeks.org/find-the-largest-subarray-with-0-sum/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/find-the-largest-subarray-with-0-sum/</a>

**Topic:**
Hashing / Sliding Window

----------------------------------------

## Step 1: Read the Problem

Given an integer array (may contain negatives), find the **length of the longest contiguous subarray** whose elements sum to 0.

Example: `[15, -2, 2, -8, 1, 7, 10, 23]`.

Subarrays summing to 0:
- `[-2, 2]` (indices 1-2): sum 0, length 2.
- `[-2, 2, -8, 1, 7]` (indices 1-5): sum = -2+2-8+1+7 = 0. Length 5.

Longest: **5**.

----------------------------------------

## Step 2: Brute Force

For each starting index i, accumulate sum as we extend j. If sum ever hits 0, record length j - i + 1. Track max.

```
for i in 0..n-1:
    s = 0
    for j in i..n-1:
        s += arr[j]
        if s == 0: best = max(best, j - i + 1)
```

O(n²). Fine for small inputs. For n ≥ 10^5, slow.

The inefficiency: we re-accumulate sum for each i. Can we share work?

----------------------------------------

## Step 3: Prefix Sums

Define prefix sum `P[i] = arr[0] + arr[1] + ... + arr[i-1]`. So `P[0] = 0`.

Sum of subarray arr[l..r] = P[r+1] - P[l].

A subarray sums to 0 iff `P[r+1] == P[l]`. So we're looking for **two equal prefix sums** — the subarray between them (exclusive of l, inclusive through r) has sum 0.

To maximize length r - l + 1 = (r + 1) - l, we want to find two indices in the prefix-sum sequence with the **same value**, maximally far apart.

Equivalent problem: given a sequence `P[0], P[1], ..., P[n]`, find the pair (i, j) with P[i] == P[j] and j - i maximal.

----------------------------------------

## Step 4: Hashmap of First Occurrences

Walk through prefix sums. For each `P[i]`:
- If we've seen `P[i]` before at index `first[P[i]]`, the subarray between those positions sums to 0. Length = i - first[P[i]].
- If we haven't seen `P[i]`, record `first[P[i]] = i`.

Why "first occurrence"? Because we want the longest subarray. Given two occurrences of the same prefix sum, the earlier index pairs with the current one to give a longer subarray.

```
first = {0: -1}   # prefix sum 0 at "index -1" (representing empty prefix)
sum = 0
best = 0

for i in 0..n-1:
    sum += arr[i]
    if sum in first:
        best = max(best, i - first[sum])
    else:
        first[sum] = i

return best
```

The trick `first[0] = -1` handles the case where the subarray starts from index 0. The prefix sum before any element is 0, conceptually at index -1.

----------------------------------------

## Step 5: Trace on the Example

`arr = [15, -2, 2, -8, 1, 7, 10, 23]`.

```
first = {0: -1}. sum = 0. best = 0.

i=0, arr[0]=15. sum = 15. Not in map. first[15] = 0.
i=1, arr[1]=-2. sum = 13. Not in map. first[13] = 1.
i=2, arr[2]=2. sum = 15. In map at 0. best = max(0, 2 - 0) = 2.
i=3, arr[3]=-8. sum = 7. Not in map. first[7] = 3.
i=4, arr[4]=1. sum = 8. Not in map. first[8] = 4.
i=5, arr[5]=7. sum = 15. In map at 0. best = max(2, 5 - 0) = 5.
i=6, arr[6]=10. sum = 25. Not in map. first[25] = 6.
i=7, arr[7]=23. sum = 48. Not in map. first[48] = 7.
```

Return 5. ✓

Notice at i = 5, we found sum = 15 which was first seen at i = 0. The subarray from i=1 to i=5 (indices 1, 2, 3, 4, 5) sums to 0, length 5. ✓

----------------------------------------

## Step 6: Why "First Occurrence" Specifically

Suppose we stored the **latest** index instead. For two prefix sums equal to, say, 15 — at indices 0 and 2 — we'd store index 2. Then at i = 5 (also prefix sum 15), we'd compute 5 - 2 = 3. But the real longest subarray with sum 0 is between index 0 and 5 (length 5).

Storing first occurrence gives us maximum span. Storing latest would give shortest span. First wins.

----------------------------------------

## Step 7: Sentinel `first[0] = -1`

The sentinel is important. Consider `arr = [1, 2, -3, 4]`. Prefix sums: 1, 3, 0, 4.

Subarray arr[0..2] = [1, 2, -3] sums to 0. Length 3.

Without the sentinel:
- i=0, sum=1. first[1]=0.
- i=1, sum=3. first[3]=1.
- i=2, sum=0. Not in map. first[0]=2.
- i=3, sum=4. Not in map. first[4]=3.

best stays 0. Wrong!

With the sentinel `first[0] = -1`:
- i=2, sum=0. In map at -1. best = 2 - (-1) = 3. ✓

The sentinel captures "the subarray starts at the beginning."

----------------------------------------

## Step 8: Name It

**Prefix sum + hashmap of first occurrence.** A ubiquitous technique for "longest subarray with some sum-based property." Related:
- Subarray Sum Equals K (count or detect).
- Longest Subarray with Equal 0s and 1s (convert 0s to -1s, find 0-sum subarrays).
- Contiguous Array with equal count of two values.

Whenever a contiguous-subarray question maps to "equal prefix values," this pattern applies.

----------------------------------------

## Step 9: Complexity

Time: **O(n)** — single pass, O(1) per hashmap op.
Space: **O(n)** for the hashmap.

----------------------------------------

## Step 10: C++ Implementation

```cpp
int maxLen(vector<int>& arr) {
    unordered_map<int, int> first;
    first[0] = -1;   // sentinel: empty prefix has sum 0 "at index -1"
    int sum = 0;
    int best = 0;

    for (int i = 0; i < (int)arr.size(); ++i) {
        sum += arr[i];
        auto it = first.find(sum);
        if (it != first.end()) {
            best = max(best, i - it->second);
        } else {
            first[sum] = i;
        }
    }
    return best;
}
```

Clean 10 lines. Running sum + hashmap = length of longest subarray with sum 0.

----------------------------------------

## Step 11: Follow-up Questions

- **Longest subarray with sum k.** Replace the check: look for `sum - k` in the map instead of `sum`.
- **Count all subarrays with sum 0 (not longest).** Accumulate counts instead of tracking first occurrence.
- **Longest subarray with sum ≥ threshold.** Harder; involves sorted prefix sums or sliding window for non-negatives.
- **Longest with sum divisible by k.** Use `sum % k` as the hashmap key (mind negative mod).
- **Longest with equal 0s and 1s.** Replace 0s with -1s, then find longest zero-sum subarray.
- **Dynamic updates to arr.** Hashmap technique doesn't trivially handle updates; use a segment tree.
