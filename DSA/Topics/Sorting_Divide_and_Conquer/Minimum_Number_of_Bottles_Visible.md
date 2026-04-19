# Minimum Number of Bottles Visible

**Problem Link:**
https://leetcode.com/problems/minimum-number-of-bottles-visible-when-standing-on-a-shelf/

**Topic:**
Sorting / Divide and Conquer

----------------------------------------

## Step 1: The Setup

Bottles are arranged on a shelf. Each bottle has a **height**. When you look at the shelf from one side, **each bottle hides behind every taller bottle that stands between it and the viewer** in the row — so the minimum number of bottles visible equals the number of bottles you actually see.

A cleaner framing: given heights array `h`, count how many bottles are visible given specific viewing rules.

A common variant:
- Bottles are arranged in a line. You view from the left.
- A bottle is **visible** if no taller bottle stands in front of it (to its left).
- Equivalently: a bottle at index i is visible iff `h[i]` is greater than all heights to its left.

We want the count of visible bottles — equivalently, the count of **new running maxima** as we scan left to right.

Example: `h = [3, 1, 4, 2, 5]`.
- 3 visible (nothing left of it).
- 1 not visible (3 > 1 blocks it).
- 4 visible (bigger than 3).
- 2 not visible (3 or 4 blocks).
- 5 visible (bigger than 4).

Visible count: **3**.

----------------------------------------

## Step 2: Running Maximum Scan

Looking from the left, a bottle is visible iff it's **strictly greater than the max of everything to its left**. So maintain a running max; increment visible count whenever current > running max; update running max.

```
max_so_far = -∞
visible = 0
for h in heights:
    if h > max_so_far:
        visible++
        max_so_far = h
return visible
```

O(n) time, O(1) space.

----------------------------------------

## Step 3: Trace on `[3, 1, 4, 2, 5]`

```
max_so_far = -∞, visible = 0.
h=3: 3 > -∞. visible = 1. max = 3.
h=1: 1 not > 3. skip.
h=4: 4 > 3. visible = 2. max = 4.
h=2: 2 not > 4. skip.
h=5: 5 > 4. visible = 3. max = 5.
```

Return **3**. ✓

Try `[1, 2, 3, 4]`:
```
h=1: visible = 1. max = 1.
h=2: visible = 2. max = 2.
h=3: visible = 3. max = 3.
h=4: visible = 4. max = 4.
```

All 4 visible (strictly increasing heights — nothing blocks).

Try `[4, 3, 2, 1]`:
- Only h=4 is visible. Return **1**.

----------------------------------------

## Step 4: View from the Right?

Same idea in reverse: scan right to left, tracking a running max, count new peaks. Or equivalently, reverse the array and scan left to right.

For "view from both sides": use both scans. A bottle is visible from some side if it's a running-max from either direction.

----------------------------------------

## Step 5: Handle Ties

The problem statement might say "visible if no taller OR equal bottle blocks" — check carefully. If equal heights block, the condition becomes `h > max_so_far` (strict). If equal heights don't block, use `h >= max_so_far`.

The default and most common: strict inequality — a bottle of equal height in front still blocks.

----------------------------------------

## Step 6: Why "Running Max"?

A bottle is visible iff nothing taller is in front. The **tallest bottle seen so far** summarizes all blockers: if the current bottle exceeds this maximum, it's taller than every blocker → visible.

This pattern — replace a history of comparisons with a single "running summary" — is powerful.

----------------------------------------

## Step 7: Name It

**Running maximum (prefix max)**. Related problems:
- Stock span / next greater element (but more structural — with a stack).
- Count of "record highs" in a permutation.
- Histogram skyline visibility.

When viewing from *both* sides, a related pattern emerges: peaks-as-seen-from-left and peaks-as-seen-from-right. Intersection/union of the two gives different counts.

----------------------------------------

## Step 8: Complexity

Time: **O(n)**. Single pass.
Space: **O(1)** extra.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int minVisibleBottles(vector<int>& heights) {
    int maxSoFar = INT_MIN, visible = 0;
    for (int h : heights) {
        if (h > maxSoFar) {
            visible++;
            maxSoFar = h;
        }
    }
    return visible;
}
```

Two variables and a loop. The fundamental "scan with running summary" idiom.

----------------------------------------

## Step 10: Follow-up Questions

- **Visible from both sides.** Run the scan left-to-right, then right-to-left; mark each visible from either. A bottle is counted once.
- **Bottles visible when viewed from above (projected).** Different geometry — might involve 2D ordering.
- **Heights with ties where equal heights don't block.** Change `>` to `>=` in the condition.
- **Maximum visible bottles after rearrangement.** The maximum is achieved by sorting ascending (viewed from left) — all n visible.
- **Bottles of variable width?** The blocking condition changes; pure height argument no longer works.
- **Return the indices of visible bottles, not just count.** Easy extension — track indices when updating `maxSoFar`.
