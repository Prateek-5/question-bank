# Merge Two BSTs

## Problem Link
https://leetcode.com/problems/all-elements-in-two-binary-search-trees/

## Topic
Binary Search Tree BST

## Core Concept
Convert to sorted arrays, merge, build balanced BST.

## Intuition
Combine the sorted sequences of both BSTs then reconstruct a balanced BST from the merged sorted array.

## Detailed Explanation
In-order traverse both trees into vectors; merge; build balanced BST using median-picking recursion.

## Dry Run
Tree1 [2,4]; Tree2 [1,3,5]. Merge [1,2,3,4,5]. Build root 3, left 1-2, right 4-5.

## Approach
Three-phase: flatten, merge, rebuild.

## Time and Space Complexity
Time: O(n1+n2). Space: O(n1+n2).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; TreeNode(int x):val(x),left(nullptr),right(nullptr){} };

void io(TreeNode* r, vector<int>& v) { if (!r) return; io(r->left,v); v.push_back(r->val); io(r->right,v); }
TreeNode* build(vector<int>& a, int lo, int hi) {
    if (lo > hi) return nullptr;
    int m = (lo + hi) / 2;
    auto* n = new TreeNode(a[m]);
    n->left = build(a, lo, m-1); n->right = build(a, m+1, hi);
    return n;
}
TreeNode* mergeBSTs(TreeNode* a, TreeNode* b) {
    vector<int> va, vb, merged;
    io(a, va); io(b, vb);
    merge(va.begin(),va.end(),vb.begin(),vb.end(),back_inserter(merged));
    return build(merged, 0, merged.size()-1);
}
```

## Follow-up Questions
- Keep BST structure unchanged (BST iterator merge).
- Remove duplicates during merge.
- Merge k BSTs.
