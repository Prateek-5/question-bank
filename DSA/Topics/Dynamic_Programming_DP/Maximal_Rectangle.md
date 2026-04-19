# Maximal Rectangle

**Problem Link:**
https://leetcode.com/problems/maximal-rectangle/

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Read the Problem

You have an `m × n` binary matrix (cells are `'0'` or `'1'`). Find the **largest rectangle containing only 1s** and return its area.

The rectangle must be axis-aligned (sides parallel to the grid).

Example:
```
1 0 1 0 0
1 0 1 1 1
1 1 1 1 1
1 0 0 1 0
```

By inspection, the rectangle in rows 1-2, columns 2-4 is size 2 × 3 = 6, all 1s. Is there bigger? 

What about the all-1s 2×2 block in rows 1-2, columns 3-4? Size 4, smaller.

What about the strip in row 2, columns 0-4? That's 1 × 5 = 5, smaller than 6.

Rows 1-2, columns 2-4 gives 6, which is the known answer.

----------------------------------------

## Step 2: Brute Force Thinking

Try every rectangle in the grid. Specify rectangle by (top, bottom, left, right) — O(m²·n²) rectangles. For each, check if all cells are 1s: O(m·n). Total O(m³·n³). Unusable for non-trivial inputs.

Even smarter brute: for each top-left corner, extend as far as possible. Still O(m²·n²) worst case.

We need to exploit some structural property to cut this down.

----------------------------------------

## Step 3: Reduce to a 1D Problem

Here's a key reframing. Look at each row in turn. Imagine the cells above each row are "stacked" — for column c in row i, count how many consecutive 1s exist ending at row i. Call this height[c].

Now for each row, the problem becomes: **given a histogram with bars of these heights, find the largest rectangle in the histogram**.

Let me illustrate with the example.

```
Row 0: 1 0 1 0 0          heights: [1, 0, 1, 0, 0]
Row 1: 1 0 1 1 1          heights: [2, 0, 2, 1, 1]
Row 2: 1 1 1 1 1          heights: [3, 1, 3, 2, 2]
Row 3: 1 0 0 1 0          heights: [4, 0, 0, 3, 0]
```

(When a cell is 0, its height resets to 0; when 1, increment from the previous row.)

Maximum rectangle in each histogram:
- Row 0 heights [1,0,1,0,0]: largest rectangle = 1 (either single 1).
- Row 1 heights [2,0,2,1,1]: options include 2×1=2 from column 0, 3×1=3 from columns 2-4 (min height 1), 2×1=2 from column 2. Hmm, let me re-check — the rectangle in columns 2-4 with height 1 (limited by columns 3, 4) is 3 × 1 = 3. Column 2 alone at height 2 is 2. So max is 3.
- Row 2 heights [3,1,3,2,2]: columns 2-4 at min height 2 → 3 × 2 = 6. Column 0 at 3 → 3. Column 2 alone at 3 → 3. Max is 6.
- Row 3 heights [4,0,0,3,0]: column 0 at 4 → 4. Column 3 at 3 → 3. Max is 4.

Overall max: **6**. ✓ Matches the expected answer.

----------------------------------------

## Step 4: Why This Decomposition Is Correct

Any rectangle of all-1s in the matrix has a bottom row. Consider the rectangle's bottom row (say row i) and its columns [left, right]. The heights of the histogram for row i capture exactly how far up the all-1s column extends from row i.

So a rectangle in the matrix with bottom at row i maps exactly to a rectangle in row i's histogram. The largest rectangle in the matrix is the maximum over all possible bottom rows, which is the max over all histograms.

No matrix rectangle is missed. Every matrix rectangle contributes to exactly one histogram (the one for its bottom row).

----------------------------------------

## Step 5: Largest Rectangle in Histogram — The Monotonic Stack

If you haven't seen this subproblem, the classical solution uses a **monotonic stack**. For each bar, find the farthest-left and farthest-right bars that are ≥ this bar's height. The rectangle using this bar as the minimum has width = (right - left - 1) and height = bar's height.

