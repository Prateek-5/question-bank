# Permutations II

## Problem Link
https://leetcode.com/problems/permutations-ii/

## Topic
Recursion

## Core Concept
Sorted backtracking with used[] skipping sibling duplicates.

## Intuition
To avoid duplicate permutations, ensure duplicates are chosen in order by skipping a duplicate whose twin hasn't been used yet at the same level.

## Detailed Explanation
Sort. dfs with used[]; for i: if used[i] or (i>0 && a[i]==a[i-1] && !used[i-1]) skip.

## Dry Run
nums=[1,1,2] → 3 unique perms.

## Approach
Sorted dfs with used-array rule.

## Time and Space Complexity
Time: O(n!·n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
void dfs(vector<int>& a, vector<bool>& used, vector<int>& cur, vector<vector<int>>& res) {
    if (cur.size() == a.size()) { res.push_back(cur); return; }
    for (int i = 0; i < (int)a.size(); ++i) {
        if (used[i]) continue;
        if (i > 0 && a[i] == a[i-1] && !used[i-1]) continue;
        used[i] = true; cur.push_back(a[i]);
        dfs(a, used, cur, res);
        cur.pop_back(); used[i] = false;
    }
}
vector<vector<int>> permuteUnique(vector<int>& a) {
    sort(a.begin(), a.end());
    vector<vector<int>> res; vector<int> cur; vector<bool> used(a.size(), false);
    dfs(a, used, cur, res);
    return res;
}
```

## Follow-up Questions
- Lexicographic order.
- Unrank permutations.
- Count distinct permutations.
