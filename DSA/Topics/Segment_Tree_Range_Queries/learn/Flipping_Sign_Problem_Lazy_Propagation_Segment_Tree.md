# Flipping Sign Problem (Lazy Propagation Segment Tree) — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Flipping_Sign_Problem_Lazy_Propagation_Segment_Tree.md`](../Flipping_Sign_Problem_Lazy_Propagation_Segment_Tree.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://www.geeksforgeeks.org/dsa/flipping-sign-problem-lazy-propagation-segment-tree/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/dsa/flipping-sign-problem-lazy-propagation-segment-tree/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: implementation of LAZY PROPAGATION. Three building blocks: `applyFlip(v)` (negate sum, toggle lazy), `push(v)` (apply pending lazy to children before recursing), and update/query that call `push()` on partial overlaps.**

**Map of this file (8 sections):**

1. Read the problem
2. The three primitives
3. Update + query templates
4. Code
5. Trace it
6. Why sum becomes -sum when flipping
7. Common pitfalls
8. The shape — segment tree + lazy template

---

## 1. Read the problem

Array `arr` of integers. Two operations:
- `flipRange(l, r)`: multiply every element in `arr[l..r]` by -1.
- `sumRange(l, r)`: return sum of `arr[l..r]`.

Both need to be O(log n).

**Example:** `arr = [1, -2, 3]`. flipRange(0, 1) → `[-1, 2, 3]`. sumRange(0, 2) = 4.

---

## 2. The three primitives

> **Mini-refresher: encapsulate lazy work into TWO helpers.**
>
> ```
> applyFlip(v):
>     sum[v] = -sum[v]
>     lazy[v] ^= 1
>
> push(v):
>     if lazy[v]:
>         applyFlip(2v)
>         applyFlip(2v+1)
>         lazy[v] = 0
> ```
>
> `applyFlip` is "do the flip on this node and remember to flip children later."
>
> `push` is "if I have a pending flip for children, apply it now."

---

## 3. Update + query templates

For range update / query with lazy:

```
update(v, lo, hi, l, r):
    if r < lo or hi < l: return                   # disjoint
    if l <= lo and hi <= r:
        applyFlip(v)                              # fully covered
        return
    push(v)                                       # PUSH before recursing
    mid = (lo + hi) / 2
    update(2v, lo, mid, l, r)
    update(2v+1, mid+1, hi, l, r)
    sum[v] = sum[2v] + sum[2v+1]                  # recompute

query(v, lo, hi, l, r):
    if r < lo or hi < l: return 0
    if l <= lo and hi <= r: return sum[v]
    push(v)                                       # PUSH before recursing
    mid = (lo + hi) / 2
    return query(2v, lo, mid, l, r) + query(2v+1, mid+1, hi, l, r)
```

The CRITICAL line is `push(v)` BEFORE descending. Skip it and you get stale sums.

---

## 4. Code

**C++:**

```cpp
class SegTree {
    vector<long long> sum;
    vector<int> lazy;
    int n;

    void build(vector<int>& arr, int v, int lo, int hi) {
        if (lo == hi) { sum[v] = arr[lo]; return; }
        int mid = (lo + hi) / 2;
        build(arr, 2*v, lo, mid);
        build(arr, 2*v+1, mid+1, hi);
        sum[v] = sum[2*v] + sum[2*v+1];
    }
    void applyFlip(int v) {
        sum[v] = -sum[v];
        lazy[v] ^= 1;
    }
    void push(int v) {
        if (lazy[v]) {
            applyFlip(2*v);
            applyFlip(2*v+1);
            lazy[v] = 0;
        }
    }
    void update(int v, int lo, int hi, int l, int r) {
        if (r < lo || hi < l) return;
        if (l <= lo && hi <= r) { applyFlip(v); return; }
        push(v);
        int mid = (lo + hi) / 2;
        update(2*v, lo, mid, l, r);
        update(2*v+1, mid+1, hi, l, r);
        sum[v] = sum[2*v] + sum[2*v+1];
    }
    long long query(int v, int lo, int hi, int l, int r) {
        if (r < lo || hi < l) return 0;
        if (l <= lo && hi <= r) return sum[v];
        push(v);
        int mid = (lo + hi) / 2;
        return query(2*v, lo, mid, l, r) + query(2*v+1, mid+1, hi, l, r);
    }
public:
    SegTree(vector<int>& arr) : n(arr.size()) {
        sum.assign(4 * n, 0);
        lazy.assign(4 * n, 0);
        build(arr, 1, 0, n - 1);
    }
    void flipRange(int l, int r) { update(1, 0, n - 1, l, r); }
    long long sumRange(int l, int r) { return query(1, 0, n - 1, l, r); }
};
```

