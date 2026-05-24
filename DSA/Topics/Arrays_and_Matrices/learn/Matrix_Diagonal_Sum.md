# Matrix Diagonal Sum — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Matrix_Diagonal_Sum.md`](../Matrix_Diagonal_Sum.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/matrix-diagonal-sum/

---

## How to use this file

Paced for someone seeing the problem for the first time. Reading time: ~15 minutes. This problem teaches the **most important muscle for any 2D problem**: deriving index formulas. Specifically, the two diagonals of an n×n matrix have index formulas you should be able to write from memory by the end of this. The parity catch (the "shared center" when `n` is odd) is the only real subtle point.

**Map of this file (10 short sections):**

1. Read the problem
2. 2D matrix indexing refresher
3. The primary diagonal — what is it, and how do I index it?
4. The anti-diagonal — what is it, and how do I index it?
5. The double-counting trap when `n` is odd
6. Why the trap doesn't happen when `n` is even
7. Code
8. Trace it
9. Common pitfalls
10. The shape — index-formula problems are everywhere

---

## 1. Read the problem

You're given a **square** matrix `mat` of size `n × n` (same number of rows and columns). Compute and return the sum of the matrix's **two diagonals**:

- **Primary diagonal**: top-left to bottom-right.
- **Secondary diagonal** (also called the **anti-diagonal**): top-right to bottom-left.

**Important edge:** if `n` is odd, the two diagonals share their center cell. You must include that cell in the sum **only once**, not twice.

Example for `n = 3`:

```
mat =
  1  2  3
  4  5  6
  7  8  9
```

- Primary diagonal cells: 1, 5, 9 (top-left to bottom-right). Sum = 15.
- Anti-diagonal cells: 3, 5, 7 (top-right to bottom-left). Sum = 15.
- The center cell `5` is on BOTH diagonals (`n` is odd → shared).
- Combined sum, **counting 5 only once**: 15 + 15 − 5 = **25**.

Example for `n = 4`:

```
mat =
  1  2  3  4
  5  6  7  8
  9 10 11 12
 13 14 15 16
```

- Primary diagonal cells: 1, 6, 11, 16. Sum = 34.
- Anti-diagonal cells: 4, 7, 10, 13. Sum = 34.
- `n` is even — **no shared center**. The two diagonals don't intersect at any cell.
- Combined sum: 34 + 34 = **68**.

---

## 2. 2D matrix indexing refresher

> **Mini-refresher: how to index a 2D matrix.**
>
> A 2D matrix in most languages is stored as an array of arrays (a "list of rows"). To get the value at row `r` and column `c`, you write `mat[r][c]`.
>
> Visually, for the 3×3 above:
>
> ```
>             c=0  c=1  c=2
>           ┌─────────────────┐
>     r=0   │  1    2    3   │
>     r=1   │  4    5    6   │
>     r=2   │  7    8    9   │
>           └─────────────────┘
> ```
>
> So `mat[0][0] = 1`, `mat[0][2] = 3` (top-right), `mat[1][1] = 5` (middle), `mat[2][0] = 7` (bottom-left), `mat[2][2] = 9` (bottom-right).
>
> **Conventions to lock in:**
> - **Row index** is the **first** subscript.
> - **Column index** is the **second** subscript.
> - Both are **0-indexed** in C++/Python/Java (first row is `r = 0`, not `r = 1`).
> - For an `n × n` matrix, both `r` and `c` range over `0, 1, ..., n-1`.

---

## 3. The primary diagonal — what is it, and how do I index it?

The primary diagonal runs from the **top-left corner** to the **bottom-right corner**. Let me list its cells for our 3×3:

```
mat =                  Primary diagonal cells:
  1  2  3                ●  ·  ·          (0, 0)
  4  5  6                ·  ●  ·          (1, 1)
  7  8  9                ·  ·  ●          (2, 2)
```

The cells visited are `(0, 0)`, `(1, 1)`, `(2, 2)`. Notice: **row index equals column index** at every step.

So the indexing formula for the primary diagonal is:

```
For i in 0..n-1:  cell is mat[i][i]
```

That's it. Walking `i` from `0` to `n − 1` and reading `mat[i][i]` each time gives you all the cells.

> **Mini-exercise:** What are the primary-diagonal cells for a 4×4 matrix?
>
> <details>
> <summary>Click to expand answer</summary>
>
> `(0, 0)`, `(1, 1)`, `(2, 2)`, `(3, 3)`. So `mat[0][0]`, `mat[1][1]`, `mat[2][2]`, `mat[3][3]`.
> </details>

---

## 4. The anti-diagonal — what is it, and how do I index it?

The anti-diagonal runs from the **top-right corner** to the **bottom-left corner**. For the 3×3:

