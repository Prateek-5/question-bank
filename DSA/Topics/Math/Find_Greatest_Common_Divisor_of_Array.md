# Find Greatest Common Divisor of Array

**Problem Link:**
<a href="https://leetcode.com/problems/find-greatest-common-divisor-of-array/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/find-greatest-common-divisor-of-array/</a>

**Topic:**
Math

----------------------------------------

## Step 1: Problem Statement

Given an integer array `nums`, find the **greatest common divisor** (GCD) of the **smallest** and **largest** numbers in the array.

Example: `nums = [2, 5, 6, 9, 10]`.
- Smallest: 2.
- Largest: 10.
- GCD(2, 10) = 2.

Return 2.

Example: `nums = [7, 5, 6, 8, 3]`.
- Smallest: 3. Largest: 8.
- GCD(3, 8) = 1.

Return 1.

----------------------------------------

## Step 2: It's Really Two Subproblems

1. **Find min and max** in nums.
2. **Compute GCD** of two numbers.

Both are textbook. Min/max: O(n) single pass.

GCD: **Euclidean algorithm**. Recurrence: `gcd(a, b) = gcd(b, a mod b)`, base `gcd(a, 0) = a`.

```
def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a
```

O(log(min(a, b))) by known analysis of the Euclidean algorithm.

----------------------------------------

## Step 3: Combined Algorithm

```
mn = min(nums)
mx = max(nums)
return gcd(mn, mx)
```

O(n) for min/max, O(log max) for GCD. Total: **O(n + log max)**.

Short and sweet.

----------------------------------------

## Step 4: Trace Euclidean Algorithm for GCD(2, 10)

```
a=2, b=10.
  (Wait: b > a. The algorithm handles this naturally: a mod b = a if a < b, so they swap on the next step.)
  Actually: a % b = 2 % 10 = 2. a, b = 10, 2.
a=10, b=2.
  a % b = 0. a, b = 2, 0.
Loop ends.
Return 2.
```

GCD(2, 10) = 2. ✓

For GCD(3, 8):
```
a=3, b=8.
  a % b = 3. a, b = 8, 3.
a=8, b=3.
  a % b = 2. a, b = 3, 2.
a=3, b=2.
  a % b = 1. a, b = 2, 1.
a=2, b=1.
  a % b = 0. a, b = 1, 0.
Return 1.
```

GCD = 1. ✓

----------------------------------------

## Step 5: Why Euclidean Algorithm Works

Fundamental identity: **gcd(a, b) = gcd(b, a mod b)**.

Proof sketch: any common divisor d of a and b satisfies `d | (a mod b)` (since `a mod b = a - k·b` and d divides both a and b, d divides their linear combination). Conversely, any common divisor of b and (a mod b) divides a. So the set of common divisors of (a, b) equals the set of common divisors of (b, a mod b). Their max is the same.

Iterating shrinks the pair until the smaller becomes 0. At that point, the GCD is the other value.

Complexity: each step at least halves the smaller value in log-average sense. O(log(min(a, b))).

----------------------------------------

## Step 6: Name It

**Euclidean algorithm for GCD**, one of the oldest algorithms in recorded math (attributed to Euclid, ~300 BCE). Fundamental in number theory.

Related:
- Extended Euclidean Algorithm (finds integers x, y such that ax + by = gcd).
- Stein's binary GCD (faster in some contexts).
- LCM: lcm(a, b) = a * b / gcd(a, b).

Any language's standard library has gcd built-in. C++ has `std::gcd` (C++17) and `__gcd` (GNU extension).

----------------------------------------

## Step 7: Complexity

Time: **O(n + log(max(nums)))**.
Space: **O(1)**.

----------------------------------------

## Step 8: C++ Implementation

```cpp
int findGCD(vector<int>& nums) {
    int mn = *min_element(nums.begin(), nums.end());
    int mx = *max_element(nums.begin(), nums.end());
    return __gcd(mn, mx);   // GCC built-in; portable alternative: write your own
}
```

`__gcd` is a compiler extension; for portability, either use `std::gcd` (C++17) or implement:

```cpp
int gcd(int a, int b) {
    while (b) {
        a %= b;
        swap(a, b);
    }
    return a;
}
```

Both versions are O(log).

----------------------------------------

## Step 9: Follow-up Questions

- **GCD of all elements (not just min and max).** Fold with gcd: `gcd(gcd(gcd(a1, a2), a3), a4), ...`. GCD of all elements = GCD of min and max iff GCD divides everything (which it always does for min and max; but the GCD of min and max may be larger than the GCD of all).

  Wait, actually: GCD of all nums equals GCD of every pair including (min, max). But is GCD of all = GCD of (min, max)? Only if min and max's GCD divides everything else, which may not hold.

  Actually: GCD of all elements divides min and max, so it divides GCD(min, max). And GCD(min, max) may not divide other elements. So GCD of all ≤ GCD(min, max). The problem specifically asks for GCD(min, max), not GCD of all.

  To compute GCD of all: iterate `g = gcd(g, nums[i])` for all i.

- **LCM of min and max.** `lcm(a, b) = a * b / gcd(a, b)`.
- **Find a pair in nums with maximum GCD.** Harder — O(n²) naive.
- **Pairs with GCD = k.** Counting problem; number theory tricks.
- **What if the array has zeros?** GCD(0, x) = x, but min could be 0; handle carefully.
- **Stein's binary GCD.** Uses only subtractions and bit shifts; faster on certain hardware.
