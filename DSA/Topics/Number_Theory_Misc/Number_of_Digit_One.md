# Number of Digit One

**Problem Link:**
<a href="https://leetcode.com/problems/number-of-digit-one/description/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/number-of-digit-one/description/</a>

**Topic:**
Number Theory / Misc (also digit DP)

----------------------------------------

## Step 1: Define the Task

Given an integer `n ≥ 0`, count the **total number of digit `1` occurrences** in the decimal representations of all integers from 0 to n, inclusive.

Example: n = 13. Numbers 0, 1, 2, ..., 13. Count of '1's:
- 1 has one '1'.
- 10 has one '1'.
- 11 has two '1's.
- 12 has one '1'.
- 13 has one '1'.
- Others: 0. (And 2-9: zero '1's each.)

Total: 1 + 1 + 2 + 1 + 1 = **6**.

----------------------------------------

## Step 2: Brute Force — Why It Fails

Iterate i from 0 to n; for each, convert to string and count '1's. O(n log n).

For n up to 10⁹, that's 3 × 10¹⁰ operations — too slow. Need to count mathematically.

----------------------------------------

## Step 3: Count Digit-1 Contributions Position by Position

Instead of iterating over all integers, count how often digit 1 appears in each **position** (units, tens, hundreds, ...) across all numbers 1..n.

For position p (values: 1, 10, 100, ...), we count how many integers in [1, n] have a '1' at position p.

Sum over positions → total count of '1's.

This reframes the problem from O(n) (per-integer) to O(log n) (per-position).

----------------------------------------

## Step 4: How Many '1's in the Units Place?

Consider position 1 (units). In [1, n], every 10th integer has a 1 in the units place: 1, 11, 21, 31, ...

So count = `floor(n / 10)` complete cycles, each contributing one '1' at the units place, plus possibly one more if n's last digit is ≥ 1.

Slightly more precisely:
- Let `rest = n / 10` (number of complete blocks of 10).
- Remaining digit (n % 10): if it's 0, no partial contribution. If it's ≥ 1, one more.

So units-place 1 count = `rest + (1 if n % 10 >= 1 else 0)` — but we can write this more cleanly.

----------------------------------------

## Step 5: General Formula Per Position

For position `p` (power of 10), let:
- `high = n / (p * 10)` (digits higher than position p)
- `cur = (n / p) % 10` (digit at position p)
- `low = n % p` (digits lower than position p)

Number of '1's at position p = depends on `cur`:
- If `cur == 0`: `high * p`.
- If `cur == 1`: `high * p + low + 1`.
- If `cur >= 2`: `(high + 1) * p`.

