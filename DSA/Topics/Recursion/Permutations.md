# Permutations

## Problem Link
https://leetcode.com/problems/permutations/

## Topic
Recursion

## Core Concept
Backtracking swapping in place.

## Intuition
At each recursion level pick an element for the current position by swapping from remaining.

## Detailed Explanation
bt(s): if s==n record current. For i from s to n-1: swap(s,i); bt(s+1); swap back.

## Dry Run
nums=[1,2,3] → 6 perms.

## Approach
In-place recursion.

## Time and Space Complexity
Time: O(n!·n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
void bt(vector<int>& a, int s, vector<vector<int>>& res) {
    if (s == (int)a.size()) { res.push_back(a); return; }
    for (int i = s; i < (int)a.size(); ++i) { swap(a[s], a[i]); bt(a, s+1, res); swap(a[s], a[i]); }
}
vector<vector<int>> permute(vector<int>& nums) {
    vector<vector<int>> res; bt(nums, 0, res); return res;
}
```

## Follow-up Questions
- Permutations II (with duplicates).
- Next permutation.
- k-th permutation sequence.
