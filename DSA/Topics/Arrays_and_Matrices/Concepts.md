# Arrays & Matrices — Concepts Guide

----------------------------------------

## 1. Introduction

Array and matrix problems test your spatial reasoning and your ability to recognize counting patterns. Many of them have clever O(n) or O(n log n) solutions hiding behind what looks like a cubic brute force. The skill is seeing the pattern.

----------------------------------------

## 2. Real-Life Analogy

Think of a building with rooms arranged in a grid. If someone asks 'how many rooms with view-of-ocean exist on floors 3 through 7?', you could walk and count every room — or you could keep per-floor pre-counts and sum five numbers. The second is the prefix-sum / per-row precomputation approach.

----------------------------------------

## 3. Core Idea

Array and matrix problems often reduce to: prefix sums for range queries, sliding windows for contiguous constraints, contribution counting (asking 'how many sub-ranges include this element?'), and clever traversals (spirals, diagonals, boundaries). The matrix versions just extend 1D ideas to two axes.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

You're in array/matrix territory when:

- **You're scanning sub-ranges or sub-rectangles.**
- **The problem involves rows, columns, diagonals, or boundaries.**
- **You need per-element aggregated info across rows/columns.**
- **The problem is about in-place mutation** (rotate, transpose).

----------------------------------------

## 5. Types / Variations

- **Per-row/column precomputation** (lucky numbers: row min ∩ col max).
- **Contribution counting** (sum of all subarray ranges, trapping rain water).
- **Boundary / spiral traversals.**
- **2D binary search** (staircase search).
- **In-place matrix rotation** (transpose + reverse).

----------------------------------------

## 6. Step-by-Step Working

**Trapping Rain Water (two-pointer):**
1. Maintain two pointers l, r and running `leftMax`, `rightMax`.
2. Move the pointer with the smaller height inward.
3. If its current height is ≥ maxOnItsSide, update maxOnItsSide. Else add (maxOnItsSide - height) to water.
4. Continue until l == r.

**Sum of all subarray ranges via contribution:**
1. Each element `a[i]` appears in `(i+1) * (n-i)` subarrays.
2. Sum contribution accordingly.

----------------------------------------

## 7. Visual Explanation

**Spiral traversal of a 3×3 matrix:**

```
1 → 2 → 3
        ↓
8 → 9   4
↑       ↓
7 ← 6 ← 5
```

Order: 1, 2, 3, 4, 5, 6, 7, 8, 9 — walking the perimeter, shrinking boundaries, then continuing inward.

----------------------------------------

## 8. Code Templates (C++)

```cpp
// Trapping Rain Water (two-pointer)
int trap(vector<int>& h) {
    int l = 0, r = h.size() - 1, ml = 0, mr = 0, water = 0;
    while (l < r) {
        if (h[l] < h[r]) {
            ml = max(ml, h[l]);
            water += ml - h[l];
            l++;
        } else {
            mr = max(mr, h[r]);
            water += mr - h[r];
            r--;
        }
    }
    return water;
}

// Matrix rotation 90 CW: transpose + reverse rows
for (int i = 0; i < n; ++i)
    for (int j = i + 1; j < n; ++j) swap(M[i][j], M[j][i]);
for (auto& row : M) reverse(row.begin(), row.end());
```

----------------------------------------

## 9. Common Mistakes

- **Boundary errors** on spiral / diagonal traversals.
- **Integer overflow** when summing large matrices.
- **Forgetting to reset shared state** across test cases.
- **In-place transforms that corrupt unvisited cells** — use a marker or a buffer.

----------------------------------------

## 10. Interview Insights

Array/matrix problems favor candidates who think visually. Interviewers want to see:

1. **A small diagram sketched to clarify indices.**
2. **Recognition of the underlying pattern** (prefix sum, sliding window, contribution).
3. **Careful index handling** without buggy off-by-ones.
4. **In-place vs extra-space trade-offs.**

Draw the first few iterations on paper if allowed. It's the fastest way to catch your own bugs.
