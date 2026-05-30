# Trapping Rain Water — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Trapping_Rain_Water.md`](../Trapping_Rain_Water.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/trapping-rain-water/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/trapping-rain-water/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~40 minutes. This is **THE classic** array problem — it's been asked in interviews for two decades. The lesson isn't a single trick; it's a **three-step difficulty escalation**: brute force → precomputed-prefix-arrays → two-pointer. Each step uses the previous as a thinking aid. By the end, you'll see why the two-pointer trick is "obvious" — even though it really isn't on first sight.

**Map of this file (12 short sections):**

1. Read the problem (visually)
2. The "per-position" rule for trapped water
3. Brute force #1 — the O(n²) scan-both-ways
4. Why brute force fails
5. Brute force #2 — precompute left-max and right-max (O(n) time, O(n) space)
6. The pivot — can we drop the O(n) extra arrays?
7. Two pointers — the setup
8. The decision rule: process the shorter side
9. Why "process the shorter side" works (the proof, in plain arithmetic)
10. Code + trace
11. Common pitfalls
12. The shape — where "L/R max precomputation" appears later

---

## 1. Read the problem (visually)

You're given an array `height` representing the heights of vertical bars, each 1 unit wide. After rain, water pools in the "valleys" between taller bars. Return the **total volume of trapped water**.

Example: `height = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]`.

A picture (each `▓` is a 1×1 block of bar, each `░` is a 1×1 block of trapped water):

```
                          ▓
              ▓           ▓           ▓
              ▓     ▓     ▓     ▓     ▓
        ▓     ▓     ▓     ▓     ▓     ▓     ▓
heights: 0  1  0  2  1  0  1  3  2  1  2  1
                                  ↑
            water collects in the valleys between taller bars
```

Adding the water blocks:

```
                          ▓
              ▓  ░  ░  ░  ▓           ▓
              ▓  ░  ▓  ░  ▓  ░  ░  ░  ▓
        ▓  ░  ▓  ░  ▓  ░  ▓  ░  ▓  ░  ▓  ░
heights: 0  1  0  2  1  0  1  3  2  1  2  1
                                              total water = 6
```

That's 6 units of water trapped. The answer for this input is **6**.

The problem **isn't asking you to draw this**. It's asking you to compute the **count** of `░` cells in linear-or-better time.

---

## 2. The "per-position" rule for trapped water

Forget the array for a second. Pick a single position `i`. How much water sits **above** bar `i` after the rain?

Water sits above `i` until it would spill over either side. So the water height above `i` is bounded by the **shorter of the tallest bar to its left and tallest bar to its right** — whichever wall is shorter is what limits the water.

Formally:

```
water_above(i) = min(left_max[i], right_max[i]) − height[i]
```

where:

- `left_max[i]` = the maximum bar height in `height[0..i]` (including `i`).
- `right_max[i]` = the maximum bar height in `height[i..n−1]` (including `i`).

If the result is negative (which happens when `height[i]` is taller than both side maxes — meaning `i` itself is the tallest bar in its neighborhood), the water above is `0`, not negative.

**Quick check on the example, position `i = 2` (height 0):**

- Heights to its left (inclusive): `[0, 1, 0]`. Max = 1.
- Heights to its right (inclusive): `[0, 2, 1, 0, 1, 3, 2, 1, 2, 1]`. Max = 3.
- Water above `i = 2` = `min(1, 3) − height[2]` = `1 − 0` = **1 unit**.

Matches the picture (one `░` block at column 2).

**Position `i = 7` (height 3):**

