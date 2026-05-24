# Minimum Weight Cycle — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Minimum_Weight_Cycle.md`](../Minimum_Weight_Cycle.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://www.geeksforgeeks.org/problems/minimum-weight-cycle/1

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. **The lesson: a minimum-weight cycle through edge (u, v, w) = w + shortest u→v path AVOIDING that edge. Try every edge as the "closing edge," sum w + Dijkstra-without-edge; take the minimum.**

**Map of this file (9 sections):**

1. Read the problem
2. Cycle through a fixed edge
3. Dijkstra "skip one edge" trick
4. Algorithm
5. Code
6. Trace it
7. Alternative — Floyd-Warshall for dense graphs
8. Common pitfalls
9. The shape — per-edge shortest-path probes

---

## 1. Read the problem

Undirected weighted graph (positive weights). A CYCLE visits distinct vertices and returns to its start; its WEIGHT is the sum of its edge weights. Find the minimum-weight cycle, or -1 if no cycle exists.

**Example:** triangle with edges (1-2, 5), (2-3, 3), (1-3, 4). Only cycle: 1 → 2 → 3 → 1, weight = 5 + 3 + 4 = **12**.

---

## 2. Cycle through a fixed edge

> **Mini-refresher: every cycle CONTAINS some edge.**
>
> Pick any edge (u, v, w). A cycle containing it = the edge plus some u-to-v path NOT using this edge.
>
> Cycle weight = `w + shortestPath(u, v, excluding the edge (u, v))`.

If we compute that "shortest path excluding the edge" for EVERY edge and take the minimum of `w + d`, we find the minimum-weight cycle.

---

## 3. Dijkstra "skip one edge" trick

For each edge i (with endpoints u, v, weight w):

1. Remove edge i from the graph.
2. Run Dijkstra from u; read off `d[v]`.
3. If finite, candidate cycle weight = `w + d[v]`.
4. Restore edge i.

Efficient implementation: don't actually mutate the graph. Tag each adjacency entry with the edge ID; during Dijkstra, skip the entry whose ID matches `skipId`. Same effect, no copies.

---

## 4. Algorithm

```
build adj with (neighbor, weight, edge_id) entries
best = +∞
for each edge i = (u, v, w):
    d = dijkstra(u, skipId = i)[v]
    if d < ∞: best = min(best, w + d)
return best if best < ∞ else -1
```

E Dijkstra runs × O((V + E) log V) per run = **O(E · (V + E) log V)** overall.

---

## 5. Code

**C++:**

```cpp
int minimumWeightCycle(int n, vector<vector<int>>& edges) {
    vector<vector<tuple<int, int, int>>> adj(n + 1);
    for (int i = 0; i < (int)edges.size(); ++i) {
        int u = edges[i][0], v = edges[i][1], w = edges[i][2];
        adj[u].push_back({v, w, i});
        adj[v].push_back({u, w, i});
    }

    auto dijkstraSkip = [&](int src, int dst, int skipId) {
        vector<int> dist(n + 1, INT_MAX);
        dist[src] = 0;
        priority_queue<pair<int, int>, vector<pair<int, int>>, greater<>> pq;
        pq.push({0, src});
        while (!pq.empty()) {
            auto [d, u] = pq.top(); pq.pop();
            if (d > dist[u]) continue;
            for (auto& [v, w, id] : adj[u]) {
                if (id == skipId) continue;
                if (d + w < dist[v]) {
                    dist[v] = d + w;
                    pq.push({dist[v], v});
                }
            }
        }
        return dist[dst];
    };

    int best = INT_MAX;
    for (int i = 0; i < (int)edges.size(); ++i) {
        int u = edges[i][0], v = edges[i][1], w = edges[i][2];
        int d = dijkstraSkip(u, v, i);
        if (d != INT_MAX) best = min(best, w + d);
    }
    return best == INT_MAX ? -1 : best;
}
```

