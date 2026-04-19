# Maximum Depth of Binary Tree

**Problem Link:**
https://leetcode.com/problems/maximum-depth-of-binary-tree/

**Topic:**
Trees / Binary Trees

----------------------------------------

## Step 1: What Is Being Asked

Given the root of a binary tree, return its **maximum depth** — the length of the longest root-to-leaf path, counted in nodes. An empty tree has depth 0. A single-node tree has depth 1.

Example:
```
        3
       / \
      9   20
          / \
         15  7
```
The longest path is `3 → 20 → 15` or `3 → 20 → 7`, each three nodes long. Depth = **3**.

Nothing tricky about the definition. What's tricky is computing it cleanly.

----------------------------------------

## Step 2: A Natural Intuition

If I know the depth of the left subtree and the depth of the right subtree, what's the depth of the whole tree?

- If both subtrees are empty, the tree is a single node → depth 1.
- If left has depth `L` and right has depth `R`, the longest root-to-leaf path goes through whichever subtree is deeper. So the tree's depth is `1 + max(L, R)`.

That's the whole recurrence:

```
depth(tree) = 0                       if tree is null
            = 1 + max(depth(left), depth(right))   otherwise
```

Simple. Let me make sure I believe it with small cases.

- Empty tree: depth = 0. ✓
- Single node: left and right are null, each depth 0. Tree depth = 1 + max(0, 0) = 1. ✓
- Two nodes `1 → 2 (left only)`: depth(2) = 1. depth(1) = 1 + max(1, 0) = 2. ✓
- The example above: depth(9) = 1. depth(15) = depth(7) = 1. depth(20) = 1 + max(1, 1) = 2. depth(3) = 1 + max(1, 2) = 3. ✓

The recurrence holds and suggests an algorithm that recurses into children and combines their answers.

----------------------------------------

## Step 3: Why This Works — An Induction in Disguise

The claim: for any tree, `depth(t) = 1 + max(depth(t.left), depth(t.right))` correctly returns the longest root-to-leaf path length.

**Base case:** empty tree returns 0.

**Inductive step:** assume it works for all smaller trees (both subtrees). Every root-to-leaf path starts at the root, goes into one of its children, and continues to a leaf. The path length is 1 (for the root) plus the length of the path from that child to a leaf. Summing over both children and taking max gives the longest path through the root. That's `1 + max(depth(left), depth(right))`.

So by induction, the formula is correct for all finite trees. The recursion mirrors the induction.

----------------------------------------

## Step 4: Writing It As Code

```cpp
int maxDepth(TreeNode* root) {
    if (!root) return 0;
    return 1 + max(maxDepth(root->left), maxDepth(root->right));
}
```

Three lines. The recursion does exactly what the recurrence says.

Trace on the example:

```
maxDepth(3):
  maxDepth(9):
    maxDepth(null left) = 0
    maxDepth(null right) = 0
    return 1 + max(0, 0) = 1
  maxDepth(20):
    maxDepth(15):
      null children → returns 1
    maxDepth(7):
      null children → returns 1
    return 1 + max(1, 1) = 2
  return 1 + max(1, 2) = 3
```

That's **3**. ✓

----------------------------------------

## Step 5: What About Iterative?

The recursive version is elegant but uses O(h) stack space (h = tree height). For extremely deep trees (imagine a linked-list-shaped tree with a million nodes), that could overflow.

An iterative BFS version counts levels one at a time:

```cpp
int maxDepth(TreeNode* root) {
    if (!root) return 0;
    queue<TreeNode*> q;
    q.push(root);
    int depth = 0;
    while (!q.empty()) {
        int sz = q.size();
        while (sz--) {
            auto* n = q.front(); q.pop();
            if (n->left) q.push(n->left);
            if (n->right) q.push(n->right);
        }
        depth++;
    }
    return depth;
}
```

Every full cycle of the outer while processes one "level" of the tree and increments `depth`. When the queue is empty, we've counted all levels.

BFS uses O(w) space where w is the max width of the tree. For balanced trees w ≈ n/2. For deeply unbalanced trees, w is small. Pick whichever space profile fits your input.

----------------------------------------

## Step 6: Complexity

Time: every node is visited exactly once. **O(n)**.

Space (recursive): **O(h)** for the call stack — O(log n) for balanced, O(n) worst case for a skewed tree.

Space (iterative BFS): **O(w)** where w is the max level width. O(n) worst case.

----------------------------------------

## Step 7: C++ Implementation

Recursive (preferred for clarity):
```cpp
int maxDepth(TreeNode* root) {
    if (!root) return 0;
    return 1 + max(maxDepth(root->left), maxDepth(root->right));
}
```

----------------------------------------

## Step 8: Follow-up Questions

- **Minimum depth of a binary tree.** Similar recurrence, but be careful — a node with only one child has depth equal to `1 + that child's min depth`, not `1 + min(0, thatDepth)`, because the null side isn't a valid leaf.
- **Diameter of a binary tree.** Longest path between any two nodes, which might *not* go through the root. Post-order trick: each node returns its height and updates a global max = `leftHeight + rightHeight`.
- **Balanced binary tree check.** Post-order returning -1 as a "balance broken" sentinel, else the height. If we ever see -1 from a subtree, propagate up.
- **Average level depth.** BFS level by level; aggregate per-level averages.
- **Serialize and deserialize a binary tree.** Traversal design matters for round-tripping.
