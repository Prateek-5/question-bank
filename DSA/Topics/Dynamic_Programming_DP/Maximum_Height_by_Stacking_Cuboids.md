# Maximum Height by Stacking Cuboids

**Problem Link:**
https://leetcode.com/problems/maximum-height-by-stacking-cuboids/

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Understand the Rules

You have `n` cuboids, each with dimensions `[width, length, height]` (they can be reordered: a cuboid is really just three numbers, any can be the "up" dimension when stacked). You stack cuboid A on top of cuboid B **only if A's width, length, and height are each ≤ B's corresponding dimensions after you decide the orientation of each**.

Return the **maximum total height** of a valid stack.

Example: `cuboids = [[50, 45, 20], [95, 37, 53], [45, 23, 12]]`.

By orienting and picking, you could stack them to get a total of... let me figure out the answer: 190 for this example. The explanation is non-obvious.

First observation: each cuboid can be **rotated** freely. So for any cuboid with dims (a, b, c), we can choose which one is "height" (the up direction) and orient the other two as width and length.

The constraint for stacking X on Y is: after orienting both, every dim of X is ≤ every dim of Y.

----------------------------------------

## Step 2: Simplify With Sorting

Here's a key observation: for each cuboid, **always sort its dimensions in non-decreasing order**. That is, for a cuboid (a, b, c), consider (min, mid, max). Why?

Claim: for any valid stack, we can WLOG assume each cuboid is oriented with its dimensions sorted this way. Specifically, the largest dimension is the **height**, and the others are width and length. This maximizes each cuboid's contribution to total height.

Proof sketch: suppose a cuboid in the optimal stack has dimensions not sorted — say, it's placed with (b, a, c) where b > a. Could we swap to (a, b, c) instead (with c still as height)? Doing so changes the cuboid's "footprint" from (b, a) to (a, b) — same set of dimensions, just swapped. Can the cuboid above still fit? The cuboid above's footprint was constrained by (b, a); now it's constrained by (a, b). But (a, b) is just a rotation of (b, a), so the cuboid above can be rotated to match. So no loss. ✓

More crucially: can we always pick the LARGEST dimension as "height"? Yes, with a similar argument. Swapping to make the largest dim the height increases this cuboid's contribution without breaking anything above.

Conclusion: **sort each cuboid's dimensions; the largest is its height**.

----------------------------------------

## Step 3: Now Sort the Cuboids Themselves

After sorting dimensions within each cuboid, the stacking constraint is: to stack X on Y, X.width ≤ Y.width AND X.length ≤ Y.length AND X.height ≤ Y.height (with width ≤ length ≤ height for each).

Sort all cuboids by their dimension tuples (width, length, height) in ascending order. Now if we build a stack from bottom to top, we're picking an increasing subsequence of cuboids.

"Increasing" means: for i < j in our picked sequence, cuboid_i fits inside cuboid_j. Or equivalently, cuboid_j goes below cuboid_i.

Wait, the stack orientation: bottom cuboid holds everything above. So bottom's dimensions ≥ all above. If we sort ascending and pick an increasing subsequence, the last picked is the biggest — that's the bottom. Then each earlier picked (smaller) fits above the next-bigger one.

This reduces the problem to: **Longest increasing subsequence (by cuboid dimensions)** where the "length" being maximized is actually the sum of heights.

----------------------------------------

## Step 4: DP Similar to LIS

For each cuboid i (after sorting), `dp[i]` = maximum total height of a stack ending with cuboid i on top (or: cuboid i is the smallest / topmost).

Actually let's reverse: `dp[i]` = max height with cuboid i as the **bottom** of the stack. Then dp[i] considers all cuboids j that can sit ON cuboid i (j has all dims ≤ i) and picks the best.

```
sort cuboids by (width, length, height) ascending (after per-cuboid sort)

dp[i] = cuboids[i].height   # stack with just this cuboid
for i from 0 to n-1:
    for j from 0 to i-1:
        if cuboids[j] can fit on cuboids[i]  # all three dims ≤
            dp[i] = max(dp[i], dp[j] + cuboids[i].height)

return max(dp)
```

Each cuboid's height contribution depends on its position as the bottom of a sub-stack.

Hmm, I had it slightly off. Let me re-phrase. If cuboid i is the bottom, then everything above must be smaller. In the sorted-ascending order, things "above" in the stack come earlier (smaller cuboids). So dp[i] = i's height + max over j < i of dp[j] (where j fits on i).

