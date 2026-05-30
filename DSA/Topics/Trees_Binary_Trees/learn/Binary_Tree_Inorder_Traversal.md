# Binary Tree Inorder Traversal — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Binary_Tree_Inorder_Traversal.md`](../Binary_Tree_Inorder_Traversal.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/binary-tree-inorder-traversal/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/binary-tree-inorder-traversal/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: INORDER means Left → Root → Right. For a BST, this produces values in SORTED order — a key property.** **Read [`Binary_Tree_Preorder_Traversal.md`](./Binary_Tree_Preorder_Traversal.md) first.**

**Map of this file (8 short sections):**

1. Read the problem
2. What's inorder?
3. The BST connection
4. Recursive code
5. Trace it
6. Iterative inorder (preview)
7. Common pitfalls
8. The shape — when to use inorder

---

## 1. Read the problem

Given the root of a binary tree, return the **inorder traversal** of its nodes' values.

**Examples:**

- Tree `1 → right 2 → left 3`:
  ```
  1
   \
    2
   /
  3
  ```
  Inorder: **[1, 3, 2]**.

- Tree empty (`root = null`): **[]**.

- Tree with one node: `[val]`.

---

## 2. What's inorder?

> **Mini-refresher: inorder = Left, Root, Right.**
>
> The visit order:
> 1. Recursively inorder the LEFT subtree.
> 2. VISIT the current node.
> 3. Recursively inorder the RIGHT subtree.
>
> So the current node is visited BETWEEN its left and right subtree visits.

For:
```
    1
   / \
  2   3
 / \
4   5
```

Inorder: left subtree of 1 first = inorder([2, 4, 5]) = `[4, 2, 5]`. Then 1. Then inorder of right subtree = `[3]`. Full: **[4, 2, 5, 1, 3]**.

---

## 3. The BST connection

> **Mini-refresher: BST property.**
>
> A **Binary Search Tree (BST)** has the invariant: for every node `n`,
> - All values in `n`'s LEFT subtree are LESS than `n.val`.
> - All values in `n`'s RIGHT subtree are GREATER than `n.val`.

**Consequence:** an INORDER traversal of a BST yields values in **STRICTLY INCREASING (sorted) order**.

So inorder is the canonical traversal for:
- Producing sorted output from a BST.
- VALIDATING a BST (inorder must be increasing).
- Finding the k-th smallest in a BST (stop inorder after k visits).

For non-BST trees, inorder is just a specific visit order — no special sortedness.

---

## 4. Recursive code

```
def inorder(node, result):
    if node is null: return
    inorder(node.left, result)
    result.append(node.val)
    inorder(node.right, result)
```

**C++:**

```cpp
class Solution {
    void inorder(TreeNode* node, vector<int>& result) {
        if (!node) return;
        inorder(node->left, result);
        result.push_back(node->val);
        inorder(node->right, result);
    }
public:
    vector<int> inorderTraversal(TreeNode* root) {
        vector<int> result;
        inorder(root, result);
        return result;
    }
};
```

**Python:**

```python
def inorderTraversal(root):
    result = []
    def dfs(node):
        if not node: return
        dfs(node.left)
        result.append(node.val)
        dfs(node.right)
    dfs(root)
    return result
```

Complexity: **O(n) time, O(h) space** (recursion stack).

---

## 5. Trace it

**Tree:** `1 / 2 \ 3` (1 is root; left=2; 2's right=3):

Wait let me be specific. Tree:
```
  1
 / \
nil 2
   /
  3
```

Actually rewriting cleanly: root=1, root.right=2, root.right.left=3.

```
inorder(1):
  inorder(1.left=null). returns.
  visit 1                                  → result = [1]
  inorder(1.right=2):
    inorder(2.left=3):
      inorder(3.left=null). returns.
      visit 3                                → result = [1, 3]
      inorder(3.right=null). returns.
    visit 2                                  → result = [1, 3, 2]
    inorder(2.right=null). returns.

Return [1, 3, 2].  ✓
```

For BST `[2, 1, 3]` (root 2, left 1, right 3):
```
inorder(2):
  inorder(1):
    null-left.
    visit 1.
    null-right.
  visit 2.
  inorder(3):
    null-left.
    visit 3.
    null-right.

Result: [1, 2, 3]. SORTED order. ✓
```

---

## 6. Iterative inorder (preview)

The iterative version is covered in detail in the next file ([`Binary_Tree_Inorder_Traversal_Iterative.md`](./Binary_Tree_Inorder_Traversal_Iterative.md)). The key trick: walk left as far as possible, pushing nodes onto a stack. When you hit null, pop — that's the next node to visit. Then go to its right child.

Skeleton:

```
stack = []
cur = root
while cur or stack:
    while cur:
        stack.push(cur)
        cur = cur.left
    cur = stack.pop()
    visit(cur)
    cur = cur.right
```

We defer the iterative deep-dive to the dedicated file.

---

## 7. Common pitfalls

1. **Visiting BEFORE recursing left.** That's preorder, not inorder.

2. **Visiting AFTER both recurses.** That's postorder.

3. **Forgetting null check.** Crashes on `node.left` if node is null.

4. **Assuming inorder gives sorted output for ANY tree.** Only TRUE for BSTs.

5. **Trying to use inorder on a non-binary tree.** Inorder is specifically defined for trees with left/right children. N-ary trees use different traversals.

6. **Stack overflow on deep trees.** Use iterative version if depth could exceed recursion limit.

---

## 8. The shape — when to use inorder

**Inorder = visit BETWEEN children.** Key use cases:

- **BST traversal:** sorted output.
- **BST validation:** check strict ordering.
- **K-th smallest in BST:** stop after k visits.
- **In-order expression evaluation:** infix notation.
- **Tree-to-sorted-array conversion:** flatten a BST.

**Pattern to internalize:**

> "Inorder is the SPECIAL traversal for BSTs — it produces sorted output. For BST-related problems, reach for inorder."

For non-BST tasks, preorder or postorder usually fits better.

---

> **Self-check — the question to ask next time.**
>
> When you face a BST problem (sorted output, k-th smallest, validate BST), ask:
>
> > **"Can I use INORDER traversal? It naturally produces sorted output for BSTs."**
>
> If yes, you've matched the right tool.

---

## Cross-references

- **Reference card (post-mastery):** [`../Binary_Tree_Inorder_Traversal.md`](../Binary_Tree_Inorder_Traversal.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Binary_Tree_Preorder_Traversal.md`](./Binary_Tree_Preorder_Traversal.md).
  - Coming next: [`Binary_Tree_Postorder_Traversal.md`](./Binary_Tree_Postorder_Traversal.md), [`Binary_Tree_Inorder_Traversal_Iterative.md`](./Binary_Tree_Inorder_Traversal_Iterative.md).
