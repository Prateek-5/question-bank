# Range Maximum Query

**Problem Link:**
<a href="https://www.geeksforgeeks.org/range-minimum-query-for-static-array/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/range-minimum-query-for-static-array/</a>

**Topic:**
Segment Tree / Range Queries

----------------------------------------

## Step 1: The Problem

Given a static array (no updates), answer many queries of the form: "**what's the maximum element in the subarray [l, r]**?"

Example: `arr = [1, 3, 2, 7, 9, 11, 3]`.
- query(1, 4): max of [3, 2, 7, 9] = 9.
- query(0, 6): max of everything = 11.
- query(2, 2): just arr[2] = 2.

The static array constraint — no updates — is key. It unlocks a specialized technique.

----------------------------------------

## Step 2: Brute Force

Each query scans the range: O(r - l + 1) per query. For many queries on large arrays, too slow.

Can we preprocess to answer each query in O(1)?

----------------------------------------

## Step 3: Preprocessing with Power-of-Two Windows

Here's the clever idea — **Sparse Table**.

For each index `i` and each power of two `2^k`, precompute the max of the range `[i, i + 2^k - 1]`. Store in a 2D table `sparse[k][i]`.

`sparse[0][i]` = arr[i] (window of size 1).
`sparse[1][i]` = max(arr[i], arr[i+1]) (window of size 2).
`sparse[2][i]` = max(arr[i..i+3]) (window of size 4).
...
`sparse[k][i]` = max(arr[i..i+2^k-1]) (window of size 2^k).

Recurrence: `sparse[k][i] = max(sparse[k-1][i], sparse[k-1][i + 2^(k-1)])`. Two halves of size 2^(k-1) overlap to cover size 2^k.

Total table size: n × log n. Construction time: O(n log n).

----------------------------------------

## Step 4: Querying in O(1)

For query `[l, r]` with length `len = r - l + 1`:
- Let `k = floor(log2(len))`.
- The query range is covered by two (possibly overlapping) windows of size 2^k:
  - Window starting at l: `[l, l + 2^k - 1]`.
  - Window ending at r: `[r - 2^k + 1, r]`.
- Their union covers `[l, r]` (since 2·2^k > len).
- Answer: `max(sparse[k][l], sparse[k][r - 2^k + 1])`.

Why does this work? Any range can be covered by two overlapping power-of-two windows — one anchored at l, one ending at r. Max is **idempotent** (max(x, x) = x), so overlap doesn't cause double-counting.

----------------------------------------

## Step 5: Trace on `arr = [1, 3, 2, 7, 9, 11, 3]`

n = 7. log2(7) = 2, so k ranges 0..2 (maybe 3 for safety).

sparse[0][i] = arr[i]: [1, 3, 2, 7, 9, 11, 3].

sparse[1][i] = max(arr[i], arr[i+1]):
- sparse[1][0] = max(1, 3) = 3.
- sparse[1][1] = max(3, 2) = 3.
- sparse[1][2] = max(2, 7) = 7.
- sparse[1][3] = max(7, 9) = 9.
- sparse[1][4] = max(9, 11) = 11.
- sparse[1][5] = max(11, 3) = 11.
(Index 6 + 1 out of bounds.)

sparse[2][i] = max over size-4 window:
- sparse[2][0] = max(sparse[1][0], sparse[1][2]) = max(3, 7) = 7.
- sparse[2][1] = max(sparse[1][1], sparse[1][3]) = max(3, 9) = 9.
- sparse[2][2] = max(sparse[1][2], sparse[1][4]) = max(7, 11) = 11.
- sparse[2][3] = max(sparse[1][3], sparse[1][5]) = max(9, 11) = 11.
(Index 4 + 4 = 8 out of bounds; can't build sparse[2][4..6].)

**Query(1, 4)**: len = 4. k = log2(4) = 2. Window 1 starts at 1: sparse[2][1] = 9. Window 2 ends at 4: starts at 4 - 4 + 1 = 1. Same as window 1. max(9, 9) = 9. ✓

**Query(2, 5)**: len = 4. k = 2. Window starts at 2: sparse[2][2] = 11. Window ends at 5: starts at 2. Same. max(11, 11) = 11. ✓

**Query(0, 6)**: len = 7. k = log2(7) = 2 (floor). Window starts at 0: sparse[2][0] = 7. Window ends at 6: starts at 6 - 4 + 1 = 3. sparse[2][3] = 11. max(7, 11) = 11. ✓

Fantastic — O(1) per query after O(n log n) preprocessing.

----------------------------------------

## Step 6: Why Max Is Idempotent (Important for Sparse Table)

Sparse table works for operations where **applying twice doesn't double-count**. Max and min have this property: max(x, x) = x, min(x, x) = x.

GCD also: gcd(x, x) = x.

So sparse table works for **max, min, gcd**, etc. But it does **NOT** work directly for sum: sum(x, x) = 2x, not x. For sums, use segment tree or BIT.

The overlap of two 2^k windows is fine for max because overlapping contributes the same element twice — no harm.

----------------------------------------

## Step 7: Segment Tree as Alternative

If updates are allowed, sparse table is useless (rebuilding is O(n log n)). Use a segment tree keyed on max, which supports updates in O(log n) and queries in O(log n).

For static arrays where speed matters most, sparse table wins on query time (O(1) vs O(log n)).

----------------------------------------

## Step 8: Name It

**Sparse Table** for idempotent range queries on static arrays. Classical name; the power-of-two preprocessing is the defining feature.

Related:
- **Fischer-Heun structure** for O(n) preprocessing + O(1) query on RMQ. More complex, uses Cartesian trees.
- **Segment Tree** for dynamic range queries.
- **Fenwick Tree (BIT)** for sums specifically.

For competitive programming, sparse table is the go-to for immutable RMQ.

----------------------------------------

## Step 9: Complexity

Preprocessing: **O(n log n)** time and space.
Query: **O(1)**.

----------------------------------------

## Step 10: C++ Implementation

```cpp
class SparseTable {
    vector<vector<int>> sparse;
    vector<int> log2_table;

public:
    SparseTable(vector<int>& arr) {
        int n = arr.size();
        int K = log2(n) + 1;
        sparse.assign(K, vector<int>(n, 0));
        log2_table.assign(n + 1, 0);
        for (int i = 2; i <= n; ++i) log2_table[i] = log2_table[i / 2] + 1;

        for (int i = 0; i < n; ++i) sparse[0][i] = arr[i];
        for (int k = 1; (1 << k) <= n; ++k) {
            for (int i = 0; i + (1 << k) <= n; ++i) {
                sparse[k][i] = max(sparse[k-1][i], sparse[k-1][i + (1 << (k-1))]);
            }
        }
    }

    int query(int l, int r) {
        int len = r - l + 1;
        int k = log2_table[len];
        return max(sparse[k][l], sparse[k][r - (1 << k) + 1]);
    }
};
```

The `log2_table` precomputes log2 values for O(1) lookup. Could also use `__builtin_clz` tricks.

----------------------------------------

## Step 11: Follow-up Questions

- **Range minimum query.** Replace `max` with `min`. Everything else identical.
- **Range GCD query.** Replace `max` with `__gcd`. Still idempotent, so sparse table works.
- **Range sum query (static).** Sparse table doesn't work (non-idempotent). Use prefix sums: O(n) build, O(1) query.
- **Updates.** Sparse table fails. Use segment tree.
- **Approximate queries.** Lossy compression or bucketing might help.
- **2D range max.** 2D sparse table — O(n·m·log n·log m) preprocessing, O(1) queries.
