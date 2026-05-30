# Search a 2D Matrix

**Problem Link:**
<a href="https://leetcode.com/problems/search-a-2d-matrix/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/search-a-2d-matrix/</a>

**Topic:**
Searching / Binary Search

----------------------------------------

## Step 1: Understand the Matrix's Structure

You have an `m × n` matrix with two sorting properties:
- Each row is sorted ascending (left to right).
- The first value of each row is **greater** than the last value of the previous row.

So reading the matrix row-by-row (left-to-right, top-to-bottom) gives one big sorted sequence.

Example:
```
 1  3  5  7
10 11 16 20
23 30 34 60
```

Read it in row-major order: 1, 3, 5, 7, 10, 11, 16, 20, 23, 30, 34, 60. Fully sorted.

Given a target, return true if the target is in the matrix, false otherwise.

With target = 16: it's in the matrix. Return true.
With target = 13: not in the matrix. Return false.

----------------------------------------

## Step 2: First Thought — Two Binary Searches

Since the rows are sorted and rows are arranged in increasing order:
1. Find the row where the target **could** live: the row whose first element ≤ target and (next row's first element > target or no next row).
2. Within that row, binary-search for the target.

Each step is O(log m) or O(log n). Total: O(log m + log n).

This works. But there's a slicker approach that arises naturally from the problem's structure.

----------------------------------------

## Step 3: Treat the Matrix as One Sorted Array

The observation "read row-by-row gives a sorted sequence" means the matrix is effectively a sorted array of length `m · n`, just laid out in a 2D shape. We can binary-search it directly.

For a 1D index `k` in `[0, m·n)`, the corresponding 2D index is `(k / n, k % n)` — row k/n, column k%n. That's the bridge between the two representations.

```
lo = 0, hi = m * n - 1
while lo <= hi:
    mid = (lo + hi) / 2
    val = matrix[mid / n][mid % n]
    if val == target: return true
    if val < target: lo = mid + 1
    else: hi = mid - 1
return false
```

O(log(m·n)) = **O(log m + log n)**. Same complexity as the two-step approach, but half the code. Elegant.

----------------------------------------

## Step 4: Trace on the Example

`target = 11`. m = 3, n = 4. lo = 0, hi = 11.

```
lo=0, hi=11. mid=5.
  val = matrix[5/4][5%4] = matrix[1][1] = 11.
  Match. Return true.
```

`target = 13`.
```
lo=0, hi=11. mid=5.
  val = matrix[1][1] = 11. 11 < 13. lo = 6.
lo=6, hi=11. mid=8.
  val = matrix[8/4][8%4] = matrix[2][0] = 23. 23 > 13. hi = 7.
lo=6, hi=7. mid=6.
  val = matrix[1][2] = 16. 16 > 13. hi = 5.
lo=6, hi=5. Loop exits.
Return false.
```

Correct.

----------------------------------------

## Step 5: Why the Index Mapping Works

Row-major layout means consecutive array positions map to consecutive matrix cells reading left-to-right within a row, then to the next row. So:
- Array index 0 → matrix[0][0].
- Array index n-1 → matrix[0][n-1] (end of row 0).
- Array index n → matrix[1][0] (start of row 1).
- Generally: index k → matrix[k / n][k % n].

This is literally the formula for how multi-dimensional arrays are stored in memory in C and C++. Leveraging it makes the 2D problem disappear into a 1D one.

----------------------------------------

## Step 6: Why the Problem Admits This Simplification

Not every sorted 2D matrix is "a sorted array in disguise." If rows are individually sorted but rows are not globally ordered (e.g., "Search a 2D Matrix II" — each row *and* each column sorted, but not globally), the trick doesn't apply. We'd need a different approach (staircase search from top-right).

This problem's stronger guarantee — "first element of each row > last element of previous row" — is what lets us treat the matrix as a single sorted sequence.

----------------------------------------

## Step 7: Name It

This is **1D binary search on a 2D-laid-out array**. The trick generalizes to any problem where the data is stored in a rectangular arrangement but forms a single sorted sequence under row-major (or column-major) reading.

Same idea extends to higher dimensions: a 3D box whose cells form a sorted sequence along some canonical reading order can be binary-searched with a 3D-to-1D mapping.

----------------------------------------

## Step 8: Complexity

Time: **O(log(m·n))** = O(log m + log n).
Space: **O(1)**.

----------------------------------------

## Step 9: C++ Implementation

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

A subtle note: I use `lo + (hi - lo) / 2` to avoid potential overflow. For very large `m·n`, `(lo + hi) / 2` could wrap around. Good habit regardless.

----------------------------------------

## Step 10: Follow-up Questions

- **Search a 2D Matrix II (rows and columns both sorted, but not globally).** Different problem — use staircase search from top-right or bottom-left, eliminating one row or column per step.
- **Return the position (row, col) of the target instead of a boolean.** On match, return `{mid / n, mid % n}`.
- **Matrix with possible duplicates.** Same algorithm works; returns any one occurrence.
- **Count occurrences of the target.** Find lower and upper bounds with two binary searches.
- **Search a rotated sorted matrix.** Harder — mash "search rotated array" with this 2D idea; requires case analysis.
- **Insert target into sorted matrix and maintain order.** If matrix is a dynamic structure, this is hard; for static matrices, no real interpretation.
