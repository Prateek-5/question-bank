# Subarray Sum Equals K

## Problem Link
https://leetcode.com/problems/subarray-sum-equals-k/

## Topic
Hashing Sliding Window

## Core Concept
Prefix-sum + hashmap counting.

## Intuition
#subarrays ending at i with sum k equals count of previous prefix sums equal to current-k.

## Detailed Explanation
m[0]=1; run sum; ans += m[sum-k]; ++m[sum].

## Dry Run
nums=[1,1,1], k=2. Sums 1,2,3. ans=2.

## Approach
Hashmap prefix counts.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int subarraySum(vector<int>& a, int k) {
    unordered_map<int,int> m; m[0] = 1;
    int s = 0, ans = 0;
    for (int x : a) { s += x; ans += m[s - k]; m[s]++; }
    return ans;
}
```

## Follow-up Questions
- Longest subarray sum = k.
- Count subarrays divisible by k.
- 2D version.
