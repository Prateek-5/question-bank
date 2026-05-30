# Convert 1D Array Into 2D Array — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Convert_1D_Array_Into_2D_Array.md`](../Convert_1D_Array_Into_2D_Array.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/convert-1d-array-into-2d-array/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/convert-1d-array-into-2d-array/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. This problem teaches the **1D-to-2D index mapping** — a tiny piece of arithmetic that appears everywhere: how 2D arrays are stored in memory, how matrices are flattened for transport, how cache-friendly traversals work. The mapping `(k → row, col)` and its inverse `(row, col → k)` are skills you'll use for the rest of your career.

**Map of this file (9 short sections):**

1. Read the problem
2. The size-check guard
3. Visualize the mapping
4. Deriving the formula
5. Inverse direction: 2D → 1D
6. Code
7. Trace it
8. Common pitfalls
9. The shape — index-mapping in memory, storage, and traversals

---

## 1. Read the problem

You're given a 1D array `original`, plus two integers `m` and `n`. Build and return a 2D matrix of size `m × n` (`m` rows, `n` columns) filled with `original`'s elements, **filled row by row** (row 0 first, then row 1, etc.).

**Size guard:** if `original.length ≠ m × n`, return an empty 2D array `[]`.

Examples:

```
original = [1, 2, 3, 4], m = 2, n = 2
Output:    [[1, 2],
            [3, 4]]

original = [1, 2, 3], m = 1, n = 3
Output:    [[1, 2, 3]]

original = [1, 2], m = 1, n = 1
Output:    []                  (because 1*1 = 1, but original has 2 elements)
```

So the algorithm is: validate the size, then place each `original[k]` at the correct 2D position.

---

## 2. The size-check guard

> **Why do we check `original.length == m * n` first?**
>
> An `m × n` 2D array has exactly `m × n` cells. If `original` has more elements, we'd have leftovers; fewer, and some cells go unfilled. Neither is acceptable — the problem says return `[]`.
>
> The first line of the algorithm:
>
> ```
> if original.length != m * n:
>     return empty 2D array
> ```
>
> Catches this edge case before we touch any indices. Constant time.

---

## 3. Visualize the mapping

For `original = [1, 2, 3, 4, 5, 6]`, `m = 2`, `n = 3`, the expected output is:

```
       col 0  col 1  col 2
       ─────────────────────
row 0    1     2      3
row 1    4     5      6
```

So we want:

```
original[0] = 1  →  (row 0, col 0)
original[1] = 2  →  (row 0, col 1)
original[2] = 3  →  (row 0, col 2)
original[3] = 4  →  (row 1, col 0)
original[4] = 5  →  (row 1, col 1)
original[5] = 6  →  (row 1, col 2)
```

Look at the columns. As `k` increases by 1, the column cycles through `0, 1, 2, 0, 1, 2, ...` — **`col = k mod n`**.

Look at the rows. The row stays at `0` for the first `n = 3` elements, then becomes `1` for the next 3 — **`row = k / n` (integer division)**.

So:

```
For each k in 0..(m*n - 1):
    row = k / n      (integer division)
    col = k mod n
    result[row][col] = original[k]
```

That's the whole algorithm.

> **Mini-refresher: integer division and modulo.**
>
> Integer division `a / b` (in C++/Java for integers, `a // b` in Python) returns the **whole-number quotient**, throwing away any fractional part.
>
> ```
> 7 / 3 = 2          (because 3 × 2 = 6, remainder 1)
> 6 / 3 = 2          (exact)
> 0 / 3 = 0
> ```
>
> Modulo `a mod b` (written `a % b` in most languages) returns the **remainder** after dividing.
>
> ```
> 7 % 3 = 1
> 6 % 3 = 0          (exact division — remainder 0)
> 0 % 3 = 0
> ```
>
> These two operations together split any non-negative integer `k` into its `(quotient, remainder)` against any divisor `n` — the basis of every base-`n` representation, and the basis of our index mapping here.

---

## 4. Deriving the formula

Let me re-derive `row = k / n` from first principles to make it concrete.

