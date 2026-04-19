# Running Sum of 1D Array

## Problem Link
https://leetcode.com/problems/running-sum-of-1d-array/

## Topic
1 D and 2 D Arrays

## Core Concept
In-place prefix sum.

## Intuition
The i-th running sum is nums[i] + previous running sum. Build in one pass.

## Detailed Explanation
For i from 1: nums[i] += nums[i-1]. Return nums.

## Dry Run
[1,2,3,4] → [1,3,6,10].

## Approach
In-place accumulation.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<int> runningSum(vector<int>& a) {
    for (int i = 1; i < (int)a.size(); ++i) a[i] += a[i-1];
    return a;
}
```

## Follow-up Questions
- 2D running sum.
- Range sum queries using this.
- Suffix sum variant.
