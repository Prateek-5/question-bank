# Container With Most Water — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Container_With_Most_Water.md`](../Container_With_Most_Water.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/container-with-most-water/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/container-with-most-water/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. This is the **second canonical two-pointer problem** after Two Sum II. The shape is the same — two pointers at the ends, moving inward based on a comparison — but the **decision rule** is subtler. Master why "move the shorter side" is provably correct here, and you've internalized the deeper two-pointer pattern. **Read [`Two_Sum_II_Input_Array_Is_Sorted.md`](./Two_Sum_II_Input_Array_Is_Sorted.md) first** if you haven't.

**Map of this file (10 short sections):**

1. Read the problem (with picture)
2. The natural brute force
3. Why brute force fails
4. The pivot — start at the widest pair, then move inward
5. Which pointer should we move?
6. The elimination proof — why moving the shorter side is safe
7. Code
8. Trace it
9. Common pitfalls
10. The shape — "move the dominated side" appears elsewhere

---

## 1. Read the problem (with picture)

You're given an array `height` of n non-negative integers. Each `height[i]` represents the length of a vertical line at position `i` on the x-axis (lines are 1 unit apart). Pick any two lines, say at positions `i` and `j` with `i < j`. They form the two sides of a rectangular container that holds water between them.

- **Width** of the container: `j − i` (horizontal distance between the lines).
- **Height** of the water: `min(height[i], height[j])` (the water level is capped by the shorter line — if one wall is shorter, water spills over it).
- **Area** = width × height = `(j − i) × min(height[i], height[j])`.

Return the **maximum** area achievable by choosing any two lines.

**Example:** `height = [1, 8, 6, 2, 5, 4, 8, 3, 7]`.

Visualizing the lines as bars:

```
            ▓                       ▓
            ▓                       ▓
            ▓                       ▓
            ▓                       ▓                    ▓
            ▓        ▓                       ▓           ▓
            ▓        ▓              ▓        ▓           ▓
            ▓        ▓     ▓        ▓        ▓           ▓
            ▓        ▓     ▓        ▓        ▓     ▓     ▓
   ▓        ▓        ▓     ▓        ▓        ▓     ▓     ▓
   0        1        2     3        4        5     6     7     8       (x position)
height:1    8        6     2        5        4     8     3     7
```

Try pairs:

- Lines at `i=1, j=8`: heights 8 and 7, width = 7. Container area = `min(8, 7) × 7 = 7 × 7 = 49`.

- Lines at `i=0, j=8`: heights 1 and 7, width = 8. Area = `1 × 8 = 8`. (The short left wall caps the water at height 1.)

- Lines at `i=1, j=6`: heights 8 and 8, width = 5. Area = `8 × 5 = 40`.

The best for this input is **49**, formed by lines 1 and 8.

> **Mini-refresher: why `min` for the water height?**
>
> Imagine you fill the container with water. The water level rises until it would spill over the **shorter** of the two walls. So the water height is capped by `min(left_wall, right_wall)`. If one wall is height 8 and the other is height 7, the water can only rise to 7 (otherwise it overflows the shorter wall).

---

## 2. The natural brute force

Try every pair `(i, j)` with `i < j`:

```cpp
int maxArea(vector<int>& height) {
    int n = height.size();
    int best = 0;
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) {
            int area = min(height[i], height[j]) * (j - i);
            if (area > best) best = area;
        }
    }
    return best;
}
```

Two nested loops, O(n²) time, O(1) space. For `n = 10⁵`, that's `~5 × 10⁹` ops — way too slow.

---

## 3. Why brute force fails

LeetCode constraint: `n` up to `10⁵`. Brute force does ~5×10⁹ ops → TLE.

We need O(n log n) or O(n). Sorting doesn't obviously help (positions matter for width, and sorting destroys positions). The two-pointer pattern from Two Sum II — pointers at the ends, moving inward — is the natural thing to try.

**Pivot question:** if we put two pointers at the ends, how do we decide which to move?

---

## 4. The pivot — start at the widest pair, then move inward

Start with the **widest possible container**: pointers at `l = 0` and `r = n − 1`. Width = `n − 1`, the maximum possible.

Compute the area: `min(height[0], height[n−1]) × (n − 1)`. Record it.

Now we want to find better areas. **But** — every other pair `(i, j)` has width `j − i ≤ n − 1`. The current pair is the widest. So if we move inward, **we lose width**. To compensate and find a larger area, we'd need much taller walls.