`original[k]` is the `k`-th element in linear order (0-indexed). In the 2D layout, we fill **row 0** with `original[0..n-1]`, **row 1** with `original[n..2n-1]`, **row 2** with `original[2n..3n-1]`, and so on.

Generally, row `r` holds `original[r*n .. (r+1)*n - 1]`.

If `k` is somewhere in `[r*n, (r+1)*n)`, then `r = floor(k / n)`. That's exactly **integer division**: `r = k / n` in C++/Java.

And the column? Within row `r`, the column starts at 0 for `original[r*n]` and increases by 1 each step. So `col = k - r * n = k mod n`. That's **modulo**: `c = k % n`.

So:

```
k = row * n + col      ← forward formula (2D → 1D)
row = k / n            ← inverse (1D → 2D)
col = k mod n          ← inverse (1D → 2D)
```

**These are inverse formulas of each other.** Both directions are O(1) arithmetic.

---

## 5. Inverse direction: 2D → 1D

The same arithmetic flips both ways. If you have a 2D position `(row, col)` and want the flat index in 1D:

```
k = row * n + col
```

Example: `(row, col) = (1, 2)` in a matrix with `n = 3` columns → flat index `k = 1 * 3 + 2 = 5`. Check: `original[5] = 6`, which we placed at `(1, 2)`. ✓

You'll use this direction when **flattening** a 2D array (storing it in 1D, often for cache locality or serialization).

---

## 6. Code

```cpp
vector<vector<int>> construct2DArray(vector<int>& original, int m, int n) {
    if ((int)original.size() != m * n) return {};

    vector<vector<int>> result(m, vector<int>(n));

    for (int k = 0; k < (int)original.size(); k++) {
        int row = k / n;
        int col = k % n;
        result[row][col] = original[k];
    }
    return result;
}
```

Six lines of logic. Read each:

1. **Size guard** — return `{}` if mismatch.
2. **Allocate** result as `m` rows, each of `n` zero-initialized ints.
3. **Loop** through `original` by flat index.
4. **Compute row and column** via integer division and modulo.
5. **Assign**.
6. **Return**.

**Alternative: iterator slicing (C++).**

```cpp
vector<vector<int>> construct2DArray(vector<int>& original, int m, int n) {
    if ((int)original.size() != m * n) return {};
    vector<vector<int>> result;
    for (int i = 0; i < m; i++) {
        result.emplace_back(original.begin() + i * n, original.begin() + (i + 1) * n);
    }
    return result;
}
```

Each row is built by copying a contiguous slice of `original`. Same complexity, slightly different style — no explicit per-element index math.

**Python:**

```python
def construct2DArray(original, m, n):
    if len(original) != m * n:
        return []
    return [original[i*n : (i+1)*n] for i in range(m)]
```

A list comprehension that slices `original` in row-sized chunks. Very compact.

---

## 7. Trace it

`original = [1, 2, 3, 4, 5, 6]`, `m = 2`, `n = 3`.

**Size guard:** `6 == 2 * 3` ✓. Continue.

**Allocate** `result = [[0, 0, 0], [0, 0, 0]]`.

```
k = 0:  row = 0 / 3 = 0.   col = 0 % 3 = 0.   result[0][0] = 1.   result = [[1,0,0], [0,0,0]]
k = 1:  row = 1 / 3 = 0.   col = 1 % 3 = 1.   result[0][1] = 2.   result = [[1,2,0], [0,0,0]]
k = 2:  row = 2 / 3 = 0.   col = 2 % 3 = 2.   result[0][2] = 3.   result = [[1,2,3], [0,0,0]]
k = 3:  row = 3 / 3 = 1.   col = 3 % 3 = 0.   result[1][0] = 4.   result = [[1,2,3], [4,0,0]]
k = 4:  row = 4 / 3 = 1.   col = 4 % 3 = 1.   result[1][1] = 5.   result = [[1,2,3], [4,5,0]]
k = 5:  row = 5 / 3 = 1.   col = 5 % 3 = 2.   result[1][2] = 6.   result = [[1,2,3], [4,5,6]]
```

Return `[[1, 2, 3], [4, 5, 6]]`. ✓

