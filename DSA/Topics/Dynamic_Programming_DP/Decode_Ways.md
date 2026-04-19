# Decode Ways

## Problem Link
https://leetcode.com/problems/decode-ways/

## Topic
Dynamic Programming DP

## Core Concept
DP over string index — valid one-digit and two-digit decodings.

## Intuition
At position i, ways(i) = ways(i+1) if s[i] is valid (1–9) + ways(i+2) if s[i..i+1] is valid (10–26).

## Detailed Explanation
dp[i] = (s[i]!='0' ? dp[i+1] : 0) + (valid(s[i..i+1]) ? dp[i+2] : 0). Base dp[n]=1.

## Dry Run
'226'. dp[3]=1. dp[2]=1 (from 6). dp[1]=dp[2]+dp[3]=2 (2 or 26). dp[0]=dp[1]+dp[2]=3.

## Approach
Bottom-up DP.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int numDecodings(string s) {
    int n = s.size();
    if (n == 0 || s[0] == '0') return 0;
    int two = 1, one = 1;
    for (int i = 1; i < n; ++i) {
        int cur = 0;
        if (s[i] != '0') cur += one;
        int v = (s[i-1]-'0')*10 + (s[i]-'0');
        if (v >= 10 && v <= 26) cur += two;
        two = one; one = cur;
    }
    return one;
}
```

## Follow-up Questions
- Decode Ways II (wildcard '*').
- Count unique decoded strings.
- Decoding with a custom alphabet.
