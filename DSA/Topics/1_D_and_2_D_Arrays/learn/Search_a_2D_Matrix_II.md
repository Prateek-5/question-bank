# Search a 2D Matrix II — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Search_a_2D_Matrix_II.md`](../Search_a_2D_Matrix_II.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/search-a-2d-matrix-ii/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. This problem teaches **staircase search** — an elegant O(m + n) walk that beats per-row binary search. The key insight is *which corner to start from* and *why the others don't work*. Once you see it, you'll never forget.

**Map of this file (11 short sections):**

1. Read the problem
2. Don't confuse this with "Search a 2D Matrix I"
3. The natural brute force
4. Why binary-search-each-row works but isn't best
5. The pivot — find a corner where the decision is forced
6. The staircase walk
7. Why top-right (or bottom-left) — and why NOT top-left
8. Code
9. Trace it
10. Common pitfalls
11. The shape — saddleback search elsewhere

---

## 1. Read the problem

You're given an `m × n` matrix `matrix` and a `target` value. The matrix has two special properties:

1. **Each row is sorted ascending** (left to right).
2. **Each column is sorted ascending** (top to bottom).

Return `true` if `target` is in the matrix, `false` otherwise.

Example:

```
matrix =
   1   4   7  11  15
   2   5   8  12  19
   3   6   9  16  22
  10  13  14  17  24
  18  21  23  26  30
```

Verify the structure: every row goes left-to-right ascending (`1 < 4 < 7 < 11 < 15`, etc.) and every column goes top-to-bottom ascending (`1 < 2 < 3 < 10 < 18`, etc.).

