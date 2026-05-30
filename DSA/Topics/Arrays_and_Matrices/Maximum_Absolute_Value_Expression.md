# Maximum Absolute Value Expression

**Problem Link:**
<a href="https://leetcode.com/problems/maximum-of-absolute-value-expression/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/maximum-of-absolute-value-expression/</a>

**Topic:**
Arrays and Matrices

----------------------------------------

## Step 1: Understand the Expression

Given two integer arrays `arr1` and `arr2` of equal length n, for any pair of indices (i, j) define:

```
E(i, j) = |arr1[i] - arr1[j]| + |arr2[i] - arr2[j]| + |i - j|
```

Return the maximum of E(i, j) over all pairs.

Example: `arr1 = [1, 2, 3, 4]`, `arr2 = [-1, 4, 5, 6]`. Try (i, j) = (0, 3):
- |1 - 4| + |-1 - 6| + |0 - 3| = 3 + 7 + 3 = 13.

Brute-forcing every pair: O(n²). With n up to 40000, that's 1.6 × 10^9 — too slow.

----------------------------------------

## Step 2: The Absolute Value Obstruction

Absolute values are awkward algebraically. `|x - y|` doesn't decompose cleanly: we can't factor it into "something about x minus something about y" because the sign flips.

If we could get rid of absolute values, then E(i, j) = f(i) - f(j), and the max becomes `max(f) - min(f)` — computable in O(n).

Can we eliminate them?

----------------------------------------

## Step 3: The Sign-Unpacking Trick

Here's a beautiful observation:

```
|x| = max(x, -x)
```

So `|x - y| = max(x - y, y - x)`. Applied to all three terms:

```
E(i, j) = max over signs (s1, s2, s3) ∈ {+1, -1}³ of
         s1·(arr1[i] - arr1[j]) + s2·(arr2[i] - arr2[j]) + s3·(i - j)
```

Why? Because for the true optimal (i, j), one specific sign pattern produces the actual absolute-value sum, and every other pattern produces something ≤ it (since `|x| ≥ ±x`). Taking the max over all patterns recovers the exact answer.

Now rearrange each pattern:

```
s1·arr1[i] + s2·arr2[i] + s3·i − (s1·arr1[j] + s2·arr2[j] + s3·j)
       = g_signs(i) − g_signs(j)
```

where `g_signs(k) = s1·arr1[k] + s2·arr2[k] + s3·k`.

For each fixed sign pattern, max over (i, j) of `g(i) - g(j)` = `max(g) - min(g)`. We've eliminated the inner O(n) search.

----------------------------------------

## Step 4: How Many Sign Patterns?

Three signs, each ±1: 2³ = 8 combinations. But note that `g_signs(i) - g_signs(j)` with signs `(+, +, +)` equals `-(g with signs (-,-,-))` for the pair (j, i). So flipping all three signs gives the same max-minus-min value (just swapping i and j). We can fix s1 = +1 and iterate over s2, s3 — **4 patterns**.

```
patterns = [
    (+1, +1, +1),
    (+1, +1, -1),
    (+1, -1, +1),
    (+1, -1, -1),
]
```

For each, compute `g(k)` for all k, take max - min. Overall answer is the max across patterns.

----------------------------------------

## Step 5: Algorithm

```
best = 0
for (s1, s2, s3) in 4 patterns:
    values = [s1*arr1[k] + s2*arr2[k] + s3*k for k in 0..n-1]
    best = max(best, max(values) - min(values))
return best
```

4 patterns × O(n) per pattern = **O(n)** total. Huge win over O(n²).

----------------------------------------

## Step 6: Trace

`arr1 = [1, 2, 3, 4]`, `arr2 = [-1, 4, 5, 6]`. n = 4.

**Pattern (+, +, +):** g(k) = arr1[k] + arr2[k] + k.
- g = [1+(-1)+0, 2+4+1, 3+5+2, 4+6+3] = [0, 7, 10, 13].
- max - min = 13 - 0 = 13.

**Pattern (+, +, -):** g(k) = arr1[k] + arr2[k] - k.
- g = [0, 5, 6, 7]. max - min = 7.

**Pattern (+, -, +):** g(k) = arr1[k] - arr2[k] + k.
- g = [2, -1, 0, 1]. max - min = 3.

**Pattern (+, -, -):** g(k) = arr1[k] - arr2[k] - k.
- g = [2, -3, -4, -5]. max - min = 7.

Best across patterns: **13**. ✓

The winning pattern was (+, +, +), corresponding to pair (i=3, j=0) where arr1[3] > arr1[0], arr2[3] > arr2[0], and i > j — all positive signs in the unpacking.

----------------------------------------

## Step 7: Why This Works, Intuitively

Each absolute-value term hides one of two cases (positive or negative difference). Three terms have 2³ = 8 combined cases. Instead of guessing which case applies to the optimal pair, we **try all 8 and take the max** — one of them will match the true answer, and every other will under-count (never over-count, because `|x| ≥ ±x`).

The magic is that for a *fixed* sign pattern, the expression becomes separable: a function of i minus the same function of j. Max-minus-min is an O(n) scan.

The technique generalizes: any sum of absolute values over pairs, where signs can be separated per index, becomes tractable by sign enumeration.

----------------------------------------

## Step 8: Name It

**Sign-unpacking of absolute values** (also called "Manhattan distance linearization"). Related pattern: converting L1 distance in the plane into L∞ via the 45° rotation trick `(x+y, x-y)`. Same underlying idea — eliminate absolute values by considering sign combinations.

Use it for:
- Maximum Manhattan distance between points.
- Max absolute difference expressions involving multiple arrays.
- Problems with `|...|+|...|` patterns where indices can be separated.

----------------------------------------

## Step 9: Complexity

Time: **O(n)**. 4 patterns × O(n) each.
Space: **O(1)** extra (just running max/min per pattern, no need to materialize the values array).

----------------------------------------

## Step 10: C++ Implementation

```cpp
int maxAbsValExpr(vector<int>& arr1, vector<int>& arr2) {
    int n = arr1.size();
    int best = 0;

    int patterns[4][2] = {{1, 1}, {1, -1}, {-1, 1}, {-1, -1}};
    // s1 fixed at +1; iterate over s2, s3

    for (auto& p : patterns) {
        int s2 = p[0], s3 = p[1];
        int hi = INT_MIN, lo = INT_MAX;
        for (int k = 0; k < n; ++k) {
            int g = arr1[k] + s2 * arr2[k] + s3 * k;
            hi = max(hi, g);
            lo = min(lo, g);
        }
        best = max(best, hi - lo);
    }
    return best;
}
```

No need to store the array — one pass per pattern computing running max/min.

----------------------------------------

## Step 11: Follow-up Questions

- **Four absolute terms.** 2⁴ = 16 patterns, halved to 8 by sign-flip symmetry. Still O(n).
- **Manhattan distance in 2D between points (no index).** Just two terms: 4 patterns, halved to 2.
- **Minimum instead of maximum.** Minimum of |x1-x2|+|y1-y2|+|i-j| is 0 (pick i = j). Not interesting.
- **Why can we fix s1 = +1?** Flipping all three signs swaps the role of i and j, giving the same max-minus-min. So half the patterns are redundant.
- **Weighted absolute expressions like `a·|x| + b·|y|`.** Signs multiply in; same technique applies.
- **Does this extend to L∞ distance?** Yes — L∞ rotates to L1 via the (x+y, x-y) transform in 2D, reducing to this kind of problem.
