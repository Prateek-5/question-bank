# Trees / Binary Trees — Concepts

## Core Theory
Binary trees represent hierarchical data with each node having up to two children. Traversals are the main tool: preorder, inorder, postorder (DFS) and level-order (BFS). Many problems reduce to post-order aggregation from children.

## Common Patterns
- **Post-order aggregation** (height, diameter, balanced check, path sum).
- **Pre-order / BFS serialization**.
- **Divide-and-conquer reconstruction** from two traversals (preorder+inorder, etc.).
- **DFS with state** (level, sum, path) for depth-related queries.

## When to Use
For hierarchical data, decision trees, expression parsing, or whenever divide-and-conquer via subtree structure fits.

## Template
```cpp
struct TreeNode { int val; TreeNode *left, *right; };
int height(TreeNode* r) { return r ? 1 + max(height(r->left), height(r->right)) : 0; }
```

## Common Mistakes
- Forgetting null checks before dereferencing children.
- Confusing in-order and pre-order during reconstruction.
- Stack overflow on deep skewed trees — prefer iterative or Morris traversal.
