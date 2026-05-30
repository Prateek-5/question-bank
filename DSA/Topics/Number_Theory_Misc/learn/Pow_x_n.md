# Pow(x, n) — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Pow_x_n.md`](../Pow_x_n.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/powx-n/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/powx-n/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: BINARY EXPONENTIATION. Compute x^n in O(log n) by squaring x and consuming n's bits. For n's binary expansion, multiply ans by x when the current bit is 1; square x for the next bit. Handle negative n with reciprocation and `long long` to avoid `-INT_MIN` overflow.**

**Map of this file (9 sections):**

1. Read the problem
2. Why naive O(n) is wasteful
3. The squaring trick — O(log n)
4. Recursive vs iterative
5. Handle negative n
6. Code
7. Trace it
8. Common pitfalls
9. The shape — fast exponentiation

---

## 1. Read the problem

Implement `pow(x, n)` — return x raised to the integer power n. Support negative n.

**Examples:** pow(2.0, 10) = 1024.0. pow(2.0, -2) = 0.25. pow(2.0, 0) = 1.0.

---

## 2. Why naive O(n) is wasteful

Naive: multiply x by itself n times. O(n). For n = 2 billion, too slow.

There must be a better way that uses the STRUCTURE of n.

---

## 3. The squaring trick — O(log n)

> **Mini-refresher: x^n via halving the exponent.**
>
> Observation: `x^n = (x²)^(n/2)` when n is even. `x^n = x · (x²)^((n-1)/2)` when n is odd.
>
> Each step halves n while squaring x. After log₂(n) steps, n = 0 and we're done.
>
> O(log n) multiplications — far better than O(n).

---

## 4. Recursive vs iterative

**Recursive:**
```
pow(x, n):
    if n == 0: return 1
    if n even: return pow(x*x, n/2)
    else:      return x * pow(x*x, n/2)
```

**Iterative (cleaner, O(1) space):**
```
ans = 1
while n > 0:
    if n is odd: ans *= x
    x *= x
    n /= 2
return ans
```

The iterative version reads n's binary representation right-to-left. Each "1" bit contributes the current `x` (which is `x^(2^bit_pos)`) to `ans`.

---

## 5. Handle negative n

If n < 0, compute `x^(-n)` and return its reciprocal: `1 / pow(x, -n)`.

> **Mini-refresher: `-INT_MIN` overflows.**
>
> `INT_MIN = -2^31`. Naively `-INT_MIN = 2^31` doesn't fit in a signed int. Promote to `long long` BEFORE negating:
>
> ```
> long long N = n;
> if (N < 0) { x = 1 / x; N = -N; }
> ```

---

## 6. Code

**C++:**

```cpp
double myPow(double x, int n) {
    long long N = n;
    if (N < 0) { x = 1 / x; N = -N; }

    double ans = 1.0;
    while (N > 0) {
        if (N & 1) ans *= x;
        x *= x;
        N >>= 1;
    }
    return ans;
}
```

**Python:**

```python
def myPow(x, n):
    if n < 0:
        x = 1 / x
        n = -n
    ans = 1.0
    while n > 0:
        if n & 1:
            ans *= x
        x *= x
        n >>= 1
    return ans
```

Complexity: **O(log n)** time, **O(1)** space.

---

## 7. Trace it

pow(2, 10) → N = 10 = `1010` binary.

```
N=10 (1010): bit 0 = 0. skip. x = 4. N = 5.
N=5  (101):  bit 0 = 1. ans *= x = 4. x = 16. N = 2.
N=2  (10):   bit 0 = 0. skip. x = 256. N = 1.
N=1  (1):    bit 0 = 1. ans *= x = 4·256 = 1024. x = 65536. N = 0.

Return 1024.  ✓
```

The bits of 10 that are 1 contribute x^2 and x^8 to ans: 4 · 256 = 1024 = 2^10.

---

## 8. Common pitfalls

1. **Naive O(n) loop.** TLE for large n. Use binary exponentiation.
2. **`-INT_MIN` overflow.** Cast n to `long long` before negating.
3. **Recursion depth.** For very large n, recursive may hit stack limits — prefer iterative.
4. **Floating-point precision.** Accumulated errors for large n. Often acceptable; if not, use careful numeric techniques.
5. **`n & 1` vs `n % 2 == 1`.** Both work. `&` is slightly faster.
6. **`n /= 2` vs `n >>= 1` for unsigned.** Equivalent for positive n. For signed negative n, behavior may differ — but we ensure n > 0 first.

---

## 9. The shape — fast exponentiation

The pattern: **for any ASSOCIATIVE binary operation, n applications can be done in O(log n) via doubling.**

| Operation | "Squaring" step |
|---|---|
| **This problem** | multiply (double the base) |
| Modular exponentiation | x = (x · x) mod m |
| Matrix exponentiation | M = M · M (matrix multiply) |
| Repeated function f^n(x) | f = f ∘ f (composition) |
| Polynomial / formal-series power | poly·poly |
| Bigint exponentiation | bigint·bigint |

**Pattern to internalize:**

> "n applications of an associative op → BINARY EXPONENTIATION. Square the operator, consume n's bits. O(log n). Works for multiplication, matrices, function composition, modular arithmetic."

---

> **Self-check — the question to ask next time.**
>
> When you need to apply something n times where n is large:
>
> > **"Binary exponentiation. ans = identity. Loop: if n & 1, fold x into ans. x = x ∘ x. n >>= 1. O(log n)."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Pow_x_n.md`](../Pow_x_n.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Largest_Number_That_Divides_X_and_Is_Co_Prime_with_Y.md`](./Largest_Number_That_Divides_X_and_Is_Co_Prime_with_Y.md), [`Find_GCD_of_Array.md`](../../Math/learn/Find_GCD_of_Array.md).
  - Coming next: [`Ugly_Number.md`](./Ugly_Number.md).
