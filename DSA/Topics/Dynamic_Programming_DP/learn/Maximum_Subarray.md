# Maximum Subarray — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Maximum_Subarray.md`](../Maximum_Subarray.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/maximum-subarray/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: KADANE'S algorithm. Instead of asking "what's the best subarray overall?", ask "what's the best subarray ENDING at index i?" The smaller question has a clean recurrence: `best_ending(i) = a[i] + max(0, best_ending(i-1))`. Drop negative running sums.**

**Map of this file (9 sections):**

1. Read the problem
2. The O(n²) brute force
3. The pivot question — "best subarray ending at i"
4. The recurrence
5. Code
6. Trace it
7. Why "max with 0" — the reset move
8. Common pitfalls
9. The shape — Kadane / running prefix DP

---

## 1. Read the problem

Given an array of integers (positives and negatives), find the CONTIGUOUS subarray with the LARGEST SUM. Return that sum.

**Example:** `[-2, 1, -3, 4, -1, 2, 1, -5, 4]` → best subarray is `[4, -1, 2, 1]` with sum **6**.

---

## 2. The O(n²) brute force

For every start i, extend a running sum to every end j ≥ i:

```python
best = -inf
for i in range(n):
    s = 0
    for j in range(i, n):
        s += a[j]
        best = max(best, s)
```

O(n²). For n = 10^5, 10^10 ops — too slow. We need O(n).

The wasteful part: each `(i, j)` pair recomputes prefix sums independently. We're not LEARNING anything from previous (i, j) pairs.

---

## 3. The pivot question — "best subarray ending at i"

> **Mini-refresher: the magic reframe.**
>
> Instead of "what's the overall best subarray?" ask:
>
> > **"What's the best subarray that ENDS exactly at index i?"**
>
> Call that `f(i)`. The overall answer = `max over i of f(i)`.
>
> Why this helps: f(i) depends on JUST f(i-1) — a 1D DP, O(n) total.

The trick is fixing ONE endpoint of the subarray. Once fixed, the choice is binary: start fresh at i, or extend the best subarray ending at i-1.

---

## 4. The recurrence

The subarray ending at i either:
1. Is just `[a[i]]` alone → sum = `a[i]`.
2. Extends the best subarray ending at i-1 → sum = `f(i-1) + a[i]`.

So:
```
f(i) = max(a[i], f(i-1) + a[i]) = a[i] + max(0, f(i-1))
```

The second form says: "always add `a[i]`; ONLY also add the previous running sum if it was POSITIVE."

Base: f(0) = a[0]. Answer: `max(f(0), f(1), ..., f(n-1))`.

---

## 5. Code

**C++:**

```cpp
int maxSubArray(vector<int>& a) {
    int cur = a[0], best = a[0];
    for (int i = 1; i < (int)a.size(); ++i) {
        cur = max(a[i], cur + a[i]);
        best = max(best, cur);
    }
    return best;
}
```

**Python:**

```python
def maxSubArray(a):
    cur = best = a[0]
    for x in a[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best
```

Complexity: **O(n)** time, **O(1)** space.

---

## 6. Trace it

`a = [-2, 1, -3, 4, -1, 2, 1, -5, 4]`.

```
i=0: cur = -2,  best = -2.
i=1: cur = max(1, -2+1) = 1.       best = 1.
i=2: cur = max(-3, 1-3) = -2.      best = 1.
i=3: cur = max(4, -2+4) = 4.       best = 4.    ← RESET (drop -2)
i=4: cur = max(-1, 4-1) = 3.       best = 4.
i=5: cur = max(2, 3+2) = 5.        best = 5.
i=6: cur = max(1, 5+1) = 6.        best = 6.    ← answer
i=7: cur = max(-5, 6-5) = 1.       best = 6.
i=8: cur = max(4, 1+4) = 5.        best = 6.

Return 6.  ✓
```

The KEY moment is i=3: cur was -2 (useless to carry forward), so we RESET to just a[3]=4. That reset is Kadane's entire idea.

---

## 7. Why "max with 0" — the reset move

> **Mini-refresher: a negative running sum hurts you.**
>
> If `f(i-1) < 0`, then extending hurts: `f(i-1) + a[i] < a[i]`. Better to drop the past and start fresh.
>
> Equivalently: `f(i) = a[i] + max(0, f(i-1))`. The `max(0, ...)` is the reset.

This is the LOCAL move that gives a GLOBAL optimum. Whenever the "best so far" goes negative, throw it away. Beautiful.

---

## 8. Common pitfalls

1. **Initializing `best` to 0.** Wrong when all elements are negative — answer would be the LEAST-negative, not 0. Initialize to `a[0]`.
2. **Initializing `best` to `INT_MIN` then forgetting the first element.** Loop from i=0, not i=1, OR initialize to a[0] and loop from i=1.
3. **Treating "subarray" as "subset."** Subarray must be CONTIGUOUS. No skipping.
4. **Forgetting the empty-subarray edge case.** Most variants require non-empty subarray. If empty is allowed, answer is `max(best, 0)`.
5. **Trying divide-and-conquer.** Works but O(n log n) — slower than Kadane.
6. **Computing actual subarray indices without tracking starts.** If asked for indices, track them: when `cur` resets, the new start is i; record best's start/end when best updates.

---

## 9. The shape — Kadane / running prefix DP

The pattern: **for "best contiguous something" problems, fix one endpoint; the answer at i depends on the answer at i-1 with a RESET option.**

| Problem | Local choice |
|---|---|
| **This problem** | reset or extend |
| Maximum Product Subarray | track running max AND min (negatives flip) |
| Maximum Sum Circular Subarray | normal max OR total − min |
| House Robber | take or skip current |
| Best Time to Buy and Sell Stock | track running min price |
| Longest Increasing Subsequence (O(n²) version) | extend if strictly increasing |

**Pattern to internalize:**

> "When the problem says 'best contiguous (or sequential) thing,' ask 'best one ENDING at i?'. That smaller question has a recurrence with just one previous state. Reset when accumulator goes wrong-direction."

---

> **Self-check — the question to ask next time.**
>
> When you see "max/min sum of contiguous subarray," ask:
>
> > **"Best one ending at i = max(a[i], best ending at i-1 + a[i]). Track global best across all i. Reset when running sum becomes a liability."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Maximum_Subarray.md`](../Maximum_Subarray.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Climbing_Stairs.md`](./Climbing_Stairs.md), [`Min_Cost_Climbing_Stairs.md`](./Min_Cost_Climbing_Stairs.md).
  - Coming next: [`Unique_Paths.md`](./Unique_Paths.md), [`Unique_Paths_II.md`](./Unique_Paths_II.md).
