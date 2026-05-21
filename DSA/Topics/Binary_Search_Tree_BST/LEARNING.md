# Binary Search Tree (BST) — Learning Path

> **Stage:** Trees & Graphs   |   **Prereqs:** [Trees_Binary_Trees/](../Trees_Binary_Trees/LEARNING.md)   |   **Problems:** 11
>
> BST property: left subtree < root < right subtree. Inorder traversal yields sorted order. That's the entire topic.

---

## How to study this topic

1. BST-property exploitation (range, search, LCA).
2. Inorder = sorted (kth smallest, iterator).
3. Construction from sorted input.
4. Side-view / right-view (uses BFS).
5. Two-BST merge problems.

> Note: This folder also contains a few non-BST tree problems for historical reasons (the left/right side view ones). They're filed here because they share the level-order BFS pattern.

---

## Problems in study order

### BST property exploitation

1. **[Range_Sum_of_BST.md](./Range_Sum_of_BST.md)** — Prune subtrees outside the range. **must-do**
2. **[Lowest_Common_Ancestor_of_BST.md](./Lowest_Common_Ancestor_of_BST.md)** — Walk; turn left if both targets < node, right if both >, else current is LCA. **must-do**

### Inorder = sorted

3. **[Kth_Smallest_Element_in_BST.md](./Kth_Smallest_Element_in_BST.md)** — Iterative inorder; count to k. **must-do**
4. **[Binary_Search_Tree_Iterator.md](./Binary_Search_Tree_Iterator.md)** — Inorder iterator state via a stack of left-spine. **must-do**

### Construction

5. **[Convert_Sorted_Array_to_BST.md](./Convert_Sorted_Array_to_BST.md)** — Pick middle as root; recurse halves. Produces balanced BST. **must-do**
6. **[Construct_Binary_Tree_from_Traversals.md](./Construct_Binary_Tree_from_Traversals.md)** — Variant — companion to the one in Trees folder.

### Side views (BFS / level)

7. **[Binary_Tree_Right_Side_View.md](./Binary_Tree_Right_Side_View.md)** — BFS; last node of each level. **must-do**
8. **[Binary_Tree_Left_Side_View.md](./Binary_Tree_Left_Side_View.md)** — BFS; first node of each level.

### Two-BST merge

9. **[All_Elements_in_Two_BSTs.md](./All_Elements_in_Two_BSTs.md)** — Inorder both → merge two sorted lists.
10. **[Merge_Two_BSTs.md](./Merge_Two_BSTs.md)** — Flatten both, merge, rebuild balanced BST from sorted array.

### Misfit (greedy, slotted here historically)

11. **[Queue_Reconstruction_by_Height.md](./Queue_Reconstruction_by_Height.md)** — Sort by `(-height, k)` then insert at index k. Greedy.

---

## Patterns established

- **BST property:** Left < root < right. Use it to prune subtrees (Range Sum) or pick a side (LCA).
- **Inorder yields sorted:** Both recursive and iterative. Used for kth-smallest, validating BSTs, merging.
- **Balanced construction:** Middle element = root, recurse halves.
- **BST iterator state:** Push the entire left spine on init; on `next()` pop, push left spine of popped's right child. O(h) memory.
- **Level-order side views:** BFS; pick first/last of each level.
- **Sort + insert greedy:** Queue Reconstruction — taller first ensures positions are stable when shorter people insert.

---

## Common traps

- **Forgetting to prune** in Range Sum: if `node.val < low`, only recurse right; if `> high`, only left.
- **Off-by-one in middle:** For Convert Sorted Array to BST, `(lo + hi) / 2` (floor) vs `(lo + hi + 1) / 2` (ceil) yields different but valid BSTs. Be consistent.
- **Mutating shared subtrees** in Merge Two BSTs without flattening first.
- **LCA on non-BST:** Don't use BST shortcut on general binary tree — that goes in `Trees_Binary_Trees`.

---

## After this topic

- **[Heap_Priority_Queue/](../Heap_Priority_Queue/LEARNING.md)** — when you need ordered access but don't need full BST.
- **[Segment_Tree_Range_Queries/](../Segment_Tree_Range_Queries/LEARNING.md)** — specialized BST for range queries.
- **[Graph_BFS_DFS_Dijkstra_DSU/](../Graph_BFS_DFS_Dijkstra_DSU/LEARNING.md)** — BFS generalizes side-view to arbitrary graphs.
