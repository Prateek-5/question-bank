# Find the City With the Smallest Number of Neighbors at a Threshold Distance — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Find_the_City_With_the_Smallest_Number_of_Neighbors.md`](../Find_the_City_With_the_Smallest_Number_of_Neighbors.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/find-the-city-with-the-smallest-number-of-neighbors-at-a-threshold-distance/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. **The lesson: ALL-PAIRS SHORTEST PATHS — FLOYD-WARSHALL in O(n³) is the cleanest choice. After distances, count threshold-reachable cities and tie-break by largest index.**

**Map of this file (9 sections):**

1. Read the problem
2. The all-pairs reframe
3. Floyd-Warshall — the intermediate-vertex idea
4. Tie-breaking on the largest index
5. Code
6. Trace it
7. Why Floyd-Warshall over n × Dijkstra
8. Common pitfalls
9. The shape — all-pairs shortest paths

---

## 1. Read the problem

`n` cities (0..n-1), weighted undirected edges, integer `distanceThreshold`. For each city i, count how many OTHER cities j have `shortestDist(i, j) ≤ distanceThreshold`. Return the city with the SMALLEST such count; on ties, return the LARGEST city label.

**Example:** n=4, edges=`[[0,1,3],[1,2,1],[1,3,4],[2,3,1]]`, threshold=4.

Distances:
- 0: d(0,1)=3, d(0,2)=4, d(0,3)=5 → reachable {1, 2} → 2
- 1: d=3,1,2 → {0,2,3} → 3
- 2: d=4,1,1 → {0,1,3} → 3
- 3: d=5,2,1 → {1,2} → 2

Tie 0 and 3 both have count 2. Return larger label: **3**.

---

## 2. The all-pairs reframe

> **Mini-refresher: this is an ALL-PAIRS shortest path problem.**
>
> For each city, you need shortest distances to every other city. That's n single-source SSSPs OR one all-pairs computation.
>
> For small n (this problem ≤ 100), All-Pairs algorithms shine because they're simpler to code.

Two main choices:
- **n × Dijkstra:** O(n · (E + V log V)). Better for SPARSE graphs.
- **Floyd-Warshall:** O(n³). Better for DENSE graphs OR when simpler code matters.

For n ≤ 100, both are ~10^6 ops — both fast. Floyd-Warshall wins on simplicity.

---

## 3. Floyd-Warshall — the intermediate-vertex idea

> **Mini-refresher: Floyd-Warshall in one sentence.**
>
> Maintain `dist[i][j]` = current best i→j distance. For each k in 0..n-1 (as candidate intermediate), update every (i, j) pair:
>
> ```
> dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
> ```
>
> **Invariant:** after processing k, `dist[i][j]` is the shortest i→j path using only intermediates from `{0, 1, ..., k}`. After k=n-1, all intermediates are allowed → final answer.

The triple-nested loop with k as outer index is critical (not i, not j). The k-outer order is what makes the invariant hold.

---

## 4. Tie-breaking on the largest index

```
minCount = ∞
result = -1
for i in 0..n-1:
    count = number of j ≠ i with dist[i][j] ≤ threshold
    if count <= minCount:        # <= not <, so later (larger) i overwrites tie
        minCount = count
        result = i
return result
```

Iterating in increasing i with `<=` makes the LAST seen minimum win — i.e., the largest index among ties.

---

## 5. Code

**C++:**

```cpp
int findTheCity(int n, vector<vector<int>>& edges, int distanceThreshold) {
    const int INF = INT_MAX / 2;          // / 2 to prevent overflow on addition
    vector<vector<int>> dist(n, vector<int>(n, INF));
    for (int i = 0; i < n; ++i) dist[i][i] = 0;
    for (auto& e : edges) {
        dist[e[0]][e[1]] = e[2];
        dist[e[1]][e[0]] = e[2];          // undirected
    }

    for (int k = 0; k < n; ++k) {
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < n; ++j) {
                if (dist[i][k] + dist[k][j] < dist[i][j]) {
                    dist[i][j] = dist[i][k] + dist[k][j];
                }
            }
        }
    }

    int minCount = INT_MAX, result = -1;
    for (int i = 0; i < n; ++i) {
        int count = 0;
        for (int j = 0; j < n; ++j) {
            if (i != j && dist[i][j] <= distanceThreshold) count++;
        }
        if (count <= minCount) {
            minCount = count;
            result = i;
        }
    }
    return result;
}
```

