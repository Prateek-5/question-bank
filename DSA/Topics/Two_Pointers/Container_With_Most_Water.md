# Container With Most Water

**Problem Link:**
<a href="https://leetcode.com/problems/container-with-most-water/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/container-with-most-water/</a>

**Topic:**
Two Pointers

----------------------------------------

## Step 1: Visualize the Problem

You have an array `h` where `h[i]` is the height of a vertical line at x-coordinate `i`. Pick any two lines. They form the two sides of a rectangular container holding water between them. The water height is limited by the *shorter* of the two lines. The width is the distance between them.

Area formed by lines `i` and `j` (with `i < j`):

```
area(i, j) = min(h[i], h[j]) * (j - i)
```

Find the maximum possible area.

Quick sanity check with `h = [1, 8, 6, 2, 5, 4, 8, 3, 7]`:

- Lines at indices 1 and 8: heights 8 and 7, width = 7. Area = min(8,7) * 7 = **49**.
- Lines at indices 1 and 2: heights 8 and 6, width = 1. Area = 6.

The expected answer for this input is 49. Good.

----------------------------------------

## Step 2: Brute Force First

Try every pair `(i, j)` with `i < j`:

```cpp
int best = 0;
for (int i = 0; i < n; ++i)
    for (int j = i + 1; j < n; ++j)
        best = max(best, min(h[i], h[j]) * (j - i));
```

That's O(n²). For `n = 10^5`, that's 10^10 ops — way too slow.

So we need something faster. But to find a better algorithm, we need an insight about the problem's structure. Let me think about what's true about optimal pairs.

----------------------------------------

## Step 3: A Key Observation Through Experimentation

Imagine the widest possible container — lines at index 0 and index n-1. That gives us the maximum width. The area depends on `min(h[0], h[n-1])`.

Now, suppose we want to try another pair. What happens if we keep one endpoint fixed and shrink the width? Then we sacrifice width. To make up for it, we'd need a taller pair. But at most, the smaller side can rise to as tall as the *other* side — because `min()` caps at the smaller one.

This suggests: **start wide, then greedily move the shorter side inward**. Here's the reasoning that makes this work — and it's the heart of the whole algorithm.

Suppose `h[l] < h[r]` (left side is shorter). The current area is `h[l] * (r - l)`. Now think about any other pair that includes this `l`:

- Any pair `(l, r')` with `r' < r`. The height is `min(h[l], h[r'])`, which is at most `h[l]` (since `h[l]` is already the left, and `min` can't exceed it). So the area is at most `h[l] * (r' - l)`, which is **less than** our current area because `r' - l < r - l`.

In other words, the current `l` can never be part of a better pair — because any pair with `l` and a closer-right has both smaller or equal height and smaller width. Pairs with `l` and a farther-right don't exist (we started at the widest).

So `l` is useless. We should move it inward. The same logic applies symmetrically when the right side is shorter.

**Rule:** always move the *shorter* side inward.

This is the core insight. It's not a lucky guess — we proved that the current shorter side cannot contribute to a better pair, so we can safely discard it.

----------------------------------------

## Step 4: The Algorithm

```
l = 0, r = n - 1, best = 0
while l < r:
    area = min(h[l], h[r]) * (r - l)
    best = max(best, area)
    if h[l] < h[r]: l++
    else: r--
```

Simple, but the proof we built gives us confidence it's correct. Without that proof, this looks like a suspicious heuristic.

----------------------------------------

## Step 5: Dry Run on `[1, 8, 6, 2, 5, 4, 8, 3, 7]`

```
l=0, r=8:  h[l]=1, h[r]=7.  area = min(1,7)*8 = 8.   best=8.   h[l]<h[r], l++.
l=1, r=8:  h[l]=8, h[r]=7.  area = min(8,7)*7 = 49.  best=49.  h[l]>h[r], r--.
l=1, r=7:  h[l]=8, h[r]=3.  area = min(8,3)*6 = 18.  best=49.  h[l]>h[r], r--.
l=1, r=6:  h[l]=8, h[r]=8.  area = min(8,8)*5 = 40.  best=49.  tie, move either. Let's say r--.
l=1, r=5:  h[l]=8, h[r]=4.  area = min(8,4)*4 = 16.  best=49.  r--.
l=1, r=4:  h[l]=8, h[r]=5.  area = min(8,5)*3 = 15.  best=49.  r--.
l=1, r=3:  h[l]=8, h[r]=2.  area = min(8,2)*2 = 4.   best=49.  r--.
l=1, r=2:  h[l]=8, h[r]=6.  area = min(8,6)*1 = 6.   best=49.  r--.
l=1, r=1: loop ends.
```

Final: **49**. Matches.

Notice at step 2 (l=1, r=8), we hit the optimal pair. All subsequent iterations just verify that no other pair does better.

**Quick note on ties:** when `h[l] == h[r]`, moving either side is fine. The proof's inequality is non-strict at the boundary, but we don't miss the optimum because if both `l` and `r` were part of an optimum, we'd have already recorded it in `best`.

----------------------------------------

## Step 6: Complexity

Time: `l` and `r` start at opposite ends and move toward each other. Each step advances one pointer by 1, and the loop ends when they meet. So exactly n-1 iterations. **O(n)**.

Space: two pointers and a running max. **O(1)**.

Going from O(n²) brute force to O(n) just from the insight "the shorter side is useless, discard it." That's a good example of how structural reasoning beats fancy data structures.

----------------------------------------

## Step 7: C++ Implementation

```cpp
int maxArea(vector<int>& h) {
    int l = 0, r = h.size() - 1, best = 0;
    while (l < r) {
        int area = min(h[l], h[r]) * (r - l);
        best = max(best, area);
        if (h[l] < h[r]) l++;
        else r--;
    }
    return best;
}
```

----------------------------------------

## Step 8: Follow-up Questions

- **Trapping Rain Water** is a close cousin: how much water is trapped between all bars (not just two chosen)? Same two-pointer spirit but with running max heights on both sides.
- **What if the container has a bottom with a uniform height (not zero)?** Subtract the bottom from both heights; same algorithm.
- **Return the actual indices of the chosen pair.** Track `bestL, bestR` when updating `best`.
- **What if negative heights are allowed (impossible physically but mathematically)?** The pointer logic still holds — the proof didn't require positivity.
- **3D version: pick three vertical posts and find the maximum bounded volume.** Much harder — no simple two-pointer analog.
