# Most Stones Removed with Same Row or Column

**Problem Link:**
https://leetcode.com/problems/most-stones-removed-with-same-row-or-column/

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Read the Problem

Stones are placed on a 2D plane. You can remove a stone if it **shares a row or column with at least one other stone** that's still on the plane.

Return the **maximum number of stones** you can remove.

Example: `stones = [[0,0], [0,1], [1,0], [1,2], [2,1], [2,2]]`.

Six stones. Let's see which we can remove:
- (0, 0) shares row with (0, 1). Remove it.
- (2, 2) shares row with (2, 1). Remove it.
- (0, 1) shares column with (2, 1). Remove it.
- (1, 0) shares row with (1, 2). Remove it.
- (1, 2) shares column with (2, 2)? But (2, 2) was removed. Check against remaining: (2, 1). Same column? col 2 vs col 1. No. Same row? row 1 vs row 2. No. Can't remove unless we remove in different order.

Let's try:
- (1, 2) shares col with (0, 2)? Not in list. Shares row with (1, 0). Remove (1, 2).
- (2, 1) shares col with (0, 1). Remove.
- (0, 0), (0, 1), (1, 0), (2, 2) remain.
- (0, 0) and (0, 1): same row. Remove (0, 0).
- (0, 1), (1, 0), (2, 2): no pair shares row/col... wait, (0, 1) and (2, 1)? (2, 1) is already removed. (1, 0) and (0, 0)? (0, 0) removed. 

This is getting fiddly. The answer is 5. Expected: we remove 5 stones, leaving 1.

----------------------------------------

## Step 2: The Big-Picture Claim

**Claim:** the maximum number of removable stones = total stones - number of **connected components**.

Where "connected" means: two stones are in the same component iff they share a row OR column (directly or transitively).

Why? In each component of k stones, we can always remove k - 1 of them (leaving just 1). Total removals = n - number_of_components.

----------------------------------------

## Step 3: Proving the Claim

