# Range Sum Query – Immutable

## Problem Link
https://leetcode.com/problems/range-sum-query-immutable/

## Topic
Segment Tree Range Queries

## Core Concept
Prefix sums for O(1) range sum queries.

## Intuition
Range sum [l,r] = prefix[r+1] - prefix[l]. Build the prefix array once; answer queries in constant time.

## Detailed Explanation
Build P[0]=0, P[i]=P[i-1]+nums[i-1]. Query sumRange(l,r) = P[r+1]-P[l].

## Dry Run
nums=[-2,0,3,-5,2,-1]. P=[0,-2,-2,1,-4,-2,-3]. sumRange(0,2)=P[3]-P[0]=1.

## Approach
Static prefix array.

## Time and Space Complexity
Build O(n), query O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
class NumArray {
    vector<int> P;
public:
    NumArray(vector<int>& nums) {
        P.assign(nums.size()+1, 0);
        for (int i = 0; i < (int)nums.size(); ++i) P[i+1] = P[i] + nums[i];
    }
    int sumRange(int l, int r) { return P[r+1] - P[l]; }
};
```

## Follow-up Questions
- Handle updates (Range Sum Query Mutable, BIT).
- Multi-dimensional prefix sums.
- Range minimum query (sparse table).
