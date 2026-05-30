# Smallest Good Base — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Smallest_Good_Base.md`](../Smallest_Good_Base.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/smallest-good-base/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/smallest-good-base/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **This is binary search applied to a number-theoretic equation.** The lesson: **for each candidate "length" m, binary-search a base k satisfying a geometric-series equation.** Iterate m from largest to smallest to ensure we find the smallest k. Hardest of the binary-search topic — fair to find this tough on first read. **Read [`Capacity_To_Ship_Packages_Within_D_Days.md`](./Capacity_To_Ship_Packages_Within_D_Days.md) first.**

**Map of this file (10 short sections):**

1. Read the problem
2. The math — what "good base" means as an equation
3. Why the m = 2 case is trivial
4. The range of m and how to iterate
5. Binary search for k given m
6. Handling overflow safely
7. Code
8. Trace it
9. Common pitfalls
10. The shape — nested binary search with math

---

## 1. Read the problem

Given an integer `n` (as a STRING, since n can be up to 10^18), find the **smallest** integer `k ≥ 2` such that the representation of `n` in base `k` consists of **all 1's**. Return `k` as a string.

The representation must have at least 2 digits (so k ≥ 2 actually does work — see Section 3 for why m = 2 always works).

**Examples:**

- `n = "13"` → base 3: `13 = 1·9 + 1·3 + 1·1 = "111"`. Smallest k = **"3"**.
- `n = "4681"` → base 8: `4681 = 8^4·0 + 8^3·1 + 8^2·1 + 8·1 + 1 = "1111"`. Wait, that's only 4 digits.
  - Actually 4681 = 1 + 8 + 64 + 512 + 4096 = 4681. So in base 8, it's "11111" (five 1's). Smallest k = **"8"**.

---

## 2. The math — what "good base" means as an equation

If `n` in base `k` is `m` digits of all 1's, then:

```
n = 1 + k + k² + k³ + ... + k^(m-1)
```

This is a **geometric series** with first term 1, ratio k, and m terms. Closed form:

```
n = (k^m - 1) / (k - 1)
```

We want the smallest `k ≥ 2` such that this equation holds for SOME `m ≥ 2`.