**Upper bound:** In each component, at least one stone must remain (once we've removed everything but one, the last one has nothing to share with). So at most (size of component) − 1 removals per component.

**Lower bound:** For each component, we can achieve (size − 1) removals. Take any spanning tree of the component's "row/column-shared" graph. Remove leaves of the tree (always valid because a leaf still has its neighbor). Continue until one stone remains.

More concretely: pick any stone as a "keep", then repeatedly remove stones connected to already-present stones (each removal maintains the connectivity with the kept stone). Since every stone in the component is reachable from the kept one, we can order removals so each remains valid.

Hence, (component size) − 1 removals per component. Summing: n − components.

----------------------------------------

## Step 4: Counting Components with Union-Find

We need to group stones by "share row or column." Two stones share a row ↔ they have the same row coordinate. Same for column.

Use **Union-Find** with a trick: for each stone (r, c), we union it with:
- All other stones in row r.
- All other stones in column c.

But iterating for each stone over all other stones is O(n²). Instead, union the stone's (r, c) with a virtual node representing "row r" and another for "column c." All stones in row r get unioned with the same "row r" virtual node, so they end up in the same component.

**Encoding:**
- Stones labeled 0..n-1 directly.
- Virtual row node for row r: labeled `n + r`.
- Virtual column node for col c: labeled `n + maxRow + c` (offset to avoid collisions).

Or more simply: encode row r as `row_r` (some unique ID) and column c as `col_c`. In a hashmap DSU, these can be strings or offsets.

Each stone i at (r, c): `union(i, row_r)` and `union(i, col_c)`.

At the end, count distinct roots among stones 0..n-1. That's the component count. Answer = n - components.

----------------------------------------

## Step 5: A Cleaner Encoding

Since rows and columns are ≤ 10^4, we can offset:
- Union(stone_index, row + 0).
- Union(stone_index, col + 10001). (Offset by something bigger than max row.)

Wait, stone_index is in [0, n). If n ≤ 1000 and rows ≤ 10000, we have collisions. Let me be more careful.

Simplest approach: don't union stones with virtual nodes at all. Instead, maintain two hashmaps `rowToFirstStone` and `colToFirstStone`. For each stone i at (r, c):
- If rowToFirstStone has r, union(i, rowToFirstStone[r]). Else, set rowToFirstStone[r] = i.
- Same for col.

This way, all stones in row r get unioned with the first stone in row r, transitively connecting them all.

```
DSU over stones 0..n-1.
rowMap = {}, colMap = {}

for i in 0..n-1:
    (r, c) = stones[i]
    if r in rowMap: union(i, rowMap[r])
    else: rowMap[r] = i
    if c in colMap: union(i, colMap[c])
    else: colMap[c] = i

components = count of distinct find(i) for i in 0..n-1
return n - components
```

Clean, no virtual nodes needed.

----------------------------------------

## Step 6: Trace

`stones = [[0,0], [0,1], [1,0], [1,2], [2,1], [2,2]]`.

```
DSU initial: each stone its own component (6 components).
rowMap = {}, colMap = {}.

i=0 (0, 0): row 0 not in rowMap, rowMap[0]=0. col 0 not in colMap, colMap[0]=0.
i=1 (0, 1): rowMap[0]=0. union(1, 0). Now {0, 1} one component. colMap[1]=1.
i=2 (1, 0): rowMap[1]=2. colMap[0]=0. union(2, 0). Now {0, 1, 2} one component.
i=3 (1, 2): rowMap[1]=2. union(3, 2). Now {0, 1, 2, 3} one component. colMap[2]=3.
i=4 (2, 1): rowMap[2]=4. colMap[1]=1. union(4, 1). Now {0, 1, 2, 3, 4} one component.
i=5 (2, 2): rowMap[2]=4. union(5, 4). Now {0, 1, 2, 3, 4, 5} one component. colMap[2]=3. union(5, 3). Still same component.

Components = 1.
Answer = 6 - 1 = 5.
```

✓ Matches expected.

----------------------------------------

## Step 7: Name It

**Union-Find on a connectivity-by-shared-attribute graph.** We treat "sharing a row" and "sharing a column" as separate types of edges, but DSU doesn't care about edge types — it just merges components.

The clever bit: using a **hashmap to map each row/column to its first-seen stone** avoids O(n²) pairwise unions.

The general formula "n − components = max removable (or equivalent)" is a common shape in DSU problems where each component's contribution is one less than its size.

----------------------------------------

## Step 8: Complexity

Time: **O(n α(n))** — n unions, each α(n) amortized.
Space: **O(n)** for DSU + row/col maps.

----------------------------------------

## Step 9: C++ Implementation

```cpp
class DSU {
    vector<int> parent;
public:
    DSU(int n) : parent(n) { iota(parent.begin(), parent.end(), 0); }
    int find(int x) {
        return parent[x] == x ? x : parent[x] = find(parent[x]);
    }
    void unite(int a, int b) {
        int ra = find(a), rb = find(b);
        if (ra != rb) parent[ra] = rb;
    }
};

int removeStones(vector<vector<int>>& stones) {
    int n = stones.size();
    DSU dsu(n);
    unordered_map<int, int> rowMap, colMap;

    for (int i = 0; i < n; ++i) {
        int r = stones[i][0], c = stones[i][1];
        if (rowMap.count(r)) dsu.unite(i, rowMap[r]);
        else rowMap[r] = i;
        if (colMap.count(c)) dsu.unite(i, colMap[c]);
        else colMap[c] = i;
    }

    unordered_set<int> roots;
    for (int i = 0; i < n; ++i) roots.insert(dsu.find(i));
    return n - roots.size();
}
```

----------------------------------------

## Step 10: Follow-up Questions

- **Find an optimal order of removal.** More involved — construct spanning trees of each component, remove in post-order (leaves first).
- **Stones in 3D or higher.** Extend: share any coordinate → connected.
- **Maximum stones kept (instead of removed).** The complement: answer is the number of components.
- **Streaming stones.** DSU handles this online — each new stone adds at most two unions.
- **Why count components via `n - components`?** Each component contributes (size − 1) removals. Sum is n − (number of components).
- **DFS/BFS alternative.** Build the graph explicitly (stones as nodes, row/col-share as edges), run connected-component count. Works but more verbose.
