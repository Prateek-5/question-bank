# Path Sum III

## Problem Link
https://leetcode.com/problems/path-sum-iii/

## Topic
Trees Binary Trees

## Core Concept
Prefix-sum counts on paths — path-sum between any two nodes equals targetSum.

## Intuition
Paths don't need to start at root. Maintain a running prefix sum from root to current; any prefix that differs from current by targetSum defines a valid path ending at current.

## Detailed Explanation
DFS from root. Keep a map: prefixSum → count. On entering node, cur+=node.val. Add count[cur-target] to answer. Increment count[cur]. Recurse. On exit, decrement count[cur].

## Dry Run
Tree 10,5,-3,..., target=8. Count prefixes — multiple paths e.g. 5→3 sums 8, 5→2→1 sums 8. Total 3 paths.

## Approach
Prefix-sum + hashmap, DFS backtrack.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct TreeNode { int val; TreeNode *left,*right; };

class Sol {
    unordered_map<long long,int> cnt;
    long long target;
    int ans = 0;
    void dfs(TreeNode* r, long long cur) {
        if (!r) return;
        cur += r->val;
        ans += cnt[cur - target];
        cnt[cur]++;
        dfs(r->left, cur); dfs(r->right, cur);
        cnt[cur]--;
    }
public:
    int pathSum(TreeNode* root, int t) { target = t; cnt[0] = 1; dfs(root, 0); return ans; }
};
```

## Follow-up Questions
- Paths must have length ≥ k.
- Paths with sum in a range.
- Paths between arbitrary nodes (not just descending).
