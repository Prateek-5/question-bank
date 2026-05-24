# Max Area of Island — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Max_Area_of_Island.md`](../Max_Area_of_Island.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/max-area-of-island/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~10 minutes. **Variant of Number of Islands — flood-fill returns AREA, track the max.** **Read [`Number_of_Islands.md`](./Number_of_Islands.md) first.**

**Map of this file (6 short sections):**

1. Read the problem
2. The variation
3. Flood-fill returning size
4. Code
5. Trace it
6. The shape — flood-fill with aggregation

---

## 1. Read the problem

Same setup as Number of Islands: `m × n` grid of 1s (land) and 0s (water). Find the AREA (number of cells) of the LARGEST island.

**Example:**
```
0 0 1 0 0 0 0 1 0
0 0 0 0 0 0 0 1 1
0 1 1 0 1 0 0 0 0
0 1 0 0 1 1 0 0 0
0 1 0 0 1 1 0 0 0
```

Largest island has 6 cells. Return **6**.

---

## 2. The variation

> **Mini-refresher: difference from Number of Islands.**
>
> Same DFS flood-fill structure. But instead of just COUNTING islands, we MEASURE each one and track the MAX.
>
> `flood` returns the SIZE of the visited component. Outer scan updates `max_area`.

---

## 3. Flood-fill returning size

```
def flood(r, c):
    if r < 0 or r >= m or c < 0 or c >= n or grid[r][c] != 1: return 0
    grid[r][c] = 0
    return 1 + flood(r+1, c) + flood(r-1, c) + flood(r, c+1) + flood(r, c-1)
```

Each recursive call returns the size of its subtree. Sum + 1 (for self) = total reachable.

---

## 4. Code

**C++:**

```cpp
int maxAreaOfIsland(vector<vector<int>>& grid) {
    int m = grid.size();
    if (m == 0) return 0;
    int n = grid[0].size();

    function<int(int, int)> dfs = [&](int r, int c) -> int {
        if (r < 0 || c < 0 || r >= m || c >= n || grid[r][c] != 1) return 0;
        grid[r][c] = 0;
        return 1 + dfs(r+1, c) + dfs(r-1, c) + dfs(r, c+1) + dfs(r, c-1);
    };

    int best = 0;
    for (int r = 0; r < m; ++r) {
        for (int c = 0; c < n; ++c) {
            if (grid[r][c] == 1) {
                best = max(best, dfs(r, c));
            }
        }
    }
    return best;
}
```

**Python:**

```python
def maxAreaOfIsland(grid):
    if not grid: return 0
    m, n = len(grid), len(grid[0])
    
    def dfs(r, c):
        if r < 0 or c < 0 or r >= m or c >= n or grid[r][c] != 1: return 0
        grid[r][c] = 0
        return 1 + dfs(r+1, c) + dfs(r-1, c) + dfs(r, c+1) + dfs(r, c-1)
    
    best = 0
    for r in range(m):
        for c in range(n):
            if grid[r][c] == 1:
                best = max(best, dfs(r, c))
    return best
```

Complexity: **O(m × n) time, O(m × n) space** (recursion worst case).

---

## 5. Trace it

```
1 1 0
0 1 1
1 0 1
```

Outer scan:

- (0, 0) = 1 → DFS:
  - Mark (0, 0) = 0. Return 1 + dfs(neighbors).
  - dfs(1, 0): water, return 0.
  - dfs(0, 1): mark, recurse:
    - dfs(1, 1): mark, recurse:
      - dfs(2, 1): water, 0.
      - dfs(1, 2): mark, recurse:
        - dfs(2, 2): mark, recurse:
          - All neighbors water/visited.
          - Returns 1.
        - Returns 1 + 1 = 2.
      - Returns 1 + 2 = 3 (from dfs(1,1)).
    - Returns 1 + 3 = 4 (from dfs(0,1)).
  - Returns 1 + 4 = 5 (from dfs(0,0)).
  
  best = max(0, 5) = 5.

- (2, 0) = 1 → DFS: 1 cell. best = 5.

Final: **5**. ✓

---

## 6. The shape — flood-fill with aggregation

The pattern:

> **"Same flood-fill template as Number of Islands. But FLOOD-FILL RETURNS A VALUE (size, sum, etc.) that you can AGGREGATE."**

| Aggregation | Problem |
|---|---|
| Count of components | Number of Islands |
| **Size of largest component** | **This problem** |
| Sum of all cells in component | weighted variant |
| Perimeter of component | Island Perimeter |
| Bounded count | Number of Closed Islands |

**Pattern to internalize:**

> "Flood-fill is a TEMPLATE. Each problem just changes what each cell CONTRIBUTES (count 1, count value, count edges) and what to AGGREGATE (max, sum, count)."

---

## Cross-references

- **Reference card (post-mastery):** [`../Max_Area_of_Island.md`](../Max_Area_of_Island.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Number_of_Islands.md`](./Number_of_Islands.md).
  - Coming next: [`Number_of_Provinces.md`](./Number_of_Provinces.md), [`Rotting_Oranges.md`](./Rotting_Oranges.md).
