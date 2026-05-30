# Binary Tree Inorder Traversal

**Problem Link:**
<a href="https://leetcode.com/problems/binary-tree-inorder-traversal/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/binary-tree-inorder-traversal/</a>

**Topic:**
Trees / Binary Trees

----------------------------------------

## Step 1: What's Inorder?

For a binary tree, **inorder traversal** visits nodes in this order:
1. Visit the left subtree (recursively inorder).
2. Visit the current node.
3. Visit the right subtree (recursively inorder).

Return the list of node values in the order visited.

Example:
```
    1
     \
      2
     /
    3
```

- Start at 1. Visit left (null, nothing). Visit 1. Visit right (subtree rooted at 2).
- At 2: visit left (subtree rooted at 3). At 3: left null, visit 3, right null. Done with 3.
- Visit 2. Visit right (null).

Result: `[1, 3, 2]`.

Another example:
```
      1
     / \
    2   3
   / \
  4   5
```

Inorder: left subtree of 1 is `[4, 2, 5]`, then 1, then right subtree `[3]`. Full: `[4, 2, 5, 1, 3]`.

----------------------------------------

## Step 2: Why "Inorder"?

For a **Binary Search Tree (BST)**, inorder traversal yields values in **sorted ascending order**. This makes inorder useful for:
- Producing sorted output from a BST.
- Checking if a tree is a valid BST (inorder must be strictly increasing).
- Finding the k-th smallest element in a BST.

For non-BST trees, inorder is just a specific traversal convention.

----------------------------------------

## Step 3: Recursive Solution

The simplest implementation follows the definition directly:

```
def inorder(node, result):
    if node is null: return
    inorder(node.left, result)
    result.append(node.val)
    inorder(node.right, result)
```

O(n) time (visit each node once), O(h) space (recursion depth = tree height). For balanced trees h = O(log n); for skewed trees h = O(n).

----------------------------------------

## Step 4: Iterative Solution with a Stack

The problem often asks for an **iterative** version (to avoid recursion overhead or stack overflow on deep trees).

Idea: simulate the recursion using an explicit stack. Walk left as far as possible, pushing nodes onto the stack. When we hit null, pop — that's the next node to visit. Then move to its right subtree.

```
result = []
stack = []
cur = root

while cur is not null or stack not empty:
    # Descend left, pushing all ancestors
    while cur is not null:
        stack.push(cur)
        cur = cur.left
    
    # Now cur is null; pop to visit
    cur = stack.pop()
    result.append(cur.val)
    
    # Move to right subtree; outer loop resumes descending
    cur = cur.right

return result
```

O(n) time, O(h) space (the stack holds at most h nodes at once).

----------------------------------------

## Step 5: Trace Iterative on the First Tree

```
    1
     \
      2
     /
    3
```

Start: cur = 1, stack = [], result = [].

```
Iteration 1:
  Descend left: stack = [1], cur = null.
  Pop 1. result = [1]. cur = 1.right = 2.

Iteration 2:
  Descend left: cur = 2. stack = [2]. cur = 2.left = 3. stack = [2, 3]. cur = 3.left = null.
  Pop 3. result = [1, 3]. cur = 3.right = null.

Iteration 3:
  cur = null, stack = [2]. Skip inner while.
  Pop 2. result = [1, 3, 2]. cur = 2.right = null.

Iteration 4:
  cur = null, stack = []. Loop condition fails. Exit.
```

Result: `[1, 3, 2]`. ✓

----------------------------------------

## Step 6: Morris Traversal — O(1) Space

If we're allowed to **temporarily modify the tree**, we can do inorder in **O(1) extra space** using Morris traversal:
- At each node, find the rightmost node of the left subtree (the "predecessor" in inorder).
- Make the predecessor's right pointer point to the current node (temporary "thread").
- Descend to the left subtree.
- When we arrive back at current via the thread, we've finished the left subtree — visit current, remove the thread, move right.

O(n) time (each edge traversed at most twice), O(1) extra space. Restores the tree to its original state.

```
cur = root
while cur is not null:
    if cur.left is null:
        result.append(cur.val)
        cur = cur.right
    else:
        pred = cur.left
        while pred.right is not null and pred.right != cur:
            pred = pred.right
        if pred.right is null:
            pred.right = cur          # set thread
            cur = cur.left
        else:
            pred.right = null          # remove thread
            result.append(cur.val)
            cur = cur.right
```

Trickier to implement correctly, but a classic "constant space" traversal technique.

----------------------------------------

## Step 7: Name It

**Tree traversal** — a foundational algorithm. Three main flavors:
- **Inorder** (L, root, R): BST-sorted output.
- **Preorder** (root, L, R): copy a tree; prefix expression.
- **Postorder** (L, R, root): delete a tree; postfix expression.
- **Level order** (BFS): breadth-first.

Variants:
- Recursive (cleanest).
- Iterative with stack (no recursion overhead).
- Morris (O(1) space).

----------------------------------------

## Step 8: Complexity

**Recursive** / **Iterative with stack**:
- Time: O(n).
- Space: O(h) — tree height. Best case O(log n), worst O(n) for skewed trees.

**Morris traversal**:
- Time: O(n).
- Space: **O(1)** extra.

----------------------------------------

## Step 9: C++ Implementation

**Recursive:**

```cpp
struct TreeNode { int val; TreeNode *left, *right; };

void inorder(TreeNode* node, vector<int>& result) {
    if (!node) return;
    inorder(node->left, result);
    result.push_back(node->val);
    inorder(node->right, result);
}

vector<int> inorderTraversal(TreeNode* root) {
    vector<int> result;
    inorder(root, result);
    return result;
}
```

**Iterative:**

```cpp
vector<int> inorderTraversal(TreeNode* root) {
    vector<int> result;
    stack<TreeNode*> st;
    TreeNode* cur = root;
    while (cur || !st.empty()) {
        while (cur) {
            st.push(cur);
            cur = cur->left;
        }
        cur = st.top(); st.pop();
        result.push_back(cur->val);
        cur = cur->right;
    }
    return result;
}
```

**Morris:**

```cpp
vector<int> inorderTraversal(TreeNode* root) {
    vector<int> result;
    TreeNode* cur = root;
    while (cur) {
        if (!cur->left) {
            result.push_back(cur->val);
            cur = cur->right;
        } else {
            TreeNode* pred = cur->left;
            while (pred->right && pred->right != cur) pred = pred->right;
            if (!pred->right) {
                pred->right = cur;
                cur = cur->left;
            } else {
                pred->right = nullptr;
                result.push_back(cur->val);
                cur = cur->right;
            }
        }
    }
    return result;
}
```

----------------------------------------

## Step 10: Follow-up Questions

- **Preorder / postorder iterative.** Preorder uses a stack with "push right then left" so left is popped first; postorder is trickier (use two stacks or a marker).
- **Validate BST.** Inorder must be strictly increasing — scan as we traverse.
- **K-th smallest in BST.** Stop inorder early after k visits.
- **Thread safety.** Morris traversal modifies the tree; unsafe for concurrent reads.
- **Recursive depth exceeds stack limit.** Switch to iterative or Morris.
- **In-place reconstruction of a skewed tree.** Morris is the tool.
