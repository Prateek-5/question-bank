# Ugly Number II

## Problem Link
https://leetcode.com/problems/ugly-number-ii/

## Topic
Two Pointers

## Core Concept
Three-pointer merge of sequences ×2, ×3, ×5.

## Intuition
Every ugly number is 2^a * 3^b * 5^c. Generate in order by merging three ascending sequences: previous ugly numbers multiplied by 2, 3, 5.

## Detailed Explanation
u[0]=1; maintain pointers i2, i3, i5 into u. Next ugly = min(u[i2]*2, u[i3]*3, u[i5]*5). Advance whichever pointer matched (could be multiple to avoid dup).

## Dry Run
u=[1,2,3,4,5,6,8,9,10,12,...].

## Approach
Three-pointer DP.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int nthUglyNumber(int n) {
    vector<long long> u(n);
    u[0] = 1;
    int i2=0,i3=0,i5=0;
    for (int i = 1; i < n; ++i) {
        long long v = min({u[i2]*2, u[i3]*3, u[i5]*5});
        u[i] = v;
        if (v == u[i2]*2) i2++;
        if (v == u[i3]*3) i3++;
        if (v == u[i5]*5) i5++;
    }
    return (int)u[n-1];
}
```

## Follow-up Questions
- Super Ugly Number with arbitrary prime list.
- Ugly numbers up to N.
- k-th ugly number in streaming.
