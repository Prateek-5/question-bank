# Min Cost Climbing Stairs — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Min_Cost_Climbing_Stairs.md`](../Min_Cost_Climbing_Stairs.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/min-cost-climbing-stairs/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: same "what was my last move?" structure as Climbing Stairs, but with WEIGHTED edges. The TOP is position n (one past the last step), and arriving there costs nothing additional. Replace `+` with `min(+cost)`.**

**Map of this file (8 sections):**

1. Read the problem (carefully — the "top" definition matters)
2. Hand-trace a tiny case
3. The recurrence
4. Why we use `costToReach(i)`, not `costAt(i)`
5. Code
6. Trace it
7. Common pitfalls
8. The shape — weighted 1D DP

---

## 1. Read the problem (carefully — the "top" definition matters)

Array `cost` of length n; each step has a cost `cost[i]`. You can start from index 0 OR index 1 (BOTH free). From step i, you pay `cost[i]` and then jump 1 or 2 steps. **The "top" is position n** — ONE past the last step.

You DON'T pay anything to be AT the top. You pay to LEAVE a step.

**Examples:**

- `cost = [10, 15, 20]` → top is position 3.
  - Start 1 (free) → pay 15 → jump 2 → at top. Total **15**.
- `cost = [1, 100]` → top is position 2.
  - Start 0 (free) → pay 1 → jump 2 → at top. Total **1**.

---

## 2. Hand-trace a tiny case

`cost = [10, 15, 20]`:

| Start | Path | Total |
|---|---|---|
| 0 (free) | pay 10, jump 1 → step 1, pay 15, jump 1 → step 2, pay 20, jump 1 → top | 45 |
| 0 (free) | pay 10, jump 1 → step 1, pay 15, jump 2 → top | 25 |
| 0 (free) | pay 10, jump 2 → step 2, pay 20, jump 1 → top | 30 |
| 1 (free) | pay 15, jump 1 → step 2, pay 20, jump 1 → top | 35 |
| 1 (free) | pay 15, jump 2 → top | **15** ← min |

---

## 3. The recurrence

> **Mini-refresher: "what was my last move?" — same DP move as Climbing Stairs.**
>
> Let `f(i)` = minimum cost to ARRIVE at position i (no payment for being there).
>
> To arrive at i (with i ≥ 2), the previous position was either:
> - i-1 (paying `cost[i-1]` to leave it), so `f(i-1) + cost[i-1]`.
> - i-2 (paying `cost[i-2]` to leave it), so `f(i-2) + cost[i-2]`.
>
> So `f(i) = min(f(i-1) + cost[i-1], f(i-2) + cost[i-2])`.
>
> **Base cases:** f(0) = 0 and f(1) = 0 (both starts are free).
>
> **Answer:** f(n).

---

## 4. Why we use `costToReach(i)`, not `costAt(i)`

We define f(i) as "minimum to ARRIVE at i, BEFORE paying cost[i]." Why not "minimum to be at i including its cost"?

Both work, but the "arrive" framing is cleaner because:
- f(0) = f(1) = 0 (free starts).
- The "top" (position n) has no cost — naturally fits "arrive at n" without paying anything.

If you instead define f(i) = "leave step i, fully paid up," you have to handle "the top isn't a step" specially. Stick with "arrive" semantics.

---

## 5. Code

**C++:**

```cpp
int minCostClimbingStairs(vector<int>& cost) {
    int n = cost.size();
    int prev2 = 0, prev1 = 0;
    for (int i = 2; i <= n; ++i) {
        int cur = min(prev1 + cost[i - 1], prev2 + cost[i - 2]);
        prev2 = prev1;
        prev1 = cur;
    }
    return prev1;
}
```

**Python:**

```python
def minCostClimbingStairs(cost):
    n = len(cost)
    prev2 = prev1 = 0
    for i in range(2, n + 1):
        cur = min(prev1 + cost[i - 1], prev2 + cost[i - 2])
        prev2, prev1 = prev1, cur
    return prev1
```

Complexity: **O(n)** time, **O(1)** space.

---

## 6. Trace it

`cost = [10, 15, 20]`. n = 3.

```
prev2 = 0, prev1 = 0.  (f(0), f(1))

i=2: cur = min(prev1 + cost[1], prev2 + cost[0]) = min(0+15, 0+10) = 10.
     prev2 = 0, prev1 = 10.  (f(2) = 10)
i=3: cur = min(prev1 + cost[2], prev2 + cost[1]) = min(10+20, 0+15) = 15.
     prev2 = 10, prev1 = 15.  (f(3) = 15)

Return prev1 = 15.  ✓
```

---

## 7. Common pitfalls

1. **Returning `cost[n-1]` or similar.** The answer is f(n), NOT f(n-1).
2. **Off-by-one on `cost[i-1]` vs `cost[i]`.** Since f(i) is "arrive at i," the move from i-1 to i pays `cost[i-1]`.
3. **Forcing the start to position 0.** The problem allows STARTING from 0 OR 1, both free. f(1) = 0, not cost[0].
4. **Trying to recover the actual path with O(1) space.** Path recovery needs O(n) memory; if asked, switch back to a full DP array.
5. **Negative costs.** The recurrence still works (min handles any sign). No special case needed.

---

## 8. The shape — weighted 1D DP

The pattern: **same "last move" decomposition as Climbing Stairs, but with COSTS attached to edges.**

| Problem | Recurrence |
|---|---|
| Climbing Stairs | `f(n) = f(n-1) + f(n-2)` (counting) |
| **This problem** | `f(i) = min(f(i-1) + cost[i-1], f(i-2) + cost[i-2])` (min cost) |
| House Robber | `f(i) = max(f(i-1), f(i-2) + a[i])` (max value) |
| Paint Fence | `f(i) = f(i-1)*(k-1) + f(i-2)*(k-1)` (counting with rule) |

**Pattern to internalize:**

> "Counting → sum recurrence; min-cost → min(prev + edge_cost) recurrence; max-value → max(prev + edge_value). Same DP shape, different aggregator."

---

> **Self-check — the question to ask next time.**
>
> When the problem reads "min cost to reach the end with steps 1 or 2 (or k)," ask:
>
> > **"Same recurrence as Climbing Stairs, but `min(prev + edge_cost)` instead of `prev + prev`. Mind the off-by-one: f(i) is 'arrive at i,' top is at index n."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Min_Cost_Climbing_Stairs.md`](../Min_Cost_Climbing_Stairs.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Climbing_Stairs.md`](./Climbing_Stairs.md).
  - Coming next: [`Maximum_Subarray.md`](./Maximum_Subarray.md), [`Unique_Paths.md`](./Unique_Paths.md).
