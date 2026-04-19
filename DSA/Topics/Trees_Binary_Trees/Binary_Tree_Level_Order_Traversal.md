# Binary Tree Level Order Traversal

## Problem Link
https://leetcode.com/problems/binary-tree-level-order-traversal/

## Topic
Trees Binary Trees

## Core Concept
BFS using a queue, collecting each level.

## Intuition
Level-by-level iteration — process one level fully before moving to the next. A queue naturally achieves this.

## Detailed Explanation
Push root. While queue non-empty: record current level size; for that many iterations pop, record value, push children. Append level vector to result.

## Dry Run
Tree 3,9,20,_,_,15,7. Levels: [[3],[9,20],[15,7]].

## Approach
BFS with level-size bookkeeping.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

vector<vector<int>> levelOrder(TreeNode* root) {
    vector<vector<int>> res;
    if (!root) return res;
    queue<TreeNode*> q; q.push(root);
    while (!q.empty()) {
        int sz = q.size(); vector<int> level;
        while (sz--) {
            auto* n = q.front(); q.pop();
            level.push_back(n->val);
            if (n->left) q.push(n->left);
            if (n->right) q.push(n->right);
        }
        res.push_back(level);
    }
    return res;
}
```

## Follow-up Questions
- Zigzag level order.
- Bottom-up level order.
- Level order with separators for null.
