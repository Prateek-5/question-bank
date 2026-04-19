# Maximize Sum After K Negations

## Problem Link
https://leetcode.com/problems/maximize-sum-of-array-after-k-negations/

## Topic
Greedy

## Core Concept
Always flip the smallest element; parity determines final move.

## Intuition
Flipping the smallest maximizes gain if negative; if all positive, remaining flips should target the smallest absolute value. After all flips, parity of remaining k determines if we lose the min.

## Detailed Explanation
Sort asc. For i from 0 with k>0 and nums[i]<0: nums[i]=-nums[i], k--. Sum all; if remaining k odd, subtract 2*min|value|.

## Dry Run
nums=[-2,-3,-1], k=1. Flip -3 → [-2,3,-1] sum=0. But smallest abs=1. No remaining flips. Correction: sort abs→ sum=0.

## Approach
Sort + selective negation.

## Time and Space Complexity
Time: O(n log n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int largestSumAfterKNegations(vector<int>& a, int k) {
    sort(a.begin(), a.end());
    for (int i = 0; i < (int)a.size() && k > 0 && a[i] < 0; ++i, --k) a[i] = -a[i];
    int s = accumulate(a.begin(), a.end(), 0);
    if (k % 2) s -= 2 * *min_element(a.begin(), a.end());
    return s;
}
```

## Follow-up Questions
- What if we cannot flip twice the same element?
- Maximize sum after k increments/decrements.
- Multiple test cases with same array.
