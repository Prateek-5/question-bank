# Most Stones Removed with Same Row or Column — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Most_Stones_Removed_with_Same_Row_or_Column.md`](../Most_Stones_Removed_with_Same_Row_or_Column.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/most-stones-removed-with-same-row-or-column/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: max removable = n - (number of components), where components group stones connected via shared row/column. Use DSU with HASHMAPS that link each row/column to its first-seen stone.**

**Map of this file (9 sections):**

1. Read the problem
2. The component-counting claim
3. Why the claim holds
4. Avoiding O(n²) pairwise unions
5. Code
6. Trace it
7. Common pitfalls
8. The shape — components on shared attributes
9. Self-check

---

## 1. Read the problem

Stones on a 2D plane. A stone is REMOVABLE if it shares a row OR column with at least one other stone still on the plane. Return the max number of stones you can remove.

**Example:** `stones = [[0,0], [0,1], [1,0], [1,2], [2,1], [2,2]]` → answer **5** (remove 5, leave 1).

---

## 2. The component-counting claim

> **Mini-refresher: max removable = n - (components).**
>
> Define: two stones are CONNECTED iff they share a row or column (directly or transitively).
>
> Group stones into connected components by this relation. In each component of size k, you can remove exactly k - 1 stones (must leave 1).
>
> Total removable = Σ (size_i - 1) = n - (number of components).

So the entire problem reduces to: **count connected components, return n - components.**

---

## 3. Why the claim holds

**Upper bound (can't remove more than k - 1 per component):** the last remaining stone in a component has nothing to share with — it can't be removed. So at least one stone survives per component.

**Lower bound (can always remove k - 1):** any spanning tree of the component lets us peel leaves one by one. Each leaf-removal is safe because its parent neighbor (sharing a row or col) is still on the plane. Keep peeling until one stone remains.

So per component: exactly k - 1 removals are achievable.

---

## 4. Avoiding O(n²) pairwise unions

Naive: for each stone, scan all others sharing row or col and union. O(n²).

> **Mini-refresher: link each row/col to its FIRST-SEEN stone.**
>
> Maintain hashmaps `rowMap: row → stone_idx` and `colMap: col → stone_idx`. When processing stone i at (r, c):
> - If row r seen before: union i with rowMap[r]. Else: rowMap[r] = i.
> - Same for col c.
>
> All stones in the same row transitively unite with the first stone in that row. Similarly for columns. O(n · α(n)) total.

---

## 5. Code

**C++:**

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
    return n - (int)roots.size();
}
```

Complexity: **O(n · α(n))** time, **O(n)** space.

---

## 6. Trace it

`stones = [[0,0], [0,1], [1,0], [1,2], [2,1], [2,2]]`.

```
DSU init: 6 separate components.

i=0 (0,0): rowMap[0] = 0. colMap[0] = 0.
i=1 (0,1): rowMap[0]=0 → union(1, 0). colMap[1] = 1.
i=2 (1,0): rowMap[1]=2. colMap[0]=0 → union(2, 0).
i=3 (1,2): rowMap[1]=2 → union(3, 2). colMap[2] = 3.
i=4 (2,1): rowMap[2]=4. colMap[1]=1 → union(4, 1).
i=5 (2,2): rowMap[2]=4 → union(5, 4). colMap[2]=3 → union(5, 3).

All stones unite into ONE component.
roots = {single root}. Size = 1.
Return 6 - 1 = 5.  ✓
```

---

## 7. Common pitfalls

1. **Confusing rows with column INDICES in DSU.** Rows and cols are coordinates, not DSU IDs. Use hashmaps to map them to stone indices, not directly to DSU.
2. **Using stone coordinates as DSU IDs directly.** If you do `union(r, c)` over coords, collisions and bizarre groupings happen. Use stone-INDEX-based DSU instead.
3. **Trying every pair of stones.** O(n²) — works for small inputs but breaks at scale.
4. **Counting components by iterating only `i == parent[i]`.** After path compression, that's correct, but iterating all i and inserting `find(i)` into a set is foolproof.
5. **Off-by-one with the "+1 stone remains" claim.** Each component contributes (size - 1) removals; the formula is n - components, not n - components - 1.

---

## 8. The shape — components on shared attributes

The pattern: **count components defined by SHARED ATTRIBUTES, then derive n - components.**

| Problem | Shared attribute |
|---|---|
| **This problem** | row or column |
| Accounts Merge | shared email |
| Number of Operations to Make Network Connected | shared component |
| Friend Circles | direct friendship (transitive) |
| Couples Holding Hands | seating-row pairing |
| Number of Islands | adjacent land cells |

**Pattern to internalize:**

> "For each attribute (row, col, email...), link items sharing it via DSU using a hashmap. Then count distinct roots."

---

## 9. Self-check

> **The question to ask next time:**
>
> > **"Is the answer some function of `n - components`? Are items grouped by sharing an attribute? Use DSU with hashmap-of-first-seen per attribute."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Most_Stones_Removed_with_Same_Row_or_Column.md`](../Most_Stones_Removed_with_Same_Row_or_Column.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Redundant_Connection.md`](./Redundant_Connection.md), [`Accounts_Merge.md`](./Accounts_Merge.md), [`Number_of_Operations_to_Make_Network_Connected.md`](./Number_of_Operations_to_Make_Network_Connected.md).
  - Coming next: [`Satisfiability_of_Equality_Equations.md`](./Satisfiability_of_Equality_Equations.md), [`Knight_Probability_in_Chessboard.md`](./Knight_Probability_in_Chessboard.md).
