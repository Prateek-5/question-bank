# Kth Smallest Element in BST

## Problem Link
https://leetcode.com/problems/kth-smallest-element-in-a-bst/

## Topic
Binary Search Tree BST

## Core Concept
In-order traversal with early termination at k-th visit.

## Intuition
In-order yields sorted values. Stop at the k-th node visited.

## Detailed Explanation
Use an iterative in-order traversal; decrement k on each pop; when k==0, return that node's value.

## Dry Run
BST 3,1,4,_,2, k=1. Push left spine: [3,1]. Pop 1, k=0, return 1.

## Approach
Iterative in-order with stack.

## Time and Space Complexity
Time: O(h+k). Space: O(h).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

int kthSmallest(TreeNode* root, int k) {
    stack<TreeNode*> st;
    TreeNode* cur = root;
    while (cur || !st.empty()) {
        while (cur) { st.push(cur); cur = cur->left; }
        cur = st.top(); st.pop();
        if (--k == 0) return cur->val;
        cur = cur->right;
    }
    return -1;
}
```

## Follow-up Questions
- With frequent modifications — augment nodes with subtree size.
- k-th largest.
- Range count queries.
