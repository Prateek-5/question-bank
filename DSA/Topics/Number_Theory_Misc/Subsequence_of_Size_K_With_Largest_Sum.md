# Subsequence of Size K With Largest Sum

## Problem Link
https://leetcode.com/problems/subsequence-of-size-k-with-the-largest-sum/

## Topic
Number Theory Misc

## Core Concept
Partition-based selection of k largest keeping original order.

## Intuition
The largest-sum subsequence is the k largest values. We need to preserve original order — so record their indices.

## Detailed Explanation
Pair values with indices. nth_element by value descending to get top k by value. Sort those k by original index. Output values.

## Dry Run
nums=[2,1,3,3], k=2. Top 2 values: 3,3 (indices 2,3). Output [3,3].

## Approach
Selection + sort by index.

## Time and Space Complexity
Time: O(n log k). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<int> maxSubsequence(vector<int>& a, int k) {
    int n = a.size();
    vector<int> idx(n); iota(idx.begin(), idx.end(), 0);
    nth_element(idx.begin(), idx.begin()+k, idx.end(), [&](int x, int y){ return a[x] > a[y]; });
    vector<int> pick(idx.begin(), idx.begin()+k);
    sort(pick.begin(), pick.end());
    vector<int> r;
    for (int i : pick) r.push_back(a[i]);
    return r;
}
```

## Follow-up Questions
- Minimum-sum subsequence.
- Tie-break by earliest indices.
- Streaming version.
