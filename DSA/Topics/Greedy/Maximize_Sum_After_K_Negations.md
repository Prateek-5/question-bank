# Maximize Sum After K Negations

**Problem Link:**
https://leetcode.com/problems/maximize-sum-of-array-after-k-negations/

**Topic:**
Greedy

----------------------------------------

## Step 1: Read the Problem

Given an integer array `nums` and an integer `k`, perform **exactly k** negations. Each negation flips the sign of one array element (you can pick the same element multiple times). After k negations, maximize the sum.

Example: `nums = [4, 2, 3]`, k = 1.
- Flip 4 → sum = -4+2+3 = 1.
- Flip 2 → sum = 4-2+3 = 5.
- Flip 3 → sum = 4+2-3 = 3.

Best: **5**.

`nums = [-2, 3, -1, 5, -6]`, k = 3. I'll work through this more carefully in a moment.

The key subtle word: **exactly** k. We can't skip flips; we can only use them up, possibly by flipping the same element twice (which cancels).

----------------------------------------

## Step 2: Which Flips Are Helpful?

Let me think about what each flip does:
- **Flip a negative number** (say -5): it becomes +5. Sum increases by 10. *Good move.*
- **Flip zero**: stays 0. Sum unchanged. *Free move.*
- **Flip a positive**: +5 becomes -5. Sum drops by 10. *Bad move.*

So if we have any negatives, we want to flip them (best bang for the buck: flip the **most negative** first — it produces the biggest gain).

If we have no negatives left and we still have flips, we're forced to use them on non-negatives. Zeros are free. Positives are costly — but flipping the same positive twice is a net no-op.

So the question becomes: **is the number of "unproductive" flips even or odd?**

----------------------------------------

## Step 3: The Greedy Strategy Emerges

Step by step:
1. Flip the most negative values first. Each flip turns a negative into its positive twin, increasing sum by 2·|value|.
2. Keep flipping negatives until either (a) we've done k flips or (b) no negatives remain.
3. If k flips are done, we're happy.
4. If flips remain (no more negatives), we must burn them on non-negatives.
   - If a zero exists, target it — zero flips are free. We can burn all remaining flips on zero and change nothing.
   - If no zero, we must flip a positive. If remaining flips are **even**, flip the smallest positive twice, four times, etc. — always cancels out. No loss.
   - If remaining flips are **odd**, we can't fully cancel. Flip the smallest-magnitude element once to minimize loss.

This is the greedy strategy. Let me verify it's optimal.

----------------------------------------

## Step 4: Why Greedy Is Optimal

**Claim 1:** When a negative exists, we should always flip a negative (specifically, the most negative) instead of a positive.

*Proof sketch:* Flipping a negative gains 2·|negative| in sum. Flipping a positive costs 2·|positive|. Trading flips: if we're forced to flip a positive instead of the negative, we lose 2·|negative| + 2·|positive| compared to the optimal. So never do this swap.

**Claim 2:** Among negatives, flip the most negative first.

*Proof sketch:* The order doesn't actually matter for the final sum, because we're computing the sum of absolute values of everything we flip (we negate each flipped element once, net effect: add |value|·2 per flip of a negative). But flipping in order of "most negative first" is a clean mental model.

Wait, order doesn't matter? Let me check. If I flip -5 and -3, total gain is 10 + 6 = 16. If I flip -3 and -5, same gain. So order among negatives-to-be-flipped doesn't affect the final sum. What matters is *which* negatives we choose.

If k is large enough to flip every negative, we flip them all. If k is smaller, we should flip the **k** most-negative values — that gives the maximum total gain.

**Claim 3:** After all beneficial flips, if flips remain, minimize loss by flipping the smallest-absolute-value element on odd parity.

*Proof sketch:* We must use exactly k flips. Among remaining non-negatives, flipping one loses 2·|value|. Double-flipping cancels. So pair up flips; any leftover single flip should target the smallest-absolute-value element to minimize loss.

----------------------------------------

## Step 5: Trace on `[-2, 3, -1, 5, -6]`, k = 3

All negatives sorted by most-negative: -6, -2, -1. We have 3 negatives and k=3. Flip all 3.

Array after: `[2, 3, 1, 5, 6]`. k remaining = 0. Done.

Sum: 2 + 3 + 1 + 5 + 6 = **17**.

Initial sum was -2 + 3 - 1 + 5 - 6 = -1. Flipping negatives gives a gain of 2·(6 + 2 + 1) = 18. New sum: -1 + 18 = 17. ✓

Try k = 4 (one more flip than negatives). Flip all 3 negatives, then 1 remaining flip.

Remaining array: `[2, 3, 1, 5, 6]`. No zeros. 1 remaining flip (odd). Smallest-abs is 1. Flip it: becomes -1. Sum decreases by 2 (from 17 to 15).

