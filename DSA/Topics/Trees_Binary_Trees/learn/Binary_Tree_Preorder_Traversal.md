# Binary Tree Preorder Traversal — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Binary_Tree_Preorder_Traversal.md`](../Binary_Tree_Preorder_Traversal.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/binary-tree-preorder-traversal/

---

## How to use this file

Paced for someone seeing binary trees for the first time. Reading time: ~18 minutes. **The introduction to tree traversal.** The lesson: **PREORDER means Root → Left → Right.** Master this and the other two DFS traversals (inorder, postorder) follow trivially — just shuffle the "visit" step. **Read [`Subsets.md`](../../Recursion/learn/Subsets.md) first** for recursion fundamentals.

**Map of this file (10 sections):**

1. What's a binary tree?
2. The TreeNode definition
3. What's preorder?
4. The recursive solution
5. The iterative solution (with stack)
6. Code
7. Trace it
8. Common pitfalls
9. When to use preorder
10. The shape — DFS traversal family

---

## 1. What's a binary tree?

> **Mini-refresher: binary trees.**
>
> A **binary tree** is a hierarchical data structure where each NODE has:
> - A VALUE.
> - At most TWO CHILDREN: a LEFT child and a RIGHT child.
>
> Special node: the **ROOT** (top of the tree). Nodes with no children are **LEAVES**.
>
> Example:
> ```
>     1        ← root
>    / \
>   2   3
>  / \
> 4   5        ← 4, 5, 3 are leaves
> ```
>
> Properties:
> - **Depth** of a node: distance from root.
> - **Height** of the tree: max depth = number of edges on longest root-to-leaf path.
> - **N nodes** in a tree of n nodes (trivially).

---

## 2. The TreeNode definition

Standard struct (C++ / similar in Python and JS):

```cpp
struct TreeNode {
    int val;
    TreeNode* left;
    TreeNode* right;
    TreeNode(int v) : val(v), left(nullptr), right(nullptr) {}
};
```

Each node holds a value and two child pointers. `left == nullptr` or `right == nullptr` means no child in that direction.

---

## 3. What's preorder?

> **Mini-refresher: the three DFS traversals.**
>
> All three visit each node EXACTLY ONCE. They differ in WHEN to visit the current node relative to its children:
>
> - **Preorder**: visit current FIRST, then left subtree, then right subtree. (Root → Left → Right)
> - **Inorder**: visit left subtree, THEN current, THEN right subtree. (Left → Root → Right)
> - **Postorder**: visit left subtree, then right subtree, THEN current LAST. (Left → Right → Root)
>
> All three traversals visit n nodes in O(n) time. The choice depends on WHEN you need parent information.

For our example tree:
```
    1
   / \
  2   3
 / \
4   5
```

**Preorder visits:** 1 (root), then preorder of left subtree (2, 4, 5), then preorder of right subtree (3). Result: `[1, 2, 4, 5, 3]`.

---

## 4. The recursive solution

The DEFINITION IS THE ALGORITHM:

```
def preorder(node):
    if node is null: return
    visit(node)              # Root
    preorder(node.left)       # Left
    preorder(node.right)      # Right
```

Three lines for the body. Reads exactly like the definition.

> **Mini-refresher: base case for tree recursion.**
>
> Every tree recursion needs a base case for `null` (or "empty subtree"). Without it, you'd dereference `null.left` and crash.
>
> Standard convention: `if node is null: return` (do nothing for empty subtree). Then proceed with the meat of the function for non-null.

Time: O(n). Space: O(h) for the recursion stack, where h is the tree's height.

---

## 5. The iterative solution (with stack)

For very deep trees, recursion may overflow the stack. Iterative version uses an explicit stack:

```
if root is null: return []
stack = [root]
result = []
while stack not empty:
    node = stack.pop()
    result.append(node.val)
    if node.right: stack.push(node.right)
    if node.left: stack.push(node.left)
return result
```

**Critical detail: push RIGHT BEFORE LEFT.** Why? Stack is LIFO. We want LEFT to be processed FIRST after popping. So push right first (deeper in the stack), then left (top of the stack). When we pop next, we get the left child.

---

## 6. Code

**C++ — recursive:**

```cpp
class Solution {
    void preorder(TreeNode* node, vector<int>& result) {
        if (!node) return;
        result.push_back(node->val);
        preorder(node->left, result);
        preorder(node->right, result);
    }
public:
    vector<int> preorderTraversal(TreeNode* root) {
        vector<int> result;
        preorder(root, result);
        return result;
    }
};
```

**C++ — iterative:**

