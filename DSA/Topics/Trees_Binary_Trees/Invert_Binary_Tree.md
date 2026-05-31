# Invert Binary Tree

**Problem Link:**
<a href="https://leetcode.com/problems/invert-binary-tree/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/invert-binary-tree/</a>

**Topic:**
Trees / Binary Trees

----------------------------------------

## Step 1: What Does "Invert" Mean?

"Invert" means produce the **mirror image** of the tree. Every node's left subtree becomes its right subtree, and vice versa.

Example:

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

It's as if the tree were reflected across a vertical line through the root.

----------------------------------------

## Step 2: Small Cases to Build Feel

**Empty tree:** the inverted version is also empty. Nothing to do.

**Single node:** inverting a single node yields the same single node. Nothing to do.

**Two nodes, `1 → 2 (left only)`:**
```
  1         1
 /    →      \
2             2
```
After inverting, the left child should become the right child. `1.right = 1.left; 1.left = null`.

**Three nodes, full tree `1 / 2, 3`:**
```
  1         1
 / \   →   / \
2   3     3   2
```
We swap `1.left` and `1.right`.

The first thing I notice: at the root, we need to **swap children**. Is that enough? For this three-node example, yes, because the children are leaves. For larger trees, we also have to invert everything deeper — each internal node needs its children swapped too.

----------------------------------------

## Step 3: The Recursive Insight

The tree is defined recursively: a node and two subtrees. To invert the whole tree, we need to:

1. Swap the root's children.
2. Invert the left subtree (which is the old right subtree after the swap).
3. Invert the right subtree.

The order of steps 1, 2, 3 doesn't matter much, because the swap is just a pointer reassignment, and inverting a subtree is independent of its sibling. So this works:

```
invert(node):
    if node is null: return null
    left_inverted  = invert(node.left)
    right_inverted = invert(node.right)
    node.left  = right_inverted
    node.right = left_inverted
    return node
```

Or equivalently, do the swap first then recurse — same result.

Let me verify with the small tree `1 / 2, 3`:

```
invert(1):
  invert(2): no children, returns 2.
  invert(3): no children, returns 3.
  node.left = 3, node.right = 2.
```

Tree becomes `1 / 3, 2`. ✓

And for the big example:

```
invert(4):
  invert(2):
    invert(1) → 1
    invert(3) → 3
    2.left = 3, 2.right = 1.
    return 2.
  invert(7):
    invert(6) → 6
    invert(9) → 9
    7.left = 9, 7.right = 6.
    return 7.
  4.left = 7, 4.right = 2.
  return 4.
```

Final:
```
        4
       / \
      7   2
     / \ / \
    9  6 3  1
```



----------------------------------------

## Step 4: Why It Works — Structural Induction

**Claim:** the above `invert` correctly mirrors any binary tree.

**Base case:** `invert(null)` returns null — a null tree is its own mirror.

**Inductive step:** assume `invert` correctly mirrors any smaller tree (both subtrees of the current node). Then the mirror of a tree rooted at `node` is a tree where:
- The left subtree is the mirror of the old right subtree.
- The right subtree is the mirror of the old left subtree.

Our code computes `invert(node.right)` → mirror of old right, places it at `node.left`. Symmetric for the other side. Matches the definition of mirror. ✓

----------------------------------------

## Step 5: A One-Liner Version

We can simplify by swapping before recursion:

```cpp
TreeNode* invertTree(TreeNode* root) {
    if (!root) return nullptr;
    swap(root->left, root->right);
    invertTree(root->left);
    invertTree(root->right);
    return root;
}
```

The `swap` runs first, then the children (now in their new positions) are recursively inverted. Same effect, slightly shorter.

----------------------------------------

## Step 6: Iterative Alternative via BFS

If the tree is very tall (skewed), recursion might overflow the stack. Use BFS instead:

```cpp
TreeNode* invertTree(TreeNode* root) {
    if (!root) return nullptr;
    queue<TreeNode*> q;
    q.push(root);
    while (!q.empty()) {
        auto* n = q.front(); q.pop();
        swap(n->left, n->right);
        if (n->left) q.push(n->left);
        if (n->right) q.push(n->right);
    }
    return root;
}
```

Same outcome. The order of visits changes (level-by-level instead of depth-first), but since every node's swap is local and independent, the final tree is identical.

----------------------------------------

## Step 7: Complexity

Time: each node is visited once and its children are swapped in O(1). **O(n)**.

Space: recursive version uses O(h) stack, where h is the tree's height (O(log n) balanced, O(n) skewed). Iterative BFS uses O(w) queue space where w is the max level width.

----------------------------------------

## Step 8: C++ Implementation

```cpp
TreeNode* invertTree(TreeNode* root) {
    if (!root) return nullptr;
    swap(root->left, root->right);
    invertTree(root->left);
    invertTree(root->right);
    return root;
}
```

----------------------------------------

## Step 9: Follow-up Questions

- **Check whether a tree equals its own mirror (symmetric tree).** Two recursive calls that walk one tree and its mirror in sync, comparing values at each pair of nodes.
- **Invert only the subtree rooted at a specific node.** Find the node, invert from there.
- **Produce a new inverted tree without modifying the original.** Allocate new nodes in the recursion — return `new TreeNode(val, invert(right), invert(left))`.
- **Invert in constant memory (no recursion, no queue).** Morris-like traversal — possible but fiddly; rarely asked.
- **N-ary tree inversion.** Reverse the children array at each node, then recurse.


---

## Interview Signals (from LeetLens)

This problem (or close variants) was reported in **2 real interview(s)** in the LeetLens dataset (snapshot 2026-05-31). Pay attention to the company context when practicing.

| Company | Difficulty | LeetLens ID | Match | Variant note |
|---|---|---|---|---|
| Meta | Easy | `f34bd300` | 1.00 (exact-title) | Invert Binary Tree |
| Meta | Medium | `4b9a5637` | 1.00 (exact-title) | Invert Binary Tree |

_Source: LeetLens DB. Match methods: `substring` = direct hit; `token-coverage` = ≥70% of this card's filename tokens appear in the question; `jaccard`/`ratio` = fuzzy title similarity._
_See the parent folder's `EXTRACTED_QUESTIONS.md` §2 for the full list of incorporated questions._
