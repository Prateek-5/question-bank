# Cheapest Flights Within K Stops — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Cheapest_Flights_Within_K_Stops.md`](../Cheapest_Flights_Within_K_Stops.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/cheapest-flights-within-k-stops/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **The lesson: Dijkstra finds the cheapest path BUT IGNORES HOP COUNT — wrong here. Use BOUNDED BELLMAN-FORD: K+1 passes, with a SNAPSHOT COPY of the dist array per pass so each pass relaxes exactly one new edge.**

**Map of this file (10 sections):**

1. Read the problem
2. Why "stops" matters
3. Why Dijkstra fails
4. The (city, hops) state
5. Bellman-Ford bounded by K+1 passes
6. The critical snapshot trick
7. Code
8. Trace it
9. Common pitfalls
10. The shape — shortest path with hop constraint

---

## 1. Read the problem

`n` cities (0..n-1), directed flights `(from, to, price)`, source `src`, destination `dst`, integer `K`. Find the **cheapest price** from src to dst using **AT MOST K STOPS** (intermediate cities). Return -1 if impossible.

**K stops = up to K+1 flights** (e.g., K=0 means direct only; K=1 means at most 2 flights, with one layover).

**Example:** flights = `[[0,1,100], [1,2,100], [0,2,500]]`, src=0, dst=2.

- K=0 (direct only): only `0 → 2` at 500. Answer **500**.
- K=1 (≤1 stop): `0 → 1 → 2` at 200. Answer **200**.

---

## 2. Why "stops" matters

The "fewest stops" constraint can change the answer dramatically — direct flights are usually more expensive than connecting ones. The cheapest UNCONSTRAINED path may use too many hops.

We need to MINIMIZE COST SUBJECT TO HOP COUNT ≤ K+1.

---

## 3. Why Dijkstra fails

Dijkstra greedily finalizes nodes by lowest cost. With K=0 on the example, Dijkstra goes:

```
Pop (0, 0). Push (100, 1), (500, 2).
Pop (100, 1). Push (200, 2).
Pop (200, 2). Says answer = 200.
```

But that 200 uses 2 flights — violates K=0! Dijkstra doesn't track hop count, so it picks paths that are "cheaper" but use too many hops.

You CAN extend Dijkstra by adding hops to the state, but it gets tricky (and not always optimal because you might revisit nodes with the same cost but fewer hops). The cleaner pattern is Bellman-Ford.

---

## 4. The (city, hops) state

> **Mini-refresher: when greedy fails, add the constraint to the state.**
>
> Define `f[j][c]` = cheapest cost to reach city c from src using AT MOST j flights.
>
> Base: `f[0][src] = 0`, all other `f[0][*] = ∞`.
>
> Transition:
> ```
> f[j][c] = min( f[j-1][c],                    # no new flight this pass
>                min over edges (u, c, w) of f[j-1][u] + w )  # new flight in this pass
> ```
>
> Final answer: `f[K+1][dst]`.

The "at most j flights" constraint is encoded in the DP dimension j — exactly what Dijkstra was missing.

---

## 5. Bellman-Ford bounded by K+1 passes

> **Mini-refresher: Bellman-Ford = relax all edges, V-1 times.**
>
> Each pass of Bellman-Ford extends the best path by one more edge. After i passes, `dist[c]` is the cheapest path using ≤ i edges.
>
> If we STOP after K+1 passes, `dist[c]` is the cheapest path using ≤ K+1 edges = ≤ K stops.

So Bellman-Ford has the hop bound built into its iteration count — perfect fit.

---

## 6. The critical snapshot trick

> **Mini-refresher: in-place relaxation lets paths "leak" across passes.**
>
> Naive Bellman-Ford updates dist in-place. In one pass:
> - Relax (src, u): dist[u] = w1.
> - Then relax (u, v) using the JUST-UPDATED dist[u]: dist[v] = w1 + w2.
>
> Now dist[v] reflects a 2-edge path, but we're still in "pass 1"!
>
> **Fix:** at the start of each pass, copy dist → newDist. Read from `dist` (the snapshot), write to `newDist`. At the end, set dist = newDist.

This guarantees: pass i extends paths by EXACTLY one edge.

```
dist[src] = 0, others = ∞
for i in 0..K:                           # K+1 passes
    newDist = copy of dist
    for each edge (u, v, w):
        if dist[u] + w < newDist[v]:
            newDist[v] = dist[u] + w
    dist = newDist
```

