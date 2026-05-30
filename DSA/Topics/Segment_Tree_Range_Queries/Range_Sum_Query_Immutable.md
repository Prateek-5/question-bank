# Range Sum Query – Immutable

**Problem Link:**
<a href="https://leetcode.com/problems/range-sum-query-immutable/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/range-sum-query-immutable/</a>

**Topic:**
Segment Tree / Range Queries

----------------------------------------

## Step 1: The Contract

Design a class `NumArray` that:
- Is constructed with an integer array `nums`.
- Supports `sumRange(left, right)` — returning `nums[left] + nums[left+1] + ... + nums[right]` (inclusive).

Constraints:
- Up to 10^4 elements.
- Up to 10^4 queries.
- **The array never changes.** (That's the "immutable" in the problem title — a key hint.)

Example: `nums = [-2, 0, 3, -5, 2, -1]`.
- `sumRange(0, 2)` = -2 + 0 + 3 = 1.
- `sumRange(2, 5)` = 3 + (-5) + 2 + (-1) = -1.
- `sumRange(0, 5)` = -3.

----------------------------------------

## Step 2: Naive Approach and Why It's Too Slow

Simplest implementation: on each query, loop from `left` to `right`, summing.

```
def sumRange(left, right):
    s = 0
    for i in left..right: s += nums[i]
    return s
```

Per query: O(n) in the worst case. With n = 10^4 and q = 10^4, that's up to 10^8 ops — borderline. But we can do **much** better because the array is immutable.

----------------------------------------

## Step 3: Exploit the Immutability — Prefix Sums

The array doesn't change. So any precomputation we do upfront amortizes over all queries.

Define `prefix[i] = nums[0] + nums[1] + ... + nums[i-1]` (with `prefix[0] = 0`, capturing "sum of zero elements"). This is the **prefix sum array**.

Key identity:
```
sum(left, right) = prefix[right + 1] - prefix[left]
```

Why? Because `prefix[right + 1]` is sum of indices 0..right, and subtracting `prefix[left]` (sum of 0..left-1) leaves exactly indices left..right.

So each query becomes **two array lookups and a subtraction** — O(1).

Precomputing the prefix array is O(n) once. Total work: O(n + q). Dramatic improvement.

----------------------------------------

## Step 4: Building the Prefix Array

```
prefix = array of length n + 1
prefix[0] = 0
for i in 0..n-1:
    prefix[i + 1] = prefix[i] + nums[i]
```

Why `n + 1` entries and not `n`? The offset lets us express `sumRange(0, r) = prefix[r+1] - prefix[0] = prefix[r+1]` without special-casing the left = 0 boundary. `prefix[0] = 0` acts as a sentinel.

----------------------------------------

## Step 5: Trace

`nums = [-2, 0, 3, -5, 2, -1]`. n = 6.

Build prefix:
- prefix[0] = 0.
- prefix[1] = 0 + (-2) = -2.
- prefix[2] = -2 + 0 = -2.
- prefix[3] = -2 + 3 = 1.
- prefix[4] = 1 + (-5) = -4.
- prefix[5] = -4 + 2 = -2.
- prefix[6] = -2 + (-1) = -3.

Queries:
- sumRange(0, 2) = prefix[3] - prefix[0] = 1 - 0 = **1**. ✓
- sumRange(2, 5) = prefix[6] - prefix[2] = -3 - (-2) = **-1**. ✓
- sumRange(0, 5) = prefix[6] - prefix[0] = **-3**. ✓

All match.

----------------------------------------

## Step 6: Why Prefix Sum Works

Prefix sum is a **cumulative function** of the array — an "integral" in discrete form. And range sum is a difference of integrals:

```
sum(L, R) = F(R+1) - F(L)         # where F(k) = nums[0] + ... + nums[k-1]
```

This mirrors the Fundamental Theorem of Calculus: `∫[L to R] f = F(R) - F(L)`. Prefix sums are the discrete analogue.

The technique generalizes to any associative, invertible operation:
- Sum (inverse is subtraction).
- XOR (inverse is XOR itself — self-inverse).
- Product modulo a prime (inverse is modular inverse).

For min/max (not invertible), we need a different structure — a sparse table or segment tree.

----------------------------------------

## Step 7: Name It

**Prefix sums** (also: cumulative sums, running totals). Fundamental technique for:
- Range sum queries on immutable arrays.
- Subarray sum equals K (hash the prefixes, look for `prefix - K`).
- 2D versions: `prefix[i][j]` for rectangular sum queries in constant time.
- Difference arrays (the inverse operation, for range updates with point queries).

The segment tree (this topic's main tool) generalizes to support updates, but for a pure **immutable** query problem, a prefix array is lighter and faster.

----------------------------------------

## Step 8: Complexity

- **Constructor**: O(n) to build prefix.
- **sumRange**: O(1) per query.
- **Space**: O(n) extra for the prefix array.

For q queries: O(n + q). Compare with naive: O(n·q). When q is large, prefix sums win by a factor of n.

----------------------------------------

## Step 9: C++ Implementation

```cpp
class NumArray {
    vector<int> prefix;
public:
    NumArray(vector<int>& nums) {
        prefix.assign(nums.size() + 1, 0);
        for (int i = 0; i < (int)nums.size(); ++i) {
            prefix[i + 1] = prefix[i] + nums[i];
        }
    }

    int sumRange(int left, int right) {
        return prefix[right + 1] - prefix[left];
    }
};
```

Three critical details:
1. `prefix` has length `n + 1`, with `prefix[0] = 0`.
2. `prefix[i + 1] = prefix[i] + nums[i]` — each prefix extends the previous.
3. Query: `prefix[right + 1] - prefix[left]`. The `+1` on right picks up index `right` itself.

A common bug is using `prefix[right] - prefix[left]`, which misses one element. Writing out the indexing on a small example prevents this.

----------------------------------------

## Step 10: Follow-up Questions

- **Range Sum Query – Mutable.** The array changes. Segment tree or Fenwick tree (Binary Indexed Tree): both O(log n) update/query.
- **2D Range Sum – Immutable.** Precompute `prefix[i][j]` = sum of rectangle (0, 0) to (i-1, j-1). Query via 4-corner inclusion-exclusion.
- **Range XOR Query – Immutable.** XOR is self-inverse: `prefix[r+1] ^ prefix[l]` gives the range XOR.
- **Range Product – Immutable.** Product of prefixes divided — but beware of zeros and modular inverse.
- **Range Minimum Query.** Min isn't invertible; use sparse table (O(n log n) build, O(1) query) or segment tree (O(n) build, O(log n) query).
- **Why include prefix[0] = 0?** Makes the subtraction formula uniform across all left values, including left = 0.
- **Can we update nums[i] after construction?** Not with prefix sums — one update forces O(n) recompute. For updates, use a Fenwick tree or segment tree instead.
