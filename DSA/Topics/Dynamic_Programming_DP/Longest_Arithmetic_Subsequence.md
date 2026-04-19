# Longest Arithmetic Subsequence

**Problem Link:**
https://leetcode.com/problems/longest-arithmetic-subsequence/

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: What's an Arithmetic Subsequence?

A **subsequence** keeps order but can skip elements. **Arithmetic** means consecutive elements have a constant **difference**.

Example: `[9, 4, 7, 2, 10]`.
- `[9, 4]`: difference -5. AP of length 2.
- `[4, 7, 10]`: differences 3, 3. AP of length 3. ✓
- `[9, 7, 5]`: but 5 isn't in the array. Not valid.
- `[4, 10]`: difference 6. AP of length 2.

Longest AP subsequence: `[4, 7, 10]`, length **3**.

Return the length of the longest AP subsequence.

Note: any 2-element subsequence is trivially arithmetic (only one difference). So the answer is always ≥ 2 for n ≥ 2.

----------------------------------------

## Step 2: Brute Force

Enumerate every subsequence and check if it's arithmetic. That's 2^n subsequences. Way too many.

Better: for each pair (i, j) with i < j, that pair defines an AP with difference `d = a[j] - a[i]`, length 2 so far. We extend by looking for a k > j with `a[k] = a[j] + d`.

Enumerating pairs is O(n²). For each, searching for extensions could be linear — total O(n³). Slow for n = 1000+.

----------------------------------------

## Step 3: DP by (Index, Difference)

Here's the right framing. Let:

`dp[j][d]` = the length of the longest AP ending at index j with common difference d.

If we know this for every (j, d), the answer is `max dp[j][d]` over all j, d.

Recurrence: to extend an AP ending at j with difference d, we need some earlier i < j with `a[j] - a[i] = d`. The AP ending at i with difference d has length `dp[i][d]`, and appending a[j] gives `dp[i][d] + 1`.

If no such i exists, we're starting fresh — length 2 (the pair (i, j) for some i that creates this d).

```
for j in 0..n-1:
    for i in 0..j-1:
        d = a[j] - a[i]
        dp[j][d] = dp[i][d] + 1 if dp[i][d] exists else 2
```

Hm actually the base case should be: if dp[i][d] exists, dp[j][d] = dp[i][d] + 1. If not, dp[j][d] = 2 (just the pair (i, j) is an AP of length 2).

O(n²) pairs, each O(1) work. Total **O(n²)**.

The twist: `d` can be any integer, so we can't use a 2D array directly. Use a hashmap: `dp[j]` is a map from difference to length.

----------------------------------------

## Step 4: Trace on `[9, 4, 7, 2, 10]`

```
dp[0]: {}
dp[1]: pair (0, 1) gives d = 4-9 = -5. dp[1][-5] = 2.
dp[2]: 
  pair (0, 2): d = 7-9 = -2. dp[0] has no -2. dp[2][-2] = 2.
  pair (1, 2): d = 7-4 = 3. dp[1] has no 3. dp[2][3] = 2.
dp[3]:
  pair (0, 3): d = 2-9 = -7. dp[3][-7] = 2.
  pair (1, 3): d = 2-4 = -2. dp[1] no -2. dp[3][-2] = 2.
  pair (2, 3): d = 2-7 = -5. dp[2] no -5. dp[3][-5] = 2.
dp[4]:
  pair (0, 4): d = 10-9 = 1. dp[4][1] = 2.
  pair (1, 4): d = 10-4 = 6. dp[4][6] = 2.
  pair (2, 4): d = 10-7 = 3. dp[2] has 3! dp[4][3] = dp[2][3] + 1 = 3.
  pair (3, 4): d = 10-2 = 8. dp[4][8] = 2.
```

Max across all: 3 (at dp[4][3]). ✓

The winning AP is `[4, 7, 10]`, with difference 3, ending at index 4.

----------------------------------------

## Step 5: Why This Recurrence Captures Every AP

Any AP subsequence has a last element (index j) and a common difference (d). Its length is either:
- 2 (just two elements), or
- `previous length + 1` where "previous" is the AP ending at some earlier index with the same difference.

Our recurrence considers both: `dp[i][d] + 1` extends a previous AP; `2` handles a fresh pair. We take the max across all i < j.

Every AP ending at j with difference d is accounted for.

----------------------------------------

## Step 6: Name It

**2D DP indexed by (ending index, common difference)**. The hashmap on the second dimension handles the (potentially large) range of possible differences.

Same template applies to:
- Arithmetic Slices II (count APs, not longest).
- Longest Geometric Subsequence (replace difference with ratio).
- Longest Increasing Subsequence with a twist (like fixed-differences).

----------------------------------------

## Step 7: Complexity

Time: **O(n²)** — two nested loops, each pair O(1) hash operations.
Space: **O(n²)** — each of n maps can hold up to n entries.

Space-optimization via a single 2D map `dp[j][d]` doesn't help asymptotically since we need access to dp[i][d] for all i < j.

For n = 1000, O(n²) = 10^6 — fast.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int longestArithSeqLength(vector<int>& nums) {
    int n = nums.size();
    vector<unordered_map<int, int>> dp(n);   // dp[j][d]: length ending at j with diff d
    int best = 2;   // at least a pair

    for (int j = 1; j < n; ++j) {
        for (int i = 0; i < j; ++i) {
            int d = nums[j] - nums[i];
            // Extend AP ending at i (if exists), else start pair of length 2.
            auto it = dp[i].find(d);
            int len = (it != dp[i].end()) ? it->second + 1 : 2;
            dp[j][d] = max(dp[j][d], len);
            best = max(best, dp[j][d]);
        }
    }
    return best;
}
```

Critical details:
- `dp[j][d] = max(dp[j][d], len)` — there might be multiple i's giving the same d; take the max.
- Track `best` globally across all (j, d).
- Initialize `best = 2` since any pair of elements is trivially an AP of length 2.

----------------------------------------

## Step 9: Follow-up Questions

- **Count of all AP subsequences (not just longest).** Count per (j, d) and sum.
- **Longest AP subarray (contiguous).** Easier — linear scan.
- **Longest AP with a specific target difference.** Drop the inner loop's choice of d; fix d upfront; O(n) with hashmap.
- **Longest geometric subsequence.** Same template with ratio instead of difference. Be careful with division / handle 0.
- **What if n is huge and diffs have small range?** Use `vector<vector<int>>` indexed by shifted difference — might be faster than hashmap.
- **Return the actual subsequence.** Track parent pointers (which i gave the winning dp[j][d]); walk back.
