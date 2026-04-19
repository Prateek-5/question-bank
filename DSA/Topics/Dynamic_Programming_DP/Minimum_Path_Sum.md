# Minimum Path Sum

**Problem Link:**
https://leetcode.com/problems/minimum-path-sum/

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Paint the Picture

An `m × n` grid, each cell holding a non-negative number. Starting from the top-left, you want to reach the bottom-right, moving only **right** or **down**. The "cost" of a path is the sum of numbers in the cells you pass through (including both endpoints). Minimize it.

Example:
```
1 3 1
1 5 1
4 2 1
```

One possible path: 1 → 3 → 1 → 1 → 1 (top row, then rightmost column). Sum: 7.
Another: 1 → 1 → 4 → 2 → 1 (left column, then bottom row). Sum: 9.
Another: 1 → 1 → 5 → 2 → 1. Sum: 10.
Another: 1 → 1 → 5 → 1 → 1. Sum: 9.
Another: 1 → 3 → 5 → 1 → 1. Sum: 11.

The minimum I see: **7**. (1 → 3 → 1 → 1 → 1.)

----------------------------------------

## Step 2: Brute Force First

Enumerate every path. How many paths are there? In an `m × n` grid we must make `(m-1)` downs and `(n-1)` rights, any order — that's `C(m+n-2, m-1)` paths, which is exponential-ish. For a 20×20 grid, it's already 68 billion. Not feasible to enumerate.

OK so brute force is out. Let me think about what makes paths easier.

----------------------------------------

## Step 3: Every Cell's "Best Path to It" Idea

Instead of thinking about full paths, let's think cell by cell. For each cell `(i, j)`, define:

`f(i, j)` = minimum sum of any path from `(0, 0)` to `(i, j)`.

If I know this for every cell, I just return `f(m-1, n-1)`.

Now the key observation: how can a path arrive at `(i, j)`? Only from above `(i-1, j)` or from the left `(i, j-1)` — those are the only two allowed predecessors (since we move only right or down).

So:
```
f(i, j) = grid[i][j] + min(f(i-1, j), f(i, j-1))
```

We take whichever predecessor gave a smaller sum, and add the current cell.

Base cases:
- `f(0, 0) = grid[0][0]`.
- Top row (`i = 0, j > 0`): only the from-left predecessor exists. `f(0, j) = f(0, j-1) + grid[0][j]`.
- Left column (`i > 0, j = 0`): only from-above. `f(i, 0) = f(i-1, 0) + grid[i][0]`.

This fully specifies the DP.

----------------------------------------

## Step 4: Trace on the Example

Grid:
```
1 3 1
1 5 1
4 2 1
```

Build `f` left-to-right, top-to-bottom.

Row 0: `f(0,0)=1. f(0,1)=1+3=4. f(0,2)=4+1=5.`

Row 1: 
- `f(1,0)=1+1=2`.
- `f(1,1)=5 + min(4, 2) = 5 + 2 = 7`.
- `f(1,2)=1 + min(5, 7) = 1 + 5 = 6`.

Row 2:
- `f(2,0)=4 + 2 = 6`.
- `f(2,1)=2 + min(7, 6) = 2 + 6 = 8`.
- `f(2,2)=1 + min(6, 8) = 1 + 6 = 7`.

`f(2, 2) = 7`. ✓

`f` table:
```
1 4 5
2 7 6
6 8 7
```

By reading this back, we can even recover the path: at `(2,2)` we came from `(1,2)=6`; at `(1,2)` from `(0,2)=5`; at `(0,2)` from `(0,1)=4`; at `(0,1)` from `(0,0)=1`. Path: (0,0)→(0,1)→(0,2)→(1,2)→(2,2). Values: 1,3,1,1,1. Sum 7.

----------------------------------------

## Step 5: Why This Recurrence Is Right

We've implicitly used the **optimality principle**: if the best path from `(0,0)` to `(i,j)` goes through some predecessor `(i-1, j)` (say), then its prefix from `(0,0)` to `(i-1, j)` must also be a best path to `(i-1, j)`. If there were a cheaper path to `(i-1, j)`, swapping it in would give an even cheaper path to `(i, j)` — contradiction.

So `f(i, j)` depends only on the best values at the two predecessors. No need to remember entire paths, just per-cell best sums.

This is the defining property that makes dynamic programming work. If you saw the grid and your first instinct was "this looks like something where local optimality stitches to global optimality," you spotted it.

----------------------------------------

## Step 6: Space Optimization

The full `f` table takes O(m·n) space. But each row only depends on the previous row (and cells within the same row to the left). So we can overwrite the grid in place, or keep a single row of size `n`.

In-place mutation — which modifies the input — is acceptable in interview settings when the caller doesn't need the original. Let me show both options.

```cpp
// In-place, O(1) extra space
for (int i = 0; i < m; ++i) {
    for (int j = 0; j < n; ++j) {
        if (i == 0 && j == 0) continue;
        int up   = (i > 0) ? g[i-1][j] : INT_MAX;
        int left = (j > 0) ? g[i][j-1] : INT_MAX;
        g[i][j] += min(up, left);
    }
}
return g[m-1][n-1];
```

Using `INT_MAX` as a sentinel for "this neighbor doesn't exist" works because we only take `min`. When we reach a cell where both would be `INT_MAX`, we know it's `(0,0)` and we skip.

----------------------------------------

## Step 7: Name It

This is **grid DP** — a 2D tabulation where each cell combines a handful of neighbors. The same shape appears in Unique Paths, Dungeon Game, Maximal Square, Cherry Pickup, and many others. The distinguishing feature: cells have a small, fixed set of predecessors, and the answer at each cell is a simple function of its predecessors' answers.

But again — we got here by asking "how does a path arrive at `(i, j)`?", not by stating "DP." The structure was implied by the problem's own movement rules.

----------------------------------------

## Step 8: Complexity

Time: each of `m·n` cells computed in O(1). **O(m·n)**.
Space: **O(1)** in-place (modifies input), **O(n)** with a rolling row, **O(m·n)** with a full DP table.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int minPathSum(vector<vector<int>>& g) {
    int m = g.size(), n = g[0].size();
    for (int i = 0; i < m; ++i) {
        for (int j = 0; j < n; ++j) {
            if (i == 0 && j == 0) continue;
            int up   = (i > 0) ? g[i - 1][j] : INT_MAX;
            int left = (j > 0) ? g[i][j - 1] : INT_MAX;
            g[i][j] += min(up, left);
        }
    }
    return g[m - 1][n - 1];
}
```

Reading the code: at each cell (other than the origin), we add the min of its two possible predecessors — using `INT_MAX` as a sentinel for missing neighbors. After the loop, the bottom-right cell holds the answer.

----------------------------------------

## Step 10: Follow-up Questions

- **Return the actual path, not just the sum.** Store parent pointers in a separate matrix; walk them back from `(m-1, n-1)`.
- **Allow diagonal moves.** Add a third predecessor `(i-1, j-1)`.
- **Allow moving in all four directions (up, down, left, right).** It becomes a shortest-path problem on a weighted graph — Dijkstra with cell weight as edge cost.
- **Maximum path sum (same movement rules).** Swap `min` for `max`.
- **Negative cell values?** The algorithm works as long as there are no negative cycles (moves are acyclic, so no issue).
- **K obstacles you can phase through at no cost.** 3D DP with state `(i, j, obstacles_remaining)`.
