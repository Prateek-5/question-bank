# Find Greatest Common Divisor of Array — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Find_Greatest_Common_Divisor_of_Array.md`](../Find_Greatest_Common_Divisor_of_Array.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/find-greatest-common-divisor-of-array/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~15 minutes. **The introduction to the Euclidean algorithm.** The lesson: **`gcd(a, b) = gcd(b, a mod b)` reduces a pair to a smaller pair in O(log min(a,b)) steps.** This algorithm (from ~300 BCE) is still the standard. Knowing it cold is essential for any number-theory problem.

**Map of this file (9 short sections):**

1. Read the problem
2. What's a GCD?
3. The Euclidean algorithm
4. Why the algorithm works
5. Combining: find min, max, then GCD
6. Code
7. Trace it
8. Common pitfalls
9. The shape — GCD as a building block

---

## 1. Read the problem

Given an integer array `nums`, find the **greatest common divisor** of the **smallest** and **largest** numbers in the array.

**Examples:**

- `nums = [2, 5, 6, 9, 10]`. Min = 2, max = 10. GCD(2, 10) = **2**.
- `nums = [7, 5, 6, 8, 3]`. Min = 3, max = 8. GCD(3, 8) = **1**.
- `nums = [3, 3]`. Min = max = 3. GCD(3, 3) = **3**.

---

## 2. What's a GCD?

