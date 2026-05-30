# Shortest Path in an Undirected Graph — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Shortest_Path_in_an_Undirected_Graph.md`](../Shortest_Path_in_an_Undirected_Graph.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://www.geeksforgeeks.org/problems/shortest-path-in-weighted-undirected-graph/1" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/problems/shortest-path-in-weighted-undirected-graph/1</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **The lesson: WEIGHTED shortest path = DIJKSTRA. To also return the PATH (not just the cost), maintain a `parent[]` array updated alongside `dist[]`.**

**Map of this file (10 sections):**

1. Read the problem
2. Which algorithm fits?
3. Dijkstra refresher
4. Parent tracking for path recovery
5. Code
6. Trace it
7. Edge cases
8. Why stale-entry skipping matters
9. Common pitfalls
10. The shape — Dijkstra with reconstruction

---

## 1. Read the problem

Undirected weighted graph with `n` nodes (1-indexed) and `m` edges of positive integer weight. Return the **NODE SEQUENCE** of the shortest path from node 1 to node n, or `[-1]` if unreachable.

**Example:** n=5, edges `{(1,2,2), (2,5,5), (2,3,4), (1,4,1), (4,3,3), (3,5,1)}`.

Candidate paths to 5:
- 1 → 2 → 5: weight 7
- 1 → 2 → 3 → 5: 2 + 4 + 1 = 7
- 1 → 4 → 3 → 5: 1 + 3 + 1 = **5** ← shortest

Return `[1, 4, 3, 5]`.

---

## 2. Which algorithm fits?

> **Mini-refresher: which shortest-path algorithm?**
>
> | Graph property | Algorithm |
> |---|---|
> | Unweighted (or unit weights) | BFS — O(V + E) |
> | Non-negative weights | Dijkstra — O((V + E) log V) |
> | Negative weights allowed | Bellman-Ford — O(V · E) |
> | All-pairs | Floyd-Warshall — O(V³) |

Edges here have varying positive weights → **Dijkstra**.

---

## 3. Dijkstra refresher

Maintain `dist[v]` = best known weight from source to v. Min-heap of `(d, v)` pairs (process closest unfinalized vertex first).

```
dist[s] = 0, all others ∞
heap = [(0, s)]
while heap:
    (d, u) = pop min
    if d > dist[u]: continue   # stale
    for (v, w) in adj[u]:
        if dist[u] + w < dist[v]:
            dist[v] = dist[u] + w
            heap.push((dist[v], v))
```

Correctness: the first time we pop a vertex with its true `dist[v]`, we've finalized it — non-negative weights mean no later path can be shorter.

---

## 4. Parent tracking for path recovery

> **Mini-refresher: store predecessors during relaxation.**
>
> Whenever you UPDATE `dist[v] = dist[u] + w`, also set `parent[v] = u`. Then to reconstruct: walk from destination back through `parent[]` until -1, and reverse.
>
> Critical: parent must be updated EVERY time dist is updated — including when a shorter path is found later. Stale parents = wrong path.

```
path = []
cur = n
while cur != -1:
    path.append(cur)
    cur = parent[cur]
path.reverse()
```

Parent storage is O(V), much cheaper than caching full paths per node (O(V²)).

---

## 5. Code

**C++:**

```cpp
vector<int> shortestPath(int n, int m, vector<vector<int>>& edges) {
    vector<vector<pair<int, int>>> adj(n + 1);
    for (auto& e : edges) {
        int u = e[0], v = e[1], w = e[2];
        adj[u].push_back({v, w});
        adj[v].push_back({u, w});
    }

    const int INF = INT_MAX;
    vector<int> dist(n + 1, INF), parent(n + 1, -1);
    dist[1] = 0;

    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<>> pq;
    pq.push({0, 1});

    while (!pq.empty()) {
        auto [d, u] = pq.top(); pq.pop();
        if (d > dist[u]) continue;
        for (auto& [v, w] : adj[u]) {
            if (dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                parent[v] = u;
                pq.push({dist[v], v});
            }
        }
    }

    if (dist[n] == INF) return {-1};

    vector<int> path;
    for (int cur = n; cur != -1; cur = parent[cur]) path.push_back(cur);
    reverse(path.begin(), path.end());
    return path;
}
```

Complexity: **O((V + E) log V)** time, **O(V + E)** space.

---

## 6. Trace it

Example from section 1.

