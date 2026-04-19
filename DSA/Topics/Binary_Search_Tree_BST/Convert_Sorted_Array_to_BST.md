# Convert Sorted Array to BST

## Problem Link
https://leetcode.com/problems/convert-sorted-array-to-binary-search-tree/

## Topic
Binary Search Tree BST

## Core Concept
Divide and conquer — middle element becomes root, recurse on halves.

## Intuition
A balanced BST emerges when we always pick the median of the current range as root; its left half forms the left subtree, right half the right subtree.

## Detailed Explanation
Function build(lo, hi): if lo>hi return null; mid=(lo+hi)/2; node = nums[mid]; node.left = build(lo, mid-1); node.right = build(mid+1, hi). Returns a height-balanced BST.

## Dry Run
nums=[-10,-3,0,5,9]. mid=2→0. Left [-10,-3] mid→-10 then -3 as right. Right [5,9] similarly. Height 3.

## Approach
Recursive median picking.

## Time and Space Complexity
Time: O(n). Space: O(log n) recursion.

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; TreeNode(int x):val(x),left(nullptr),right(nullptr){} };

TreeNode* build(vector<int>& a, int lo, int hi) {
    if (lo > hi) return nullptr;
    int mid = (lo + hi) / 2;
    auto* n = new TreeNode(a[mid]);
    n->left = build(a, lo, mid - 1);
    n->right = build(a, mid + 1, hi);
    return n;
}
TreeNode* sortedArrayToBST(vector<int>& a) { return build(a, 0, a.size() - 1); }
```

## Follow-up Questions
- Convert sorted linked list to BST (O(n) with in-order build).
- Weight-balanced variant.
- Iterative approach.
