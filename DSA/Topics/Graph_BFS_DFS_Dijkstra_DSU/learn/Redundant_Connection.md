# Redundant Connection — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Redundant_Connection.md`](../Redundant_Connection.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/redundant-connection/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: an edge creates a cycle IFF its two endpoints are already connected. UNION-FIND answers "already connected?" in α(n) per query — scan edges left-to-right, return the first whose endpoints share a root.**

**Map of this file (9 sections):**

1. Read the problem
2. The cycle-detection insight
3. Why left-to-right returns the right answer
4. Union-Find refresher
5. Code
6. Trace it
7. Why DSU beats per-edge DFS
8. Common pitfalls
9. The shape — incremental connectivity

---

## 1. Read the problem

You're given an edge list that USED to be a TREE on n nodes (n-1 edges, no cycles, connected). Someone ADDED ONE EXTRA edge — now there are n edges and exactly one cycle.

Find the edge that was added. If multiple cycle edges qualify, return the one that appears LAST in the input.

**Example:** `edges = [[1,2], [1,3], [2,3]]`. Triangle 1-2-3. Return `[2, 3]` (last in input).

---

## 2. The cycle-detection insight

> **Mini-refresher: an edge creates a cycle iff its endpoints are already connected.**
>
> Adding edge (u, v) creates a cycle ⇔ u and v are in the same connected component BEFORE adding it. (There's already a path u → ... → v; the new edge closes it into a cycle.)
>
> So: scan edges in input order, maintaining connectivity. The first edge whose endpoints are already connected is the redundant one.

---

## 3. Why left-to-right returns the right answer

The original tree had no cycles. The added edge is the unique cycle-creator. When we scan in input order:

- Every edge BEFORE the added one is a tree edge — it connects two previously-disconnected components.
- The added edge is the ONLY one whose endpoints are already connected when we reach it.

If the input order doesn't reflect the addition order (and multiple edges could equally be "the redundant one"), the problem disambiguates by saying "last in input" — and indeed, scanning left-to-right finds exactly that edge.

---

## 4. Union-Find refresher

> **Mini-refresher: Disjoint Set Union (DSU) with path compression + union-by-rank.**
>
> Each node has a parent; following parents reaches a root. Two nodes are in the same component iff they share a root.
>
> - **find(x)**: walk parents to root, compressing the path (set every node on the way to point directly at root).
> - **unite(u, v)**: find roots of u, v. If same, no-op (and signal "already connected"). Otherwise attach the smaller tree under the larger (union-by-rank).
>
> With both optimizations, any sequence of m operations runs in O(m · α(n)) — α is the inverse Ackermann function, ≤ 4 for any practical n.

---

## 5. Code

**C++:**

```cpp
class DSU {
    vector<int> parent, rnk;
public:
    DSU(int n) : parent(n + 1), rnk(n + 1, 0) {
        iota(parent.begin(), parent.end(), 0);
    }
    int find(int x) {
        if (parent[x] != x) parent[x] = find(parent[x]);
        return parent[x];
    }
    bool unite(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return false;        // already connected
        if (rnk[a] < rnk[b]) swap(a, b);
        parent[b] = a;
        if (rnk[a] == rnk[b]) rnk[a]++;
        return true;
    }
};

vector<int> findRedundantConnection(vector<vector<int>>& edges) {
    DSU dsu(edges.size());
    for (auto& e : edges) {
        if (!dsu.unite(e[0], e[1])) return e;
    }
    return {};
}
```

Complexity: **O(n · α(n))** time (effectively linear), **O(n)** space.

---

## 6. Trace it

`edges = [[1,2], [1,3], [2,3]]`.

```
Init: parent = [_, 1, 2, 3].

Edge [1, 2]: find(1)=1, find(2)=2. Different. Unite → parent[2]=1.
Edge [1, 3]: find(1)=1, find(3)=3. Different. Unite → parent[3]=1.
Edge [2, 3]: find(2)=1 (via path compression), find(3)=1. SAME. Return [2, 3].  ✓
```

The third edge connects two nodes already linked through 1 → cycle.

---

## 7. Why DSU beats per-edge DFS

**Alternative:** for each new edge (u, v), BFS/DFS from u in the so-far-built graph to check if v is reachable. O(V + E) per edge → O(n²) total.

**DSU:** O(α(n)) per edge → O(n · α(n)) total. Effectively linear.

For large n, the difference is huge. And DSU code is shorter.

---

## 8. Common pitfalls

1. **Returning the wrong edge in a cycle.** Cycle has multiple edges; the problem wants the LAST in input. Returning on the first cycle-detection naturally yields this.
2. **Off-by-one DSU sizing.** Nodes are 1-indexed in the input (1..n). Size your DSU as n+1 (or map to 0-indexed).
3. **Forgetting path compression.** Without it, find can degrade to O(n) per call — total O(n²).
4. **Calling unite even when same-root.** Wastes a write; my `unite` returns false to signal this.
5. **Treating edges as directed.** This is undirected — unite both endpoints symmetrically.

---

## 9. The shape — incremental connectivity

The pattern: **edges arrive one at a time; answer connectivity / detect cycles fast.**

| Problem | Question |
|---|---|
| **This problem** | which edge creates the cycle? |
| Kruskal's MST | skip edges that create cycles |
| Number of Connected Components | count distinct roots |
| Friend Circles | same as above |
| Graph Valid Tree | n-1 edges + no cycle + connected |
| Most Stones Removed | components on shared row/col |
| Accounts Merge | merge sets sharing emails |

**Pattern to internalize:**

> "Incremental edges + cycle detection = DSU. The `unite` return value (true/false) is the cycle signal."

---

> **Self-check — the question to ask next time.**
>
> When edges come one at a time and you need to detect when one creates a cycle, ask:
>
> > **"Can DSU's `unite` return false (same root) here? That's my cycle signal."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Redundant_Connection.md`](../Redundant_Connection.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Number_of_Operations_to_Make_Network_Connected.md`](./Number_of_Operations_to_Make_Network_Connected.md), [`Check_if_There_Is_a_Valid_Path_in_a_Graph.md`](./Check_if_There_Is_a_Valid_Path_in_a_Graph.md).
  - Coming next: [`Accounts_Merge.md`](./Accounts_Merge.md), [`Most_Stones_Removed_with_Same_Row_or_Column.md`](./Most_Stones_Removed_with_Same_Row_or_Column.md), [`Satisfiability_of_Equality_Equations.md`](./Satisfiability_of_Equality_Equations.md).
