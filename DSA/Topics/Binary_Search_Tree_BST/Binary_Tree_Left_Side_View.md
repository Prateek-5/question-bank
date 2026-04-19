# Binary Tree Left Side View

## Problem Link
https://leetcode.com/problems/binary-tree-left-side-view/

## Topic
Binary Search Tree BST

## Core Concept
BFS level-order, pick first node of each level; or DFS tracking depth.

## Intuition
The left view shows the first node visible from the left at each depth — the leftmost node per level.

## Detailed Explanation
BFS level-by-level: push the first node dequeued per level. DFS approach: pre-order with depth; record node if depth matches result size.

## Dry Run
Tree 1,2,3,4,_,_,5. Levels: [1],[2,3],[4,5]. Left view: [1,2,4].

## Approach
BFS level size tracking.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

vector<int> leftSideView(TreeNode* root) {
    vector<int> res;
    if (!root) return res;
    queue<TreeNode*> q; q.push(root);
    while (!q.empty()) {
        int sz = q.size();
        for (int i = 0; i < sz; ++i) {
            auto* n = q.front(); q.pop();
            if (i == 0) res.push_back(n->val);
            if (n->left) q.push(n->left);
            if (n->right) q.push(n->right);
        }
    }
    return res;
}
```

## Follow-up Questions
- Bottom view; top view using column indexing.
- Right view by picking the last node per level.
- Boundary traversal.
