# Maximum Absolute Value Expression — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Maximum_Absolute_Value_Expression.md`](../Maximum_Absolute_Value_Expression.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/maximum-of-absolute-value-expression/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/maximum-of-absolute-value-expression/</a>

---

## How to use this file

Paced for someone seeing the problem for the first time. Reading time: ~25 minutes. This problem teaches **sign-unpacking** — a slick algebraic trick that turns "max over all pairs of a sum-of-absolute-values" from `O(n²)` into `O(n)`. The trick reuses everywhere Manhattan distance / L1 norms appear in optimization.

**Map of this file (10 short sections):**

1. Read the problem
2. The natural first attempt (brute force)
3. Why it fails
4. The pivot — what makes absolute values "awkward"?
5. The `|x| = max(x, −x)` identity (the engine)
6. Sign unpacking — make the expression separable
7. Why 4 sign patterns, not 8
8. Code + trace
9. Common pitfalls
10. The shape — Manhattan distance problems and beyond

---

## 1. Read the problem

You're given two integer arrays `arr1` and `arr2` of the same length `n`. For any two indices `i` and `j` (where `i ≠ j` or `i = j`, it doesn't matter — the expression is 0 when `i = j`), define:

```
E(i, j) = | arr1[i] − arr1[j] |  +  | arr2[i] − arr2[j] |  +  | i − j |
```

Return the **maximum** value of `E(i, j)` over all pairs `(i, j)`.

> **Mini-refresher: absolute value `| x |`.**
>
> The absolute value of a number is its distance from zero on the number line — always non-negative.
>
> Formal definition: `|x| = x` if `x ≥ 0`, else `|x| = −x`.
>
> Examples: `|5| = 5`, `|−7| = 7`, `|0| = 0`. The minus sign just "kills the sign" — it gives you the magnitude regardless of direction.

Example: `arr1 = [1, 2, 3, 4]`, `arr2 = [−1, 4, 5, 6]`, `n = 4`.

Try `(i, j) = (3, 0)`:

```
| arr1[3] − arr1[0] | + | arr2[3] − arr2[0] | + | 3 − 0 |
= | 4 − 1 |         + | 6 − (−1) |        + | 3 − 0 |
= |  3 |            + |  7 |               + |  3 |
=    3              +     7                +    3        =  13
```

So `E(3, 0) = 13`. We'd compute this for all pairs and return the max. For this example, **13** turns out to be the maximum.

---

## 2. The natural first attempt (brute force)

The obvious code:

```cpp
int n = arr1.size();
int best = 0;
for (int i = 0; i < n; i++) {
    for (int j = 0; j < n; j++) {
        int e = abs(arr1[i] - arr1[j])
              + abs(arr2[i] - arr2[j])
              + abs(i - j);
        best = max(best, e);
    }
}
return best;
```

Two nested loops over all pairs of indices, computing `E` each time. Each `E` computation is `O(1)`, so total is `O(n²)`.

> **Mini-refresher: `abs()` and the `%` of absolute values.**
>
> Most languages have a built-in `abs(x)` that returns `|x|`. In C++ it's `<cstdlib>`'s `abs()`. In Python it's the built-in `abs()`. The behavior is identical to the mathematical definition.

---

## 3. Why it fails

For `n = 40000` (the typical constraint), `n²` is `1.6 × 10⁹`. At ~10⁸ ops/sec, that's **16 seconds**. Hard TLE.

So we need something faster than `O(n²)`. Sorting and binary search are tempting but they don't obviously help — the expression involves three different "axes" (`arr1`, `arr2`, and `i`), and sorting on one breaks the others.

The way out is **algebraic**: simplify the expression so that it stops requiring per-pair computation.

---

## 4. The pivot — what makes absolute values "awkward"?

Let me look at the simplest term in `E(i, j)`:

```
| arr1[i] − arr1[j] |
```

In a perfect world, this would equal `f(arr1[i]) − g(arr1[j])` for some functions `f, g` — then summing over `(i, j)` would split into "max over `i` of `f`" minus "min over `j` of `g`," each `O(n)`.

But it doesn't, because of the absolute value:

```
| 5 − 3 | = 2,  same as 5 − 3.
| 3 − 5 | = 2,  same as -(3 − 5).
```

The **sign flips** depending on which side is bigger. So `|arr1[i] − arr1[j]|` isn't a simple `arr1[i] − arr1[j]`; it's either `+(arr1[i] − arr1[j])` or `−(arr1[i] − arr1[j])`, whichever is positive.

