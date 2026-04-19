# Binary Tree Postorder Traversal

## Problem Link
https://leetcode.com/problems/binary-tree-postorder-traversal/

## Topic
Trees Binary Trees

## Core Concept
Left-right-root traversal.

## Intuition
Postorder yields children before parents — useful for delete/free and dependency processing.

## Detailed Explanation
Recurse left, recurse right, then push current value.

## Dry Run
Tree 1,_,2,3. Postorder: 3,2,1.

## Approach
Recursion; iterative using two-stack trick or modified preorder reversed.

## Time and Space Complexity
Time: O(n). Space: O(h).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

void po(TreeNode* r, vector<int>& v) { if (!r) return; po(r->left,v); po(r->right,v); v.push_back(r->val); }
vector<int> postorderTraversal(TreeNode* root) { vector<int> v; po(root, v); return v; }
```

## Follow-up Questions
- Iterative with stack.
- Level-order reverse.
- Morris postorder (trickier).
