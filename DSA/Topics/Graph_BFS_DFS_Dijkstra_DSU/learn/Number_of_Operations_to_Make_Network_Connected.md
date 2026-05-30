# Number of Operations to Make Network Connected — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Number_of_Operations_to_Make_Network_Connected.md`](../Number_of_Operations_to_Make_Network_Connected.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/number-of-operations-to-make-network-connected/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/number-of-operations-to-make-network-connected/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: the answer is `(number of components) - 1`, provided we have enough cables (≥ n - 1). Each "operation" moves a redundant cable to bridge two components.**

**Map of this file (8 sections):**

1. Read the problem
2. The minimum-cable threshold
3. Count components → operations
4. Why we always have enough redundant cables
5. Code (DFS + DSU)
6. Trace it
7. Common pitfalls
8. The shape — counting components

---

## 1. Read the problem

`n` computers labeled 0..n-1; cables `connections[i] = [a, b]` directly link a and b. One "operation" = unplug a cable from one pair and plug it between any other pair. Make all computers connected with the FEWEST operations, or return -1 if impossible.

**Example:** `n = 4, connections = [[0,1], [0,2], [1,2]]`.

Computers 0, 1, 2 form a triangle. Computer 3 is isolated. 4 cables total? No — only 3 cables. Need at least n-1 = 3. We have exactly 3. The 0-1-2 triangle has a REDUNDANT edge — we can detach it and reconnect to 3.

Answer: **1**.

---

## 2. The minimum-cable threshold

> **Mini-refresher: connecting n nodes requires AT LEAST n - 1 cables.**
>
> A spanning TREE on n nodes uses exactly n - 1 edges. If you have FEWER cables than n - 1, no rearrangement can connect everything.
>
> First check: `if len(connections) < n - 1: return -1`.

This is the only "impossible" case.

---

## 3. Count components → operations

> **Mini-refresher: c components → c - 1 operations to merge.**
>
> Each operation bridges two components into one — reduces the component count by 1.
>
> Starting at c components, we need c - 1 operations to reach 1 component.

So the algorithm is:
1. If `len(connections) < n - 1`: return -1.
2. Count connected components → c.
3. Return c - 1.

---

## 4. Why we always have enough redundant cables

You might worry: "What if an operation needs a 'spare' cable, but every cable is essential (part of its component's spanning tree)?"

It can't happen. Here's why:

- A spanning forest on c components needs `n - c` edges (each component's spanning tree).
- We have `m ≥ n - 1` total cables.
- Redundant cables (in cycles) = `m - (n - c) = m - n + c`.
- Plugging in m ≥ n - 1: redundant ≥ `(n - 1) - n + c = c - 1`.

So we always have AT LEAST `c - 1` redundant cables — exactly what we need.

> **Mini-refresher: cycle rank = redundant edges.**
>
> The number of "extra" edges beyond a spanning forest is exactly the cycle rank. It measures how connected the graph already is, beyond the bare minimum.

---

## 5. Code (DFS + DSU)

**C++ — DFS version:**

```cpp
int makeConnected(int n, vector<vector<int>>& connections) {
    if ((int)connections.size() < n - 1) return -1;

    vector<vector<int>> adj(n);
    for (auto& e : connections) {
        adj[e[0]].push_back(e[1]);
        adj[e[1]].push_back(e[0]);
    }

    vector<bool> visited(n, false);
    function<void(int)> dfs = [&](int u) {
        visited[u] = true;
        for (int v : adj[u]) if (!visited[v]) dfs(v);
    };

    int components = 0;
    for (int u = 0; u < n; ++u) {
        if (!visited[u]) {
            dfs(u);
            components++;
        }
    }
    return components - 1;
}
```

**C++ — DSU version:**

```cpp
struct DSU {
    vector<int> p, r;
    DSU(int n) : p(n), r(n, 0) { iota(p.begin(), p.end(), 0); }
    int find(int x) { return p[x] == x ? x : p[x] = find(p[x]); }
    void unite(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return;
        if (r[a] < r[b]) swap(a, b);
        p[b] = a;
        if (r[a] == r[b]) r[a]++;
    }
};

int makeConnected(int n, vector<vector<int>>& connections) {
    if ((int)connections.size() < n - 1) return -1;
    DSU dsu(n);
    for (auto& e : connections) dsu.unite(e[0], e[1]);
    int components = 0;
    for (int u = 0; u < n; ++u) if (dsu.find(u) == u) components++;
    return components - 1;
}
```

Complexity: **O(n + m · α(n))** with DSU. **O(n + m)** with DFS.

---

## 6. Trace it

**`n = 6, connections = [[0,1], [0,2], [0,3], [1,2], [1,3]]`:**

5 cables ≥ n - 1 = 5. OK.

DFS:
- From 0: visit {0, 1, 2, 3}. components = 1.
- From 4 (unvisited): visit {4}. components = 2.
- From 5 (unvisited): visit {5}. components = 3.

Return 3 - 1 = **2**.

Verify: with 5 cables and 3 components, redundant = 5 - (6 - 3) = 2. We have exactly 2 redundant cables — enough to bridge the 3 components into 1 with 2 operations.

---

## 7. Common pitfalls

1. **Off-by-one on the threshold.** Need ≥ n - 1 cables, not ≥ n.
2. **Returning `c` instead of `c - 1`.** Merging c components takes c - 1 operations.
3. **Not initializing DSU sizes properly.** `iota(p.begin(), p.end(), 0)` sets parent[i] = i.
4. **Counting components by visited cells only (in DSU).** Count `dsu.find(u) == u` (self-root). Or maintain a component counter.
5. **Treating directed edges.** Cables are undirected — push both directions in the adjacency list.
6. **Returning -1 when it's possible.** Only return -1 if cable count is below n - 1.

---

## 8. The shape — counting components

The pattern: **count connected components and derive the answer.**

| Problem | Component-based answer |
|---|---|
| **This problem** | c - 1 operations |
| Number of Provinces | c itself |
| Friend Circles | c itself |
| Number of Connected Components in an Undirected Graph | c itself |
| Graph Valid Tree | "c == 1 AND no cycle" |
| Redundant Connection | the edge that causes c to NOT decrease |

**Pattern to internalize:**

> "When an operation merges components, the cost to fully connect is `c - 1`. Feasibility check: do you have enough edges (n - 1)?"

---

> **Self-check — the question to ask next time.**
>
> When the problem says "move cables to connect everything," ask:
>
> > **"Do I have at least n - 1 cables? If yes, count components; return c - 1."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Number_of_Operations_to_Make_Network_Connected.md`](../Number_of_Operations_to_Make_Network_Connected.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Number_of_Provinces.md`](./Number_of_Provinces.md), [`Number_of_Islands.md`](./Number_of_Islands.md), [`Check_if_There_Is_a_Valid_Path_in_a_Graph.md`](./Check_if_There_Is_a_Valid_Path_in_a_Graph.md).
  - Coming next: [`Redundant_Connection.md`](./Redundant_Connection.md), [`Accounts_Merge.md`](./Accounts_Merge.md), [`Most_Stones_Removed_with_Same_Row_or_Column.md`](./Most_Stones_Removed_with_Same_Row_or_Column.md).