- Left max (inclusive): max of `[0,1,0,2,1,0,1,3]` = 3.
- Right max (inclusive): max of `[3,2,1,2,1]` = 3.
- Water above = `min(3, 3) − 3` = `0`. No water. (It's a peak.)

The **total trapped water** is the sum over all `i` of `max(0, min(left_max[i], right_max[i]) − height[i])`.

This formula gives us a clear, exact answer. The remaining question is just: **how do we compute `left_max[i]` and `right_max[i]` efficiently?**

---

## 3. Brute force #1 — the O(n²) scan-both-ways

The most direct approach: for each `i`, do TWO inner scans — one to find the max to the left, one to the right.

```cpp
int trap(vector<int>& height) {
    int n = height.size();
    int total = 0;
    for (int i = 0; i < n; i++) {
        int leftMax = 0, rightMax = 0;
        for (int j = 0; j <= i; j++) leftMax  = max(leftMax,  height[j]);
        for (int j = i; j <  n; j++) rightMax = max(rightMax, height[j]);
        total += max(0, min(leftMax, rightMax) - height[i]);
    }
    return total;
}
```

Two inner loops, each O(n). Outer loop O(n). Total: O(n²) time. O(1) extra space.

Correct, but slow.

---

## 4. Why brute force fails

For `n = 10⁴` (the typical constraint), `n² = 10⁸` — borderline. For `n = 10⁵`, `n² = 10¹⁰`, hard TLE.

The wasted work is obvious: we recompute the left-max from scratch for every `i`, even though the left-max at position `i+1` is just `max(left_max[i], height[i+1])` — one more comparison, not a full re-scan. Same for right-max in reverse.

**Pivot question #1:**

> **"What if I precompute `left_max[]` and `right_max[]` once, then use them as lookups?"**

---

## 5. Brute force #2 — precompute left-max and right-max (O(n) time, O(n) space)

Build two arrays:

```
left_max[0] = height[0]
left_max[i] = max(left_max[i-1], height[i])   for i ≥ 1     ← left-to-right pass

right_max[n-1] = height[n-1]
right_max[i]   = max(right_max[i+1], height[i])  for i ≤ n-2  ← right-to-left pass
```

Each array is filled in one linear pass.

Then for each `i`, water contribution is `max(0, min(left_max[i], right_max[i]) − height[i])`.

```cpp
int trap(vector<int>& h) {
    int n = h.size();
    if (n == 0) return 0;

    vector<int> L(n), R(n);
    L[0] = h[0];
    for (int i = 1; i < n; i++) L[i] = max(L[i-1], h[i]);

    R[n-1] = h[n-1];
    for (int i = n-2; i >= 0; i--) R[i] = max(R[i+1], h[i]);

    int water = 0;
    for (int i = 0; i < n; i++) {
        water += min(L[i], R[i]) - h[i];   // note: this is always ≥ 0 — see below
    }
    return water;
}
```

> **Why is `min(L[i], R[i]) − h[i]` always ≥ 0?**
>
> `L[i]` is the max over `h[0..i]` — it includes `h[i]`. So `L[i] ≥ h[i]`. Similarly `R[i] ≥ h[i]`. Therefore `min(L[i], R[i]) ≥ h[i]`, and the subtraction is non-negative. We don't need the `max(0, ...)` guard. (The earlier `max(0, ...)` was defensive — here we get safety for free.)

This is **O(n) time, O(n) extra space**. Three linear passes. Quite efficient.

This would pass LeetCode. We could stop here — but the problem is famous because there's a slicker solution that drops the space to **O(1)**. Let's chase it.

---

## 6. The pivot — can we drop the O(n) extra arrays?

We're using two arrays of size `n`. Can we get away with just a few variables?

Look at the formula for each `i`:

```
water[i] = min(L[i], R[i]) − h[i]
```

The whole thing depends on **the lesser of `L[i]` and `R[i]`**. **If we somehow knew which side was smaller, we could compute the water contribution using only that side's max** — we wouldn't need the other side's max value at all.

**Pivot question #2:**

> **"What if we walk inward from both ends, and at each step we only do work on whichever side we're CERTAIN has the smaller running max so far?"**

That's the two-pointer idea. Let's set it up.

---

## 7. Two pointers — the setup

Two pointers, `l` starting at 0 and `r` starting at `n − 1`. They walk toward each other.

We also maintain two scalars (not arrays!):

- `left_max` = max of `height[0..l]` so far.
- `right_max` = max of `height[r..n−1]` so far.

These scalars grow (or stay) as the pointers move inward. They're the "running max" each pointer has seen on its own side.

The loop runs while `l < r`. Each iteration:

1. Look at `height[l]` vs `height[r]`.
2. **Process the shorter side** (we'll prove this is the safe one in §9).
3. Move that pointer inward.

That's the sketch. The "process the shorter side" rule is the heart of the algorithm — and the only non-obvious part.

---

## 8. The decision rule: process the shorter side

Here's the rule in code:

```
while l < r:
    if height[l] < height[r]:
        # process position l
        if height[l] ≥ left_max:
            left_max = height[l]   # new left-side max; no water here
        else:
            water += left_max − height[l]
        l += 1
    else:
        # process position r (symmetric)
        if height[r] ≥ right_max:
            right_max = height[r]
        else:
            water += right_max − height[r]
        r -= 1
```

The structure is: **whichever pointer has the shorter bar, process that one and move it inward.**

When processing a position:

- If its height meets-or-exceeds the running max on that side, it becomes the new max (no water sits above a new peak).
- Otherwise, water = `(running max on this side) − height[pos]`. We don't need to know the **other side's** max — see why next.

The pointer advances. Repeat until they meet.

---

## 9. Why "process the shorter side" works (the proof, in plain arithmetic)

This is the only subtle step. Let me prove it carefully on the example, then state it generally.

**At step `l = 5, r = 7` in the example** (`height = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]`):

- `height[l] = height[5] = 0`. `height[r] = height[7] = 3`.
- `height[l] < height[r]` → process the left side at position 5.

For position 5, the water-above formula is:

```
water[5] = min(true_left_max_at_5, true_right_max_at_5) − height[5]
```

What are these "true" values?

- `true_left_max_at_5` = max of `height[0..5]` = max(0, 1, 0, 2, 1, 0) = 2. Our running `left_max` should also be 2 at this point (we've been tracking it).
- `true_right_max_at_5` = max of `height[5..11]` = max(0, 1, 3, 2, 1, 2, 1) = 3.

We don't KNOW the `true_right_max_at_5 = 3` exactly. But we know one thing:

> **The right side of position 5 contains `height[r] = height[7] = 3`** (which we can see). So the true right max is AT LEAST 3.

In fact, the true right max is at least `max(height[r+1], height[r+2], ..., height[n−1])`, but for our reasoning we only need **at least `height[r]`** (since `r` is to the right of `l`).

So:

```
true_right_max_at_5 ≥ height[r] = 3.
```

Now we compare to our running `left_max = 2`:

```
true_right_max_at_5 ≥ 3 > 2 = left_max ≥ true_left_max_at_5
```

(That last `≥` holds because `left_max` is the max we've seen so far, equal to the true left-max-at-`l` — and as we move `l` rightward, the true left max can only grow.)

So `true_right_max_at_5 > true_left_max_at_5`, meaning `min(true_left, true_right) = true_left = left_max`. We can use `left_max` as the binding constraint:

```
water[5] = left_max − height[5] = 2 − 0 = 2.
```

**The right max doesn't matter** for this position — we only needed to know it was bigger than the left max, which the comparison `height[l] < height[r]` guarantees.

**Generalized statement:**

> **If `height[l] < height[r]`, then the true right-max at any position in `[l, r]` is ≥ `height[r] > height[l] ≥ left_max_so_far ≥ true_left_max_at_l`.** Therefore `min(true_left, true_right) = true_left = left_max_so_far`, and we can safely compute water at position `l` using `left_max` alone.

Symmetric for the other case (`height[l] ≥ height[r]`, process right side).

The "process the shorter side" rule is **safe** because the shorter side has a guaranteed-larger opposing-side max. We don't need to compute the opposing max — its existence is enough.

---

## 10. Code + trace

**C++:**

```cpp
int trap(vector<int>& h) {
    int n = h.size();
    if (n == 0) return 0;

    int l = 0, r = n - 1;
    int left_max = 0, right_max = 0;
    int water = 0;

    while (l < r) {
        if (h[l] < h[r]) {
            // process left side at position l
            if (h[l] >= left_max) left_max = h[l];
            else                  water += left_max - h[l];
            l++;
        } else {
            // process right side at position r
            if (h[r] >= right_max) right_max = h[r];
            else                   water += right_max - h[r];
            r--;
        }
    }
    return water;
}
```

**Trace on `[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]`:**

```
n = 12.  l = 0, r = 11.  left_max = 0, right_max = 0.  water = 0.

Iter  1: l=0, r=11.  h[l]=0, h[r]=1.  h[l] < h[r] → process LEFT.
         h[l]=0 ≥ left_max=0 → update left_max=0. (no water)
         l = 1.

Iter  2: l=1, r=11.  h[l]=1, h[r]=1.  h[l] < h[r]? No (tied). Process RIGHT.
         h[r]=1 ≥ right_max=0 → update right_max=1. (no water)
         r = 10.

Iter  3: l=1, r=10.  h[l]=1, h[r]=2.  h[l] < h[r] → LEFT.
         h[l]=1 ≥ left_max=0 → update left_max=1. (no water)
         l = 2.

Iter  4: l=2, r=10.  h[l]=0, h[r]=2.  LEFT.
         h[l]=0 < left_max=1 → water += 1 - 0 = 1. water = 1.
         l = 3.

Iter  5: l=3, r=10.  h[l]=2, h[r]=2.  Tied. RIGHT.
         h[r]=2 ≥ right_max=1 → update right_max=2. (no water)
         r = 9.

Iter  6: l=3, r=9.   h[l]=2, h[r]=1.  h[l] < h[r]? No. RIGHT.
         h[r]=1 < right_max=2 → water += 2 - 1 = 1. water = 2.
         r = 8.

Iter  7: l=3, r=8.   h[l]=2, h[r]=2.  Tied. RIGHT.
         h[r]=2 ≥ right_max=2 → update right_max=2. (no change, no water)
         r = 7.

Iter  8: l=3, r=7.   h[l]=2, h[r]=3.  LEFT.
         h[l]=2 ≥ left_max=1 → update left_max=2. (no water)
         l = 4.

Iter  9: l=4, r=7.   h[l]=1, h[r]=3.  LEFT.
         h[l]=1 < left_max=2 → water += 2 - 1 = 1. water = 3.
         l = 5.

Iter 10: l=5, r=7.   h[l]=0, h[r]=3.  LEFT.
         h[l]=0 < left_max=2 → water += 2 - 0 = 2. water = 5.
         l = 6.

Iter 11: l=6, r=7.   h[l]=1, h[r]=3.  LEFT.
         h[l]=1 < left_max=2 → water += 2 - 1 = 1. water = 6.
         l = 7.

Loop exit: l = r = 7.

Return water = 6.  ✓
```

The total trapped water is **6** — matches the visual diagram in section 1.

---

## 11. Common pitfalls

1. **Returning negative water from `min(L, R) − h[i]`.** As noted in section 5, this is impossible because L and R both include `h[i]`. But it's worth understanding why — and if you reimplement L/R with subtle off-by-one bugs (e.g., L excludes `h[i]`), the formula CAN go negative. Use the `max(0, ...)` guard if you're unsure.

2. **The pivot pointer's "starts at 0" assumption.** Initialize `left_max = 0` and `right_max = 0`. This works because all heights are ≥ 0. For arrays with negative values, you'd need `INT_MIN`. (Not the case here — physical heights aren't negative.)

3. **`while (l < r)` vs `while (l <= r)`.** Use strict `<`. When `l == r`, both pointers refer to the same single bar; there's no "between them" to contain water. The strict version correctly stops there.

4. **Tied heights: which side to process?** When `h[l] == h[r]`, EITHER choice works — both are equally short (or equally tall, depending on perspective). The proof still holds because `true_right_max ≥ h[r] = h[l] ≥ left_max`, with equality in the worst case but still ≥. The code above processes the right side on ties (`else` branch); it doesn't matter for correctness.

5. **Forgetting to update `left_max` / `right_max` on the "new peak" branch.** When `h[l] ≥ left_max`, we update `left_max` and DON'T add water. Forgetting the update means future positions compute their water against an outdated (smaller) `left_max`, undercounting.

6. **Misreading the problem as "store water in physical buckets, not above bars."** The water is the SPACE BETWEEN bars, sitting in the valleys — not stored "in" the bars themselves. Re-read the spec if confused.

---

## 12. The shape — where "L/R max precomputation" appears later

Both versions of this algorithm — the L/R precomputed arrays AND the two-pointer — generalize to a broad class of problems where **each position's answer depends on the max (or min, or sum) of its left side and right side simultaneously**.

| Problem | L/R quantities |
|---|---|
| **Trapping Rain Water** | left/right max of height |
| **Largest Rectangle in Histogram** | "next smaller" left and right (via stack, not L/R arrays — but same shape) |
| **Product of Array Except Self** | left/right product (precomputed prefix-product and suffix-product) |
| **Container With Most Water** | two-pointer with "shorter side" rule — sibling problem of this one |
| **Sliding Window Maximum** | running max with sliding boundary (monotonic deque, different mechanism) |
| **Candy** (LC #135) | left/right "passes" assigning candy based on neighbor rankings |

**Pattern to internalize:** when each position's answer depends on what's on its left AND its right, two options:

- **L/R precomputed arrays:** O(n) time, O(n) space, simple to reason about. Use this if memory is fine.
- **Two-pointer with running max/min:** O(n) time, O(1) space, requires a "decision rule" proof. Use this if memory matters or if the interviewer asks for it.

Both versions are good answers. The two-pointer is the senior-bar version because the decision rule isn't obvious — but you should know both and explain the choice.

---

> **Self-check — the question to ask next time.**
>
> When a problem asks for **"compute something at each position that depends on aggregate (max/min/sum) of elements both to the left and to the right,"** before reaching for nested loops, ask:
>
> > **"Can I precompute left-aggregate and right-aggregate arrays in two linear passes, then answer each position in O(1)? And — bonus — can I drop those arrays in favor of two pointers walking inward, processing one side at a time using only a running scalar?"**
>
> The first answer gives `O(n)` time / `O(n)` space (always works). The second gives `O(n)` time / `O(1)` space (requires proving you can safely process one side without knowing the other side's max yet — see §9 above for the template proof).

---

## Cross-references

- **Reference card (post-mastery):** [`../Trapping_Rain_Water.md`](../Trapping_Rain_Water.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Container_With_Most_Water.md`](../../Two_Pointers/learn/Container_With_Most_Water.md) (when written) — sibling problem; uses the same two-pointer shorter-side rule for max-area
  - Coming later: Largest Rectangle in Histogram, Product of Array Except Self — same "left+right precompute" shape