A monotonic increasing stack of indices achieves this in O(n):
- When a bar shorter than the stack top arrives, the bar at the top has found its right boundary (the incoming shorter bar). Pop and compute its rectangle.
- The new top of the stack after popping is its left boundary.

Full algorithm:

```
stack = []   # indices of bars with strictly increasing heights
best = 0
for i in 0..n-1:
    while stack and heights[stack.top()] > heights[i]:
        popped = stack.pop()
        h = heights[popped]
        left = stack.top() if stack else -1
        width = i - left - 1
        best = max(best, h * width)
    stack.push(i)
# handle remaining bars at the end by treating "right boundary" as n
while stack:
    popped = stack.pop()
    h = heights[popped]
    left = stack.top() if stack else -1
    width = n - left - 1
    best = max(best, h * width)
return best
```

Linear time. For each row's histogram, apply this → O(n) per row, O(m · n) total.

----------------------------------------

## Step 6: Stitching It All Together

```
heights = [0] * n
best = 0
for i in 0..m-1:
    for c in 0..n-1:
        if matrix[i][c] == '1': heights[c] += 1
        else: heights[c] = 0
    best = max(best, largestRectangleInHistogram(heights))
return best
```

Each row update is O(n). Each histogram solve is O(n). Total: **O(m · n)**.

----------------------------------------

## Step 7: Name What We Did

This problem combines **two DP-flavored techniques**: "build a column-height accumulator as we sweep rows" and "largest rectangle in histogram via monotonic stack." It's a classic example of reducing a 2D problem to a sequence of 1D problems.

The column-height DP alone isn't a full DP per se — it's a rolling state. But the reframing from "find largest all-1s rectangle" to "for each bottom row, solve histogram" is the crux.

----------------------------------------

## Step 8: Complexity

Time: **O(m · n)**. Each cell is touched once in the row updates, and the histogram pass is O(n) per row.
Space: **O(n)** for the heights array and the stack.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int largestInHistogram(vector<int>& heights) {
    stack<int> stk;
    int best = 0;
    int n = heights.size();
    for (int i = 0; i <= n; ++i) {
        int curHeight = (i == n) ? 0 : heights[i];  // sentinel flushes remaining
        while (!stk.empty() && heights[stk.top()] > curHeight) {
            int h = heights[stk.top()]; stk.pop();
            int left = stk.empty() ? -1 : stk.top();
            int width = i - left - 1;
            best = max(best, h * width);
        }
        stk.push(i);
    }
    return best;
}

int maximalRectangle(vector<vector<char>>& matrix) {
    if (matrix.empty() || matrix[0].empty()) return 0;
    int m = matrix.size(), n = matrix[0].size();
    vector<int> heights(n, 0);
    int best = 0;
    for (int i = 0; i < m; ++i) {
        for (int c = 0; c < n; ++c) {
            heights[c] = (matrix[i][c] == '1') ? heights[c] + 1 : 0;
        }
        best = max(best, largestInHistogram(heights));
    }
    return best;
}
```

Notes:
- I use a sentinel `i == n` with height 0 to flush the stack cleanly at the end of each histogram.
- Heights reset to 0 on '0' cells; otherwise they accumulate.

----------------------------------------

## Step 10: Follow-up Questions

- **Largest square submatrix of 1s.** Much simpler DP: `dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])` for cells with 1; answer is max dp² (side squared).
- **Maximal rectangle in a grid where cells have weights and we maximize weighted sum.** Different DP — 2D prefix sums plus Kadane on the collapsed array.
- **Maximum all-ones rectangle count, not just the biggest.** Count rectangles using similar stack techniques; trickier.
- **Online matrix (cells flip 0↔1 over time).** Hard — updating heights and histograms efficiently needs segment trees.
- **Why does the monotonic stack find rectangles correctly?** Each popped bar is a "minimum height" rectangle; we find its maximal extent. Every rectangle's determining-height-bar gets its rectangle computed when popped.
- **What if the matrix is extremely large?** Stream-process row by row; we only need the current heights array, not the full matrix.
