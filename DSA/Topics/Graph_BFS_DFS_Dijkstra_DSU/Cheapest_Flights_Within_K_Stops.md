# Cheapest Flights Within K Stops

**Problem Link:**
<a href="https://leetcode.com/problems/cheapest-flights-within-k-stops/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/cheapest-flights-within-k-stops/</a>

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Read the Problem Carefully

You have `n` cities numbered 0..n-1 and a list of directed flights `(from, to, price)`. Find the **cheapest price** to travel from city `src` to city `dst` using **at most K stops** (intermediate cities).

"At most K stops" means: if K = 1, the route can have at most one city between src and dst — i.e., at most 2 flights. If K = 0, we can only take a direct flight.

If no valid route, return -1.

----------------------------------------

## Step 2: Walk Through a Small Example Carefully

Cities 0, 1, 2. Flights: `[[0,1,100], [1,2,100], [0,2,500]]`. src = 0, dst = 2.

If K = 1: I can use at most 1 stop. Options:
- 0 → 2 directly. Cost 500. Zero stops. Valid.
- 0 → 1 → 2. Cost 100 + 100 = 200. One stop. Valid.

Cheapest = **200**.

If K = 0: I can use zero stops — must fly direct.
- 0 → 2 directly. Cost 500. Only option.

Cheapest = **500**.

Interesting: changing K from 1 to 0 changes the answer from 200 to 500. The stops constraint *really* matters — it rules out otherwise-better routes.

----------------------------------------

## Step 3: Why Dijkstra, the Usual Shortest-Path Tool, Isn't Enough

If I ignored the stops constraint, I'd reach for **Dijkstra's algorithm** — it finds the cheapest path from a source using a priority queue. Let me trace it on the K=0 case just to see what happens.

Dijkstra from 0:
- dist = [0, ∞, ∞]. Push (0, 0).
- Pop (0, 0). Expand: (100, 1), (500, 2). dist = [0, 100, 500].
- Pop (100, 1). Expand: (200, 2). dist[2] = 200.
- Pop (200, 2). That's our answer, Dijkstra says 200.

But for K = 0, the correct answer is 500 (the direct flight). Dijkstra gave 200 — the 0 → 1 → 2 path, which uses 1 stop, violating K=0.

**Dijkstra doesn't know about the stops constraint.** It just finds the overall cheapest, ignoring how many hops we used.

So we need something that tracks both cost *and* hops.

----------------------------------------

## Step 4: First Attempt — Track (City, Hops) State

Let's enrich the state. Instead of just "cheapest to reach city c," we track "cheapest to reach city c **using exactly j flights**."

Define `f(j, c) = min cost to reach c from src using at most j flights`.

