# Binary Tree Postorder Traversal

**Problem Link:**
https://leetcode.com/problems/binary-tree-postorder-traversal/

**Topic:**
Trees / Binary Trees

----------------------------------------

## Step 1: What's Postorder?

Given a binary tree, visit nodes in the order **Left subtree → Right subtree → Root**.

Example:
```
    1
     \
      2
     /
    3
```

Postorder:
- 1's left subtree (empty).
- 1's right subtree: (2)-rooted. Recurse.
  - 2's left subtree: (3)-rooted.
    - 3's left (empty), right (empty). Visit 3.
  - 2's right (empty). Visit 2.
- Visit 1.

Order: [3, 2, 1].

Key property: **the root is always visited LAST** within its own subtree. Children are visited before parents.

----------------------------------------

## Step 2: Recursive Version

```
def postorder(node):
    if node is null: return
    postorder(node.left)
    postorder(node.right)
    visit(node)
```

Natural mapping from the definition. O(n) time, O(h) stack space.

Common interview question: write this iteratively (without recursion).

----------------------------------------

## Step 3: The Iterative Challenge

Preorder and inorder have clean iterative forms with a single stack. **Postorder is trickier** because we want to visit the node after both its children — but when we pop the node from our stack, we need to know whether we've already processed its children.

Two main techniques:

**Technique 1: Two stacks.**
First compute a "reverse postorder" via modified preorder (push left first, then right — reversed from normal preorder). This gives Root, Right, Left in reverse = Left, Right, Root. Reverse the result at the end.

**Technique 2: One stack with a "last visited" pointer.**
Walk down the left spine. At each node, check if we need to process the right subtree before visiting this node.

Technique 1 is simpler to write. Technique 2 is more elegant but subtle.

----------------------------------------

## Step 4: Two-Stack Technique

```
def postorder(root):
    if root is null: return []
    stack1 = [root]
    stack2 = []   # holds nodes in reverse-postorder (postorder-reversed)
    while stack1 not empty:
        node = stack1.pop()
        stack2.push(node)
        if node.left: stack1.push(node.left)
        if node.right: stack1.push(node.right)
    # stack2 now contains nodes in order: Root, Right, Left (each level). Reversing gives postorder.
    result = []
    while stack2 not empty: result.append(stack2.pop().val)
    return result
```

Why does this work? The first loop processes nodes in "Root → Right → Left" order (a variant of preorder where we push Left first, causing Right to pop first). Storing these in stack2 and then reversing gives "Left → Right → Root" = postorder.

Trace for our example tree:
```
1 \ 2 / 3
```

```
stack1 = [1]. stack2 = [].
Pop 1. stack2 = [1]. Push 1.left = null (skip). Push 1.right = 2. stack1 = [2].
Pop 2. stack2 = [1, 2]. Push 2.left = 3. Push 2.right = null (skip). stack1 = [3].
Pop 3. stack2 = [1, 2, 3]. No children to push. stack1 = [].

Reverse stack2 for output: [3, 2, 1]. ✓
```

----------------------------------------

## Step 5: Alternative — Modified Preorder Then Reverse

Equivalent but cleaner:

```
def postorder(root):
    if root is null: return []
    stack = [root]
    result = []
    while stack not empty:
        node = stack.pop()
        result.append(node.val)   # append in "reverse postorder"
        if node.left: stack.push(node.left)
        if node.right: stack.push(node.right)
    return reversed(result)
```

Same idea; no separate second stack. Reverse at the end.

----------------------------------------

## Step 6: One-Stack Elegant Version

This one is trickier but uses no second stack and doesn't reverse:

```
def postorder(root):
    stack = []
    last = null   # last-visited node
    cur = root
    result = []
    
    while cur or stack not empty:
        # go left as far as possible
        while cur:
            stack.push(cur)
            cur = cur.left
        
        peek = stack.top()
        # if right subtree not yet processed, go right
        if peek.right and last != peek.right:
            cur = peek.right
        else:
            # right done (or no right) — visit and mark
            result.append(peek.val)
            last = peek
            stack.pop()
    
    return result
```

`last` tracks which node we most recently visited. If `peek.right` exists and wasn't just visited, we need to recurse into it. Otherwise, the peek's subtrees are fully done — visit peek.

Subtle but beautiful. O(n) time, O(h) stack.

----------------------------------------

## Step 7: Complexity

Time: **O(n)**.
Space: **O(h)** for the stack.

----------------------------------------

## Step 8: C++ Implementation

**Recursive:**

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

**Iterative (modified-preorder + reverse):**

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

The cleanest iterative approach. The critical trick: push left first so right gets processed first, producing "Root, Right, Left" order; reverse to get postorder.

----------------------------------------

## Step 9: Why Postorder Matters

Postorder visits children before parents. Good for:
- **Freeing a tree:** delete children before the parent (else dangling pointers).
- **Computing heights, sums, sizes:** parent needs children's values, which are computed first.
- **Expression tree evaluation:** postorder gives postfix notation.
- **Bottom-up DP:** values at leaves propagate up.

Many tree problems are naturally post-order: diameter, balance check, path sum, LCA via post-order.

----------------------------------------

## Step 10: Follow-up Questions

- **Inorder and preorder iteratively.** Different shapes — preorder is simplest, inorder uses left-spine pushing.
- **Traversal of N-ary tree.** Same patterns with a children loop instead of left/right.
- **Morris postorder.** Exists but quite complex.
- **Serialize/deserialize via postorder.** Requires null markers; reconstruction reads in reverse.
- **Why is postorder trickier than preorder iteratively?** Because children must be processed before the parent, which requires knowing when to "come back" to the parent.
- **Handle traversal of tree that's very deep.** Iterative (especially two-stack) avoids recursion overflow.
