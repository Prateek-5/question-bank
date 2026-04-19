# Lowest Common Ancestor of BST

**Problem Link:**
https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/

**Topic:**
Binary Search Tree (BST)

----------------------------------------

## Step 1: Recall LCA

Given a BST and two of its nodes `p` and `q`, return the **lowest common ancestor**: the deepest node that has both `p` and `q` in its subtree (where a node can be a descendant of itself).

Example BST:
```
        6
       / \
      2   8
     / \ / \
    0  4 7  9
      / \
     3   5
```

- LCA(2, 8) = 6. (Both descend from 6; neither is an ancestor of the other.)
- LCA(2, 4) = 2. (2 is an ancestor of 4, so 2 is their LCA.)
- LCA(3, 5) = 4.

The "lowest" means we don't just return any ancestor — we want the deepest one.

----------------------------------------

## Step 2: Forget BST for a Moment — How Would We Solve for a Generic Binary Tree?

For a **general** binary tree (no ordering), LCA takes a recursive post-order walk. At each node, we check whether p or q was found in the left subtree vs the right. If found in different subtrees, this node is the LCA. If both in one subtree, the LCA is deeper in that subtree. That's O(n).

But here we have a **BST** — a much stronger structural property. The question is: does the BST property let us do better?

----------------------------------------

## Step 3: Use the BST Property

The defining BST property: for any node N with value v, every node in N's left subtree has value < v, every node in N's right subtree has value > v.

Consider the root. Where could p and q be relative to root's value?

**Case A: both p and q have values less than root.val.**
Both live in the root's left subtree. The LCA is deeper in the left subtree. Recurse left.

**Case B: both p and q have values greater than root.val.**
Symmetric. Recurse right.

**Case C: p and q are on opposite sides of root** (one less, one greater), **or one of them equals root**.
The root is their LCA! Here's why:
- If they're on opposite sides, the root is the "split point" — any deeper node would be in only one of the sides, losing access to the other.
- If one of them is the root itself, the root is an ancestor of itself, and the other is somewhere below, making root the LCA.

That's it. Three cases, and in each one we either recurse into exactly one subtree or return the current node. We descend at most the tree's height — **O(h)**.

This is a huge improvement over the generic binary-tree approach because we never visit both subtrees at the same level. The BST ordering tells us which side to go.

----------------------------------------

## Step 4: Trace on the Example

LCA(2, 4) in the example tree.

```
At root 6:
  p.val=2, q.val=4. Both < 6. Recurse left.

At node 2:
  p.val=2 equals current (special case — it's on both sides or is root).
  p=current → return 2.
```

Result: 2. ✓

LCA(3, 5):

```
At root 6:
  p.val=3, q.val=5. Both < 6. Recurse left.

At node 2:
  p.val=3, q.val=5. Both > 2. Recurse right.

At node 4:
  p.val=3 < 4, q.val=5 > 4. Split! Return 4.
```

Result: 4. ✓

LCA(2, 8):

```
At root 6:
  p.val=2 < 6, q.val=8 > 6. Split! Return 6.
```

Result: 6. ✓

All correct in at most 3 steps each — very efficient.

----------------------------------------

## Step 5: Iterative Version

Because the recursion always recurses into exactly one subtree, we can unroll it into a loop:

```
cur = root
while cur:
    if p.val < cur.val and q.val < cur.val: cur = cur.left
    elif p.val > cur.val and q.val > cur.val: cur = cur.right
    else: return cur
```

Constant space, equally fast. Many interviewers prefer this form because it highlights the O(h) descent without recursion overhead.

----------------------------------------

## Step 6: Why This Doesn't Work on Non-BST Trees

Without the BST ordering, `p.val < cur.val` tells us nothing about whether p is in the left or right subtree. Values could be anywhere. So for general binary trees we have no choice but to explore both subtrees — the O(n) approach.

The BST property is a very specific type of "sorted" structure, and this problem showcases how much it simplifies traversal when you can use it.

----------------------------------------

## Step 7: Name It

This is the **LCA-in-BST algorithm** — a focused specialization of generic tree-LCA that leverages the ordering invariant. It generalizes to any "ordered tree" problems where comparing values tells you which direction to go.

Related:
- LCA in generic binary tree: O(n) post-order approach.
- LCA with parent pointers: walk both p and q up to collect ancestors, find the deepest common one.
- Range-based LCA via Euler tour + RMQ: O(1) per query after O(n log n) preprocessing.

----------------------------------------

## Step 8: Complexity

Time: **O(h)** where h is the tree height. Balanced BST → O(log n); skewed → O(n).
Space: **O(1)** iterative, **O(h)** recursive (stack).

----------------------------------------

## Step 9: C++ Implementation

Iterative (preferred):

```cpp
TreeNode* lowestCommonAncestor(TreeNode* root, TreeNode* p, TreeNode* q) {
    while (root) {
        if (p->val < root->val && q->val < root->val) {
            root = root->left;
        } else if (p->val > root->val && q->val > root->val) {
            root = root->right;
        } else {
            return root;
        }
    }
    return nullptr;   // unreachable if p, q are in the tree
}
```

Recursive:

```cpp
TreeNode* lowestCommonAncestor(TreeNode* root, TreeNode* p, TreeNode* q) {
    if (p->val < root->val && q->val < root->val)
        return lowestCommonAncestor(root->left, p, q);
    if (p->val > root->val && q->val > root->val)
        return lowestCommonAncestor(root->right, p, q);
    return root;
}
```

Both are concise. The iterative uses O(1) stack space; the recursive is a bit more declarative.

----------------------------------------

## Step 10: Follow-up Questions

- **LCA in a general (non-BST) binary tree.** Different algorithm — post-order recursion that returns "found a target" status from each side.
- **If the tree has duplicate values.** The BST invariant becomes ambiguous. Handle with care; usually problem statements promise distinct values.
- **If we don't know whether p and q are both in the tree.** The algorithm above might return a wrong node. Add a post-check: verify both are descendants of the returned node.
- **If only values are given (not nodes), and the tree is a general BT.** We'd first search for p and q to get their nodes, then find LCA.
- **What if the BST is very unbalanced?** O(h) could be O(n). AVL or red-black trees would guarantee O(log n).