Complexity: build O(n), each op **O(log n)**, space O(n).

---

## 5. Trace it

`arr = [1, -2, 3]`.

Initial sums:
```
[0..2] sum=2
├── [0..1] sum=-1
│   ├── [0]=1
│   └── [1]=-2
└── [2]=3
```

**flipRange(0, 1):**
- Root [0..2], range [0..1]: partial. push (lazy=0, nothing). Recurse.
  - [0..1] fully covered by [0..1]. applyFlip: sum = 1 (was -1), lazy = 1. Return.
  - [2] disjoint with [0..1]. Return.
- root sum = 1 + 3 = 4.

State:
- root sum = 4, lazy = 0.
- [0..1] sum = 1, lazy = 1 (children stale).
- [0]=1, [1]=-2 (stale; will be updated only if a query descends here).

**sumRange(0, 2):** root fully covers [0..2]. Return sum[root] = **4**.  ✓

(Check by hand: after flip, arr = [-1, 2, 3]. Sum = 4. ✓)

If we then called `sumRange(0, 0)`:
- Root partial. push (lazy=0). Recurse to [0..1] partial. push (lazy=1) → applyFlip([0]) (sum: 1 → -1), applyFlip([1]) (sum: -2 → 2). [0..1].lazy = 0. Recurse to [0]: full → return -1.
- Now stale children are updated only when needed.

---

## 6. Why sum becomes -sum when flipping

Every element in the segment flipped sign. So:
- `new_sum = -a_l - a_{l+1} - ... - a_r = -(a_l + a_{l+1} + ... + a_r) = -old_sum`.

One arithmetic negation captures the entire range's flip on the SUM.

For other ops:
- Range add k → `new_sum = old_sum + k · length` (length = segment size).
- Range assign v → `new_sum = v · length`.
- Range multiply m → `new_sum = old_sum · m`.

---

## 7. Common pitfalls

1. **Forgetting `push(v)` before recursing on partial overlap.** Children read stale sums.
2. **Calling `push(v)` on a leaf.** Leaves have no children — guard with the `if (lazy[v])` check OR skip push entirely (lazy on leaves is a no-op anyway).
3. **Not recomputing `sum[v]` after recursive update.** Must `sum[v] = sum[left] + sum[right]` after children return.
4. **Wrong lazy combination.** For flip, `lazy ^= 1`. For add, `lazy += delta`. Get the OPERATOR right for your op.
5. **Returning `INT_MIN` from disjoint sum query.** Use 0 (sum's identity). For max it'd be INT_MIN.
6. **4n vs 2n tree size.** 4n is the safe upper bound.

---

## 8. The shape — segment tree + lazy template

The pattern: **structure of the lazy-prop segment tree is FIXED; what changes is the (combine, apply, compose) trio.**

| Range op | applyOp(v) | Composition |
|---|---|---|
| **Flip sign** | sum = -sum; lazy ^= 1 | XOR |
| Range add k | sum += k · len; lazy += k | sum addends |
| Range assign x | sum = x · len; lazy = (set, x) | last assignment wins |
| Range multiply m | sum *= m; lazy *= m | product |
| Mixed (add+assign) | careful canonicalization | order matters |

**Pattern to internalize:**

> "Lazy propagation = three primitives: applyOp (update node's aggregate + record), push (push lazy to children), and the standard update/query templates that call push before partial-overlap recursion."

---

> **Self-check — the question to ask next time.**
>
> When implementing range update + range query:
>
> > **"Define applyOp(v) and push(v). Update template: if fully covered → applyOp; else push, recurse, recompute. Query template: same skeleton minus the recompute. O(log n) per op."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Flipping_Sign_Problem_Lazy_Propagation_Segment_Tree.md`](../Flipping_Sign_Problem_Lazy_Propagation_Segment_Tree.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Flipping_Sign_Problem_Lazy_Propagation.md`](./Flipping_Sign_Problem_Lazy_Propagation.md) (the concept companion).
  - [`Range_Sum_Query_Mutable.md`](./Range_Sum_Query_Mutable.md), [`Segment_Tree_Range_Maximum_Query_Node_Update.md`](./Segment_Tree_Range_Maximum_Query_Node_Update.md).
  - **Topic complete — next: Number Theory & Misc (final topic, 19 problems).**
