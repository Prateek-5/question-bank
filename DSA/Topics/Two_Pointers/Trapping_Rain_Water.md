# Trapping Rain Water (Two Pointers)

**Problem Link:**
<a href="https://leetcode.com/problems/trapping-rain-water/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/trapping-rain-water/</a>

**Topic:**
Two Pointers

----------------------------------------

## Step 1: Understand the Geometry

Heights array `height[]` represents bars of unit width. Rain falls; water settles between bars. Compute how much water is trapped after it rains.

Visualize `height = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]`:

```
        |
    |   | |
|   | | | | |
| | | | | | | |
0 1 0 2 1 0 1 3 2 1 2 1
```

Water settles in the "valleys." Total trapped = **6**.

----------------------------------------

## Step 2: Water Above Each Bar

For each index i, the water sitting on top of bar i has height:

```
water[i] = max(0, min(maxLeft[i], maxRight[i]) - height[i])
```

Where:
- `maxLeft[i]` = maximum height among bars 0..i.
- `maxRight[i]` = maximum height among bars i..n-1.

Intuition: water at index i can rise to the **lower** of the two surrounding walls (the left-max and right-max). If height[i] is less than that level, the difference is trapped on top of bar i.

Sum water[i] over all indices → total.

----------------------------------------

## Step 3: Precomputed Arrays — O(n) Space

Compute maxLeft and maxRight in two sweeps:

```
maxLeft[0] = height[0]
for i in 1..n-1: maxLeft[i] = max(maxLeft[i-1], height[i])

maxRight[n-1] = height[n-1]
for i from n-2 to 0: maxRight[i] = max(maxRight[i+1], height[i])

total = 0
for i in 0..n-1:
    total += max(0, min(maxLeft[i], maxRight[i]) - height[i])
```

O(n) time, O(n) space.

----------------------------------------

## Step 4: Two-Pointer Optimization — O(1) Space

The clever trick. Use two pointers `l = 0`, `r = n - 1`, and track `leftMax` and `rightMax` as we scan inward.

Key insight: at any step, compare `height[l]` and `height[r]`:
- If `height[l] < height[r]`: water level at index l is bounded by leftMax (since rightMax ≥ height[r] > height[l] ≥ ... , so the left wall is the binding constraint).
  - Update leftMax. Add `leftMax - height[l]` to total. Advance l.
- Else (height[l] >= height[r]): symmetric on the right.
  - Update rightMax. Add `rightMax - height[r]` to total. Retreat r.

This works because when processing the shorter side, we know the opposite side has at least that height somewhere — so the min of the two walls is determined by the current side's max.

O(n) time, O(1) space.

----------------------------------------

## Step 5: Trace Two-Pointer on `[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]`

Initial: l=0, r=11. leftMax = 0, rightMax = 0. total = 0.

```
h[0]=0, h[11]=1. h[l] < h[r]. Process left.
  leftMax = max(0, 0) = 0. Add 0 - 0 = 0. l=1.
h[1]=1, h[11]=1. h[l] >= h[r]. Process right.
  rightMax = max(0, 1) = 1. Add 1 - 1 = 0. r=10.
h[1]=1, h[10]=2. h[l] < h[r]. Process left.
  leftMax = max(0, 1) = 1. Add 1 - 1 = 0. l=2.
h[2]=0, h[10]=2. Process left.
  leftMax = max(1, 0) = 1. Add 1 - 0 = 1. total=1. l=3.
h[3]=2, h[10]=2. Process right.
  rightMax = max(1, 2) = 2. Add 2 - 2 = 0. r=9.
h[3]=2, h[9]=1. Process right.
  rightMax = max(2, 1) = 2. Add 2 - 1 = 1. total=2. r=8.
h[3]=2, h[8]=2. Process right.
  rightMax = max(2, 2) = 2. Add 2 - 2 = 0. r=7.
h[3]=2, h[7]=3. Process left.
  leftMax = max(1, 2) = 2. Add 2 - 2 = 0. l=4.
h[4]=1, h[7]=3. Process left.
  leftMax = max(2, 1) = 2. Add 2 - 1 = 1. total=3. l=5.
h[5]=0, h[7]=3. Process left.
  leftMax = max(2, 0) = 2. Add 2 - 0 = 2. total=5. l=6.
h[6]=1, h[7]=3. Process left.
  leftMax = max(2, 1) = 2. Add 2 - 1 = 1. total=6. l=7.
l == r. Stop.
```

Total: **6**. ✓

----------------------------------------

## Step 6: Why the Two-Pointer Logic Works

We're essentially "walking inward from the shorter side." When height[l] < height[r], the bar on the right is taller than the current left bar. Therefore:
- rightMax is already ≥ height[r] > height[l].
- So min(leftMax, rightMax) = leftMax (we only need leftMax to compute water at position l).
- We can safely process position l knowing its water level is determined purely by leftMax.

Symmetric argument when height[l] >= height[r]. The "shorter side moves first" invariant keeps us honest.

----------------------------------------

## Step 7: Name It

**Two-pointer converging walk**, a cousin of the classic "container with most water" two-pointer. Applications:
- Trapping Rain Water (this one).
- Container With Most Water.
- Merge two sorted arrays.
- Partition problems.

The pattern: two pointers at opposite ends, move the one whose condition is "weaker," amortized O(n).

Related approaches for this specific problem:
- **Stack-based**: process bars with a monotonic decreasing stack; settle water when a taller bar arrives.
- **DP with maxLeft/maxRight arrays**: intuitive, O(n) space.

----------------------------------------

## Step 8: Complexity

Two-pointer: **O(n)** time, **O(1)** space.
DP with arrays: O(n) time, O(n) space.
Stack-based: O(n) time, O(n) space.

All linear time; two-pointer wins on space.

----------------------------------------

## Step 9: C++ Implementation (Two Pointers)

```cpp
int trap(vector<int>& height) {
    int l = 0, r = height.size() - 1;
    int leftMax = 0, rightMax = 0;
    int total = 0;

    while (l < r) {
        if (height[l] < height[r]) {
            leftMax = max(leftMax, height[l]);
            total += leftMax - height[l];
            l++;
        } else {
            rightMax = max(rightMax, height[r]);
            total += rightMax - height[r];
            r--;
        }
    }
    return total;
}
```

Eight lines of loop body; the logic is tight.

----------------------------------------

## Step 10: Follow-up Questions

- **2D Trapping Rain Water** (rectangular grid of heights). Min-heap / priority queue; flood-fill from the boundary with the "current water level" increasing.
- **Return water level at each position.** Same algorithm — just record `min(leftMax, rightMax)` at each step.
- **Dynamic heights (bars change).** Precompute structure needed; heap-based approach for 2D.
- **Why two pointers and not DP?** Both work; two-pointer is O(1) space vs O(n).
- **Can water flow out sideways?** No — walls are infinite in 1D; water is bounded entirely by the height profile.
- **What if all heights are equal?** No water is trapped (no valleys). The algorithm correctly returns 0.
