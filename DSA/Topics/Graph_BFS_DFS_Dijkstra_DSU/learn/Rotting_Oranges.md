# Rotting Oranges — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Rotting_Oranges.md`](../Rotting_Oranges.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/rotting-oranges/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/rotting-oranges/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The introduction to MULTI-SOURCE BFS.** The lesson: **seed the BFS queue with ALL sources at distance 0. BFS naturally expands from all sources simultaneously, giving each cell its MIN distance from ANY source.** This pattern reappears constantly in grid problems. **Read [`Number_of_Islands.md`](./Number_of_Islands.md) and [`Binary_Tree_Level_Order_Traversal.md`](../../Trees_Binary_Trees/learn/Binary_Tree_Level_Order_Traversal.md) first.**

**Map of this file (9 short sections):**

1. Read the problem
2. The single-source warm-up
3. Why multi-source BFS works
4. The level-counting trick
5. Code
6. Trace it
7. The "unreachable → return -1" check
8. Common pitfalls
9. The shape — multi-source BFS

---

## 1. Read the problem

`m × n` grid where each cell is:
- `0` = empty.
- `1` = fresh orange.
- `2` = rotten orange.

Every MINUTE, fresh oranges 4-DIRECTIONALLY adjacent to rotten ones become rotten.

Return the MINIMUM number of minutes until NO FRESH oranges remain. Return `-1` if impossible (some fresh orange is unreachable).

**Example:**
```
2 1 1
1 1 0
0 1 1
```

- Minute 0: rotten at (0,0).
- Minute 1: rot spreads to (0,1), (1,0).
- Minute 2: rot to (0,2), (1,1).
- Minute 3: rot to (2,1).
- Minute 4: rot to (2,2).

All rotten. Return **4**.

---

## 2. The single-source warm-up

If there were ONE rotten orange, standard BFS from that source assigns each reachable fresh orange a distance = time of rotting. Answer = MAX distance.

```
BFS from (r, c):
    q = [(r, c)]
    dist[r][c] = 0
    while q:
        (rr, cc) = q.popleft()
        for each 4-neighbor (nr, nc):
            if in bounds and dist[nr][nc] not set:
                dist[nr][nc] = dist[rr][cc] + 1
                q.append((nr, nc))
```

But what about MANY initial rotten oranges? Running BFS from each takes O((mn)²).

---

## 3. Why multi-source BFS works

> **Mini-refresher: SEED THE QUEUE with ALL sources.**
>
> Standard BFS: queue starts with ONE source. Each level expands outward.
>
> MULTI-source BFS: queue starts with ALL sources (each at distance 0). The BFS naturally expands from ALL of them SIMULTANEOUSLY.
>
> **The first time a cell is reached, its distance is the MIN distance from ANY source** — because BFS processes by INCREASING distance, and all sources start at distance 0.

So: enqueue ALL rotten oranges initially. BFS gives each fresh orange its time-to-rot = min distance from any rotten source.

Answer = max time across all fresh oranges (when the LAST one rots).

---

## 4. The level-counting trick

Track the MAX TIME seen during BFS. After BFS:
- If `fresh_count == 0`: all fresh oranges rotted. Return max_time.
- Else: some unreachable. Return -1.

```
fresh = count of fresh oranges
queue = list of rotten orange positions, each with time=0
max_time = 0

while queue:
    (r, c, t) = queue.popleft()
    max_time = max(max_time, t)
    for each fresh neighbor:
        mark rotten
        fresh -= 1
        queue.append((nr, nc, t+1))

return max_time if fresh == 0 else -1
```

O(mn) time and space.

---

## 5. Code

**C++:**

```cpp
int orangesRotting(vector<vector<int>>& g) {
    int m = g.size(), n = g[0].size();
    queue<tuple<int, int, int>> q;          // (r, c, time)
    int fresh = 0;

    for (int r = 0; r < m; ++r)
        for (int c = 0; c < n; ++c) {
            if (g[r][c] == 2) q.push({r, c, 0});
            else if (g[r][c] == 1) fresh++;
        }

    int maxTime = 0;
    int dr[] = {-1, 1, 0, 0}, dc[] = {0, 0, -1, 1};

    while (!q.empty()) {
        auto [r, c, t] = q.front(); q.pop();
        maxTime = max(maxTime, t);
        for (int k = 0; k < 4; ++k) {
            int nr = r + dr[k], nc = c + dc[k];
            if (nr < 0 || nc < 0 || nr >= m || nc >= n) continue;
            if (g[nr][nc] != 1) continue;
            g[nr][nc] = 2;
            fresh--;
            q.push({nr, nc, t + 1});
        }
    }

    return fresh == 0 ? maxTime : -1;
}
```

