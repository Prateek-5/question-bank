# Binary Tree Preorder Traversal

## Problem Link
https://leetcode.com/problems/binary-tree-preorder-traversal/

## Topic
Trees Binary Trees

## Core Concept
Root-left-right traversal.

## Intuition
Preorder gives the root before children — suitable for tree copy/serialize.

## Detailed Explanation
Push current value, recurse left, recurse right.

## Dry Run
Tree 1,_,2,3. Preorder: 1,2,3.

## Approach
Recursion or iterative stack pushing right first.

## Time and Space Complexity
Time: O(n). Space: O(h).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

void pr(TreeNode* r, vector<int>& v) { if (!r) return; v.push_back(r->val); pr(r->left,v); pr(r->right,v); }
vector<int> preorderTraversal(TreeNode* root) { vector<int> v; pr(root, v); return v; }
```

## Follow-up Questions
- Iterative preorder with stack.
- Morris preorder.
- Threaded binary tree traversals.