---

## 7. Code

**C++:**

```cpp
int findCheapestPrice(int n, vector<vector<int>>& flights, int src, int dst, int K) {
    const int INF = INT_MAX;
    vector<int> dist(n, INF);
    dist[src] = 0;

    for (int i = 0; i <= K; ++i) {
        vector<int> newDist = dist;
        for (auto& f : flights) {
            int u = f[0], v = f[1], w = f[2];
            if (dist[u] == INF) continue;
            if (dist[u] + w < newDist[v]) {
                newDist[v] = dist[u] + w;
            }
        }
        dist = newDist;
    }

    return dist[dst] == INF ? -1 : dist[dst];
}
```

Complexity: **O((K + 1) · E)** time, **O(n)** space.

---

## 8. Trace it

**Example, K=0:** 1 pass.

```
dist = [0, ∞, ∞]

Pass 1: newDist = [0, ∞, ∞]
  (0,1,100): dist[0]+100 = 100. newDist[1] = 100.
  (1,2,100): dist[1] = ∞. Skip.
  (0,2,500): dist[0]+500 = 500. newDist[2] = 500.
dist = [0, 100, 500].

Return dist[2] = 500.  ✓
```

**Example, K=1:** 2 passes. After pass 1 (same as above), dist = [0, 100, 500].

```
Pass 2: newDist = [0, 100, 500]
  (0,1,100): 100 not < newDist[1]=100. Skip.
  (1,2,100): dist[1]+100 = 200 < 500. newDist[2] = 200.
  (0,2,500): 500 not < newDist[2]=200. Skip.
dist = [0, 100, 200].

Return dist[2] = 200.  ✓
```

Without the snapshot, pass 1 might have set newDist[1]=100 and then immediately used it to set newDist[2]=200 — collapsing two hops into one pass and wrongly answering 200 for K=0.

---

## 9. Common pitfalls

1. **Running K passes instead of K+1.** K stops = K+1 flights. Off-by-one is the most common bug.
2. **In-place update.** Without the snapshot, paths chain across edges within a pass.
3. **Trying to extend Dijkstra naively.** Dijkstra finalizes nodes by cost; same node might be reachable with fewer hops but higher cost later. Requires extra state and a re-visit policy.
4. **Skipping the `dist[u] == INF` guard.** Adding w to INT_MAX overflows.
5. **Not handling `src == dst` early.** Most solutions return 0 naturally because dist[src] = 0; double-check.
6. **Building adj list and forgetting the snapshot.** Bellman-Ford iterates over the EDGE LIST, not an adjacency list. Iterate over edges directly.

---

## 10. The shape — shortest path with hop constraint

The pattern: **cheapest path with an EDGE-COUNT constraint.**

| Problem | Constraint |
|---|---|
| **This problem** | ≤ K stops (≤ K+1 edges) |
| Shortest Path in K-Hop Network | ≤ K edges |
| Detect negative cycle | run V passes, check for improvement |
| Bellman-Ford classic | finds shortest paths even with negative weights |
| Longest path in DAG | DP on topological order |
| Walks of length exactly k | matrix exponentiation of adjacency |

**Pattern to internalize:**

> "When greedy (Dijkstra) ignores a side constraint, encode the constraint in the state. For hop-bounded shortest path, BELLMAN-FORD with K+1 passes + SNAPSHOT copies."

A Dijkstra variant with `(cost, city, hops)` state also works and can be faster on sparse instances, but Bellman-Ford is cleaner.

---

> **Self-check — the question to ask next time.**
>
> When the problem says "cheapest path BUT at most K hops," ask:
>
> > **"Does pure Dijkstra ignore the hop bound? Yes — use Bellman-Ford with K+1 passes and a per-pass copy of `dist`."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Cheapest_Flights_Within_K_Stops.md`](../Cheapest_Flights_Within_K_Stops.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Network_Delay_Time.md`](./Network_Delay_Time.md), [`Shortest_Path_in_an_Undirected_Graph.md`](./Shortest_Path_in_an_Undirected_Graph.md).
  - Coming next: [`Find_the_City_With_the_Smallest_Number_of_Neighbors.md`](./Find_the_City_With_the_Smallest_Number_of_Neighbors.md), [`Number_of_Operations_to_Make_Network_Connected.md`](./Number_of_Operations_to_Make_Network_Connected.md).
