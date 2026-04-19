# Range Sum Query – Mutable

## Problem Link
https://leetcode.com/problems/range-sum-query-mutable/

## Topic
Segment Tree Range Queries

## Core Concept
Fenwick Tree (Binary Indexed Tree) for O(log n) update and query.

## Intuition
BIT maintains partial sums under point updates in O(log n) — the implicit binary structure uses each index's lowest set bit to skip efficiently.

## Detailed Explanation
update(i, d): i++ then while i<=n: tree[i]+=d; i+=i&-i. query(i): s=0; i++; while i>0: s+=tree[i]; i-=i&-i. sumRange = query(r) - query(l-1).

## Dry Run
nums=[1,3,5]. After build: query(2)=9. update(1,2): array=[1,5,5]. query(2)=11. sumRange(0,2)=11.

## Approach
BIT with 1-indexed internal array.

## Time and Space Complexity
Update/query O(log n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
class NumArray {
    vector<int> bit, a;
    int n;
    void add(int i, int d) { for (++i; i <= n; i += i & -i) bit[i] += d; }
    int q(int i) { int s = 0; for (++i; i > 0; i -= i & -i) s += bit[i]; return s; }
public:
    NumArray(vector<int>& nums) : a(nums), n(nums.size()) {
        bit.assign(n+1, 0);
        for (int i = 0; i < n; ++i) add(i, nums[i]);
    }
    void update(int i, int v) { add(i, v - a[i]); a[i] = v; }
    int sumRange(int l, int r) { return q(r) - (l > 0 ? q(l-1) : 0); }
};
```

## Follow-up Questions
- Range update + point query (use difference array BIT).
- 2D BIT for matrix updates.
- Persistent BIT.
