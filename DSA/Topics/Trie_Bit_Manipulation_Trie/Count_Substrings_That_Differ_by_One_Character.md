# Count Substrings That Differ by One Character

## Problem Link
https://leetcode.com/problems/count-substrings-that-differ-by-one-character/description/

## Topic
Trie Bit Manipulation Trie

## Core Concept
DP counting matching suffix lengths with a single mismatch.

## Intuition
For each alignment (i, j) in s and t, maintain counts of matching characters before and after a potential mismatch; their product counts substrings ending with the alignment and differing by exactly one.

## Detailed Explanation
For each (i, j), track prev (matching run) and cur (running mismatch-allowed). When s[i]==t[j], cur extends; else reset. Sum prev*cur via careful recurrence over start positions.

## Dry Run
s='aba', t='baba'. Answer = 6.

## Approach
Two DP tables over (i,j).

## Time and Space Complexity
Time: O(|s|·|t|). Space: O(|s|·|t|).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int countSubstrings(string s, string t) {
    int n = s.size(), m = t.size(), res = 0;
    vector<vector<int>> pre(n+1, vector<int>(m+1,0)), suf(n+2, vector<int>(m+2,0));
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) pre[i+1][j+1] = s[i]==t[j] ? pre[i][j]+1 : 0;
    for (int i=n-1;i>=0;i--) for (int j=m-1;j>=0;j--) suf[i][j] = s[i]==t[j] ? suf[i+1][j+1]+1 : 0;
    for (int i=0;i<n;i++) for (int j=0;j<m;j++) if (s[i]!=t[j]) res += (pre[i][j]+1) * (suf[i+1][j+1]+1);
    return res;
}
```

## Follow-up Questions
- Allow k differences.
- Longest common substring with ≤k diffs.
- Case-insensitive variant.
