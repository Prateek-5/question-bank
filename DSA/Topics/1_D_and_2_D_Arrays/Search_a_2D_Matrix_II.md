# Search a 2D Matrix II

**Problem Link:**
https://leetcode.com/problems/search-a-2d-matrix-ii/

**Topic:**
1-D & 2-D Arrays

----------------------------------------

## Step 1: Understand the Matrix Structure

An `m × n` matrix where:
- Each **row** is sorted left-to-right (ascending).
- Each **column** is sorted top-to-bottom (ascending).

Note: unlike "Search a 2D Matrix" (I), the matrix **isn't** a single sorted sequence in row-major. Rows and columns are individually sorted; the flattened matrix isn't sorted.

Search for target. Return true if found, false otherwise.

Example:
```
 1  4  7 11 15
 2  5  8 12 19
 3  6  9 16 22
10 13 14 17 24
18 21 23 26 30
```

Search 5: present. Return true.
Search 20: not present. Return false.

----------------------------------------

## Step 2: Why Binary Search on the Flattened Array Doesn't Work

In "Search a 2D Matrix I," the entire matrix was globally sorted in row-major order. Binary search over the flat array worked.

Here, rows and columns are each sorted, but row k+1's first element may be less than row k's last element. E.g., in the example, row 1's last is 19, but row 2's first is 3 (less than 19).

Global ordering is broken. We need a different approach.

----------------------------------------

## Step 3: The Staircase Trick

Consider starting at the **top-right corner** `(0, n-1)`. Compare matrix[r][c] with target:

- If equal: found, return true.
- If matrix[r][c] > target: target must be in a column with smaller values. All of column c below row r is even larger (column sorted). So eliminate column c — move **left**.
- If matrix[r][c] < target: target must be in a row with larger values. All of row r to the left is even smaller (row sorted). So eliminate row r — move **down**.

Each comparison eliminates a full row or column. We make at most m + n steps total.

Result: O(m + n) time. Beautiful.

----------------------------------------

## Step 4: Why Start at Top-Right (or Bottom-Left)?

The top-right and bottom-left corners have the property that they're **larger than everything on one side and smaller than everything on another**.

Top-right (0, n-1):
- Above: nothing.
- Below: all values are larger (column sorted).
- Left: all values are smaller (row sorted).
- Right: nothing.

So at any step, we can **unambiguously decide** to move left (if too big) or down (if too small).

Corners like top-left don't have this property — top-left is smaller than both right-neighbor and down-neighbor, so we can't tell which direction to eliminate.

----------------------------------------

## Step 5: Trace for Target = 5

Starting at (0, 4) = 15.

- 15 > 5. Move left. Now at (0, 3) = 11.
- 11 > 5. Move left. Now at (0, 2) = 7.
- 7 > 5. Move left. Now at (0, 1) = 4.
- 4 < 5. Move down. Now at (1, 1) = 5.
- 5 == 5. Return true. ✓

Trace for Target = 20:

- (0, 4) = 15 < 20. Move down. (1, 4) = 19.
- 19 < 20. Down. (2, 4) = 22.
- 22 > 20. Left. (2, 3) = 16.
- 16 < 20. Down. (3, 3) = 17.
- 17 < 20. Down. (4, 3) = 26.
- 26 > 20. Left. (4, 2) = 23.
- 23 > 20. Left. (4, 1) = 21.
- 21 > 20. Left. (4, 0) = 18.
- 18 < 20. Down. Row = 5, out of bounds.
- Return false. ✓

Total steps: 9 for this 5×5 matrix. O(m + n) = O(10) matches.

----------------------------------------

## Step 6: Why O(m + n)

At each step, we decrement column or increment row. Column: n steps max (from n-1 to -1). Row: m steps max (from 0 to m). Total: m + n.

For m = n = 100, that's 200 ops — blazing fast.

Binary search per row would be O(m log n). Staircase is better.

----------------------------------------

## Step 7: Name It

**Staircase search** on a matrix with sorted rows and columns. Elegant and unique — rarely applicable elsewhere but memorable.

The key insight: **a corner has a direction from which elimination is always safe**.

Related:
- Search a 2D Matrix (I) — global sort, binary search.
- Kth smallest in sorted matrix — heap or binary search on value.
- Saddleback search (another name for this technique).

----------------------------------------

## Step 8: Complexity

Time: **O(m + n)**.
Space: **O(1)**.

Much better than O(m · n) brute force or O(m · log n) per-row binary search.

----------------------------------------

## Step 9: C++ Implementation

```cpp
bool searchMatrix(vector<vector<int>>& matrix, int target) {
    if (matrix.empty() || matrix[0].empty()) return false;
    int m = matrix.size(), n = matrix[0].size();
    int r = 0, c = n - 1;   // start at top-right
    while (r < m && c >= 0) {
        if (matrix[r][c] == target) return true;
        if (matrix[r][c] > target) c--;   // eliminate column
        else r++;                          // eliminate row
    }
    return false;
}
```

Five lines. Elegant staircase navigation.

Alternative: start at **bottom-left** (m-1, 0). Same logic, mirrored:
- If element > target, move up.
- If element < target, move right.

Either starting corner works.

----------------------------------------

## Step 10: Follow-up Questions

- **Return the position of target (not just true/false).** Record (r, c) on match.
- **Count occurrences of target.** Can't directly use staircase; target might appear multiple times. Use staircase to find one, then explore neighbors.
- **Find the k-th smallest element.** Different problem — use a min-heap or binary search on value.
- **Matrix of float values.** Same algorithm.
- **Matrix where rows AND columns are sorted, but allowed decreasing.** Different algorithm needed.
- **3D analog.** Start at a "corner" in 3D space; eliminate plane by plane.
