# Find the Pivot Integer — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Find_the_Pivot_Integer.md`](../Find_the_Pivot_Integer.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/find-the-pivot-integer/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/find-the-pivot-integer/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~14 minutes. **An algebra-first problem.** The lesson: **set up the equation, simplify, and the loop disappears.** Closed-form solutions impress interviewers and are O(1) instead of O(n).

**Map of this file (9 short sections):**

1. Read the problem
2. The brute force
3. Setting up the equation
4. Solving for x
5. Checking integer-ness
6. Code
7. Trace it
8. Common pitfalls
9. The shape — algebra over loops

---

## 1. Read the problem

Given a positive integer `n`, find an integer `x` such that:
- `1 ≤ x ≤ n`, AND
- `1 + 2 + ... + x` (sum left half) `==` `x + (x+1) + ... + n` (sum right half).

Note that `x` is included in BOTH sums.

Return `x` if such an integer exists; else `-1`.

**Examples:**

- `n = 8`. Try `x = 6`. Left: 1+2+3+4+5+6 = 21. Right: 6+7+8 = 21. ✓ Return **6**.
- `n = 1`. Left: 1. Right: 1. ✓ Return **1**.
- `n = 4`. Test all x: 1→ 1 vs 10; 2 → 3 vs 9; 3 → 6 vs 7; 4 → 10 vs 4. None match. Return **-1**.

---

## 2. The brute force

For each candidate `x`, compute both sums and compare.

```
total = n * (n + 1) // 2     # sum 1..n
left = 0
for x in 1..n:
    left += x
    # right = x + (x+1) + ... + n = total - (1 + ... + x - 1) = total - (x - 1) * x // 2
    # Or equivalently: right = total - left + x  (since left ends at x, and right starts at x)
    right = total - left + x
    if left == right:
        return x
return -1
```

O(n). Works for n up to 10^9 only if we don't loop n times directly — and we DO. For LeetCode's small n, fine. But there's a closed form.

> **Mini-refresher: sum of 1 to n.**
>
> The arithmetic series `1 + 2 + ... + n = n(n+1)/2`. Constant time. Use it for any "sum to k" calculation.

---

## 3. Setting up the equation

Let's translate the requirement to algebra. Define:
- Left sum: `L(x) = 1 + 2 + ... + x = x(x+1)/2`.
- Right sum: `R(x) = x + (x+1) + ... + n`.

`R(x)` is `total - (1 + 2 + ... + (x-1))` = `n(n+1)/2 - (x-1)x/2`.

Setting `L(x) = R(x)`:

```
x(x+1)/2 = n(n+1)/2 - (x-1)x/2
```

Multiply both sides by 2:

```
x(x+1) = n(n+1) - (x-1)x
x(x+1) + (x-1)x = n(n+1)
x · [(x+1) + (x-1)] = n(n+1)
x · 2x = n(n+1)
2x² = n(n+1)
```

---

## 4. Solving for x

```
x² = n(n+1) / 2
x = sqrt(n(n+1) / 2)
```

So x is the **square root** of `n(n+1)/2`. **It's the answer IFF this value is a PERFECT INTEGER SQUARE.**

> **Mini-refresher: perfect square.**
>
> A non-negative integer `s` is a "perfect square" if `s = k²` for some non-negative integer `k`. Examples: 0, 1, 4, 9, 16, 25.
>
> To check: compute `k = floor(sqrt(s))`. Then `s` is a perfect square iff `k * k == s`.
>
> Caveat for large s and floating-point sqrt: rounding error may give `k - 1` instead of `k`. Verify with `k * k` and `(k+1) * (k+1)`.

---

## 5. Checking integer-ness

Compute `n(n+1)/2`. Take the integer square root. Verify it squares back to the same value.

```
S = n * (n + 1) // 2
x = isqrt(S)            # integer square root (floor)
if x * x == S: return x
return -1
```

`isqrt` exists in Python 3.8+. In C++, you may need `(int)sqrt(S)` with verification.

---

## 6. Code

**C++:**

```cpp
int pivotInteger(int n) {
    int S = n * (n + 1) / 2;
    int x = (int)sqrt((double)S);
    // Floating-point sqrt may round down; check x, x+1 (and x-1 for safety)
    for (int candidate : {x - 1, x, x + 1}) {
        if (candidate >= 1 && candidate <= n && candidate * candidate == S) {
            return candidate;
        }
    }
    return -1;
}
```

