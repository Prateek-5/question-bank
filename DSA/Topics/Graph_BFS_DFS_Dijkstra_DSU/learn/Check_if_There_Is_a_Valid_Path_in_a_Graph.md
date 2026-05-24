# Check if There Is a Valid Path in a Graph — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Check_if_There_Is_a_Valid_Path_in_a_Graph.md`](../Check_if_There_Is_a_Valid_Path_in_a_Graph.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/find-if-path-exists-in-graph/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: pure REACHABILITY between two nodes. Three valid tools: BFS, DFS, UNION-FIND. Same O(V + E) — pick based on query pattern.**

**Map of this file (8 sections):**

1. Read the problem
2. The three tools
3. BFS approach
4. Union-Find approach
5. Code (both)
6. Trace it
7. When to prefer each
8. The shape — single-pair reachability

---

## 1. Read the problem

Given an **undirected** graph with `n` nodes (0-indexed) and an edge list, return true if a path exists from `source` to `destination`.

**Examples:**

- `n=3, edges=[[0,1], [1,2], [2,0]]`, source=0, destination=2. Triangle — reachable. **true**.
- `n=6, edges=[[0,1], [0,2], [3,5], [5,4], [4,3]]`, source=0, destination=5. Two disjoint components {0,1,2} and {3,4,5}. **false**.

---

## 2. The three tools

> **Mini-refresher: reachability has three textbook solutions.**
>
> 1. **BFS from source** — pop until destination is dequeued or queue empties.
> 2. **DFS from source** — recursive or stack-based.
> 3. **Union-Find** — union every edge; check `find(source) == find(destination)`.
>
> All are O(V + E) for a single query. Union-Find amortizes better for MANY queries on the same static graph.

---

## 3. BFS approach

```
build adj list
visited = [False] * n
queue = [source]
visited[source] = True
while queue:
    u = pop
    if u == destination: return True
    for v in adj[u]:
        if not visited[v]:
            visited[v] = True
            queue.push(v)
return False
```

Standard.

---

## 4. Union-Find approach

> **Mini-refresher: Disjoint Set Union (DSU).**
>
> Maintain disjoint components. Two operations:
> - **find(x)**: returns x's component representative (with path compression).
> - **unite(a, b)**: merges a's and b's components.
>
> After uniting every edge, two nodes are reachable iff they share a representative.

```
DSU dsu(n)
for (a, b) in edges: dsu.unite(a, b)
return dsu.find(source) == dsu.find(destination)
```

With path compression + union by rank, each op is **O(α(n))** — effectively constant.

---

## 5. Code (both)

**C++ — BFS:**

```cpp
bool validPath(int n, vector<vector<int>>& edges, int source, int destination) {
    vector<vector<int>> adj(n);
    for (auto& e : edges) {
        adj[e[0]].push_back(e[1]);
        adj[e[1]].push_back(e[0]);
    }
    vector<bool> visited(n, false);
    queue<int> q;
    q.push(source);
    visited[source] = true;
    while (!q.empty()) {
        int u = q.front(); q.pop();
        if (u == destination) return true;
        for (int v : adj[u]) {
            if (!visited[v]) {
                visited[v] = true;
                q.push(v);
            }
        }
    }
    return false;
}
```

**C++ — Union-Find:**

```cpp
class DSU {
    vector<int> parent;
public:
    DSU(int n) : parent(n) { iota(parent.begin(), parent.end(), 0); }
    int find(int x) { return parent[x] == x ? x : parent[x] = find(parent[x]); }
    void unite(int a, int b) { parent[find(a)] = find(b); }
};

bool validPath(int n, vector<vector<int>>& edges, int source, int destination) {
    DSU dsu(n);
    for (auto& e : edges) dsu.unite(e[0], e[1]);
    return dsu.find(source) == dsu.find(destination);
}
```

Complexity: both **O((V + E) · α(n))** time, **O(V + E)** space.

---

## 6. Trace it

**Example 2: `n=6, edges=[[0,1], [0,2], [3,5], [5,4], [4,3]]`, source=0, dest=5.**

**BFS:**
```
adj[0] = [1, 2], adj[1] = [0], adj[2] = [0], adj[3] = [5, 4], adj[4] = [5, 3], adj[5] = [3, 4].
queue = [0], visited = {0}.

Pop 0. Push 1, 2. visited = {0, 1, 2}.
Pop 1. Already explored.
Pop 2. Already explored.
queue empty. Return false.  ✓ (never reached 5)
```

**Union-Find:**
```
DSU parent = [0,1,2,3,4,5].
unite(0,1): parent[0] = 1.
unite(0,2): find(0)=1, find(2)=2. parent[1] = 2.
unite(3,5): parent[3] = 5.
unite(5,4): find(5)=5, find(4)=4. parent[5] = 4.
unite(4,3): find(4)=4, find(3)=4 (via 5). Same component, no-op.

find(0) = 2 (via 0→1→2). find(5) = 4. Different → return false.  ✓
```

---

## 7. When to prefer each

| Setting | Best tool |
|---|---|
| **Single query, sparse graph** | BFS or DFS (simpler) |
| **Many queries, static graph** | Union-Find (preprocess once) |
| **Incremental edge additions** | Union-Find (handles online efficiently) |
| **Need the path itself** | BFS with parent[] |
| **Need shortest distance** | BFS (gives distances) |
| **Edge weights matter** | Dijkstra, not BFS/Union-Find |

For this problem (single query), either works. Union-Find is shorter to write.

---

## 8. The shape — single-pair reachability

The pattern: **"can A reach B?" without weights.**

| Problem | Tool |
|---|---|
| **This problem** | BFS / DFS / DSU, your pick |
| Number of Connected Components | DFS counting components |
| Friend Circles | DSU |
| Number of Provinces | DFS or DSU |
| Graph Valid Tree | DSU + edge count check |
| Redundant Connection | DSU (find the cycle edge) |

**Pattern to internalize:**

> "Pure reachability + no weights = BFS, DFS, or DSU — all O(V + E). Pick by query pattern: single = BFS/DFS, many or dynamic = DSU."

---

> **Self-check — the question to ask next time.**
>
> When the problem is "is there ANY path from A to B?", ask:
>
> > **"Edges unweighted? Then BFS/DFS/DSU all work. How many queries on the same graph? One → BFS. Many → DSU."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Check_if_There_Is_a_Valid_Path_in_a_Graph.md`](../Check_if_There_Is_a_Valid_Path_in_a_Graph.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Keys_and_Rooms.md`](./Keys_and_Rooms.md), [`Number_of_Provinces.md`](./Number_of_Provinces.md), [`Number_of_Islands.md`](./Number_of_Islands.md).
  - Coming next: [`Course_Schedule_II.md`](./Course_Schedule_II.md), [`Network_Delay_Time.md`](./Network_Delay_Time.md).
