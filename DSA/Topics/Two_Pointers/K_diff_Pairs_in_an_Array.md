# K-diff Pairs in an Array

## Problem Link
https://leetcode.com/problems/k-diff-pairs-in-an-array/

## Topic
Two Pointers

## Core Concept
Hashmap frequency count — special-case k=0 for duplicates.

## Intuition
Count unique values. For k>0, count pairs (v, v+k) both present. For k=0, count values with frequency ≥ 2.

## Detailed Explanation
Build count map. If k==0: answer = number of keys with count>=2. Else: for each key v, if cnt contains v+k, answer++.

## Dry Run
nums=[3,1,4,1,5], k=2. Unique pairs (1,3),(3,5). Answer=2.

## Approach
Single hashmap pass.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int findPairs(vector<int>& nums, int k) {
    if (k < 0) return 0;
    unordered_map<int,int> c;
    for (int x : nums) c[x]++;
    int ans = 0;
    for (auto& [v, f] : c) {
        if (k == 0 && f >= 2) ans++;
        if (k > 0 && c.count(v + k)) ans++;
    }
    return ans;
}
```

## Follow-up Questions
- Count ordered pairs instead of unique.
- |diff|=k with two arrays.
- k-diff triples.
