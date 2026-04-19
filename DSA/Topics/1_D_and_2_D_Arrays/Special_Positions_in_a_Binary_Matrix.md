# Special Positions in a Binary Matrix

**Problem Link:**
https://leetcode.com/problems/special-positions-in-a-binary-matrix/

**Topic:**
1-D & 2-D Arrays

----------------------------------------

## Step 1: Define "Special"

A position (r, c) in a binary matrix is **special** if:
- `mat[r][c] == 1`, and
- All other cells in **row r** are 0, and
- All other cells in **column c** are 0.

Count special positions.

Example:
```
1 0 0
0 0 1
1 0 0
```

- (0, 0) = 1. Row 0: [1, 0, 0] — the 1 is only at (0, 0). Column 0: [1, 0, 1]. Two 1s. Not special.
- (1, 2) = 1. Row 1: [0, 0, 1] — only at (1, 2). Column 2: [0, 1, 0] — only at (1, 2). Special. ✓
- (2, 0) = 1. Column 0 has two 1s. Not special.

Count: 1.

----------------------------------------

## Step 2: Precompute Row and Column Sums

Naive: for each cell that's 1, check row and column for other 1s. O(n²) cells × O(n + m) check = O(n² · (n+m)).

Better: **precompute** row sums and column sums in O(m·n). Then checking a cell is O(1).

```
rowSum[i] = sum of row i
colSum[j] = sum of col j

count = 0
for each (r, c) with mat[r][c] == 1:
    if rowSum[r] == 1 and colSum[c] == 1:
        count++
return count
```

Why does this work? If (r, c) is 1 and its row sum is 1, the only 1 in row r is at (r, c). Same for column.

O(m · n) time, O(m + n) space.

----------------------------------------

## Step 3: Trace

Matrix:
```
1 0 0
0 0 1
1 0 0
```

rowSum = [1, 1, 1]. colSum = [2, 0, 1].

Check each cell with value 1:
- (0, 0): rowSum[0]=1 ✓, colSum[0]=2 ✗. Not special.
- (1, 2): rowSum[1]=1 ✓, colSum[2]=1 ✓. Special!
- (2, 0): rowSum[2]=1 ✓, colSum[0]=2 ✗. Not special.

Count: 1. ✓

----------------------------------------

## Step 4: Why Precomputation Helps

Without precomputation, for each 1-cell we re-scan its row and column. Redundant: many cells share rows/columns.

Precomputing once (O(m·n)) amortizes the row/column sum cost. Each cell's check becomes O(1) lookup.

Classic speed-up: pay upfront for aggregate structures, then query in constant time.

----------------------------------------

## Step 5: Name It

**Row-and-column sum preprocessing**. A specialized case of the more general prefix-sum technique.

Related:
- Lucky Numbers in a Matrix (per-row min vs per-column max).
- Find Valid Matrix Given Row and Column Sums.
- Row With Maximum Ones.

Whenever a problem asks about "this cell's relationship to its row and column," precomputing aggregates is usually the move.

----------------------------------------

## Step 6: Complexity

Time: **O(m · n)** for precomputation + O(m · n) for checking. Total O(m · n).
Space: O(m + n) for row and column sums.

Beats the naive O(m · n · (m + n)).

----------------------------------------

## Step 7: C++ Implementation

```cpp
int numSpecial(vector<vector<int>>& mat) {
    int m = mat.size(), n = mat[0].size();
    vector<int> rowSum(m, 0), colSum(n, 0);

    for (int r = 0; r < m; ++r) {
        for (int c = 0; c < n; ++c) {
            rowSum[r] += mat[r][c];
            colSum[c] += mat[r][c];
        }
    }

    int count = 0;
    for (int r = 0; r < m; ++r) {
        for (int c = 0; c < n; ++c) {
            if (mat[r][c] == 1 && rowSum[r] == 1 && colSum[c] == 1) {
                count++;
            }
        }
    }
    return count;
}
```

Two passes: first compute sums, then check cells. Clean separation.

----------------------------------------

## Step 8: Follow-up Questions

- **Count "almost special" positions (row sum ≤ k, column sum ≤ k).** Just change the threshold.
- **Positions unique to their row only (ignore column).** Remove column check.
- **Return the positions, not just count.** Record (r, c) pairs.
- **Dynamic matrix (cells change).** Maintain rowSum and colSum incrementally.
- **3D version.** Row, column, depth sums.
- **Matrix with values beyond 0/1.** Special might mean "distinct from row/column others"; different definition.
