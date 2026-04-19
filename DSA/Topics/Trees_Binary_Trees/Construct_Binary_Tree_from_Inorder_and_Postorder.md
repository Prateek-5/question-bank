# Construct Binary Tree from Inorder & Postorder

## Problem Link
https://leetcode.com/problems/construct-binary-tree-from-inorder-and-postorder-traversal/

## Topic
Trees Binary Trees

## Core Concept
Postorder's last element is root; split inorder around it.

## Intuition
Similar to preorder+inorder but process postorder right-to-left (building right subtree first).

## Detailed Explanation
Map inorder value→index. Use postorder pointer p from end. In build(lo, hi): v=post[p--]; root=v; build right first (idx+1..hi) then left (lo..idx-1).

## Dry Run
in=[9,3,15,20,7], post=[9,15,7,20,3]. root=3, split at 1. Right in [15,20,7] root=20, etc.

## Approach
Recursive with postorder pointer and hashmap.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; TreeNode(int x):val(x),left(nullptr),right(nullptr){} };

class Sol {
    unordered_map<int,int> idx;
    vector<int> post;
    int p;
    TreeNode* build(int lo, int hi) {
        if (lo > hi) return nullptr;
        int v = post[p--];
        auto* n = new TreeNode(v);
        n->right = build(idx[v]+1, hi);
        n->left = build(lo, idx[v]-1);
        return n;
    }
public:
    TreeNode* buildTree(vector<int>& inorder, vector<int>& postorder) {
        post = postorder; p = post.size() - 1;
        for (int i = 0; i < (int)inorder.size(); ++i) idx[inorder[i]] = i;
        return build(0, inorder.size()-1);
    }
};
```

## Follow-up Questions
- Build from pre+post (ambiguous).
- Check that arrays are valid traversals.
- Serialize the reconstructed tree.