Sum: **15**.

Try k = 5. Flip all negatives (3 flips), 2 remaining. Even, so cancel them (flip any element twice). Sum stays 17.

Actually let me double-check with odd-parity: k = 6 means 3 extra after negatives. Flip 1 → -1 (sum 15). Flip 1 again → 1 (sum 17). Flip 1 again → -1 (sum 15). Sum = 15, same as k=4. So for any odd remaining, answer is 15 (lose smallest-abs once). For any even remaining, answer is 17.

This matches my claim: remaining parity determines the outcome.

----------------------------------------

## Step 6: The Clean Algorithm

```
# Step 1: flip the k most-negative values (or all negatives if fewer than k)
sort nums by value ascending  # most-negative first
i = 0
while i < len(nums) and nums[i] < 0 and k > 0:
    nums[i] = -nums[i]
    k -= 1
    i += 1

# Step 2: handle remaining flips if any
# (all remaining flips must target non-negatives)
if k % 2 == 1:
    # need to flip one element. Pick the smallest-absolute-value.
    flip the element with smallest |value|

return sum(nums)
```

Why sort by value ascending (not absolute value)? Because the "most negative" is literally the smallest value. After flipping, they become large positives. Then when we look for "smallest absolute value" among the post-flip array, it could be anywhere — but we can find it with a scan, or by maintaining state.

Actually, a cleaner approach: sort by **absolute value**. Then smallest-abs is at the start, and we'll re-sort later... let me just show it cleanly.

----------------------------------------

## Step 7: Why Sort by Absolute Value

If we sort by `|value|` ascending:
- Negatives and positives are intermixed by magnitude.
- The **smallest-absolute** element is at index 0.

This makes the algorithm crisp:

```
sort nums by |value| ascending

# Flip negatives we encounter, going right-to-left (largest-abs first).
for i from n-1 down to 0:
    if nums[i] < 0 and k > 0:
        nums[i] = -nums[i]
        k -= 1

# If k remaining and odd, flip smallest-abs (index 0).
if k % 2 == 1:
    nums[0] = -nums[0]

return sum
```

Traversing right-to-left targets large-absolute-value elements first. If any of them are negative, we flip (biggest gain). After this pass, remaining unfllpped negatives (if any) must have been the smallest-abs values — but wait, we ran out of k, so we couldn't flip them all. That's fine.

If k > 0 after the pass, no negatives remain (we would have flipped them all). Parity decides the rest.

----------------------------------------

## Step 8: Even Cleaner — Min-Heap

The algorithm is pristine with a min-heap:

```
heap = min-heap of all nums
for _ in range(k):
    x = heap.pop()
    heap.push(-x)
return sum(heap)
```

At each step, we flip the **current minimum** — which is the most-negative element (if any exist) or the smallest non-negative (if all are non-negative). Flipping it:
- If negative: becomes positive, big gain.
- If zero: stays zero, no change.
- If positive: becomes negative, which is the new minimum. Next iteration flips it back. Pairs cancel automatically.

The heap handles the greedy choice at every step without explicit case analysis. Beautiful.

----------------------------------------

## Step 9: Complexity

- Sort approach: **O(n log n)** for sort + O(n) for pass + O(1) for parity adjustment. Total O(n log n).
- Heap approach: **O((n + k) log n)**.

For typical inputs, both are fast.

----------------------------------------

## Step 10: C++ Implementation

**Sort version:**

```cpp
int largestSumAfterKNegations(vector<int>& nums, int k) {
    sort(nums.begin(), nums.end(), [](int a, int b) {
        return abs(a) < abs(b);
    });

    // Flip largest-abs negatives first.
    for (int i = (int)nums.size() - 1; i >= 0 && k > 0; --i) {
        if (nums[i] < 0) {
            nums[i] = -nums[i];
            k--;
        }
    }
    // Handle remaining flips: if odd, flip smallest-abs (at index 0 after sort by abs).
    if (k % 2 == 1) nums[0] = -nums[0];

    return accumulate(nums.begin(), nums.end(), 0);
}
```

**Heap version (shortest, elegant):**

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

The heap version is my favorite — each step exactly implements "flip the current smallest," which is the greedy rule we derived.

----------------------------------------

## Step 11: Follow-up Questions

- **Each element can be negated at most once.** Different problem — sort by value, flip the k smallest.
- **Maximize product instead of sum.** Sign count matters more than magnitudes; different analysis.
- **Minimize sum with k negations.** Symmetric — flip the largest positives greedily.
- **k is massive (10^9).** After all negatives are flipped and the array stabilizes, further flips alternate on the smallest element. Shortcut via parity rather than iterating.
- **Array mixed with decimals / negatives of various forms.** Same greedy works as long as the "flip improves" rule holds (i.e., for any real negative, flipping gains 2·|value|).