The walls can vary, but the water height is capped at `min(height[l], height[r])` — the shorter side. Going inward might bring us a taller wall on one side, but if the OTHER side stays short, the water height stays the same (it's capped by the shorter side).

**This is the key intuition: the shorter side is the bottleneck.** As long as it's there, we can't improve the area beyond `(shorter_wall) × width`. To improve, we need to discard the shorter wall and look further.

Each step: compute the area of the current pair, record the best, then decide which pointer to move. The decision rule is what makes the two-pointer correctness non-trivial.

---

## 5. Which pointer should we move?

When `height[l] < height[r]`, the LEFT side is shorter. **Move `l` right** (toward the interior, looking for a taller left wall).

When `height[l] > height[r]`, the right side is shorter. **Move `r` left**.

When `height[l] == height[r]`, either works.

This is the rule. The next section proves it's correct.

---

## 6. The elimination proof — why moving the shorter side is safe

> **Claim:** When `height[l] < height[r]`, the current `l` cannot be part of the optimal answer. So we can safely move `l` rightward and never miss the maximum.

**Proof:**

Suppose for contradiction the optimal pair is `(l, r')` for some `r' ≤ r` (since `r` is the current rightmost; `r'` is somewhere in `[l+1, r]`). The optimal area is:

```
area(l, r') = min(height[l], height[r']) × (r' − l)
```

Two sub-cases:

**Case A:** `height[r'] ≤ height[l]`. Then `min(height[l], height[r']) = height[r']`. The area is `height[r'] × (r' − l)`.

But we also know `height[l] < height[r]` (given). So `height[r'] ≤ height[l] < height[r]`. We could pair the current `r` with anything taller than `height[r']` and get a taller min. In particular, the original pair `(l, r)` already had area `height[l] × (r − l)`, and:

- `height[r'] ≤ height[l]` (sub-case assumption).
- `r' − l ≤ r − l` (since `r' ≤ r`).

So `area(l, r') ≤ height[l] × (r − l) = area(l, r)`. The current pair `(l, r)` is at least as good as `(l, r')` — we've already recorded it. Moving `l` doesn't discard a strictly better pair.

**Case B:** `height[r'] > height[l]`. Then `min(height[l], height[r']) = height[l]`. The area is `height[l] × (r' − l)`.

But `r' ≤ r`, so `r' − l ≤ r − l`. Thus:

```
area(l, r') = height[l] × (r' − l) ≤ height[l] × (r − l) = area(l, r)
```

Again, the current pair `(l, r)` is at least as good. Moving `l` doesn't lose anything.

**Conclusion:** in both cases, `area(l, r') ≤ area(l, r)`. The current pair `(l, r)` is the best pair involving `l`. We've already considered it, so `l` is "done" and can be safely retired. Move `l` right. ✓

Symmetrically, when `height[l] > height[r]`, the current `r` is done and we move `r` left.

> **In plain English:** the shorter side caps the water height. Any other pair using the shorter side as one wall has WIDTH at most the current width AND HEIGHT at most the shorter side's height. So the current pair is already the best one involving the shorter side. Discard it; look elsewhere.

---

## 7. Code

```cpp
int maxArea(vector<int>& height) {
    int l = 0;
    int r = height.size() - 1;
    int best = 0;

    while (l < r) {
        int h = min(height[l], height[r]);
        int area = h * (r - l);
        if (area > best) best = area;

        if (height[l] < height[r]) {
            l++;                      // left side is shorter — retire it
        } else {
            r--;                      // right side is shorter (or tied) — retire it
        }
    }

    return best;
}
```

Eight lines.

**Python:**

```python
def maxArea(height):
    l, r = 0, len(height) - 1
    best = 0
    while l < r:
        h = min(height[l], height[r])
        area = h * (r - l)
        if area > best:
            best = area
        if height[l] < height[r]:
            l += 1
        else:
            r -= 1
    return best
```

**JavaScript:**

```javascript
function maxArea(height) {
    let l = 0, r = height.length - 1, best = 0;
    while (l < r) {
        const h = Math.min(height[l], height[r]);
        const area = h * (r - l);
        if (area > best) best = area;
        if (height[l] < height[r]) l++;
        else r--;
    }
    return best;
}
```

All O(n) time, O(1) space.

---

## 8. Trace it

`height = [1, 8, 6, 2, 5, 4, 8, 3, 7]`, n = 9.

```
l = 0, r = 8, best = 0.

Iter 1:  h[l]=1, h[r]=7.  h = min(1, 7) = 1.   area = 1 * 8 = 8.   best = 8.
         h[l] < h[r] → l++.     l = 1, r = 8.

Iter 2:  h[l]=8, h[r]=7.  h = min(8, 7) = 7.   area = 7 * 7 = 49.  best = 49.   ← optimal!
         h[l] > h[r] → r--.     l = 1, r = 7.

Iter 3:  h[l]=8, h[r]=3.  h = 3.   area = 3 * 6 = 18.   best = 49.
         h[l] > h[r] → r--.     l = 1, r = 6.

Iter 4:  h[l]=8, h[r]=8.  h = 8.   area = 8 * 5 = 40.   best = 49.
         tied → take the else branch → r--.   l = 1, r = 5.

Iter 5:  h[l]=8, h[r]=4.  h = 4.   area = 4 * 4 = 16.   best = 49.
         r--.   l = 1, r = 4.

Iter 6:  h[l]=8, h[r]=5.  h = 5.   area = 5 * 3 = 15.   best = 49.
         r--.   l = 1, r = 3.

Iter 7:  h[l]=8, h[r]=2.  h = 2.   area = 2 * 2 = 4.    best = 49.
         r--.   l = 1, r = 2.

Iter 8:  h[l]=8, h[r]=6.  h = 6.   area = 6 * 1 = 6.    best = 49.
         r--.   l = 1, r = 1.

Loop ends (l == r). Return 49.  ✓
```

Notice the trace: we found the optimal answer (49) on iteration 2, after only 1 pointer move. The remaining 6 iterations confirmed no other pair was better.

**About the tied case (iter 4):** when `h[l] == h[r]`, we move `r` here (the `else` branch). Moving `l` would also be fine — both walls are "done" simultaneously because the area can't improve while EITHER is the limiting height.

---

## 9. Common pitfalls

1. **Moving the TALLER side.** Counterintuitive but very common. If `height[l] = 1` and `height[r] = 8`, you might think "move `r` because its wall is the tall one we want to keep." Wrong. The shorter side caps the water; we want to DISCARD the limiting wall. Move the SHORTER side inward.

2. **Comparing to `best` before computing area.** Some implementations write `best = max(best, h * (r - l))` in-place — fine. But computing area, then forgetting to compare, is a common typo.

3. **Loop guard `l <= r` instead of `l < r`.** When `l == r`, width is 0, area is 0 — useless work and a clutter source. Use strict `<`.

4. **Integer overflow on `(r - l) × height`.** For `n = 10⁵` and `height[i]` up to `10⁴`, the max area is `10⁵ × 10⁴ = 10⁹` — fits in `int32` but BARELY. Use `long long` for extreme constraints to be safe.

5. **Trying a divide-and-conquer or DP approach.** People sometimes overthink this. The two-pointer is provably optimal at O(n). No fancier approach helps.

6. **Confusing this with Trapping Rain Water.** Both use "two pointers, move the shorter side." But Container With Most Water picks **ONE pair** of walls and computes area between them. Trapping Rain Water sums water trapped between ALL bars. Different objectives — same pointer mechanics. See the cross-references.

---

## 10. The shape — "move the dominated side" appears elsewhere

The two-pointer with "discard the dominated side" technique is a refinement of the basic Two Sum II pattern. The key idea: **at each step, identify which side CAN'T be part of the answer and discard it.**

| Problem | What's compared | Which side to retire |
|---|---|---|
| **This problem** (Container With Most Water) | `min(h[l], h[r])` (caps water height) | the SHORTER side — its current pair is already its best |
| Trapping Rain Water | `height[l]` vs `height[r]` | the SHORTER side — its water is determined |
| Two Sum II (different shape) | `nums[l] + nums[r]` vs target | the side that's "too small" (l) or "too big" (r) |
| Valid Mountain Array | both `l` and `r` walk inward | walk while ascending |
| Sort Colors (Dutch national flag) | three pointers, not two | swap based on color |

**Pattern to internalize:**

> "Two pointers at the ends. At each step, the metric you care about (area, sum, water level, etc.) depends on BOTH endpoints. Identify which endpoint is the 'limit' — the one currently dragging the metric down. Argue (via an elimination proof) that this endpoint can't be part of a strictly better pair. Move it inward."

The elimination proof is what makes the algorithm provably correct. Without the proof, "move the shorter side" looks like a heuristic that might fail on some clever counter-example. The proof in §6 shows it can't.

---

> **Self-check — the question to ask next time.**
>
> When you see a problem asking for the **best pair** in an array under some metric that depends on both endpoints (sum, area, ratio, etc.), before nesting loops, ask:
>
> > **"Can I put two pointers at the ends and identify which endpoint is 'dragging the metric down' at each step? Can I prove that endpoint can't be part of a better pair, and so safely move it inward?"**
>
> If yes, you've turned `O(n²)` into `O(n)`.

---

## Cross-references

- **Reference card (post-mastery):** [`../Container_With_Most_Water.md`](../Container_With_Most_Water.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Two_Sum_II_Input_Array_Is_Sorted.md`](./Two_Sum_II_Input_Array_Is_Sorted.md) — the simpler "sum vs target" two-pointer (required reading first)
  - [`../../Arrays_and_Matrices/learn/Trapping_Rain_Water.md`](../../Arrays_and_Matrices/learn/Trapping_Rain_Water.md) — same "process shorter side" trick, different goal (sum of all trapped water, not max area between two walls)
  - Coming next in this topic: 3Sum (builds Two Sum II into a 3-element search)
