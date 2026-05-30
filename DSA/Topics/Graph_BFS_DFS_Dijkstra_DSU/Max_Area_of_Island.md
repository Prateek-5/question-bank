# Max Area of Island

**Problem Link:**
<a href="https://leetcode.com/problems/max-area-of-island/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/max-area-of-island/</a>

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Understand the Problem

Given an `m × n` grid of 0s and 1s, an **island** is a maximal group of 1s connected horizontally or vertically (not diagonally). Return the **area** (number of 1-cells) of the largest island.

Example:
```
0 0 1 0 0 0 0 1 0 0 0 0 0
0 0 0 0 0 0 0 1 1 1 0 0 0
0 1 1 0 1 0 0 0 0 0 0 0 0
0 1 0 0 1 1 0 0 1 0 1 0 0
0 1 0 0 1 1 0 0 1 1 1 0 0
0 0 0 0 0 0 0 0 0 0 1 0 0
0 0 0 0 0 0 0 1 1 1 0 0 0
0 0 0 0 0 0 0 1 1 0 0 0 0
```

Several islands. The largest has area 6. Identify it by flood-filling each island and taking the max.

----------------------------------------

## Step 2: Connection to Number of Islands

If you've seen **Number of Islands**, this is the same setup with a twist. In Number of Islands, we count how many islands exist. Here, we find the **largest** area.

The algorithm is the same — traverse each 1-cell via DFS/BFS, marking visited, summing area — but instead of incrementing an island counter, we track the size of each DFS/BFS run.

----------------------------------------

## Step 3: DFS With Area Accumulation

For each unvisited 1-cell, launch DFS. DFS visits every connected 1-cell, returning the count.

```
def dfs(r, c):
    if r, c out of bounds or grid[r][c] != 1: return 0
    grid[r][c] = 0   # mark visited by overwriting
    return 1 + dfs(r+1, c) + dfs(r-1, c) + dfs(r, c+1) + dfs(r, c-1)

max_area = 0
for each cell (r, c):
    if grid[r][c] == 1:
        max_area = max(max_area, dfs(r, c))
return max_area
```

Each 1-cell is visited exactly once across all DFS calls (after being visited, it's marked 0). O(m × n) total.

----------------------------------------

## Step 4: Trace a Small Example

```
1 1 0
0 1 1
1 0 1
```

Scan cells in row-major order.

(0, 0) = 1. DFS:
- Mark (0, 0) = 0. Visit neighbors.
- (1, 0) = 0. (0, 1) = 1. DFS into (0, 1).
  - Mark (0, 1) = 0. Visit (0, 2) = 0, (1, 1) = 1. DFS into (1, 1).
    - Mark (1, 1) = 0. Visit (2, 1) = 0, (1, 0) = 0, (1, 2) = 1. DFS into (1, 2).
      - Mark (1, 2) = 0. Visit (0, 2) = 0, (2, 2) = 1. DFS into (2, 2).
        - Mark (2, 2) = 0. Visit (2, 1) = 0, (1, 2) = 0, (2, 3) OOB.
        - Return 1.
      - Return 1 + 1 = 2.
    - Return 1 + 2 = 3.
  - Return 1 + 3 = 4.
- (−1, 0) OOB. Return 1 + 4 = 5.

Wait, DFS(0, 0) had children — what came back from which call? Let me not worry about exact totals and just note: DFS(0, 0) returns the size of the connected component starting there.

Total for the upper-left component: 5 cells (the 1s at (0,0), (0,1), (1,1), (1,2), (2,2)).

Next scan cells. (2, 0) = 1. DFS:
- Mark it. Visit (1, 0) = 0, (2, 1) = 0, (3, 0) OOB.
- Return 1.

Island of size 1.

max_area = max(5, 1) = 5.

----------------------------------------

## Step 5: Why Marking Matters

If we don't mark visited cells as 0, DFS would re-enter them endlessly and double-count area. Marking ensures each cell contributes exactly once.

Alternatively, use a separate `visited` matrix. That preserves the input but uses O(mn) extra space. For interview, either is fine.

----------------------------------------

## Step 6: Name It

**Flood fill with area tracking.** Same skeleton as Number of Islands, with area (node count per flood) replacing island count.

Generalizes to:
- Largest volume in a 3D binary grid.
- Weighted islands (each cell has a value; sum instead of count).
- Shortest distance within an island.
- Count islands with specific properties (e.g., only count islands of size > k).

----------------------------------------

## Step 7: Complexity

Time: **O(m · n)** — each cell visited at most once.
Space: **O(m · n)** for recursion stack in the worst case (one giant island).

----------------------------------------

## Step 8: C++ Implementation

```cpp
int maxAreaOfIsland(vector<vector<int>>& grid) {
    int m = grid.size();
    if (m == 0) return 0;
    int n = grid[0].size();

    function<int(int, int)> dfs = [&](int r, int c) -> int {
        if (r < 0 || c < 0 || r >= m || c >= n || grid[r][c] != 1) return 0;
        grid[r][c] = 0;   // mark visited
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

The recursive DFS is the simplest. For very large grids, use an iterative BFS/DFS with explicit stack to avoid recursion overflow.

----------------------------------------

## Step 9: Follow-up Questions

- **Count the number of islands (not area).** Increment count instead of summing area.
- **Count islands of a specific size.** Filter DFS results by size threshold.
- **Islands with diagonal connectivity.** Add 4 more neighbor offsets.
- **Maximum perimeter of an island.** Different aggregation — count edges adjacent to water or boundary.
- **Flood fill with recoloring (different color for each island).** Assign a unique marker to each flood.
- **Weighted grid (each cell has a value).** Sum values during DFS instead of counting.
