# Triangle — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Triangle.md`](../Triangle.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/triangle/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: BOTTOM-UP DP. Start at the last row (best-from-here is the cell's own value); roll upward via `dp[j] = triangle[i][j] + min(dp[j], dp[j+1])`. A single 1D array of size n suffices.**

**Map of this file (8 sections):**

1. Read the problem
2. Why bottom-up
3. The recurrence
4. The 1D in-place trick
5. Code
6. Trace it
7. Common pitfalls
8. The shape — bottom-up path DP

---

## 1. Read the problem

A triangle of numbers — row i has i+1 entries. Starting at the top, each move goes to one of two adjacent positions in the next row (`j` or `j+1`). Minimize the sum along the path top-to-bottom.

**Example:**
```
   [2]
  [3, 4]
 [6, 5, 7]
[4, 1, 8, 3]
```

Best path: 2 → 3 → 5 → 1 = **11**.

---

## 2. Why bottom-up

> **Mini-refresher: bottom-up = build from base cases upward.**
>
> Top-down recursion: from (0, 0), recurse to two children. Exponential without memo.
>
> Bottom-up: start at the last row (each cell's best-from-here is itself), then for each row above, combine each cell with the BEST of its two children below. Result: O(n²) time, O(n) space.
>
> Bottom-up wins here because the last row's answers are TRIVIAL (just the cell values), and each row above depends only on the row BELOW.

---

## 3. The recurrence

Let `best(i, j)` = minimum path sum from (i, j) DOWN to any cell in the last row.

```
best(last_row, j) = triangle[last_row][j]
best(i, j) = triangle[i][j] + min(best(i+1, j), best(i+1, j+1))
```

Answer: `best(0, 0)`.

---

## 4. The 1D in-place trick

> **Mini-refresher: a single array of size n (rows) suffices.**
>
> Initialize `dp` as a copy of the last row. For each row i above (from bottom to top), update each `dp[j]` IN PLACE:
>
> ```
> dp[j] = triangle[i][j] + min(dp[j], dp[j + 1])
> ```
>
> This works because we process j from 0 to i (the row's length):
> - `dp[j]` BEFORE this update still holds row (i+1)'s value (the cell directly below).
> - `dp[j+1]` holds row (i+1)'s value at column j+1 (the lower-right child).
>
> AFTER the update, `dp[j]` holds row i's value — but `dp[j+1]` is still row (i+1)'s (untouched this iteration). So the next iteration (j+1) reads `dp[j+1]` and `dp[j+2]` — both still row (i+1). Safe.

---

## 5. Code

**C++:**

```cpp
int minimumTotal(vector<vector<int>>& triangle) {
    vector<int> dp(triangle.back().begin(), triangle.back().end());
    for (int i = (int)triangle.size() - 2; i >= 0; --i) {
        for (int j = 0; j <= i; ++j) {
            dp[j] = triangle[i][j] + min(dp[j], dp[j + 1]);
        }
    }
    return dp[0];
}
```

**Python:**

```python
def minimumTotal(triangle):
    dp = triangle[-1][:]
    for i in range(len(triangle) - 2, -1, -1):
        for j in range(i + 1):
            dp[j] = triangle[i][j] + min(dp[j], dp[j + 1])
    return dp[0]
```

Complexity: **O(n²)** time (total cells), **O(n)** space.

---

## 6. Trace it

```
triangle = [[2], [3,4], [6,5,7], [4,1,8,3]]

dp = [4, 1, 8, 3]   (last row)

Row 2 [6, 5, 7]:
  j=0: dp[0] = 6 + min(4, 1) = 7.
  j=1: dp[1] = 5 + min(1, 8) = 6.
  j=2: dp[2] = 7 + min(8, 3) = 10.
  dp = [7, 6, 10, 3]   (last value ignored from now on)

Row 1 [3, 4]:
  j=0: dp[0] = 3 + min(7, 6) = 9.
  j=1: dp[1] = 4 + min(6, 10) = 10.
  dp = [9, 10, ...]

Row 0 [2]:
  j=0: dp[0] = 2 + min(9, 10) = 11.

Return dp[0] = 11.  ✓
```

---

## 7. Common pitfalls

1. **Computing top-down.** Forces a 2D DP with parent dependencies; less elegant. Bottom-up uses 1D in place.
2. **Updating `dp[j]` then reading `dp[j+1]` later as if it were row i.** The trick relies on `dp[j+1]` STILL being row (i+1)'s value when we compute j. Don't update right-to-left.
3. **Out-of-bounds on `dp[j+1]` for j = i.** When j = i (last column of row i), `dp[i+1]` is OUTSIDE the relevant range. But the array still holds a value (from initialization or stale), and we only access valid indices because we loop `j ∈ [0, i]` — `dp[i+1]` exists because dp has size n.
4. **Returning the wrong cell.** Answer is `dp[0]` (the top of the triangle), not `dp[-1]` or `dp[n-1]`.
5. **Modifying the triangle directly.** Possible but mutates input; the 1D array is cleaner.

---

## 8. The shape — bottom-up path DP

The pattern: **start at base cases, work backward toward the answer.**

| Problem | Base cases |
|---|---|
| **This problem** | last row = own values |
| Dungeon Game | bottom-right corner (HP constraint) |
| House Robber | f(n-1) = a[n-1], f(n-2) = max(a[n-1], a[n-2]) |
| Egg Drop | base: f(0, _) = 0, f(_, 0) = 0 |
| Edit Distance | dp[i][0] = i, dp[0][j] = j |
| Wildcard Matching | dp[0][0] = true, dp[0][j] = pattern starts with * |

**Pattern to internalize:**

> "When the problem has a CLEAR TERMINAL state (last row of triangle, bottom of grid), bottom-up DP often gives a clean iterative solution with O(n) (or O(n²)) space."

---

> **Self-check — the question to ask next time.**
>
> When choosing top-down vs bottom-up DP, ask:
>
> > **"Is the base case TRIVIAL at a specific end (last row, leaf, smallest input)? If so, bottom-up is usually cleaner — often allowing O(n) space via in-place updates."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Triangle.md`](../Triangle.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Minimum_Path_Sum.md`](./Minimum_Path_Sum.md), [`Unique_Paths.md`](./Unique_Paths.md).
  - Coming next: [`Longest_Increasing_Subsequence.md`](./Longest_Increasing_Subsequence.md), [`Longest_Common_Subsequence.md`](./Longest_Common_Subsequence.md).
