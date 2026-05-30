# Triangle

**Problem Link:**
<a href="https://leetcode.com/problems/triangle/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/triangle/</a>

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Visualize Before Coding

You get a triangle of numbers, arranged so each row has one more entry than the row above it:

```
   [2]
  [3, 4]
 [6, 5, 7]
[4, 1, 8, 3]
```

Starting from the top, each step you move to one of two adjacent numbers in the row below. From position `j` in row `i`, you can go to position `j` or position `j+1` in row `i+1`. Return the minimum path sum from top to bottom.

Let me mark the possible paths on this small triangle by hand.

Starting at 2 (top). From 2, go to 3 or 4.
- If 3: from 3, go to 6 or 5.
  - If 6: from 6, go to 4 or 1. Sums: 2+3+6+4=15, 2+3+6+1=12.
  - If 5: from 5, go to 1 or 8. Sums: 2+3+5+1=11, 2+3+5+8=18.
- If 4: from 4, go to 5 or 7.
  - If 5: from 5, go to 1 or 8. Sums: 2+4+5+1=12, 2+4+5+8=19.
  - If 7: from 7, go to 8 or 3. Sums: 2+4+7+8=21, 2+4+7+3=16.

Minimum: **11** (2 → 3 → 5 → 1).

----------------------------------------

## Step 2: The Exponential Problem

Each row doubles our choices. A triangle with `n` rows has `2^(n-1)` paths. For n = 30, that's a billion paths — way too many to enumerate.

The inefficiency is obvious once I write out my hand-enumeration: at position (row 2, col 1) — the `5` — I get there from two different paths (via 3 or via 4), and *from there* my future choices are identical. Whatever best path starts at `5` in row 2 is the same regardless of how we arrived. Enumerating full paths re-solves this "best future from here" question many times.

----------------------------------------

## Step 3: Local Question That Breaks the Recursion

Let me define:
`best(i, j)` = minimum path sum from cell (i, j) down to the bottom of the triangle.

Then the answer is `best(0, 0)`.

For a cell on the bottom row, the minimum path from there is just the cell's own value — there are no more rows.

For any other cell, we must move next to either `(i+1, j)` or `(i+1, j+1)`. We pick whichever has the smaller best-downward-sum. So:

```
best(i, j) = triangle[i][j] + min(best(i+1, j), best(i+1, j+1))
```

This is what dynamic programming lets us do: compute each cell's best-from-here once, cache it, reuse it.

----------------------------------------

## Step 4: Which Direction to Compute?

There's a natural choice: **bottom-up**. Start at the last row (where `best` is trivially the cell's value), and work upward, filling in each cell using the row below.

This is neater than top-down-with-memo because we don't need recursion. Let me build a running array that starts as the last row, and update it row by row going up.

After the last row: `dp = [4, 1, 8, 3]`. This is `best(3, 0), best(3, 1), best(3, 2), best(3, 3)`.

Move up to row 2 (values `[6, 5, 7]`):
- `best(2, 0) = 6 + min(dp[0], dp[1]) = 6 + min(4, 1) = 7.`
- `best(2, 1) = 5 + min(dp[1], dp[2]) = 5 + min(1, 8) = 6.`
- `best(2, 2) = 7 + min(dp[2], dp[3]) = 7 + min(8, 3) = 10.`

New `dp = [7, 6, 10, *]` (we don't care about position 3 anymore).

Row 1 (`[3, 4]`):
- `best(1, 0) = 3 + min(dp[0], dp[1]) = 3 + min(7, 6) = 9.`
- `best(1, 1) = 4 + min(dp[1], dp[2]) = 4 + min(6, 10) = 10.`

`dp = [9, 10, *, *]`.

Row 0 (`[2]`):
- `best(0, 0) = 2 + min(dp[0], dp[1]) = 2 + min(9, 10) = 11.`

Answer: **11**. ✓ Matches our hand-enumeration.

----------------------------------------

## Step 5: Why Bottom-Up Is Clean

In this problem, bottom-up has a particular elegance: when we iterate row by row from bottom to top, each cell at row `i` writes into the slot it occupies, and reads from its own slot and the next slot in the already-updated row below. We can use a **single array** of length `n` (the number of rows), updating in place from left to right.

After we update `dp[j]`, the old value at `dp[j]` is no longer needed — we've consumed it. The value at `dp[j+1]` is still needed for one more update (the next column's left neighbor). That works out because we iterate j from 0 to i (inclusive), and each step only looks at j and j+1.

Let me re-verify that this in-place update doesn't corrupt anything:

At row i, we want `dp[j] = triangle[i][j] + min(dp[j], dp[j+1])` where `dp[j]` and `dp[j+1]` are the values from row i+1.

When we compute column j, `dp[j]` still holds row (i+1)'s value (we haven't overwritten it yet). `dp[j+1]` likewise. After we assign, `dp[j]` holds row i's value — and when we compute j+1, we need `dp[j+1]` (still row i+1) and `dp[j+2]` (still row i+1). So the left-to-right update order within a row works perfectly.

----------------------------------------

## Step 6: Name It

This is **path DP on a grid / triangle** — the defining feature is that each cell has a small constant number of predecessors (or successors, depending on direction), and we combine their best values with the current cell's cost.

The in-place update with a 1D array is a common space optimization for such DPs.

----------------------------------------

## Step 7: Complexity

Time: each cell is visited once; constant work per cell. **O(n²)** where n is the number of rows (because the total number of cells is n·(n+1)/2).

Space: **O(n)** with the 1D array optimization. **O(1)** if the problem allows mutating the input triangle in place.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int minimumTotal(vector<vector<int>>& triangle) {
    vector<int> dp(triangle.back().begin(), triangle.back().end());
    for (int i = triangle.size() - 2; i >= 0; --i) {
        for (int j = 0; j <= i; ++j) {
            dp[j] = triangle[i][j] + min(dp[j], dp[j + 1]);
        }
    }
    return dp[0];
}
```

Read the code: `dp` starts as a copy of the last row. We iterate rows upward, each time updating `dp[0..i]` to hold the best-from-here values for row `i`. At the end, `dp[0]` is the answer.

----------------------------------------

## Step 9: Follow-up Questions

- **Maximum path sum, not minimum.** Swap `min` for `max`. Same algorithm.
- **Return the actual path.** Track parent choices while filling `dp`; walk back from `(0, 0)` choosing the winning neighbor each step.
- **What if movement is allowed to any of the three neighbors below (left, straight, right)?** In a standard triangle, only two neighbors exist per cell. For a non-triangular grid, add the third case in `min`.
- **Multiple triangles stacked** (answer the question for each in a batch). Preprocess each independently; O(n²) per triangle.
- **Triangle with weighted edges (rather than cell values)** — reinterpret as a graph shortest-path.
- **Can we solve it top-down from the root?** Yes, but the in-place 1D trick is messier because `dp[j]` in row `i+1` depends on cells in both row `i`. Bottom-up is cleaner here.
