# Binary Tree Right Side View

## Problem Link
https://leetcode.com/problems/binary-tree-right-side-view/

## Topic
Binary Search Tree BST

## Core Concept
BFS level-order, pick last node of each level.

## Intuition
Right view shows the rightmost node at each depth.

## Detailed Explanation
Level-by-level BFS; in each level push only the last node's value. Alternatively reverse-preorder DFS.

## Dry Run
Tree 1,2,3,_,5,_,4. Levels [1],[2,3],[5,4]. Right view: [1,3,4].

## Approach
BFS level size.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

vector<int> rightSideView(TreeNode* root) {
    vector<int> res;
    if (!root) return res;
    queue<TreeNode*> q; q.push(root);
    while (!q.empty()) {
        int sz = q.size();
        for (int i = 0; i < sz; ++i) {
            auto* n = q.front(); q.pop();
            if (i == sz - 1) res.push_back(n->val);
            if (n->left) q.push(n->left);
            if (n->right) q.push(n->right);
        }
    }
    return res;
}
```

## Follow-up Questions
- Variation: both left and right views combined.
- Column-wise view.
- Top view.