**Question for us:** can we find a way to ELIMINATE the absolute values, replacing each one with a known sign, so the expression becomes a simple difference of linear functions?

That's the pivot question:

> **"What if we enumerate the possible sign combinations and turn the problem into multiple linear (no-absolute-value) sub-problems?"**

---

## 5. The `|x| = max(x, −x)` identity (the engine)

Here's the key piece of algebra. For any number `x`:

```
| x | = max( x, −x )
```

If `x ≥ 0`: `max(x, −x) = x = |x|`. ✓
If `x < 0`: `max(x, −x) = −x = |x|`. ✓

Always true. It's a one-line identity but tremendously useful.

Apply it to our first term:

```
| arr1[i] − arr1[j] | = max(  arr1[i] − arr1[j],  −(arr1[i] − arr1[j])  )
                     = max(  arr1[i] − arr1[j],  arr1[j] − arr1[i]  )
```

Apply it to all three terms in `E(i, j)`:

```
E(i, j) = max( ±(arr1[i] − arr1[j]) )
        + max( ±(arr2[i] − arr2[j]) )
        + max( ±(i − j) )
```

where each `±` represents the choice of `+` or `−` independently.

But — and this is the move you should pause and absorb — **the SUM of three maxes is at most the MAX of all sign combinations**:

```
For any fixed pair (i, j):
    E(i, j) = max over (s₁, s₂, s₃) ∈ {±1}³ of
              s₁·(arr1[i] − arr1[j]) + s₂·(arr2[i] − arr2[j]) + s₃·(i − j)
```

