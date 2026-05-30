# Magnetic Force Between Two Balls

**Problem Link:**
<a href="https://leetcode.com/problems/magnetic-force-between-two-balls/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/magnetic-force-between-two-balls/</a>

**Topic:**
Searching / Binary Search

----------------------------------------

## Step 1: Understand the Problem

You have `n` baskets at integer positions on a 1D line (given in `position` array). You want to place `m` balls into these baskets such that the **minimum pairwise distance** between any two balls is **maximized**.

Return that maximum-minimum distance.

Example: `position = [1, 2, 3, 4, 7]`, m = 3.

Need to place 3 balls. Which baskets give the best "min distance"?

- Place at positions 1, 3, 7: min distance = min(|3-1|, |7-3|) = min(2, 4) = 2. But wait, |7 - 1| = 6 is also a pair; we want pairwise min. Actually for consecutive placement, only adjacent pairs matter for min. So min pair-distance = min(3-1, 7-3) = 2.
- Place at 1, 2, 3: min distance = 1. Worse.
- Place at 1, 4, 7: min = 3. Better!

Answer: **3**. Max-min distance = 3.

The objective is the classic "Aggressive Cows" problem.

----------------------------------------

## Step 2: Intuition — Bigger Distance = Harder

Notice: if we can place all m balls with minimum distance ≥ d, we can definitely place them with min distance ≥ d' for any d' ≤ d (just use the same placement — it still has min distance ≥ d ≥ d').

So the predicate "**can place m balls with min distance ≥ d**" is **monotonic in d**: true for small d, false for large d. Binary search on d.

----------------------------------------

## Step 3: Checking Feasibility Greedily

For a given d, can we place m balls with min distance ≥ d?

Greedy: sort positions. Place the first ball at position[0]. Place the next ball at the leftmost position ≥ previous + d. Repeat until m balls placed or positions exhausted.

If we placed all m, then d is feasible.

```
def canPlace(positions, m, d):
    count = 1
    last = positions[0]
    for p in positions[1:]:
        if p - last >= d:
            count++
            last = p
            if count == m: return True
    return count >= m
```

Why greedy works: placing the first ball at the leftmost position gives the most room for the remaining balls. Delaying would only make the next placement harder.

----------------------------------------

## Step 4: Binary Search on d

Search d in a range. Lower bound: 1 (min positive distance). Upper bound: max - min (the overall range).

```
sort(positions)
lo = 1
hi = positions[n-1] - positions[0]

while lo < hi:
    mid = lo + (hi - lo + 1) / 2   # upper-mid to find "largest feasible"
    if canPlace(positions, m, mid):
        lo = mid   # d = mid feasible; try larger
    else:
        hi = mid - 1   # d = mid infeasible; try smaller

return lo
```

Subtle detail: we're finding the **largest** feasible d. The search pattern uses `(lo + hi + 1) / 2` (upper-mid) to avoid infinite loops when lo and hi are adjacent.

----------------------------------------

## Step 5: Trace on `[1, 2, 3, 4, 7]`, m = 3

Sort: already sorted.

lo = 1, hi = 7 - 1 = 6.

```
Iter 1: mid = (1+6+1)/2 = 4. Feasibility check for d=4:
  Place at 1. Next ≥ 1+4=5: position 7. Place there.
  Count = 2. Need m=3. Fail.
  lo=1, hi=3.

Iter 2: mid = (1+3+1)/2 = 2 (wait, that's (1+3+1)/2 = 2.5 → 2). 
  Actually (lo+hi+1)/2 = (1+3+1)/2 = 2. Feasibility for d=2:
  Place at 1. Next ≥ 3: position 3. Place. Next ≥ 5: position 7. Place.
  Count = 3 ≥ m. Feasible.
  lo=2.

Iter 3: lo=2, hi=3. mid=(2+3+1)/2=3. Feasibility for d=3:
  Place at 1. Next ≥ 4: position 4. Place. Next ≥ 7: position 7. Place.
  Count = 3 ≥ m. Feasible.
  lo=3.

Iter 4: lo=3, hi=3. Exit.
Return 3.
```

✓ Matches expected.

----------------------------------------

## Step 6: Why Upper-Mid?

Standard binary search with `(lo + hi) / 2` on "find largest feasible x":
- If feasible: lo = mid.
- Else: hi = mid - 1.

If lo = 2, hi = 3, mid = (2+3)/2 = 2 (integer division). If feasible, lo = 2 again. Infinite loop.

Use upper-mid `(lo + hi + 1) / 2`:
- lo=2, hi=3, mid=3. If feasible, lo = 3. Next iteration lo == hi, exit.

The "+1" in the midpoint formula is the fix. It's the standard trick for "find largest" binary search.

----------------------------------------

## Step 7: Complexity

Time: binary search has O(log(max_pos)) iterations. Each feasibility check is O(n). Total **O(n · log(max_pos))**.
Space: **O(1)**.

For n = 10^5 and max_pos = 10^9, that's ~3 × 10^6 ops — fast.

----------------------------------------

## Step 8: Name It

**Binary search on the answer** applied to a "maximize the minimum" optimization. Pattern:
1. Recognize: "minimum of something, maximized."
2. Make the objective a monotonic predicate.
3. Binary search for the boundary.

Same template solves:
- Koko Eating Bananas (minimize the max rate).
- Capacity to Ship Packages Within D Days.
- Split Array Largest Sum.
- Aggressive Cows.

The greedy feasibility check inside the binary search is often the problem-specific piece.

----------------------------------------

## Step 9: Complexity

Time: **O(n log n)** for sort + **O(n log(max_pos))** for binary search. Overall dominated by the binary search for typical ranges.
Space: **O(1)** beyond the sort.

----------------------------------------

## Step 10: C++ Implementation

```cpp
class Solution {
    bool canPlace(vector<int>& position, int m, int d) {
        int count = 1;
        int last = position[0];
        for (int i = 1; i < (int)position.size(); ++i) {
            if (position[i] - last >= d) {
                count++;
                last = position[i];
                if (count >= m) return true;
            }
        }
        return false;
    }

public:
    int maxDistance(vector<int>& position, int m) {
        sort(position.begin(), position.end());
        int lo = 1;
        int hi = position.back() - position.front();

        while (lo < hi) {
            int mid = lo + (hi - lo + 1) / 2;
            if (canPlace(position, m, mid)) lo = mid;
            else hi = mid - 1;
        }
        return lo;
    }
};
```

Two parts clearly separated: feasibility check (`canPlace`) and binary search (`maxDistance`).

The sort is essential — greedy only works on sorted positions.

----------------------------------------

## Step 11: Follow-up Questions

- **Minimize the max distance instead.** Inverts the monotonicity; binary search direction flips.
- **Return the actual placement.** Track positions during the successful feasibility check.
- **Weighted positions (some prefer certain baskets).** Harder — greedy may fail; need DP.
- **Balls of different "sizes" that can't overlap.** Adjust the feasibility rule.
- **Mix of positions on a 2D plane.** Becomes a different, harder problem (placing in the plane).
- **What if we want the minimum pairwise distance maximized, not just adjacent-pairs distance?** For linear positions with sorted placement, adjacent-min is the overall min. For 2D or unsorted data, all pairs matter.
