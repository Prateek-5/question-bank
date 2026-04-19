# Flipping Sign Problem (Lazy Propagation)

## Problem Link
https://www.geeksforgeeks.org/dsa/flipping-sign-problem-lazy-propagation-segment-tree/

## Topic
Segment Tree Range Queries

## Core Concept
Segment tree with lazy propagation — defer sign flips to descendants.

## Intuition
Flipping signs on a range can affect many elements; propagating lazily only when needed keeps operations in O(log n).

## Detailed Explanation
Each node stores sum and a flip flag. On range flip: if segment fully within range, negate sum and toggle flip flag; else push flag to children and recurse. On query, push flag before descending.

## Dry Run
Array [1,-2,3,4]. Flip range [1,3]: sum=1+2-3-4=-4. Query sum[0,3]: push+recurse → -4.

## Approach
Segment tree with deferred updates.

## Time and Space Complexity
Update/query O(log n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
class SegFlip {
    int n;
    vector<long long> sum;
    vector<int> flip;
    void push(int v) {
        if (flip[v]) {
            for (int c : {2*v, 2*v+1}) { sum[c] = -sum[c]; flip[c] ^= 1; }
            flip[v] = 0;
        }
    }
    void build(int v, int l, int r, vector<int>& a) {
        if (l==r) { sum[v] = a[l]; return; }
        int m = (l+r)/2;
        build(2*v,l,m,a); build(2*v+1,m+1,r,a);
        sum[v] = sum[2*v] + sum[2*v+1];
    }
    void upd(int v, int l, int r, int ql, int qr) {
        if (ql>r||qr<l) return;
        if (ql<=l && r<=qr) { sum[v]=-sum[v]; flip[v]^=1; return; }
        push(v);
        int m=(l+r)/2;
        upd(2*v,l,m,ql,qr); upd(2*v+1,m+1,r,ql,qr);
        sum[v]=sum[2*v]+sum[2*v+1];
    }
    long long qry(int v, int l, int r, int ql, int qr) {
        if (ql>r||qr<l) return 0;
        if (ql<=l && r<=qr) return sum[v];
        push(v);
        int m=(l+r)/2;
        return qry(2*v,l,m,ql,qr) + qry(2*v+1,m+1,r,ql,qr);
    }
public:
    SegFlip(vector<int>& a) : n(a.size()) { sum.assign(4*n,0); flip.assign(4*n,0); build(1,0,n-1,a); }
    void flipRange(int l, int r) { upd(1,0,n-1,l,r); }
    long long sumRange(int l, int r) { return qry(1,0,n-1,l,r); }
};
```

## Follow-up Questions
- Add point-update plus range-flip.
- Flip with multiplication (lazy with composition).
- Persistent segment tree.
