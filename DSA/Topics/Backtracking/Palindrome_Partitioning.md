# Palindrome Partitioning

## Problem Link
https://leetcode.com/problems/palindrome-partitioning/

## Topic
Backtracking

## Core Concept
Backtracking with palindrome check on each prefix.

## Intuition
For each cut point, if the prefix is a palindrome, recurse on the suffix. Collect all decompositions.

## Detailed Explanation
dfs(start): if start==n record current. For end=start..n-1: if s.substr(start, end-start+1) palindrome, push, recurse with end+1, pop.

## Dry Run
s='aab' → [['a','a','b'],['aa','b']].

## Approach
DFS with palindrome check.

## Time and Space Complexity
Time: O(2^n·n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
bool pal(const string& s, int l, int r) { while (l<r) if (s[l++]!=s[r--]) return false; return true; }
void dfs(const string& s, int i, vector<string>& cur, vector<vector<string>>& res) {
    if (i == (int)s.size()) { res.push_back(cur); return; }
    for (int j = i; j < (int)s.size(); ++j) if (pal(s, i, j)) {
        cur.push_back(s.substr(i, j - i + 1));
        dfs(s, j + 1, cur, res);
        cur.pop_back();
    }
}
vector<vector<string>> partition(string s) { vector<vector<string>> res; vector<string> cur; dfs(s, 0, cur, res); return res; }
```

## Follow-up Questions
- Minimum cuts (DP).
- Count distinct palindromic partitions.
- Palindromic substring DP preprocessing.
