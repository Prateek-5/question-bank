# Single Number

## Problem Link
https://leetcode.com/problems/single-number/

## Topic
Bit Manipulation

## Core Concept
XOR accumulation cancels pairs.

## Intuition
x XOR x = 0 and XOR is commutative — paired values vanish; only the lone value survives.

## Detailed Explanation
XOR all elements; result is the single number.

## Dry Run
nums=[2,2,1] → 2^2^1=1.

## Approach
One pass XOR.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int singleNumber(vector<int>& a) { int x = 0; for (int v : a) x ^= v; return x; }
```

## Follow-up Questions
- Single Number II (others thrice).
- Single Number III (two singletons).
- Missing number.
