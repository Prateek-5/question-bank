# Network Delay Time — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Network_Delay_Time.md`](../Network_Delay_Time.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/network-delay-time/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: "time for the signal to reach ALL nodes" = SINGLE-SOURCE SHORTEST PATHS, then take the MAX. Use DIJKSTRA. Return -1 if any node is unreachable.**

**Map of this file (9 sections):**

1. Read the problem
2. The reframe — max of shortest paths
3. Why BFS doesn't work
4. Dijkstra — BFS generalized with a heap
5. Code
6. Trace it
7. Why non-negative weights are required
8. Common pitfalls
9. The shape — single-source shortest path

---

## 1. Read the problem

`n` nodes labeled 1..n. Directed weighted edges `times[i] = [u, v, w]` mean a signal from u reaches v in w units of time. Starting from node `k`, return the **time for the signal to reach EVERY node**, or `-1` if some node never gets it.

**Example:** `times = [[2,1,1], [2,3,1], [3,4,1]]`, `n = 4`, `k = 2`.

Distances from 2: d[1]=1, d[2]=0, d[3]=1, d[4]=2. Max = 2 → return **2**.

If `n = 5` (a disconnected node 5 added), d[5] = ∞ → return **-1**.

---

## 2. The reframe — max of shortest paths

> **Mini-refresher: the "broadcast time" is the LAST node to receive.**
>
> Since the signal propagates along the fastest route from k to every node, "time to reach all" = `max(d[v])` over all v.
>
> If any d[v] is ∞ (unreachable), the signal never finishes → return -1.

So the algorithm splits cleanly:
1. Compute single-source shortest paths from k.
2. Take the max; check for ∞.

---

## 3. Why BFS doesn't work

BFS processes nodes in HOP-COUNT order, not WEIGHT order. Counter-example:

```
A --1--> B --1--> C
A --100--> C
```

BFS from A visits B (1 hop) then C (1 hop via direct edge). It claims `d[C] = 100`, but actually `d[C] = 2` via A → B → C.

BFS is right ONLY when all edges have equal weight.

---

## 4. Dijkstra — BFS generalized with a heap

> **Mini-refresher: replace FIFO queue with min-heap on distance.**
>
> Dijkstra processes nodes in order of "best known distance from source." A min-heap of `(d, u)` gives us the closest unfinalized node in O(log V).
>
> Each pop finalizes the popped node's distance — guaranteed correct because all weights are non-negative (any future path is longer).

```
d[k] = 0; others = ∞
heap = [(0, k)]
while heap:
    (du, u) = pop min
    if du > d[u]: continue                  # stale entry
    for (v, w) in adj[u]:
        if d[u] + w < d[v]:
            d[v] = d[u] + w
            heap.push((d[v], v))
```

Same structure as BFS — only the queue type changed.

---

## 5. Code

**C++:**

```cpp
int networkDelayTime(vector<vector<int>>& times, int n, int k) {
    vector<vector<pair<int, int>>> g(n + 1);
    for (auto& e : times) g[e[0]].push_back({e[1], e[2]});

    vector<int> d(n + 1, INT_MAX);
    d[k] = 0;
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<>> pq;
    pq.push({0, k});

    while (!pq.empty()) {
        auto [du, u] = pq.top(); pq.pop();
        if (du > d[u]) continue;
        for (auto& [v, w] : g[u]) {
            if (d[u] + w < d[v]) {
                d[v] = d[u] + w;
                pq.push({d[v], v});
            }
        }
    }

    int ans = 0;
    for (int i = 1; i <= n; ++i) {
        if (d[i] == INT_MAX) return -1;
        ans = max(ans, d[i]);
    }
    return ans;
}
```

Complexity: **O((V + E) log V)** time, **O(V + E)** space.

---

## 6. Trace it

`times = [[2,1,1], [2,3,1], [3,4,1]]`, n=4, k=2.

```
g[2] = [(1, 1), (3, 1)]
g[3] = [(4, 1)]
g[1] = g[4] = []

d = [_, ∞, 0, ∞, ∞]. heap = [(0, 2)].

Pop (0, 2). Relax:
  2 → 1 (w=1): d[1] = 1, push (1, 1).
  2 → 3 (w=1): d[3] = 1, push (1, 3).

Pop (1, 1). No outgoing edges.

Pop (1, 3). Relax:
  3 → 4 (w=1): d[4] = 2, push (2, 4).

Pop (2, 4). No outgoing edges. heap empty.

d = [_, 1, 0, 1, 2]. Max = 2.  Return 2.  ✓
```

---

## 7. Why non-negative weights are required

> **Mini-refresher: Dijkstra's correctness relies on the "popped = finalized" invariant.**
>
> When you pop `(du, u)` from the min-heap, every UNPOPPED entry has distance ≥ du. So any future path to u would pass through some node with distance ≥ du, total ≥ du. No improvement possible — u's distance is final.
>
> This argument BREAKS with negative weights: a later path could subtract and improve. For that, use Bellman-Ford.

Network delays here are non-negative — Dijkstra is safe.

---

## 8. Common pitfalls

1. **Using BFS.** Wrong for weighted graphs.
2. **Comparing `du < d[u]` instead of `du > d[u]`.** The stale-check is `du > d[u]` (pop is stale if its key is worse than current best).
3. **Forgetting the unreachable check.** If any d[i] stays at ∞, return -1 — don't include ∞ in the max.
4. **Adding reverse edges.** This graph is DIRECTED; only push the forward edge.
5. **Indexing from 0 when input is 1-indexed.** Allocate n+1 slots and ignore index 0.
6. **Stopping at "we found the destination."** This problem requires distances to ALL nodes — let the loop drain.

---

## 9. The shape — single-source shortest path

The pattern: **single-source shortest path on a non-negative-weight graph.**

| Problem | Twist |
|---|---|
| **This problem** | take max(d[i]); -1 if unreachable |
| Shortest Path in Undirected Graph | return the path itself |
| Path with Minimum Effort | grid; weight = max edge on path |
| Swim in Rising Water | grid; weight = max cell on path |
| Cheapest Flights Within K Stops | + hop constraint → Bellman-Ford |
| The Maze II | grid Dijkstra with rolling-ball moves |

**Pattern to internalize:**

> "Single-source + non-negative weights = Dijkstra. Lazy deletion via stale-check. O((V + E) log V)."

---

> **Self-check — the question to ask next time.**
>
> When the problem says "time/cost from one source to many destinations," ask:
>
> > **"Are weights non-negative? Dijkstra with a min-heap. Take max (or specific value) of d[i] at the end."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Network_Delay_Time.md`](../Network_Delay_Time.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Shortest_Path_in_an_Undirected_Graph.md`](./Shortest_Path_in_an_Undirected_Graph.md), [`Shortest_Path_in_Binary_Matrix.md`](./Shortest_Path_in_Binary_Matrix.md).
  - Coming next: [`Cheapest_Flights_Within_K_Stops.md`](./Cheapest_Flights_Within_K_Stops.md), [`Find_the_City_With_the_Smallest_Number_of_Neighbors.md`](./Find_the_City_With_the_Smallest_Number_of_Neighbors.md).
