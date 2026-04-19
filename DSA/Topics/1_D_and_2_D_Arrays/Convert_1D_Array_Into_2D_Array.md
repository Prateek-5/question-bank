# Convert 1D Array Into 2D Array

**Problem Link:**
https://leetcode.com/problems/convert-1d-array-into-2d-array/

**Topic:**
1-D & 2-D Arrays

----------------------------------------

## Step 1: What's Asked

Given a 1D array `original`, two integers `m` and `n`, construct a 2D array with m rows and n columns. Fill row by row (row 0 first).

If `original.length != m * n`, return an empty 2D array.

Example: `original = [1, 2, 3, 4]`, m = 2, n = 2. Expected output: `[[1, 2], [3, 4]]`.

Example: `original = [1, 2, 3]`, m = 1, n = 3. Output: `[[1, 2, 3]]`.

Example: `original = [1, 2]`, m = 1, n = 1. 1 * 1 = 1 ≠ 2. Output: `[]`.

----------------------------------------

## Step 2: Check Size, Then Iterate

Two steps:
1. Verify `original.size() == m * n`. If not, return empty.
2. Fill an m × n 2D array row by row.

Index mapping: element `k` of `original` goes to position `(k / n, k % n)` in the 2D array. Row = k / n; column = k % n.

```
if len(original) != m * n: return []
result = new m × n 2D array
for k in 0..len(original)-1:
    result[k / n][k % n] = original[k]
return result
```

O(m · n) time, O(m · n) space.

----------------------------------------

## Step 3: Trace

`original = [1, 2, 3, 4, 5, 6]`, m = 2, n = 3.

Size check: 6 == 6. OK.

```
k=0: result[0/3][0%3] = result[0][0] = 1.
k=1: result[0][1] = 2.
k=2: result[0][2] = 3.
k=3: result[3/3][3%3] = result[1][0] = 4.
k=4: result[1][1] = 5.
k=5: result[1][2] = 6.
```

Result: [[1, 2, 3], [4, 5, 6]]. ✓

----------------------------------------

## Step 4: Index Mapping — Why It Works

In row-major storage, the element at position (r, c) in an m × n grid has flat index `r * n + c`. Inverse: from flat index k, row is `k / n`, column is `k % n`.

This is identical to how languages like C lay out multidimensional arrays in memory.

Knowing this mapping makes converting between 1D and 2D trivial.

----------------------------------------

## Step 5: Cleaner C++: Use Iterator Chunks

Alternative: use substring-like slicing.

```
if (original.size() != m * n) return {};
vector<vector<int>> result;
for (int i = 0; i < m; ++i) {
    result.emplace_back(original.begin() + i * n, original.begin() + (i + 1) * n);
}
return result;
```

Each row is a chunk of n consecutive elements from `original`. Vector-of-vectors construction via iterator pairs.

----------------------------------------

## Step 6: Name It

**1D-to-2D index mapping.** A fundamental transformation. Used in:
- Matrix representations in memory.
- Serializing grids for storage/transport.
- Flattening a 2D array for sorting or search.
- Cache-friendly iteration patterns.

The reverse direction (flattening 2D to 1D) uses the same math.

----------------------------------------

## Step 7: Complexity

Time: **O(m · n)**.
Space: **O(m · n)** for output.

----------------------------------------

## Step 8: C++ Implementation

```cpp
vector<vector<int>> construct2DArray(vector<int>& original, int m, int n) {
    if ((int)original.size() != m * n) return {};
    vector<vector<int>> result(m, vector<int>(n));
    for (int k = 0; k < (int)original.size(); ++k) {
        result[k / n][k % n] = original[k];
    }
    return result;
}
```

Six lines.

----------------------------------------

## Step 9: Follow-up Questions

- **Column-major filling (column 0 first, then column 1, ...).** Mapping becomes `k / m, k % m`. Or fill with nested loops.
- **2D to 1D conversion.** Reverse: for each cell, flat[i * n + j] = mat[i][j].
- **Partial arrays (allow `original.size() < m * n`, fill remainder with 0).** Adjust check; zero-initialize remainder.
- **Reshape into different (m, n) without allocating.** Wrap in a view / span with stride arithmetic.
- **Reshape with different orderings (spiral, zigzag).** Different traversal pattern; fill accordingly.
- **What if m and n are negative or zero?** Validate inputs.
