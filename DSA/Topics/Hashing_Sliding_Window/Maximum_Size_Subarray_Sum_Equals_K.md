# Maximum Size Subarray Sum Equals K

## Problem Link
https://leetcode.com/problems/maximum-size-subarray-sum-equals-k/

## Topic
Hashing Sliding Window

## Core Concept
Prefix-sum + hashmap of first occurrence.

## Intuition
If prefix[j] - prefix[i] = k, subarray (i,j] sums to k. Track earliest index per prefix value to maximize length.

## Detailed Explanation
Map m[0] = -1. Iterate with cumulative sum; if (sum-k) in m, update best length = i - m[sum-k]. Record first sum occurrence.

## Dry Run
nums=[1,-1,5,-2,3], k=3. Prefix sums 1,0,5,3,6. Check each; best length 4.

## Approach
Hashmap of prefix sums.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int maxSubArrayLen(vector<int>& a, int k) {
    unordered_map<long long,int> m; m[0] = -1;
    long long s = 0; int best = 0;
    for (int i = 0; i < (int)a.size(); ++i) {
        s += a[i];
        if (m.count(s - k)) best = max(best, i - m[s - k]);
        if (!m.count(s)) m[s] = i;
    }
    return best;
}
```

## Follow-up Questions
- Count subarrays summing to k.
- Longest subarray with sum ≤ k.
- 2D variant.
