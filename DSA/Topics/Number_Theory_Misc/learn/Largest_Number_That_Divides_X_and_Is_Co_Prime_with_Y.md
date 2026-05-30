# Largest Number That Divides X and Is Co-Prime with Y — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Largest_Number_That_Divides_X_and_Is_Co_Prime_with_Y.md`](../Largest_Number_That_Divides_X_and_Is_Co_Prime_with_Y.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://www.geeksforgeeks.org/dsa/largest-number-divides-x-co-prime-y/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/dsa/largest-number-divides-x-co-prime-y/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. **The lesson: REPEATEDLY divide X by gcd(X, Y) until coprime. One gcd doesn't suffice — repeat until gcd hits 1. Each iteration peels off another power of a shared prime.**

**Map of this file (7 sections):**

1. Read the problem
2. The coprime-reduction idea
3. Why a SINGLE gcd doesn't suffice
4. Code
5. Trace it
6. Common pitfalls
7. The shape — iterated GCD reduction

---

## 1. Read the problem

Given X, Y positive. Return the LARGEST D such that:
- D divides X, AND
- gcd(D, Y) = 1.

**Examples:**

- X=15, Y=3 → divisors of 15: {1, 3, 5, 15}. Coprime with 3: {1, 5}. Largest: **5**.
- X=12, Y=5 → {1,2,3,4,6,12} all coprime with 5. Largest: **12**.
- X=100, Y=10 → 100 = 2²·5². Y=10 = 2·5 shares 2 AND 5. Largest coprime divisor: **1**.

---

## 2. The coprime-reduction idea

> **Mini-refresher: strip shared prime factors from X.**
>
> gcd(D, Y) = 1 means D and Y share NO prime factors. We want the LARGEST divisor of X with this property.
>
> Start with D = X. While gcd(D, Y) > 1, divide D by gcd(D, Y). This removes one "layer" of shared factors. Eventually gcd hits 1 → D is coprime with Y.

---

## 3. Why a SINGLE gcd doesn't suffice

Naively: D = X / gcd(X, Y). But this can leave shared factors!

Example: X=100, Y=10. gcd = 10. X/gcd = 10. But 10 still shares 2 and 5 with Y.

The fix: REPEAT the division until gcd = 1.

In the X=100, Y=10 example: 100 → 10 → 1 (3 iterations). After 3 divisions, fully coprime.

---

## 4. Code

**C++:**

```cpp
int largestCoprimeDivisor(int X, int Y) {
    int D = X;
    while (true) {
        int g = __gcd(D, Y);
        if (g == 1) break;
        D /= g;
    }
    return D;
}
```

**Python:**

```python
import math
def largestCoprimeDivisor(X, Y):
    D = X
    while True:
        g = math.gcd(D, Y)
        if g == 1:
            break
        D //= g
    return D
```

Complexity: **O(log² X)** time (Euclidean gcd is O(log min)), **O(1)** space.

---

## 5. Trace it

**X=15, Y=3:**
- D=15. gcd(15, 3)=3. D=5.
- gcd(5, 3)=1. Stop.
- Return **5**.  ✓

**X=100, Y=10:**
- D=100. gcd=10. D=10.
- D=10. gcd=10. D=1.
- gcd(1, 10)=1. Stop.
- Return **1**.  ✓

**X=200, Y=6:**
- D=200, gcd=2, D=100.
- D=100, gcd=2, D=50.
- D=50, gcd=2, D=25.
- D=25, gcd=1. Stop.
- Return **25**. (25 divides 200; gcd(25, 6)=1.)  ✓

---

## 6. Common pitfalls

1. **Single division only.** Misses cases where X has higher powers of a shared prime than Y. The loop is essential.
2. **Forgetting to break when gcd == 1.** Infinite loop dividing by 1.
3. **Confusion: "coprime with Y" vs "coprime with X/Y."** We want D coprime with the ORIGINAL Y, not anything else.
4. **Negative or zero X.** Problem typically guarantees positives — handle edge cases if not.
5. **Using prime factorization explicitly.** Works but more code. Iterated gcd is cleaner.

---

## 7. The shape — iterated GCD reduction

The pattern: **remove all shared prime structure between two numbers via iterated gcd.**

| Goal | Approach |
|---|---|
| **This problem** | iterate D /= gcd(D, Y) until coprime |
| Find Y-smooth part of X | converges via iterated gcd |
| Coprime divisors enumeration | combinations of non-Y primes in X |
| Greatest divisor sharing nothing with Y | this problem |
| Find "Y-free part" of X | same idea, naming convention |

**Pattern to internalize:**

> "To strip ALL shared prime structure between X and Y: repeatedly divide X by gcd(X, Y) until the gcd becomes 1. Each iteration peels off another layer."

---

> **Self-check — the question to ask next time.**
>
> When you need the largest divisor of X coprime with Y:
>
> > **"D = X. Loop: g = gcd(D, Y). If g==1 break; else D /= g. Return D."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Largest_Number_That_Divides_X_and_Is_Co_Prime_with_Y.md`](../Largest_Number_That_Divides_X_and_Is_Co_Prime_with_Y.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Largest_Multiple_of_Three.md`](./Largest_Multiple_of_Three.md), [`Find_GCD_of_Array.md`](../../Math/learn/Find_GCD_of_Array.md).
  - Coming next: [`Pow_x_n.md`](./Pow_x_n.md), [`Ugly_Number.md`](./Ugly_Number.md).