Why? Think of which prefixes/suffixes yield a '1' at position p:
- **Full cycles of the prefix**: every prefix value 0, 1, ..., high-1 contributes a full block of p values (all suffixes 0..p-1) with '1' at position p. That's `high * p`.
- **The "current" prefix of value `high`**: this only contributes depending on what digits at and below position p allow.
  - cur = 0: never hits '1' at this position (we're at digit 0 currently). No contribution.
  - cur = 1: hits '1' for suffixes 0..low. That's `low + 1` numbers.
  - cur ≥ 2: we've already "passed" '1' at this position — all p suffixes contribute. That's `p` numbers.

Sum these per-position counts over all p.

----------------------------------------

## Step 6: Algorithm

```
count = 0
p = 1
while p <= n:
    high = n / (p * 10)
    cur = (n / p) % 10
    low = n % p

    if cur == 0:
        count += high * p
    elif cur == 1:
        count += high * p + low + 1
    else:
        count += (high + 1) * p

    p *= 10
return count
```

O(log n) iterations — one per decimal digit of n.

----------------------------------------

## Step 7: Trace on n = 13

- p = 1 (units):
  - high = 13 / 10 = 1. cur = (13 / 1) % 10 = 3. low = 13 % 1 = 0.
  - cur = 3 ≥ 2: add `(high + 1) * p = 2 * 1 = 2`.

- p = 10 (tens):
  - high = 13 / 100 = 0. cur = (13 / 10) % 10 = 1. low = 13 % 10 = 3.
  - cur = 1: add `high * p + low + 1 = 0 + 3 + 1 = 4`.

- p = 100: 100 > 13, stop.

Total: 2 + 4 = **6**. ✓

----------------------------------------

## Step 8: Trace on n = 100

- p = 1: high = 10, cur = 0, low = 0. cur = 0: add 10 * 1 = 10.
- p = 10: high = 1, cur = 0, low = 0. cur = 0: add 1 * 10 = 10.
- p = 100: high = 0, cur = 1, low = 0. cur = 1: add 0 * 100 + 0 + 1 = 1.
- p = 1000 > 100, stop.

Total: 10 + 10 + 1 = **21**.

Sanity check: numbers 1..100. 1's in units: 1, 11, 21, 31, ..., 91 → 10 numbers. 1's in tens: 10, 11, ..., 19 → 10 numbers. 1 at hundreds: 100 → 1 number. Grand total = 21. ✓

----------------------------------------

## Step 9: Why This Formula Works

Think of each integer in [1, n] as a (log n)-digit number with leading zeros. Each of the n numbers contributes to each digit position independently.

For position p, we count how many of the n numbers have digit 1 at this position. The formula handles three cases:
- Numbers with prefix strictly less than "high": they can have any suffix (0..p-1), so p numbers with '1' at position p in that block.
- Numbers with prefix exactly "high": constrained by cur (the digit at position p for n itself) and low (trailing digits of n).

Summing per position yields the total.

----------------------------------------

## Step 10: Name It

**Digit counting formula** — a specific technique for "count occurrences of digit d from 0 to n" problems. A cornerstone of **digit DP**.

Applications:
- Count numbers in [0, n] with a given digit property.
- Count numbers divisible by some number with digit constraints.
- Numbers at Most N Given Digit Set (another LeetCode problem using digit DP).

For more complex predicates, use generic digit DP: `f(pos, tight, ...)` recursive formulation with memoization.

----------------------------------------

## Step 11: Complexity

Time: **O(log₁₀ n)** — one iteration per decimal digit of n.
Space: **O(1)**.

Dramatic improvement over O(n log n) brute force.

----------------------------------------

## Step 12: C++ Implementation

```cpp
int countDigitOne(int n) {
    long long count = 0;
    long long p = 1;
    while (p <= n) {
        long long high = n / (p * 10);
        long long cur = (n / p) % 10;
        long long low = n % p;

        if (cur == 0)        count += high * p;
        else if (cur == 1)   count += high * p + low + 1;
        else                 count += (high + 1) * p;

        p *= 10;
    }
    return (int)count;
}
```

Use `long long` for p and count: p * 10 can overflow when p ≈ 10⁹, and total count can slightly exceed 32-bit.

----------------------------------------

## Step 13: Follow-up Questions

- **Count digit k (not just 1) from 0 to n.** Generalize the formula. For digit 0, be careful about leading zeros.
- **Count numbers with digit 1 in them (not how many times).** Different — count integers with at least one '1'. Subtract numbers with no '1'.
- **Range [L, R] instead of [0, n].** Compute f(R) - f(L - 1).
- **Sum of all digits from 0 to n.** Aggregate the formula across digits 0..9.
- **Why `high * p` for cur == 0?** High cycles complete before reaching n; each cycle of p numbers (with the prefix fixed) has exactly one number with '1' at this position — no wait, let me reconsider...

Actually, `high * p` counts contributions from complete prefix-blocks. In one such block (prefix fixed to some value < high), the digit at position p cycles through 0-9, and for each suffix (0..p-1), exactly one of those 10 cycles has '1'. So one block contributes `p` '1's. And `high` blocks contribute `high * p`. ✓

- **Variant: count numbers with exactly k '1's in their decimal.** Use digit DP with a counter of 1's seen so far.
