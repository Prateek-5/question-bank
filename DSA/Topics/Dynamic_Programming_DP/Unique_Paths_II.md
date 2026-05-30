# Unique Paths II

**Problem Link:**
<a href="https://leetcode.com/problems/unique-paths-ii/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/unique-paths-ii/</a>

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: The Grid and the Rules

You have an m × n grid where each cell is either:
- `0` = empty (passable).
- `1` = obstacle (blocked).

Starting at cell `(0, 0)` and ending at `(m-1, n-1)`, count the number of **unique paths** from start to end, where each move is either **one step right** or **one step down**.

If start or end is an obstacle, there are 0 paths.

Example:
```
[[0, 0, 0],
 [0, 1, 0],
 [0, 0, 0]]
```

Paths without obstacles: C(4, 2) = 6. But the middle obstacle blocks some. Valid paths:
- R, R, D, D
- R, D, R, D (blocked — passes (1,1))
- R, D, D, R
- D, R, R, D
- D, R, D, R (blocked)
- D, D, R, R

4 survive. Answer: **2**. (Wait, let me recount — actually I need to recheck by enumeration.)

Carefully: 6 total unblocked-grid paths. Paths through (1,1) are blocked. In a 3×3, paths passing through (1,1) = (paths 0,0 → 1,1) × (paths 1,1 → 2,2) = C(2,1) × C(2,1) = 2 × 2 = 4. So unblocked = 6 - 4 = **2**. ✓

----------------------------------------

## Step 2: DP Setup

Let `dp[i][j]` = number of unique paths from (0, 0) to (i, j).

Recurrence: a path arrives at (i, j) either from above or from the left.

```
dp[i][j] = dp[i-1][j] + dp[i][j-1]
```

Boundary: if (i, j) is an obstacle, dp[i][j] = 0 (no path through).

Base case: dp[0][0] = 1 (one way to start at start — if (0,0) is not an obstacle). If (0, 0) is an obstacle, dp[0][0] = 0.

First row / first column: only one way each (only one direction available) — as long as the path isn't blocked by an obstacle. Propagate: dp[0][j] = dp[0][j-1] if grid[0][j] is free, else 0.

----------------------------------------

## Step 3: Obstacles Break the Propagation

A key subtlety: if any cell in the first row is an obstacle, all cells **after** it in that row have dp = 0 (can't reach them going only right).

Example first row: `[0, 0, 1, 0]`. dp = [1, 1, 0, 0]. The obstacle at column 2 kills paths to columns 2 and 3.

Same for first column.

----------------------------------------

## Step 4: Algorithm

```
if grid[0][0] == 1 or grid[m-1][n-1] == 1: return 0

dp[0][0] = 1
for j in 1..n-1:
    dp[0][j] = dp[0][j-1] if grid[0][j] == 0 else 0
for i in 1..m-1:
    dp[i][0] = dp[i-1][0] if grid[i][0] == 0 else 0

for i in 1..m-1:
    for j in 1..n-1:
        if grid[i][j] == 1:
            dp[i][j] = 0
        else:
            dp[i][j] = dp[i-1][j] + dp[i][j-1]

return dp[m-1][n-1]
```

O(m · n) time. O(m · n) space — reducible to O(n) using a 1D rolling array.

----------------------------------------

## Step 5: Trace

```
grid = [[0, 0, 0],
        [0, 1, 0],
        [0, 0, 0]]
```

Initialize dp[0][0] = 1.

First row: dp[0] = [1, 1, 1] (no obstacles).
First column: dp[0][0] = 1, dp[1][0] = 1 (free), dp[2][0] = 1.

Fill:
- dp[1][1]: grid = 1 → dp = 0.
- dp[1][2]: grid = 0. dp = dp[0][2] + dp[1][1] = 1 + 0 = 1.
- dp[2][1]: grid = 0. dp = dp[1][1] + dp[2][0] = 0 + 1 = 1.
- dp[2][2]: grid = 0. dp = dp[1][2] + dp[2][1] = 1 + 1 = 2.

```
dp = [[1, 1, 1],
      [1, 0, 1],
      [1, 1, 2]]
```

Return **2**. ✓

----------------------------------------

## Step 6: Space Optimization — 1D Rolling Array

We only need the previous row to compute the current row. Keep a single array `dp` of length n.

```
dp[0] = 1 if grid[0][0] == 0 else 0
for j in 1..n-1:
    dp[j] = dp[j-1] if grid[0][j] == 0 else 0

for i in 1..m-1:
    dp[0] = dp[0] if grid[i][0] == 0 else 0
    for j in 1..n-1:
        if grid[i][j] == 1:
            dp[j] = 0
        else:
            dp[j] = dp[j] + dp[j-1]   # dp[j] is previous row's; dp[j-1] is current row's

return dp[n-1]
```

O(n) space. The update `dp[j] = dp[j] + dp[j-1]` works because `dp[j]` still holds the previous row's value before we overwrite it.

----------------------------------------

## Step 7: Why DP?

Each cell's count depends only on its upper and left neighbors — both computed before it in row-major order. That's textbook DP: overlapping subproblems (same cell appears in many path-counts) + optimal substructure (count through a cell = sum of counts through predecessors).

Without DP, naive recursion would be exponential (each cell branches into 2, depth m + n).

----------------------------------------

## Step 8: Name It

**Grid DP / path counting**. Foundational:
- Unique Paths (no obstacles — pure C(m+n-2, m-1) combinatorial).
- Unique Paths II (this problem).
- Minimum Path Sum (same recurrence, different optimization — min instead of sum).
- Edit Distance, Longest Common Subsequence, Matrix DP generally.

All share the "fill the grid row by row using left and upper neighbors" template.

----------------------------------------

## Step 9: Complexity

Time: **O(m · n)** — each cell computed once in O(1).
Space: **O(m · n)** naive, **O(n)** optimized.

----------------------------------------

## Step 10: C++ Implementation

**2D version:**

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

**1D optimized:**

```cpp
int uniquePathsWithObstacles(vector<vector<int>>& grid) {
    int m = grid.size(), n = grid[0].size();
    vector<long long> dp(n, 0);
    dp[0] = grid[0][0] ? 0 : 1;
    for (int j = 1; j < n; ++j) dp[j] = grid[0][j] ? 0 : dp[j-1];

    for (int i = 1; i < m; ++i) {
        dp[0] = grid[i][0] ? 0 : dp[0];
        for (int j = 1; j < n; ++j) {
            dp[j] = grid[i][j] ? 0 : (dp[j] + dp[j-1]);
        }
    }
    return (int)dp[n-1];
}
```

Long-long guards against overflow (path counts can be huge for large grids).

----------------------------------------

## Step 11: Follow-up Questions

- **Diagonal moves allowed.** Add `dp[i-1][j-1]` to the recurrence.
- **Grid with K obstacles, paths avoiding exactly K obstacles.** Stateful DP: (i, j, obstacles_hit).
- **Count paths with minimum obstacles encountered.** Different metric; similar DP shape.
- **Return one valid path.** Backtrack from end; at each step, choose the predecessor with positive count.
- **Why long-long?** For m, n around 100, path counts can exceed 2^63 without obstacles. Actual problem constraints usually ensure counts fit in 32-bit, but safer to guard.
- **Obstacles can move (dynamic).** Grid DP doesn't support this well; simulation per query.
