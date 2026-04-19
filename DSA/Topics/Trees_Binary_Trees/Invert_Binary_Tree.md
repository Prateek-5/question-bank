# Invert Binary Tree

## Problem Link
https://leetcode.com/problems/invert-binary-tree/

## Topic
Trees Binary Trees

## Core Concept
Recursively swap left and right at every node.

## Intuition
Mirroring the tree means left↔right swap at each node. Apply recursively in any order.

## Detailed Explanation
invert(node): if null return null; swap node->left and node->right; recurse on both. Return node.

## Dry Run
Tree 4,2,7,1,3,6,9. Swap becomes 4,7,2,9,6,3,1.

## Approach
Recursion or BFS iterative swap.

## Time and Space Complexity
Time: O(n). Space: O(h).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

TreeNode* invertTree(TreeNode* root) {
    if (!root) return nullptr;
    swap(root->left, root->right);
    invertTree(root->left); invertTree(root->right);
    return root;
}
```

## Follow-up Questions
- Invert only specific levels.
- Check if a tree equals its mirror.
- Convert tree to its mirror iteratively.