```
mat =                  Anti-diagonal cells:
  1  2  3                ·  ·  ●          (0, 2)
  4  5  6                ·  ●  ·          (1, 1)
  7  8  9                ●  ·  ·          (2, 0)
```

Cells: `(0, 2)`, `(1, 1)`, `(2, 0)`. Row index goes 0, 1, 2 (downward as before). Column index goes 2, 1, 0 (**leftward**).

Let me see if there's a formula linking the row and column. The matrix is 3×3, so `n = 3`.

```
row i=0  →  col = 2   →  hmm, that's n - 1 - 0 = 2. ✓
row i=1  →  col = 1   →  n - 1 - 1 = 1. ✓
row i=2  →  col = 0   →  n - 1 - 2 = 0. ✓
```

So the column for the anti-diagonal at row `i` is `n - 1 - i`. The full formula:

```
For i in 0..n-1:  cell is mat[i][n - 1 - i]
```

> **Why `n - 1 - i`?** As `i` goes up by 1 (we move down one row), the column needs to go down by 1 (we move left one column). The expression `n - 1 - i` does exactly that: when `i = 0`, column is `n - 1` (rightmost); when `i = n - 1`, column is `0` (leftmost). It's a mirror flip of `i` across the matrix width.

> **Mini-exercise:** For a 4×4 matrix (`n = 4`), what is the anti-diagonal column at row `i = 2`?
>
> <details>
> <summary>Click to expand answer</summary>
>
> Column = `n - 1 - i` = `4 - 1 - 2` = `1`. So the cell is `mat[2][1]`. (Verify: for 4×4 the anti-diagonal cells are `(0, 3), (1, 2), (2, 1), (3, 0)` — yes, `(2, 1)` matches.)
> </details>

---

## 5. The double-counting trap when `n` is odd

If we just sum both diagonals using the formulas above, we get:

```
total = sum over i of mat[i][i]                  (primary)
      + sum over i of mat[i][n - 1 - i]          (anti-diagonal)
```

That's two passes (or one combined pass) over `i = 0..n-1`. We touch `2n` cells.

**But wait** — for `n = 3`, the diagonals intersected at `(1, 1)`. Let me check whether our formulas both pick that cell up:

- At `i = 1`: primary formula gives `mat[1][1] = 5`. ✓
- At `i = 1`: anti-diagonal formula gives `mat[1][n - 1 - 1] = mat[1][1] = 5`. ✓

**Both formulas hit `mat[1][1]` at `i = 1`.** So `5` gets added **twice** to our running total. That's the trap.

For the 3×3:

```
Primary sum: mat[0][0] + mat[1][1] + mat[2][2] = 1 + 5 + 9 = 15
Anti sum:    mat[0][2] + mat[1][1] + mat[2][0] = 3 + 5 + 7 = 15
                                              ↑
                                     this 5 is the SAME cell
                                     already counted in primary
Naive total: 15 + 15 = 30          ← WRONG (5 counted twice)
Correct:     30 − 5 = 25           ← subtract one copy of the shared center
```

So when `n` is odd, the **center cell** `mat[n/2][n/2]` is counted by both diagonal formulas. We have to subtract one copy of it from the naive total.

---

## 6. Why the trap doesn't happen when `n` is even

For `n = 4`, let me check whether there's any `i` where both formulas hit the same cell.

- Primary: `mat[i][i]`
- Anti-diagonal: `mat[i][n - 1 - i]` = `mat[i][3 - i]`

They'd refer to the same cell when `i == n - 1 - i`, i.e., `2i == n - 1`, i.e., `i == (n - 1) / 2`.

For `n = 4`: `(4 - 1) / 2 = 1.5`. Not an integer. There's no `i` that satisfies this, so no overlap. ✓

For `n = 3`: `(3 - 1) / 2 = 1`. Integer — overlap at `i = 1` (which is `(n/2, n/2) = (1, 1)`).

**General rule:**
- `n` odd → overlap at the single center cell `(n/2, n/2)` (using integer division). Subtract one copy.
- `n` even → no overlap. No correction needed.

That's the only edge case in the problem.

---

## 7. Code

```cpp
int diagonalSum(vector<vector<int>>& mat) {
    int n = mat.size();
    int total = 0;
    for (int i = 0; i < n; i++) {
        total += mat[i][i];                  // primary diagonal cell
        total += mat[i][n - 1 - i];          // anti-diagonal cell
    }
    if (n % 2 == 1) {                        // odd n → subtract the double-counted center
        total -= mat[n / 2][n / 2];
    }
    return total;
}
```

Six lines. Read each:

- `n = mat.size()` — number of rows (which equals number of columns in a square matrix).
- The loop walks `i` once, adding both diagonal cells per iteration.
- The `if` corrects the double-count when needed.
- Return.

> **Why `n % 2 == 1` instead of `n & 1`?** Both check "is `n` odd?" `% 2` is more universally readable; `& 1` is slightly faster (irrelevant here). Pick the more readable form unless you have a reason to optimize.

