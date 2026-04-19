# Maximum Product of Three Numbers

## Problem Link
https://leetcode.com/problems/maximum-product-of-three-numbers/

## Topic
Greedy

## Core Concept
Consider either the top 3 or the two smallest (negatives) × the largest.

## Intuition
Maximum product uses either three largest positives or two largest-magnitude negatives plus the biggest positive.

## Detailed Explanation
Sort. Return max(nums[n-1]*nums[n-2]*nums[n-3], nums[0]*nums[1]*nums[n-1]).

## Dry Run
nums=[-10,-10,1,3,2]. Sorted: [-10,-10,1,2,3]. top3: 1*2*3=6. neg2*max: -10*-10*3=300 → answer 300.

## Approach
Sort + compare two candidates.

## Time and Space Complexity
Time: O(n log n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int maximumProduct(vector<int>& a) {
    sort(a.begin(), a.end());
    int n = a.size();
    return max(a[n-1]*a[n-2]*a[n-3], a[0]*a[1]*a[n-1]);
}
```

## Follow-up Questions
- O(n) single pass tracking top3/bottom2.
- Product of k numbers — DP or careful greedy.
- Subarray product maximum.
