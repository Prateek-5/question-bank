# Unique Paths

**Problem Link:**
<a href="https://leetcode.com/problems/unique-paths/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/unique-paths/</a>

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: The Setup

You're on an `m × n` grid, standing at the top-left corner `(0, 0)`. You want to reach the bottom-right corner `(m-1, n-1)`. At each step, you can only move **right** or **down**. How many distinct paths are there?

Example: `m = 3, n = 2`.

```
start . .
.     . .
.     . end
```

I could go: RDD, DRD, DDR. That's 3 paths. Let me sanity-check by brute force.

Any path consists of some rights and some downs. To reach (2, 1) from (0, 0), I need exactly 2 downs and 1 right — in any order. Number of arrangements = C(3, 1) = 3. ✓

So the closed-form answer is `C((m-1) + (n-1), m-1) = C(m + n - 2, m - 1)`. But let's see how we'd *derive* that, because the DP way teaches a more transferable technique.

----------------------------------------

## Step 2: Try a Small Grid by Hand

Let me count paths to each cell for a 3×3 grid.

```
(0,0) (0,1) (0,2)
(1,0) (1,1) (1,2)
(2,0) (2,1) (2,2)
```

Paths to `(0, 0)`: 1 (already there).

Paths to cells in the top row `(0, j)`: only way is all rights. 1 path each.

Paths to cells in the left column `(i, 0)`: only way is all downs. 1 path each.

Paths to `(1, 1)`: I can come from `(0, 1)` (move down) or `(1, 0)` (move right). So paths to `(1, 1)` = paths to `(0, 1)` + paths to `(1, 0)` = 1 + 1 = 2.

Paths to `(1, 2)`: from `(0, 2)` or `(1, 1)` = 1 + 2 = 3.

Paths to `(2, 1)`: from `(1, 1)` or `(2, 0)` = 2 + 1 = 3.

Paths to `(2, 2)`: from `(1, 2)` or `(2, 1)` = 3 + 3 = 6.

Let me write out the grid:

```
1 1 1
1 2 3
1 3 6
```

And for any cell `(i, j)` with `i, j > 0`: `paths(i, j) = paths(i-1, j) + paths(i, j-1)`.

----------------------------------------

## Step 3: The Recurrence Is the Reasoning

This recurrence isn't arbitrary. It says: "the number of ways to reach `(i, j)` is the number of ways to arrive from the cell directly above, plus the number of ways to arrive from the cell directly to the left." That's because those are the *only* two incoming moves. No overlap (a path is either its-last-move-was-down or its-last-move-was-right, not both), and it covers everything.

So the DP is exact, not an approximation.

```
paths(i, j) = 1                               if i == 0 or j == 0
            = paths(i-1, j) + paths(i, j-1)   otherwise
```

With this recurrence, fill the table row by row (or column by column) and read off `paths(m-1, n-1)`.

----------------------------------------

## Step 4: Table for m=3, n=7 (the Classic Example)

Expected answer is 28.

```
1 1 1 1 1 1 1
1 2 3 4 5 6 7
1 3 6 10 15 21 28
```

Each cell is the sum of the cell above and the cell to the left. Bottom-right is 28. ✓

Hmm, look at row 2: `1 3 6 10 15 21 28`. Those are triangular-number-like values. Row 1 is the identity. This is Pascal's triangle on its side — and that's not a coincidence. It leads us to the closed form.

----------------------------------------

## Step 5: Closed Form via Combinatorics

As noted in Step 1, any path has exactly `(m - 1)` down-moves and `(n - 1)` right-moves. The total is `(m + n - 2)` moves. We're choosing which of those are downs (equivalently, which are rights). So:

```
paths(m, n) = C(m + n - 2, m - 1) = C(m + n - 2, n - 1)
```

That's O(min(m, n)) to compute with a running product:

```cpp
long long r = 1;
int small = min(m, n) - 1;
for (int i = 1; i <= small; ++i) r = r * (m + n - 1 - i) / i;
return (int)r;
```

Beautiful, but the DP version has the advantage that it generalizes — if we add obstacles (Unique Paths II) or weighted cells, the recurrence still works but the combinatorial formula doesn't.

----------------------------------------

## Step 6: Space-Optimized DP

Look at the recurrence: `paths(i, j) = paths(i-1, j) + paths(i, j-1)`. Only the *previous row* and the *current row* (for the left neighbor) matter. So we can compute in place with one row:

```cpp
vector<int> dp(n, 1);   // top row: all 1s
for (int i = 1; i < m; ++i) {
    for (int j = 1; j < n; ++j) {
        dp[j] += dp[j - 1];    // dp[j] is "from above", dp[j-1] is "from left"
    }
}
return dp[n - 1];
```

This is the same algorithm as the 2D table, but stored as a single row that updates row by row. O(n) space.

Let me trace this briefly for m=3, n=3. Expected answer 6.

```
Row 0: dp = [1, 1, 1]
Row 1: update j=1: dp[1] = 1 + 1 = 2. update j=2: dp[2] = 1 + 2 = 3. dp = [1, 2, 3].
Row 2: update j=1: dp[1] = 2 + 1 = 3. update j=2: dp[2] = 3 + 3 = 6. dp = [1, 3, 6].
```

`dp[n-1] = 6`. ✓

----------------------------------------

## Step 7: Complexity

Time: `m · n` cells, O(1) per cell. **O(m · n)** for DP, **O(min(m, n))** for the combinatorial formula.

Space: **O(n)** with the 1D optimization, **O(1)** for the combinatorial version.

----------------------------------------

## Step 8: C++ Implementation

Combinatorial (fastest):

```cpp
int uniquePaths(int m, int n) {
    long long r = 1;
    for (int i = 1; i < m; ++i) r = r * (n - 1 + i) / i;
    return (int)r;
}
```

1D DP (more instructive, handles generalizations):

```cpp
int uniquePaths(int m, int n) {
    vector<int> dp(n, 1);
    for (int i = 1; i < m; ++i)
        for (int j = 1; j < n; ++j)
            dp[j] += dp[j - 1];
    return dp[n - 1];
}
```

Either is fine. The combinatorial version is an algorithmic flex; the DP is the one you build on for harder variants.

----------------------------------------

## Step 9: Follow-up Questions

- **Unique Paths II (obstacles).** DP with `dp[i][j] = 0` if the cell is an obstacle; combinatorial formula no longer works.
- **Unique Paths III (visit every empty cell exactly once, start/end given).** This is NP-hard in general — backtracking with bitmask DP when board is small.
- **What if you can move in more directions (up, left too)?** Changes the problem entirely — might introduce cycles, making "count paths" infinite without extra constraints.
- **3D grid.** Extend the recurrence: `paths(i, j, k) = paths(i-1, j, k) + paths(i, j-1, k) + paths(i, j, k-1)`. Combinatorial: `C(m+n+p-3, m-1, n-1, p-1)` (multinomial).
- **What if cells have costs, and you want the minimum-cost path?** Minimum Path Sum — replace addition with min and add cell cost.
