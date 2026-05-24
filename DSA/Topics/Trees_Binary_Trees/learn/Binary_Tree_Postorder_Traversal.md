# Binary Tree Postorder Traversal — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Binary_Tree_Postorder_Traversal.md`](../Binary_Tree_Postorder_Traversal.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/binary-tree-postorder-traversal/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: POSTORDER means Left → Right → Root. Children visited before parent — ideal for BOTTOM-UP computations (height, sum, balance check).** The iterative version is trickier than preorder/inorder; use the "modified preorder + reverse" trick. **Read [`Binary_Tree_Preorder_Traversal.md`](./Binary_Tree_Preorder_Traversal.md) first.**

**Map of this file (9 short sections):**

1. Read the problem
2. What's postorder?
3. Recursive code
4. Trace it
5. Iterative challenge — why postorder is tricky
6. The "modified preorder + reverse" trick
7. Common pitfalls
8. When to use postorder
9. The shape — bottom-up computations

---

## 1. Read the problem

Given the root of a binary tree, return the **POSTORDER traversal** of its nodes' values.

**Example:** for tree
```
    1
   / \
  2   3
 / \
4   5
```

Postorder: `[4, 5, 2, 3, 1]`.

(Left subtree of 1 postorder = [4, 5, 2]. Right subtree = [3]. Root = 1. Concatenate: [4, 5, 2, 3, 1].)

---

## 2. What's postorder?

> **Mini-refresher: postorder = Left, Right, Root.**
>
> Visit order:
> 1. Recursively postorder the LEFT subtree.
> 2. Recursively postorder the RIGHT subtree.
> 3. Visit the CURRENT node LAST.
>
> The root is always visited LAST. Children come before parents.

This "children-before-parent" property is what makes postorder useful for BOTTOM-UP aggregation (subtree sums, heights, etc.).

---

## 3. Recursive code

```
def postorder(node, result):
    if node is null: return
    postorder(node.left, result)
    postorder(node.right, result)
    result.append(node.val)         # visit LAST
```

**C++:**

```cpp
class Solution {
    void postorder(TreeNode* node, vector<int>& result) {
        if (!node) return;
        postorder(node->left, result);
        postorder(node->right, result);
        result.push_back(node->val);
    }
public:
    vector<int> postorderTraversal(TreeNode* root) {
        vector<int> result;
        postorder(root, result);
        return result;
    }
};
```

**Python:**

```python
def postorderTraversal(root):
    result = []
    def dfs(node):
        if not node: return
        dfs(node.left)
        dfs(node.right)
        result.append(node.val)
    dfs(root)
    return result
```

Complexity: **O(n) time, O(h) space.**

---

## 4. Trace it

**Tree:** root=1, left=2 with children 4, 5; right=3.

```
postorder(1):
  postorder(2):
    postorder(4):
      null-left, null-right.
      visit 4                                → result = [4]
    postorder(5):
      visit 5                                 → result = [4, 5]
    visit 2                                   → result = [4, 5, 2]
  postorder(3):
    visit 3                                   → result = [4, 5, 2, 3]
  visit 1                                     → result = [4, 5, 2, 3, 1]

Return [4, 5, 2, 3, 1].  ✓
```

Notice: **1 is visited LAST.** And **each child is visited before its parent** (4 and 5 before 2; 2 and 3 before 1).

---

## 5. Iterative challenge — why postorder is tricky

Preorder iteratively is straightforward (single stack, push right then left). Inorder iteratively is moderate (left-spine walk).

**Postorder iteratively is harder.** Why? Because when you pop a node, you DON'T know whether its CHILDREN have been processed yet. You'd need to remember "have I returned from my right subtree yet?" — which requires additional bookkeeping.

Two main techniques:
1. **Modified preorder + reverse** (cleanest).
2. **One-stack with "last visited" pointer** (more elegant but subtle).

We'll cover Technique 1 — the standard interview answer.

---

## 6. The "modified preorder + reverse" trick

The trick: instead of doing postorder directly, do a MODIFIED preorder that visits in "Root → Right → Left" order. Then REVERSE the result to get "Left → Right → Root" = postorder.

```
def postorder(root):
    if root is null: return []
    stack = [root]
    result = []
    while stack:
        node = stack.pop()
        result.append(node.val)          # visit "Root" (early)
        if node.left: stack.push(node.left)    # left FIRST so right pops first
        if node.right: stack.push(node.right)
    return reversed(result)              # reverse to get postorder
```