> **Mini-refresher: geometric series.**
>
> For ratio `r ≠ 1`:
> ```
> 1 + r + r² + ... + r^(n-1) = (r^n - 1) / (r - 1)
> ```
> For our problem, r = k (the base), n = m (the number of 1's).
>
> Examples:
> - k = 2, m = 5: 1 + 2 + 4 + 8 + 16 = 31. Formula: (2^5 - 1) / (2 - 1) = 31/1 = 31. ✓
> - k = 10, m = 4: 1 + 10 + 100 + 1000 = 1111. Formula: (10^4 - 1) / 9 = 9999/9 = 1111. ✓

We need to find: for what `(k, m)` pair does this equation equal our given `n`, with `k` minimal?

---

## 3. Why the m = 2 case is trivial

If m = 2, then `n = 1 + k`, so `k = n - 1`. This always works for any `n ≥ 3`: just pick `k = n - 1`.

So the worst-case "good base" is `n - 1`. The interesting question is whether there's a SMALLER good base.

We'll compute the answer by:
- **Default to `k = n - 1`** (the always-works m = 2 solution).
- For each `m ≥ 3`, try to find a smaller `k` that gives a longer representation.

If for some `m ≥ 3` we find a valid `k`, return it. Otherwise, fall back to `n - 1`.

---

## 4. The range of m and how to iterate

From `n ≥ 1 + k + k² + ... + k^(m-1) ≥ k^(m-1)`, we get `k ≤ n^(1/(m-1))`. Since `k ≥ 2`:
```
2 ≤ n^(1/(m-1))
2^(m-1) ≤ n
m - 1 ≤ log₂(n)
m ≤ log₂(n) + 1
```

For `n` up to 10^18, `log₂(n) ≈ 60`. So `m` ranges from 2 to ~60.

**Why iterate m from largest to smallest?**

For fixed `m`, the equation `n = 1 + k + ... + k^(m-1)` has a UNIQUE k (the function is strictly increasing in k for k ≥ 2). Different m's give different k's.

Larger m → smaller k. So to find the SMALLEST k, try LARGEST m first.

```
for m from ~60 down to 3:
    use binary search to find k satisfying (k^m - 1)/(k - 1) = n
    if found: return k

return n - 1   # fallback
```

The first match (in this iteration order) is our answer.

---

## 5. Binary search for k given m

For fixed `m`, we want the smallest `k ≥ 2` such that `1 + k + k² + ... + k^(m-1) = n`.

The function `f(k) = 1 + k + ... + k^(m-1)` is STRICTLY INCREASING in k. So binary search.

Bounds:
- Lower: `k = 2`.
- Upper: `k = floor(n^(1/(m-1))) + 1` (since `k^(m-1) ≤ n` roughly).

```
lo, hi = 2, n^(1/(m-1)) + 1
while lo <= hi:
    k = (lo + hi) // 2
    s = 1 + k + k² + ... + k^(m-1)
    if s == n: return k        # found
    elif s < n: lo = k + 1
    else: hi = k - 1
```

If the loop exits without finding, no good base of length m exists; try the next m.

---

## 6. Handling overflow safely

For large n (10^18) and moderate k (say k = 2, m = 60), `k^(m-1)` is already 2^59 — comparable to n. For larger k or m, the powers can overflow 64-bit integers.

**Strategy:** compute the sum iteratively, with early termination if it exceeds n.

```
def sum_of_geometric(k, m, n):
    s, term = 0, 1
    for _ in range(m):
        s += term
        if s > n:
            return s             # overflow direction; will compare > n
        if _ < m - 1:
            if term > n // k + 1:
                return n + 1     # signal "too big"
            term *= k
    return s
```

If at any point the sum exceeds `n`, we can short-circuit — the comparison `s > n` will dictate the binary-search update.

> **Mini-refresher: avoiding integer overflow in geometric sums.**
>
> `k^m` can grow MASSIVELY. For 64-bit overflow safety:
> 1. Sum iteratively (not via closed form).
> 2. Check `term > n / k` before multiplying — if true, next term would overflow.
> 3. Track total `s`; if `s > n`, stop early.
>
> In Python, integers are arbitrary precision — no overflow. But the iterative approach is still important to avoid computing absurdly large numbers.

---

## 7. Code

**C++:**

```cpp
string smallestGoodBase(string nStr) {
    long long n = stoll(nStr);
    long long answer = n - 1;                          // m = 2 fallback

    int maxM = (int)(log2(n)) + 1;

    for (int m = maxM; m >= 3; --m) {
        long long lo = 2;
        long long hi = (long long)pow((double)n, 1.0 / (m - 1)) + 1;

        while (lo <= hi) {
            long long k = lo + (hi - lo) / 2;

            // Compute 1 + k + k^2 + ... + k^(m-1)
            long long sum = 0, term = 1;
            bool overflow = false;
            for (int i = 0; i < m; ++i) {
                sum += term;
                if (sum > n || sum < 0) { overflow = true; break; }   // detect overflow
                if (i < m - 1) {
                    if (term > n / k + 1) { overflow = true; break; }
                    term *= k;
                }
            }

            if (overflow || sum > n) hi = k - 1;
            else if (sum < n) lo = k + 1;
            else return to_string(k);
        }
    }

    return to_string(answer);
}
```

**Python:** (arbitrary-precision integers simplify this):

```python
def smallestGoodBase(n_str):
    n = int(n_str)
    answer = n - 1

    max_m = n.bit_length()                              # ~log2(n) + 1

    for m in range(max_m, 2, -1):
        # Compute upper bound for k: k^(m-1) <= n
        hi = int(n ** (1 / (m - 1))) + 1
        lo = 2

        while lo <= hi:
            k = (lo + hi) // 2
            # Sum 1 + k + k^2 + ... + k^(m-1)
            s = (k ** m - 1) // (k - 1) if k > 1 else m
            if s == n:
                return str(k)
            elif s < n:
                lo = k + 1
            else:
                hi = k - 1

    return str(answer)
```

Complexity:
- Outer loop: O(log n) values of m.
- Inner binary search: O(log(n^(1/(m-1)))) = O(log n / (m-1)).
- Per iteration: O(m) for the sum.

Total: O((log n)² × m) ≈ O((log n)³). For n = 10^18, that's about 60³ = 2 × 10^5 ops. Fast.

---

## 8. Trace it

**`n = 13`:**

max_m = log₂(13) + 1 ≈ 4.

**m = 4:** find k where 1 + k + k² + k³ = 13.
- k = 2: 1 + 2 + 4 + 8 = 15. Too big.
- k = 1: invalid (k must be ≥ 2).
- No match.

**m = 3:** find k where 1 + k + k² = 13.
- Bounds: lo = 2, hi = 13^(1/2) + 1 ≈ 4.6 → 4.
- k = 3: 1 + 3 + 9 = 13. MATCH. Return "3". ✓

**`n = 4681`:**

max_m ≈ 13.

**m = 13** through **m = 6** check (with binary search) — no match.

**m = 5:** find k where 1 + k + k² + k³ + k⁴ = 4681.
- k = 8: 1 + 8 + 64 + 512 + 4096 = 4681. MATCH. Return "8". ✓

(For m = 5, hi = 4681^(1/4) + 1 ≈ 8.2 + 1 = 9. Binary search lands quickly on k = 8.)

---

## 9. Common pitfalls

1. **Iterating m from small to large.** Wrong — you'd find the LARGEST k first (the trivial n-1 case). Iterate from large to small.

2. **Forgetting the m = 2 fallback.** If no m ≥ 3 yields a match, we must return n - 1. Initialize the answer to n - 1.

3. **Overflow in computing the sum.** For large k and m, the sum overflows 64-bit. Use iterative summation with overflow checks (C++), or Python's arbitrary-precision integers.

4. **Wrong upper bound for k.** Using `hi = n` is correct but wasteful. Using `hi = n^(1/(m-1)) + 1` is tighter and faster.

5. **Using `pow(n, 1.0/(m-1))` and trusting the floating-point result exactly.** Floats are imprecise — add a small buffer (`+ 1`) and let binary search handle the exact value.

6. **Forgetting to convert input string to integer FIRST.** For n up to 10^18, you need `long long` in C++ or arbitrary-precision in Python.

7. **Returning `k` as int when the problem wants a STRING.** Read the spec — return type is string.

8. **Confusing "good base" with "good number representation in any base."** A good base means ALL digits are 1's. NOT all digits the same; all are SPECIFICALLY 1.

---

## 10. The shape — nested binary search with math

This problem combines two ideas:
1. **Iteration over a small structural parameter (m).**
2. **Binary search on a numeric parameter (k) within each m.**

Where this generalizes:

| Problem | Outer parameter | Inner binary search |
|---|---|---|
| **This problem** | length m (≤ log₂ n) | base k |
| Kth Smallest in Multiplication Table | (no outer) | candidate value |
| Median of Two Sorted Arrays (advanced) | size of partition | actual value |
| Find Square Root | (no outer) | candidate sqrt |
| Aggressive Cows | (no outer) | distance d |

**Pattern to internalize:**

> "When the problem has a STRUCTURAL parameter with small range (length, count, exponent) and a NUMERIC parameter with large range, iterate the structural parameter outside and binary-search the numeric parameter inside."

This nested approach handles many number-theoretic puzzles.

---

> **Self-check — the question to ask next time.**
>
> When you face a numeric search with multiple parameters, ask:
>
> > **"Can I split into a small structural loop (few iterations) and a binary search over the numeric range (log iterations)?"**
>
> If yes, you've factored the problem into manageable nested searches.

---

## Cross-references

- **Reference card (post-mastery):** [`../Smallest_Good_Base.md`](../Smallest_Good_Base.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Capacity_To_Ship_Packages_Within_D_Days.md`](./Capacity_To_Ship_Packages_Within_D_Days.md), [`Magnetic_Force_Between_Two_Balls.md`](./Magnetic_Force_Between_Two_Balls.md) — earlier binary-search-on-answer problems.
  - Searching topic complete! Next topic: Math.
