# Minimize Maximum Pair Sum in Array — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Minimize_Maximum_Pair_Sum_in_Array.md`](../Minimize_Maximum_Pair_Sum_in_Array.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/minimize-maximum-pair-sum-in-array/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/minimize-maximum-pair-sum-in-array/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. This problem teaches the **"pair extremes" greedy** — sort the array, pair the smallest with the largest, second-smallest with second-largest, and so on. The greedy is provable via a clean **exchange argument**. This proof technique appears in many later greedy problems.

**Map of this file (9 short sections):**

1. Read the problem
2. Small cases by hand
3. The greedy idea — pair extremes
4. Why "pair extremes" works (exchange-argument proof)
5. Code
6. Trace it
7. Common pitfalls
8. The exchange argument as a pattern
9. The shape — sort-then-pair greedies

---

## 1. Read the problem

You're given an integer array `nums` of **even length** `n`. You must split the array into **n/2 pairs**, with every element in exactly one pair.

For each pair, compute the **pair sum** (the two values added together). The "maximum pair sum" of a pairing is the largest such sum.

Your goal: choose the pairing that **minimizes the maximum pair sum**. Return that minimum value.

**Example 1:** `nums = [3, 5, 2, 3]`. Possible pairings:

- `(3, 5)` and `(2, 3)`: sums `8` and `5`. Max = 8.
- `(3, 2)` and `(5, 3)`: sums `5` and `8`. Max = 8.
- `(3, 3)` and `(5, 2)`: sums `6` and `7`. **Max = 7.** ← best so far.

Minimum achievable max: **7**.

**Example 2:** `nums = [3, 5, 4, 2, 4, 6]`. The optimal pairing turns out to be `(2, 6), (3, 5), (4, 4)` — pair sums `8, 8, 8`, max = **8**.

---

## 2. Small cases by hand

Try `nums = [1, 2, 3, 4]`:

- `(1, 2), (3, 4)`: max = 7.
- `(1, 3), (2, 4)`: max = 6.
- `(1, 4), (2, 3)`: max = **5**.  ← best

The pattern: pair the smallest with the largest, the next-smallest with the next-largest, etc.

Sorting `[1, 2, 3, 4]` ascending gives the same array. Pair `(1, 4)` and `(2, 3)`. Both sums are `5`. Max = 5. ✓

Try `nums = [1, 1, 5, 5]`:

- `(1, 1), (5, 5)`: max = 10.
- `(1, 5), (1, 5)`: max = **6**. ← best

Sort: `[1, 1, 5, 5]`. Pair `(1, 5)` and `(1, 5)`. Sums: 6 and 6. Max = 6. ✓

In every small case the rule is: **sort, then pair the i-th smallest with the i-th largest**.

---

## 3. The greedy idea — pair extremes

Here's the intuition. The maximum pair sum is going to be driven by some "heavy" pair — one with a large value in it. We want to make that heavy pair as light as possible.

The **largest** value in `nums` has to go into SOME pair. Whatever partner we give it, that pair's sum is `max_value + partner`. To minimize this sum, give the largest value the **smallest** partner possible.

Once the largest and smallest are paired, consider the SECOND-largest. It goes into some other pair. Same logic — give it the smallest remaining partner (which is now the second-smallest, since we've used the smallest).

Continue. The pattern: pair the **i-th largest** with the **i-th smallest**.

Implementation: sort ascending, then pair `nums[i]` with `nums[n - 1 - i]` for `i = 0..n/2 - 1`.

Each pair's sum: `nums[i] + nums[n - 1 - i]`. Maximum over all such sums is the answer.

---

## 4. Why "pair extremes" works (exchange-argument proof)

> **Mini-refresher: the exchange argument.**
>
> An exchange argument proves that a greedy is optimal by showing: "Any pairing that differs from the greedy choice can be improved (or kept equal) by swapping toward the greedy choice."
>
> Iteratively applying the swap turns ANY pairing into the greedy one, never increasing the answer. Therefore the greedy pairing achieves the minimum.

Suppose the optimal pairing is NOT "pair extremes." Then somewhere in the pairing, we have two pairs `(a, b)` and `(c, d)` where:

- `a < c ≤ d < b`. (So `a` is small, `b` is large, and `c, d` are inner values.)
- `a` is paired with `b`, `c` is paired with `d`.

In the "pair extremes" version, we'd pair `a` with `d` (the largest remaining if `b` is gone — but here we're keeping all four for the exchange).

