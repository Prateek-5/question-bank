# Number of Islands — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Number_of_Islands.md`](../Number_of_Islands.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/number-of-islands/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **THE introduction to grid DFS / connected components.** The lesson: **walk grid cells; for each unvisited LAND cell, FLOOD-FILL it (mark all connected land as visited). Each flood = one island.** Master this template — it's reused in dozens of grid-graph problems. **Read [`Subsets.md`](../../Recursion/learn/Subsets.md) for recursion basics first.**

**Map of this file (9 short sections):**

1. Read the problem
2. The "count and cross-out" intuition
3. Flood-fill via DFS
4. The outer scan
5. Code
6. Trace it
7. BFS alternative
8. Common pitfalls
9. The shape — grid as a graph

---

## 1. Read the problem

Given an `m × n` grid where `'1'` = LAND and `'0'` = WATER. An **ISLAND** is a maximal group of `'1'`s connected HORIZONTALLY OR VERTICALLY (NOT diagonally). Count the number of distinct islands.

**Example:**
```
1 1 0
0 1 0
0 0 1
```

Islands: `{(0,0), (0,1), (1,1)}` (one island), `{(2,2)}` (another). Total: **2**.

---

## 2. The "count and cross-out" intuition

> **Mini-refresher: how a HUMAN would count islands on paper.**
>
> 1. Find any `1` cell you haven't crossed out.
> 2. CROSS OUT every `1` connected to it (horizontally/vertically). That's one island.
> 3. Count += 1.
> 4. Repeat until no `1`s remain.
>
> The algorithm is exactly this — scan, flood-fill, count.

The flood-fill "marks visited" so we don't count the same island twice.

---

## 3. Flood-fill via DFS

From a starting cell, RECURSIVELY visit all 4 neighbors that are LAND. Mark visited as you go.

```
def flood(r, c):
    if r < 0 or r >= m or c < 0 or c >= n: return     # out of bounds
    if grid[r][c] != '1': return                        # water or visited
    grid[r][c] = '0'                                    # mark visited
    flood(r+1, c)
    flood(r-1, c)
    flood(r, c+1)
    flood(r, c-1)
```

> **Mini-refresher: marking visited via mutation.**
>
> We MUTATE the grid (turning visited `'1'` into `'0'`) to avoid a separate visited array. Saves memory.
>
> Alternative: use a parallel `visited[m][n]` boolean array if you can't mutate the input.

---

## 4. The outer scan

Scan all cells. For each unvisited `'1'`: increment count, flood-fill.

```
count = 0
for r in 0..m-1:
    for c in 0..n-1:
        if grid[r][c] == '1':
            count += 1
            flood(r, c)
return count
```

After flood at (r, c), the entire island is sunk to `'0'`. Subsequent scans skip it.

---

## 5. Code

**C++:**

```cpp
class Solution {
    int m, n;
    void flood(vector<vector<char>>& g, int r, int c) {
        if (r < 0 || c < 0 || r >= m || c >= n || g[r][c] != '1') return;
        g[r][c] = '0';
        flood(g, r + 1, c);
        flood(g, r - 1, c);
        flood(g, r, c + 1);
        flood(g, r, c - 1);
    }
public:
    int numIslands(vector<vector<char>>& g) {
        m = g.size(); n = g[0].size();
        int count = 0;
        for (int r = 0; r < m; ++r) {
            for (int c = 0; c < n; ++c) {
                if (g[r][c] == '1') { count++; flood(g, r, c); }
            }
        }
        return count;
    }
};
```

**Python:**

```python
def numIslands(grid):
    if not grid: return 0
    m, n = len(grid), len(grid[0])
    
    def flood(r, c):
        if r < 0 or r >= m or c < 0 or c >= n: return
        if grid[r][c] != '1': return
        grid[r][c] = '0'
        flood(r+1, c); flood(r-1, c); flood(r, c+1); flood(r, c-1)
    
    count = 0
    for r in range(m):
        for c in range(n):
            if grid[r][c] == '1':
                count += 1
                flood(r, c)
    return count
```

Complexity: **O(m × n) time** (each cell visited once), **O(m × n) space** (recursion).

---

## 6. Trace it

**Grid:**
```
1 1 0
0 1 0
0 0 1
```

Outer scan:

- (0, 0) = '1' → count = 1. Flood from (0, 0):
  - Mark (0, 0) = '0'. Recurse 4 neighbors.
  - (1, 0) = '0' (water, return). (-1, 0) OOB.
  - (0, 1) = '1' → mark, recurse:
    - (1, 1) = '1' → mark, recurse:
      - All neighbors null/water/visited.
  - All recursion bottoms out.
  
  Grid now:
  ```
  0 0 0
  0 0 0
  0 0 1
  ```

- (0, 1)..(2, 1): all '0'. Skip.
- (2, 2) = '1' → count = 2. Flood from (2, 2):
  - Mark (2, 2). Neighbors all water/OOB.

Final count = **2**. ✓

---

## 7. BFS alternative

For very large islands, DFS recursion may overflow. Use BFS with explicit queue:

```python
from collections import deque

def flood_bfs(grid, r, c):
    m, n = len(grid), len(grid[0])
    q = deque([(r, c)])
    grid[r][c] = '0'
    while q:
        rr, cc = q.popleft()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = rr + dr, cc + dc
            if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] == '1':
                grid[nr][nc] = '0'
                q.append((nr, nc))
```

Same O(mn) time; safer for huge grids.

---

## 8. Common pitfalls

1. **Forgetting to mark visited.** Infinite recursion or counting the same island many times.

2. **Marking visited AT POP (in BFS).** Same cell can be enqueued multiple times. Mark at ENQUEUE.

3. **Diagonal neighbors.** This problem says 4-DIRECTIONAL only. Diagonal would give different counts.

4. **Out-of-bounds check missing.** Crashes on grid edges.

5. **Treating `'1'` and `1` as same.** Input is CHARACTERS, not integers. Use `'1'` not `1`.

6. **Recursion depth for huge grids.** A 10⁶-cell all-land grid → 10⁶ deep recursion → stack overflow. Use BFS or iterative DFS.

---

## 9. The shape — grid as a graph

The pattern this problem teaches:

> **"A GRID IS A GRAPH. Each cell is a node; horizontal/vertical neighbors are edges. Connected components count = islands."**

| Problem | Variation |
|---|---|
| **This problem** | count components |
| Max Area of Island | size of largest component |
| Number of Closed Islands | components not touching border |
| Surrounded Regions | flip non-border components |
| Pacific Atlantic Water Flow | reachability from boundaries |
| Walls and Gates | multi-source BFS distance |
| Rotting Oranges | multi-source BFS time |

**Pattern to internalize:**

> "Grid problems are GRAPH problems with implicit edges between neighbors. DFS for connectivity, BFS for shortest distance. Mark visited."

---

## Cross-references

- **Reference card (post-mastery):** [`../Number_of_Islands.md`](../Number_of_Islands.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Max_Area_of_Island.md`](./Max_Area_of_Island.md), [`Number_of_Provinces.md`](./Number_of_Provinces.md).
