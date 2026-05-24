# Lowest Common Ancestor of BST — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Lowest_Common_Ancestor_of_BST.md`](../Lowest_Common_Ancestor_of_BST.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. **A SIMPLER version of the general-tree LCA, thanks to BST ordering.** The lesson: **compare p and q's values to the current node. If BOTH less → go left. BOTH greater → go right. ELSE current is LCA.** O(h) walk vs O(n) for general trees. **Read [`Lowest_Common_Ancestor_of_Binary_Tree.md`](../../Trees_Binary_Trees/learn/Lowest_Common_Ancestor_of_Binary_Tree.md) first.**

**Map of this file (8 short sections):**

1. Read the problem
2. Recall: general-tree LCA (O(n))
3. The BST insight
4. The three cases
5. Code (iterative and recursive)
6. Trace it
7. Common pitfalls
8. The shape — BST-ordered walks

---

## 1. Read the problem

Given a **BST** and two nodes `p` and `q` from it, return their **LOWEST COMMON ANCESTOR** (the deepest node that has both as descendants; a node is its own descendant).

**Example:**

```
        6
       / \
      2   8
     / \ / \
    0  4 7  9
      / \
     3   5
```

- `LCA(2, 8) = 6` (split at root).
- `LCA(2, 4) = 2` (2 is ancestor of itself and of 4).
- `LCA(3, 5) = 4`.

---

## 2. Recall: general-tree LCA (O(n))

For a generic binary tree, LCA is O(n) post-order DFS — see the general LCA walkthrough.

But BSTs have STRUCTURE (the ordering invariant). Can we do better?

**Yes — O(h) walk, like binary search.**

---

## 3. The BST insight

> **Mini-refresher: BST ordering.**
>
> For any BST node N:
> - All values in N's LEFT subtree are LESS than N.val.
> - All values in N's RIGHT subtree are GREATER than N.val.

For LCA(p, q), at the current node `cur`, three cases by comparing values:

**Case A: `p.val < cur.val AND q.val < cur.val`.**
- Both targets are LESS than cur → both are in the LEFT subtree.
- The LCA is somewhere in the left subtree (deeper than cur).
- **Go left.**

**Case B: `p.val > cur.val AND q.val > cur.val`.**
- Both targets in RIGHT subtree. **Go right.**

**Case C: otherwise** (one less, one greater, OR one equals cur).
- p and q are on DIFFERENT sides of cur (or one IS cur).
- **`cur` IS the LCA.**

Why? If they're on different sides, cur is the SPLIT POINT — going deeper would lose access to one side. If one equals cur, cur is its own ancestor.

---

## 4. The three cases

```
while cur:
    if p.val < cur.val and q.val < cur.val:
        cur = cur.left
    elif p.val > cur.val and q.val > cur.val:
        cur = cur.right
    else:
        return cur
```

The recursion ALWAYS goes into EXACTLY ONE subtree at each step, so it unrolls naturally into an iterative loop.

> **Mini-refresher: O(h) descent.**
>
> Like binary search on an array, each step halves (or more) the search space. Total iterations: O(h). For balanced BSTs, O(log n).

---

## 5. Code (iterative and recursive)

**C++ — iterative:**

```cpp
TreeNode* lowestCommonAncestor(TreeNode* root, TreeNode* p, TreeNode* q) {
    while (root) {
        if (p->val < root->val && q->val < root->val) {
            root = root->left;
        } else if (p->val > root->val && q->val > root->val) {
            root = root->right;
        } else {
            return root;
        }
    }
    return nullptr;
}
```

**C++ — recursive:**

```cpp
TreeNode* lowestCommonAncestor(TreeNode* root, TreeNode* p, TreeNode* q) {
    if (p->val < root->val && q->val < root->val)
        return lowestCommonAncestor(root->left, p, q);
    if (p->val > root->val && q->val > root->val)
        return lowestCommonAncestor(root->right, p, q);
    return root;
}
```

**Python (iterative):**

```python
def lowestCommonAncestor(root, p, q):
    while root:
        if p.val < root.val and q.val < root.val:
            root = root.left
        elif p.val > root.val and q.val > root.val:
            root = root.right
        else:
            return root
    return None
```

Complexity: **O(h) time, O(1) space iterative** (O(h) recursive).

---

## 6. Trace it

**`LCA(3, 5)`** in the example tree.

```
cur = 6. 3 < 6 AND 5 < 6 → go left. cur = 2.
cur = 2. 3 > 2 AND 5 > 2 → go right. cur = 4.
cur = 4. 3 < 4 AND 5 > 4 → SPLIT. Return 4.
```

Three iterations. ✓

**`LCA(2, 8)`:**

```
cur = 6. 2 < 6 AND 8 > 6 → SPLIT. Return 6.
```

One iteration. ✓

**`LCA(2, 4)`:**

```
cur = 6. 2 < 6 AND 4 < 6 → go left. cur = 2.
cur = 2. 2 == 2 (not strictly less). Hits the ELSE branch. Return 2.
```

Two iterations. ✓

---

## 7. Common pitfalls

1. **Using `<=` or `>=` instead of `<` and `>`.** Need STRICT comparisons. When one equals cur, the ELSE branch (return cur) is correct.

2. **Trying the general-tree algorithm.** O(n) instead of O(h). Don't.

3. **Treating duplicate values.** BSTs usually have distinct values. If duplicates exist (non-standard), the algorithm might need adjustment.

4. **Going both directions.** Only one — the comparisons dictate which.

5. **Returning the wrong node when split happens.** Must return `cur` (the split point), not its child.

6. **Forgetting that p and q might not be IN the tree.** Problem usually guarantees they are. If not, post-validate.

---

## 8. The shape — BST-ordered walks

The pattern:

> **"BST property lets you DECIDE WHICH SUBTREE to descend into based on a value comparison. Each step is O(1); total O(h)."**

| Operation | Walk decision |
|---|---|
| **This problem** (LCA) | both < cur → left; both > cur → right; else cur |
| Search | val < cur → left; val > cur → right; val == cur → found |
| Insert | walk to a null spot using same comparison |
| Delete | walk + complex pointer surgery |
| Range queries | use bounds to prune |

**Pattern to internalize:**

> "On BSTs, you can WALK DOWN guided by comparisons. Most queries are O(h). For balanced BSTs, O(log n)."

---

## Cross-references

- **Reference card (post-mastery):** [`../Lowest_Common_Ancestor_of_BST.md`](../Lowest_Common_Ancestor_of_BST.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Range_Sum_of_BST.md`](./Range_Sum_of_BST.md).
  - [`../../Trees_Binary_Trees/learn/Lowest_Common_Ancestor_of_Binary_Tree.md`](../../Trees_Binary_Trees/learn/Lowest_Common_Ancestor_of_Binary_Tree.md) — general tree (O(n)).
  - Coming next: [`Kth_Smallest_Element_in_BST.md`](./Kth_Smallest_Element_in_BST.md).