Complexity: **O(E · (V + E) log V)** time, **O(V + E)** space.

---

## 6. Trace it

Triangle: edges `[(1, 2, 5), (2, 3, 3), (1, 3, 4)]`.

**Edge 0 (1-2, w=5):** Dijkstra from 1, skip edge 0.
Adjacencies from 1: (3, 4, edge 2). From 3: (2, 3, edge 1).
Path 1 → 3 → 2: cost 4 + 3 = 7. d[2] = 7. Candidate = 5 + 7 = **12**.

**Edge 1 (2-3, w=3):** Dijkstra from 2, skip edge 1.
Path 2 → 1 → 3: 5 + 4 = 9. Candidate = 3 + 9 = **12**.

**Edge 2 (1-3, w=4):** Dijkstra from 1, skip edge 2.
Path 1 → 2 → 3: 5 + 3 = 8. Candidate = 4 + 8 = **12**.

Minimum: 12.  ✓

All three perspectives find the same cycle. Taking the min is harmless when ties exist.

---

## 7. Alternative — Floyd-Warshall for dense graphs

For small V (≤ 400-ish), Floyd-Warshall computes all-pairs shortest paths in O(V³). Then for each edge (u, v, w), the cycle through u-v is `w + dist_through_others(u, v)`.

Care needed: standard `dist[u][v]` includes the edge (u, v) itself. Use the "shortest path with intermediate ≠ direct edge" formulation, or recompute selectively.

> **Mini-refresher: alternative formulation.**
>
> For each pair (i, j) with an edge of weight w(i, j), and intermediate k ≠ i, j:
> `cycle = w(i, j) + dist[i][k] + dist[k][j]` (path i→k + path k→j + the direct edge).
> Take the minimum.

Useful when V is small and E is large.

---

## 8. Common pitfalls

1. **Removing the edge by physically erasing.** Inefficient and error-prone in multigraphs. Use edge-id skipping.
2. **Forgetting the edge is undirected — only skipping one direction.** Both `(u → v, id)` and `(v → u, id)` need the same edge id; skipping by id handles both directions.
3. **Using BFS for weighted graphs.** Wrong unless weights are unit.
4. **Returning -1 when a cycle exists.** Make sure to check `best != INT_MAX` correctly.
5. **Counting trivial "self-cycles" (single edge)?** A cycle requires DISTINCT vertices apart from start = end. A single edge u-v IS NOT a cycle. The algorithm correctly skips this because dijkstra-without-the-edge needs another path.
6. **Overflow on `w + d`.** Cast to long long if weights are large.

---

## 9. The shape — per-edge shortest-path probes

The pattern: **enumerate one edge as "special"; solve the rest with shortest-path; combine.**

| Problem | Special edge |
|---|---|
| **This problem** | the cycle-closing edge |
| Second-shortest path | each edge on the first shortest path; recompute SP avoiding it |
| Replacement paths | each edge removed, compute s-t SP |
| Critical edges in MST | edges that must be in every MST |
| Find a Bridge | removing the bridge disconnects |

**Pattern to internalize:**

> "For 'minimum cycle' or 'second-shortest' problems, ENUMERATE one edge as special, run shortest-path on the rest, take the minimum across choices."

---

> **Self-check — the question to ask next time.**
>
> When the problem asks for the minimum CYCLE in a weighted graph, ask:
>
> > **"Can I fix one edge and find the shortest path between its endpoints WITHOUT it? Sum gives a candidate cycle weight. Try every edge; take min."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Minimum_Weight_Cycle.md`](../Minimum_Weight_Cycle.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Network_Delay_Time.md`](./Network_Delay_Time.md), [`Shortest_Path_in_an_Undirected_Graph.md`](./Shortest_Path_in_an_Undirected_Graph.md), [`Find_the_City_With_the_Smallest_Number_of_Neighbors.md`](./Find_the_City_With_the_Smallest_Number_of_Neighbors.md).
  - **Topic complete — next: Greedy.**
