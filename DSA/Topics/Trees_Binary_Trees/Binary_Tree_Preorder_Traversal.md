# Binary Tree Preorder Traversal

**Problem Link:**
https://leetcode.com/problems/binary-tree-preorder-traversal/

**Topic:**
Trees / Binary Trees

----------------------------------------

## Step 1: What's Preorder?

Given a binary tree, return its **preorder** traversal: visit each node in the order **Root → Left subtree → Right subtree**.

Example:
```
    1
     \
      2
     /
    3
```

Preorder visits: 1 (root), then left subtree (empty), then right subtree (the (2)-rooted subtree).
For (2)-rooted subtree: visit 2, then left subtree (the (3)-rooted subtree), then right (empty).
For (3)-rooted subtree: visit 3.

Order: [1, 2, 3].

Another:
```
     F
    / \
   B   G
  / \   \
 A   D   I
    / \  /
   C   E H
```

Preorder: F, B, A, D, C, E, G, I, H.

----------------------------------------

## Step 2: Recursive — The Natural Expression

The definition *is* the algorithm:

```
def preorder(node):
    if node is null: return
    visit(node)          # Root
    preorder(node.left)  # Left
    preorder(node.right) # Right
```

Translates directly from the definition. O(n) time, O(h) stack space where h is tree height.

For the first example:
- preorder(1): visit 1. preorder(1.left = null). preorder(1.right = 2).
  - preorder(2): visit 2. preorder(2.left = 3).
    - preorder(3): visit 3. null left, null right.
  - preorder(2.right = null).

Order of visits: 1, 2, 3. ✓

----------------------------------------

## Step 3: Iterative — Simulate the Call Stack

For very deep trees (skewed to a chain), recursion might blow the stack. The iterative version uses an explicit stack:

```
def preorder(root):
    if root is null: return []
    stack = [root]
    result = []
    while stack not empty:
        node = stack.pop()
        visit(node)
        if node.right: stack.push(node.right)
        if node.left: stack.push(node.left)
    return result
```

Key detail: push **right first, then left**. When we pop, we get left first (because the stack is LIFO). This preserves the preorder "Root → Left → Right" visit order.

Trace for the tree `1 \ 2 / 3`:
```
stack = [1].
Pop 1. Visit 1. No right child. Push left (null? In this tree, 1.left = null so don't push). Push right (2). stack = [2].

Wait, 1.left is null and 1.right is 2. Push right = 2.
Order: push right first? Actually per my code: "if node.right: stack.push(node.right)" then "if node.left: stack.push(node.left)". So we'd push 2 first, then... but left is null. stack = [2].

Pop 2. Visit 2. Push right (null). Push left (3). stack = [3].
Pop 3. Visit 3. Null children. stack = [].
```

Order: 1, 2, 3. ✓

The "right before left" push order is the crucial trick. Getting it backward gives you postorder reversed or a mangled order.

----------------------------------------

## Step 4: Morris Preorder — O(1) Space

There's a technique called **Morris traversal** that achieves O(n) time with O(1) extra space by temporarily modifying the tree (using null right pointers as "threads"). It's clever but more complex.

For interviews, recursive and iterative-with-stack are the standard answers. Morris is a "flex" — mention it exists, implement only if asked.

----------------------------------------

## Step 5: Trace Both Versions on a Bigger Tree

Tree:
```
     1
    / \
   2   3
  / \
 4   5
```

**Recursive:**
- preorder(1): visit 1. preorder(2).
  - preorder(2): visit 2. preorder(4).
    - preorder(4): visit 4. (null children)
  - preorder(5).
    - preorder(5): visit 5.
- preorder(3): visit 3. (null children)

Order: 1, 2, 4, 5, 3.

**Iterative:**
```
stack=[1].
Pop 1. Visit. Push right (3), left (2). stack=[3, 2].
Pop 2. Visit. Push right (5), left (4). stack=[3, 5, 4].
Pop 4. Visit. No children. stack=[3, 5].
Pop 5. Visit. No children. stack=[3].
Pop 3. Visit. No children.
```

Order: 1, 2, 4, 5, 3. ✓ Same.

----------------------------------------

## Step 6: Why Preorder Is Useful

- **Serialization:** preorder + null markers uniquely encode the tree structure.
- **Expression tree evaluation:** prefix notation (Polish notation) for math.
- **Tree copying:** build a copy by visiting in preorder and cloning.
- **Directory listing:** "folder first, then contents" matches preorder.

When to pick preorder vs inorder vs postorder? Depends on when the parent info matters:
- **Preorder:** parent info available *before* descending into children.
- **Inorder:** parent info available *between* left and right child traversals.
- **Postorder:** parent info available *after* both children processed.

For recursive problems that aggregate from children (heights, sums), postorder fits. For problems that propagate info down (depths, paths), preorder fits.

----------------------------------------

## Step 7: Name It

**Preorder (Root-Left-Right) DFS traversal.** One of the three classic binary tree traversals; learn all three.

----------------------------------------

## Step 8: Complexity

Time: **O(n)** — visit each node once.
Space: **O(h)** for recursion or stack. O(1) for Morris.

----------------------------------------

## Step 9: C++ Implementation

**Recursive:**

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

**Iterative:**

```cpp
vector<int> preorderTraversal(TreeNode* root) {
    vector<int> result;
    if (!root) return result;
    stack<TreeNode*> stk;
    stk.push(root);
    while (!stk.empty()) {
        TreeNode* node = stk.top(); stk.pop();
        result.push_back(node->val);
        if (node->right) stk.push(node->right);
        if (node->left) stk.push(node->left);
    }
    return result;
}
```

Both are clean. Recursive is shortest; iterative is stack-safe.

----------------------------------------

## Step 10: Follow-up Questions

- **Iterative inorder traversal.** Different structure — push left spine, pop to visit, then move right.
- **Iterative postorder traversal.** Trickier — two-stack approach or track last-visited.
- **Morris traversal.** Thread right pointers for O(1) space.
- **N-ary tree preorder.** Similar recursion; loop over children instead of two calls.
- **Concurrent traversal.** Each thread picks up from where the previous left off; state is pointer + stack.
- **Serialize/deserialize a tree.** Use preorder with null markers.
