# Minimum Platforms

## Problem Link
https://practice.geeksforgeeks.org/problems/minimum-platforms-1587115620/1

## Topic
Greedy

## Core Concept
Sweep-line / two-pointer over sorted arrivals and departures.

## Intuition
Count maximum simultaneous trains at any time. Sort arrivals and departures separately; advance one pointer at a time to track the count's maximum.

## Detailed Explanation
i=0 (arr), j=0 (dep), count=0, peak=0. While i<n: if arr[i]<=dep[j] count++, i++; else count--, j++. Track max count.

## Dry Run
arr=[900,940,950,1100,1500,1800], dep=[910,1200,1120,1130,1900,2000]. Peak concurrent=3 → answer 3.

## Approach
Two pointers on sorted arrays.

## Time and Space Complexity
Time: O(n log n). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int findPlatform(vector<int>& arr, vector<int>& dep) {
    sort(arr.begin(), arr.end()); sort(dep.begin(), dep.end());
    int n = arr.size(), i=0, j=0, cnt=0, peak=0;
    while (i < n) {
        if (arr[i] <= dep[j]) { cnt++; i++; }
        else { cnt--; j++; }
        peak = max(peak, cnt);
    }
    return peak;
}
```

## Follow-up Questions
- Return the actual platform assignment per train.
- Handle equal time-ties (pick policy).
- Variable platform costs.
