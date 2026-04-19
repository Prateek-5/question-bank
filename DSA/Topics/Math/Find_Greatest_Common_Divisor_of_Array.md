# Find Greatest Common Divisor of Array

## Problem Link
https://leetcode.com/problems/find-greatest-common-divisor-of-array/

## Topic
Math

## Core Concept
GCD(min, max) — GCD of array equals GCD of its smallest and largest elements only *if* the array is specified that way; generally you iterate.

## Intuition
The problem specifically asks for GCD of the smallest and largest elements in the array — a single gcd call suffices.

## Detailed Explanation
Find min and max in one pass (or with STL). Return gcd(min, max) using Euclid's algorithm.

## Dry Run
nums=[2,5,6,9,10]. min=2, max=10. gcd(2,10)=2.

## Approach
Linear scan for min/max, then Euclidean gcd.

## Time and Space Complexity
Time: O(n + log max). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int findGCD(vector<int>& nums) {
    int lo = *min_element(nums.begin(), nums.end());
    int hi = *max_element(nums.begin(), nums.end());
    return __gcd(lo, hi);
}
```

## Follow-up Questions
- Compute GCD of all elements (fold gcd).
- LCM of array.
- GCD over a sliding window (segment tree).