Base: `f(0, src) = 0`. `f(0, c) = ∞` for c ≠ src. (With 0 flights we're still at src, unable to reach elsewhere.)

Transition: to find `f(j, c)`, we consider two possibilities:
- We reached c using at most j-1 flights: then `f(j, c) = f(j-1, c)` (unchanged).
- We use the j-th flight to arrive at c: then we were at some predecessor u, took flight (u, c, w), so cost is `f(j-1, u) + w`. Minimize over all predecessors.

Combined:
```
f(j, c) = min( f(j-1, c),  min over edges (u, c, w) of f(j-1, u) + w )
```

We want `f(K+1, dst)` — at most K+1 flights = K stops.

This is a 2D DP over (number of flights, city). It directly encodes the constraint into the state.

----------------------------------------

## Step 5: The Classical Name — Bounded Bellman-Ford

This recurrence is **Bellman-Ford's** relaxation, applied exactly **K+1 times**. Bellman-Ford iteratively relaxes all edges; after `i` iterations, `dist[c]` holds the shortest path using at most `i` edges. So running it K+1 times gives the right answer.

The classic Bellman-Ford **updates the distance array in place**. But if I do that here, I break the "at most j edges" property:
- Suppose in one pass I first relax edge `(src, u)`, updating dist[u] = w1.
- Then I relax edge `(u, v)` using the newly-updated dist[u], giving dist[v] = w1 + w2.

Now dist[v] reflects a **2-edge path**, but my counter says I'm in "pass 1" (which should permit at most 1 edge). The in-place update chained two edges in one pass.

The fix: **make a copy of the distance array at the start of each pass** and relax edges by reading from the snapshot but writing to the new copy. This way, each pass relaxes exactly one new edge per city.

```
dist = [∞] * n; dist[src] = 0

for i in 0..K:             # K+1 passes
    newDist = copy of dist
    for each edge (u, v, w):
        if dist[u] + w < newDist[v]:
            newDist[v] = dist[u] + w
    dist = newDist

return dist[dst] if dist[dst] != ∞ else -1
```

The copy is the critical insight. Without it, paths could sneak in extra edges per pass.

----------------------------------------

## Step 6: Trace on K = 0 and K = 1

**K = 0**, src = 0, dst = 2. We do 1 pass.

```
dist = [0, ∞, ∞].

Pass 1: newDist = [0, ∞, ∞].
  (0,1,100): dist[0]+100 = 100 < ∞. newDist[1] = 100.
  (1,2,100): dist[1] = ∞. Skip.
  (0,2,500): dist[0]+500 = 500 < ∞. newDist[2] = 500.
dist = [0, 100, 500].
```

dist[2] = **500**. ✓ (Direct flight only, as expected.)

**K = 1**, same setup. We do 2 passes. After pass 1, dist = [0, 100, 500] (same as above).

```
Pass 2: newDist = [0, 100, 500].
  (0,1,100): dist[0]+100 = 100. Not less than newDist[1]=100. Skip.
  (1,2,100): dist[1]+100 = 200 < 500. newDist[2] = 200.
  (0,2,500): dist[0]+500 = 500. Not less. Skip.
dist = [0, 100, 200].
```

dist[2] = **200**. ✓ (Uses 2 flights = 1 stop.)

Compare: if we'd updated in place, pass 1 would have set dist[1] = 100 and then in the same pass used that to set dist[2] = 200 via edge (1, 2). That would give 200 even for K=0 — wrong.

----------------------------------------

## Step 7: Why the Copy Enforces "One Hop Per Pass"

The invariant is: after pass `i`, `dist[c]` = cheapest path to c using **at most i** edges.

To preserve this invariant, each relaxation in pass i must use only `dist[u]` from **before** this pass (which represents i-1 edges) and produce a path of i edges by adding one more.

Reading from a snapshot (`dist`) and writing to a separate buffer (`newDist`) guarantees that within a pass, no path gets counted with more edges than the pass number allows.

----------------------------------------

## Step 8: Name It

This is **layered Bellman-Ford** or **shortest path with edge-count constraint**. Same pattern applies to:
- Walks of exactly k steps in a graph.
- k-hop network reachability.
- Flights/routes with layover constraints.

A Dijkstra variant also works — use state (cost, city, stops_used) in the priority queue — but the Bellman-Ford version is cleaner for this problem.

----------------------------------------

## Step 9: Complexity

Time: **O((K+1) · E)**. Each of K+1 passes processes all edges in O(E).
Space: **O(n)** for the two distance arrays (copy).

For typical K (small), this is fast.

----------------------------------------

## Step 10: C++ Implementation

```cpp
int findCheapestPrice(int n, vector<vector<int>>& flights, int src, int dst, int K) {
    const int INF = INT_MAX;
    vector<int> dist(n, INF);
    dist[src] = 0;

    for (int i = 0; i <= K; ++i) {
        vector<int> newDist = dist;   // snapshot
        for (auto& f : flights) {
            int u = f[0], v = f[1], w = f[2];
            if (dist[u] == INF) continue;   // u unreachable so far
            if (dist[u] + w < newDist[v]) {
                newDist[v] = dist[u] + w;
            }
        }
        dist = newDist;
    }

    return dist[dst] == INF ? -1 : dist[dst];
}
```

Three critical details:
- `newDist = dist` at the top of each pass — the snapshot.
- Skip relaxation if `dist[u] == INF` to prevent overflow.
- Run the loop `K + 1` times (K stops means up to K+1 flights).

----------------------------------------

## Step 11: Follow-up Questions

- **Return the actual route (list of cities), not just the price.** Track parent pointers in the DP; reconstruct by walking back.
- **Count cheapest routes (multiple minima).** Track `(min_cost, count)` per city.
- **Unbounded stops.** Standard Dijkstra works.
- **Negative-weight edges.** Dijkstra fails; Bellman-Ford naturally handles (our algorithm already uses Bellman-Ford).
- **Multiple sources.** Seed the algorithm with `dist[s] = 0` for each source.
- **Can we use Dijkstra with extended state (cost, stops)?** Yes — priority queue on (cost, city, stops). It can be faster in practice when solutions are found early. But Bellman-Ford is cleaner to implement and analyze for this problem.
