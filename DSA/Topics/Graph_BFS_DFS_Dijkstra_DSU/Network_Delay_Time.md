# Network Delay Time

**Problem Link:**
https://leetcode.com/problems/network-delay-time/

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Read the Scenario

There are `n` network nodes labeled `1` to `n`. You're given a list of directed, weighted edges `times[i] = [u_i, v_i, w_i]` meaning "a signal from u takes w_i time to reach v." You send a signal from a starting node `k`.

Return the **time it takes** for the signal to reach **all** nodes. If some node is unreachable, return -1.

Example: `times = [[2,1,1], [2,3,1], [3,4,1]]`, `n = 4`, `k = 2`.

From 2:
- Signal reaches 1 in 1.
- Signal reaches 3 in 1.
- Signal reaches 4 via 3, so 1 + 1 = 2.

The signal reaches all nodes. Max time to any node = 2. Return **2**.

If we change `n = 5` (adding a disconnected node 5), node 5 never gets the signal. Return **-1**.

----------------------------------------

## Step 2: Reframe as "Shortest Paths"

Reading "time for the signal to reach each node" is the same as asking "what's the shortest path from k to every other node?" (The signal travels along the fastest route.)

So we need single-source shortest paths from k. Once we have distances `d[1], d[2], ..., d[n]`, the answer is `max(d[i])` if all are finite; else -1.

----------------------------------------

## Step 3: BFS or Something More?

If all edge weights were the same (say 1), a plain BFS would suffice: the number of edges on the shortest path equals the distance.

But here edges have different weights. BFS assumes each step has equal cost; with varying weights, BFS gives wrong answers. Example: `A --10--> B --1--> C`, and also `A --5--> C`. BFS would say A→B→C is "2 hops" and A→C is "1 hop"; BFS picks A→C, distance says the edge weight is 5. But it should compare 5 vs 10+1=11. OK 5 is still better. Let me try a different example.

`A --1--> B --1--> C` and `A --100--> C`. BFS from A visits B at depth 1, C at depth 1 (via A→C direct edge). Says C's distance is 100. But through B it's 2 (which is smaller). Wrong.

The issue is BFS walks in number-of-edges order. What we actually want is the reverse: traverse in **total-weight order**.

----------------------------------------

## Step 4: Generalize BFS to Weighted Edges

What structure gives us the next-nearest unvisited node in weighted graphs? A **min-heap** keyed by "current best known distance."

Algorithm:
1. Initialize `d[k] = 0`, all others = ∞.
2. Push `(0, k)` into a min-heap.
3. While heap not empty:
   - Pop `(d_u, u)` — the closest unvisited node.
   - If `d_u > d[u]`, this is a stale entry (we found a better path since pushing it). Skip.
   - For each outgoing edge `(u, v, w)`: if `d[u] + w < d[v]`, update `d[v] = d[u] + w` and push `(d[v], v)`.

This is the canonical **Dijkstra's algorithm** — though I want to emphasize we arrived at it by generalizing BFS to handle variable edge weights.

----------------------------------------

## Step 5: Why "Stale Entry" Skipping Matters

Each push adds an entry; we might push the same node multiple times before any of its entries are popped. The **first time** a node is popped is when we have its true shortest distance (this is the core invariant of Dijkstra). Later pops of the same node are stale — ignore them.

Without skipping, the algorithm still gives correct answers but wastes work on outdated entries.

The invariant proof: when we pop `u` with distance `d`, every unpopped entry has distance ≥ `d` (because the heap is a min-heap). So any future path to `u` would go through some node with distance ≥ `d`, making total ≥ `d` — can't improve. Hence `d` is optimal for `u`.

