# Number of Enclaves

**Problem Link:**
<a href="https://leetcode.com/problems/number-of-enclaves/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/number-of-enclaves/</a>

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Understand the Problem

A binary matrix of land (1) and water (0). A move is a step to an adjacent land cell (4-directional) or walking off the boundary. Count the land cells from which you **cannot** walk off the boundary. These are the "enclaves."

Example:
```
0 0 0 0
1 0 1 0
0 1 1 0
0 0 0 0
```

Can each land cell escape to the boundary?
- (1, 0) is on the boundary already. Not enclave.
- (1, 2) is surrounded. From (1, 2), can we walk to boundary via land? Neighbors: (1, 1)=0 water, (1, 3)=0 water, (0, 2)=0 water, (2, 2)=1 land. Connected to (2, 2). (2, 2) connects to (2, 1)=1. From (2, 1), neighbors include (2, 0)=0 water, (2, 2), (3, 1)=0, (1, 1)=0. Land cluster {(1,2), (2,1), (2,2)} doesn't reach the boundary.
- (1, 0) is boundary.

So 3 enclave cells: (1, 2), (2, 1), (2, 2). Return **3**.

----------------------------------------

## Step 2: Negative-Space Framing

Instead of "which land cells are enclaves," ask: **which land cells can reach the boundary**? Those are NOT enclaves. The rest are.

To find "can reach boundary": flood-fill from every border land cell, marking all connected land. Any unmarked land at the end is an enclave. Count them.

This mirrors Surrounded Regions — same structural insight. Flooding from the boundary is cleaner than computing "can't reach boundary" directly.

----------------------------------------

## Step 3: The Algorithm

```
# Step 1: flood-fill from every border land cell, marking cells as "escaped" (or set to 0)
for each border cell (r, c):
    if grid[r][c] == 1:
        flood_fill(r, c)  # marks all connected land as 0

# Step 2: count remaining 1s — these are enclaves
count = 0
for all (r, c):
    if grid[r][c] == 1: count++
return count
```

The flood-fill marks border-connected cells as water (0), so they're removed from the count. What remains is land that couldn't reach the boundary — enclaves.

----------------------------------------

## Step 4: Trace on the Example

```
0 0 0 0
1 0 1 0
0 1 1 0
0 0 0 0
```

Border cells: row 0 (all 0), row 3 (all 0), column 0 (rows 0-3 = 0, 1, 0, 0), column 3 (rows 0-3 = 0, 0, 0, 0).

Border land cells: (1, 0). Only one.

Flood from (1, 0):
- (1, 0) → 0. Mark visited.
- Neighbors: (0, 0)=0, (2, 0)=0, (1, 1)=0. No land to spread to.
- Done.

After step 1:
```
0 0 0 0
0 0 1 0
0 1 1 0
0 0 0 0
```

Count remaining 1s: (1, 2), (2, 1), (2, 2) → 3.

Return 3. ✓

----------------------------------------

## Step 5: Why This Is Correct

**Claim:** a land cell is an enclave iff it's not reachable from any border land cell via 4-connected land.

**Proof:** "reachable from border land cell" means we can walk there starting from somewhere on the border. By reversibility, we can also walk *from* that cell to the boundary via the same land path. So reachable-from-border land = non-enclave. Unreachable = enclave.

Our flood-fill marks exactly the reachable-from-border land as water. What remains unchanged are the enclaves.

----------------------------------------

## Step 6: Name It

**Boundary flood-fill** — seed the search from the boundary, mark the reachable region, and the complement is the answer.

Same technique as Surrounded Regions and Pacific Atlantic Water Flow. Useful whenever a problem describes "cells enclosed by X" — flooding from non-enclosed (boundary) gives a clean answer.

----------------------------------------

## Step 7: Complexity

Time: each cell visited at most twice (once during boundary flood, once during final count). **O(m · n)**.
Space: O(m · n) for the DFS stack in the worst case (whole grid is one flood).

----------------------------------------

## Step 8: C++ Implementation

```cpp
int numEnclaves(vector<vector<int>>& grid) {
    int m = grid.size();
    if (m == 0) return 0;
    int n = grid[0].size();

    function<void(int, int)> flood = [&](int r, int c) {
        if (r < 0 || c < 0 || r >= m || c >= n || grid[r][c] != 1) return;
        grid[r][c] = 0;
        flood(r+1, c); flood(r-1, c); flood(r, c+1); flood(r, c-1);
    };

    // Flood from border
    for (int r = 0; r < m; ++r) {
        flood(r, 0);
        flood(r, n - 1);
    }
    for (int c = 0; c < n; ++c) {
        flood(0, c);
        flood(m - 1, c);
    }

    // Count remaining 1s (enclaves)
    int count = 0;
    for (int r = 0; r < m; ++r) {
        for (int c = 0; c < n; ++c) {
            if (grid[r][c] == 1) count++;
        }
    }
    return count;
}
```

Destructive on input; wrap input if you need to preserve it.

----------------------------------------

## Step 9: Follow-up Questions

- **Count the number of enclave **islands** (connected components of enclaves), not cells.** After the boundary flood, do a second flood from each remaining 1 to count components.
- **Size of the largest enclave.** Similar — flood each remaining region and track the max size.
- **8-directional movement.** Extend the flood to 8 offsets.
- **Non-destructive (don't modify grid).** Use a separate visited matrix.
- **Distance from each enclave to the nearest boundary.** Multi-source BFS from the boundary.
- **Weighted walk costs.** Different problem — use Dijkstra instead of flood.
