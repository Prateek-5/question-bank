# Unique Paths II — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Unique_Paths_II.md`](../Unique_Paths_II.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/unique-paths-ii/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/unique-paths-ii/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: same recurrence as Unique Paths, but OBSTACLES force `dp[i][j] = 0`. The combinatorial closed-form fails — only DP survives. Watch row/column propagation: an obstacle in the first row/column blocks everything after it.**

**Map of this file (8 sections):**

1. Read the problem
2. The recurrence + obstacle override
3. Edge cases: blocked endpoints, obstacle in border row/col
4. Code (2D + 1D)
5. Trace it
6. Why combinatorics fails
7. Common pitfalls
8. The shape — grid DP with forbidden cells

---

## 1. Read the problem

`m × n` grid where each cell is 0 (open) or 1 (obstacle). Move only right or down. Count paths from `(0,0)` to `(m-1, n-1)` that AVOID obstacles. Return 0 if no path exists.

**Example:**
```
[[0, 0, 0],
 [0, 1, 0],
 [0, 0, 0]]
```
→ 2 paths (must go around the center obstacle).

---

## 2. The recurrence + obstacle override

> **Mini-refresher: same as Unique Paths, with a single override.**
>
> ```
> dp[i][j] = 0                              if grid[i][j] == 1   (obstacle)
>          = 1                              if (i, j) == (0, 0)
>          = dp[i-1][j] + dp[i][j-1]        otherwise
> ```
>
> An obstacle has 0 paths through it. Cells AFTER an obstacle still get computed normally — but their predecessors may now be 0, so the count propagates down.

---

## 3. Edge cases: blocked endpoints, obstacle in border row/col

- **Start blocked:** `grid[0][0] == 1` → return 0.
- **End blocked:** `grid[m-1][n-1] == 1` → return 0.
- **Obstacle in first row:** `[0, 0, 1, 0]` → dp row = `[1, 1, 0, 0]`. The obstacle kills everything to its right (only-right movement can't go around).
- **Obstacle in first column:** symmetric.

These boundaries get handled naturally by the recurrence if `dp[0][0] = 1` and you set obstacle cells to 0 — but you have to be careful when initializing the first row and column.

---

## 4. Code (2D + 1D)

**C++ — 2D, clean:**

```cpp
int uniquePathsWithObstacles(vector<vector<int>>& grid) {
    int m = grid.size(), n = grid[0].size();
    if (grid[0][0] == 1 || grid[m-1][n-1] == 1) return 0;

    vector<vector<long long>> dp(m, vector<long long>(n, 0));
    dp[0][0] = 1;

    for (int j = 1; j < n; ++j) dp[0][j] = grid[0][j] ? 0 : dp[0][j-1];
    for (int i = 1; i < m; ++i) dp[i][0] = grid[i][0] ? 0 : dp[i-1][0];

    for (int i = 1; i < m; ++i)
        for (int j = 1; j < n; ++j)
            dp[i][j] = grid[i][j] ? 0 : dp[i-1][j] + dp[i][j-1];

    return (int)dp[m-1][n-1];
}
```

**C++ — 1D rolling, O(n) space:**

```cpp
int uniquePathsWithObstacles(vector<vector<int>>& grid) {
    int m = grid.size(), n = grid[0].size();
    vector<long long> dp(n, 0);
    dp[0] = grid[0][0] ? 0 : 1;
    for (int j = 1; j < n; ++j) dp[j] = grid[0][j] ? 0 : dp[j-1];

    for (int i = 1; i < m; ++i) {
        if (grid[i][0]) dp[0] = 0;
        for (int j = 1; j < n; ++j) {
            dp[j] = grid[i][j] ? 0 : (dp[j] + dp[j-1]);
        }
    }
    return (int)dp[n-1];
}
```

Complexity: **O(m · n)** time, **O(n)** space.

---

## 5. Trace it

```
grid = [[0, 0, 0],
        [0, 1, 0],
        [0, 0, 0]]
```

```
Init dp[0][0] = 1.
First row: dp[0] = [1, 1, 1].
First col: dp[*][0] = [1, 1, 1].

(1, 1): grid=1 → 0.
(1, 2): grid=0 → dp[0][2] + dp[1][1] = 1 + 0 = 1.
(2, 1): grid=0 → dp[1][1] + dp[2][0] = 0 + 1 = 1.
(2, 2): grid=0 → dp[1][2] + dp[2][1] = 1 + 1 = 2.

dp = [[1, 1, 1],
      [1, 0, 1],
      [1, 1, 2]]

Return 2.  ✓
```

The "0" at (1,1) propagates: any cell that USED to count via (1,1) gets a reduced count.

---

## 6. Why combinatorics fails

In Unique Paths (no obstacles), the count is `C(m+n-2, m-1)` — closed form, O(1)-ish.

With obstacles, every blocked cell removes a SUBSET of paths, and those subsets overlap. Inclusion-exclusion gets ugly fast. DP handles it by aggregating per-cell — much cleaner.

---

## 7. Common pitfalls

1. **Forgetting to check `grid[0][0]`.** If the start is blocked, no path can exist — return 0.
2. **`dp[0][0] = 1` even when blocked.** That's wrong — dp[0][0] should reflect the obstacle.
3. **First-row/first-column logic.** After encountering an obstacle, ALL subsequent cells in that row/column are 0 (can't go around in 1D). The pattern `dp[0][j] = grid[0][j] ? 0 : dp[0][j-1]` handles this correctly.
4. **Integer overflow.** For large m, n, counts can exceed 2^31. Use `long long` to be safe.
5. **Modifying the input grid as the DP table.** Works, but if the grid contains 1s for obstacles, you'd need a different sentinel for counts. Don't mix.

---

## 8. The shape — grid DP with forbidden cells

The pattern: **standard grid DP + override for forbidden cells.**

| Problem | Forbidden rule |
|---|---|
| **This problem** | obstacles set dp = 0 |
| Dungeon Game | path must keep HP > 0; reverse DP |
| Maximal Square | only 1-cells contribute |
| Number of Islands | DFS over connected 1s |
| Cherry Pickup | path can't enter thorns |
| Where Will the Ball Fall | grid with deflectors |

**Pattern to internalize:**

> "Grid DP + obstacles: the same recurrence as the obstacle-free version, BUT override `dp[i][j] = 0` (or sentinel) at forbidden cells. The 0s propagate naturally."

---

> **Self-check — the question to ask next time.**
>
> When the grid has forbidden cells, ask:
>
> > **"Same recurrence as Unique Paths, but `dp[i][j] = 0` at obstacles. Border row/col propagate 0 from the first obstacle onward."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Unique_Paths_II.md`](../Unique_Paths_II.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Unique_Paths.md`](./Unique_Paths.md).
  - Coming next: [`Minimum_Path_Sum.md`](./Minimum_Path_Sum.md), [`Triangle.md`](./Triangle.md).