This invariant is why Dijkstra requires **non-negative edge weights**. With negatives, a later path could subtract and improve — so the "already-popped distance is optimal" assumption fails. (That's when you need Bellman-Ford.)

In our problem, weights are non-negative (transmission times), so Dijkstra is perfect.

----------------------------------------

## Step 6: Trace on the Example

`times = [[2,1,1], [2,3,1], [3,4,1]]`, `n = 4`, `k = 2`.

Graph (directed):
- 2 → 1 (w=1)
- 2 → 3 (w=1)
- 3 → 4 (w=1)

```
d = [∞, ∞, 0, ∞, ∞] (index 1..4, d[2]=0)
heap = [(0, 2)]

Pop (0, 2). d[2]=0 matches. Process neighbors:
  (2, 1, 1): d[2]+1 = 1 < ∞. d[1]=1. Push (1, 1).
  (2, 3, 1): d[2]+1 = 1 < ∞. d[3]=1. Push (1, 3).
heap = [(1, 1), (1, 3)]

Pop (1, 1). d[1]=1 matches. Neighbors of 1: none.
heap = [(1, 3)]

Pop (1, 3). d[3]=1 matches. Neighbors:
  (3, 4, 1): d[3]+1 = 2 < ∞. d[4]=2. Push (2, 4).
heap = [(2, 4)]

Pop (2, 4). d[4]=2 matches. Neighbors of 4: none.
heap empty.
```

d = [_, 1, 0, 1, 2]. Max = 2. Return **2**. ✓

----------------------------------------

## Step 7: Name It

We derived **Dijkstra's algorithm** by generalizing BFS with a priority queue. The name comes with it, but the key mental move was:

> "BFS assumes uniform edge weights. Replace its FIFO queue with a min-heap keyed by distance, and it generalizes to non-negative weighted graphs."

This generalization is one of the foundational moves in graph algorithms. Recognizing it unlocks Dijkstra, A* (Dijkstra with a heuristic), Prim's MST (similar structure, different key), and more.

----------------------------------------

## Step 8: Complexity

Time: each edge is relaxed at most once (when its endpoint is first popped). Each relaxation might push into the heap, so the heap has O(E) operations. Each heap op is O(log V). Total: **O(E log V)**.

If using `priority_queue` with potentially stale entries, worst-case is O((V+E) log V) — same order.

Space: heap holds O(E) entries worst case. **O(V + E)**.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int networkDelayTime(vector<vector<int>>& times, int n, int k) {
    // Build adjacency list
    vector<vector<pair<int,int>>> g(n + 1);      // 1-indexed
    for (auto& e : times) g[e[0]].push_back({e[1], e[2]});

    vector<int> d(n + 1, INT_MAX);
    d[k] = 0;
    priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;
    pq.push({0, k});

    while (!pq.empty()) {
        auto [dist, u] = pq.top(); pq.pop();
        if (dist > d[u]) continue;               // stale entry
        for (auto [v, w] : g[u]) {
            if (d[u] + w < d[v]) {
                d[v] = d[u] + w;
                pq.push({d[v], v});
            }
        }
    }

    int ans = 0;
    for (int i = 1; i <= n; ++i) {
        if (d[i] == INT_MAX) return -1;          // unreachable
        ans = max(ans, d[i]);
    }
    return ans;
}
```

Implementation details:
- Node indices are 1..n; I size vectors as n+1 and ignore index 0.
- `priority_queue<..., greater<>>` makes a min-heap.
- The stale-check `dist > d[u]` avoids re-processing nodes whose better path was found later.
- At the end, the answer is the max d[i], or -1 if any d[i] is still `INT_MAX`.

----------------------------------------

## Step 10: Follow-up Questions

- **Negative edge weights.** Dijkstra fails. Use Bellman-Ford (O(VE)) or SPFA.
- **All-pairs shortest paths.** Run Dijkstra from each node (O(V·E log V)) or Floyd-Warshall (O(V³)).
- **Bounded number of hops (like Cheapest Flights Within K Stops).** Modify Bellman-Ford to stop after K iterations.
- **Shortest path with specific constraints (e.g., must visit certain nodes).** Harder — often DP on subsets (Held-Karp for TSP).
- **Grid-based variant (shortest path in a weighted grid).** Same Dijkstra, 4 or 8 directional neighbors.
- **Why not BFS?** Equal-weighted only. With 0/1 weights, "0-1 BFS" with a deque works.
