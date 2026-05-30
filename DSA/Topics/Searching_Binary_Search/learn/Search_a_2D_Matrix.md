# Search a 2D Matrix — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Search_a_2D_Matrix.md`](../Search_a_2D_Matrix.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/search-a-2d-matrix/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/search-a-2d-matrix/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. The lesson: **when a 2D matrix has the property that reading row-major gives a SORTED 1D sequence, treat the matrix AS a sorted 1D array** with a simple index-mapping formula. **Read [`Find_First_and_Last_Position_of_Element_in_Sorted_Array.md`](./Find_First_and_Last_Position_of_Element_in_Sorted_Array.md) first** for the binary search template.

**Map of this file (9 short sections):**

1. Read the problem
2. The matrix's structure
3. The two-step approach
4. The slicker approach — flat sorted array
5. The index mapping
6. Code
7. Trace it
8. Common pitfalls
9. The shape — when 2D is just 1D in disguise

---

## 1. Read the problem

Given an `m × n` integer matrix with these two properties:
1. **Each row is sorted ascending** (left to right).
2. **The first integer of each row is greater than the last integer of the previous row.**

Given a target value, return `true` if it's in the matrix, `false` otherwise.

**Required:** O(log(m·n)) time.

**Example:**

```
matrix = [ 1,  3,  5,  7]
        [10, 11, 16, 20]
        [23, 30, 34, 60]

target = 16  → true
target = 13  → false
```

---

## 2. The matrix's structure

> **Mini-refresher: the two properties combined imply a sorted READING.**
>
> Reading the matrix in **row-major order** (left-to-right, then top-to-bottom):
> ```
> 1, 3, 5, 7, 10, 11, 16, 20, 23, 30, 34, 60
> ```
> This sequence is FULLY SORTED ascending.
>
> Why? Property 1 ensures within-row sortedness. Property 2 ensures cross-row sortedness (the last element of row i is < the first element of row i+1).
>
> Combined: the matrix is just a sorted 1D array, drawn in a 2D grid.

This is a much stronger property than "Search a 2D Matrix II" (rows AND columns sorted but no cross-row guarantee), which requires a different algorithm. Read the problem carefully — these are different problems.

---

## 3. The two-step approach

A natural first idea:

1. **Find the right row.** Binary-search the first column for the row whose first element is ≤ target. Specifically, find the largest row index `r` such that `matrix[r][0] <= target`. (Equivalently: the row where `target` could live.)
2. **Within that row, binary-search for the target.**

Each step is O(log m) and O(log n). Total: **O(log m + log n) = O(log(m·n))**.

Works. But there's a SINGLE binary search that's even cleaner.

---

## 4. The slicker approach — flat sorted array

Since the matrix-as-1D-array is sorted, we can just binary-search it as a 1D sorted array of length `m × n`.

The only twist: we need to know how to access `nums[i]` when `nums` is conceptually a 1D view of a 2D matrix. The formula:

```
flat_index = k    →    2D index = (row = k / n, col = k % n)
```

Where `n` is the number of COLUMNS.

So `matrix[k / n][k % n]` retrieves the value at 1D-index `k`.

The binary search:

```
lo, hi = 0, m * n - 1
while lo <= hi:
    mid = (lo + hi) // 2
    val = matrix[mid // n][mid % n]
    if val == target: return true
    elif val < target: lo = mid + 1
    else: hi = mid - 1
return false
```

One binary search. **O(log(m·n))** time.

---

## 5. The index mapping

Why does `(k // n, k % n)` work?

Row-major layout: the first row holds indices 0 through n-1. The second row holds indices n through 2n-1. Etc.

So for any flat index `k`:
- `k // n` = which row (integer division).
- `k % n` = position within that row (the column).

For matrix `[m=3, n=4]`:
- `k = 0` → (0/4, 0%4) = (0, 0). matrix[0][0].
- `k = 3` → (0, 3). matrix[0][3].
- `k = 4` → (1, 0). matrix[1][0].
- `k = 5` → (1, 1). matrix[1][1].
- `k = 11` → (2, 3). matrix[2][3].

Range of valid k: 0 to m·n - 1 (inclusive).

> **Mini-refresher: row-major vs column-major.**
>
> **Row-major** (C/C++/Python): rows stored contiguously. `arr[i][j]` is at offset `i × n + j`.
>
> **Column-major** (Fortran, MATLAB): columns stored contiguously. `arr[i][j]` is at offset `j × m + i`.
>
> For this problem, the matrix is conceptually row-major (the spec says rows-first). Index formula: `(k // n, k % n)`.

---

## 6. Code

**C++:**

