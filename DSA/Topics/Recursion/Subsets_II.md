# Subsets II

## Problem Link
https://leetcode.com/problems/subsets-ii/

## Topic
Recursion

## Core Concept
Sort + skip duplicates at same depth.

## Intuition
After sorting, duplicates appear consecutively. Skip them after the first to avoid duplicate subsets.

## Detailed Explanation
Sort. dfs(start): record current. For i=start..n-1: if i>start and a[i]==a[i-1] skip. Push, recurse, pop.

## Dry Run
nums=[1,2,2] → [[],[1],[1,2],[1,2,2],[2],[2,2]].

## Approach
Sorted subset backtracking.

## Time and Space Complexity
Time: O(2^n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
void dfs(vector<int>& a, int s, vector<int>& cur, vector<vector<int>>& res) {
    res.push_back(cur);
    for (int i = s; i < (int)a.size(); ++i) {
        if (i > s && a[i] == a[i-1]) continue;
        cur.push_back(a[i]); dfs(a, i+1, cur, res); cur.pop_back();
    }
}
vector<vector<int>> subsetsWithDup(vector<int>& a) {
    sort(a.begin(), a.end());
    vector<vector<int>> res; vector<int> cur;
    dfs(a, 0, cur, res);
    return res;
}
```

## Follow-up Questions
- Count distinct subsets.
- Fixed-size subsets with duplicates.
- Lexicographic order.
