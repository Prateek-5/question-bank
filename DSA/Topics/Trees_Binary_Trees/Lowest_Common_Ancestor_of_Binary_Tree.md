# Lowest Common Ancestor of Binary Tree

## Problem Link
https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/

## Topic
Trees Binary Trees

## Core Concept
Post-order recursion — node is LCA if p and q found in different subtrees.

## Intuition
Descend the tree; if both targets appear in different subtrees of a node, that node is their LCA; otherwise propagate the found one upward.

## Detailed Explanation
lca(node): if null or node==p or node==q, return node. L=lca(left); R=lca(right). If both non-null return node; else return the non-null one.

## Dry Run
Tree 3,5,1,..., p=5,q=1. From root: left returns 5, right returns 1 → root=3 is LCA.

## Approach
Post-order propagation.

## Time and Space Complexity
Time: O(n). Space: O(h).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

TreeNode* lowestCommonAncestor(TreeNode* r, TreeNode* p, TreeNode* q) {
    if (!r || r == p || r == q) return r;
    auto* l = lowestCommonAncestor(r->left, p, q);
    auto* R = lowestCommonAncestor(r->right, p, q);
    if (l && R) return r;
    return l ? l : R;
}
```

## Follow-up Questions
- What if p or q may be absent?
- LCA with parent pointers (two-pointer technique).
- Offline LCA queries (Tarjan's).