Complexity: **O(n³)** time, **O(n²)** space.

---

## 6. Trace it

Example from section 1.

Initial dist:
```
[0, 3, ∞, ∞]
[3, 0, 1, 4]
[∞, 1, 0, 1]
[∞, 4, 1, 0]
```

**k=0:** Vertex 0 has limited connections — no improvements.

**k=1:** Vertex 1 connects 0, 2, 3:
- dist[0][2] = min(∞, 3+1) = 4
- dist[0][3] = min(∞, 3+4) = 7
- dist[2][0] = 4, dist[3][0] = 7

```
[0, 3, 4, 7]
[3, 0, 1, 4]
[4, 1, 0, 1]
[7, 4, 1, 0]
```

**k=2:** Vertex 2 enables shortcuts:
- dist[1][3] = min(4, 1+1) = 2
- dist[0][3] = min(7, 4+1) = 5
- dist[3][1] = 2, dist[3][0] = 5

```
[0, 3, 4, 5]
[3, 0, 1, 2]
[4, 1, 0, 1]
[5, 2, 1, 0]
```

**k=3:** no improvements (k=3 only opens what k=1 and k=2 already provided).

Counts at threshold=4:
- City 0: {1@3, 2@4} → 2
- City 1: {0@3, 2@1, 3@2} → 3
- City 2: {0@4, 1@1, 3@1} → 3
- City 3: {1@2, 2@1} → 2  (0@5 > 4, skip)

Minimum: 2. Tie between 0 and 3. Iterating with `<=`, the later (larger) i = 3 wins. Return **3**.  ✓

---

## 7. Why Floyd-Warshall over n × Dijkstra

| Aspect | Floyd-Warshall | n × Dijkstra |
|---|---|---|
| Time | O(n³) | O(n · (E + V log V)) |
| Space | O(n²) | O(n + E) per call, O(n²) for outputs |
| Code | ~5 lines | ~15 lines |
| Best when | Dense graph or small n | Sparse graph, large n |
| Negative weights | Handles (no negative cycles) | Fails |

For n ≤ 100 (this problem's constraint), Floyd-Warshall is the obvious winner — three nested loops, done.

---

## 8. Common pitfalls

1. **Using `INT_MAX` instead of `INT_MAX / 2`.** Adding two INT_MAX values overflows.
2. **Wrong k ordering.** k MUST be the outermost loop. Putting i or j outside breaks the invariant.
3. **Forgetting symmetric edges.** Undirected → set dist[u][v] AND dist[v][u].
4. **Initializing dist[i][i] to INF.** Self-distance is 0.
5. **Tie-breaking by index** — needs `<=`, not `<`, AND iterating from smallest to largest. Otherwise the smallest tied index wins (wrong for this problem).
6. **Counting j == i.** Don't count the city itself among its neighbors.

---

## 9. The shape — all-pairs shortest paths

The pattern: **all-pairs distances, then per-row aggregation.**

| Problem | Aggregation |
|---|---|
| **This problem** | count cities within threshold; min count |
| Cheapest Path Through Matrix | choose best per row |
| Eccentricity of a Graph | max d[i][j] per row (radius / diameter) |
| Diameter of a Graph | max over all pairs |
| Closeness Centrality | 1 / sum(d[i][j]) per row |
| Reachable in K Hops | Floyd-Warshall with edge-count, not weight |

**Pattern to internalize:**

> "All-pairs shortest paths + small n? Floyd-Warshall in O(n³) — three nested loops with k OUTERMOST. Aggregate the resulting matrix as needed."

---

> **Self-check — the question to ask next time.**
>
> When you need shortest distances from EVERY source to EVERY destination, ask:
>
> > **"Is n small (≤ 500)? Floyd-Warshall — k OUTERMOST. Then aggregate per row. Mind tie-breaking and infinity arithmetic."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Find_the_City_With_the_Smallest_Number_of_Neighbors.md`](../Find_the_City_With_the_Smallest_Number_of_Neighbors.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Network_Delay_Time.md`](./Network_Delay_Time.md), [`Cheapest_Flights_Within_K_Stops.md`](./Cheapest_Flights_Within_K_Stops.md).
  - Coming next: [`Number_of_Operations_to_Make_Network_Connected.md`](./Number_of_Operations_to_Make_Network_Connected.md), [`Redundant_Connection.md`](./Redundant_Connection.md), [`Accounts_Merge.md`](./Accounts_Merge.md).
