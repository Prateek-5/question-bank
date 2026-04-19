# Combination Sum II

## Problem Link
https://leetcode.com/problems/combination-sum-ii/

## Topic
Recursion

## Core Concept
Backtracking over sorted candidates; skip duplicates.

## Intuition
Each candidate used at most once — sort and, during recursion, skip sibling duplicates at the same depth.

## Detailed Explanation
Sort. dfs(start, remaining, path). For i from start: if i>start and c[i]==c[i-1] skip. If c[i]>remaining break. Recurse with i+1 and remaining-c[i].

## Dry Run
c=[10,1,2,7,6,1,5], target=8 → [[1,1,6],[1,2,5],[1,7],[2,6]].

## Approach
Sorted backtracking with dup pruning.

## Time and Space Complexity
Time: O(2^n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
void dfs(vector<int>& c, int s, int t, vector<int>& cur, vector<vector<int>>& res) {
    if (t == 0) { res.push_back(cur); return; }
    for (int i = s; i < (int)c.size(); ++i) {
        if (i > s && c[i] == c[i-1]) continue;
        if (c[i] > t) break;
        cur.push_back(c[i]);
        dfs(c, i+1, t - c[i], cur, res);
        cur.pop_back();
    }
}
vector<vector<int>> combinationSum2(vector<int>& c, int t) {
    sort(c.begin(), c.end());
    vector<vector<int>> res; vector<int> cur;
    dfs(c, 0, t, cur, res);
    return res;
}
```

## Follow-up Questions
- With repetition allowed (Combination Sum).
- Count rather than list.
- Lexicographic order variants.
