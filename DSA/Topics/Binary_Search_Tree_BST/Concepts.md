# Binary Search Tree (BST) — Concepts Guide

----------------------------------------

## 1. Introduction

A Binary Search Tree is a tree where every node's value is greater than everything in its left subtree and less than everything in its right subtree. That simple rule gives us O(log n) search, insert, and delete *on average* — plus the ability to traverse keys in sorted order without sorting. BSTs are the bridge between trees (structural thinking) and sorted arrays (ordered access).

----------------------------------------

## 2. Real-Life Analogy

Think of a well-organized library where books are placed by their dewey decimal number. To find a specific book, you don't scan every shelf — you navigate to the right section first, then the right row. That's exactly what a BST does: at every node, you decide 'left or right' based on how the target compares, and you eliminate half the remaining possibilities with each step.

----------------------------------------

## 3. Core Idea

The BST invariant — left < node < right for every node — is powerful because it creates a globally sorted structure from local comparisons. In-order traversal (left, root, right) visits nodes in sorted order, which turns many questions into 'walk the BST in sorted order and do X'. Balanced BSTs (AVL, red-black) enforce O(log n) height; unbalanced BSTs can degrade to O(n) (essentially a linked list), which is why production code almost always uses a balanced variant.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Reach for a BST (or a built-in balanced equivalent like `std::set`/`std::map`) when you need:

- **Sorted iteration** combined with dynamic insert/delete.
- **Nearest predecessor or successor** of a value.
- **Range queries** (all keys in [lo, hi]).
- **K-th smallest/largest** with changes over time.
- **Ordered statistics** — rank of an element, element at a rank.

If you only need unordered membership tests, use a hash set instead — it's O(1) on average.

----------------------------------------

## 5. Types / Variations

- **Unbalanced BST:** simple to implement, can degrade to O(n) height.
- **Balanced BSTs:** AVL trees (rigid balance), red-black trees (looser balance, used in `std::set`), splay trees (self-adjusting).
- **Augmented BST:** store extra info per node (subtree size, subtree sum) to support rank/select queries in O(log n).
- **B-tree:** generalization with more than two children per node — used in databases and filesystems.

----------------------------------------

## 6. Step-by-Step Working

**Search(node, key):**
1. If node is null, return null.
2. If key == node.val, return node.
3. If key < node.val, recurse on node.left.
4. Else recurse on node.right.

**Insert(node, key):**
1. If node is null, create and return a new node.
2. If key < node.val, node.left = insert(node.left, key).
3. Else node.right = insert(node.right, key).
4. Return node.

**In-order traversal (gives sorted order):**
1. Recurse on left.
2. Visit current.
3. Recurse on right.

----------------------------------------

## 7. Visual Explanation

**BST after inserting 5, 3, 7, 1, 4, 6, 8:**

```
         5
       /   \
      3     7
     / \   / \
    1   4 6   8
```

**In-order traversal visits:** 1 → 3 → 4 → 5 → 6 → 7 → 8 (sorted!).

**Searching for 4:** compare 4 with 5 (go left) → compare with 3 (go right) → compare with 4 (found).

Notice we only looked at 3 of the 7 nodes. That's the O(log n) magic of a balanced tree.

----------------------------------------

## 8. Code Templates (C++)

```cpp
struct TreeNode {
    int val;
    TreeNode *left, *right;
    TreeNode(int x): val(x), left(nullptr), right(nullptr) {}
};

TreeNode* insert(TreeNode* root, int v) {
    if (!root) return new TreeNode(v);
    if (v < root->val) root->left = insert(root->left, v);
    else root->right = insert(root->right, v);
    return root;
}

bool search(TreeNode* root, int v) {
    while (root) {
        if (v == root->val) return true;
        root = v < root->val ? root->left : root->right;
    }
    return false;
}

// In-order iterator (stack-based, O(1) amortized next)
class BSTIterator {
    stack<TreeNode*> st;
    void pushLeft(TreeNode* n) { while (n) { st.push(n); n = n->left; } }
public:
    BSTIterator(TreeNode* root) { pushLeft(root); }
    bool hasNext() { return !st.empty(); }
    int next() {
        TreeNode* n = st.top(); st.pop();
        pushLeft(n->right);
        return n->val;
    }
};
```

----------------------------------------

## 9. Common Mistakes

- **Assuming the tree is balanced.** Worst-case height can be O(n) for an unbalanced BST.
- **Deletion is subtle** — particularly when removing a node with two children (use in-order successor or predecessor).
- **Duplicate keys policy must be explicit** — left? right? skip? — decide before coding.
- **Recursive traversals stack-overflowing** on deep trees — prefer iterative when depth can be large.
- **Confusing BST invariant with heap invariant** — they are different. BSTs are ordered left-to-right; heaps are ordered root-to-children.

----------------------------------------

## 10. Interview Insights

BST problems check whether you can exploit the ordering invariant rather than treating the tree as an arbitrary binary tree. Interviewers want to see:

1. **Do you use the BST property?** Walking into a BST question and doing a full tree traversal when O(log n) was possible signals you missed the point.
2. **Can you reason about in-order traversal?** Many problems become trivial once you realize in-order yields a sorted sequence.
3. **Can you handle balance and worst cases?** Follow-up questions often ask about balanced trees.
4. **Do you know when *not* to use a BST?** If you just need membership, a hash set is better.

Mantra: 'If the problem mentions a BST, the first question to ask yourself is — does the BST property let me skip half the tree?' Usually the answer is yes.