Yes, that's the pattern: dp[i] considers cuboid i at the bottom, extended by smaller cuboids sitting on top.

----------------------------------------

## Step 5: Why Sorting Makes This an LIS-Variant

After sorting ascending (width, length, height), if j < i in the sorted order, then cuboids[j].width ≤ cuboids[i].width automatically (by sort). But we also need length and height constraints.

For cuboid j to fit on cuboid i (with j above), we need **all three dimensions ≤**. Since j ≤ i in width (from sort), we need to additionally check length and height.

Some cuboids with equal widths might have different lengths/heights — those checks are still needed explicitly.

The DP is O(n²) — n cuboids, each checking all predecessors.

----------------------------------------

## Step 6: Trace on the Example

`cuboids = [[50, 45, 20], [95, 37, 53], [45, 23, 12]]`.

Step 1: sort each cuboid's dims ascending.
- (50, 45, 20) → (20, 45, 50).
- (95, 37, 53) → (37, 53, 95).
- (45, 23, 12) → (12, 23, 45).

Step 2: sort cuboids.
- (12, 23, 45).
- (20, 45, 50).
- (37, 53, 95).

Step 3: DP with cuboids in this order. Heights: 45, 50, 95.

```
dp[0] = 45. (just (12, 23, 45))
dp[1] = 50 (base). Check cuboid 0: (12, 23, 45) fits on (20, 45, 50)? 12≤20, 23≤45, 45≤50. Yes. dp[1] = 45 + 50 = 95.
dp[2] = 95 (base). Check j=0: (12, 23, 45) on (37, 53, 95)? Yes. dp[2] = max(95, 45 + 95) = 140.
       Check j=1: (20, 45, 50) on (37, 53, 95)? 20 ≤ 37, 45 ≤ 53, 50 ≤ 95. Yes. dp[2] = max(140, 95 + 95) = 190.
```

max(dp) = 190. ✓

----------------------------------------

## Step 7: Name It

This is a **2D/3D Longest Increasing Subsequence** variant, solved with sorting + DP. The twist:
- Each cuboid is first normalized (sort dims).
- All cuboids are sorted (so width order is fixed).
- DP builds the max-height stack.

Related patterns:
- Russian Doll Envelopes (2D LIS).
- Longest Chain in Pair Sequence.
- Tower of Babel-style box stacking.

The general technique: when the comparison is multi-dimensional, sort by one dimension first and DP on the others.

----------------------------------------

## Step 8: Complexity

Time: **O(n²)** for the DP. Plus O(n log n) for sorting cuboids and O(1) per cuboid for internal sort. Dominated by DP.
Space: **O(n)** for dp array.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int maxHeight(vector<vector<int>>& cuboids) {
    // Step 1: sort each cuboid's dimensions ascending
    for (auto& c : cuboids) sort(c.begin(), c.end());

    // Step 2: sort cuboids lexicographically (so earlier ones are "smaller")
    sort(cuboids.begin(), cuboids.end());

    int n = cuboids.size();
    vector<int> dp(n);
    int best = 0;
    for (int i = 0; i < n; ++i) {
        dp[i] = cuboids[i][2];   // stack with just this cuboid at bottom
        for (int j = 0; j < i; ++j) {
            // Can cuboids[j] sit on cuboids[i]? (j already has width ≤ i via sort, check len & height)
            if (cuboids[j][0] <= cuboids[i][0] &&
                cuboids[j][1] <= cuboids[i][1] &&
                cuboids[j][2] <= cuboids[i][2]) {
                dp[i] = max(dp[i], dp[j] + cuboids[i][2]);
            }
        }
        best = max(best, dp[i]);
    }
    return best;
}
```

Two key preprocessing steps:
1. Sort dims within each cuboid (pick the biggest as height).
2. Sort cuboids themselves lexicographically.

Then standard LIS-flavored DP.

----------------------------------------

## Step 10: Follow-up Questions

- **Return the actual stack (list of cuboids in order).** Track parent pointers.
- **Maximize the stack's minimum cuboid's volume instead.** Different objective; needs careful DP.
- **Cuboids with "orientation locked" (can't rotate).** Then step 1 doesn't apply; DP directly on given orientations.
- **Stack with weighted cuboids (different importance).** Multiply dp transitions by weights.
- **Very large n (10^5+).** O(n²) DP too slow. Use more advanced structures like segment trees indexed by dimensions.
- **Prove sorting-to-max-height optimality more rigorously.** The exchange argument I sketched works formally.
