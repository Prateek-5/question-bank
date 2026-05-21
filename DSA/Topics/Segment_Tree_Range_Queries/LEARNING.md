# Segment Tree & Range Queries — Learning Path

> **Stage:** Advanced   |   **Prereqs:** [1_D_and_2_D_Arrays/](../1_D_and_2_D_Arrays/LEARNING.md), [Trees_Binary_Trees/](../Trees_Binary_Trees/LEARNING.md)   |   **Problems:** 6
>
> Beyond prefix sum: when you need both **fast range queries AND fast point updates**, you need a segment tree.

---

## How to study this topic

Strict difficulty order:

1. Prefix sum (no updates) — warm-up.
2. Segment tree for sum (point update + range query).
3. Range max (the other classic operation).
4. Lazy propagation (the hard one — range update + range query).

---

## Problems in study order

### Warm-up — prefix sum (no updates needed)

1. **[Range_Sum_Query_Immutable.md](./Range_Sum_Query_Immutable.md)** — Prefix-sum array; range query O(1). No segment tree needed. **must-do**

### Segment tree — sum

2. **[Range_Sum_Query_Mutable.md](./Range_Sum_Query_Mutable.md)** — Segment tree (or Fenwick/BIT). Build, update, query all O(log n). **must-do**

### Segment tree — max

3. **[Range_Maximum_Query.md](./Range_Maximum_Query.md)** — Same shape; `max` instead of `sum`. **must-do**
4. **[Segment_Tree_Range_Maximum_Query_Node_Update.md](./Segment_Tree_Range_Maximum_Query_Node_Update.md)** — Companion with point updates.

### Lazy propagation

5. **[Flipping_Sign_Problem_Lazy_Propagation.md](./Flipping_Sign_Problem_Lazy_Propagation.md)** — Range flip; defer propagation. The hard one.
6. **[Flipping_Sign_Problem_Lazy_Propagation_Segment_Tree.md](./Flipping_Sign_Problem_Lazy_Propagation_Segment_Tree.md)** — Companion / variant.

---

## Patterns established

- **Prefix sum is enough** when there are no updates. Segment tree adds support for updates at O(log n) cost.
- **Segment tree shape:** Array of size `4n` (power-of-2 padded). Each node covers a range; children cover halves.
- **Build O(n), query O(log n), update O(log n).**
- **Query template:** If node's range completely inside `[l, r]`, return its value. If completely outside, return identity (0 for sum, -∞ for max). Else recurse children.
- **Lazy propagation:** Pending updates stored at nodes; pushed down on demand. Allows range updates in O(log n).
- **Fenwick / BIT** (Binary Indexed Tree) — simpler structure for prefix sums; not always taught with this folder but worth knowing.

---

## Common traps

- **Array size `4n`, not `2n`.** Safe upper bound for any input size.
- **Recursive vs iterative segment tree.** Recursive is clearer; iterative is faster but trickier with lazy.
- **Forgetting to push lazy** before recursing children in query.
- **Identity element wrong:** Sum is 0, min is +∞, max is -∞, GCD is 0, product is 1.
- **Off-by-one on ranges.** Decide once: `[l, r]` inclusive vs `[l, r)` half-open.

---

## After this topic

- **[Dynamic_Programming_DP/](../Dynamic_Programming_DP/LEARNING.md)** — DP problems sometimes use segment trees for range max/sum queries.
- **[Trie_Bit_Manipulation_Trie/](../Trie_Bit_Manipulation_Trie/LEARNING.md)** — another specialized tree structure.
- **[Sorting_Divide_and_Conquer/](../Sorting_Divide_and_Conquer/LEARNING.md)** — Count of Smaller After Self also solvable with BIT.
