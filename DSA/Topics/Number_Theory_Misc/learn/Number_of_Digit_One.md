# Number of Digit One — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Number_of_Digit_One.md`](../Number_of_Digit_One.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/number-of-digit-one/description/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. **The lesson: digit DP / per-position counting. For each digit position p, count how many integers in [1, n] have a '1' at position p. Sum over positions. O(log n).**

**Map of this file (8 sections):**

1. Read the problem
2. Brute force and its limits
3. Per-position decomposition
4. The three cases (cur = 0, 1, ≥2)
5. Code
6. Trace it
7. Common pitfalls
8. The shape — digit-position counting

---

## 1. Read the problem

Given integer n ≥ 0, count the TOTAL number of '1' digits in the decimal representations of all integers from 0 to n.

**Examples:**

- n = 13 → in 1, 10, 11, 12, 13: digit 1 appears 1+1+2+1+1 = **6** times.
- n = 100 → **21** times.

---

## 2. Brute force and its limits

For each i in [1, n]: count '1's in its decimal. O(n log n) total. For n = 10⁹, ~3 × 10¹⁰ ops → too slow.

We need a position-by-position counting formula.

---

## 3. Per-position decomposition

> **Mini-refresher: count '1's at each digit position SEPARATELY.**
>
> For each power of 10 `p` (units, tens, hundreds, ...): count integers in [1, n] with digit 1 at position p.
>
> Total = sum over all positions p ≤ n.
>
> Per position, the count has a closed form depending on n's digits.

---

## 4. The three cases (cur = 0, 1, ≥2)

Let p be the current power of 10. Decompose n:
- `high = n / (p * 10)` (digits above position p).
- `cur = (n / p) % 10` (digit AT position p).
- `low = n % p` (digits below position p).

> **Mini-refresher: count of '1's at position p in [1, n].**
>
> - `cur == 0`: count = `high * p`. (Full cycles of "high" each contribute p numbers with 1 at this position.)
> - `cur == 1`: count = `high * p + low + 1`. (Full cycles + partial cycle: numbers from `high·10^{p+1} + 10^p` to n.)
> - `cur >= 2`: count = `(high + 1) * p`. (Full cycles already include the case where position-p digit is 1.)

---

## 5. Code

**C++:**

```cpp
int countDigitOne(int n) {
    long long count = 0;
    long long p = 1;
    while (p <= n) {
        long long high = n / (p * 10);
        long long cur = (n / p) % 10;
        long long low = n % p;
        if (cur == 0)      count += high * p;
        else if (cur == 1) count += high * p + low + 1;
        else               count += (high + 1) * p;
        p *= 10;
    }
    return (int)count;
}
```

Complexity: **O(log n)** time (one iteration per digit), **O(1)** space.

`long long` guards against `p * 10` overflow at high digit positions.

---

## 6. Trace it

**n = 13:**

- p=1: high=1, cur=3, low=0. cur≥2 → `(1+1)·1 = 2`.
- p=10: high=0, cur=1, low=3. cur=1 → `0·10 + 3 + 1 = 4`.
- p=100 > 13, stop.

Total = 2 + 4 = **6**.  ✓

**n = 100:**

- p=1: high=10, cur=0, low=0. cur=0 → `10·1 = 10`. (Units = 1: 1, 11, 21, ..., 91 → 10 cases.)
- p=10: high=1, cur=0, low=0. cur=0 → `1·10 = 10`. (Tens = 1: 10-19 → 10 cases.)
- p=100: high=0, cur=1, low=0. cur=1 → `0·100 + 0 + 1 = 1`. (Hundreds = 1: just 100.)
- p=1000 > 100, stop.

Total = 10 + 10 + 1 = **21**.  ✓

---

## 7. Common pitfalls

1. **Overflow on `p * 10`.** Use `long long` throughout.
2. **Off-by-one on `low + 1`.** When cur=1, we include numbers with this position = 1 AND lower-positions from 0 to `low` — that's `low + 1` numbers.
3. **Mixing 0-indexed positions.** Position 0 is units (p=1), position 1 is tens (p=10), etc. The `p` variable tracks this directly.
4. **Stopping too early.** Loop while `p <= n` — until p exceeds n's magnitude.
5. **Forgetting that high and cur depend on n's digits, not p alone.** Recompute per iteration.

---

## 8. The shape — digit-position counting

The pattern: **count occurrences of digit d across [0, n] via per-position closed-form.**

| Problem | Counts |
|---|---|
| **This problem** | digit 1 in [0, n] |
| Count Numbers with Digit Property | various properties via digit DP |
| Number of Digit Two, Five, etc. | analogous formula |
| Sum of All Digits in [0, n] | aggregate across digits 0..9 |
| Numbers at Most N Given Digit Set | digit DP with restricted digit choices |

**Pattern to internalize:**

> "Digit counting over [0, n]: per-position closed form using (high, cur, low). Three cases for cur (0, 1, ≥2). O(log n)."

For more complex digit constraints (e.g., 'has digit X', 'no two consecutive equal digits'), generalize to digit DP with memo on `(position, tight, started, ...)`.

---

> **Self-check — the question to ask next time.**
>
> When counting digit occurrences in a range:
>
> > **"Per position: split n into (high, cur, low). Apply the three-case formula. Sum over positions. O(log n)."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Number_of_Digit_One.md`](../Number_of_Digit_One.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Numbers_at_Most_N_Given_Digit_Set.md`](../../Dynamic_Programming_DP/learn/Numbers_at_Most_N_Given_Digit_Set.md), [`Find_the_Smallest_Binary_Digit_Multiple_of_Given_Number.md`](../../Graph_BFS_DFS_Dijkstra_DSU/learn/Find_the_Smallest_Binary_Digit_Multiple_of_Given_Number.md).
  - Coming next: [`Divisor_Game.md`](./Divisor_Game.md), [`Memoization_DP_Basics.md`](./Memoization_DP_Basics.md), [`Implement_Rand10_Using_Rand7.md`](./Implement_Rand10_Using_Rand7.md).