Let me look at the swap: change `(a, b), (c, d)` to `(a, d), (c, b)`.

Compare maxes:

- Before: `max(a + b, c + d)`.
- After: `max(a + d, c + b)`.

We need to show: `max(a + d, c + b) ≤ max(a + b, c + d)`.

Examine each new pair:

- `a + d`: since `d < b`, we have `a + d < a + b`. So `a + d ≤ max(a + b, c + d)`. ✓
- `c + b`: since `c ≤ d` and `b > d`, we have `c + b`. Compare to `a + b`: since `c > a`, we have `c + b > a + b`. So `c + b` could exceed `a + b`. But compare to `c + d`: since `b > d`, `c + b > c + d`. Hmm.

So `c + b` is BIGGER than both `a + b` and `c + d`? Let me re-check on a small case.

`a = 1, b = 5, c = 2, d = 3`. `a + b = 6, c + d = 5`. Max = 6.
Swap: `a + d = 4, c + b = 7`. Max = 7. **The swap made it worse!**

So the exchange I described doesn't help. Let me re-think.

The correct exchange to use: swap the **partners** of the smallest with the partner of the second smallest in a way that pairs extreme-with-extreme.

Cleaner argument: suppose the optimal pairing has the **largest value `b`** NOT paired with the smallest. Say `b` is paired with `y` (some value), and the smallest `z` is paired with `w`. We want to show: swapping to `(b, z)` and `(y, w)` doesn't make the max worse.

Sums before: `b + y` and `z + w`. Max = `max(b + y, z + w)`.
Sums after:  `b + z` and `y + w`.

Is `max(b + z, y + w) ≤ max(b + y, z + w)`?

Examine:

- `b + z ≤ b + y` because `z ≤ y` (z is the smallest). ✓
- `y + w` vs `max(b + y, z + w)`: since `w ≤ b` (b is the largest), `y + w ≤ y + b = b + y`. ✓

Both new sums are `≤ max(b + y, z + w)`. So `max(b + z, y + w) ≤ max(b + y, z + w)`. The swap doesn't make max worse.

After this swap, `b` is paired with `z` (smallest with largest — matches the greedy choice). Now apply the same argument inductively to the remaining `n − 2` elements: in the remaining array, the largest should pair with the smallest, etc.

**Conclusion:** any optimal pairing can be transformed into "pair extremes" via these swaps without increasing the max. Therefore "pair extremes" is optimal.

---

## 5. Code

```cpp
int minPairSum(vector<int>& nums) {
    sort(nums.begin(), nums.end());
    int n = nums.size();
    int best = 0;
    for (int i = 0; i < n / 2; i++) {
        int pairSum = nums[i] + nums[n - 1 - i];
        if (pairSum > best) best = pairSum;
    }
    return best;
}
```

Six lines.

**Python:**

```python
def minPairSum(nums):
    nums.sort()
    n = len(nums)
    best = 0
    for i in range(n // 2):
        pair_sum = nums[i] + nums[n - 1 - i]
        if pair_sum > best:
            best = pair_sum
    return best
```

**JavaScript:**

```javascript
function minPairSum(nums) {
    nums.sort((a, b) => a - b);
    const n = nums.length;
    let best = 0;
    for (let i = 0; i < n / 2; i++) {
        const pairSum = nums[i] + nums[n - 1 - i];
        if (pairSum > best) best = pairSum;
    }
    return best;
}
```

All `O(n log n)` (dominated by sort), `O(1)` extra space if sorted in-place.

---

## 6. Trace it

**`nums = [3, 5, 2, 3]`:**

```
Sort: [2, 3, 3, 5].  n = 4.
i = 0:  pairSum = nums[0] + nums[3] = 2 + 5 = 7.  best = 7.
i = 1:  pairSum = nums[1] + nums[2] = 3 + 3 = 6.  best = max(7, 6) = 7.
Return 7.  ✓
```

**`nums = [3, 5, 4, 2, 4, 6]`:**

```
Sort: [2, 3, 4, 4, 5, 6].  n = 6.
i = 0:  pairSum = 2 + 6 = 8.  best = 8.
i = 1:  pairSum = 3 + 5 = 8.  best = 8.
i = 2:  pairSum = 4 + 4 = 8.  best = 8.
Return 8.  ✓
```

