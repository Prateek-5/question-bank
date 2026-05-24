# Is Graph Bipartite — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Is_Graph_Bipartite.md`](../Is_Graph_Bipartite.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/is-graph-bipartite/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: a graph is bipartite iff it has NO ODD CYCLE. Detect with BFS 2-coloring — alternate colors layer-by-layer; conflict if a neighbor already has the same color.**

**Map of this file (9 sections):**

1. Read the problem
2. What "bipartite" means
3. The odd-cycle theorem
4. BFS 2-coloring
5. Code
6. Trace it
7. Disconnected components
8. Common pitfalls
9. The shape — 2-coloring as constraint satisfaction

---

## 1. Read the problem

Given an undirected graph (as adjacency list `graph[u]` = neighbors of u), return true if it's **BIPARTITE**: i.e., the nodes can be split into two disjoint sets A and B such that EVERY edge goes between A and B (no edge stays within a single set).

**Examples:**

- `graph = [[1,3], [0,2], [1,3], [0,2]]` — a 4-cycle `0-1-2-3-0`. Color `0, 2` red; `1, 3` blue. All edges cross → **true**.
- `graph = [[1,2,3], [0,2], [0,1,3], [0,2]]` — triangle `0-1-2`. Any 2-coloring forces two of these three to share a color → **false**.

---

## 2. What "bipartite" means

Picture a college dance: students on the left, faculty on the right. Every connection (edge) is a student-faculty pair; never student-student or faculty-faculty.

If you can partition nodes into "left" and "right" sets and ensure every edge crosses, you have a bipartite graph.

---

## 3. The odd-cycle theorem

> **Mini-refresher: a graph is bipartite iff it has no ODD cycle.**
>
> Why? If you walk around a cycle alternating colors (red, blue, red, blue, ...), to come back to your start with a consistent color, you need an EVEN number of steps. Odd cycles force a conflict.
>
> Triangles (length 3) are the smallest odd cycle. That's why triangles immediately disqualify a graph.

You don't have to enumerate cycles. Just try to 2-color greedily; if you ever hit a conflict, an odd cycle exists.

---

## 4. BFS 2-coloring

```
color = [-1] * n   # -1 = uncolored
for s in 0..n-1:
    if color[s] != -1: continue
    color[s] = 0
    queue = [s]
    while queue:
        u = pop front
        for v in graph[u]:
            if color[v] == -1:
                color[v] = 1 - color[u]    # opposite
                queue.push(v)
            elif color[v] == color[u]:
                return False                # conflict
return True
```

Key:
- Outer loop handles disconnected components.
- Start each component with color 0.
- For each neighbor, assign the opposite color; if already colored, must be opposite.

---

## 5. Code

**C++:**

```cpp
bool isBipartite(vector<vector<int>>& graph) {
    int n = graph.size();
    vector<int> color(n, -1);
    for (int s = 0; s < n; ++s) {
        if (color[s] != -1) continue;
        queue<int> q;
        q.push(s);
        color[s] = 0;
        while (!q.empty()) {
            int u = q.front(); q.pop();
            for (int v : graph[u]) {
                if (color[v] == -1) {
                    color[v] = 1 - color[u];
                    q.push(v);
                } else if (color[v] == color[u]) {
                    return false;
                }
            }
        }
    }
    return true;
}
```

**Python:**

```python
from collections import deque

def isBipartite(graph):
    n = len(graph)
    color = [-1] * n
    for s in range(n):
        if color[s] != -1:
            continue
        color[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for v in graph[u]:
                if color[v] == -1:
                    color[v] = 1 - color[u]
                    q.append(v)
                elif color[v] == color[u]:
                    return False
    return True
```

Complexity: **O(V + E)** time, **O(V)** space.

---

## 6. Trace it

**Bipartite case:** `graph = [[1,3], [0,2], [1,3], [0,2]]` (4-cycle).

