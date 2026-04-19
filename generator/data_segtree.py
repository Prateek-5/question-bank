DATA = {
"Range Sum Query Immutable": {
  "concept": "Prefix sums for O(1) range sum queries.",
  "intuition": "Range sum [l,r] = prefix[r+1] - prefix[l]. Build the prefix array once; answer queries in constant time.",
  "explanation": "Build P[0]=0, P[i]=P[i-1]+nums[i-1]. Query sumRange(l,r) = P[r+1]-P[l].",
  "dry_run": "nums=[-2,0,3,-5,2,-1]. P=[0,-2,-2,1,-4,-2,-3]. sumRange(0,2)=P[3]-P[0]=1.",
  "approach": "Static prefix array.",
  "complexity": "Build O(n), query O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
class NumArray {
    vector<int> P;
public:
    NumArray(vector<int>& nums) {
        P.assign(nums.size()+1, 0);
        for (int i = 0; i < (int)nums.size(); ++i) P[i+1] = P[i] + nums[i];
    }
    int sumRange(int l, int r) { return P[r+1] - P[l]; }
};""",
  "followups": "- Handle updates (Range Sum Query Mutable, BIT).\n- Multi-dimensional prefix sums.\n- Range minimum query (sparse table)."
},

"Range Sum Query Mutable": {
  "concept": "Fenwick Tree (Binary Indexed Tree) for O(log n) update and query.",
  "intuition": "BIT maintains partial sums under point updates in O(log n) — the implicit binary structure uses each index's lowest set bit to skip efficiently.",
  "explanation": "update(i, d): i++ then while i<=n: tree[i]+=d; i+=i&-i. query(i): s=0; i++; while i>0: s+=tree[i]; i-=i&-i. sumRange = query(r) - query(l-1).",
  "dry_run": "nums=[1,3,5]. After build: query(2)=9. update(1,2): array=[1,5,5]. query(2)=11. sumRange(0,2)=11.",
  "approach": "BIT with 1-indexed internal array.",
  "complexity": "Update/query O(log n).",
  "code": """#include <bits/stdc++.h>
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
};""",
  "followups": "- Range update + point query (use difference array BIT).\n- 2D BIT for matrix updates.\n- Persistent BIT."
},

"Range Maximum Query": {
  "concept": "Sparse table for immutable arrays or segment tree with max for mutable.",
  "intuition": "For static arrays, precompute st[i][j] = max over [i, i+2^j). Any range max is combined from two overlapping power-of-two windows in O(1).",
  "explanation": "Build st with DP: st[i][j] = max(st[i][j-1], st[i+2^(j-1)][j-1]). Query(l,r): k=log2(r-l+1); max(st[l][k], st[r-2^k+1][k]).",
  "dry_run": "a=[1,3,2,7,9,11,3]. Build sparse table. query(1,4): k=2; max(a[1..4] via st[1][2],st[2][2])=9.",
  "approach": "Sparse table for O(n log n) build, O(1) query.",
  "complexity": "Build O(n log n), query O(1).",
  "code": """#include <bits/stdc++.h>
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
};""",
  "followups": "- Extend for min, gcd.\n- Mutable — switch to segment tree.\n- Range-mode query (harder)."
},

"Flipping Sign Problem (Lazy Propagation)": {
  "concept": "Segment tree with lazy propagation — defer sign flips to descendants.",
  "intuition": "Flipping signs on a range can affect many elements; propagating lazily only when needed keeps operations in O(log n).",
  "explanation": "Each node stores sum and a flip flag. On range flip: if segment fully within range, negate sum and toggle flip flag; else push flag to children and recurse. On query, push flag before descending.",
  "dry_run": "Array [1,-2,3,4]. Flip range [1,3]: sum=1+2-3-4=-4. Query sum[0,3]: push+recurse → -4.",
  "approach": "Segment tree with deferred updates.",
  "complexity": "Update/query O(log n).",
  "code": """#include <bits/stdc++.h>
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
};""",
  "followups": "- Add point-update plus range-flip.\n- Flip with multiplication (lazy with composition).\n- Persistent segment tree."
},

"Segment Tree Range Maximum Query Node Update": {
  "concept": "Point-update segment tree with range-max queries.",
  "intuition": "Segment tree partitions the array; each node stores the max of its range. Point updates touch O(log n) nodes, queries combine O(log n) nodes.",
  "explanation": "build(v,l,r) fills t[v]. update(v,l,r,i,val): recurse to leaf, set, then recompute ancestors. query(v,l,r,ql,qr): return 0/−∞ if out, full segment if inside, else max of recursion on children.",
  "dry_run": "a=[1,3,2,4]. Build t. Query(0,3)=4. Update(2,5): a=[1,3,5,4]. Query(0,3)=5.",
  "approach": "Array-backed segment tree (size 4n).",
  "complexity": "Build O(n), update/query O(log n).",
  "code": """#include <bits/stdc++.h>
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
};""",
  "followups": "- Range update with lazy propagation.\n- Range set instead of point update.\n- Persistent segment tree."
},

"Flipping Sign Problem (Lazy Propagation Segment Tree)": {
  "concept": "Same as 'Flipping Sign Problem (Lazy Propagation)' — see that entry.",
  "intuition": "This duplicate exists as a drill to implement lazy propagation once more.",
  "explanation": "Refer to earlier entry; lazy flag toggles on partial cover; pushes on descent.",
  "dry_run": "See earlier entry.",
  "approach": "Segment tree with lazy flip flag.",
  "complexity": "Update/query O(log n).",
  "code": """// See Flipping Sign Problem (Lazy Propagation) implementation above.""",
  "followups": "- See earlier entry."
},
}
