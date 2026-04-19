# Construct Binary Tree from Traversals

## Problem Link
https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/

## Topic
Binary Search Tree BST

## Core Concept
Reconstruct from preorder+inorder (or postorder+inorder) using index split.

## Intuition
Preorder's first element is the root. Locate it in inorder to split left/right subtrees' sizes. Recurse on the two halves.

## Detailed Explanation
Build a map value→index in inorder for O(1) lookup. Maintain a preorder pointer. In build(lo, hi): root = preorder[p++]; split at inorderIndex[root]; build left then right.

## Dry Run
pre=[3,9,20,15,7], in=[9,3,15,20,7]. root=3, split at idx 1. Left in [9] → root 9. Right in [15,20,7] → root 20, etc.

## Approach
Recursive construction with hash map.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; TreeNode(int x):val(x),left(nullptr),right(nullptr){} };

class Sol {
    unordered_map<int,int> idx;
    vector<int> pre;
    int p = 0;
    TreeNode* build(int lo, int hi) {
        if (lo > hi) return nullptr;
        int v = pre[p++];
        auto* n = new TreeNode(v);
        n->left = build(lo, idx[v]-1);
        n->right = build(idx[v]+1, hi);
        return n;
    }
public:
    TreeNode* buildTree(vector<int>& preorder, vector<int>& inorder) {
        pre = preorder;
        for (int i = 0; i < (int)inorder.size(); ++i) idx[inorder[i]] = i;
        return build(0, inorder.size()-1);
    }
};
```

## Follow-up Questions
- Build from inorder + postorder.
- Build from preorder + postorder (ambiguous — may need BST assumption).
- Serialize/deserialize.
