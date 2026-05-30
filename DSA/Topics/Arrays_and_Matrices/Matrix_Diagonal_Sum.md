# Matrix Diagonal Sum

**Problem Link:**
<a href="https://leetcode.com/problems/matrix-diagonal-sum/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/matrix-diagonal-sum/</a>

**Topic:**
Arrays & Matrices

----------------------------------------

## Step 1: What Are the Diagonals?

Given a square `n × n` matrix, sum its two diagonals:
- **Primary diagonal**: top-left to bottom-right. Cells (0, 0), (1, 1), (2, 2), ..., (n-1, n-1).
- **Secondary (anti) diagonal**: top-right to bottom-left. Cells (0, n-1), (1, n-2), (2, n-3), ..., (n-1, 0).

If n is odd, the center cell `(n/2, n/2)` is on **both** diagonals — it'd be double-counted. Subtract it once.

Return the sum.

Example (n = 3):
```
1 2 3
4 5 6
7 8 9
```
- Primary: 1 + 5 + 9 = 15.
- Secondary: 3 + 5 + 7 = 15.
- Sum: 30. Center (5) double-counted; subtract: 30 - 5 = **25**.

Example (n = 4):
```
 1  1  1  1
 1  1  1  1
 1  1  1  1
 1  1  1  1
```
- Primary: 1+1+1+1 = 4.
- Secondary: 1+1+1+1 = 4.
- Even n — no shared center.
- Sum: 8.

----------------------------------------

## Step 2: Direct Algorithm

```
total = 0
for i in 0..n-1:
    total += mat[i][i]             # primary
    total += mat[i][n - 1 - i]     # secondary

if n is odd:
    total -= mat[n/2][n/2]   # subtract double-counted center

return total
```

O(n) time, O(1) space.

Primary: row i, col i.
Secondary: row i, col n - 1 - i.

----------------------------------------

## Step 3: Trace on the 3x3 Example

```
i=0: total += mat[0][0]=1 → 1. total += mat[0][2]=3 → 4.
i=1: total += mat[1][1]=5 → 9. total += mat[1][1]=5 → 14. (Same cell! Double-counted.)
i=2: total += mat[2][2]=9 → 23. total += mat[2][0]=7 → 30.
```

n = 3 is odd. Subtract mat[1][1] = 5. Total = 25. ✓

----------------------------------------

## Step 4: Trace on the 4x4 Example

```
i=0: total += mat[0][0]=1 → 1. total += mat[0][3]=1 → 2.
i=1: total += mat[1][1]=1 → 3. total += mat[1][2]=1 → 4.
i=2: total += mat[2][2]=1 → 5. total += mat[2][1]=1 → 6.
i=3: total += mat[3][3]=1 → 7. total += mat[3][0]=1 → 8.
```

n = 4 is even. No subtraction. Total = 8. ✓

----------------------------------------

## Step 5: Why the Center is Double-Counted When n is Odd

For odd n, the primary diagonal cell at (n/2, n/2) coincides with the secondary diagonal cell at (n/2, n - 1 - n/2) = (n/2, n/2) because n - 1 - n/2 = (n - 1)/2 = n/2 when n is odd.

For even n, the center doesn't exist — (n - 1) / 2 is a half-integer; no cell sits on both diagonals.

So for odd n, exactly one cell overlaps, and we subtract it once.

----------------------------------------

## Step 6: Name It

**Simple matrix traversal** with index arithmetic. Not a "clever algorithm" — just carefully picking the right cells.

Similar patterns:
- Trace of a matrix (just primary diagonal).
- Anti-trace (secondary diagonal).
- Sum along any diagonal offset.
- Spiral traversal (more complex index math).

Getting index arithmetic right is a fundamental skill.

----------------------------------------

## Step 7: Complexity

Time: **O(n)** — n loop iterations.
Space: **O(1)**.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int diagonalSum(vector<vector<int>>& mat) {
    int n = mat.size();
    int total = 0;
    for (int i = 0; i < n; ++i) {
        total += mat[i][i];
        total += mat[i][n - 1 - i];
    }
    if (n % 2 == 1) {
        total -= mat[n / 2][n / 2];
    }
    return total;
}
```

Six lines. Clean.

----------------------------------------

## Step 9: Follow-up Questions

- **Diagonals of a rectangular (non-square) matrix.** Primary and secondary can be different lengths; careful indexing.
- **All anti-diagonals (grouped by `i + j`).** Group cells with same sum of indices.
- **All primary-parallel diagonals (grouped by `i - j`).** Group by difference.
- **Sum of top-k largest diagonal sums.** Compute each diagonal's sum, sort, take top k.
- **Minimum or maximum diagonal.** Min/max across diagonals.
- **What if the matrix contains very large values?** Use `long long` to avoid overflow.
