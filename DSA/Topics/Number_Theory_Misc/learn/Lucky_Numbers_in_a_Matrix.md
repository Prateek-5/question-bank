# Lucky Numbers in a Matrix — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Lucky_Numbers_in_a_Matrix.md`](../Lucky_Numbers_in_a_Matrix.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/lucky-numbers-in-a-matrix/description/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/lucky-numbers-in-a-matrix/description/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. **The lesson: PRECOMPUTE row-mins and col-maxes once. A "lucky" cell satisfies BOTH. With DISTINCT values, at most ONE lucky cell exists (chain-inequality proof).**

**Map of this file (7 sections):**

1. Read the problem
2. The row-min + col-max filter
3. Code
4. Trace it
5. Why at most one lucky number (with distinct values)
6. Common pitfalls
7. The shape — row/col aggregate precomputation

---

## 1. Read the problem

`m × n` matrix of DISTINCT integers. A cell is LUCKY iff it's the MIN of its row AND the MAX of its column. Return all lucky numbers.

**Example:**
```
[[ 3,  7,  8],
 [ 9, 11, 13],
 [15, 16, 17]]
```
- Row mins: 3, 9, 15. Col maxes: 15, 16, 17.
- 15 is row 2's min AND col 0's max → **lucky**. Output `[15]`.

---

## 2. The row-min + col-max filter

> **Mini-refresher: precompute aggregates once.**
>
> Compute `rowMin[i]` for each row and `colMax[j]` for each column. Then scan cells; report those equal to BOTH their row-min and col-max.
>
> Per cell check: O(1). Total: O(m · n).

---

## 3. Code

**C++:**

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
            if (mat[i][j] == rowMin[i] && mat[i][j] == colMax[j])
                lucky.push_back(mat[i][j]);
        }
    return lucky;
}
```

Complexity: **O(m · n)** time, **O(m + n)** space.

---

## 4. Trace it

Example:
- rowMin = [3, 9, 15]. colMax = [15, 16, 17].
- Cell (2, 0) = 15 = rowMin[2] AND colMax[0] → **lucky**.
- No other cell matches both.

Output: `[15]`.

---

## 5. Why at most one lucky number (with distinct values)

> **Mini-refresher: chain inequalities.**
>
> Suppose A at (i₁, j₁) and B at (i₂, j₂) are both lucky with i₁ ≠ i₂, j₁ ≠ j₂.
>
> - A = row-min of row i₁ → A ≤ mat[i₁][j₂].
> - A = col-max of col j₁ → A ≥ mat[i₂][j₁].
> - B = row-min of row i₂ → B ≤ mat[i₂][j₁].
> - B = col-max of col j₂ → B ≥ mat[i₁][j₂].
>
> Chain: A ≤ mat[i₁][j₂] ≤ B ≤ mat[i₂][j₁] ≤ A → A = B. But values are DISTINCT → contradiction.

So with distinct values, there's at most one lucky cell.

---

## 6. Common pitfalls

1. **Computing per-cell row min and col max inside the second loop.** O(m · n · (m + n)) — way slower than the two-pass approach.
2. **Initializing rowMin to 0.** If matrix has negatives, 0 is wrong. Use INT_MAX (or first element).
3. **Initializing colMax to 0.** Same issue — use INT_MIN.
4. **Returning early after the first match.** With distinct values there's at most one, but the loop costs nothing extra — let it finish.
5. **Assuming distinct values for non-distinct inputs.** With duplicates, multiple lucky cells can exist; the algorithm still finds them all.

---

## 7. The shape — row/col aggregate precomputation

The pattern: **summarize row/col stats once; then per-cell checks become O(1).**

| Problem | Aggregate |
|---|---|
| **This problem** | row min + col max |
| Special Positions in a Binary Matrix | row sum + col sum |
| Saddle Point | max in row + min in col |
| Set Matrix Zeroes | rows/cols containing 0 |
| Number of Equivalent Domino Pairs | grouped by sorted-tuple |

**Pattern to internalize:**

> "When a cell's 'specialness' depends on row-wide or col-wide aggregates, precompute the aggregates ONCE. Per-cell checks then O(1)."

---

> **Self-check — the question to ask next time.**
>
> When asked about cells with row/col-wide properties:
>
> > **"Precompute row-* and col-* aggregates. Two passes; second pass checks per-cell properties in O(1)."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Lucky_Numbers_in_a_Matrix.md`](../Lucky_Numbers_in_a_Matrix.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Self_Dividing_Numbers.md`](./Self_Dividing_Numbers.md).
  - Coming next: [`Subtract_Product_and_Sum_of_Digits.md`](./Subtract_Product_and_Sum_of_Digits.md), [`Number_of_Good_Pairs.md`](./Number_of_Good_Pairs.md).