> **Mini-refresher: greatest common divisor (GCD).**
>
> The **GCD** of two positive integers `a` and `b` is the LARGEST positive integer that divides both.
>
> Examples:
> - GCD(12, 8) = 4 (divisors of 12: {1,2,3,4,6,12}; divisors of 8: {1,2,4,8}; common: {1,2,4}; max = 4).
> - GCD(17, 11) = 1 (17 is prime, doesn't divide 11). When GCD = 1, the numbers are **coprime**.
> - GCD(a, 0) = a (everything divides 0; the largest is a itself).
> - GCD(a, b) is symmetric: GCD(a, b) = GCD(b, a).
>
> Used in: simplifying fractions, modular inverses, RSA, lattice algorithms, finding least common multiples (`LCM(a,b) = a*b/GCD(a,b)`).

---

## 3. The Euclidean algorithm

The key recurrence:

> **`gcd(a, b) = gcd(b, a mod b)`** for `b > 0`.
> **`gcd(a, 0) = a`** (base case).

Iterative form:

```
while b != 0:
    a, b = b, a mod b
return a
```

Each step: the second number becomes `a mod b`, which is strictly less than `b` (and is ≥ 0). The pair shrinks. Eventually `b` hits 0; the current `a` is the GCD.

**Convergence:** at most O(log(min(a, b))) iterations (Fibonacci-like worst case).

> **Mini-refresher: walk an example.**
>
> Compute GCD(48, 18):
>
> - 48, 18. `48 mod 18 = 12`. → (18, 12).
> - 18, 12. `18 mod 12 = 6`. → (12, 6).
> - 12, 6. `12 mod 6 = 0`. → (6, 0).
> - 6, 0. Loop exits. Return 6.
>
> GCD(48, 18) = 6. ✓ (Verify: 48/6=8, 18/6=3, no larger common divisor.)

---

## 4. Why the algorithm works

The math:

> **Claim:** every common divisor of `(a, b)` is ALSO a common divisor of `(b, a mod b)`, and vice versa.

Why? Write `a = q·b + r` where `r = a mod b`.

- If `d` divides both `a` and `b`, then `d` divides `r = a - q·b` (since `d | a` and `d | q·b`).
- Conversely, if `d` divides `b` and `r`, then `d` divides `a = q·b + r`.

So the SET of common divisors of (a, b) equals the SET of common divisors of (b, r). Their GREATEST elements are equal too.

Iterating: `gcd(a, b) = gcd(b, r₁) = gcd(r₁, r₂) = ... = gcd(r_k, 0) = r_k`. The final non-zero value IS the GCD.

> **Mini-refresher: why does b → 0 eventually?**
>
> Each iteration produces `r_(i+1) = r_(i-1) mod r_i`, which is strictly LESS than `r_i`. So the sequence is strictly decreasing in non-negative integers. It must hit 0 in at most `r_1` steps.
>
> In fact much faster: the Fibonacci sequence is the worst case, giving O(log_φ(min)) ≈ O(log min).

---

## 5. Combining: find min, max, then GCD

This problem has two sub-tasks:
1. Find min and max of `nums` (one O(n) scan).
2. Compute GCD of these two (O(log) via Euclidean).

```
mn = min(nums)
mx = max(nums)
return gcd(mn, mx)
```

That's the whole solution.

> **Mini-refresher: why min and max specifically?**
>
> The problem ASKS for GCD of min and max — a specific choice. It does NOT ask for GCD of all elements (which would be a different problem).
>
> Note: GCD of MIN and MAX may differ from GCD of ALL elements (the latter divides everything, including elements between min and max).

Example: `nums = [4, 6, 8]`. min=4, max=8. GCD(4, 8) = 4. But GCD of all: GCD(4,6,8) = 2. Different!

This problem wants GCD(min, max), which is 4 here.

---

## 6. Code

**C++:**

```cpp
int findGCD(vector<int>& nums) {
    int mn = *min_element(nums.begin(), nums.end());
    int mx = *max_element(nums.begin(), nums.end());
    return __gcd(mn, mx);     // GCC built-in; or std::gcd in C++17
}
```

**C++ with explicit Euclidean:**

```cpp
int gcd(int a, int b) {
    while (b != 0) {
        a %= b;
        swap(a, b);
    }
    return a;
}

int findGCD(vector<int>& nums) {
    int mn = *min_element(nums.begin(), nums.end());
    int mx = *max_element(nums.begin(), nums.end());
    return gcd(mn, mx);
}
```

**Python (uses `math.gcd`):**

```python
from math import gcd

def findGCD(nums):
    return gcd(min(nums), max(nums))
```

**JavaScript:**

```javascript
function gcd(a, b) {
    while (b !== 0) {
        [a, b] = [b, a % b];
    }
    return a;
}

function findGCD(nums) {
    const mn = Math.min(...nums);
    const mx = Math.max(...nums);
    return gcd(mn, mx);
}
```

Complexity: **O(n + log(max)) time, O(1) space.**

---

## 7. Trace it

**`nums = [2, 5, 6, 9, 10]`:**

- Min: 2. Max: 10.
- GCD(2, 10):
  - 2, 10. `2 % 10 = 2`. swap → (10, 2).
  - 10, 2. `10 % 2 = 0`. swap → (2, 0).
  - Loop exits. Return 2.

Answer: **2**. ✓

**`nums = [7, 5, 6, 8, 3]`:**

- Min: 3. Max: 8.
- GCD(3, 8):
  - 3, 8. `3 % 8 = 3`. swap → (8, 3).
  - 8, 3. `8 % 3 = 2`. swap → (3, 2).
  - 3, 2. `3 % 2 = 1`. swap → (2, 1).
  - 2, 1. `2 % 1 = 0`. swap → (1, 0).
  - Loop exits. Return 1.

Answer: **1**. ✓ (3 and 8 are coprime.)

---

## 8. Common pitfalls

1. **Computing GCD of all elements instead of min and max.** Read the problem — it specifies min and max. Different from "GCD of all."

2. **Recursive Euclidean that overflows the stack.** For large numbers, iterative is safer. (Modern Pythons and most compilers handle thousands of recursions fine, but iterative has no risk.)

3. **Not handling `b == 0` in the recursion.** Base case is `gcd(a, 0) = a`. Don't recurse on `(b, a % 0)` which is undefined.

4. **Forgetting `__gcd` is a GCC extension.** Portable choices: write your own, or use `std::gcd` (C++17).

5. **GCD with negatives.** Mathematically GCD is defined for non-negative integers. If inputs can be negative, take absolute values first.

6. **Using subtraction-based GCD.** `gcd(a, b) = gcd(a - b, b)` for a > b works but is O(max(a,b) / min(a,b)) in the worst case — exponentially slower than mod-based.

7. **Computing LCM instead.** `LCM(a, b) = a*b/GCD(a, b)`. Mind the multiplication for overflow.

8. **Not initializing min/max correctly.** Use the first element or use `min_element`/`max_element` library calls.

---

## 9. The shape — GCD as a building block

The Euclidean algorithm is one of the oldest and most useful algorithms. Where GCD appears:

| Problem | GCD usage |
|---|---|
| **This problem** | direct |
| Simplify fraction `a/b` | divide both by `gcd(a, b)` |
| Check coprimality | `gcd(a, b) == 1`? |
| Compute LCM | `a*b / gcd(a, b)` |
| GCD of array of N numbers | fold: `gcd(gcd(gcd(a,b),c),d)...` |
| Modular inverse | extended Euclidean algorithm |
| Bezout's identity (ax + by = gcd) | extended Euclidean |
| Linear Diophantine equations | solvable iff `gcd(a, b)` divides target |
| Cycle in tortoise-and-hare proof | uses gcd-like reasoning |
| Find smallest period of repetition | gcd-based |

**Pattern to internalize:**

> "Whenever you see divisibility, modular arithmetic, or proportional relationships in a problem, the Euclidean algorithm is likely your tool. Memorize the iterative version cold."

The Euclidean algorithm dates to ~300 BCE. It's older than most countries — and still the fastest GCD algorithm for general use.

---

> **Self-check — the question to ask next time.**
>
> When you face divisibility or "common factor" problems, ask:
>
> > **"Does this reduce to a GCD computation? If yes, Euclidean algorithm gives O(log) GCD."**
>
> If yes, you've got an ancient but optimal tool.

---

## Cross-references

- **Reference card (post-mastery):** [`../Find_Greatest_Common_Divisor_of_Array.md`](../Find_Greatest_Common_Divisor_of_Array.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Add_Digits.md`](./Add_Digits.md), [`Find_the_Pivot_Integer.md`](./Find_the_Pivot_Integer.md) — number-theoretic.
  - Coming next: [`Subarray_Sums_Divisible_by_K.md`](./Subarray_Sums_Divisible_by_K.md) — modular arithmetic + hashing.
