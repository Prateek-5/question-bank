# Maximum Height by Stacking Cuboids — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Maximum_Height_by_Stacking_Cuboids.md`](../Maximum_Height_by_Stacking_Cuboids.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/maximum-height-by-stacking-cuboids/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: two-step reduction — (1) sort each cuboid's dims ascending (largest as height for max contribution), (2) sort all cuboids lexicographically, then O(n²) LIS-DP on max-height. Each cuboid's "height" is its largest dim.**

**Map of this file (8 sections):**

1. Read the problem
2. The "rotate the cuboid" insight — pick max as height
3. Sort cuboids — reduces to 3D chain
4. The DP
5. Code
6. Trace it
7. Common pitfalls
8. The shape — generalized chain / LIS

---

## 1. Read the problem

`n` cuboids, each `[w, l, h]`. Each cuboid can be ROTATED freely (any dim can be the "vertical" one). You can stack cuboid A on cuboid B iff after orienting both, ALL of A's dims ≤ B's corresponding dims. Maximize the total height (sum of vertical dims of the stack).

**Example:** `[[50, 45, 20], [95, 37, 53], [45, 23, 12]]` → max height **190**.

---

## 2. The "rotate the cuboid" insight — pick max as height

> **Mini-refresher: for each cuboid, sort dims ascending; treat the largest as height.**
>
> Claim: WLOG, each cuboid in the optimal stack uses its LARGEST dim as the vertical one.
>
> Why? Suppose in OPT a cuboid uses a non-largest dim as height. Swap to use the largest — the cuboid's "footprint" (the other two dims) becomes the smaller pair, which is EASIER to fit below other cuboids and EASIER to host smaller cuboids on top. Strictly better (or equal). So we can always pick the largest as height.

After this normalization, each cuboid is `(min, mid, max)` with `max` being its height contribution.

---

## 3. Sort cuboids — reduces to 3D chain

> **Mini-refresher: sort cuboids lexicographically.**
>
> After dim-sort, sort the whole list ascending by `(w, l, h)` (which is `(min, mid, max)` per cuboid).
>
> Now in sorted order, widths are non-decreasing. To stack cuboid j on cuboid i (j above i), we need all three dims of j ≤ all three dims of i. Since j < i in width (from sort), check length and height explicitly.

This converts the problem into a CHAIN-LIS: find the chain of cuboids where each fits strictly inside the next, MAXIMIZING the sum of heights.

---

## 4. The DP

For each cuboid i (in sorted order), `dp[i]` = max total height of a stack where cuboid i is at the BOTTOM.

```
dp[i] = cuboids[i].height            # stack of just cuboid i
for j < i:
    if cuboids[j] FITS on cuboids[i] (all three dims ≤):
        dp[i] = max(dp[i], dp[j] + cuboids[i].height)
return max(dp)
```

O(n²) time, O(n) space.

---

## 5. Code

**C++:**

```cpp
int maxHeight(vector<vector<int>>& cuboids) {
    for (auto& c : cuboids) sort(c.begin(), c.end());
    sort(cuboids.begin(), cuboids.end());

    int n = cuboids.size();
    vector<int> dp(n);
    int best = 0;
    for (int i = 0; i < n; ++i) {
        dp[i] = cuboids[i][2];
        for (int j = 0; j < i; ++j) {
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

Complexity: **O(n²)** time, **O(n)** space (plus O(n log n) for sort).

---

## 6. Trace it

`cuboids = [[50, 45, 20], [95, 37, 53], [45, 23, 12]]`.

Step 1 — sort each cuboid's dims:
- (50, 45, 20) → (20, 45, 50)
- (95, 37, 53) → (37, 53, 95)
- (45, 23, 12) → (12, 23, 45)

Step 2 — sort cuboids:
```
[(12, 23, 45), (20, 45, 50), (37, 53, 95)]
```

Step 3 — DP:
```
dp[0] = 45 (just (12,23,45)).
dp[1] = 50 base. Check j=0: (12,23,45) ≤ (20,45,50)? Yes. dp[1] = 45 + 50 = 95.
dp[2] = 95 base. 
  j=0: (12,23,45) ≤ (37,53,95)? Yes. dp[2] = 45 + 95 = 140.
  j=1: (20,45,50) ≤ (37,53,95)? Yes. dp[2] = max(140, 95 + 95) = 190.

best = max(45, 95, 190) = 190.  ✓
```

The stack uses ALL three cuboids: top (12,23,45) → middle (20,45,50) → bottom (37,53,95). Heights 45 + 50 + 95 = 190.

---

## 7. Common pitfalls

1. **Choosing a non-largest dim as height for some cuboid.** Suboptimal — always pick the largest.
2. **Forgetting to sort dims within each cuboid.** Then the lex sort on cuboids doesn't align with the "fits" relation.
3. **Allowing equality in only some dims.** The problem says "≤ in each dim is OK for stacking" — adapt to your interpretation (this problem allows equality; if it required strict, change `<=` to `<`).
4. **Trying to recover the actual stack with O(n) memory only.** Need parent pointers.
5. **O(n²) too slow for n = 10^5.** Constraint is n ≤ 100 here, so O(n²) is fine. For larger n, you'd need more clever structures.

---

## 8. The shape — generalized chain / LIS

The pattern: **multi-dimensional chain problem reducible to sort + DP.**

| Problem | Dimensions | Optimization |
|---|---|---|
| LIS | 1 | length |
| Russian Doll Envelopes | 2 | length |
| **This problem** | 3 | sum of heights |
| Box Stacking (general) | 3 | sum of heights, with rotation |
| Longest Chain of Pairs | 2 | length |

**Pattern to internalize:**

> "Multi-dim chain + max sum/length: sort the multidim items, run an LIS-flavored DP. Per-item normalization (sort dims ascending) ensures the largest dim is always the height contribution."

---

> **Self-check — the question to ask next time.**
>
> When the problem allows free rotation and asks for max sum/height in a chain:
>
> > **"Sort each item's dims ascending (max becomes the contributing dim). Sort items lex. O(n²) DP — fits if all subsequent dims ≤ current dims."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Maximum_Height_by_Stacking_Cuboids.md`](../Maximum_Height_by_Stacking_Cuboids.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Russian_Doll_Envelopes.md`](./Russian_Doll_Envelopes.md), [`Longest_Increasing_Subsequence.md`](./Longest_Increasing_Subsequence.md).
  - Coming next: [`Longest_Common_Subsequence.md`](./Longest_Common_Subsequence.md), [`Longest_Palindromic_Subsequence.md`](./Longest_Palindromic_Subsequence.md).
