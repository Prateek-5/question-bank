# Trapping Rain Water

**Problem Link:**
<a href="https://leetcode.com/problems/trapping-rain-water/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/trapping-rain-water/</a>

**Topic:**
Arrays & Matrices

----------------------------------------

## Step 1: The Problem

You have an array `height` representing a 2D elevation map (each entry is a bar's height, bars are 1 unit wide). After rain, how much water is trapped?

Example: `[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]` → trapped water = **6**.

Let me draw it to make sure I understand:

```
                    ██
        ██          ██      ██
        ██    ██    ██  ██  ██  ██
  ██    ██    ██    ██  ██  ██  ██
0 1 0 2 1 0 1 3 2 1 2 1
```

Water pools wherever there's a "valley" — a lower bar with taller bars on both sides. The water level at any position is bounded by the shorter of the two side walls.

----------------------------------------

## Step 2: The Key Question, Per Position

Forget the whole array for a moment. Focus on one position `i`. How much water can sit on top of bar `i`?

Water fills until it would spill over the nearest tall wall on either side. So the water height above `i` is:

> `water_above(i) = min(tallest_bar_to_left_of_i, tallest_bar_to_right_of_i) - height[i]`

If that value is negative (which happens when `height[i]` is already taller than both side maxes — like at a peak), water is 0.

So the total trapped water is:

> `total = sum over all i of max(0, min(left_max[i], right_max[i]) - height[i])`

Already, this tells us the answer. The remaining question is: how do we compute `left_max[i]` and `right_max[i]` efficiently?

----------------------------------------

## Step 3: Precompute Prefix and Suffix Maxes

- `left_max[i]` = max of `height[0..i]`. Computed in one pass left-to-right.
- `right_max[i]` = max of `height[i..n-1]`. Computed in one pass right-to-left.

Then iterate again and accumulate `water` per position.

```cpp
vector<int> L(n), R(n);
L[0] = height[0];
for (int i = 1; i < n; ++i) L[i] = max(L[i-1], height[i]);
R[n-1] = height[n-1];
for (int i = n-2; i >= 0; --i) R[i] = max(R[i+1], height[i]);

int water = 0;
for (int i = 0; i < n; ++i)
    water += min(L[i], R[i]) - height[i];
```

Works. O(n) time, O(n) extra space.

Can we do better on space?

----------------------------------------

## Step 4: The Two-Pointer Insight

Here's the beautiful observation that eliminates the extra arrays.

Suppose I have two pointers, `l` at the start and `r` at the end. I also keep `left_max` = max I've seen from the left so far, and `right_max` = max from the right so far.

Claim: at each step, the pointer at the **shorter side** knows its own water contribution without needing to look at the other side.

**Why?** Suppose `height[l] < height[r]`. The relevant question for position `l` is "what's the bounding height on both sides?" Well:

- Left bound = `left_max` (the max from positions `0..l`, which I've been tracking).
- Right bound = the max of `height[l..n-1]`. We don't know this exactly, but we know it's **at least `height[r]`** (because r is to the right of l and its height is known). And we know `left_max ≤ height[r]` (since we know `height[l] < height[r]`, and `left_max` was at most the tallest on the left which... hmm, not quite obvious yet).

Let me be more careful. The condition is `height[l] < height[r]`. We want to argue the water above position `l` is exactly `left_max - height[l]` (assuming left_max ≥ height[l]).

Why is the right bound at position `l` *at least* `left_max`? Because the right bound is the max of `height[l+1..n-1]`, which includes `height[r]`, so it's at least `height[r]`. And `height[r] > height[l]`. But that alone doesn't give us `right_bound ≥ left_max`...

OK, let me re-examine. The water at position `l` is `min(left_max, right_bound) - height[l]`.

If `left_max ≤ right_bound`, water = `left_max - height[l]`.
If `left_max > right_bound`, water = `right_bound - height[l]`.

Can `left_max > right_bound` happen when `height[l] < height[r]`?

`right_bound` is max of `height[l+1..n-1]`, which ≥ `height[r]`. So `right_bound ≥ height[r] > height[l]`. But `left_max` could still be bigger than `right_bound` in theory.

Hmm, so the two-pointer argument isn't immediately obvious. Let me think differently.

----------------------------------------

## Step 5: The Right Intuition

Here's the cleaner phrasing. Maintain `left_max` and `right_max` as the best each pointer has seen on its own side.

Invariant: `left_max = max(height[0..l])` and `right_max = max(height[r..n-1])`. As the pointers move inward, these maxes only grow.

Decision rule: at each step, if `left_max < right_max`, process position `l`:
- We know `right_max ≥ left_max`, so `min(left_max, right_bound at l) = left_max` (because `right_bound at l ≥ right_max ≥ left_max`).
- Water = `left_max - height[l]` (or 0 if negative).
- Advance `l`, and update `left_max` if `height[l]` exceeds it.

Symmetric for the other side.

Wait, I need to verify: `right_bound at l ≥ right_max`. The `right_bound at l` is max of `height[l+1..n-1]`. `right_max` is max of `height[r..n-1]`. Since `l+1 ≤ r`, the first range is a superset of the second — so `right_bound at l ≥ right_max`. ✓

So the clever simplification is: we don't need `right_bound` (the max of all elements to the right of l). We only need to know that `right_max ≥ left_max`, because that's enough to tell us `left_max` is the binding constraint.

And when we choose which pointer to advance, we pick the side with the smaller max, because that's the side where we're **certain** about the water contribution.

----------------------------------------

## Step 6: Pseudocode

```
l = 0, r = n - 1
left_max = 0, right_max = 0
water = 0
while l < r:
    if height[l] < height[r]:
        if height[l] >= left_max:
            left_max = height[l]
        else:
            water += left_max - height[l]
        l++
    else:
        if height[r] >= right_max:
            right_max = height[r]
        else:
            water += right_max - height[r]
        r--
```

At each step, we process one position and move one pointer. The loop runs exactly `n - 1` times.

----------------------------------------

## Step 7: Dry Run on `[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]`

```
l=0, r=11, left_max=0, right_max=0, water=0

height[l]=0, height[r]=1. h[l] < h[r] → process l.
  h[l]=0 ≥ left_max=0 → update left_max=0. (no water added)
  l=1.

l=1, r=11. h[l]=1, h[r]=1. Tie, go else branch → process r.
  h[r]=1 ≥ right_max=0 → right_max=1.
  r=10.

l=1, r=10. h[l]=1, h[r]=2. h[l]<h[r] → process l.
  h[l]=1 ≥ left_max=0 → left_max=1.
  l=2.

l=2, r=10. h[l]=0, h[r]=2. h[l]<h[r] → process l.
  h[l]=0 < left_max=1 → water += 1-0 = 1. total=1.
  l=3.

l=3, r=10. h[l]=2, h[r]=2. Tie, process r.
  h[r]=2 ≥ right_max=1 → right_max=2.
  r=9.

l=3, r=9. h[l]=2, h[r]=1. h[l]>h[r] → process r.
  h[r]=1 < right_max=2 → water += 2-1 = 1. total=2.
  r=8.

l=3, r=8. h[l]=2, h[r]=2. Tie → process r.
  h[r]=2 ≥ right_max → right_max=2. (unchanged).
  r=7.

l=3, r=7. h[l]=2, h[r]=3. h[l]<h[r] → process l.
  h[l]=2 ≥ left_max=1 → left_max=2.
  l=4.

l=4, r=7. h[l]=1, h[r]=3. process l.
  h[l]=1 < left_max=2 → water += 1. total=3.
  l=5.

l=5, r=7. h[l]=0. process l.
  water += 2 - 0 = 2. total=5.
  l=6.

l=6, r=7. h[l]=1. process l.
  water += 2-1 = 1. total=6.
  l=7.

l=7, r=7. Loop ends.
```

Total = **6**. ✓

That matches the known answer.

The neat thing about this trace: we never kept explicit `right_max` for positions to the right of `l` (the global right_max), yet it was always enough. The invariant carried the argument.

----------------------------------------

## Step 8: Complexity

Time: each pointer advances toward the center, total n-1 steps. **O(n)**.
Space: four integer variables. **O(1)**.

From O(n) time with O(n) space down to O(n) time with O(1) space. The two-pointer trick costs us nothing and saves us an array.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int trap(vector<int>& h) {
    int l = 0, r = h.size() - 1;
    int left_max = 0, right_max = 0;
    int water = 0;
    while (l < r) {
        if (h[l] < h[r]) {
            if (h[l] >= left_max) left_max = h[l];
            else water += left_max - h[l];
            l++;
        } else {
            if (h[r] >= right_max) right_max = h[r];
            else water += right_max - h[r];
            r--;
        }
    }
    return water;
}
```

----------------------------------------

## Step 10: Follow-up Questions

- **2D rain water (Trapping Rain Water II).** Harder — use a min-heap BFS starting from the boundary cells, always processing the shortest wall first.
- **Return the amount of water above each bar, not just the total.** Same two-pointer structure, but record per-position additions.
- **What if bars have variable widths?** Multiply the water contribution by the width.
- **Streaming version — bars arrive one by one.** Can't two-pointer anymore; use a monotonic stack.
- **Monotonic-stack solution for the same problem.** At each bar, pop shorter bars on top, and each pop corresponds to a bucket of water. It's another elegant O(n) approach.
