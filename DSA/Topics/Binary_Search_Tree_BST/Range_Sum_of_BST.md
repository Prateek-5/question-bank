# Range Sum of BST

## Problem Link
https://leetcode.com/problems/range-sum-of-bst/

## Topic
Binary Search Tree BST

## Core Concept
DFS pruning using BST property.

## Intuition
Use BST structure to skip subtrees outside [L,R]. If current < L, only right subtree matters; if > R, only left.

## Detailed Explanation
rangeSum(node): if null 0; if val < L return rangeSum(right); if val > R return rangeSum(left); else val + rangeSum(left) + rangeSum(right).

## Dry Run
BST 10,5,15,3,7,_,18, L=7,R=15. 10 in range → add 10+rs(5)+rs(15). rs(5): 5<7 → rs(7)=7. rs(15)→15+rs(_)+rs(18, 18>15 →rs(left)=0)=15. Total 32.

## Approach
Recursive pruning.

## Time and Space Complexity
Time: O(n) worst, O(h+k) with skew. Space: O(h).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

int rangeSumBST(TreeNode* r, int L, int R) {
    if (!r) return 0;
    if (r->val < L) return rangeSumBST(r->right, L, R);
    if (r->val > R) return rangeSumBST(r->left, L, R);
    return r->val + rangeSumBST(r->left, L, R) + rangeSumBST(r->right, L, R);
}
```

## Follow-up Questions
- Count nodes in range.
- Range sum with frequent updates — augmented BST.
- K-th element in range.
