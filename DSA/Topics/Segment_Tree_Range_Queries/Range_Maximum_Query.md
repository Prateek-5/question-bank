# Range Maximum Query

## Problem Link
https://leetcode.com/problems/range-maximum-query-2d-immutable/

## Topic
Segment Tree Range Queries

## Core Concept
Sparse table for immutable arrays or segment tree with max for mutable.

## Intuition
For static arrays, precompute st[i][j] = max over [i, i+2^j). Any range max is combined from two overlapping power-of-two windows in O(1).

## Detailed Explanation
Build st with DP: st[i][j] = max(st[i][j-1], st[i+2^(j-1)][j-1]). Query(l,r): k=log2(r-l+1); max(st[l][k], st[r-2^k+1][k]).

## Dry Run
a=[1,3,2,7,9,11,3]. Build sparse table. query(1,4): k=2; max(a[1..4] via st[1][2],st[2][2])=9.

## Approach
Sparse table for O(n log n) build, O(1) query.

## Time and Space Complexity
Build O(n log n), query O(1).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
class RMQ {
    vector<vector<int>> st;
    vector<int> lg;
public:
    RMQ(vector<int>& a) {
        int n = a.size(), K = 0; while ((1 << K) <= n) K++;
        st.assign(K, vector<int>(n));
        for (int i = 0; i < n; ++i) st[0][i] = a[i];
        for (int j = 1; (1 << j) <= n; ++j)
            for (int i = 0; i + (1 << j) <= n; ++i)
                st[j][i] = max(st[j-1][i], st[j-1][i + (1 << (j-1))]);
        lg.assign(n+1, 0);
        for (int i = 2; i <= n; ++i) lg[i] = lg[i/2] + 1;
    }
    int query(int l, int r) {
        int k = lg[r - l + 1];
        return max(st[k][l], st[k][r - (1 << k) + 1]);
    }
};
```

## Follow-up Questions
- Extend for min, gcd.
- Mutable — switch to segment tree.
- Range-mode query (harder).
