# Longest Substring Without Repeating Characters

## Problem Link
https://leetcode.com/problems/longest-substring-without-repeating-characters/

## Topic
Hashing Sliding Window

## Core Concept
Sliding window with char→last-index map.

## Intuition
Maintain a window [l, r] with distinct chars. When a repeat enters at r, jump l to the position after the previous occurrence of that char.

## Detailed Explanation
For each r: if last[c]>=l, l=last[c]+1. Update last[c]=r; track max window size.

## Dry Run
s='abcabcbb'. Windows 'abc','bca','cab','abc','cb','b' → max length 3.

## Approach
Sliding window.

## Time and Space Complexity
Time: O(n). Space: O(Σ).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int lengthOfLongestSubstring(string s) {
    vector<int> last(256, -1);
    int l = 0, best = 0;
    for (int r = 0; r < (int)s.size(); ++r) {
        if (last[s[r]] >= l) l = last[s[r]] + 1;
        last[s[r]] = r;
        best = max(best, r - l + 1);
    }
    return best;
}
```

## Follow-up Questions
- At most k distinct chars.
- With repeating but ≤ k times each.
- Longest unique substring in a stream.
