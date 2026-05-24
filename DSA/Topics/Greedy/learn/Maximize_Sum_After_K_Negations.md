# Maximize Sum After K Negations — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Maximize_Sum_After_K_Negations.md`](../Maximize_Sum_After_K_Negations.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/maximize-sum-of-array-after-k-negations/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: flip the most-negative element first (biggest gain). When negatives run out, parity decides — odd remaining flips = flip the smallest absolute value; even = no-op. Or: just use a MIN-HEAP that always flips the current minimum.**

**Map of this file (9 sections):**

1. Read the problem
2. What each flip does to the sum
3. The greedy rule
4. Parity for leftover flips
5. Code (sort + heap versions)
6. Trace it
7. Why greedy is optimal
8. Common pitfalls
9. The shape — repeated greedy choice

---

## 1. Read the problem

Array `nums` and integer `k`. Perform EXACTLY `k` negations (each negation flips one element's sign; the same element can be flipped multiple times). Maximize the final sum.

**Examples:**

- `nums = [4, 2, 3], k = 1` → flip 2 → sum = 4 - 2 + 3 = 5? wait. Best: flip 2 (smallest positive) → 4 + (-2) + 3 = 5. Actually flipping ANY single element makes that element negative — flipping the smallest is least harmful. Answer **5**.

  Hmm — actually, flipping 2 gives `[4, -2, 3]`, sum 5. Flipping 3 gives `[4, 2, -3]`, sum 3. Flipping 4 gives `[-4, 2, 3]`, sum 1. So **5** is correct (flip smallest positive).

- `nums = [-2, 3, -1, 5, -6], k = 3` → flip all 3 negatives → `[2, 3, 1, 5, 6]` → sum **17**.

---

## 2. What each flip does to the sum

> **Mini-refresher: per-flip delta.**
>
> - Flipping a NEGATIVE `-x`: sum gains `2x` (turn it into +x). **Good.**
> - Flipping a ZERO: sum unchanged. **Free.**
> - Flipping a POSITIVE `x`: sum loses `2x`. **Bad.**
>
> So we want to flip negatives whenever possible — biggest-magnitude first.

---

## 3. The greedy rule

1. **Phase 1:** flip the most-negative values, one at a time, until either k flips done OR no negatives remain.
2. **Phase 2:** if flips remain, they must hit non-negatives. Strategy:
   - If any ZERO exists, target it (free) and you're done.
   - Otherwise, parity matters (see next section).

---

## 4. Parity for leftover flips

If we have `k_remaining` flips on an all-non-negative array (no zeros):

> **Mini-refresher: pair up flips on the smallest element.**
>
> Flipping the smallest positive `m` twice = m → -m → m. No-op.
>
> - If `k_remaining` is EVEN: pair them all on the smallest. No change.
> - If `k_remaining` is ODD: pair all but one; the one leftover must turn the smallest into its negative. Sum drops by `2m`.

So the loss is at most `2 × smallest_absolute_value`, but ONLY when `k_remaining` is odd.

---

## 5. Code (sort + heap versions)

**C++ — sort by absolute value:**

```cpp
int largestSumAfterKNegations(vector<int>& nums, int k) {
    sort(nums.begin(), nums.end(), [](int a, int b) {
        return abs(a) < abs(b);
    });

    for (int i = (int)nums.size() - 1; i >= 0 && k > 0; --i) {
        if (nums[i] < 0) {
            nums[i] = -nums[i];
            k--;
        }
    }
    if (k % 2 == 1) nums[0] = -nums[0];   // smallest |value| at index 0
    return accumulate(nums.begin(), nums.end(), 0);
}
```

**C++ — min-heap (elegant):**

```cpp
int largestSumAfterKNegations(vector<int>& nums, int k) {
    priority_queue<int, vector<int>, greater<int>> pq(nums.begin(), nums.end());
    while (k--) {
        int x = pq.top(); pq.pop();
        pq.push(-x);
    }
    int sum = 0;
    while (!pq.empty()) { sum += pq.top(); pq.pop(); }
    return sum;
}
```

The heap version is delightfully simple — each iteration flips THE current minimum, which naturally implements the greedy rule.

Complexity: sort version **O(n log n)**; heap version **O((n + k) log n)**.

---

## 6. Trace it

**`nums = [-2, 3, -1, 5, -6], k = 3`:**

Sort by |value|: `[-1, -2, 3, 5, -6]` (abs 1, 2, 3, 5, 6).

Walk right-to-left:
- index 4 (-6): negative, flip → 6. k=2.
- index 3 (5): positive, skip.
- index 2 (3): positive, skip.
- index 1 (-2): negative, flip → 2. k=1.
- index 0 (-1): negative, flip → 1. k=0.

Array: `[1, 2, 3, 5, 6]`. k=0, no parity adjustment. Sum = **17**. ✓

**`nums = [4, 2, 3], k = 1`:**

Sort by |value|: `[2, 3, 4]`.

Walk right-to-left, k=1:
- 4: positive, skip.
- 3: positive, skip.
- 2: positive, skip.

k=1 remaining, odd. Flip smallest (index 0): 2 → -2.

Array: `[-2, 3, 4]`. Sum = **5**. ✓

---

## 7. Why greedy is optimal

> **Mini-refresher: exchange argument.**
>
> Suppose OPT differs from greedy. Find the first divergence:
> - If OPT skips a "should-flip" negative that greedy flips: swap — OPT now flips the negative, gaining 2|x|. Whatever OPT was doing elsewhere is at best as good.
> - If OPT flips a positive when greedy would have flipped a negative: swap — gain 2|negative| + 2|positive|.
>
> Each swap improves or maintains OPT's sum. So greedy ≥ OPT.

The parity tail: with no negatives left, the smallest-absolute element absorbs minimum loss when odd flips remain.

---

## 8. Common pitfalls

1. **Stopping when k > 0 but no negatives.** You MUST use all k flips — apply parity rule.
2. **Sorting by value (not absolute value).** Confuses "smallest absolute" with "most negative."
3. **Flipping the same negative twice.** Wastes a flip. Move on to the next.
4. **Forgetting zeros.** A zero absorbs all extra flips (free). Check for it before applying parity.
5. **Returning the partial sum mid-iteration.** Sum after the final parity adjustment, not before.
6. **Heap version: ending after k iterations without summing.** The pq still holds elements; sum them.

---

## 9. The shape — repeated greedy choice

The pattern: **at each step, make the LOCALLY BEST choice; trust that it accumulates to the optimal global outcome.**

| Problem | Local choice |
|---|---|
| **This problem** | flip current minimum |
| Last Stone Weight | smash heaviest two |
| Kth Largest in Stream | keep top-k via min-heap |
| Connect Ropes (min cost) | merge two smallest |
| Top K Frequent | track top-k by frequency |
| Reorganize String | always place most-frequent char (with constraint) |

**Pattern to internalize:**

> "When the problem is 'make k local choices to optimize a global sum,' a MIN-HEAP (or sort) lets you repeatedly pick the current best. Trust the greedy if exchange argument confirms."

---

> **Self-check — the question to ask next time.**
>
> When you have k operations to apply and each operation has a local cost/benefit, ask:
>
> > **"Can I greedily pick the best target at each step? A min-heap (or sort + scan) handles this. Don't forget the parity tail when you must use ALL k operations."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Maximize_Sum_After_K_Negations.md`](../Maximize_Sum_After_K_Negations.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Maximum_Product_of_Three_Numbers.md`](./Maximum_Product_of_Three_Numbers.md), [`Last_Stone_Weight.md`](../../Heap_Priority_Queue/learn/Last_Stone_Weight.md).
  - Coming next: [`Non_overlapping_Intervals.md`](./Non_overlapping_Intervals.md), [`Minimum_Platforms.md`](./Minimum_Platforms.md), [`Bulb_Switcher.md`](./Bulb_Switcher.md).
