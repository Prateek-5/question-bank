# Sort Colors

## Problem Link
https://leetcode.com/problems/sort-colors/

## Topic
Sorting Divide and Conquer

## Core Concept
Dutch National Flag — three-way partition.

## Intuition
Partition array into <1, ==1, >1 using three pointers lo, mid, hi. Swap nums[mid] with nums[lo] or nums[hi] depending on value.

## Detailed Explanation
lo=0, mid=0, hi=n-1. While mid<=hi: if nums[mid]==0 swap(lo,mid), lo++,mid++; ==1 mid++; ==2 swap(mid,hi), hi--.

## Dry Run
nums=[2,0,2,1,1,0] → [0,0,1,1,2,2].

## Approach
Three-pointer partition.

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
void sortColors(vector<int>& a) {
    int lo = 0, mid = 0, hi = a.size() - 1;
    while (mid <= hi) {
        if (a[mid] == 0) swap(a[lo++], a[mid++]);
        else if (a[mid] == 1) mid++;
        else swap(a[mid], a[hi--]);
    }
}
```

## Follow-up Questions
- k colors (k-way partition).
- Stable partition.
- Sort 0s/1s only.