```
Init: dist = [_, 0, ∞, ∞, ∞, ∞], parent all -1, heap = [(0, 1)].

Pop (0, 1). Relax neighbors of 1:
  1 → 2 (w=2): dist[2] = 2, parent[2] = 1. push (2, 2).
  1 → 4 (w=1): dist[4] = 1, parent[4] = 1. push (1, 4).

Pop (1, 4). Relax:
  4 → 1: 1 + 1 = 2 > dist[1] = 0. Skip.
  4 → 3 (w=3): dist[3] = 4, parent[3] = 4. push (4, 3).

Pop (2, 2). Relax:
  2 → 3 (w=4): 2 + 4 = 6 > dist[3] = 4. Skip.
  2 → 5 (w=5): dist[5] = 7, parent[5] = 2. push (7, 5).

Pop (4, 3). Relax:
  3 → 5 (w=1): 4 + 1 = 5 < 7. dist[5] = 5, parent[5] = 3. push (5, 5).
  Others skipped.

Pop (5, 5). Nothing improves.

Pop (7, 5). d = 7 > dist[5] = 5. STALE — skip.

dist[5] = 5. parent = [_, -1, 1, 4, 1, 3].

Reconstruct from 5: 5 → 3 → 4 → 1 → STOP.
Reverse: [1, 4, 3, 5].  ✓
```

The pivotal moment was when relaxing through 3 lowered dist[5] from 7 to 5; both `dist[5]` AND `parent[5]` got updated.

---

## 7. Edge cases

- **n = 1**: source = destination. dist[1] = 0. Path = [1].
- **Destination unreachable**: dist[n] stays ∞ → return [-1].
- **Multiple edges between the same pair**: Dijkstra naturally picks the lighter one via relaxation.
- **Self-loops**: harmless (`dist[u] + w ≥ dist[u]`).

---

## 8. Why stale-entry skipping matters

The same vertex can be pushed onto the heap multiple times — each time we relax a shorter path, we push a new entry without removing the old one (binary heaps don't support cheap decrease-key).

> **Mini-refresher: lazy deletion.**
>
> When you pop `(d, u)` with `d > dist[u]`, you're looking at a stale entry — already superseded by a better one. Skip with `continue`. The cost is at most O(E log V) total pops, still optimal.

Without the stale check, you'd re-relax neighbors with an outdated d, which is harmless for correctness but wasteful.

---

## 9. Common pitfalls

1. **Forgetting both edge directions.** It's undirected — push (v, w) in adj[u] AND (u, w) in adj[v].
2. **Updating parent only at first relaxation.** A later, shorter path needs a new parent. Update parent EVERY time dist drops.
3. **Returning parents in forward order without reversal.** Walking from n via parent[] gives reverse order.
4. **Using BFS for weighted graphs.** Only valid when all weights are equal.
5. **Initializing dist[s] = ∞.** Then nothing relaxes — fix to 0.
6. **No stale check.** Works but does redundant relaxations.

---

## 10. The shape — Dijkstra with reconstruction

The pattern: **weighted shortest path + retrieve the path itself.**

| Problem | Twist |
|---|---|
| **This problem** | weighted undirected, return path |
| Network Delay Time (LC 743) | weighted, return max dist |
| Cheapest Flights Within K Stops | weighted + hop constraint |
| Find the City With the Smallest Number of Neighbors | weighted, all-pairs reachable count |
| Path with Minimum Effort | grid with weights = absolute height diff |
| Swim in Rising Water | shortest path with "max edge weight" metric |

**Pattern to internalize:**

> "For weighted shortest path with non-negative edges, use Dijkstra. To recover the actual path, maintain `parent[]` updated alongside `dist[]` on every relaxation."

---

> **Self-check — the question to ask next time.**
>
> When a problem says "shortest path" and weights vary, ask:
>
> > **"All weights non-negative? Dijkstra. Need the path itself, not just the cost? Add a `parent[]` array updated every time `dist` improves."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Shortest_Path_in_an_Undirected_Graph.md`](../Shortest_Path_in_an_Undirected_Graph.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Is_Graph_Bipartite.md`](./Is_Graph_Bipartite.md), [`Keys_and_Rooms.md`](./Keys_and_Rooms.md).
  - Coming next: [`Shortest_Path_in_Binary_Matrix.md`](./Shortest_Path_in_Binary_Matrix.md), [`Network_Delay_Time.md`](./Network_Delay_Time.md), [`Cheapest_Flights_Within_K_Stops.md`](./Cheapest_Flights_Within_K_Stops.md).
