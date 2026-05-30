# Invert Binary Tree — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Invert_Binary_Tree.md`](../Invert_Binary_Tree.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/invert-binary-tree/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/invert-binary-tree/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~10 minutes. **A tiny but famous problem.** The lesson: **at each node, swap its children, then recurse into both. Three lines.** Famously the Homebrew interview question.

**Map of this file (6 short sections):**

1. Read the problem
2. The recursive insight
3. Code
4. Trace it
5. The BFS alternative
6. Common pitfalls + the shape

---

## 1. Read the problem

Given the root of a binary tree, **INVERT** the tree (produce its mirror image) and return the root.

> **Mini-refresher: what's "invert"?**
>
> Inverting (mirroring) a tree means: at every node, swap its left and right children. Visually, the tree is reflected across a vertical axis through the root.

**Example:**

Before:
```
    4
   / \
  2   7
 / \ / \
1  3 6  9
```

After:
```
    4
   / \
  7   2
 / \ / \
9  6 3  1
```

---

## 2. The recursive insight

For any node:
1. **Swap** its left and right children.
2. **Recurse** into the (now-swapped) subtrees.

Base: null nodes — nothing to do.

```
def invert(node):
    if node is null: return null
    node.left, node.right = node.right, node.left   # swap
    invert(node.left)
    invert(node.right)
    return node
```

Three lines of real work. Order of swap vs recurse doesn't matter (the swap is just pointer reassignment; recursion is independent of sibling).

---

## 3. Code

**C++:**

```cpp
TreeNode* invertTree(TreeNode* root) {
    if (!root) return nullptr;
    swap(root->left, root->right);
    invertTree(root->left);
    invertTree(root->right);
    return root;
}
```

**Python:**

```python
def invertTree(root):
    if not root: return None
    root.left, root.right = root.right, root.left
    invertTree(root.left)
    invertTree(root.right)
    return root
```

**JavaScript:**

```javascript
function invertTree(root) {
    if (!root) return null;
    [root.left, root.right] = [root.right, root.left];
    invertTree(root.left);
    invertTree(root.right);
    return root;
}
```

Complexity: **O(n) time, O(h) space.**

---

## 4. Trace it

**Tree:** root=1, left=2, right=3 (each leaves).

```
invert(1):
  swap 1.left and 1.right → 1.left=3, 1.right=2.
  invert(3): null children → no-op.
  invert(2): null children → no-op.
  return 1.

Tree is now: root=1, left=3, right=2.  ✓
```

For deeper trees, each level swaps independently.

---

## 5. The BFS alternative

For very deep trees, recursion might overflow. Use BFS:

```python
def invertTree(root):
    if not root: return None
    q = deque([root])
    while q:
        node = q.popleft()
        node.left, node.right = node.right, node.left
        if node.left: q.append(node.left)
        if node.right: q.append(node.right)
    return root
```

Each node is processed once; its children swapped. Same outcome.

---

## 6. Common pitfalls + the shape

**Pitfalls:**

1. **Forgetting to recurse after swap.** The swap only handles ONE level; you need to recurse into both children too.

2. **Returning a NEW tree.** This problem MUTATES the input tree in place. Don't allocate new nodes (unless you specifically want a non-mutating version).

3. **Swapping AFTER recursion.** Works — but the result is the same. Either order is fine.

**The shape:**

> **"Tree operations that locally modify each node generally follow the pattern: process this node, then recurse into both children. The order (pre/post) often doesn't matter for simple mutations."**

This problem is famous for being deceptively simple yet asked by major companies.

---

## Cross-references

- **Reference card (post-mastery):** [`../Invert_Binary_Tree.md`](../Invert_Binary_Tree.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Binary_Tree_Preorder_Traversal.md`](./Binary_Tree_Preorder_Traversal.md), [`Maximum_Depth_of_Binary_Tree.md`](./Maximum_Depth_of_Binary_Tree.md).
  - Coming next: [`Path_Sum.md`](./Path_Sum.md), [`Path_Sum_II.md`](./Path_Sum_II.md), [`Path_Sum_III.md`](./Path_Sum_III.md).
