# Lucky Numbers in a Matrix

**Problem Link:**
<a href="https://leetcode.com/problems/lucky-numbers-in-a-matrix/description/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/lucky-numbers-in-a-matrix/description/</a>

**Topic:**
Number Theory / Misc

----------------------------------------

## Step 1: What's a "Lucky" Number?

You have an m × n matrix of **distinct** integers. A cell's value is **lucky** if it's:
- The **minimum** of its row, AND
- The **maximum** of its column.

Return all lucky numbers (in any order).

Example matrix:
```
[[ 3,  7,  8],
 [ 9, 11, 13],
 [15, 16, 17]]
```

- Row 0: min is 3 (at col 0). Column 0 values: 3, 9, 15 — max is 15. So 3 is not a column max. Not lucky.
- Row 1: min is 9 (at col 0). Column 0 max is 15. Not lucky.
- Row 2: min is 15 (at col 0). Column 0 max is 15. Match! **15 is lucky.**

Output: `[15]`.

----------------------------------------

## Step 2: Brute Force

For each cell (i, j):
1. Check if it's the minimum of row i.
2. Check if it's the maximum of column j.
3. If both, add to result.

Per cell: O(m + n) work. Total: O(m · n · (m + n)). For 50 × 50 matrices that's 250,000 — fine. But we can do better with precomputation.

----------------------------------------

## Step 3: Precompute Row Mins and Column Maxes

Compute:
- `rowMin[i]` = minimum of row i.
- `colMax[j]` = maximum of column j.

Each takes O(m · n) total. Then for each cell (i, j):

```
if mat[i][j] == rowMin[i] AND mat[i][j] == colMax[j]:
    lucky.append(mat[i][j])
```

Per cell: O(1). Total: O(m · n).

----------------------------------------

## Step 4: How Many Lucky Numbers Are Possible?

Think about it. Suppose (i1, j1) and (i2, j2) are both lucky with i1 ≠ i2 and j1 ≠ j2. Denote mat[i1][j1] = A, mat[i2][j2] = B.

- A is row-min of row i1: `A ≤ mat[i1][j2]`.
- A is column-max of column j1: `A ≥ mat[i2][j1]`.
- B is row-min of row i2: `B ≤ mat[i2][j1]`.
- B is column-max of column j2: `B ≥ mat[i1][j2]`.

Chain: `A ≤ mat[i1][j2] ≤ B ≤ mat[i2][j1] ≤ A`. So A = B.

But values are distinct. Contradiction. So at most one lucky number exists (in different row and column). If two lucky numbers share a row or column, they must be equal — again impossible by distinctness.

**There is at most one lucky number.** But since the problem allows returning a list, our algorithm returns zero or one element.

----------------------------------------

## Step 5: Algorithm

```
rowMin = [min of each row]
colMax = [max of each column]
lucky = []
for i, j in all cells:
    if mat[i][j] == rowMin[i] and mat[i][j] == colMax[j]:
        lucky.append(mat[i][j])
return lucky
```

----------------------------------------

## Step 6: Trace

```
mat = [[ 3,  7,  8],
       [ 9, 11, 13],
       [15, 16, 17]]
```

rowMin: [3, 9, 15]. colMax: [15, 16, 17].

Check cells:
- (0, 0) = 3. rowMin[0] = 3 ✓. colMax[0] = 15 ≠ 3. No.
- (0, 1) = 7 ≠ rowMin[0] = 3. No.
- (0, 2) = 8 ≠ 3. No.
- (1, 0) = 9. rowMin[1] = 9 ✓. colMax[0] = 15 ≠ 9. No.
- (1, 1) = 11 ≠ rowMin[1] = 9. No.
- (2, 0) = 15. rowMin[2] = 15 ✓. colMax[0] = 15 ✓. **Lucky!** Add 15.
- Remaining cells: not row-mins.

Result: `[15]`. ✓

----------------------------------------

## Step 7: Why Precompute Separately?

A single cell being row-min OR column-max is a local property, but cheap to check if we've **summarized** the row/column once. Precomputing rowMin and colMax once amortizes the work.

Same pattern as **Special Positions in a Binary Matrix** — precompute row/column aggregates for fast per-cell lookups.

----------------------------------------

## Step 8: Name It

**Row/column aggregate precomputation.** A row-min + column-max filter. Related patterns:
- Saddle point in a matrix (min in row AND min in column, or other combinations).
- Special Positions in a Binary Matrix.
- Find the cell equal to the row sum (aggregate comparison).

Whenever a cell's "specialness" depends on row-wide or column-wide statistics, precompute those statistics once.

----------------------------------------

## Step 9: Complexity

Time: **O(m · n)** — precomputation and scan are both O(m · n).
Space: **O(m + n)** for rowMin and colMax.

----------------------------------------

## Step 10: C++ Implementation

```cpp
vector<int> luckyNumbers(vector<vector<int>>& mat) {
    int m = mat.size(), n = mat[0].size();
    vector<int> rowMin(m, INT_MAX), colMax(n, INT_MIN);

    for (int i = 0; i < m; ++i)
        for (int j = 0; j < n; ++j) {
            rowMin[i] = min(rowMin[i], mat[i][j]);
            colMax[j] = max(colMax[j], mat[i][j]);
        }

    vector<int> lucky;
    for (int i = 0; i < m; ++i)
        for (int j = 0; j < n; ++j) {
            if (mat[i][j] == rowMin[i] && mat[i][j] == colMax[j]) {
                lucky.push_back(mat[i][j]);
            }
        }
    return lucky;
}
```

Two passes: compute aggregates, then filter cells.

----------------------------------------

## Step 11: Follow-up Questions

- **Allow duplicates (not distinct values).** Multiple lucky cells possible; same algorithm still works.
- **Max of row, min of column ("saddle point").** Same framework, flip the predicate.
- **No preconditions on distinctness — proof caveat.** The "at most one" proof used distinctness; with duplicates, multiple can exist at equal values.
- **Very large matrix, find lucky without materializing it (streaming rows).** Compute rowMin online; track column running max; check at the end. Needs a second pass to verify.
- **Why at most one lucky number when values are distinct?** Chain inequalities force equality between any two candidates → contradiction with distinctness.
- **Instead of absolute min/max, top-2 in each.** Richer structure — different problem.