```cpp
vector<int> preorderTraversal(TreeNode* root) {
    vector<int> result;
    if (!root) return result;
    stack<TreeNode*> stk;
    stk.push(root);
    while (!stk.empty()) {
        TreeNode* node = stk.top(); stk.pop();
        result.push_back(node->val);
        if (node->right) stk.push(node->right);   // push right FIRST
        if (node->left) stk.push(node->left);     // push left LAST → popped first
    }
    return result;
}
```

**Python:**

```python
def preorderTraversal(root):
    result = []
    def dfs(node):
        if not node: return
        result.append(node.val)
        dfs(node.left)
        dfs(node.right)
    dfs(root)
    return result
```

Complexity: **O(n) time, O(h) space.**

---

## 7. Trace it

**Tree:**
```
    1
   / \
  2   3
 / \
4   5
```

**Recursive:**

```
preorder(1):
  visit 1                                  → result = [1]
  preorder(2):
    visit 2                                 → result = [1, 2]
    preorder(4):
      visit 4                                → result = [1, 2, 4]
      preorder(null), preorder(null).
    preorder(5):
      visit 5                                → result = [1, 2, 4, 5]
  preorder(3):
    visit 3                                  → result = [1, 2, 4, 5, 3]

Return [1, 2, 4, 5, 3].  ✓
```

**Iterative:**

```
stack = [1]. result = [].

Pop 1. result = [1]. Push 1.right=3, then 1.left=2. stack = [3, 2].
Pop 2. result = [1, 2]. Push 2.right=5, then 2.left=4. stack = [3, 5, 4].
Pop 4. result = [1, 2, 4]. No children. stack = [3, 5].
Pop 5. result = [1, 2, 4, 5]. No children. stack = [3].
Pop 3. result = [1, 2, 4, 5, 3]. No children. stack = [].

Return [1, 2, 4, 5, 3].  ✓
```

Both produce the same order. The iterative push order (right-then-left) ensures left is processed first.

---

## 8. Common pitfalls

1. **Forgetting the null check.** Crashes on `node.left` if node is null.

2. **In iterative: pushing left FIRST.** This produces "Root → Right → Left" order — reverse postorder, not preorder. **Push right first.**

3. **Treating the tree as 0-indexed (like arrays).** Trees don't have indices; they have pointers.

4. **Trying to modify the tree.** Standard traversals are READ-ONLY.

5. **Off-by-one when computing depth.** Depth is the NUMBER OF EDGES on the root-to-node path, or NUMBER OF NODES minus 1. Conventions vary; check the problem.

6. **Confusing preorder with BFS.** Preorder is DFS (depth-first). BFS visits by levels (covered in Level Order Traversal).

---

## 9. When to use preorder

**Preorder = Root before children.** Good for tasks where parent info is needed BEFORE descending:

- **Tree copying:** allocate the root, then recurse into children with the root as parent.
- **Serializing a tree:** root-first encoding (with null markers) uniquely captures structure.
- **Path enumeration:** parent contributes to path before exploring children.
- **Compiler "prefix expression" generation:** root operator comes first.
- **Directory listing:** "folder first, then contents."

If your computation NEEDS the parent processed BEFORE its children, use preorder.

---

## 10. The shape — DFS traversal family

The traversal family:

| Traversal | Order | Use case |
|---|---|---|
| **Preorder** | Root, Left, Right | Tree copy, serialization, prefix expressions |
| **Inorder** | Left, Root, Right | BST → sorted; expression evaluation in-order |
| **Postorder** | Left, Right, Root | Subtree computations (height, sum), free tree |
| **Level Order** | BFS by level | Level-by-level processing |

All three DFS traversals share the same RECURSION STRUCTURE; they just place the "visit" step at different points.

**Pattern to internalize:**

> "DFS traversals are templates with one knob: WHEN to visit the current node. Preorder = before children. Inorder = between left and right. Postorder = after both children."

---

> **Self-check — the question to ask next time.**
>
> When you face a tree-traversal task, ask:
>
> > **"Do I need parent info BEFORE children (preorder), BETWEEN them (inorder), or AFTER both (postorder)?"**
>
> Pick the traversal that matches the data flow.

---

## Cross-references

- **Reference card (post-mastery):** [`../Binary_Tree_Preorder_Traversal.md`](../Binary_Tree_Preorder_Traversal.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Binary_Tree_Inorder_Traversal.md`](./Binary_Tree_Inorder_Traversal.md), [`Binary_Tree_Postorder_Traversal.md`](./Binary_Tree_Postorder_Traversal.md).
