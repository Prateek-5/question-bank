# 1-D & 2-D Arrays — Concepts Guide

----------------------------------------

## 1. Introduction

Arrays are the most fundamental data structure — a contiguous block of memory giving you O(1) random access. Most 'array' problems are really problems in disguise: sliding window, prefix sums, two pointers, or clever indexing. Mastering arrays means mastering those patterns.

----------------------------------------

## 2. Real-Life Analogy

Think of a row of mailboxes. Each mailbox has an address (index) and a piece of content (value). You can walk directly to any mailbox — that's O(1) access. If you want the running total of letters in mailboxes 0 through i, you don't want to recount every time — you precompute a prefix sum, and answer any prefix query in O(1). Arrays are exactly this: addressable storage with clever precomputation on top.

----------------------------------------

## 3. Core Idea

Array problems usually reduce to one of three tools: **prefix sums** (for range sum queries), **sliding window** (for contiguous subarray constraints), or **in-place transformations** (rotate, reverse, partition). 2D arrays add row/column/diagonal traversals and 2D prefix sums. The trick is spotting which tool applies — often just rephrasing the problem in your head is enough.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Array techniques are useful when:

- **You need range sums or aggregates** → prefix sum.
- **You're looking at contiguous sub-segments** → sliding window or prefix sum.
- **Input is sorted** → two pointers or binary search.
- **You need to transform in place** → careful index manipulation.
- **2D structure matters (rows/columns/diagonals)** → per-row/col precomputation.

----------------------------------------

## 5. Types / Variations

- **1D prefix sum:** O(1) range sum queries.
- **2D prefix sum:** O(1) rectangular sum queries via inclusion-exclusion.
- **Difference array:** O(1) range update, O(n) reconstruct.
- **In-place rotation:** reverse-reverse-reverse trick for cyclic shifts.
- **Spiral / diagonal traversals** for matrices.

----------------------------------------

## 6. Step-by-Step Working

**Prefix sum (1D):**
1. Build `P[0] = 0`, `P[i] = P[i-1] + a[i-1]`.
2. Query sum of `a[l..r]` = `P[r+1] - P[l]`.

**2D prefix sum:**
1. `P[i+1][j+1] = M[i][j] + P[i][j+1] + P[i+1][j] - P[i][j]`.
2. Rectangle `(r1,c1)-(r2,c2)` sum = `P[r2+1][c2+1] - P[r1][c2+1] - P[r2+1][c1] + P[r1][c1]`.

**Sliding window:**
1. Extend right pointer `r` greedily.
2. When the window violates a constraint, advance left pointer `l`.
3. Track the best value so far.

----------------------------------------

## 7. Visual Explanation

**Prefix sum on `a = [3, 1, 4, 1, 5]`:**

```
i:  0  1  2  3  4  5
P:  0  3  4  8  9  14
```

**Sum of a[1..3] = P[4] - P[1] = 9 - 3 = 6** (matches 1 + 4 + 1).

**Sliding window on longest substring with ≤ 2 distinct chars:**

```
s = 'eceba'

Step 1: l=0, r=0 → 'e'      distinct=1  best=1
Step 2: l=0, r=1 → 'ec'     distinct=2  best=2
Step 3: l=0, r=2 → 'ece'    distinct=2  best=3
Step 4: l=0, r=3 → 'eceb'   distinct=3, shrink l until distinct=2 → l=2
                  'eb'      best=3
...
```

----------------------------------------

## 8. Code Templates (C++)

```cpp
// 1D prefix sum
vector<int> P(n + 1, 0);
for (int i = 0; i < n; ++i) P[i+1] = P[i] + a[i];
int rangeSum = P[r+1] - P[l];

// 2D prefix sum
int n = M.size(), m = M[0].size();
vector<vector<int>> P(n+1, vector<int>(m+1, 0));
for (int i = 0; i < n; ++i) for (int j = 0; j < m; ++j)
    P[i+1][j+1] = M[i][j] + P[i][j+1] + P[i+1][j] - P[i][j];

// Sliding window skeleton
int l = 0, best = 0;
for (int r = 0; r < n; ++r) {
    // include a[r]
    while (/* window invalid */) {
        // exclude a[l], l++
    }
    best = max(best, r - l + 1);
}
```

----------------------------------------

## 9. Common Mistakes

- **Off-by-one errors** with prefix arrays. Always use size n+1 and query `P[r+1] - P[l]`.
- **Row-major vs column-major confusion** in 2D problems.
- **Forgetting to reset state** between multiple test cases.
- **Mutating an array being iterated** — classic source of bugs.
- **Integer overflow** on sums of large arrays — use `long long`.

----------------------------------------

## 10. Interview Insights

Array problems test core competence. Interviewers want to see:

1. **Do you spot the pattern quickly?** Prefix sum, sliding window, or two pointers should be immediate reflexes.
2. **Can you index without errors?** Off-by-ones cost easy points.
3. **Can you reason about in-place vs extra-space trade-offs?**
4. **Do you know STL helpers** (`partial_sum`, `accumulate`, `sort`)?

Many interview problems that look complex reduce to a 10-line array loop once you see the pattern. Train your eye for those shapes.
