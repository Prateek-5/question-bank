# Sum of All Submatrices (Odd Length Subarrays)

## Problem Link
https://leetcode.com/problems/sum-of-all-odd-length-subarrays/

## Topic
1 D and 2 D Arrays

## Core Concept
Contribution counting: each element appears in a known number of odd-length subarrays.

## Intuition
For index i in array of size n, total subarrays containing i = (i+1)*(n-i). Out of these, odd-length ones = ((i+1)*(n-i)+1)/2.

## Detailed Explanation
Sum over i of arr[i] * ((i+1)*(n-i)+1)/2.

## Dry Run
arr=[1,4,2,5,3], n=5. For each i compute contribution; total = 58.

## Approach
Closed form per-element contribution.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int sumOddLengthSubarrays(vector<int>& a) {
    int n = a.size(), s = 0;
    for (int i = 0; i < n; ++i) {
        int c = ((i + 1) * (n - i) + 1) / 2;
        s += c * a[i];
    }
    return s;
}
```

## Follow-up Questions
- Even-length subarrays version.
- Sum of min/max over all subarrays (monotonic stack).
- Submatrices of a matrix.
