# Climbing Stairs — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Climbing_Stairs.md`](../Climbing_Stairs.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/climbing-stairs/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/climbing-stairs/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: the count of ways to reach step n = ways to reach (n-1) + ways to reach (n-2) — because your last move is either a 1-step or a 2-step. This is FIBONACCI in disguise. THE introductory DP problem; the "what was my last move?" trick generalizes to all DP.**

**Map of this file (8 sections):**

1. Read the problem
2. Hand-count small cases
3. Spot the Fibonacci pattern
4. Derive the recurrence — "what was the last move?"
5. Code (rolling variables, O(1) space)
6. Trace it
7. Common pitfalls
8. The shape — 1D linear DP

---

## 1. Read the problem

Staircase of n steps. At each move you take 1 step or 2 steps. How many distinct sequences of moves reach the top?

**Examples:** n=1 → 1. n=2 → 2. n=3 → 3. n=4 → 5. n=5 → 8.

(Just count sequences; not minimize, not optimize — just enumerate by counting.)

---

## 2. Hand-count small cases

When the problem is abstract, COUNT BY HAND for tiny inputs.

- **n=1:** `[1]` → **1**.
- **n=2:** `[1,1]`, `[2]` → **2**.
- **n=3:** `[1,1,1]`, `[1,2]`, `[2,1]` → **3**.
- **n=4:** `[1,1,1,1]`, `[1,1,2]`, `[1,2,1]`, `[2,1,1]`, `[2,2]` → **5**.
- **n=5:** all 1s (1) + four 4-elem with one 2 (4) + three 3-elem with two 2s (3) = **8**.

Sequence: `1, 2, 3, 5, 8, ...`

---

## 3. Spot the Fibonacci pattern

3 = 2 + 1, 5 = 3 + 2, 8 = 5 + 3 — each term is the sum of the previous two. That's Fibonacci.

But spotting isn't proving. Why?

---

## 4. Derive the recurrence — "what was the last move?"

> **Mini-refresher: condition on the LAST move.**
>
> To reach step n, your last move was either:
> - A **1-step** from step (n-1) — there are `ways(n-1)` of getting to (n-1) first.
> - A **2-step** from step (n-2) — there are `ways(n-2)` of getting to (n-2) first.
>
> These cases are DISJOINT (different last move) and EXHAUSTIVE (no other way to arrive at n).
>
> So `ways(n) = ways(n-1) + ways(n-2)`.

That's a complete proof. The pattern wasn't a coincidence — it's forced by the structure.

This "condition on the last action" technique is THE most generalizable trick in DP. Every grid path / sequence / decision problem uses it.

---

## 5. Code (rolling variables, O(1) space)

We only need the last two values. No array needed.

**C++:**

```cpp
int climbStairs(int n) {
    if (n <= 2) return n;
    int a = 1, b = 2;
    for (int i = 3; i <= n; ++i) {
        int c = a + b;
        a = b;
        b = c;
    }
    return b;
}
```

**Python:**

```python
def climbStairs(n):
    if n <= 2:
        return n
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b
```

Complexity: **O(n)** time, **O(1)** space.

(For huge n, matrix exponentiation gives O(log n), but that's overkill for typical constraints.)

---

## 6. Trace it

n = 5.

```
a = 1, b = 2.   (ways(1) = 1, ways(2) = 2)
i=3: c = 1 + 2 = 3. a = 2, b = 3.
i=4: c = 2 + 3 = 5. a = 3, b = 5.
i=5: c = 3 + 5 = 8. a = 5, b = 8.

Return 8.  ✓ (matches hand-count of 8)
```

---

## 7. Common pitfalls

1. **Naive recursion without memoization.** O(2^n) — exponential blowup. For n=40 the program hangs.
2. **Wrong base cases.** ways(0) = 1 (empty sequence reaches 0), ways(1) = 1, ways(2) = 2. Off-by-one is the most common mistake.
3. **Using `long` unnecessarily.** ways(45) = ~10^9 fits in int. Only need long for n > 90.
4. **Treating "1-step then 2-step" as the same as "2-step then 1-step".** They're distinct sequences (problem counts ordered moves).
5. **Allocating a full DP array.** Wastes O(n) space; rolling 2 variables is enough.

---

## 8. The shape — 1D linear DP

The pattern: **`dp[i]` depends on a constant number of previous values.**

| Problem | Recurrence |
|---|---|
| **This problem** | `f(n) = f(n-1) + f(n-2)` |
| Min Cost Climbing Stairs | `f(i) = min(f(i-1) + c[i-1], f(i-2) + c[i-2])` |
| Maximum Subarray (Kadane) | `f(i) = max(a[i], f(i-1) + a[i])` |
| House Robber | `f(i) = max(f(i-1), f(i-2) + a[i])` |
| Decode Ways | `f(i) = f(i-1) + maybe f(i-2)` |
| Fibonacci | `f(n) = f(n-1) + f(n-2)` |

**Pattern to internalize:**

> "When the answer at step n depends only on a CONSTANT number of earlier steps, you have 1D linear DP. Roll a few variables; O(n) time, O(1) space. The 'what was the last move/decision?' question gives you the recurrence."

---

> **Self-check — the question to ask next time.**
>
> When the problem asks "count ways" or "find min/max" over sequential decisions, ask:
>
> > **"What was my last move? Case-split. The cases must be disjoint and exhaustive. Sum (or min/max) over them. That's the recurrence."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Climbing_Stairs.md`](../Climbing_Stairs.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: [`Min_Cost_Climbing_Stairs.md`](./Min_Cost_Climbing_Stairs.md), [`Maximum_Subarray.md`](./Maximum_Subarray.md), [`Unique_Paths.md`](./Unique_Paths.md).
