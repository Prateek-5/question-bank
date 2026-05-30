# Binary Tree Left Side View

**Problem Link:**
<a href="https://www.geeksforgeeks.org/print-left-view-binary-tree/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/print-left-view-binary-tree/</a>

**Topic:**
Binary Search Tree (BST)

----------------------------------------

## Step 1: Visualize Looking from the Left

Stand to the **left** of a binary tree. What nodes do you see? At each depth level, you see the **leftmost** node — the others are blocked behind it.

Return the list of visible values, top to bottom.

Example:
```
       1
      / \
     2   3
      \   \
       5   4
```

- Level 0: see 1.
- Level 1: 2 is leftmost. See 2.
- Level 2: 5 is left-of 4 (5 is at column 2, 4 is at column 4 say; 5 comes first). See 5.

Result: `[1, 2, 5]`.

Another:
```
     1
      \
       2
        \
         3
```

All nodes are on the right spine, but each level has only one node. From the left, we see that one node at each level: [1, 2, 3].

"Leftmost per level" is key. It's symmetric to Right Side View.

----------------------------------------

## Step 2: BFS by Level — First Node Per Level

Standard BFS with level-size tracking. For each level, pop all nodes; the **first** popped is the leftmost.

```
def leftView(root):
    result = []
    if root is null: return result
    q = [root]
    while q not empty:
        level_size = len(q)
        for i in 0..level_size-1:
            node = q.pop_front()
            if i == 0:
                result.append(node.val)
            if node.left: q.push(node.left)
            if node.right: q.push(node.right)
    return result
```

Each iteration of the outer while processes one level. The first dequeue per level is the leftmost at that level.

----------------------------------------

## Step 3: DFS Alternative — Left-First Preorder

Same shape as Right Side View's DFS alternative, but recurse **left first**.

```
def leftView(root):
    result = []
    def dfs(node, depth):
        if node is null: return
        if len(result) == depth:
            result.append(node.val)   # first to arrive at this depth
        dfs(node.left, depth + 1)
        dfs(node.right, depth + 1)
    dfs(root, 0)
    return result
```

Since we recurse left first, the **first** node visited at each depth is the leftmost. Check "have we recorded anything at this depth yet?" via `len(result) == depth`.

Both BFS and DFS give the same output.

----------------------------------------

## Step 4: Trace on the Example

```
       1
      / \
     2   3
      \   \
       5   4
```

**BFS:**
```
q=[1]. result=[].

Level 0 (size=1):
  i=0: pop 1. i==0, append. result=[1]. Push children (no left, right=3). Actually wait — 1 has left=2, right=3. Push 2, push 3.
q=[2, 3].

Wait I mis-wrote the tree. Let me reread: "1 /(2) \(3); 2 has right 5; 3 has right 4." So 1.left=2, 1.right=3.

Level 0 revised: pop 1, append to result. Push 2, 3. q=[2, 3].

Level 1 (size=2):
  i=0: pop 2. i==0, append. result=[1, 2]. Push 2.left (null, skip), 2.right = 5. q=[3, 5].
  i=1: pop 3. Not first. Push 3.left (null), 3.right = 4. q=[5, 4].

Level 2 (size=2):
  i=0: pop 5. i==0, append. result=[1, 2, 5]. No children.
  i=1: pop 4. Not first. No children.

q=[]. Done.
```

result = [1, 2, 5]. ✓

----------------------------------------

## Step 5: Why Both Approaches Work

**BFS:** processes nodes level by level. The queue's front at the start of each level is the leftmost.

**DFS with left-first recursion:** descends leftmost first, so the first node encountered at each depth is the leftmost.

Both are O(n).

----------------------------------------

## Step 6: Name It

**Left-side view of a binary tree.** Symmetric to the right-side view. Together they describe the "silhouette" of the tree.

Related:
- Binary Tree Top View.
- Binary Tree Bottom View.
- Boundary of Binary Tree (top + right + bottom + left).

All use the same level-awareness ideas with different picks.

----------------------------------------

## Step 7: Complexity

Time: **O(n)** — each node visited once.
Space: O(h) for DFS stack, O(level-width) for BFS queue. Worst case O(n).

----------------------------------------

## Step 8: C++ Implementation

**BFS:**

```cpp
vector<int> leftSideView(TreeNode* root) {
    vector<int> result;
    if (!root) return result;
    queue<TreeNode*> q;
    q.push(root);
    while (!q.empty()) {
        int levelSize = q.size();
        for (int i = 0; i < levelSize; ++i) {
            TreeNode* node = q.front(); q.pop();
            if (i == 0) result.push_back(node->val);
            if (node->left) q.push(node->left);
            if (node->right) q.push(node->right);
        }
    }
    return result;
}
```

**DFS:**

```cpp
class Solution {
    vector<int> result;
    void dfs(TreeNode* node, int depth) {
        if (!node) return;
        if ((int)result.size() == depth) result.push_back(node->val);
        dfs(node->left, depth + 1);
        dfs(node->right, depth + 1);
    }
public:
    vector<int> leftSideView(TreeNode* root) {
        dfs(root, 0);
        return result;
    }
};
```

Both work; pick whichever feels natural.

----------------------------------------

## Step 9: Follow-up Questions

- **Top view.** Track horizontal distance from root; for each distance, remember the first node encountered (smallest depth).
- **Bottom view.** Track horizontal distance; remember the last node (largest depth) or just the latest seen.
- **Right side view.** Symmetric: pick last per level.
- **Diagonal traversal.** Group nodes by some diagonal key.
- **Return all nodes at a specific level.** Stop BFS at that level; return the dequeued set.
- **Streaming tree.** BFS adapts naturally as levels arrive.
