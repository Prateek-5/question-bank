# Minimum Window Substring

## Problem Link
https://leetcode.com/problems/minimum-window-substring/

## Topic
Hashing Sliding Window

## Core Concept
Sliding window with required-char count.

## Intuition
Expand r until the window contains all chars of t; then contract l to shrink while still valid. Track smallest.

## Detailed Explanation
Maintain need[] of counts from t and have[]; cnt of matched distinct chars. Expand r incrementing; when matched equals required distinct, try shrinking by incrementing l and updating best.

## Dry Run
s='ADOBECODEBANC', t='ABC'. Smallest window 'BANC' length 4.

## Approach
Two-pointer sliding window.

## Time and Space Complexity
Time: O(n). Space: O(Σ).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
string minWindow(string s, string t) {
    vector<int> need(256, 0);
    for (char c : t) need[c]++;
    int required = 0;
    for (int x : need) if (x) required++;
    vector<int> have(256, 0);
    int matched = 0, l = 0, bestL = 0, bestLen = INT_MAX;
    for (int r = 0; r < (int)s.size(); ++r) {
        char c = s[r]; have[c]++;
        if (need[c] > 0 && have[c] == need[c]) matched++;
        while (matched == required) {
            if (r - l + 1 < bestLen) { bestLen = r - l + 1; bestL = l; }
            char d = s[l++]; have[d]--;
            if (need[d] > 0 && have[d] < need[d]) matched--;
        }
    }
    return bestLen == INT_MAX ? "" : s.substr(bestL, bestLen);
}
```

## Follow-up Questions
- Window covering at least k chars of each.
- Minimum window subsequence.
- Smallest window in a stream.
