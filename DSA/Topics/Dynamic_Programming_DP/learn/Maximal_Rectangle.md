# Maximal Rectangle — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Maximal_Rectangle.md`](../Maximal_Rectangle.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/maximal-rectangle/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/maximal-rectangle/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. **The lesson: reduce 2D problem to n 1D problems. For each row, build a HISTOGRAM of "consecutive 1-heights ending at this row," then solve LARGEST RECTANGLE IN HISTOGRAM (monotonic stack). Track max across all rows.**

**Map of this file (9 sections):**

1. Read the problem
2. Why brute force fails
3. The histogram reduction
4. Largest rectangle in histogram — monotonic stack
5. Code
6. Trace it
7. Why this captures every rectangle
8. Common pitfalls
9. The shape — DP + monotonic stack hybrid

---

## 1. Read the problem

Given an `m × n` binary matrix of `'0'` and `'1'`, find the AREA of the LARGEST AXIS-ALIGNED RECTANGLE filled entirely with `'1'`s.

**Example:**
```
1 0 1 0 0
1 0 1 1 1
1 1 1 1 1
1 0 0 1 0
```

Best rectangle: rows 1-2, cols 2-4 → 2×3 = **6**.

---

## 2. Why brute force fails

Enumerate every (top, bottom, left, right) quadruple and check all cells. O(m²·n²·m·n) = O(m³·n³). Way too slow.

We need to exploit structure.

---

## 3. The histogram reduction

> **Mini-refresher: for each row, collapse the matrix above into a HISTOGRAM.**
>
> `heights[c]` = consecutive 1s ending at row i, column c.
>
> For each '1', `heights[c]` increments from the previous row's value. For each '0', `heights[c]` resets to 0.
>
> Then: any axis-aligned all-1s rectangle with its BOTTOM at row i corresponds to a rectangle in this histogram.

So the problem reduces to: for each row, solve LARGEST RECTANGLE IN HISTOGRAM. Take the max.

For our example:
- Row 0: heights `[1,0,1,0,0]` → max rect 1.
- Row 1: `[2,0,2,1,1]` → max 3 (cols 2-4 at height 1).
- Row 2: `[3,1,3,2,2]` → max **6** (cols 2-4 at height 2).
- Row 3: `[4,0,0,3,0]` → max 4.

Overall max: 6.

---

## 4. Largest rectangle in histogram — monotonic stack

> **Mini-refresher: for each bar, find LEFT and RIGHT bounds where heights are ≥ this bar.**
>
> Maintain a stack of indices with STRICTLY INCREASING heights. When a SHORTER bar arrives:
> - POP the taller bar. Its rectangle has height = popped bar's height.
> - LEFT bound = new stack top (or -1 if empty).
> - RIGHT bound = current index.
> - Width = right - left - 1.
> - Area = height × width.
>
> O(n) per histogram via the amortized push/pop.

---

## 5. Code

**C++:**

```cpp
int largestInHistogram(vector<int>& heights) {
    stack<int> stk;
    int best = 0;
    int n = heights.size();
    for (int i = 0; i <= n; ++i) {
        int curHeight = (i == n) ? 0 : heights[i];   // sentinel flushes remaining
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

Complexity: **O(m · n)** time (each row updates heights in O(n), histogram solves in O(n)). **O(n)** extra space.

---

## 6. Trace it

For the example, after row 2 the heights array is `[3, 1, 3, 2, 2]`.

Largest rectangle in `[3, 1, 3, 2, 2]`:

```
stack starts empty.

i=0 (h=3): push. stack=[0].
i=1 (h=1): 1 < 3, pop 0 (h=3). left=-1, width=1, area=3.
  Now stack empty, push 1. stack=[1].
i=2 (h=3): push. stack=[1, 2].
i=3 (h=2): 2 < 3, pop 2 (h=3). left=1, width=3-1-1=1, area=3.
  3 not < 2 at stack top (h=1). Push. stack=[1, 3].
i=4 (h=2): 2 not < 2 at top (h=2). Push. stack=[1, 3, 4].
i=5 (sentinel h=0):
  pop 4 (h=2). left=3, width=5-3-1=1, area=2.
  pop 3 (h=2). left=1, width=5-1-1=3, area=6.   ← winner
  pop 1 (h=1). left=-1, width=5, area=5.

Max area = 6.  ✓
```

---

## 7. Why this captures every rectangle

Every all-1s rectangle has a UNIQUE BOTTOM ROW i. When we process row i, the heights array correctly records how far up each column extends as all-1s. Any rectangle with bottom at row i corresponds to a rectangle in the row-i histogram. So iterating over all bottom rows captures every all-1s rectangle.

---

## 8. Common pitfalls

1. **Forgetting the sentinel at i = n.** Without it, bars remaining in the stack at the end never get their rectangle computed.
2. **Strict vs non-strict comparison.** `> curHeight` (pop strictly taller). If you use `>=`, you'll pop equal-height bars and miss combining them — but it might still give the right max for some cases. Safer to use `>`.
3. **Treating `matrix[i][c]` as int.** It's a CHAR `'0'` or `'1'`. Compare to '1'.
4. **Resetting heights to current row instead of accumulating.** `heights[c] = heights[c] + 1` for '1', `0` for '0'. Don't overwrite from scratch.
5. **Allocating O(m · n) DP table.** Unnecessary — the heights array is O(n).

---

## 9. The shape — DP + monotonic stack hybrid

The pattern: **reduce a 2D problem to a sequence of 1D problems; solve each with the appropriate structure (here, a monotonic stack).**

| Problem | Reduction |
|---|---|
| **This problem** | per-row histogram |
| Maximal Square | DP `dp[i][j] = 1 + min(top, left, diag)` for `'1'` cells |
| Largest Submatrix With Rearrangements | sort rows, columns by 1-height |
| Trapping Rain Water II | priority-queue sweep |
| Skyline Problem | sweep events + heap |

**Pattern to internalize:**

> "For 2D max-rectangle of 1s: build column heights row by row, run LARGEST RECTANGLE IN HISTOGRAM per row. The 1D solver via monotonic stack is the workhorse."

---

> **Self-check — the question to ask next time.**
>
> When asked for the largest all-1s rectangle in a 2D grid:
>
> > **"For each row, build histogram of 1-heights ending here. Run LRH on each row via monotonic stack. Max across rows."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Maximal_Rectangle.md`](../Maximal_Rectangle.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Largest_Rectangle_in_Histogram.md`](../../Stack/learn/Largest_Rectangle_in_Histogram.md), [`Minimum_Path_Sum.md`](./Minimum_Path_Sum.md).
  - Coming next: [`Dungeon_Game.md`](./Dungeon_Game.md), [`Numbers_at_Most_N_Given_Digit_Set.md`](./Numbers_at_Most_N_Given_Digit_Set.md).
