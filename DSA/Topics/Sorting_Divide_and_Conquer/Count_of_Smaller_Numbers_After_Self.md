# Count of Smaller Numbers After Self

## Problem Link
https://leetcode.com/problems/count-of-smaller-numbers-after-self/

## Topic
Sorting Divide and Conquer

## Core Concept
Merge sort counting inversions on the right side.

## Intuition
During merge, when taking an element from the left half, elements already moved from the right half are smaller and all come after in the original array — count them.

## Detailed Explanation
Sort indices by value via merge sort; in each merge step, when copying left[i], increment counts[idx[left[i]]] by number of right elements already taken.

## Dry Run
nums=[5,2,6,1]. counts=[2,1,1,0].

## Approach
Merge sort on indices.

## Time and Space Complexity
Time: O(n log n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
void merge(vector<int>& idx, vector<int>& tmp, vector<int>& nums, vector<int>& counts, int l, int r) {
    if (l >= r) return;
    int m = (l + r) / 2;
    merge(idx, tmp, nums, counts, l, m);
    merge(idx, tmp, nums, counts, m+1, r);
    int i = l, j = m+1, k = l, right = 0;
    while (i <= m && j <= r) {
        if (nums[idx[i]] <= nums[idx[j]]) { counts[idx[i]] += right; tmp[k++] = idx[i++]; }
        else { right++; tmp[k++] = idx[j++]; }
    }
    while (i <= m) { counts[idx[i]] += right; tmp[k++] = idx[i++]; }
    while (j <= r) tmp[k++] = idx[j++];
    for (int x = l; x <= r; ++x) idx[x] = tmp[x];
}
vector<int> countSmaller(vector<int>& nums) {
    int n = nums.size();
    vector<int> idx(n), tmp(n), counts(n, 0);
    iota(idx.begin(), idx.end(), 0);
    merge(idx, tmp, nums, counts, 0, n-1);
    return counts;
}
```

## Follow-up Questions
- Number of inversions total.
- BIT-based approach.
- Online queries.
