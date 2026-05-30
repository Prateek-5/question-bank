# Minimum Path Sum — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Minimum_Path_Sum.md`](../Minimum_Path_Sum.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/minimum-path-sum/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/minimum-path-sum/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: same grid-DP shape as Unique Paths, but COUNTING (sum) becomes COST (min). `f(i,j) = grid[i][j] + min(f(i-1,j), f(i,j-1))`. Same "what was my last move?" decomposition.**

**Map of this file (8 sections):**

1. Read the problem
2. The recurrence
3. Why optimality stitches locally
4. Code (in-place / 1D / 2D)
5. Trace it
6. Recovering the actual path
7. Common pitfalls
8. The shape — grid DP for min-cost

---

## 1. Read the problem

`m × n` grid of non-negative integers. Start top-left, end bottom-right. Move only right or down. Each cell's value contributes to the path cost (INCLUDING start and end). Minimize total cost.

**Example:**
```
1 3 1
1 5 1
4 2 1
```

Path `1 → 3 → 1 → 1 → 1` (top row, then right column): sum **7**. Best.

---

## 2. The recurrence

> **Mini-refresher: same "last move" trick, with min instead of sum.**
>
> Let `f(i, j)` = minimum sum from (0, 0) to (i, j).
>
> Last move: from (i-1, j) [down] or (i, j-1) [right].
>
> ```
> f(i, j) = grid[i][j] + min(f(i-1, j), f(i, j-1))
> ```
>
> Base: `f(0, 0) = grid[0][0]`. Top row: `f(0, j) = f(0, j-1) + grid[0][j]`. Left col: symmetric.
>
> Answer: `f(m-1, n-1)`.

---

## 3. Why optimality stitches locally

> **Mini-refresher: optimality principle (Bellman).**
>
> If the OPTIMAL path to (i, j) passes through predecessor (i-1, j), then its PREFIX from (0,0) to (i-1, j) must also be OPTIMAL for that subproblem. If a cheaper prefix existed, swapping it in would give an even cheaper path to (i, j) — contradiction.
>
> So the best path's cost at (i, j) is determined by the best costs at its predecessors — no need to track full paths.

This is THE defining property that makes DP work.

---

## 4. Code (in-place / 1D / 2D)

**C++ — in-place (mutates input, O(1) extra space):**

```cpp
int minPathSum(vector<vector<int>>& g) {
    int m = g.size(), n = g[0].size();
    for (int i = 0; i < m; ++i) {
        for (int j = 0; j < n; ++j) {
            if (i == 0 && j == 0) continue;
            int up   = (i > 0) ? g[i-1][j] : INT_MAX;
            int left = (j > 0) ? g[i][j-1] : INT_MAX;
            g[i][j] += min(up, left);
        }
    }
    return g[m-1][n-1];
}
```

**C++ — non-destructive 2D:**

```cpp
int minPathSum(vector<vector<int>>& g) {
    int m = g.size(), n = g[0].size();
    vector<vector<int>> f(m, vector<int>(n));
    f[0][0] = g[0][0];
    for (int j = 1; j < n; ++j) f[0][j] = f[0][j-1] + g[0][j];
    for (int i = 1; i < m; ++i) f[i][0] = f[i-1][0] + g[i][0];
    for (int i = 1; i < m; ++i)
        for (int j = 1; j < n; ++j)
            f[i][j] = g[i][j] + min(f[i-1][j], f[i][j-1]);
    return f[m-1][n-1];
}
```

Complexity: **O(m · n)** time. Space **O(1)** (in-place) / **O(n)** (1D rolling) / **O(m·n)** (full).

---

## 5. Trace it

```
grid = [[1, 3, 1],
        [1, 5, 1],
        [4, 2, 1]]

f[0][0] = 1.
Row 0: 1, 1+3=4, 4+1=5.   → [1, 4, 5]
Col 0: 1, 1+1=2, 2+4=6.   

f[1][1] = 5 + min(4, 2) = 7.
f[1][2] = 1 + min(5, 7) = 6.
f[2][1] = 2 + min(7, 6) = 8.
f[2][2] = 1 + min(6, 8) = 7.

f = [[1, 4, 5],
     [2, 7, 6],
     [6, 8, 7]]

Return 7.  ✓
```

---

## 6. Recovering the actual path

If asked for the path itself (not just the sum), backtrack from `f[m-1][n-1]`:

```
i, j = m-1, n-1
path = [(i, j)]
while i > 0 or j > 0:
    if i == 0: j -= 1
    elif j == 0: i -= 1
    elif f[i-1][j] <= f[i][j-1]: i -= 1
    else: j -= 1
    path.append((i, j))
path.reverse()
```

The full DP table (or parent pointers) is needed — the in-place version loses this info.

---

## 7. Common pitfalls

1. **Forgetting to add grid[0][0].** It's included in the cost.
2. **`INT_MAX + something` overflow.** Use INT_MAX as sentinel ONLY when guarded by the `i > 0` / `j > 0` check, OR cast to `long long`.
3. **Treating start as "free."** It's not — the start cell's value is part of the cost.
4. **Computing top-down with naive recursion.** Exponential blowup; you MUST memoize.
5. **Using `<` instead of `<=` in path reconstruction tie-break.** Either is valid; pick consistently.

---

## 8. The shape — grid DP for min-cost

The pattern: **same shape as Unique Paths, but `combine = min(...) + cell_value`.**

| Problem | Combine |
|---|---|
| Unique Paths | sum (count) |
| Unique Paths II | sum, 0 at obstacles |
| **This problem** | `grid[i][j] + min(prev)` |
| Maximum Path Sum in Grid | `max` instead of `min` |
| Dungeon Game | reverse DP (constraint on HP) |
| Cherry Pickup | two simultaneous paths |
| Path with Minimum Effort | `max(prev_max, |diff|)` |

**Pattern to internalize:**

> "Grid DP MIN-COST: `f(i, j) = cell + min(f(i-1, j), f(i, j-1))`. Same skeleton as counting; swap aggregator. In-place mutates input — O(1) extra space."

---

> **Self-check — the question to ask next time.**
>
> When the problem is "shortest/cheapest path on a grid moving right/down only":
>
> > **"Grid DP. `f(i, j) = grid[i][j] + min(f above, f left)`. O(m·n) time. In-place if mutation allowed."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Minimum_Path_Sum.md`](../Minimum_Path_Sum.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Unique_Paths.md`](./Unique_Paths.md), [`Unique_Paths_II.md`](./Unique_Paths_II.md).
  - Coming next: [`Triangle.md`](./Triangle.md), [`Longest_Increasing_Subsequence.md`](./Longest_Increasing_Subsequence.md).