```cpp
bool searchMatrix(vector<vector<int>>& matrix, int target) {
    if (matrix.empty() || matrix[0].empty()) return false;
    int m = matrix.size(), n = matrix[0].size();
    int lo = 0, hi = m * n - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        int val = matrix[mid / n][mid % n];
        if (val == target) return true;
        if (val < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return false;
}
```

**Python:**

```python
def searchMatrix(matrix, target):
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    lo, hi = 0, m * n - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        val = matrix[mid // n][mid % n]
        if val == target:
            return True
        elif val < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return False
```

**JavaScript:**

```javascript
function searchMatrix(matrix, target) {
    if (matrix.length === 0 || matrix[0].length === 0) return false;
    const m = matrix.length, n = matrix[0].length;
    let lo = 0, hi = m * n - 1;
    while (lo <= hi) {
        const mid = Math.floor((lo + hi) / 2);
        const val = matrix[Math.floor(mid / n)][mid % n];
        if (val === target) return true;
        if (val < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return false;
}
```

Complexity: **O(log(m·n)) time, O(1) space.**

---

## 7. Trace it

**`matrix = [[1,3,5,7],[10,11,16,20],[23,30,34,60]]`, target = 11.**

```
m=3, n=4. m·n = 12. lo=0, hi=11.

Iter 1: mid = 5.
  val = matrix[5/4][5%4] = matrix[1][1] = 11.
  Match! Return true.
```

**target = 13** (not present).

```
m·n = 12. lo=0, hi=11.

Iter 1: mid=5. val = matrix[1][1] = 11. 11 < 13. lo = 6.
Iter 2: lo=6, hi=11. mid=8. val = matrix[2][0] = 23. 23 > 13. hi = 7.
Iter 3: lo=6, hi=7. mid=6. val = matrix[1][2] = 16. 16 > 13. hi = 5.

lo > hi. Return false.
```

---

## 8. Common pitfalls

1. **Confusing this with Search 2D Matrix II.** This problem has the strong cross-row property; II only has row/column sortedness (and needs staircase search). Different algorithms.

2. **Forgetting `m * n` could overflow.** For very large matrices, `int` might wrap. Use `long long` or `size_t`. (LeetCode constraints typically prevent this.)

3. **Wrong index mapping.** It's `(k / n, k % n)` for row-major. Using `(k / m, k % m)` (swapping m and n) gives wrong results.

4. **Forgetting the empty-matrix check.** If `matrix` is empty or has empty rows, `n` would be undefined. Guard at the top.

5. **Using `<` instead of `<=` in the loop condition (with `hi = mid - 1`).** Causes off-by-one. The template `lo <= hi` with `hi = mid - 1` is canonical for "exists" search.

6. **Doing two binary searches when one suffices.** Two searches work (and give the same complexity), but the single flat-search is cleaner.

7. **Trying to use `(k % n, k / n)`** — that's column-major. The matrix is row-major.

8. **Returning the position rather than a boolean.** Read the spec — this problem wants `true`/`false`.

---

## 9. The shape — when 2D is just 1D in disguise

The pattern:

> **"If a 2D structure has a sortedness property that lets you 'flatten' it into a 1D sorted sequence, binary-search the 1D and use index math to project back to 2D coordinates."**

Where this applies:

| Problem | 2D-to-1D mapping |
|---|---|
| **This problem** | row-major: (k/n, k%n) |
| Kth Smallest in a Sorted Matrix (LC #378) — NOT this strong, uses different approach |  |
| Find K-th Smallest Pair Distance | binary search on pair-distance value |
| Image rotation (90 degrees) | (i, j) ↔ (j, n-1-i) — different but same kind of mapping |
| Read storage of column-major arrays | (k%m, k/m) instead |

**Pattern to internalize:**

> "Don't be intimidated by 2D problems. Often the 2D structure is window dressing — the underlying SEQUENCE is 1D and admits 1D algorithms with a simple index conversion."

---

> **Self-check — the question to ask next time.**
>
> When you face a 2D structure that's sorted "in reading order," ask:
>
> > **"Can I treat this as a 1D sorted array using `(k / n, k % n)` to access elements? If yes, all my 1D binary-search tools apply directly."**
>
> If yes, you've reduced 2D to 1D in one line of code.

---

## Cross-references

- **Reference card (post-mastery):** [`../Search_a_2D_Matrix.md`](../Search_a_2D_Matrix.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Find_First_and_Last_Position_of_Element_in_Sorted_Array.md`](./Find_First_and_Last_Position_of_Element_in_Sorted_Array.md) — 1D template.
  - Coming next: Capacity_To_Ship_Packages, Magnetic_Force — binary search on the ANSWER.
  - Coming after: Smallest_Good_Base — number theory + binary search.
