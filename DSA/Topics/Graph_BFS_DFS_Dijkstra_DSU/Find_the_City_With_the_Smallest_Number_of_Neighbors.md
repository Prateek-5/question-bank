# Find the City With the Smallest Number of Neighbors at a Threshold Distance

**Problem Link:**
<a href="https://leetcode.com/problems/find-the-city-with-the-smallest-number-of-neighbors-at-a-threshold-distance/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/find-the-city-with-the-smallest-number-of-neighbors-at-a-threshold-distance/</a>

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Decode the Problem

Given `n` cities (0 to n-1), a list of weighted edges, and a `distanceThreshold`, find the **city** from which you can reach the **fewest other cities** within `distanceThreshold` (via shortest paths).

If multiple cities tie, return the **largest** city label.

Example: `n = 4`, `edges = [[0,1,3], [1,2,1], [1,3,4], [2,3,1]]`, `distanceThreshold = 4`.

Shortest distances:
- From 0: to 1 = 3, to 2 = 4, to 3 = 5. Within threshold: {1, 2} → 2 cities.
- From 1: to 0 = 3, to 2 = 1, to 3 = 2. All within threshold. {0, 2, 3} → 3.
- From 2: to 0 = 4, to 1 = 1, to 3 = 1. {0, 1, 3} → 3.
- From 3: to 0 = 5, to 1 = 2, to 2 = 1. {1, 2} → 2.

Cities with fewest reachable (within threshold): cities 0 and 3, both with 2. Return the **larger label**: 3.

----------------------------------------

## Step 2: We Need All-Pairs Shortest Paths

For each city, we need shortest distances to every other city. Then count how many are within threshold.

Two main algorithms:
- **Dijkstra from every city**: O(V · (E + V log V)). For n ≤ 100, that's ~10^6 ops — fast.
- **Floyd-Warshall**: O(V³). For n ≤ 100, that's 10^6 ops too.

Both work. Floyd-Warshall is **simpler to code** and well-suited when we need all pairs.

----------------------------------------

## Step 3: Floyd-Warshall — A Brief Refresher

Maintain a matrix `dist[i][j]` = shortest distance from i to j.

Initialize: `dist[i][i] = 0`, `dist[i][j] = weight(i, j)` if edge exists, else infinity.

Iterate over intermediate vertices `k` from 0 to n-1. For each pair (i, j), relax via k: `dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])`.

After iterating all k, `dist` has all-pairs shortest paths.

Why it works: after the k-th iteration, `dist[i][j]` is the shortest i→j path using only intermediate vertices from {0, 1, ..., k}. Final answer uses any subset as intermediates.

O(V³). Short to code.

----------------------------------------

## Step 4: After All-Pairs, Count Reachable

For each city i, count j ≠ i with `dist[i][j] ≤ distanceThreshold`. That's the "neighbor count."

Find the city with minimum count; on ties, return the largest label.

```
min_count = infinity
result_city = -1

for i in 0..n-1:
    count = 0
    for j in 0..n-1:
        if j != i and dist[i][j] <= distanceThreshold:
            count += 1
    if count <= min_count:
        min_count = count
        result_city = i   # on tie, larger i overwrites earlier choice

return result_city
```

The tie-breaking logic: use `<=` and iterate in increasing order; the largest city with the minimum count overwrites earlier ties.

----------------------------------------

## Step 5: Trace on the Example

n = 4. Initialize dist:

```
dist = [
  [0, 3, ∞, ∞],
  [3, 0, 1, 4],
  [∞, 1, 0, 1],
  [∞, 4, 1, 0]
]
```

(Edges are undirected, so set both directions.)

Floyd-Warshall iterations (k=0, 1, 2, 3):

**k = 0:** can we go through vertex 0? Most pairs can't improve (no edges 0-2 or 0-3 directly beyond infinity). dist unchanged in most cells.

