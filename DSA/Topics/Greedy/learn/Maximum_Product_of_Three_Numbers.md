# Maximum Product of Three Numbers — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Maximum_Product_of_Three_Numbers.md`](../Maximum_Product_of_Three_Numbers.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/maximum-product-of-three-numbers/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/maximum-product-of-three-numbers/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: the max product of three is EITHER the three LARGEST OR the two SMALLEST × the largest. Two negatives multiply to a positive — beware ignoring them.**

**Map of this file (8 sections):**

1. Read the problem
2. Why "top 3" isn't enough
3. The two candidates
4. Why those two cover all cases
5. Code (sort + O(n))
6. Trace it
7. Common pitfalls
8. The shape — extremes for product

---

## 1. Read the problem

Given an integer array `nums` (can include negatives), return the MAXIMUM product of any three numbers.

**Examples:**

- `[1, 2, 3, 4]` → 2 × 3 × 4 = **24**.
- `[-10, -10, 5, 2]` → (-10) × (-10) × 5 = **500** (not -10 × 2 × 5 = -100).
- `[-5, -4, -3, -2, -1]` → (-1) × (-2) × (-3) = **-6** (least negative).

---

## 2. Why "top 3" isn't enough

> **Mini-refresher: two negatives multiplied = a positive.**
>
> If the array has two large-magnitude negatives, their product is a large positive. Multiplied by the LARGEST POSITIVE, this can BEAT the top-3 product.
>
> Example: `[-10, -10, 5, 2]`. Top 3: -10, 2, 5 → -100. But (-10)(-10)(5) = 500. Greedy "pick top 3" misses this.

---

## 3. The two candidates

> **Mini-refresher: only two configurations can be the max.**
>
> Let the sorted array be `[a₀ ≤ a₁ ≤ ... ≤ a_{n-1}]`. The maximum product of three is:
>
> - **Candidate A: three largest** — `a_{n-1} × a_{n-2} × a_{n-3}`.
> - **Candidate B: two smallest × largest** — `a₀ × a₁ × a_{n-1}`.
>
> Return `max(A, B)`.

---

## 4. Why those two cover all cases

Any configuration that uses neither all-large nor "two-min + max-large" is dominated:

- **One negative + two positives** = negative → worse than any all-positive product (if it exists).
- **Three negatives** = negative → worse than swapping in any positive.
- **(a_min, a_mid, a_max)** with `a_min < 0 < a_mid`: if `a_min` is needed for its magnitude, the SECOND-smallest is also negative (both contribute positive factor); use `a_min × a_{min+1} × a_max` — that's Candidate B.

So A and B are the only contenders.

---

## 5. Code (sort + O(n))

**C++ — sort version (simpler):**

```cpp
int maximumProduct(vector<int>& nums) {
    sort(nums.begin(), nums.end());
    int n = nums.size();
    return max(nums[n - 1] * nums[n - 2] * nums[n - 3],
               nums[0] * nums[1] * nums[n - 1]);
}
```

**C++ — O(n) version (track top-3 and bottom-2):**

```cpp
int maximumProduct(vector<int>& nums) {
    int max1 = INT_MIN, max2 = INT_MIN, max3 = INT_MIN;
    int min1 = INT_MAX, min2 = INT_MAX;

    for (int x : nums) {
        if (x > max1) { max3 = max2; max2 = max1; max1 = x; }
        else if (x > max2) { max3 = max2; max2 = x; }
        else if (x > max3) { max3 = x; }

        if (x < min1) { min2 = min1; min1 = x; }
        else if (x < min2) { min2 = x; }
    }
    return max(max1 * max2 * max3, min1 * min2 * max1);
}
```

Complexity: sort version **O(n log n)**; tracker version **O(n)**. Both **O(1)** space.

---

## 6. Trace it

**`[-10, -10, 5, 2]`:**
- Sorted: `[-10, -10, 2, 5]`.
- A = 5 · 2 · (-10) = -100.
- B = (-10) · (-10) · 5 = 500.
- max = **500**. ✓

**`[1, 2, 3, 4]`:**
- A = 4 · 3 · 2 = 24.
- B = 1 · 2 · 4 = 8.
- max = **24**. ✓

**`[-5, -4, -3, -2, -1]`:**
- A = (-1)(-2)(-3) = -6.
- B = (-5)(-4)(-1) = -20.
- max = **-6**. ✓

**`[-4, -3, -2, -1, 60]`:**
- A = 60 · (-1) · (-2) = 120.
- B = (-4)(-3) · 60 = 720.
- max = **720**. ✓

---

## 7. Common pitfalls

1. **Returning only the top-3 product.** Misses the two-negatives case.
2. **Overflow.** Three ints multiplied can exceed 32-bit. Cast to `long long` for safety.
3. **Sorting by absolute value.** Doesn't help — you lose sign info needed for the two-negatives case.
4. **Computing the bottom-3 product as a candidate.** Three negatives = negative; worse than the two-negatives-plus-largest case.
5. **Forgetting that all-negative arrays exist.** The answer can be negative.
6. **The O(n) tracker miscoded:** updating max3 before max2 destroys the chain. Careful with the cascade order.

---

## 8. The shape — extremes for product

The pattern: **for max/min of products, the EXTREMES (largest, smallest) matter; middles don't.**

| Problem | Extremes used |
|---|---|
| **This problem** | top 3 OR bottom 2 + top 1 |
| Maximum Product Subarray | track running max AND min |
| Maximum of Absolute Value Expression | extremes by transformed coords |
| Minimum Product of Three Numbers | symmetric: bottom 3 OR top 2 + bottom 1 |

**Pattern to internalize:**

> "For PRODUCT extremes, consider all sign-combinations of extreme elements. Often just 2-3 candidates need checking; take min/max."

---

> **Self-check — the question to ask next time.**
>
> When you need a max/min of products of k elements:
>
> > **"Are there negatives? Then top-k alone isn't enough — pair small (negative) extremes with big (positive) extremes. Check all sign combinations of extreme elements."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Maximum_Product_of_Three_Numbers.md`](../Maximum_Product_of_Three_Numbers.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Distribute_Candies.md`](./Distribute_Candies.md).
  - Coming next: [`Maximize_Sum_After_K_Negations.md`](./Maximize_Sum_After_K_Negations.md), [`Non_overlapping_Intervals.md`](./Non_overlapping_Intervals.md).
