# Lowest Common Ancestor of BST

## Problem Link
https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/

## Topic
Binary Search Tree BST

## Core Concept
Walk down the BST using BST property until p and q split.

## Intuition
If both p and q are smaller than current, go left. If both are bigger, go right. Otherwise current is the split point — their LCA.

## Detailed Explanation
Iteratively traverse from root. Compare values: if p.val < cur.val and q.val < cur.val go left; if both > cur.val go right; else return cur.

## Dry Run
BST root=6, p=2, q=4. 2<6, 4<6 → go left to 2. Then 2==cur → return 2.

## Approach
Top-down pointer walk.

## Time and Space Complexity
Time: O(h). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

TreeNode* lowestCommonAncestor(TreeNode* root, TreeNode* p, TreeNode* q) {
    while (root) {
        if (p->val < root->val && q->val < root->val) root = root->left;
        else if (p->val > root->val && q->val > root->val) root = root->right;
        else return root;
    }
    return nullptr;
}
```

## Follow-up Questions
- Normal binary tree LCA.
- LCA with parent pointers.
- Persistent LCA queries.