**k = 1:** vertex 1 connects {0, 2, 3}.
- dist[0][2] = min(∞, dist[0][1] + dist[1][2]) = min(∞, 3 + 1) = 4.
- dist[0][3] = min(∞, 3 + 4) = 7.
- dist[2][0] = 4 (symmetric).
- dist[2][3] = min(1, 1 + 4) = 1. (Already 1.)
- dist[3][0] = 7.
- dist[3][2] = 1.

```
dist = [
  [0, 3, 4, 7],
  [3, 0, 1, 4],
  [4, 1, 0, 1],
  [7, 4, 1, 0]
]
```

**k = 2:** vertex 2 connects {1, 3} strongly.
- dist[1][3] = min(4, dist[1][2] + dist[2][3]) = min(4, 1 + 1) = 2.
- dist[0][3] = min(7, dist[0][2] + dist[2][3]) = min(7, 4 + 1) = 5.
- dist[3][1] = 2. dist[3][0] = 5.

```
dist = [
  [0, 3, 4, 5],
  [3, 0, 1, 2],
  [4, 1, 0, 1],
  [5, 2, 1, 0]
]
```

**k = 3:** no improvements (k=3 only connects via {1, 2} edges, all already found).

Now count neighbors within threshold = 4:

- City 0: d(0,1)=3 ✓, d(0,2)=4 ✓, d(0,3)=5 ✗. Count = 2.
- City 1: d(1,0)=3 ✓, d(1,2)=1 ✓, d(1,3)=2 ✓. Count = 3.
- City 2: d(2,0)=4 ✓, d(2,1)=1 ✓, d(2,3)=1 ✓. Count = 3.
- City 3: d(3,0)=5 ✗, d(3,1)=2 ✓, d(3,2)=1 ✓. Count = 2.

Tie: cities 0 and 3 both have 2. Return the largest: **3**. ✓

----------------------------------------

## Step 6: Name It

**All-Pairs Shortest Paths via Floyd-Warshall + post-processing**. For this problem size (n ≤ 100), Floyd-Warshall's O(n³) is fast enough and very code-friendly.

Dijkstra from each source is also valid and scales better for sparse large graphs (when E is much less than V²).

----------------------------------------

## Step 7: Complexity

Floyd-Warshall: **O(n³)**.
Post-processing (counting): O(n²).
Total: **O(n³)**.
Space: **O(n²)** for dist matrix.

For n ≤ 100, ~10^6 ops. Fast.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int findTheCity(int n, vector<vector<int>>& edges, int distanceThreshold) {
    const int INF = INT_MAX / 2;   // avoid overflow when adding
    vector<vector<int>> dist(n, vector<int>(n, INF));
    for (int i = 0; i < n; ++i) dist[i][i] = 0;
    for (auto& e : edges) {
        dist[e[0]][e[1]] = e[2];
        dist[e[1]][e[0]] = e[2];   // undirected
    }

    // Floyd-Warshall
    for (int k = 0; k < n; ++k) {
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < n; ++j) {
                if (dist[i][k] + dist[k][j] < dist[i][j]) {
                    dist[i][j] = dist[i][k] + dist[k][j];
                }
            }
        }
    }

    int minCount = INT_MAX;
    int result = -1;
    for (int i = 0; i < n; ++i) {
        int count = 0;
        for (int j = 0; j < n; ++j) {
            if (i != j && dist[i][j] <= distanceThreshold) count++;
        }
        if (count <= minCount) {
            minCount = count;
            result = i;   // on tie, larger i wins
        }
    }
    return result;
}
```

Using `INT_MAX / 2` as INF prevents overflow during `dist[i][k] + dist[k][j]`.

----------------------------------------

## Step 9: Follow-up Questions

- **With n = 10^5.** Floyd-Warshall infeasible. Dijkstra from each source: O(V · (E + V log V)) — might still be slow if E is dense.
- **Very sparse graph.** Dijkstra from each source wins.
- **Online queries (threshold changes).** Precompute all-pairs once. Each query O(n²).
- **Return the actual reachable city list, not just count.** Track during post-processing.
- **Weighted vertices (not just edges).** Adjust the Floyd-Warshall update.
- **Why Floyd-Warshall instead of n × Dijkstra for small n?** Simpler code. Same asymptotic for dense graphs.
