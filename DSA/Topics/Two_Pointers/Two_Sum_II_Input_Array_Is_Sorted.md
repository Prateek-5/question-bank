# Two Sum II – Input Array Is Sorted

## Problem Link
https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/

## Topic
Two Pointers

## Core Concept
Two-pointer sum on a sorted array.

## Intuition
If the current sum is too small, move left pointer right to increase; if too big, move right pointer left.

## Detailed Explanation
l=0, r=n-1. While l<r: s=a[l]+a[r]. If s==target return {l+1,r+1}; if s<target l++ else r--.

## Dry Run
a=[2,7,11,15], target=9. l=0,r=3: 17>9→r=2. 13>9→r=1. 9=9 → {1,2}.

## Approach
Two pointers O(n).

## Time and Space Complexity
Time: O(n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<int> twoSum(vector<int>& a, int t) {
    int l = 0, r = a.size() - 1;
    while (l < r) {
        int s = a[l] + a[r];
        if (s == t) return {l+1, r+1};
        if (s < t) l++; else r--;
    }
    return {};
}
```

## Follow-up Questions
- All pairs with given sum.
- Unsorted variant (hashmap).
- Two-sum in a BST.
