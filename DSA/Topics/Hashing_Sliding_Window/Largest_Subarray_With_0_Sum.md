# Largest Subarray With 0 Sum

## Problem Link
https://www.geeksforgeeks.org/problems/largest-subarray-with-0-sum/1

## Topic
Hashing Sliding Window

## Core Concept
Prefix-sum + hashmap of first occurrence.

## Intuition
Subarray with zero sum means two prefix sums are equal. Track earliest index of each sum; at later index compute length.

## Detailed Explanation
m[0]=-1. Running sum; if sum seen earlier update best = i - m[sum]. Else record m[sum]=i.

## Dry Run
arr=[15,-2,2,-8,1,7,10,23]. Prefix sums include a repeat → longest subarray length 5.

## Approach
Hashmap.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int largestZeroSumSubarray(vector<int>& a) {
    unordered_map<int,int> m; m[0] = -1;
    int s = 0, best = 0;
    for (int i = 0; i < (int)a.size(); ++i) {
        s += a[i];
        if (m.count(s)) best = max(best, i - m[s]);
        else m[s] = i;
    }
    return best;
}
```

## Follow-up Questions
- Count zero-sum subarrays.
- Target-sum variant.
- 2D zero sum submatrix.