**Python:**

```python
from collections import deque

def orangesRotting(grid):
    m, n = len(grid), len(grid[0])
    q = deque()
    fresh = 0
    for r in range(m):
        for c in range(n):
            if grid[r][c] == 2: q.append((r, c, 0))
            elif grid[r][c] == 1: fresh += 1
    
    max_time = 0
    while q:
        r, c, t = q.popleft()
        max_time = max(max_time, t)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] == 1:
                grid[nr][nc] = 2
                fresh -= 1
                q.append((nr, nc, t + 1))
    
    return max_time if fresh == 0 else -1
```

Complexity: **O(m × n) time and space.**

---

## 6. Trace it

```
Grid:
2 1 1
1 1 0
0 1 1

Initial: q = [(0,0,0)]. fresh = 6.

Pop (0,0,0). max_time = 0.
  (1,0)=1 → rot. fresh=5. Push (1,0,1).
  (0,1)=1 → rot. fresh=4. Push (0,1,1).

Pop (1,0,1). max_time = 1.
  (2,0)=0 skip. (1,1)=1 → rot. fresh=3. Push (1,1,2).

Pop (0,1,1). max_time = 1.
  (0,2)=1 → rot. fresh=2. Push (0,2,2). (1,1) already rotten.

Pop (1,1,2). max_time = 2.
  (2,1)=1 → rot. fresh=1. Push (2,1,3).

Pop (0,2,2). max_time = 2.
  No fresh neighbors.

Pop (2,1,3). max_time = 3.
  (2,2)=1 → rot. fresh=0. Push (2,2,4).

Pop (2,2,4). max_time = 4. No fresh.

fresh = 0. Return 4.  ✓
```

---

## 7. The "unreachable → return -1" check

If some fresh orange is SURROUNDED by empty cells (no rotten orange can reach it), BFS won't visit it.

Track `fresh` count. If `fresh > 0` at the end, some are unreachable → return -1.

```
Example:
1 0 0
0 0 0
0 0 1

Two fresh oranges, no rotten. fresh = 2.
BFS doesn't even start (queue is empty initially).
Return -1.
```

(Actually for this example with NO rotten, we'd also need to handle "no rotten at all but fresh exists" — same -1 case. The general check handles all cases.)

---

## 8. Common pitfalls

1. **Forgetting to enqueue ALL initial rotten oranges.** Without multi-source, distant fresh oranges get wrong times.

2. **Marking rotten BEFORE checking.** Mark immediately when you ENQUEUE a fresh neighbor. Otherwise the same cell gets enqueued multiple times.

3. **Forgetting the `fresh == 0` check.** Some unreachable fresh oranges? Return -1.

4. **Returning `max_time + 1` or off-by-one errors.** Time is updated per BFS layer. Last layer = max_time correctly.

5. **Not handling the all-zero or all-rotten case.** If no fresh oranges initially, return 0.

6. **Trying DFS.** DFS doesn't give shortest-distance-from-sources. Use BFS.

---

## 9. The shape — multi-source BFS

The pattern:

> **"For 'distance to NEAREST source' problems with MULTIPLE sources, enqueue ALL sources at distance 0. BFS naturally expands simultaneously from all of them."**

| Problem | Sources |
|---|---|
| **This problem** | initially rotten oranges |
| 01 Matrix | all `0` cells |
| Walls and Gates | all gates |
| Shortest Bridge | one island's border cells |
| As Far From Land As Possible | all land cells |
| Map of Highest Peak | initial water cells |

**Pattern to internalize:**

> "MULTI-SOURCE BFS = seed queue with ALL sources at distance 0. Each cell's BFS distance = MIN distance from ANY source. O(mn) for grids."

---

## Cross-references

- **Reference card (post-mastery):** [`../Rotting_Oranges.md`](../Rotting_Oranges.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Number_of_Islands.md`](./Number_of_Islands.md), [`Max_Area_of_Island.md`](./Max_Area_of_Island.md).
  - Coming next: [`01_Matrix.md`](./01_Matrix.md), [`Surrounded_Regions.md`](./Surrounded_Regions.md), [`Number_of_Enclaves.md`](./Number_of_Enclaves.md).