Notice in the second example, ALL three pair sums are 8 — the algorithm "balances" them. That's the hallmark of the greedy working: the extremes-pairing strategy tends to equalize pair sums.

---

## 7. Common pitfalls

1. **Forgetting to sort.** Without sorting, the indices `i` and `n - 1 - i` don't refer to "i-th smallest" and "i-th largest." The whole algorithm collapses. Sort FIRST.

2. **Pairing adjacent values instead of extremes.** `(nums[0], nums[1]), (nums[2], nums[3]), ...` is the WORST pairing — it pairs small-with-small (creating tiny sums) and large-with-large (creating huge sums, which dominates the max). That MAXIMIZES the max, opposite of what we want.

3. **Looping `i = 0..n - 1` instead of `i = 0..n/2 - 1`.** Going through all `n` indices would compute each pair sum TWICE (once for each endpoint of the pair). The loop should stop at the middle.

4. **Integer overflow on the sum.** For typical constraints (`nums[i]` up to `10⁵`), pair sums fit in `int32`. For huge constraints, use `long long`.

5. **Trying to brute-force all pairings.** The number of pairings of n items is `n! / (2^(n/2) × (n/2)!)` — astronomical. Brute force is infeasible above n = 12 or so. The greedy collapses this to O(n log n).

---

## 8. The exchange argument as a pattern

The proof in §4 is an example of an **exchange argument**, the standard tool for proving greedy algorithms correct:

> **Exchange argument template:**
>
> 1. Suppose the optimal solution differs from the greedy choice somewhere.
> 2. Identify a specific "swap" you can apply that brings the optimal one step closer to the greedy.
> 3. Show that the swap doesn't make the objective worse.
> 4. Apply swaps iteratively. The optimal converges to the greedy, never getting worse.
> 5. Conclude: the greedy is optimal.

This shape appears in many greedy proofs:

| Problem | Greedy rule | Exchange |
|---|---|---|
| **This problem** | pair smallest with largest | swap b's partner with z's partner (b = max, z = min) |
| Interval Scheduling Maximization | sort by end time, pick earliest end | swap any other choice's "first interval" with the earliest-ending one |
| Huffman coding | merge two smallest weights first | swap any tree where the two smallest aren't siblings |
| Activity selection | pick non-overlapping with earliest finish | same as interval scheduling |
| Cookies / kids assignment | match smallest cookie with smallest kid | swap any mismatched assignments |

Once you see the pattern a few times, "exchange argument" becomes your reflex when you need to prove a greedy.

---

## 9. The shape — sort-then-pair greedies

The "sort, then pair extremes" specific pattern appears in:

| Problem | Pair criterion |
|---|---|
| **This problem** (Minimize Maximum Pair Sum) | sum |
| Minimize maximum pair PRODUCT | same (pair small with large) |
| Maximize MINIMUM pair sum | sort + pair adjacent (opposite of extremes) |
| Maximize MINIMUM pair PRODUCT | sort + pair adjacent |
| Fair team assignments (split into two teams of equal size to balance strength) | similar swap-extremes idea |
| Boats to Save People (LC #881) | sort + pair lightest with heaviest if they fit; else heaviest goes alone |

**Pattern to internalize:**

> "When the objective is to MINIMIZE the MAXIMUM (or MAXIMIZE the MINIMUM) of some pairwise quantity, sort the array, then pair extremes — the i-th smallest with the i-th largest. Prove correctness via an exchange argument."

The opposite ("pair adjacent in sorted order") solves the dual problem: maximize the minimum or minimize the maximum (depending on the direction of the objective).

---

> **Self-check — the question to ask next time.**
>
> When you see a problem that asks to **partition items into groups (pairs, triplets, etc.) and minimize the max (or maximize the min) of some per-group quantity**, before brute-forcing all partitions, ask:
>
> > **"If I sort and pair extremes (smallest with largest), is the resulting partition optimal? Can I prove it with an exchange argument?"**
>
> If yes — you've turned an exponential-search problem into a sort + linear scan.

---

## Cross-references

- **Reference card (post-mastery):** [`../Minimize_Maximum_Pair_Sum_in_Array.md`](../Minimize_Maximum_Pair_Sum_in_Array.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Two_Sum_II_Input_Array_Is_Sorted.md`](./Two_Sum_II_Input_Array_Is_Sorted.md) — same "two indices walking inward" structure, different objective.
  - Coming later in Greedy topic: Assign Cookies, Non-overlapping Intervals — same exchange-argument shape.
