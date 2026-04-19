# Balanced Binary Tree

## Problem Link
https://leetcode.com/problems/balanced-binary-tree/

## Topic
Trees Binary Trees

## Core Concept
Post-order DFS returning height, propagating -1 on imbalance.

## Intuition
A tree is balanced if every node's two subtree heights differ by at most 1. Compute heights bottom-up and short-circuit when imbalance detected.

## Detailed Explanation
h(node): if null return 0. l=h(left); r=h(right). If l==-1 or r==-1 or |l-r|>1 return -1. Else return max(l,r)+1. Overall balanced iff h(root)!=-1.

## Dry Run
Tree 3,9,20,_,_,15,7. h(9)=1,h(15)=1,h(7)=1,h(20)=2,h(3)=3. No imbalance → balanced.

## Approach
Single post-order traversal, short-circuit via sentinel.

## Time and Space Complexity
Time: O(n). Space: O(h).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

int h(TreeNode* r) {
    if (!r) return 0;
    int l = h(r->left); if (l == -1) return -1;
    int rr = h(r->right); if (rr == -1) return -1;
    if (abs(l - rr) > 1) return -1;
    return max(l, rr) + 1;
}
bool isBalanced(TreeNode* root) { return h(root) != -1; }
```

## Follow-up Questions
- Balanced within k instead of 1.
- Weight-balanced tree check.
- Convert unbalanced tree to balanced.
