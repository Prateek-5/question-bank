# Unique Paths — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Unique_Paths.md`](../Unique_Paths.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/unique-paths/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/unique-paths/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: `paths(i, j) = paths(i-1, j) + paths(i, j-1)`. THE grid-DP template — same "what was my last move?" trick as Climbing Stairs, now in 2D. Closed-form combinatorial: `C(m+n-2, m-1)`, but the DP generalizes (Unique Paths II, Min Path Sum, etc.).**

**Map of this file (9 sections):**

1. Read the problem
2. Hand-fill a small grid
3. The recurrence
4. Code (2D + 1D rolling)
5. Trace it
6. Closed-form combinatorial
7. Common pitfalls
8. The shape — grid DP
9. Self-check

---

## 1. Read the problem

`m × n` grid. Start at top-left `(0, 0)`. Reach bottom-right `(m-1, n-1)`. You can only move RIGHT or DOWN. How many distinct paths?

**Examples:**

- m=3, n=2 → **3** (paths: RDD, DRD, DDR).
- m=3, n=7 → **28**.

---

## 2. Hand-fill a small grid

3×3 grid. Each cell `(i, j)` shows the number of paths from (0,0) to that cell.

- (0, j) for any j: only "all rights" — 1 path each. Top row = `[1, 1, 1]`.
- (i, 0) for any i: only "all downs" — 1 path each. Left column = 1, 1, 1.
- (1, 1): comes from (0, 1) or (1, 0). 1 + 1 = 2.
- (1, 2): from (0, 2) or (1, 1). 1 + 2 = 3.
- (2, 1): from (1, 1) or (2, 0). 2 + 1 = 3.
- (2, 2): from (1, 2) or (2, 1). 3 + 3 = 6.

Table:
```
1 1 1
1 2 3
1 3 6
```

Pascal's triangle on its side — a hint that the closed form is binomial.

---

## 3. The recurrence

> **Mini-refresher: same "what was my last move?" trick, now in 2D.**
>
> To arrive at (i, j) you came from either:
> - (i-1, j) by moving DOWN.
> - (i, j-1) by moving RIGHT.
>
> Disjoint, exhaustive. So:
>
> ```
> paths(i, j) = 1                          if i == 0 or j == 0  (edge row/col)
>             = paths(i-1, j) + paths(i, j-1)   otherwise
> ```
>
> Answer: `paths(m-1, n-1)`.

---

## 4. Code (2D + 1D rolling)

**C++ — full 2D table:**

```cpp
int uniquePaths(int m, int n) {
    vector<vector<int>> dp(m, vector<int>(n, 1));
    for (int i = 1; i < m; ++i)
        for (int j = 1; j < n; ++j)
            dp[i][j] = dp[i-1][j] + dp[i][j-1];
    return dp[m-1][n-1];
}
```

**C++ — 1D rolling (O(n) space):**

```cpp
int uniquePaths(int m, int n) {
    vector<int> dp(n, 1);
    for (int i = 1; i < m; ++i)
        for (int j = 1; j < n; ++j)
            dp[j] += dp[j - 1];   // dp[j] is "from above"; dp[j-1] is "from left"
    return dp[n - 1];
}
```

Complexity: **O(m · n)** time. Space **O(n)** (rolling), **O(m·n)** (full).

---

## 5. Trace it (1D version for m=3, n=3)

```
Init: dp = [1, 1, 1].   (top row)

Row i=1:
  j=1: dp[1] += dp[0] → 1+1 = 2. dp = [1, 2, 1].
  j=2: dp[2] += dp[1] → 1+2 = 3. dp = [1, 2, 3].

Row i=2:
  j=1: dp[1] += dp[0] → 2+1 = 3. dp = [1, 3, 3].
  j=2: dp[2] += dp[1] → 3+3 = 6. dp = [1, 3, 6].

Return dp[2] = 6.  ✓
```

After row k, dp = row k of the 2D table. The trick: when processing row i, `dp[j]` BEFORE update equals "from above" (row i-1), and `dp[j-1]` AFTER its update equals "from left" (row i, column j-1). The order (j from left to right) ensures this.

---

## 6. Closed-form combinatorial

> **Mini-refresher: each path has (m-1) downs and (n-1) rights.**
>
> Total moves: m + n - 2. Choose which are downs: `C(m+n-2, m-1)`.
>
> Same answer in O(min(m, n)) time, O(1) space:
>
> ```cpp
> long long r = 1;
> for (int i = 1; i < m; ++i) r = r * (n - 1 + i) / i;
> return (int)r;
> ```

Beautiful, but doesn't extend to obstacles or weighted cells. DP is more reusable.

---

## 7. Common pitfalls

1. **Initializing dp[0][0] = 0.** It's 1 (one way to be at the start).
2. **Allocating m*n when O(n) suffices.** Just track one row, update left-to-right.
3. **Wrong axis ordering.** `dp[i-1][j]` is the cell ABOVE; `dp[i][j-1]` is the cell to the LEFT. Don't swap.
4. **Trying the closed form for Unique Paths II (with obstacles).** The combinatorial formula breaks; DP is necessary.
5. **Integer overflow.** For m=n=23, paths exceed 2^32. Use `long long` (or Python's bignum).
6. **Off-by-one with grid bounds.** Grid is `m × n` → indices 0..m-1 and 0..n-1. The TARGET is `dp[m-1][n-1]`.

---

## 8. The shape — grid DP

The pattern: **`dp[i][j] = combine(dp[i-1][j], dp[i][j-1])` (+ maybe more).**

| Problem | Combine |
|---|---|
| **This problem** | sum (counting) |
| Unique Paths II | sum but 0 at obstacles |
| Minimum Path Sum | min + grid[i][j] |
| Maximum Path Sum | max + grid[i][j] |
| Cherry Pickup | two paths interlocked |
| Edit Distance | `dp[i-1][j-1]` (match) or 1 + min(...) |
| Longest Common Subsequence | `dp[i-1][j-1] + 1` or max(...) |

**Pattern to internalize:**

> "Grid DP: `dp[i][j] = combine(dp[i-1][j], dp[i][j-1], maybe dp[i-1][j-1])`. The 'last move' technique gives the recurrence. Rolling row collapses to O(n) space."

---

## 9. Self-check

> **The question to ask next time:**
>
> > **"What was my last move to arrive at (i, j)? From (i-1, j)? From (i, j-1)? Maybe diagonal? Combine those subproblems."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Unique_Paths.md`](../Unique_Paths.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Climbing_Stairs.md`](./Climbing_Stairs.md), [`Maximum_Subarray.md`](./Maximum_Subarray.md).
  - Coming next: [`Unique_Paths_II.md`](./Unique_Paths_II.md), [`Minimum_Path_Sum.md`](./Minimum_Path_Sum.md), [`Triangle.md`](./Triangle.md).
