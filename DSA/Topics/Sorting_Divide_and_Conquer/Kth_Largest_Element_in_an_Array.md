# Kth Largest Element in an Array

## Problem Link
https://leetcode.com/problems/kth-largest-element-in-an-array/

## Topic
Sorting Divide and Conquer

## Core Concept
Quickselect partition around a pivot.

## Intuition
Hoare's partition places the pivot in its final sorted position; if that's the target rank, done. Else recurse into the correct side.

## Detailed Explanation
Pick random pivot, partition, compare pivot index with target (n-k). Recurse on the appropriate side.

## Dry Run
nums=[3,2,1,5,6,4], k=2 → target idx = 4. Quickselect returns 5.

## Approach
Randomized quickselect.

## Time and Space Complexity
Time: O(n) avg, O(n²) worst. Space: O(log n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int findKthLargest(vector<int>& nums, int k) {
    int n = nums.size(), target = n - k, lo = 0, hi = n - 1;
    while (true) {
        int pivot = nums[lo + rand() % (hi - lo + 1)];
        int i = lo, j = hi, p = lo;
        while (p <= j) {
            if (nums[p] < pivot) swap(nums[p++], nums[i++]);
            else if (nums[p] > pivot) swap(nums[p], nums[j--]);
            else p++;
        }
        if (target < i) hi = i - 1;
        else if (target > j) lo = j + 1;
        else return pivot;
    }
}
```

## Follow-up Questions
- Median-of-medians for O(n) worst.
- Bucket for bounded ranges.
- Streaming median.
