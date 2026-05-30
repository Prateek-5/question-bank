# Range Sum of BST

**Problem Link:**
<a href="https://leetcode.com/problems/range-sum-of-bst/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/range-sum-of-bst/</a>

**Topic:**
Binary Search Tree (BST)

----------------------------------------

## Step 1: Understand the Task

Given the root of a **Binary Search Tree** and two integers `low` and `high`, return the **sum of values** of all nodes whose value is in the range [low, high] inclusive.

Example:
```
        10
       /  \
      5   15
     / \    \
    3   7   18
```
low = 7, high = 15.

Nodes with values in [7, 15]: 7, 10, 15. Sum = 32.

Easy enough if we just traverse everything and sum matches. The question is whether we can do better.

----------------------------------------

## Step 2: Naive Approach

Visit every node. If value is in [low, high], add to sum.

```
def rangeSum(node, low, high):
    if node is null: return 0
    s = 0
    if low <= node.val <= high: s += node.val
    return s + rangeSum(node.left, low, high) + rangeSum(node.right, low, high)
```

O(n). Works on any binary tree (BST or not).

But we have a BST here — that means **order**. Can we prune branches we don't need to visit?

----------------------------------------

## Step 3: Leverage the BST Property for Pruning

BST property: for any node with value v, everything in its **left subtree** is < v, and everything in its **right subtree** is > v.

Now think about the current node:
- If `node.val < low`: all values in the left subtree are also < low (strictly less than v, which is already < low). No nodes in [low, high] exist in the left subtree. **Skip left.**
- If `node.val > high`: all values in the right subtree are > node.val > high. **Skip right.**
- If node.val is in range: include it. Both subtrees might contain more in-range values; recurse into both.
- Regardless of whether node is in range, we might have in-range values on the opposite side:
  - If node.val < low: there could be values in [low, high] in the right subtree (values > node.val, possibly in range). Recurse right.
  - If node.val > high: there could be in-range values in the left subtree. Recurse left.
  - If in range: recurse both.

So the refined algorithm:
```
def rangeSum(node, low, high):
    if node is null: return 0
    if node.val < low:  return rangeSum(node.right, low, high)
    if node.val > high: return rangeSum(node.left,  low, high)
    # in range
    return node.val + rangeSum(node.left, low, high) + rangeSum(node.right, low, high)
```

Each case makes exactly one or two recursive calls — the ones that **might** contain in-range values. The pruned subtrees are guaranteed to contain nothing useful, so skipping them is safe.

----------------------------------------

## Step 4: Trace on the Example

Tree (same as above), low=7, high=15.

```
rangeSum(10):
  10 in [7, 15]. Include 10. Recurse both.
  rangeSum(5):
    5 < 7. Skip left. Recurse right only.
    rangeSum(7):
      7 in [7, 15]. Include 7. Recurse both (but 7 has no children).
      Sub-recursions on null return 0.
      Return 7.
    Return 7.
  rangeSum(15):
    15 in [7, 15]. Include 15. Recurse both.
    rangeSum(null left). Return 0.
    rangeSum(18):
      18 > 15. Skip right. Recurse left only.
      rangeSum(null). Return 0.
      Return 0.
    Return 15 + 0 + 0 = 15.
  Return 10 + 7 + 15 = 32.
```

Result: **32**. ✓

Notice how we never visited nodes 3 and 18 (beyond confirming their positions). Node 3 is in the left subtree of 5, but we pruned it. Node 18 was visited but contributed nothing because its only meaningful path (left) leads to null.

For a balanced BST where the range is narrow, pruning skips most nodes.

----------------------------------------

## Step 5: Why Pruning Is Safe

**Claim:** if `node.val < low`, nothing in the left subtree is ≥ low.

**Proof:** BST property says everything in the left subtree is < node.val. And node.val < low. So everything in the left subtree is < low. None are in range. ✓

Symmetric argument for `node.val > high`.

This is the structural reason BSTs are more efficient than unsorted trees for range queries: we can discard entire branches based on a single comparison.

----------------------------------------

## Step 6: Complexity

Worst case (e.g., range covers everything): **O(n)** — same as naive.

Best/common case: when the range is narrow, we touch only **O(log n + k)** nodes (k = nodes in range) for balanced trees.

Space: O(h) for recursion stack, where h = tree height.

----------------------------------------

## Step 7: Name It

This is **BST range query with pruning**. The technique generalizes:
- Count of nodes in range: same pruning, return 1 instead of node.val.
- Smallest in range: same pruning, return first in-range value encountered via in-order traversal.
- Product in range: swap sum for product.

The BST property lets every range query operation leverage the "discard entire subtree" trick. This is what makes balanced BSTs (like std::set and std::map) fast for range operations.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int rangeSumBST(TreeNode* root, int low, int high) {
    if (!root) return 0;
    if (root->val < low) return rangeSumBST(root->right, low, high);
    if (root->val > high) return rangeSumBST(root->left, low, high);
    return root->val + rangeSumBST(root->left, low, high) + rangeSumBST(root->right, low, high);
}
```

Six lines. The three cases directly implement the pruning.

Iterative version with a stack:

```cpp
int rangeSumBST(TreeNode* root, int low, int high) {
    int sum = 0;
    stack<TreeNode*> stk;
    if (root) stk.push(root);
    while (!stk.empty()) {
        TreeNode* node = stk.top(); stk.pop();
        if (!node) continue;
        if (node->val < low) {
            if (node->right) stk.push(node->right);
        } else if (node->val > high) {
            if (node->left) stk.push(node->left);
        } else {
            sum += node->val;
            if (node->left) stk.push(node->left);
            if (node->right) stk.push(node->right);
        }
    }
    return sum;
}
```

Useful when recursion depth could be large. Same pruning logic.

----------------------------------------

## Step 9: Follow-up Questions

- **Count nodes in range instead of summing.** Return 1 instead of node.val; same algorithm.
- **List nodes in range, sorted.** Do an in-order traversal with pruning; collect in-range values.
- **Find k-th smallest value in range.** In-order with pruning and a counter.
- **Range sum in an augmented BST with subtree-sum cache.** Each node stores `subtree_sum`; range sum computed in O(log² n) via predecessor/successor arithmetic.
- **If we allow duplicates, does the algorithm still work?** Yes — duplicates in BST are typically placed consistently (say, right subtree), and the comparisons still correctly prune.
- **What about non-BST trees?** The pruning relies on BST property. Without it, we must traverse everything (O(n)).
