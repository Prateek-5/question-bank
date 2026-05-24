# Trees / Binary Trees — Learning Path

> **Stage:** Trees & Graphs   |   **Prereqs:** [Recursion/](../Recursion/LEARNING.md)   |   **Problems:** 15
>
> All tree problems are some combination of traversal + per-node state. Master the four traversals first; everything else is variations on them.
>
> **Two-tier format:** each problem has a **reference card** (linked first below) AND a paced **teaching walkthrough** in [`learn/`](./learn/) for first-time learners.

---

## How to study this topic

1. Four traversals (recursive first, then iterative).
2. Height / structural properties.
3. Single-node ops.
4. Path-sum family (light → heavy).
5. Tree construction.

---

## Problems in study order

### Traversals — the foundation

1. **[Binary_Tree_Preorder_Traversal.md](./Binary_Tree_Preorder_Traversal.md)**  ·  [walkthrough →](./learn/Binary_Tree_Preorder_Traversal.md) — Visit, left, right. **must-do**
2. **[Binary_Tree_Inorder_Traversal.md](./Binary_Tree_Inorder_Traversal.md)**  ·  [walkthrough →](./learn/Binary_Tree_Inorder_Traversal.md) — Left, visit, right. Sorted on BSTs. **must-do**
3. **[Binary_Tree_Postorder_Traversal.md](./Binary_Tree_Postorder_Traversal.md)**  ·  [walkthrough →](./learn/Binary_Tree_Postorder_Traversal.md) — Left, right, visit. **must-do**
4. **[Binary_Tree_Inorder_Traversal_Iterative.md](./Binary_Tree_Inorder_Traversal_Iterative.md)**  ·  [walkthrough →](./learn/Binary_Tree_Inorder_Traversal_Iterative.md) — Explicit stack; the "leftmost-first" pattern. **must-do**
5. **[Binary_Tree_Level_Order_Traversal.md](./Binary_Tree_Level_Order_Traversal.md)**  ·  [walkthrough →](./learn/Binary_Tree_Level_Order_Traversal.md) — BFS with queue; snapshot per level. **must-do**

### Structural / property

6. **[Maximum_Depth_of_Binary_Tree.md](./Maximum_Depth_of_Binary_Tree.md)**  ·  [walkthrough →](./learn/Maximum_Depth_of_Binary_Tree.md) — `1 + max(left, right)`. **must-do**
7. **[Balanced_Binary_Tree.md](./Balanced_Binary_Tree.md)**  ·  [walkthrough →](./learn/Balanced_Binary_Tree.md) — Post-order returns height OR `-1` if unbalanced. The "encode invalid as -1" trick. **must-do**

### Single-node ops

8. **[Invert_Binary_Tree.md](./Invert_Binary_Tree.md)**  ·  [walkthrough →](./learn/Invert_Binary_Tree.md) — Swap left/right, recurse. The Homebrew problem.

### Path-sum family

9. **[Path_Sum.md](./Path_Sum.md)**  ·  [walkthrough →](./learn/Path_Sum.md) — Exists root-to-leaf with target sum? **must-do**
10. **[Path_Sum_II.md](./Path_Sum_II.md)**  ·  [walkthrough →](./learn/Path_Sum_II.md) — Collect all such paths. Backtracking on tree.
11. **[Path_Sum_III.md](./Path_Sum_III.md)**  ·  [walkthrough →](./learn/Path_Sum_III.md) — Any path (not necessarily root-leaf). Prefix-sum + hash. **must-do**
12. **[Paths_from_root_with_a_specified_sum.md](./Paths_from_root_with_a_specified_sum.md)**  ·  [walkthrough →](./learn/Paths_from_root_with_a_specified_sum.md) — Companion variant.
13. **[Sum_Root_to_Leaf_Numbers.md](./Sum_Root_to_Leaf_Numbers.md)**  ·  [walkthrough →](./learn/Sum_Root_to_Leaf_Numbers.md) — Accumulate `10 * acc + node.val`.

### LCA + Construction

14. **[Lowest_Common_Ancestor_of_Binary_Tree.md](./Lowest_Common_Ancestor_of_Binary_Tree.md)**  ·  [walkthrough →](./learn/Lowest_Common_Ancestor_of_Binary_Tree.md) — Recursive: if both children find something, current is LCA. **must-do**
15. **[Construct_Binary_Tree_from_Inorder_and_Postorder.md](./Construct_Binary_Tree_from_Inorder_and_Postorder.md)**  ·  [walkthrough →](./learn/Construct_Binary_Tree_from_Inorder_and_Postorder.md) — Last of postorder is root; split inorder by it; recurse.

---

## Patterns established

- **The four traversals as templates:** Recursive — visit position determines order. Iterative — explicit stack for DFS, queue for BFS.
- **Post-order return value:** Pass info up the tree (height, subtree sum). Combined with "encode invalid as -1" for short-circuit.
- **Prefix-sum on trees:** Path Sum III — accumulate prefix sum on root-to-current path; use hash map of prefixes.
- **LCA recursion:** Recurse left and right; if both non-null, current is LCA. Elegant.
- **Construction from traversals:** Need inorder + (pre or post) to uniquely reconstruct. One alone is not enough.

---

## Common traps

- **Forgetting null check** before accessing `node.left` / `node.right`.
- **Iterative inorder: pushing too early.** Push the node, dive left, pop and visit, then go right. Not "visit when pushing."
- **BFS without level tracking** when the problem needs levels. Snapshot `queue.length` at start of each level.
- **Path Sum III double-counting:** Restore the prefix-sum count on the way back up.
- **Building tree from preorder alone:** Doesn't uniquely identify the tree.

---

## After this topic

- **[Binary_Search_Tree_BST/](../Binary_Search_Tree_BST/LEARNING.md)** — BST inorder = sorted.
- **[Trie_Bit_Manipulation_Trie/](../Trie_Bit_Manipulation_Trie/LEARNING.md)** — specialized n-ary tree.
- **[Graph_BFS_DFS_Dijkstra_DSU/](../Graph_BFS_DFS_Dijkstra_DSU/LEARNING.md)** — trees are graphs with `n-1` edges, no cycles.
- **[Recursion/](../Recursion/LEARNING.md)** — tree recursion is the same shape as array recursion.
