# Smallest Good Base

**Problem Link:**
<a href="https://leetcode.com/problems/smallest-good-base/description/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/smallest-good-base/description/</a>

**Topic:**
Searching / Binary Search

----------------------------------------

## Step 1: Define "Good Base"

For an integer `n > 1`, a base `k ≥ 2` is **good** if n's representation in base k consists **entirely of 1's** (all digits are 1, and length ≥ 2 so that k ≥ 2 meaningfully).

Given n (as a string since n can be huge), return the **smallest** good base as a string.

Example: n = 13. In base 3: 13 = 1·9 + 1·3 + 1 = "111". Good!
Smallest good base of 13 → **3**.

Example: n = 4681. In base 8: 4681 = 8³ + 8² + 8 + 1 = "1111". Good!
Smaller? Base 2: 4681 = "1001001001001" (not all 1's). So 8 is the smallest. Answer **8**.

Example: n = 1000000000000000000 — huge, need careful.

----------------------------------------

## Step 2: Mathematical Formulation

If n in base k is all 1's with `m` digits, then:

```
n = 1 + k + k² + ... + k^(m-1) = (k^m - 1) / (k - 1)
```

We want the **smallest k ≥ 2** such that this equation holds for some **m ≥ 2**.

Rewrite: for a given m (length of the representation), we solve for k:

```
k^m - 1 = n · (k - 1)
```

Not easy algebraically. But for fixed m, the function `(k^m - 1) / (k - 1)` is monotonically increasing in k (for k ≥ 2). So we can **binary search** for k.

----------------------------------------

## Step 3: Range of m

If m = 2: n = k + 1, so k = n - 1. Always works. This gives k = n - 1 as the fallback — the "boring" good base.

For m ≥ 2, smaller k corresponds to larger m. Rough bound: since n = 1 + k + ... + k^(m-1) ≥ k^(m-1), we have `k ≤ n^(1/(m-1))`. Since k ≥ 2, we get `2^(m-1) ≤ n`, i.e., `m ≤ log2(n) + 1`.

For n up to 10¹⁸, m ≤ 60.

**Strategy:** iterate m from the largest possible (~60) down to 2. For each m, binary search for the k such that `1 + k + k² + ... + k^(m-1) = n`. First valid k is the smallest — return it.

Why largest m first? Because larger m corresponds to smaller k (from the above bound). The **smallest k** comes from the **largest m** that admits a valid base.

----------------------------------------

## Step 4: Binary Search for k Given m

For fixed m ≥ 3:
- Lower bound: k = 2.
- Upper bound: k = floor(n^(1/(m-1))) + 1, or just n^(1/(m-1)) carefully.

Binary search in [2, upper]. For each candidate k, compute `(k^m - 1) / (k - 1)` and compare with n:
- If equal → found.
- If less → k too small, increase.
- If more → k too large, decrease.

Careful with overflow. For n up to 10¹⁸, k^m for m=60 and k=2 is already 2^60 ≈ 10¹⁸. Use unsigned or check for overflow.

A safer comparison: instead of computing (k^m - 1), compute `1 + k + k² + ...` iteratively, and stop early if it exceeds n.

----------------------------------------

## Step 5: Algorithm

```
n = given (as integer, possibly needs big integer in Python; in C++, use long long)

# m = 2 always works: k = n - 1
answer = n - 1

max_m = log2(n) + 1

for m from max_m down to 3:
    lo, hi = 2, n ** (1 / (m - 1))     # real-number bound
    while lo <= hi:
        k = (lo + hi) / 2
        s = 1 + k + k**2 + ... + k**(m-1)  # compute iteratively
        if s == n:
            return k   # smallest k for this m; also smallest overall since m is largest
        elif s < n:
            lo = k + 1
        else:
            hi = k - 1

return answer
```

----------------------------------------

## Step 6: Why Iterate m Largest-First?

Consider the function k(m) = smallest k such that 1 + k + ... + k^(m-1) = n.

For m = 60, k must satisfy k^59 ≈ n, so k ≈ n^(1/59) — very small (just above 1).
For m = 2, k = n - 1 — huge.

Smaller m → larger k. So the smallest possible k comes from the LARGEST m that yields a valid solution.

Iterate m from max down. First m that produces an integer k → that k is the answer.

----------------------------------------

## Step 7: Trace on n = 13

max_m = log2(13) + 1 ≈ 4.

**m = 4**: k must satisfy 1 + k + k² + k³ = 13. Try k = 2: 1 + 2 + 4 + 8 = 15. Too big. k = 1 invalid (k ≥ 2). No valid k.

**m = 3**: 1 + k + k² = 13. k = 3: 1 + 3 + 9 = 13. ✓ Return **3**.

Output: **3**. ✓

----------------------------------------

## Step 8: Trace on n = 4681

max_m ≈ log2(4681) + 1 ≈ 13.

**m = 13**: k = 2 → 2^13 - 1 = 8191. (1 + 2 + ... + 2^12) = 8191. Too big (> 4681). k = 2 is smallest allowed → no fit.

**m = 12**: k = 2 → sum = 4095. Too small. No valid k.

**m = 11, 10, ...**: similar checking (no match).

**m = 4**: 1 + k + k² + k³ = 4681. Try k = 16: 1 + 16 + 256 + 4096 = 4369. Too small. k = 17: 1 + 17 + 289 + 4913 = 5220. Too big. No fit.

**m = 5**: 1 + k + k² + k³ + k⁴ = 4681. Search for k... doesn't hit exactly.

... Continuing, at **m = 4** check k = 16 doesn't work. Eventually **m = 4** with k = 8? 1 + 8 + 64 + 512 = 585. Too small. No fit.

Wait, let me recompute. 4681 = 8³ + 8² + 8 + 1 = 512 + 64 + 8 + 1 = 585? That's wrong. Let me check: 8³ = 512. 512 + 64 = 576. 576 + 8 = 584. 584 + 1 = 585. So 4681 ≠ 8³+8²+8+1 at m=4.

Let me check m=5 with k=8: 1 + 8 + 64 + 512 + 4096 = 4681. ✓ Yes!

So at **m = 5**, k = 8 works. Iteration would find this.

Output: **8**. ✓

(I had the wrong formula earlier — fixed: m is the number of 1's in the representation.)

----------------------------------------

## Step 9: Name It

**Nested binary search over geometric-series equation.** A specific numerical-search technique for problems where:
- Outer loop iterates over a parameter (here, m).
- Inner loop binary-searches another (here, k).
- The "validity" is a precise numerical equality.

Related:
- Nth Ugly Number via binary search.
- Smallest Prime X Not in Range.
- Integer Break.

The geometric-series equation `(k^m - 1) / (k - 1) = n` is a common number-theoretic shape.

----------------------------------------

## Step 10: Complexity

- Outer loop: O(log n) values of m.
- Inner binary search: O(log(n^(1/(m-1)))) = O((log n)/(m-1)).
- Per iteration: O(m) to evaluate the sum.

Total: O((log n)² × m_avg) which for n = 10¹⁸ is ~ 60² × 30 = 10⁵. Fast.

Space: O(1).

----------------------------------------

## Step 11: C++ Implementation

```cpp
string smallestGoodBase(string nStr) {
    long long n = stoll(nStr);
    // Fallback: m = 2 always works, k = n - 1.
    long long answer = n - 1;

    int maxM = (int)(log2(n)) + 1;

    for (int m = maxM; m >= 3; --m) {
        long long lo = 2, hi = (long long)pow((double)n, 1.0 / (m - 1)) + 1;
        while (lo <= hi) {
            long long k = lo + (hi - lo) / 2;
            // Evaluate 1 + k + k^2 + ... + k^(m-1). Detect overflow / early exit.
            long long sum = 0, term = 1;
            bool overflow = false;
            for (int i = 0; i < m; ++i) {
                sum += term;
                if (i < m - 1) {
                    if (term > n / k + 1) { overflow = true; break; }
                    term *= k;
                }
                if (sum > n) { overflow = true; break; }
            }
            if (overflow || sum > n) hi = k - 1;
            else if (sum < n) lo = k + 1;
            else return to_string(k);
        }
    }
    return to_string(answer);
}
```

Critical: overflow check during the sum. For n near 10¹⁸ and m = 60, powers can explode.

----------------------------------------

## Step 12: Follow-up Questions

- **Largest good base instead of smallest.** Always n - 1 (m = 2 case). Trivial.
- **Count of good bases.** Iterate m from 2 to max_m; for each, check if a valid k exists.
- **What if n = 1?** Edge case: "1" in any base is "1" (1 digit). Problem constraint n > 1 avoids this.
- **All bases (not just good).** Different problem; just convert n to every base.
- **Why does m = 2 always work?** n = 1 + k → k = n - 1, which is ≥ 2 for n ≥ 3.
- **Geometric series closed form.** (k^m - 1)/(k - 1); the direct formula. Computing it directly risks overflow, so iteratively summing with early-exit is safer.