**Why?** Because for the *actual* signs that make each `|x|` positive (call them `s₁*, s₂*, s₃*`), the inner expression equals `E(i, j)` exactly. For any OTHER sign combination, the expression equals something `≤ E(i, j)` (because we're using `±x` instead of `|x|`, and `|x| ≥ ±x`). So taking the **max over all 8 sign combinations** recovers `E(i, j)` exactly.

> **Mini-exercise:** Convince yourself by trying it on `i = 3, j = 0` from our example. `arr1[3]−arr1[0] = 3`, `arr2[3]−arr2[0] = 7`, `3−0 = 3`. The "true" signs are all `+1`. With `(+1, +1, +1)`, the inner sum is `3 + 7 + 3 = 13`. With any other sign combo (say `(−1, +1, +1)`), you get `−3 + 7 + 3 = 7 ≤ 13`. The max over all 8 combos is 13. ✓
>
> <details>
> <summary>Show all 8 combinations for (i, j) = (3, 0)</summary>
>
> Let `a = 3, b = 7, c = 3`.
>
> ```
> (+,+,+):  a + b + c  =  3 + 7 + 3 = 13   ← matches E(3,0)
> (+,+,-):  a + b - c  =  3 + 7 - 3 =  7
> (+,-,+):  a - b + c  =  3 - 7 + 3 = -1
> (+,-,-):  a - b - c  =  3 - 7 - 3 = -7
> (-,+,+):  -a + b + c = -3 + 7 + 3 =  7
> (-,+,-):  -a + b - c = -3 + 7 - 3 =  1
> (-,-,+):  -a - b + c = -3 - 7 + 3 = -7
> (-,-,-):  -a - b - c = -3 - 7 - 3 = -13
> ```
>
> Max = 13. ✓ Matches.
>
> Notice (-,-,-) is just the negation of (+,+,+). For any fixed sign tuple `S`, the tuple `-S` produces the negation. So one of them is ≥ 0 and the other is ≤ 0; the max-positive one always "wins." This will matter in section 7 when we reduce 8 patterns to 4.
> </details>

---

## 6. Sign unpacking — make the expression separable

Here's where the magic happens. For a **fixed** sign combination `(s₁, s₂, s₃)`, expand the inner expression:

```
s₁·(arr1[i] − arr1[j]) + s₂·(arr2[i] − arr2[j]) + s₃·(i − j)

= s₁·arr1[i] − s₁·arr1[j]
+ s₂·arr2[i] − s₂·arr2[j]
+ s₃·i        − s₃·j

= ( s₁·arr1[i] + s₂·arr2[i] + s₃·i )   ←  depends only on i
- ( s₁·arr1[j] + s₂·arr2[j] + s₃·j )   ←  depends only on j

= g(i) − g(j)
```

where `g(k) = s₁·arr1[k] + s₂·arr2[k] + s₃·k`.

**This is the magic.** For a fixed sign pattern, the inner expression **separates** into `g(i) − g(j)` — a difference of the same function evaluated at two different indices.

Now we want the maximum of `g(i) − g(j)` over **all pairs** `(i, j)`. That's just:

```
max over (i, j) of [g(i) − g(j)]   =   max(g)  −  min(g)
```

because picking the largest possible `g(i)` and the smallest possible `g(j)` maximizes their difference. **No nested loops.** One pass computes both `max(g)` and `min(g)`. That's `O(n)` per sign pattern.

So the full algorithm:

```
best = 0
for each of 8 sign patterns (s₁, s₂, s₃) ∈ {±1}³:
    compute g(k) = s₁·arr1[k] + s₂·arr2[k] + s₃·k for all k
    candidate = max(g) − min(g)
    best = max(best, candidate)
return best
```

8 patterns × O(n) per pattern = **O(8n) = O(n)**. We've crushed `O(n²)` flat.

---

## 7. Why 4 sign patterns, not 8

Look at any sign pattern and its negation. For pattern `S = (s₁, s₂, s₃)` and `−S = (−s₁, −s₂, −s₃)`:

```
g_S(k)   =  s₁·arr1[k] + s₂·arr2[k] + s₃·k
g_{−S}(k) = −s₁·arr1[k] − s₂·arr2[k] − s₃·k  =  −g_S(k)
```

So `g_{−S}` is just the negation of `g_S`. Therefore:

```
max(g_S) − min(g_S)  =  max(−g_{−S}) − min(−g_{−S})
                      = (−min(g_{−S})) − (−max(g_{−S}))
                      = max(g_{−S}) − min(g_{−S})
```

**The "max − min" gap is the same for `S` and `−S`.** So we only need 4 patterns out of 8 — the other 4 give us the same gap values.

To pick the 4: **fix `s₁ = +1`**, iterate over `(s₂, s₃) ∈ {±1}²`. That's:

```
patterns = [
    (+1, +1, +1),
    (+1, +1, -1),
    (+1, -1, +1),
    (+1, -1, -1),
]
```

Halves the work. (4n instead of 8n — same complexity, half the constant.)

---

## 8. Code + trace

**C++:**

```cpp
int maxAbsValExpr(vector<int>& arr1, vector<int>& arr2) {
    int n = arr1.size();
    int best = 0;

    // (s2, s3) pairs; s1 is fixed at +1
    int patterns[4][2] = {{1, 1}, {1, -1}, {-1, 1}, {-1, -1}};

    for (auto& p : patterns) {
        int s2 = p[0], s3 = p[1];
        int hi = INT_MIN, lo = INT_MAX;
        for (int k = 0; k < n; k++) {
            int g = arr1[k] + s2 * arr2[k] + s3 * k;
            hi = max(hi, g);
            lo = min(lo, g);
        }
        best = max(best, hi - lo);
    }

    return best;
}
```

No need to store the full `g` array — track running `max`/`min` on the fly.

**Trace on `arr1 = [1, 2, 3, 4]`, `arr2 = [-1, 4, 5, 6]`:**

```
n = 4.  best = 0.

Pattern (s2, s3) = (1, 1):  g(k) = arr1[k] + arr2[k] + k
    k=0: g = 1 + (-1) + 0 = 0
    k=1: g = 2 +   4  + 1 = 7
    k=2: g = 3 +   5  + 2 = 10
    k=3: g = 4 +   6  + 3 = 13
    hi = 13, lo = 0.    candidate = 13.    best = 13.

Pattern (s2, s3) = (1, -1):  g(k) = arr1[k] + arr2[k] - k
    k=0: 1 + (-1) -  0 = 0
    k=1: 2 +   4  -  1 = 5
    k=2: 3 +   5  -  2 = 6
    k=3: 4 +   6  -  3 = 7
    hi = 7, lo = 0.    candidate = 7.    best = max(13, 7) = 13.

Pattern (s2, s3) = (-1, 1):  g(k) = arr1[k] - arr2[k] + k
    k=0: 1 - (-1) +  0 = 2
    k=1: 2 -   4  +  1 = -1
    k=2: 3 -   5  +  2 = 0
    k=3: 4 -   6  +  3 = 1
    hi = 2, lo = -1.    candidate = 3.    best = 13.

Pattern (s2, s3) = (-1, -1):  g(k) = arr1[k] - arr2[k] - k
    k=0: 1 - (-1) -  0 = 2
    k=1: 2 -   4  -  1 = -3
    k=2: 3 -   5  -  2 = -4
    k=3: 4 -   6  -  3 = -5
    hi = 2, lo = -5.    candidate = 7.    best = 13.

Return 13.  ✓
```

The winning pattern was `(+1, +1, +1)`, corresponding to `i = 3, j = 0`. In that pair, every absolute-value term had positive sign, so the "all positive" pattern produced the actual `E(3, 0) = 13`. The other patterns gave smaller candidates.

---

## 9. Common pitfalls

1. **Initializing `best = INT_MIN` or 0?** Use `0`. `E(i, j) ≥ 0` always (sum of absolute values), so `best = 0` is a valid initial lower bound and also handles the `n ≤ 1` edge case correctly.

2. **Forgetting that `g(k)` involves `k` as an integer, not the array value.** The third term `|i − j|` becomes `±i ∓ j`, so it's the **index** that contributes to `g(k)`, not anything from `arr1` or `arr2`.

3. **Trying all 8 patterns when 4 suffice.** Not wrong, just twice the constant factor. Fix `s₁ = +1`.

4. **Storing all `g` values in an array unnecessarily.** Just track running `max`/`min`. Cuts memory from `O(n)` to `O(1)` extra.

5. **Overflow on large `n` × large array values.** If `arr1[k]`, `arr2[k]`, and `n` all approach `10⁵`, then `g(k)` could be `~10⁵ + 10⁵ + 10⁵ ≈ 3 × 10⁵` — fits in `int32`. But `max(g) − min(g)` could approach `6 × 10⁵`, still fine. If constraints grow, switch to `long long`.

6. **Confusing "max over pairs of `g(i) − g(j)`" with `max(g) − max(g)` or similar.** It's `max(g) − min(g)`. Take the biggest `g` value as the `i`-side and the smallest as the `j`-side.

---

## 10. The shape — Manhattan distance problems and beyond

This trick is fundamental to several problem families.

**Manhattan distance in 2D.** Distance between points `(x₁, y₁)` and `(x₂, y₂)` is `|x₁ − x₂| + |y₁ − y₂|`. To find the max pairwise distance over `n` points, use sign-unpacking: 4 patterns become 2 (fixing the sign of the first term). For each, `max(g) − min(g)` over the points' transformed coordinates. O(n) per pattern.

**L∞ (Chebyshev) distance via rotation.** `max(|x₁ − x₂|, |y₁ − y₂|)` can be transformed into L1 distance by the **45° rotation** `(x, y) → (x + y, x − y)`. After transform, L∞ becomes L1, and you can apply sign-unpacking.

**General absolute-sum optimization.** Whenever an objective has the shape "sum of `|f_i(x) − g_i(y)|`" and the `f_i`, `g_i` are linear in their separate variables, you can sign-unpack to enumerate cases and solve each linearly.

| Where it appears | What the absolute values are |
|---|---|
| **This problem** | `|arr1[i]−arr1[j]| + |arr2[i]−arr2[j]| + |i−j|` |
| Max Manhattan distance over n points (LC #1131) | `|x_i − x_j| + |y_i − y_j| + |i − j|` (exactly this problem) |
| Max Manhattan distance over n points (no index) (LC #1029-ish) | `|x_i − x_j| + |y_i − y_j|` (2 patterns) |
| Chebyshev / L∞ distance, rotated to L1 | same as above after `(x, y) → (x+y, x−y)` |
| L1-weighted sum minimization (median property) | `sum |x − c|` minimized at `c = median` |

**Pattern to internalize:** `|x| = max(x, −x)` lets you replace `|·|` with sign choices. Once the absolute values are gone, expressions separate by variable and become single-pass scans.

---

> **Self-check — the question to ask next time.**
>
> When a problem asks for **"maximize / minimize a sum of absolute values across some pairs of indices,"** before reaching for `O(n²)`, ask:
>
> > **"Can I use `|x| = max(x, −x)` to replace each absolute value with a sign choice, enumerate the sign combinations, and inside each combination separate the expression into `g(i) − g(j)` whose max-over-pairs is `max(g) − min(g)`?"**
>
> If yes, you've turned `O(n²)` into `O(2^k · n)` where `k` is the number of absolute values — usually a small constant.

---

## Cross-references

- **Reference card (post-mastery):** [`../Maximum_Absolute_Value_Expression.md`](../Maximum_Absolute_Value_Expression.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:** [`Total_Hamming_Distance.md`](./Total_Hamming_Distance.md) — different shape, same "rearrange the algebra to kill the O(n²)" mindset.