Queries:
- `searchMatrix(matrix, 5)` → `true` (it's at row 1, col 1).
- `searchMatrix(matrix, 20)` → `false` (no 20 in the matrix).
- `searchMatrix(matrix, 30)` → `true` (bottom-right corner).

---

## 2. Don't confuse this with "Search a 2D Matrix I"

There's a similar LeetCode problem — "Search a 2D Matrix" (LC #74) — where the matrix has a **stronger** property: the entire grid is sorted "in reading order" (row-major). Specifically, the last value of each row is less than the first value of the next row. That makes the whole flattened matrix a single sorted array, and you can binary-search it in O(log(m × n)).

**This problem (LC #240) does NOT have that property.** Each row is sorted and each column is sorted, but a row's last value can be GREATER than the next row's first value.

Look at our example:

```
Row 1's last value:  19
Row 2's first value: 3       ← 3 is less than 19!
```

So if you flatten the matrix in row-major order, the resulting 1D array is NOT sorted (`..., 12, 19, 3, 6, ...`). Binary search on it fails.

This problem needs a different technique — one that uses the **row-sorted AND column-sorted** structure but not the stronger "globally sorted" property of LC #74.

---

## 3. The natural brute force

The most direct approach: scan every cell.

```cpp
bool searchMatrix(vector<vector<int>>& matrix, int target) {
    for (int r = 0; r < matrix.size(); r++) {
        for (int c = 0; c < matrix[0].size(); c++) {
            if (matrix[r][c] == target) return true;
        }
    }
    return false;
}
```

**O(m × n)** time, O(1) space. Correct but doesn't use the sorted structure at all.

For LeetCode's constraints (`m, n ≤ 300`), worst case is 9 × 10⁴ cells. Fast. But not the lesson the interviewer wants to test.

---

## 4. Why binary-search-each-row works but isn't best

Each row is sorted. So we can binary-search each row for the target:

```cpp
bool searchMatrix(vector<vector<int>>& matrix, int target) {
    for (auto& row : matrix) {
        if (binary_search(row.begin(), row.end(), target)) return true;
    }
    return false;
}
```

Per row: O(log n). m rows. Total: **O(m × log n)**.

For m = n = 300, that's `300 × log₂(300) ≈ 300 × 8.2 ≈ 2400` ops. Very fast.

But the problem has MORE structure than just "each row is sorted." Each COLUMN is also sorted. We're throwing away the column information. Can we use both?

**Pivot question:** is there a single walk through the matrix that uses both row-sortedness and column-sortedness to eliminate candidates more efficiently?

---

## 5. The pivot — find a corner where the decision is forced

Imagine standing at some cell `(r, c)` in the matrix, asking yourself "is `target` in this matrix?" Suppose you compare `matrix[r][c]` to `target`:

- If `matrix[r][c] == target`: found! Return `true`.
- If `matrix[r][c] > target`: we need a SMALLER cell to find target.
- If `matrix[r][c] < target`: we need a LARGER cell to find target.

The question is: **based on the row+column sorted structure, can we definitively eliminate part of the matrix and move on?**

That depends on which cell `(r, c)` we're standing at. Let me think through the four corners.

**Top-left corner `(0, 0)`:**

- All cells to the right (in row 0) are `≥ matrix[0][0]`.
- All cells below (in column 0) are `≥ matrix[0][0]`.

If `matrix[0][0] > target`, no cell in the matrix can be ≤ target (everything is ≥ this). Return `false`. ✓
If `matrix[0][0] < target`, we need to look right OR down — but we don't know which! Multiple directions = ambiguous = no clean elimination.

Top-left isn't a useful starting point.

**Top-right corner `(0, n−1)`:**

- All cells to the LEFT (in row 0) are `≤ matrix[0][n−1]`.
- All cells BELOW (in column n−1) are `≥ matrix[0][n−1]`.

If `matrix[0][n−1] > target`: all cells below are ≥ this, so they're ≥ target — they're too big. We can eliminate the entire column n−1 (except the current cell). **Move LEFT** to `(0, n−2)`. ✓
If `matrix[0][n−1] < target`: all cells to the left are ≤ this, so they're ≤ target — they're too small. We can eliminate the entire row 0 (except the current cell). **Move DOWN** to `(1, n−1)`. ✓
If `matrix[0][n−1] == target`: found.

**The decision is forced, in both directions.** No ambiguity.

**Bottom-left corner `(m−1, 0)`:** By symmetry, also has forced decisions (move UP if too big, RIGHT if too small).

**Bottom-right corner `(m−1, n−1)`:** Symmetric to top-left — ambiguous.

So the **top-right or bottom-left corner** is where to start. Each cell visited eliminates a whole row or column. We make at most `m + n` moves total.

---

## 6. The staircase walk

Starting at top-right `(r, c) = (0, n−1)`:

```
while in bounds (r < m AND c >= 0):
    if matrix[r][c] == target:
        return true
    if matrix[r][c] > target:
        c -= 1            # eliminate column c, move left
    else:  # matrix[r][c] < target
        r += 1            # eliminate row r, move down
return false
```

Each step makes one move — either left or down. Starting from `(0, n−1)`:

- Going left, `c` can decrease from `n−1` down to `−1` (off the left edge). That's at most `n` steps left.
- Going down, `r` can increase from `0` up to `m` (off the bottom edge). That's at most `m` steps down.

Total moves: at most `m + n`. **O(m + n)** time, O(1) space.

For m = n = 300, that's 600 ops. Three times faster than the binary-search-per-row approach.

The visual is a **staircase**: each "left" move chops off a column, each "down" move chops off a row. The remaining unexamined region is always a sub-rectangle. The boundary between examined and unexamined zigzags down-and-left like a stair.

---

## 7. Why top-right (or bottom-left) — and why NOT top-left

Let me make the corner-choice argument concrete with a small example. Suppose:

```
matrix =
   1   3   5
   4   6   8
   7   9  11
```

Search for `target = 6`.

**Starting at top-LEFT `(0, 0) = 1`:** `1 < 6`. We need a bigger value. But where? Right gives `3`, down gives `4`. Both are bigger. Both are reasonable. We have no way to decide which direction "must" lead to the target. We'd have to try both → backtracking → not O(m + n).

**Starting at top-RIGHT `(0, 2) = 5`:** `5 < 6`. We need a bigger value. Right doesn't exist (we're at the rightmost column). Below: `8`. That's bigger. Move down to `(1, 2) = 8`. `8 > 6`. We need smaller. Below: `11` — even bigger, eliminate. Left: `6`. Move left to `(1, 1) = 6`. Match! Return `true`.

**The top-right's superpower:** at every step, exactly ONE direction makes progress in each direction (left = smaller, down = larger). The other directions are guaranteed wrong.

> **Why?** Top-right starts at the largest of its row and the smallest of its column. So:
> - "Smaller" can only be found by going **left** (down would be even larger, by column-sort).
> - "Larger" can only be found by going **down** (left would be even smaller, by row-sort).
>
> Top-left has the opposite problem: it's the smallest of its row AND smallest of its column. "Larger" lives both right and down — ambiguous.

Symmetric reasoning applies to bottom-left.

---

## 8. Code

```cpp
bool searchMatrix(vector<vector<int>>& matrix, int target) {
    if (matrix.empty() || matrix[0].empty()) return false;
    int m = matrix.size();
    int n = matrix[0].size();

    int r = 0;
    int c = n - 1;             // start at top-right

    while (r < m && c >= 0) {
        if (matrix[r][c] == target) return true;
        if (matrix[r][c] > target) {
            c--;                // too big — column c is all too big below; move left
        } else {
            r++;                // too small — row r is all too small to the left; move down
        }
    }
    return false;
}
```

Six lines of logic.

**Bottom-left version** (equivalent — same algorithm, mirrored):

```cpp
bool searchMatrix(vector<vector<int>>& matrix, int target) {
    if (matrix.empty() || matrix[0].empty()) return false;
    int m = matrix.size(), n = matrix[0].size();
    int r = m - 1, c = 0;       // start at bottom-left
    while (r >= 0 && c < n) {
        if (matrix[r][c] == target) return true;
        if (matrix[r][c] > target) r--;     // too big — move up
        else                       c++;     // too small — move right
    }
    return false;
}
```

Same complexity. Pick whichever corner you find more intuitive.

**Python:**

```python
def searchMatrix(matrix, target):
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    r, c = 0, n - 1
    while r < m and c >= 0:
        if matrix[r][c] == target:
            return True
        if matrix[r][c] > target:
            c -= 1
        else:
            r += 1
    return False
```

---

## 9. Trace it

**Example: matrix above, search target = 5.**

```
matrix =
   1   4   7  11  15
   2   5   8  12  19
   3   6   9  16  22
  10  13  14  17  24
  18  21  23  26  30

m = 5, n = 5. Start at (r, c) = (0, 4), matrix[0][4] = 15.

Step 1: 15 vs 5. 15 > 5. Move left. c = 3.    matrix[0][3] = 11.
Step 2: 11 vs 5. 11 > 5. Move left. c = 2.    matrix[0][2] =  7.
Step 3:  7 vs 5.  7 > 5. Move left. c = 1.    matrix[0][1] =  4.
Step 4:  4 vs 5.  4 < 5. Move down. r = 1.    matrix[1][1] =  5.
Step 5:  5 vs 5. MATCH. Return true.  ✓
```

5 steps for a 5×5 matrix. Total visits = m + n − 1 worst case, here it was less.

**Example: same matrix, search target = 20.**

```
Start (0, 4) = 15.

15 < 20.  Move down. (1, 4) = 19.
19 < 20.  Move down. (2, 4) = 22.
22 > 20.  Move left. (2, 3) = 16.
16 < 20.  Move down. (3, 3) = 17.
17 < 20.  Move down. (4, 3) = 26.
26 > 20.  Move left. (4, 2) = 23.
23 > 20.  Move left. (4, 1) = 21.
21 > 20.  Move left. (4, 0) = 18.
18 < 20.  Move down. r = 5 — OUT OF BOUNDS.
Loop exits. Return false.  ✓
```

9 steps. For 5×5 the worst case is m + n − 1 = 9, achieved here (the search "weaves" the most).

Notice the **staircase pattern** of visited cells: `(0,4), (1,4), (2,4), (2,3), (3,3), (4,3), (4,2), (4,1), (4,0)`. It goes down-right-mostly, sometimes left. The unvisited cells form a shrinking rectangle each step.

---

## 10. Common pitfalls

1. **Starting at the wrong corner.** Top-left (`r=0, c=0`) is tempting but ambiguous — you don't know whether to move right or down. Stick with top-right or bottom-left.

2. **Wrong direction on the comparison.** From top-right: `matrix[r][c] > target` means MOVE LEFT (current column is too big going down), `matrix[r][c] < target` means MOVE DOWN (current row is too small going left). If you swap these, you'll skip the target.

3. **Off-by-one in the loop guard.** `while (r < m && c >= 0)`. The strict `<` on `r` checks "row is in bounds." `c >= 0` checks "column is in bounds." Forgetting either lets the indices go invalid.

4. **Returning the wrong thing when found.** The problem asks for a boolean. Return `true` immediately on match.

5. **Trying to use the LC #74 binary search.** As covered in §2 — this matrix is NOT globally sorted. Binary search on the flattened array fails. If unsure, check `matrix[0][n−1]` vs `matrix[1][0]` — if the first is greater, you're in LC #240 land, not LC #74.

6. **Forgetting the empty-matrix guard.** `matrix.empty()` and `matrix[0].empty()` handle the edge cases. Skipping them gives a crash on empty input.

---

## 11. The shape — saddleback search elsewhere

The staircase trick has a formal name: **saddleback search**. It applies wherever you have a 2D structure with the property that one corner is **monotonically related in two different ways to its two neighbor directions**.

| Where you'll see saddleback search | What's monotonic |
|---|---|
| **This problem** (Search 2D Matrix II) | rows ↑ and columns ↑ → top-right is "max of row, min of column" |
| Search in a Young tableau | rows ↑ and columns ↑ (same property) — same algorithm |
| Find a value in a 2D grid where rows and columns are sorted in opposite directions | adapted corners |
| 2D problems with "sum equals target" using sorted rows | start at a corner; move based on whether running sum is too big/small |
| Median of two sorted arrays (advanced — uses related "monotonic boundary" reasoning) | not directly, but the corner-elimination idea echoes |

**Pattern to internalize:**

> "When you have a 2D structure with sorted rows AND sorted columns, start at a corner where moving in each direction has the **opposite** effect on the value (one direction always larger, the other always smaller). The staircase walk eliminates one row or one column per step — O(m + n) total."

This is a tight specialty pattern but worth knowing — when it applies, it's elegant and unbeatable.

---

> **Self-check — the question to ask next time.**
>
> When you see a 2D problem where **rows are sorted AND columns are sorted** (and the matrix is NOT globally sorted), before reaching for binary search on each row, ask:
>
> > **"Can I start at a corner where one neighbor direction means 'smaller' and the other means 'larger,' so the comparison forces an unambiguous move?"**
>
> If yes, the staircase walk is O(m + n) — and beats O(m × log n) for any non-trivial matrix.

---

## Cross-references

- **Reference card (post-mastery):** [`../Search_a_2D_Matrix_II.md`](../Search_a_2D_Matrix_II.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Convert_1D_Array_Into_2D_Array.md`](./Convert_1D_Array_Into_2D_Array.md) (basic 2D indexing — required reading first)
  - [`Special_Positions_in_a_Binary_Matrix.md`](./Special_Positions_in_a_Binary_Matrix.md) (precompute-then-query — different speed-up for 2D)
  - Coming later (Searching topic): Search a 2D Matrix (LC #74) — global-sort version, uses binary search instead.
