# Find the Pivot Integer

**Problem Link:**
<a href="https://leetcode.com/problems/find-the-pivot-integer/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/find-the-pivot-integer/</a>

**Topic:**
Math

----------------------------------------

## Step 1: Understand the Definition

Given a positive integer `n`, find an integer `x` (with `1 ≤ x ≤ n`) such that:

- Sum of integers from 1 to x == Sum of integers from x to n.

Return x if it exists, else -1.

Example: n = 8.

Try x = 6. Sum(1..6) = 21. Sum(6..8) = 6+7+8 = 21. ✓ Return 6.

Example: n = 1. Sum(1..1) = 1. Sum(1..1) = 1. ✓ Return 1.

Example: n = 4. Sum(1..x) == Sum(x..4) for some x?
- x=1: 1 vs 1+2+3+4=10. No.
- x=2: 1+2=3 vs 2+3+4=9. No.
- x=3: 1+2+3=6 vs 3+4=7. No.
- x=4: 10 vs 4. No.
Return -1.

----------------------------------------

## Step 2: Brute-Force Linear Search

For each x from 1 to n, compute both sums and compare.

```
for x in 1..n:
    left = sum(1..x) = x * (x + 1) / 2
    right = sum(x..n) = n * (n + 1) / 2 - (x - 1) * x / 2
    if left == right: return x
return -1
```

O(n) with constant-time sum formulas (arithmetic series). Good enough.

But there's a neat closed-form: we can derive x directly.

----------------------------------------

## Step 3: Deriving the Closed Form

Set the sums equal:

```
x(x+1)/2 = n(n+1)/2 - (x-1)x/2 + x
```

Wait, let me be careful. Sum(1..x) = x(x+1)/2. Sum(x..n) = Sum(1..n) - Sum(1..x-1) = n(n+1)/2 - (x-1)x/2.

Setting Sum(1..x) == Sum(x..n):
```
x(x+1)/2 = n(n+1)/2 - (x-1)x/2
```

Multiply both sides by 2:
```
x(x+1) = n(n+1) - (x-1)x
x(x+1) + (x-1)x = n(n+1)
x[(x+1) + (x-1)] = n(n+1)
x · 2x = n(n+1)
2x² = n(n+1)
x² = n(n+1)/2
x = sqrt(n(n+1)/2)
```

So the pivot exists iff n(n+1)/2 is a **perfect square**. If yes, x is its square root.

Example: n = 8. n(n+1)/2 = 36. sqrt(36) = 6. Integer ✓. Return 6.

n = 4. n(n+1)/2 = 10. sqrt(10) ≈ 3.16. Not integer. Return -1.

n = 1. 1·2/2 = 1. sqrt(1) = 1. Return 1.

----------------------------------------

## Step 4: O(1) Solution

```
def pivotInteger(n):
    S = n * (n + 1) // 2
    x = int(sqrt(S))
    if x * x == S: return x
    return -1
```

Compute the total sum, take integer square root, verify it's exact.

Be careful with floating-point sqrt for large n: rounding could give x or x ± 1. Use `round()` and check, or use integer sqrt.

----------------------------------------

## Step 5: Trace

n = 8: S = 36. sqrt(36) = 6.0. 6 × 6 = 36. ✓ Return 6.

n = 4: S = 10. sqrt(10) ≈ 3.162. int(3.162) = 3. 3 × 3 = 9 ≠ 10. Return -1.

n = 1: S = 1. sqrt(1) = 1. 1 × 1 = 1. Return 1.

n = 49: S = 49·50/2 = 1225. sqrt(1225) = 35. 35² = 1225. Return 35.

Let me verify: Sum(1..35) = 35·36/2 = 630. Sum(35..49) = 630 (since Sum(1..49) = 1225, and 1225 - 629 = 596... wait something's off). 

Actually Sum(1..49) = 1225. Sum(1..34) = 34·35/2 = 595. Sum(35..49) = 1225 - 595 = 630. ✓ And Sum(1..35) = 630. ✓

n = 49, pivot = 35.

----------------------------------------

## Step 6: Name It

**Closed-form solution via equation manipulation.** The problem's setup is algorithmic ("find x such that..."), but algebra collapses it to O(1).

The trick: equate the two sums, use arithmetic-series formulas, solve for x.

Related:
- Perfect square identification.
- Arithmetic series manipulation.
- Number Theory problems that reduce to "is N a perfect square?"

----------------------------------------

## Step 7: Complexity

Brute force: O(n).
Closed form: **O(1)** (ignoring sqrt cost).
Space: O(1).

----------------------------------------

## Step 8: C++ Implementation

**Closed form:**

```cpp
int pivotInteger(int n) {
    int total = n * (n + 1) / 2;
    int x = (int)sqrt(total);
    // Check nearby candidates to handle floating-point imprecision
    for (int candidate : {x - 1, x, x + 1}) {
        if (candidate > 0 && candidate * candidate == total) return candidate;
    }
    return -1;
}
```

The `{x - 1, x, x + 1}` check guards against `sqrt` rounding. For small n, `sqrt` is accurate; for larger n, it's good practice.

**Brute force (if preferred for simplicity):**

```cpp
int pivotInteger(int n) {
    int totalSum = n * (n + 1) / 2;
    int leftSum = 0;
    for (int x = 1; x <= n; ++x) {
        leftSum += x;
        int rightSum = totalSum - leftSum + x;   // includes x in both
        if (leftSum == rightSum) return x;
    }
    return -1;
}
```

O(n) but straightforward.

----------------------------------------

## Step 9: Follow-up Questions

- **Pivot with a different definition** (e.g., sum(1..x) == sum(x+1..n), excluding x). Derive a new equation.
- **Find all pivots (if multiple exist).** They can't exist for the same n — the equation has at most one positive solution.
- **Generalize to any arithmetic sequence, not just 1..n.** Sum formulas change; derivation analogous.
- **Why does this require n(n+1)/2 to be a perfect square?** Because x² = n(n+1)/2 must yield integer x.
- **Smallest n for which a pivot exists.** n = 1 (pivot = 1). Next n with pivot exists iff n(n+1)/2 is square. Sequence: 1, 8, 49, 288, 1681, ... (related to Pell's equation).
- **Algorithmic variant: find smallest k such that sum up to k > total/2.** Related but different; use binary search.
