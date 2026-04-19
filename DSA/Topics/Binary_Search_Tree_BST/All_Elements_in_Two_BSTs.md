# All Elements in Two BSTs

## Problem Link
https://leetcode.com/problems/all-elements-in-two-binary-search-trees/

## Topic
Binary Search Tree BST

## Core Concept
In-order traversal produces sorted arrays; merge both sorted lists.

## Intuition
In-order traversal of a BST yields keys in sorted order. Do it for both trees to get two sorted lists, then merge them like merge-step of merge sort.

## Detailed Explanation
Traverse tree1 in-order into v1; tree2 into v2. Use two pointers to merge into a single sorted list.

## Dry Run
Tree1 in-order: [1,2,4]; Tree2: [0,3,5]. Merge: [0,1,2,3,4,5].

## Approach
Two in-order traversals + linear merge.

## Time and Space Complexity
Time: O(n1+n2). Space: O(n1+n2).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

void inorder(TreeNode* r, vector<int>& v) { if (!r) return; inorder(r->left,v); v.push_back(r->val); inorder(r->right,v); }

vector<int> getAllElements(TreeNode* a, TreeNode* b) {
    vector<int> v1, v2, res;
    inorder(a, v1); inorder(b, v2);
    int i=0, j=0;
    while (i < (int)v1.size() && j < (int)v2.size())
        res.push_back(v1[i] <= v2[j] ? v1[i++] : v2[j++]);
    while (i < (int)v1.size()) res.push_back(v1[i++]);
    while (j < (int)v2.size()) res.push_back(v2[j++]);
    return res;
}
```

## Follow-up Questions
- Do it with O(h) memory using two iterator stacks.
- Intersect keys instead of merging.
- k-th smallest across both BSTs.
