# Path Sum II

## Problem Link
https://leetcode.com/problems/path-sum-ii/

## Topic
Trees Binary Trees

## Core Concept
Backtracking along root-to-leaf paths collecting matches.

## Intuition
Extend Path Sum by recording the current path. On a leaf with the target sum met, snapshot the path.

## Detailed Explanation
DFS with a running vector. On entry push node. On leaf with remaining sum zero, copy path to result. On exit pop node.

## Dry Run
Tree similar; collect each root-to-leaf path equaling target.

## Approach
Backtracking DFS.

## Time and Space Complexity
Time: O(n²) worst case. Space: O(h).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

void dfs(TreeNode* r, int s, vector<int>& cur, vector<vector<int>>& res) {
    if (!r) return;
    cur.push_back(r->val);
    if (!r->left && !r->right && s == r->val) res.push_back(cur);
    dfs(r->left, s - r->val, cur, res);
    dfs(r->right, s - r->val, cur, res);
    cur.pop_back();
}
vector<vector<int>> pathSum(TreeNode* r, int s) { vector<vector<int>> res; vector<int> cur; dfs(r, s, cur, res); return res; }
```

## Follow-up Questions
- Count paths with sum ≤ target.
- Paths of exactly k edges.
- Tolerate negative values (already works).
