# Binary Tree Inorder Traversal

## Problem Link
https://leetcode.com/problems/binary-tree-inorder-traversal/

## Topic
Trees Binary Trees

## Core Concept
Recursive left-root-right traversal.

## Intuition
In-order visits left subtree, then node, then right subtree — yielding sorted order in a BST.

## Detailed Explanation
Recurse on left, push current value, recurse on right.

## Dry Run
Tree 1,_,2,3. In-order: 1,3,2.

## Approach
Simple recursion; iterative via stack also common.

## Time and Space Complexity
Time: O(n). Space: O(h).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

void io(TreeNode* r, vector<int>& v) { if (!r) return; io(r->left, v); v.push_back(r->val); io(r->right, v); }
vector<int> inorderTraversal(TreeNode* root) { vector<int> v; io(root, v); return v; }
```

## Follow-up Questions
- Iterative inorder using stack.
- Morris inorder in O(1) space.
- BFS inorder for threaded trees.
