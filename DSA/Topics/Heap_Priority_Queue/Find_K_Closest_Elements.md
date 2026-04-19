# Find K Closest Elements

## Problem Link
https://leetcode.com/problems/find-k-closest-elements/

## Topic
Heap Priority Queue

## Core Concept
Binary search for the left boundary of a k-length window around x.

## Intuition
Array is sorted. We need the window of size k whose elements are closest to x. Binary search finds the left index lo such that arr[lo..lo+k-1] is optimal — by comparing |arr[mid] - x| vs |arr[mid+k] - x|.

## Detailed Explanation
Maintain lo=0, hi=n-k. While lo < hi, let mid=(lo+hi)/2. If x - arr[mid] > arr[mid+k] - x, lo=mid+1 (the right element is closer so shift right), else hi=mid. End: window [lo..lo+k-1].

## Dry Run
arr=[1,2,3,4,5], k=4, x=3. lo=0, hi=1. mid=0. x-arr[0]=2, arr[4]-x=2. 2>2? no → hi=0. Loop ends. Window = arr[0..3] = [1,2,3,4].

## Approach
Binary search on left boundary in O(log(n-k)). Much faster than heap O(n log k).

## Time and Space Complexity
Time: O(log(n-k) + k). Space: O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;

vector<int> findClosestElements(vector<int>& arr, int k, int x) {
    int lo = 0, hi = arr.size() - k;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        if (x - arr[mid] > arr[mid + k] - x) lo = mid + 1;
        else hi = mid;
    }
    return vector<int>(arr.begin()+lo, arr.begin()+lo+k);
}
```

## Follow-up Questions
- If array is unsorted, sort first or use a max-heap by |a - x|.
- What if there are duplicates? Behavior unchanged.
- Solve with two pointers shrinking from both ends.
