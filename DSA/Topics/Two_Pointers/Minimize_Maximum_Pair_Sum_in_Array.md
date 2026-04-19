# Minimize Maximum Pair Sum in Array

## Problem Link
https://leetcode.com/problems/minimize-maximum-pair-sum-in-array/description/

## Topic
Two Pointers

## Core Concept
Sort; pair smallest with largest, etc.

## Intuition
Pairing smallest with largest keeps all pair sums close to the mean, minimizing the maximum.

## Detailed Explanation
Sort. For i in [0, n/2), compute a[i] + a[n-1-i]; track max.

## Dry Run
a=[3,5,2,3]. Sort [2,3,3,5]. Pairs (2+5),(3+3)=7,6. Max=7.

## Approach
Sort + linear pairing.

## Time and Space Complexity
Time: O(n log n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int minPairSum(vector<int>& a) {
    sort(a.begin(), a.end());
    int n = a.size(), best = 0;
    for (int i = 0; i < n/2; ++i) best = max(best, a[i] + a[n-1-i]);
    return best;
}
```

## Follow-up Questions
- Prove optimality via exchange argument.
- Triplet sum minimization.
- Weighted pair sums.