```
color = [-1, -1, -1, -1]
s=0: color[0] = 0. queue = [0].
  Pop 0. Neighbors: 1, 3.
    color[1] = 1, push. color[3] = 1, push.
  queue = [1, 3].
  Pop 1. Neighbors: 0 (color 0, opp of 1, OK), 2 (uncolored).
    color[2] = 0, push.
  Pop 3. Neighbors: 0 (OK), 2 (color 0, opp of 1, OK).
  Pop 2. Neighbors: 1 (OK), 3 (OK).
Return true.  ✓
```

**Non-bipartite case:** `graph = [[1,2,3], [0,2], [0,1,3], [0,2]]` (triangle 0-1-2 + extras).

```
s=0: color[0] = 0. queue = [0].
  Pop 0. Neighbors: 1, 2, 3.
    color[1] = 1. color[2] = 1. color[3] = 1.
  Pop 1. Neighbors: 0 (OK), 2 (color 1 == color[1] = 1) → CONFLICT.
Return false.  ✓
```

The triangle `0-1-2` (all three pairwise connected) means after coloring 0 = red, both 1 and 2 must be blue, but 1-2 is an edge between two blues → conflict.

---

## 7. Disconnected components

The outer `for s in 0..n-1` loop is critical — without it, a disconnected component would never get colored. Each component is colored independently; the entire graph is bipartite iff EVERY component is.

> **Mini-refresher: which color a component starts with doesn't matter.**
>
> Flipping every color in one component is also a valid 2-coloring (bipartite is closed under color swap). So starting each new component with 0 is arbitrary but harmless.

---

## 8. Common pitfalls

1. **Iterating only from node 0.** Misses other components.
2. **Treating the graph as directed.** Edges in `graph[u]` should be symmetric (undirected). If only one direction is listed, you must add reverse edges yourself.
3. **Using DFS without color cache.** Re-recursion blows up; always check color before recursing.
4. **`color[v] == color[u]` vs `color[v] != 1 - color[u]`.** Equivalent — but pick one and stick with it for readability.
5. **Forgetting `color[s] = 0` before pushing s.** Without it, the start node looks "uncolored" and you'd re-push.
6. **Starting BFS but assigning color *inside* the pop loop instead of before push.** Then a node can be pushed multiple times with different colors before popping.

---

## 9. The shape — 2-coloring as constraint satisfaction

The pattern: **alternate labels along edges; verify consistency.**

| Problem | Constraint |
|---|---|
| **This problem** | adjacent nodes must differ (2 colors) |
| Possible Bipartition (LC 886) | "dislikes" list, split into two groups |
| Map Coloring (general) | adjacent regions differ (4 colors — NP-hard for 3) |
| Tasks-with-conflicts scheduling | conflicting tasks in different shifts |
| Bipartite Matching | precondition: graph must be bipartite |

**Pattern to internalize:**

> "2-coloring = BFS/DFS that alternates labels along edges. Conflict = odd cycle = not bipartite. O(V + E)."

Generalizations:
- **k-coloring for k ≥ 3** is NP-hard.
- **Edge-coloring** (colors on edges, not nodes) is a different problem with different bounds.

---

> **Self-check — the question to ask next time.**
>
> When the problem says "split into two groups so no edge stays within a group," ask:
>
> > **"Can I run BFS, alternating colors? Each component starts at 0; if any edge connects same-color nodes, fail."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Is_Graph_Bipartite.md`](../Is_Graph_Bipartite.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Keys_and_Rooms.md`](./Keys_and_Rooms.md), [`Find_the_Town_Judge.md`](./Find_the_Town_Judge.md), [`Find_Eventual_Safe_States.md`](./Find_Eventual_Safe_States.md).
  - Coming next: [`Shortest_Path_in_an_Undirected_Graph.md`](./Shortest_Path_in_an_Undirected_Graph.md), [`Course_Schedule_II.md`](./Course_Schedule_II.md).
