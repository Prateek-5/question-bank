# Maximum Depth of Binary Tree

## Problem Link
https://leetcode.com/problems/maximum-depth-of-binary-tree/

## Topic
Trees Binary Trees

## Core Concept
1 + max(depth(left), depth(right)).

## Intuition
Depth is the longest root-to-leaf path. Recursion naturally decomposes the problem per subtree.

## Detailed Explanation
Base: null returns 0. Recursive: return 1 + max(depth(left), depth(right)).

## Dry Run
Tree 3,9,20,_,_,15,7. depth(3)=1+max(1,2)=3.

## Approach
Post-order recursion.

## Time and Space Complexity
Time: O(n). Space: O(h).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

int maxDepth(TreeNode* r) {
    if (!r) return 0;
    return 1 + max(maxDepth(r->left), maxDepth(r->right));
}
```

## Follow-up Questions
- Minimum depth of a binary tree.
- Diameter of a binary tree.
- Depth of every node as an array.