**Python:**

```python
from math import isqrt

def pivotInteger(n):
    S = n * (n + 1) // 2
    x = isqrt(S)
    if x * x == S:
        return x
    return -1
```

**JavaScript:**

```javascript
function pivotInteger(n) {
    const S = n * (n + 1) / 2;
    const x = Math.round(Math.sqrt(S));
    if (x * x === S && x >= 1 && x <= n) return x;
    return -1;
}
```

Complexity: **O(1) time, O(1) space.**

---

## 7. Trace it

**n = 8:** S = 8·9/2 = 36. sqrt(36) = 6. 6² = 36. ✓ Return 6.

**n = 4:** S = 4·5/2 = 10. sqrt(10) ≈ 3.16. isqrt = 3. 3² = 9 ≠ 10. Return -1.

**n = 1:** S = 1·2/2 = 1. sqrt(1) = 1. 1² = 1. ✓ Return 1.

**n = 49:** S = 49·50/2 = 1225. sqrt(1225) = 35. 35² = 1225. ✓ Return 35.

Verify n=49 manually: Sum(1..35) = 35·36/2 = 630. Sum(35..49) = Sum(1..49) - Sum(1..34) = 1225 - 595 = 630. ✓

---

## 8. Common pitfalls

1. **Forgetting that x is in BOTH sums.** The problem says `sum(1..x) == sum(x..n)`, where x APPEARS in both. If you misread as `sum(1..x) == sum(x+1..n)`, you'd get a different equation.

2. **Off-by-one in sum formulas.** `1 + 2 + ... + x` is `x(x+1)/2`, NOT `(x-1)x/2`.

3. **Floating-point sqrt rounding errors.** For large S, `sqrt(S)` may give `k - 0.0001`, and `(int)sqrt` truncates to `k - 1`. Check `x`, `x+1` (and `x-1` for safety).

4. **Using `int` and overflowing.** For `n` near 10^6, `n(n+1)` is near 10^12 — overflows `int`. Use `long long` in C++ for the multiplication if `n` can be large.

5. **Submitting the brute force when O(1) is available.** Works, but the closed form is the senior signal.

6. **Confusing "smallest x" with "any x."** The equation has AT MOST ONE positive solution (since x = sqrt(...) is unique), so there's no "smallest vs any" ambiguity here.

7. **Trying binary search.** Could work (search x in [1, n] for the equation), but unnecessary — algebra solved it directly.

---

## 9. The shape — algebra over loops

The pattern:

> **When a problem is described in terms of conditions on sums, products, or other arithmetic, set up the EQUATION first. Often algebra collapses it to a one-line solution.**

| Problem | Algebraic insight |
|---|---|
| **This problem** | `x² = n(n+1)/2` |
| Find the Square Root | binary search OR Newton's method |
| Sum 1 to n | `n(n+1)/2` |
| Sum of squares 1 to n | `n(n+1)(2n+1)/6` |
| Find missing number in [0, n] | sum of all minus sum given |
| Number of trailing zeroes of n! | count factors of 5 |
| Smallest Good Base | geometric series equation |
| Power of Two check | `n > 0 and (n & (n - 1)) == 0` |

**Pattern to internalize:**

> "Before writing a loop, ask: can algebra give me a closed-form equation? Often the answer is yes, and the resulting O(1) solution is both faster and shorter."

---

> **Self-check — the question to ask next time.**
>
> When you face a problem involving sums/products and a condition, ask:
>
> > **"Can I write the condition as an equation and SOLVE for the unknown algebraically?"**
>
> If yes, you've replaced a loop with arithmetic.

---

## Cross-references

- **Reference card (post-mastery):** [`../Find_the_Pivot_Integer.md`](../Find_the_Pivot_Integer.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Add_Digits.md`](./Add_Digits.md), [`Count_of_Matches_in_Tournament.md`](./Count_of_Matches_in_Tournament.md) — other closed-form solutions.
  - Coming next: [`Find_Greatest_Common_Divisor_of_Array.md`](./Find_Greatest_Common_Divisor_of_Array.md), [`Subarray_Sums_Divisible_by_K.md`](./Subarray_Sums_Divisible_by_K.md).