Watch the pattern: `k = 0, 1, 2` all map to row 0 (because integer division by 3 of a value < 3 is 0). At `k = 3`, the row flips to 1. Modulo 3 cycles the column through `0, 1, 2, 0, 1, 2`.

---

## 8. Common pitfalls

1. **Floating-point division instead of integer division.** In Python, `k / n` is **floating-point** division (gives `0.5` for `k=1, n=2`). Use `k // n` for integer. In JavaScript, `Math.floor(k / n)`. In C++/Java, `int / int` is already integer (truncates).

2. **Negative `k` in modulo.** Not a problem here (`k ≥ 0`), but in other problems `k` can be negative — and in C++, `-1 % 3` is `-1`, not `2`. Use `((k % n) + n) % n` for "positive modulo" if needed.

3. **Mixing up `m` and `n` (rows vs columns).** This problem reads "m rows, n columns" — so `result` has `m` outer entries, each with `n` inner entries. Easy to swap by accident. Double-check before submitting.

4. **Off-by-one on the size check.** Always `original.length == m * n` (equality, not `<=` or `>=`). Mismatched sizes should return `[]`, not a partially-filled matrix.

5. **Allocating before the size check.** If the check fails, you've wasted a `m × n` allocation. Always check FIRST, then allocate.

6. **Confusing this with "reshape" semantics in NumPy/MATLAB.** NumPy's `reshape` defaults to **row-major (C-order)**, which matches this problem. Some array libraries are column-major (FORTRAN-order) — in those, the mapping would be `col = k / m, row = k % m`. Same math, different convention.

---

## 9. The shape — index-mapping in memory, storage, and traversals

The `k = row * n + col` formula is **how computers store 2D arrays in memory**. Most programming languages lay out a 2D array as a flat 1D block, using exactly this formula to compute "where in the block is element `(row, col)`?"

| Where you see this mapping | What it does |
|---|---|
| **This problem** | reshape 1D → 2D |
| C/C++/Java `int arr[m][n]` storage | computes the byte offset of `arr[r][c]` as `(r * n + c) * sizeof(int)` |
| NumPy `array.reshape(m, n)` | uses the same arithmetic |
| Cache-friendly row-major iteration | iterating `for r: for c:` accesses memory linearly (fast) |
| Cache-unfriendly column-major iteration | iterating `for c: for r:` jumps by `n × sizeof(int)` each step (slow on row-major storage) |
| Serializing a matrix for file I/O | flatten via `row * n + col`, write 1D, reload by inverse |
| Hashing a 2D position into an integer (game grids) | combine `(row, col)` into a single key via `row * n + col` |
| Spatial hashing (chunked grids) | same idea at a coarser granularity |

**Pattern to internalize:**

> "1D ↔ 2D conversion is constant-time arithmetic. `flat = row * n + col`; `row = flat / n`; `col = flat % n`. Burn it into reflex."

Once you have this, problems that look "tricky because they involve a 2D grid" often simplify — you can flatten internally, do 1D operations (like sliding window or two-pointer), and unflatten at the end.

---

> **Self-check — the question to ask next time.**
>
> When you face a problem that involves **moving between 1D and 2D representations** (reshape, flatten, serialize, index into a "logical 2D" stored as 1D), before reaching for nested loops, ask:
>
> > **"Can I do the conversion with `k = row * n + col` (forward) or `row = k / n`, `col = k % n` (inverse), both in O(1)?"**
>
> If yes, you've reduced "shape transformation" to constant-time arithmetic and a single linear-time pass.

---

## Cross-references

- **Reference card (post-mastery):** [`../Convert_1D_Array_Into_2D_Array.md`](../Convert_1D_Array_Into_2D_Array.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Running_Sum_of_1D_Array.md`](./Running_Sum_of_1D_Array.md) (1D preprocessing — prefix sums)
  - [`Richest_Customer_Wealth.md`](./Richest_Customer_Wealth.md) (basic 2D iteration without reshape)
  - Coming later: Range_Sum_Query_2D_Immutable (uses the same row-major indexing internally)
