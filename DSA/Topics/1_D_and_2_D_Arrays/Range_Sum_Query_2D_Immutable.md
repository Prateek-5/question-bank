# Range Sum Query 2D — Immutable

**Problem Link:**
<a href="https://leetcode.com/problems/range-sum-query-2d-immutable/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/range-sum-query-2d-immutable/</a>

**Topic:**
1-D & 2-D Arrays

----------------------------------------

## Step 1: Problem Spec

Given a 2D matrix, answer queries of the form: "**what's the sum of the sub-rectangle from (r1, c1) to (r2, c2)?**"

The matrix is immutable (no updates). Multiple queries expected.

Example matrix:
```
 3  0  1  4  2
 5  6  3  2  1
 1  2  0  1  5
 4  1  0  1  7
 1  0  3  0  5
```

sumRegion(2, 1, 4, 3) = sum of submatrix rows 2-4, cols 1-3 = `2 + 0 + 1 + 1 + 0 + 1 + 0 + 3 + 0 = 8`.

----------------------------------------

## Step 2: Brute Force Per Query

Loop over the submatrix, summing. O((r2 - r1 + 1) × (c2 - c1 + 1)) per query.

For small grids and few queries, fine. For many queries on a large grid, slow. Need to preprocess.

----------------------------------------

## Step 3: 2D Prefix Sums

Define `P[i][j]` = sum of the sub-rectangle from (0, 0) to (i-1, j-1). (1-indexed for cleaner formulas.)

Construction:
```
P[i][j] = matrix[i-1][j-1] + P[i-1][j] + P[i][j-1] - P[i-1][j-1]
```

The `- P[i-1][j-1]` subtracts the double-counted overlap between the top and left extensions.

O(m · n) preprocessing.

----------------------------------------

## Step 4: Query Formula

Sum of sub-rectangle (r1, c1) to (r2, c2) via **inclusion-exclusion** with prefix sums:

```
sumRegion(r1, c1, r2, c2) = P[r2+1][c2+1]
                          - P[r1][c2+1]          # subtract top slab
                          - P[r2+1][c1]          # subtract left slab
                          + P[r1][c1]             # add back over-subtracted corner
```

Drawing a picture:
```
   0 ....... c1  ...... c2 
 0 +-------+-------------+
   |  A    |     B       |
 r1+-------+-------------+
   |  C    |     D       |
 r2+-------+-------------+
```

We want D. We have:
- Total (P[r2+1][c2+1]) = A + B + C + D.
- Top (P[r1][c2+1]) = A + B.
- Left (P[r2+1][c1]) = A + C.
- Corner (P[r1][c1]) = A.

D = Total - Top - Left + Corner = (A+B+C+D) - (A+B) - (A+C) + A = D. ✓

Each query is O(1) after O(m · n) preprocessing.

----------------------------------------

## Step 5: Trace

Matrix above (5 × 5). Compute P (6 × 6 array, 1-indexed).

I won't compute the whole table, but for the query sumRegion(2, 1, 4, 3):
- P[5][4] - P[2][4] - P[5][1] - P[2][1] would give the answer.
- Let's just trust the formula and verify with the hand-computed 8.

For this example, the expected answer is 8. The formula handles it correctly (given the full table).

----------------------------------------

## Step 6: Why 1-Indexed P

Using (n+1) × (m+1) prefix tables with P[0][*] = P[*][0] = 0 avoids edge cases:
- No need to special-case the top row or left column.
- Query formula `P[r2+1][c2+1] - ...` works uniformly.

Matrix indices are 0-indexed (as usual); prefix table is 1-indexed (for ease).

----------------------------------------

## Step 7: Name It

**2D Prefix Sum**, also called "summed-area table" in computer graphics. Applications:
- Image processing (Haar-like feature detection).
- Histogram queries on rectangles.
- Any static "sum over sub-rectangle" problem.

Closely related to **1D prefix sum** and **inclusion-exclusion** principle.

----------------------------------------

## Step 8: Complexity

Preprocessing: **O(m · n)**.
Query: **O(1)**.
Space: **O(m · n)** for the prefix table.

----------------------------------------

## Step 9: C++ Implementation

```cpp
class NumMatrix {
    vector<vector<int>> P;
public:
    NumMatrix(vector<vector<int>>& matrix) {
        int m = matrix.size();
        int n = matrix[0].size();
        P.assign(m + 1, vector<int>(n + 1, 0));
        for (int i = 1; i <= m; ++i) {
            for (int j = 1; j <= n; ++j) {
                P[i][j] = matrix[i-1][j-1]
                        + P[i-1][j]
                        + P[i][j-1]
                        - P[i-1][j-1];
            }
        }
    }

    int sumRegion(int r1, int c1, int r2, int c2) {
        return P[r2+1][c2+1]
             - P[r1][c2+1]
             - P[r2+1][c1]
             + P[r1][c1];
    }
};
```

Constructor: O(m · n). Each query: O(1).

----------------------------------------

## Step 10: Follow-up Questions

- **Mutable matrix (updates allowed).** Prefix sums invalidate on updates. Use 2D Binary Indexed Tree or 2D Segment Tree — O(log m · log n) per update and query.
- **Max/min over sub-rectangle.** Different — sparse table in 2D, or 2D segment tree with max.
- **3D prefix sums.** Extend formula: 2³ = 8 inclusion-exclusion terms.
- **Non-rectangular regions (triangles, circles).** Prefix sums don't directly handle; use other techniques.
- **Count elements matching a predicate in sub-rectangle.** Preprocess per-predicate prefix count.
- **Memory-constrained version (can't afford O(m·n) table).** Row-wise prefix + per-query accumulation gives O(m) per query — middle ground.
