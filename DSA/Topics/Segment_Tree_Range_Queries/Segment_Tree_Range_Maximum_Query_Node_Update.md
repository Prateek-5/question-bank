# Segment Tree Range Maximum Query Node Update

## Problem Link
https://www.geeksforgeeks.org/dsa/segment-tree-set-2-range-maximum-query-node-update/

## Topic
Segment Tree Range Queries

## Core Concept
Point-update segment tree with range-max queries.

## Intuition
Segment tree partitions the array; each node stores the max of its range. Point updates touch O(log n) nodes, queries combine O(log n) nodes.

## Detailed Explanation
build(v,l,r) fills t[v]. update(v,l,r,i,val): recurse to leaf, set, then recompute ancestors. query(v,l,r,ql,qr): return 0/−∞ if out, full segment if inside, else max of recursion on children.

## Dry Run
a=[1,3,2,4]. Build t. Query(0,3)=4. Update(2,5): a=[1,3,5,4]. Query(0,3)=5.

## Approach
Array-backed segment tree (size 4n).

## Time and Space Complexity
Build O(n), update/query O(log n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
class SegMax {
    int n; vector<int> t;
    void build(int v,int l,int r, vector<int>& a) {
        if(l==r){t[v]=a[l];return;}
        int m=(l+r)/2;
        build(2*v,l,m,a); build(2*v+1,m+1,r,a);
        t[v]=max(t[2*v], t[2*v+1]);
    }
    void upd(int v,int l,int r,int i,int val) {
        if(l==r){t[v]=val;return;}
        int m=(l+r)/2;
        if(i<=m) upd(2*v,l,m,i,val); else upd(2*v+1,m+1,r,i,val);
        t[v]=max(t[2*v], t[2*v+1]);
    }
    int qry(int v,int l,int r,int ql,int qr) {
        if(ql>r||qr<l) return INT_MIN;
        if(ql<=l&&r<=qr) return t[v];
        int m=(l+r)/2;
        return max(qry(2*v,l,m,ql,qr), qry(2*v+1,m+1,r,ql,qr));
    }
public:
    SegMax(vector<int>& a):n(a.size()){t.assign(4*n,INT_MIN); build(1,0,n-1,a);}
    void update(int i, int v) { upd(1,0,n-1,i,v); }
    int query(int l, int r) { return qry(1,0,n-1,l,r); }
};
```

## Follow-up Questions
- Range update with lazy propagation.
- Range set instead of point update.
- Persistent segment tree.
