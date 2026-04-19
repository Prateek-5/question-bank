# Balanced Binary Tree

**Problem Link:**
https://leetcode.com/problems/balanced-binary-tree/

**Topic:**
Trees / Binary Trees

----------------------------------------

## Step 1: Decode the Definition

A tree is called **height-balanced** if for **every** node, the heights of its left and right subtrees differ by at most 1. Return true or false accordingly.

Two important words: "every" and "heights". The condition must hold at every node, not just at the root. And "height" is the usual depth — the length of the longest path from that node down to a leaf.

Example of a balanced tree:
```
      3
     / \
    9   20
        / \
       15  7
```
Every node's left and right heights differ by at most 1. Balanced.

Example of an unbalanced tree:
```
      1
     /
    2
   /
  3
```
At node 1, left height = 2, right height = 0. Difference = 2 > 1. Unbalanced.

----------------------------------------

## Step 2: A First Attempt

The most direct translation of the definition:

```cpp
int height(TreeNode* n) {
    if (!n) return 0;
    return 1 + max(height(n->left), height(n->right));
}

bool isBalanced(TreeNode* n) {
    if (!n) return true;
    if (abs(height(n->left) - height(n->right)) > 1) return false;
    return isBalanced(n->left) && isBalanced(n->right);
}
```

This works. But let me trace the work being done. At the root, we compute the heights of both subtrees — each is O(n) in the worst case. Then we recurse into each subtree, and at each of those we again compute heights of *their* subtrees. That's a lot of re-traversal.

In the worst case (a skewed tree), this is O(n²). For n = 10^4, that's 10^8 — slow. For n = 10^5, way too slow.

The fix is to compute the height and check balance **in the same pass**. That's where a clever recursive trick comes in.

----------------------------------------

## Step 3: The Insight — One Function, Two Jobs

Instead of having two separate functions (one that returns height, one that checks balance), let's have **one** function that returns the height **unless** we've detected an imbalance somewhere below, in which case we signal "not balanced."

How do we signal that with a single integer return value? Use a **sentinel**: return `-1` when the subtree is unbalanced. A real height is always ≥ 0, so -1 can't collide.

The recursion then looks like:

```
check(node):
    if node is null: return 0
    lh = check(node.left)
    if lh == -1: return -1       # already unbalanced below; propagate up
    rh = check(node.right)
    if rh == -1: return -1
    if |lh - rh| > 1: return -1  # current node is unbalanced
    return 1 + max(lh, rh)
```

Two things happen in one pass:
1. We compute the height.
2. We detect imbalance and short-circuit up the call stack.

At the root, if `check(root) != -1`, the tree is balanced.

----------------------------------------

## Step 4: Why It's Now O(n)

Each node is visited exactly once, with O(1) work. Total: O(n). The early termination is a nice bonus but isn't needed for correctness.

Contrast with the naïve version where we were re-traversing subtrees. The insight wasn't a fancier algorithm — it was **merging the two concerns (height + balance) into one post-order pass**. This pattern appears often: "compute a value AND a flag together, so you don't retraverse."

----------------------------------------

## Step 5: Trace a Balanced Example

```
      3
     / \
    9   20
        / \
       15  7
```

```
check(3):
  check(9):
    check(null) = 0, check(null) = 0.
    |0 - 0| ≤ 1. return 1.
  check(20):
    check(15):
      null, null, return 1.
    check(7):
      null, null, return 1.
    |1 - 1| ≤ 1. return 2.
  |1 - 2| ≤ 1. return 3.
```

Returned 3 (not -1) → balanced. ✓

And an unbalanced case:
```
  1
 /
2
 \
  3
```

```
check(1):
  check(2):
    check(null) = 0.
    check(3):
      null, null, return 1.
    |0 - 1| ≤ 1. return 2.
  check(null) = 0.
  |2 - 0| = 2 > 1. return -1.
```

-1 at the root → not balanced. ✓

The propagation via -1 stops us from doing any more useless work once we've detected imbalance.

----------------------------------------

## Step 6: Complexity

Time: one post-order visit per node, O(1) work at each. **O(n)**.
Space: recursion stack up to the tree's height. **O(h)**.

From O(n²) down to O(n). The whole gain comes from computing height and checking balance in the same traversal.

----------------------------------------

## Step 7: C++ Implementation

```cpp
int check(TreeNode* n) {
    if (!n) return 0;
    int l = check(n->left);
    if (l == -1) return -1;
    int r = check(n->right);
    if (r == -1) return -1;
    if (abs(l - r) > 1) return -1;
    return 1 + max(l, r);
}

bool isBalanced(TreeNode* root) {
    return check(root) != -1;
}
```

Two small habits to notice. First, we propagate the `-1` immediately — no need to recurse into the right subtree if the left is already broken. Second, the wrapper `isBalanced` just translates the sentinel into a boolean so the interface is clean.

----------------------------------------

## Step 8: Follow-up Questions

- **Balanced within some threshold k (not just 1).** Replace `> 1` with `> k`. Same structure.
- **Return the smallest subtree that is unbalanced.** Modify the recursion to pass back a pointer; short-circuit to capture it.
- **Check AVL invariant — each node stores its own height.** Traverse and verify `stored_height == 1 + max(l, r)` at every node.
- **Convert an unbalanced BST to a balanced one.** In-order traversal to a sorted array, then median-based reconstruction (this is the Convert Sorted Array to BST pattern).
- **Weight-balanced check (sub-tree node counts, not heights).** Same technique, but return node count instead of height and compare.
