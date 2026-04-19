# Subsets

## Problem Link
https://leetcode.com/problems/subsets/

## Topic
Recursion

## Core Concept
Backtracking including/excluding each index.

## Intuition
Each element is either chosen or not — binary tree of choices yields 2^n subsets.

## Detailed Explanation
dfs(start): record current. For i from start: push, dfs(i+1), pop.

## Dry Run
nums=[1,2,3] → 8 subsets.

## Approach
Classical subset backtracking.

## Time and Space Complexity
Time: O(2^n·n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
void dfs(vector<int>& a, int s, vector<int>& cur, vector<vector<int>>& res) {
    res.push_back(cur);
    for (int i = s; i < (int)a.size(); ++i) { cur.push_back(a[i]); dfs(a, i+1, cur, res); cur.pop_back(); }
}
vector<vector<int>> subsets(vector<int>& a) { vector<vector<int>> res; vector<int> cur; dfs(a, 0, cur, res); return res; }
```

## Follow-up Questions
- Subsets with duplicates (II).
- Bitmask enumeration.
- Iterative generation by doubling.
