# Bulb Switcher — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Bulb_Switcher.md`](../Bulb_Switcher.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/bulb-switcher/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/bulb-switcher/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **The lesson: a procedural simulation hides a number-theory observation. Bulb i toggled = (divisors of i). Bulb stays ON ⇔ odd number of divisors ⇔ i is a PERFECT SQUARE. Answer = floor(sqrt(n)).**

**Map of this file (8 sections):**

1. Read the problem
2. When is a bulb on?
3. Divisor parity → perfect squares
4. Counting perfect squares ≤ n
5. Code
6. Trace it
7. Common pitfalls
8. The shape — simulation hiding a closed form

---

## 1. Read the problem

`n` bulbs, all OFF initially. Perform n rounds:
- Round r: toggle every r-th bulb.

After n rounds, how many bulbs are ON?

**Examples:**

- n=3 → Round 1: all ON. Round 2: toggle bulb 2. Round 3: toggle bulb 3. Final `[on, off, off]` → **1**.
- n=4 → Final `[on, off, off, on]` → **2**.
- n=12 → **3** (bulbs 1, 4, 9).

---

## 2. When is a bulb on?

> **Mini-refresher: bulb i is toggled once per divisor of i.**
>
> Round r toggles bulbs r, 2r, 3r, ... So bulb i is toggled in round r iff `r divides i`.
>
> Total toggles of bulb i = number of divisors of i.
>
> Bulb i is ON at the end iff it was toggled an ODD number of times ⇔ i has an ODD number of divisors.

---

## 3. Divisor parity → perfect squares

> **Mini-refresher: divisors come in pairs, except for perfect squares.**
>
> For any divisor d of n, `n/d` is ALSO a divisor. So divisors pair up: (d, n/d).
>
> EXCEPTION: when `d = n/d`, i.e., `d² = n`. This is the case when n is a perfect square — its square root pairs with itself (counted ONCE, not twice).
>
> So:
> - Non-square n → even number of divisors.
> - Square n → odd number of divisors.

Therefore: bulb i is on after all rounds ⇔ i is a perfect square.

---

## 4. Counting perfect squares ≤ n

Perfect squares in [1, n]: 1², 2², 3², ..., k² where k² ≤ n.

Count = `floor(sqrt(n))`.

---

## 5. Code

**C++:**

```cpp
int bulbSwitch(int n) {
    return (int)sqrt((double)n);
}
```

**Safer (avoids floating-point hiccups for huge n):**

```cpp
int bulbSwitch(int n) {
    int s = (int)sqrt((double)n);
    while ((long long)(s + 1) * (s + 1) <= n) s++;
    while ((long long)s * s > n) s--;
    return s;
}
```

**Python:**

```python
import math
def bulbSwitch(n):
    return int(math.isqrt(n))   # integer square root, exact
```

Complexity: **O(1)** time, **O(1)** space.

---

## 6. Trace it

- n=3: sqrt(3) ≈ 1.73 → floor 1. Perfect squares ≤ 3: just {1}. **1**. ✓
- n=4: sqrt(4) = 2. {1, 4}. **2**. ✓
- n=12: sqrt(12) ≈ 3.46 → floor 3. {1, 4, 9}. **3**. ✓

---

## 7. Common pitfalls

1. **Simulating literally.** O(n²) — slow for large n. Recognize the divisor-count pattern instead.
2. **Floating-point sqrt inaccuracy.** For large n, `(int)sqrt(...)` can be 1 off. Use `math.isqrt` (Python) or correct with a guard loop (C++).
3. **Counting bulbs from 0 instead of 1.** Bulbs are 1-indexed in the problem statement; 1 has divisors {1} — odd, ON. (sqrt(n) naturally handles this — 1 = 1² is included.)
4. **Including 0 as a perfect square.** 0² = 0 is not in [1, n]. Don't count it.
5. **Trying to find a different invariant.** The divisor-parity insight is the right one — don't overcomplicate.

---

## 8. The shape — simulation hiding a closed form

The pattern: **a procedural problem with a mathematical invariant beneath.**

| Problem | Closed-form insight |
|---|---|
| **This problem** | divisor count parity → perfect squares |
| Nth Tribonacci Number | recurrence has matrix form |
| Climbing Stairs | Fibonacci-like |
| Find the Nth Digit | digit-length blocks |
| Find Smallest Missing Number | bucket-based O(n) |
| Reach a Number (LC 754) | triangular numbers parity |

**Pattern to internalize:**

> "When a simulation feels too slow, ask: what's INVARIANT about the final state? Often it's a counting argument (parity, divisor count, modular structure) that collapses to O(1) or O(log n)."

The thought sequence:
1. "What does the final state depend on?" → A count.
2. "When is the count odd/even/k?" → A number-theoretic property.
3. "Can I directly count items with that property?" → Closed form.

---

> **Self-check — the question to ask next time.**
>
> When a simulation problem has a clean rule and feels n² or worse, ask:
>
> > **"What does each item's final state depend on? Often a divisor/parity count. Can I count those directly?"**

---

## Cross-references

- **Reference card (post-mastery):** [`../Bulb_Switcher.md`](../Bulb_Switcher.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Count_Primes.md`](../../Graph_BFS_DFS_Dijkstra_DSU/learn/Count_Primes.md), [`Find_GCD_of_Array.md`](../../Math/learn/Find_GCD_of_Array.md).
  - **Topic complete — next: Dynamic Programming.**
