# Longest Increasing Subsequence

## Problem Link
https://leetcode.com/problems/longest-increasing-subsequence/

## Topic
Dynamic Programming DP

## Core Concept
Patience sorting / binary search for O(n log n).

## Intuition
Keep tails[i] = smallest possible tail of an LIS of length i+1. For each number, replace the first tail ≥ number via lower_bound — or append if all smaller.

## Detailed Explanation
For each x in nums: position = lower_bound(tails.begin(),tails.end(),x); if position==end append else replace. Length of tails is LIS length.

## Dry Run
nums=[10,9,2,5,3,7,101,18]. tails evolves [10]→[9]→[2]→[2,5]→[2,3]→[2,3,7]→[2,3,7,101]→[2,3,7,18]. LIS=4.

## Approach
Patience sorting.

## Time and Space Complexity
Time: O(n log n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int lengthOfLIS(vector<int>& nums) {
    vector<int> t;
    for (int x : nums) {
        auto it = lower_bound(t.begin(), t.end(), x);
        if (it == t.end()) t.push_back(x); else *it = x;
    }
    return t.size();
}
```

## Follow-up Questions
- Print the LIS.
- Non-decreasing variant (upper_bound).
- Weighted LIS.
