# 3Sum

## Problem Link
https://leetcode.com/problems/3sum/

## Topic
Two Pointers

## Core Concept
Sort + fix first + two-pointer on remaining.

## Intuition
To find triplets summing to 0, sort, fix i, and two-pointer for j,k such that nums[j]+nums[k] = -nums[i]. Skip duplicates.

## Detailed Explanation
Sort. For each i: if nums[i]>0 break. Skip duplicate i. j=i+1, k=n-1; while j<k: compare sum; if zero, record and skip duplicates; adjust pointers.

## Dry Run
nums=[-1,0,1,2,-1,-4] → sorted [-4,-1,-1,0,1,2]. Triplets: [-1,-1,2],[-1,0,1].

## Approach
Sort + two pointers.

## Time and Space Complexity
Time: O(n²). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<vector<int>> threeSum(vector<int>& a) {
    sort(a.begin(), a.end());
    int n = a.size();
    vector<vector<int>> res;
    for (int i = 0; i < n - 2; ++i) {
        if (a[i] > 0) break;
        if (i > 0 && a[i] == a[i-1]) continue;
        int j = i+1, k = n-1;
        while (j < k) {
            int s = a[i] + a[j] + a[k];
            if (s == 0) {
                res.push_back({a[i], a[j], a[k]});
                while (j < k && a[j] == a[j+1]) j++;
                while (j < k && a[k] == a[k-1]) k--;
                j++; k--;
            } else if (s < 0) j++;
            else k--;
        }
    }
    return res;
}
```

## Follow-up Questions
- 3Sum Closest.
- 4Sum with k-sum recursion.
- 3Sum Smaller.
