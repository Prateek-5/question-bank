# Path Sum

## Problem Link
https://leetcode.com/problems/path-sum/

## Topic
Trees Binary Trees

## Core Concept
DFS decrementing target along root-to-leaf paths.

## Intuition
Check if any root-to-leaf path sums to target. At each node, subtract its value and recurse; at a leaf, check if remaining equals zero.

## Detailed Explanation
hasPath(node, sum): if null return false. If leaf: return node.val == sum. Else return hasPath(left, sum-node.val) || hasPath(right, sum-node.val).

## Dry Run
Tree 5,4,8,11,_,13,4,7,2, target=22. Path 5→4→11→2 sums 22 → true.

## Approach
Recursion.

## Time and Space Complexity
Time: O(n). Space: O(h).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

bool hasPathSum(TreeNode* r, int s) {
    if (!r) return false;
    if (!r->left && !r->right) return s == r->val;
    return hasPathSum(r->left, s - r->val) || hasPathSum(r->right, s - r->val);
}
```

## Follow-up Questions
- Return the path values.
- Count all paths with sum = target.
- Path from any node to any descendant.