---

## 8. Trace it

**On the 3×3 example:**

```
mat =
  1  2  3
  4  5  6
  7  8  9

n = 3.  total = 0.

i = 0:
    total += mat[0][0] = 1.            total = 1.
    total += mat[0][3 - 1 - 0] = mat[0][2] = 3.   total = 4.

i = 1:
    total += mat[1][1] = 5.            total = 9.
    total += mat[1][3 - 1 - 1] = mat[1][1] = 5.   total = 14.   ← same cell counted again!

i = 2:
    total += mat[2][2] = 9.            total = 23.
    total += mat[2][3 - 1 - 2] = mat[2][0] = 7.   total = 30.

After loop:  total = 30.

n % 2 == 1 is true (3 is odd).
total -= mat[3/2][3/2] = mat[1][1] = 5.            total = 25.

Return 25.  ✓
```

Notice at `i = 1` both formulas resolved to `mat[1][1]` — the trap fires there, and we corrected it after the loop.

**On the 4×4 example (all 1s):**

```
n = 4.  total = 0.

i = 0:  total += mat[0][0] = 1 → 1.   total += mat[0][3] = 1 → 2.
i = 1:  total += mat[1][1] = 1 → 3.   total += mat[1][2] = 1 → 4.
i = 2:  total += mat[2][2] = 1 → 5.   total += mat[2][1] = 1 → 6.
i = 3:  total += mat[3][3] = 1 → 7.   total += mat[3][0] = 1 → 8.

After loop: total = 8.

n % 2 == 0 → no correction.

Return 8.  ✓
```

At no `i` did both formulas resolve to the same cell. No correction needed.

---

## 9. Common pitfalls

1. **Forgetting the `n` odd correction.** Naive sum is `2 × diagonal_sum`, off by one center cell for odd `n`. Test with a 3×3 to catch this.

2. **Writing `mat[n - i][n - 1 - i]` or similar typos.** The primary diagonal is `mat[i][i]`, the anti-diagonal is `mat[i][n - 1 - i]`. Mixing them up gives garbage.

3. **Treating the matrix as non-square.** This problem guarantees square. If it didn't, the anti-diagonal formula would be different (you'd use `cols - 1 - i`, not `n - 1 - i`).

4. **Using `n / 2` with floating-point.** In Python, `n / 2` is `1.5` for `n = 3` (floating-point division). Use `n // 2` for integer division so you get `1`. In C++/Java, `int / int` is already integer division (truncation), so `3 / 2 == 1`.

5. **Overflow on large matrices.** If `n` is huge and cell values are near `INT_MAX`, the sum can overflow. Use `long long` if the problem hints at large values. (For LeetCode #1572 the constraints are small.)

---

## 10. The shape — index-formula problems are everywhere

The whole skill in this problem was **deriving a formula linking row and column for a specific pattern of cells**. That skill transfers everywhere in 2D problems:

| Pattern | Formula | Example use |
|---|---|---|
| **Primary diagonal** | `mat[i][i]` | this problem |
| **Anti-diagonal** | `mat[i][n - 1 - i]` | this problem |
| **All cells with same `i + j`** | group by `r + c` (one anti-diagonal per group) | "Find max value on each anti-diagonal" |
| **All cells with same `i - j`** | group by `r - c` (one primary-parallel diagonal) | bishop moves in chess |
| **Spiral order** | direction vectors `(dr, dc)` | Spiral Matrix II |
| **Rotate 90° clockwise** | `out[i][j] = mat[n - 1 - j][i]` | Rotate Image |
| **Transpose** | `out[i][j] = mat[j][i]` | Transpose Matrix |
| **Reflect horizontally** | `out[i][j] = mat[i][n - 1 - j]` | image flip |

The technique to recognize: **list cells the pattern visits, look for the algebraic link between row and column** — then turn it into a formula. With practice, you'll write these formulas without conscious effort.

---

> **Self-check — the question to ask next time.**
>
> When a problem describes a pattern of cells in a matrix (a diagonal, a spiral, a rotation, a reflection), before writing nested loops, ask:
>
> > **"What's the algebraic relationship between row and column for the cells in this pattern? Once I have that, can I walk a single index `i` and derive both `r` and `c` from it?"**
>
> If yes, you've turned a `O(n²)` "look at all cells" problem into a `O(n)` "walk one parameter" problem. (When the pattern only visits `O(n)` cells out of `n²`, this can be a huge speedup.)

---

## Cross-references

- **Reference card (post-mastery):** [`../Matrix_Diagonal_Sum.md`](../Matrix_Diagonal_Sum.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:** [`Spiral_Matrix_II.md`](./Spiral_Matrix_II.md) (next-level index-formula problem — direction vectors)
