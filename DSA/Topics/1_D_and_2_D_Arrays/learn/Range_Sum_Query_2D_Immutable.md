# Range Sum Query 2D — Immutable — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Range_Sum_Query_2D_Immutable.md`](../Range_Sum_Query_2D_Immutable.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/range-sum-query-2d-immutable/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/range-sum-query-2d-immutable/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~25 minutes. This problem is the **2D version of prefix sums**. Once you understand the 4-term inclusion-exclusion formula for sub-rectangle sums, you've unlocked a building block that powers image processing (Haar features), histogram queries, summed-area tables, and many "count things in a rectangle" problems. Read after `Running_Sum_of_1D_Array.md` so the 1D recurrence is already in your head.

**Map of this file (11 short sections):**

1. Read the problem
2. The natural brute force (and why it's a poor fit)
3. Recap: 1D prefix sums in 30 seconds
4. The 2D prefix sum — what it represents
5. Building the 2D prefix sum (inclusion-exclusion, build step)
6. Querying a sub-rectangle (inclusion-exclusion, query step)
7. Why the 1-indexed `P` of size (m+1)×(n+1)
8. Code
9. Trace it
10. Common pitfalls
11. The shape — summed-area tables everywhere

---

## 1. Read the problem

You're given a 2D matrix `matrix` of size `m × n`. You must answer many queries of the form **"what is the sum of the sub-rectangle with corners (r1, c1) at the top-left and (r2, c2) at the bottom-right?"**

The matrix is **immutable** — once set, it doesn't change. The queries arrive after the constructor runs.

```
NumMatrix(matrix)                          # constructor — preprocess
sumRegion(r1, c1, r2, c2)                  # answer one query — should be fast
sumRegion(...)                              # another query
sumRegion(...)                              # another query
... possibly thousands of queries
```

Example: matrix =

```
        c=0  c=1  c=2  c=3  c=4
r=0      3    0    1    4    2
r=1      5    6    3    2    1
r=2      1    2    0    1    5
r=3      4    1    0    1    7
r=4      1    0    3    0    5
```

`sumRegion(2, 1, 4, 3)` asks for the sum of the sub-rectangle from `(2, 1)` to `(4, 3)`:

```
        c=1  c=2  c=3
r=2      2    0    1
r=3      1    0    1
r=4      0    3    0
```

Sum = `2 + 0 + 1 + 1 + 0 + 1 + 0 + 3 + 0 = 8`.

**The challenge:** the matrix is static (immutable), but there could be many queries. We want each query to be **fast** — ideally O(1).

---

## 2. The natural brute force (and why it's a poor fit)

The most direct approach — sum the sub-rectangle on each query:

```cpp
int sumRegion(int r1, int c1, int r2, int c2) {
    int total = 0;
    for (int r = r1; r <= r2; r++)
        for (int c = c1; c <= c2; c++)
            total += matrix[r][c];
    return total;
}
```

Per query: O((r2 − r1 + 1) × (c2 − c1 + 1)) — up to O(m × n) for the full matrix.

For Q queries: O(Q × m × n). For Q = 10⁴ and m = n = 300, that's 10⁴ × 9 × 10⁴ = 9 × 10⁸ — TLE territory.

The mismatch: the matrix is fixed, but we're recomputing sums from scratch every time. **We should be able to pay an O(m × n) preprocessing cost ONCE, then answer each query in O(1).**

That's the structural play for any "many queries on static data" problem: **preprocess once, query fast.**

---

## 3. Recap: 1D prefix sums in 30 seconds

> **Mini-refresher: 1D prefix sums.**
>
> Given `arr[0..n-1]`, define `prefix[i]` = `arr[0] + arr[1] + ... + arr[i-1]` (sum of the first `i` elements; `prefix[0] = 0` is the empty prefix).
>
> Then:
>
> ```
> sum of arr[l..r]  =  prefix[r + 1]  −  prefix[l]
> ```
>
> Building `prefix` is one linear pass; each range sum is **one subtraction = O(1)**.
>
> See [`Running_Sum_of_1D_Array.md`](./Running_Sum_of_1D_Array.md) for the derivation if needed.

We're going to generalize this to 2D. The 1D rule was "sum of a range = difference of two prefix values." The 2D rule will be "sum of a sub-rectangle = four prefix values combined via inclusion-exclusion."

---

## 4. The 2D prefix sum — what it represents

Define **`P[i][j]`** to mean: the **sum of the sub-rectangle from (0, 0) to (i − 1, j − 1)**, inclusive.

(Note the `i − 1`. We're 1-indexing `P` so that `P[0][j] = P[i][0] = 0` represents "the empty rectangle." This trick eliminates boundary special-cases — same reason we use `prefix[0] = 0` in 1D.)

Visualizing `P[i][j]`:

```
        c=0  c=1  c=2  c=3  c=4
r=0  ╔═════════════════╗
r=1  ║                 ║
r=2  ║   the rectangle ║
r=3  ║   (0,0) → (i-1, ║          P[i][j] = sum of values in
     ║      j-1)       ║                      this rectangle
     ╚═════════════════╝
```

For our 5×5 matrix above:

- `P[1][1]` = sum of the 1×1 rectangle at top-left = `matrix[0][0] = 3`.
- `P[1][2]` = sum of `matrix[0][0..1]` = `3 + 0 = 3`.
- `P[2][2]` = sum of the 2×2 rectangle = `3 + 0 + 5 + 6 = 14`.
- `P[5][5]` = sum of the **whole matrix**.

The full `P` table has dimensions `(m+1) × (n+1)` — one extra row of zeros at the top, one extra column of zeros at the left.

---

## 5. Building the 2D prefix sum (inclusion-exclusion, build step)

How do we fill in `P[i][j]` for a general cell?

Think recursively. `P[i][j]` covers the rectangle from `(0, 0)` to `(i−1, j−1)`. This rectangle has:

- The **single cell** at `(i−1, j−1)` — the bottom-right corner.
- The **rectangle above** it (rows `0` to `i−2`, columns `0` to `j−1`) — that's `P[i-1][j]`.
- The **rectangle to the left** of it (rows `0` to `i−1`, columns `0` to `j−2`) — that's `P[i][j-1]`.

If we add those together — `matrix[i−1][j−1] + P[i−1][j] + P[i][j−1]` — we **double-count** the overlap region (rows `0..i−2`, columns `0..j−2`). That overlap region is `P[i−1][j−1]`.

So:

```
P[i][j] = matrix[i−1][j−1] + P[i−1][j] + P[i][j−1] − P[i−1][j−1]
```

This is **inclusion-exclusion**: include the cell, include the top piece, include the left piece, then **subtract** the overlap once because it was counted twice.

> **Mini-refresher: inclusion-exclusion in plain English.**
>
> When you want to count items in a union of two overlapping regions:
>
> ```
> |A ∪ B| = |A| + |B| − |A ∩ B|
> ```
>
> Take the size of A, plus the size of B, but subtract the size of their intersection (since it was counted in both A and B).
>
> Our 2D prefix sum uses this twice. We're combining three pieces (cell, top, left) into one rectangle; the "top" and "left" overlap in the upper-left sub-rectangle, so we subtract that overlap once.

Visualization for `P[3][4]` (rectangle from (0,0) to (2, 3)):

```
       c=0  c=1  c=2  c=3       c=0  c=1  c=2  c=3
r=0   ┌───────────────┐       ┌───────────────┐ = top piece
r=1   │   top piece   │       │               │   (rows 0..1, cols 0..3)
r=2   ├───────────────┤
                                                  
                              c=0  c=1  c=2  c=3
                              ┌──────────┐       = left piece
                              │  left    │       (rows 0..2, cols 0..2)
                              │  piece   │
                              └──────────┘
                              
                              c=0  c=1  c=2
                              ┌──────────┐       = overlap
                              │  overlap │       (rows 0..1, cols 0..2)
                              │   (TL)   │       counted in BOTH top and left
                              └──────────┘
                              
                              + one cell at (2, 3) = matrix[2][3]
```

So `P[3][4] = matrix[2][3] + P[2][4] + P[3][3] − P[2][3]`.

Filling the entire table in a double loop:

```
for i = 1..m:
    for j = 1..n:
        P[i][j] = matrix[i-1][j-1] + P[i-1][j] + P[i][j-1] - P[i-1][j-1]
```

**O(m × n) preprocessing.** Each cell is computed in O(1) given its three neighbors (already filled in the same row-major scan).

---

## 6. Querying a sub-rectangle (inclusion-exclusion, query step)

Now the payoff. Given a query `sumRegion(r1, c1, r2, c2)`, we want the sum of the sub-rectangle from `(r1, c1)` to `(r2, c2)`.

We have `P[i][j]` — the sum of the rectangle from `(0, 0)` to `(i−1, j−1)`. Let's label four key rectangles:

```
                  c=0 ........... c=c1 ............... c=c2
                ┌──────────────────────────────────────┐
            r=0 │                                      │
                │       A          │       B           │
                │                  │                   │
        r=r1 ───┼──────────────────┼───────────────────┤
                │                  │                   │
                │       C          │       D           │
                │                  │                   │
        r=r2 ───┼──────────────────┼───────────────────┘
                │                  │
                ⋮
```

- `A` = rectangle from (0,0) to (r1−1, c1−1) — that's `P[r1][c1]`.
- `A + B` = rectangle from (0,0) to (r1−1, c2) — that's `P[r1][c2+1]`. So `B = P[r1][c2+1] − P[r1][c1] = P[r1][c2+1] − A`.
- `A + C` = rectangle from (0,0) to (r2, c1−1) — that's `P[r2+1][c1]`. So `C = P[r2+1][c1] − A`.
- `A + B + C + D` = rectangle from (0,0) to (r2, c2) — that's `P[r2+1][c2+1]`. So `D = P[r2+1][c2+1] − A − B − C`.

We want **`D`**. Substituting `B`, `C`, and `A`:

```
D = P[r2+1][c2+1] − A − B − C
  = P[r2+1][c2+1] − A − (P[r1][c2+1] − A) − (P[r2+1][c1] − A)
  = P[r2+1][c2+1] − A − P[r1][c2+1] + A − P[r2+1][c1] + A
  = P[r2+1][c2+1] − P[r1][c2+1] − P[r2+1][c1] + A
  = P[r2+1][c2+1] − P[r1][c2+1] − P[r2+1][c1] + P[r1][c1]
```

So:

```
sumRegion(r1, c1, r2, c2) = P[r2+1][c2+1]
                          − P[r1][c2+1]
                          − P[r2+1][c1]
                          + P[r1][c1]
```

**Four prefix-table lookups, three arithmetic operations. O(1) per query.**

> **Sanity check the formula on the picture:**
>
> Top-left big rectangle (A+B+C+D), MINUS top strip (A+B), MINUS left strip (A+C), PLUS the small upper-left (A) because it was over-subtracted (subtracted in both the top strip and the left strip — putting it back once balances the count).
>
> Result: D. ✓

---

## 7. Why the 1-indexed `P` of size (m+1)×(n+1)

You may have noticed the awkward `r+1` and `c+1` indices. They're not random.

If `P` were 0-indexed (size `m × n`), the formula would need special cases for queries that touch the matrix edges:

- `sumRegion(0, c1, r2, c2)` — there's no "row above r1 = 0," so `P[r1-1][...]` would be undefined.

By padding `P` with an extra row and column of zeros at the top and left (making it `(m+1) × (n+1)` with `P[0][*] = P[*][0] = 0`), the formula works uniformly **without edge cases**. The zeros in row 0 and column 0 represent "empty rectangle" and naturally contribute nothing.

> **Pattern to internalize:** when prefix structures need to handle queries that touch the array's beginning, **pad with a zero entry at the start**. The result is one extra slot of memory and one cleaner formula. Worth it every time.

---

## 8. Code

```cpp
class NumMatrix {
    vector<vector<int>> P;       // (m+1) × (n+1) 2D prefix sum

public:
    NumMatrix(vector<vector<int>>& matrix) {
        int m = matrix.size();
        int n = matrix[0].size();
        P.assign(m + 1, vector<int>(n + 1, 0));   // pad row 0 and col 0 with zeros

        for (int i = 1; i <= m; i++) {
            for (int j = 1; j <= n; j++) {
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

Constructor: O(m × n). Each query: O(1). Total memory: O(m × n).

**Python:**

```python
class NumMatrix:
    def __init__(self, matrix):
        m, n = len(matrix), len(matrix[0])
        self.P = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                self.P[i][j] = (matrix[i-1][j-1]
                              + self.P[i-1][j]
                              + self.P[i][j-1]
                              - self.P[i-1][j-1])

    def sumRegion(self, r1, c1, r2, c2):
        return (self.P[r2+1][c2+1]
              - self.P[r1][c2+1]
              - self.P[r2+1][c1]
              + self.P[r1][c1])
```

---

## 9. Trace it

Let me build `P` for a small 3×3 matrix:

```
matrix =
  3  0  1
  5  6  3
  1  2  0
```

`P` starts as a 4×4 grid of zeros.

```
Initial P:
       c=0  c=1  c=2  c=3
r=0     0    0    0    0
r=1     0
r=2     0
r=3     0
```

Build cell by cell:

```
i=1, j=1:  P[1][1] = matrix[0][0] + P[0][1] + P[1][0] - P[0][0]
                   = 3 + 0 + 0 - 0 = 3

i=1, j=2:  P[1][2] = matrix[0][1] + P[0][2] + P[1][1] - P[0][1]
                   = 0 + 0 + 3 - 0 = 3

i=1, j=3:  P[1][3] = matrix[0][2] + P[0][3] + P[1][2] - P[0][2]
                   = 1 + 0 + 3 - 0 = 4

i=2, j=1:  P[2][1] = matrix[1][0] + P[1][1] + P[2][0] - P[1][0]
                   = 5 + 3 + 0 - 0 = 8

i=2, j=2:  P[2][2] = matrix[1][1] + P[1][2] + P[2][1] - P[1][1]
                   = 6 + 3 + 8 - 3 = 14

i=2, j=3:  P[2][3] = matrix[1][2] + P[1][3] + P[2][2] - P[1][2]
                   = 3 + 4 + 14 - 3 = 18

i=3, j=1:  P[3][1] = matrix[2][0] + P[2][1] + P[3][0] - P[2][0]
                   = 1 + 8 + 0 - 0 = 9

i=3, j=2:  P[3][2] = matrix[2][1] + P[2][2] + P[3][1] - P[2][1]
                   = 2 + 14 + 9 - 8 = 17

i=3, j=3:  P[3][3] = matrix[2][2] + P[2][3] + P[3][2] - P[2][2]
                   = 0 + 18 + 17 - 14 = 21

Final P:
       c=0  c=1  c=2  c=3
r=0     0    0    0    0
r=1     0    3    3    4
r=2     0    8   14   18
r=3     0    9   17   21
```

Quick sanity check: `P[3][3]` should be the sum of the entire matrix. Sum = `3+0+1+5+6+3+1+2+0 = 21`. ✓

**Now a query: sumRegion(1, 1, 2, 2)** — sum of the 2×2 sub-rectangle from (1,1) to (2,2). That sub-rectangle is `[[6, 3], [2, 0]]`, sum = `6 + 3 + 2 + 0 = 11`.

Formula:

```
= P[r2+1][c2+1] - P[r1][c2+1] - P[r2+1][c1] + P[r1][c1]
= P[3][3]       - P[1][3]     - P[3][1]     + P[1][1]
= 21            - 4           - 9           + 3
= 11
```

✓ Matches.

**Another query: sumRegion(0, 0, 2, 2)** — sum of the entire matrix = 21.

```
= P[3][3] - P[0][3] - P[3][0] + P[0][0]
= 21      - 0       - 0       + 0
= 21  ✓
```

---

## 10. Common pitfalls

1. **Forgetting the `+ 1` offsets in queries.** The query uses `P[r2+1][c2+1]` (note the `+ 1`), not `P[r2][c2]`. Because `P` is 1-indexed relative to the matrix, the bottom-right corner of the query at matrix-position `(r2, c2)` corresponds to `P[r2+1][c2+1]`.

2. **Building `P` of size `m × n` instead of `(m+1) × (n+1)`.** Without the extra row/column of zeros, you'll need conditional logic for queries that touch row 0 or column 0. The padded version handles all queries uniformly.

3. **Mismatched indexing in the build loop.** The build uses `matrix[i-1][j-1]` (the 0-indexed matrix cell that corresponds to the 1-indexed P cell at (i, j)). Confusing the offset gives garbage.

4. **Computing each query in O(m × n) by re-summing.** That defeats the entire purpose. The point of the prefix sum is O(1) queries.

5. **Integer overflow on large matrices.** If `m × n` is large and values are big, the cumulative sum in `P` can exceed `INT_MAX`. For LeetCode's constraints (`m, n ≤ 200`, values ≤ 10⁵), the worst-case sum is `2 × 10⁹` — fits in `int32` but barely. For larger problems, use `long long`.

6. **Trying to maintain `P` after updates.** This is the "Immutable" version — `matrix` doesn't change. If you need updates, prefix sums become invalid after each change; use a 2D Fenwick tree (BIT) or 2D segment tree — both give O(log m × log n) per update and query.

---

## 11. The shape — summed-area tables everywhere

The 2D prefix sum has a more impressive name in computer graphics and computer vision: **summed-area table**. It powers:

| Domain / Problem | What 2D prefix sum buys you |
|---|---|
| **This problem** | sub-rectangle sums in O(1) after O(m × n) preprocess |
| Haar-like features (face detection, Viola-Jones) | rectangular feature sums in O(1) — fast enough for real-time |
| Image blurring (mean filter) | box-blur of any size in O(1) per output pixel |
| Histogram of oriented gradients (HOG) | rectangular gradient counts in O(1) |
| Count of cells with property X in a sub-rectangle | preprocess a per-cell 0/1 mask, then prefix-sum it |
| LeetCode Maximum Sum of Submatrix Not Larger Than K | 2D prefix sum + 1D Kadane-with-cap variant |
| LeetCode Matrix Block Sum | sub-rectangle sum centered on each cell |
| Counting subarrays/submatrices with sum equal to / divisible by K | combine 2D prefix with hash map |

**Pattern to internalize:**

> "Whenever the same expensive aggregate (sum, count, or-mask) is queried over many ranges of a static matrix, build a 2D prefix sum once. Each query becomes 4 lookups."

The 4-term inclusion-exclusion formula is worth memorizing — you'll write it many times.

---

> **Self-check — the question to ask next time.**
>
> When a problem involves **many sum / count queries over rectangular regions of a fixed 2D grid**, before writing nested loops per query, ask:
>
> > **"Can I preprocess a 2D prefix sum table once in O(m × n), then answer each query in O(1) via the 4-term inclusion-exclusion formula?"**
>
> If yes, you've reduced total time from O(Q × m × n) to O(m × n + Q). For large Q, this is the difference between TLE and AC.

---

## Cross-references

- **Reference card (post-mastery):** [`../Range_Sum_Query_2D_Immutable.md`](../Range_Sum_Query_2D_Immutable.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Running_Sum_of_1D_Array.md`](./Running_Sum_of_1D_Array.md) (the 1D prefix sum — required reading before this)
  - [`Special_Positions_in_a_Binary_Matrix.md`](./Special_Positions_in_a_Binary_Matrix.md) (per-row + per-column aggregation — a simpler "precompute and lookup" pattern)
  - [`Sum_of_All_Submatrices_Odd_Length_Subarrays.md`](./Sum_of_All_Submatrices_Odd_Length_Subarrays.md) (per-element contribution — a different angle on summing over subarrays)
  - Coming later: Range Sum Query Mutable (Segment Tree topic) — for when updates ARE allowed.
