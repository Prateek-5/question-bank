# Single Element in a Sorted Array

## Problem Link
https://leetcode.com/problems/single-element-in-a-sorted-array/description/

## Topic
Searching Binary Search

## Core Concept
Binary search on parity — single element breaks the paired pattern.

## Intuition
In a perfectly paired array, element at even i equals next odd i+1. Once the single element is encountered, this pairing shifts.

## Detailed Explanation
lo=0, hi=n-1. While lo<hi: m=(lo+hi)/2 & ~1 (make even). If a[m]==a[m+1] lo=m+2 else hi=m. Return a[lo].

## Dry Run
nums=[1,1,2,3,3,4,4,8,8]. m=4(even),a[4]=3,a[5]=4 ≠ → hi=4. m=2(even),a[2]=2,a[3]=3 ≠ → hi=2. m=0,a[0]=a[1] → lo=2. Answer a[2]=2.

## Approach
Binary search using pair parity.

## Time and Space Complexity
Time: O(log n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int singleNonDuplicate(vector<int>& a) {
    int lo = 0, hi = a.size() - 1;
    while (lo < hi) {
        int m = (lo + hi) / 2;
        if (m % 2) m--;
        if (a[m] == a[m+1]) lo = m + 2;
        else hi = m;
    }
    return a[lo];
}
```

## Follow-up Questions
- Two single elements (XOR + bit split).
- Unsorted variant (XOR).
- Custom equality function.