**Why this works:**
- Push LEFT first, then RIGHT. Stack is LIFO, so RIGHT pops FIRST.
- We visit ROOT → RIGHT subtree → LEFT subtree (a reverse-preorder).
- Reverse the recorded order: LEFT subtree → RIGHT subtree → ROOT = postorder.

```
Visit order during loop: Root, Right, Right's children, Left, Left's children.
After reversal: Left's children, Left, Right's children, Right, Root.
```

That's postorder. ✓

**C++:**

```cpp
vector<int> postorderTraversal(TreeNode* root) {
    vector<int> result;
    if (!root) return result;
    stack<TreeNode*> stk;
    stk.push(root);
    while (!stk.empty()) {
        TreeNode* node = stk.top(); stk.pop();
        result.push_back(node->val);
        if (node->left) stk.push(node->left);
        if (node->right) stk.push(node->right);
    }
    reverse(result.begin(), result.end());
    return result;
}
```

**Python:**

```python
def postorderTraversal(root):
    if not root: return []
    stack = [root]
    result = []
    while stack:
        node = stack.pop()
        result.append(node.val)
        if node.left: stack.append(node.left)
        if node.right: stack.append(node.right)
    return result[::-1]
```

---

## 7. Common pitfalls

1. **Visiting before recursing.** That's preorder.

2. **In iterative: pushing right BEFORE left** (standard preorder push order). Then the result is preorder reversed, NOT postorder.

3. **Forgetting to reverse** at the end of the iterative version.

4. **Using a single stack without the reverse trick.** Possible but requires "last-visited" tracking. The modified-preorder + reverse is cleaner.

5. **Trying to visit during the descent.** Postorder visits ON THE WAY BACK UP — after both children are done.

---

## 8. When to use postorder

**Postorder = visit AFTER both children.** Ideal for:

- **Computing heights:** `height = 1 + max(height(left), height(right))`. Need children's heights first.
- **Computing subtree sums:** `sum = node.val + sum(left) + sum(right)`.
- **Balanced tree check:** combine "left balanced" AND "right balanced" AND "|left height - right height| ≤ 1".
- **Tree destruction:** delete children FIRST, then the node (else dangling pointers).
- **Postfix expression evaluation:** RPN.
- **Lowest Common Ancestor:** combine info from left and right subtrees.

If your computation NEEDS children processed before the parent, use postorder.

---

## 9. The shape — bottom-up computations

The postorder template for "return some value computed from children":

```
def compute(node):
    if node is null: return base_case_value
    left_val = compute(node.left)
    right_val = compute(node.right)
    return combine(node.val, left_val, right_val)
```

| Application | Combine function |
|---|---|
| Height | `1 + max(left, right)` (base: 0) |
| Sum | `node.val + left + right` (base: 0) |
| Count nodes | `1 + left + right` (base: 0) |
| Balanced check | `(left == -1 or right == -1 or abs(left - right) > 1) ? -1 : 1 + max(left, right)` |
| Diameter | tracks max via reference; returns height |
| LCA | propagates "found" status up |

**Pattern to internalize:**

> "Postorder is the workhorse of BOTTOM-UP tree algorithms. When the parent needs aggregated info from its subtrees, post-order recursion returns that info. The function signature usually has a return value."

---

> **Self-check — the question to ask next time.**
>
> When you face a tree task where the parent's answer depends on its children's results, ask:
>
> > **"Can I postorder traverse, returning aggregated values up the recursion?"**
>
> If yes, you've matched the right pattern.

---

## Cross-references

- **Reference card (post-mastery):** [`../Binary_Tree_Postorder_Traversal.md`](../Binary_Tree_Postorder_Traversal.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Binary_Tree_Preorder_Traversal.md`](./Binary_Tree_Preorder_Traversal.md), [`Binary_Tree_Inorder_Traversal.md`](./Binary_Tree_Inorder_Traversal.md).
  - Coming next: [`Binary_Tree_Inorder_Traversal_Iterative.md`](./Binary_Tree_Inorder_Traversal_Iterative.md), [`Binary_Tree_Level_Order_Traversal.md`](./Binary_Tree_Level_Order_Traversal.md).
