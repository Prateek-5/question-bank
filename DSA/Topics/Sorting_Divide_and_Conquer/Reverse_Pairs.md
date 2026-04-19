# Reverse Pairs

## Problem Link
https://leetcode.com/problems/reverse-pairs/

## Topic
Sorting Divide and Conquer

## Core Concept
Merge sort counting pairs (i,j) with i<j and nums[i] > 2·nums[j].

## Intuition
After sorting halves, count valid (i,j) via two-pointer before merging.

## Detailed Explanation
Mergesort. Before merging, for i in left, advance j in right while nums[i]>2·nums[j]; add (j-m-1) to count. Then merge normally.

## Dry Run
nums=[1,3,2,3,1]. Pairs: (3,1),(3,1) from two 3s vs 1s → total 2.

## Approach
Merge sort counting phase.

## Time and Space Complexity
Time: O(n log n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int mergeCount(vector<int>& a, int l, int r) {
    if (l >= r) return 0;
    int m = (l + r) / 2;
    int cnt = mergeCount(a, l, m) + mergeCount(a, m+1, r);
    int j = m + 1;
    for (int i = l; i <= m; ++i) {
        while (j <= r && a[i] > 2LL * a[j]) j++;
        cnt += j - m - 1;
    }
    inplace_merge(a.begin()+l, a.begin()+m+1, a.begin()+r+1);
    return cnt;
}
int reversePairs(vector<int>& nums) { return mergeCount(nums, 0, nums.size()-1); }
```

## Follow-up Questions
- BIT / Fenwick approach.
- Generalized k·nums[j].
- Online updates.
