# Max Points on a Line

**Problem Link:**
https://leetcode.com/problems/max-points-on-a-line/

**Topic:**
Hashing / Sliding Window

----------------------------------------

## Step 1: Understand the Problem

Given an array of 2D points, return the **maximum number of points that lie on the same straight line**.

Example: `points = [[1, 1], [2, 2], [3, 3]]`. All three are on the line y = x. Answer: **3**.

Example: `points = [[1, 1], [2, 2], [2, 3]]`. The first two are on y = x. (2, 3) is off that line. Best line contains 2 points. Answer: **2**.

For n ≤ 2 points, the answer is trivially n.

----------------------------------------

## Step 2: How Does One Line Emerge?

Two points always determine a unique line. Three points are collinear iff they all lie on the same line, which is the line through any two of them.

So we can fix one point (a "pivot") and consider every line that passes through it. For each such line, count how many other points also lie on it. Add 1 (for the pivot itself). Track the best.

How do we identify a line through the pivot? By its **slope**: from the pivot to any other point, compute the slope. All points sharing the same slope with the pivot are on the same line through the pivot.

So for each pivot `p`, count how many points share each slope with `p`. The line with the most shared-slope points is the best through `p`.

Do this for every pivot; take the max.

O(n²): n pivots × n points to check per pivot.

----------------------------------------

## Step 3: The Slope Trap — Use Ratios, Not Decimals

Slope = (y2 - y1) / (x2 - x1). As a decimal, this runs into floating-point issues: e.g., `2/6` and `1/3` are the same slope mathematically, but with floats, `2.0/6.0 = 0.3333...` and `1.0/3.0 = 0.3333...` might not be bit-identical.

Also, vertical lines have infinite slope (dx = 0).

**Fix: represent slope as a reduced (dy, dx) pair.** Divide both by their GCD. Normalize sign so the representation is unique.

For two equivalent slopes:
- (2, 6) → gcd=2 → (1, 3).
- (1, 3) → gcd=1 → (1, 3).
- (-1, -3) → gcd=1 → (-1, -3) → sign flip → (1, 3).

All three produce the same canonical key. Two points share a slope iff their (dy, dx) reductions match.

----------------------------------------

## Step 4: Handle Edge Cases

**Vertical line:** dx = 0. Reduced form: (1, 0). (dy normalized to positive.)
**Horizontal line:** dy = 0. Reduced form: (0, 1).
**Same point as pivot (duplicate):** dx = dy = 0. Special case — these are "on every line through pivot," so they always count toward the current pivot's line count. Track duplicates separately.

For the canonicalization:
- Compute g = gcd(|dx|, |dy|).
- Reduce: dx /= g, dy /= g.
- If dx < 0, flip both signs (so dx is non-negative).
- If dx == 0 (vertical), ensure dy > 0.

After canonicalization, equivalent slopes have identical (dy, dx) pairs.

----------------------------------------

## Step 5: Algorithm

```
best = 1  # at minimum, 1 point "on a line"

for i in 0..n-1:
    slope_count = empty hashmap
    duplicates = 0
    local_best = 0
    
    for j in 0..n-1, j != i:
        if points[j] == points[i]:
            duplicates++
            continue
        compute (dy, dx) as canonical slope from i to j
        slope_count[(dy, dx)]++
        local_best = max(local_best, slope_count[(dy, dx)])
    
    # max points on a line through pivot = (best slope count) + duplicates + 1 (for pivot)
    best = max(best, local_best + duplicates + 1)

return best
```

For each pivot, after counting slopes, the line through pivot has at most `local_best + duplicates + 1` points. Duplicates are on every line through pivot (they coincide with it).

----------------------------------------

## Step 6: Trace on `[[1, 1], [2, 2], [3, 3]]`

No duplicates. n = 3.

**Pivot i = 0 (point (1, 1)):**
- j = 1 (point (2, 2)): dx = 1, dy = 1. gcd = 1. Canonical (1, 1). slope_count[(1,1)] = 1.
- j = 2 (point (3, 3)): dx = 2, dy = 2. gcd = 2. Canonical (1, 1). slope_count[(1,1)] = 2.

local_best = 2. Line through (1, 1) with slope (1, 1) has 2 + 0 + 1 = 3 points. Update best to 3.

**Pivot i = 1 (point (2, 2)):**
Same analysis. Also 3.

**Pivot i = 2:** 3.

Final: 3. ✓

Now try `[[1, 1], [2, 2], [2, 3]]`:

**Pivot i = 0 (point (1, 1)):**
- j = 1: (2, 2). dx=1, dy=1. Canonical (1, 1). Count = 1.
- j = 2: (2, 3). dx=1, dy=2. gcd=1. Canonical (2, 1). Count = 1.

local_best = 1. best = 1 + 0 + 1 = 2.

**Pivot i = 1, i = 2:** symmetrical, best still 2.

Final: 2. ✓

----------------------------------------

## Step 7: Why Canonical Slope Is Essential

Without it, we'd hit false negatives. Consider (1, 1), (2, 2), (3, 3), and use float slopes:
- slope(0, 1) = 1/1 = 1.0.
- slope(0, 2) = 2/2 = 1.0.

These happen to agree. But for (1, 1) and (10^9, 10^9): slope 1/1 and slope 10^9/10^9. Both 1.0 in principle, but with certain computation orders and rounding, floats can differ.

More sinister: (1, 0), (2, 0), (3, 0). All horizontal. dy/dx = 0. But a vertical line has dx = 0 → division error.

The canonical-integer approach avoids all these issues.

----------------------------------------

## Step 8: Name It

**Hashmap of canonical slopes per pivot.** The core trick:
1. "For each pivot" — fix one point at a time and look at lines through it.
2. "Canonical slope" — reduce (dy, dx) to a unique representation so equal slopes hash the same.
3. "Hashmap count" — group other points by slope; max group + duplicates + pivot = line size through pivot.

The technique generalizes to any collinearity or angle-based grouping problem.

----------------------------------------

## Step 9: Complexity

Time: O(n²) pivot-point pairs; each GCD is O(log max_coord). **O(n² log max_coord)**.
Space: O(n) for slope map per pivot (reused across pivots).

For n ≤ 300, ~10^5 ops — fast.

----------------------------------------

## Step 10: C++ Implementation

```cpp
int maxPoints(vector<vector<int>>& points) {
    int n = points.size();
    if (n <= 2) return n;

    int best = 1;
    for (int i = 0; i < n; ++i) {
        map<pair<int, int>, int> slopes;
        int duplicates = 0;
        int localBest = 0;

        for (int j = 0; j < n; ++j) {
            if (i == j) continue;

            int dx = points[j][0] - points[i][0];
            int dy = points[j][1] - points[i][1];

            if (dx == 0 && dy == 0) {
                duplicates++;
                continue;
            }

            // Canonicalize: reduce, ensure dx >= 0, then dy > 0 if dx == 0
            int g = __gcd(abs(dx), abs(dy));
            dx /= g;
            dy /= g;
            if (dx < 0) { dx = -dx; dy = -dy; }
            if (dx == 0 && dy < 0) dy = -dy;

            slopes[{dx, dy}]++;
            localBest = max(localBest, slopes[{dx, dy}]);
        }

        best = max(best, localBest + duplicates + 1);   // +1 for pivot itself
    }
    return best;
}
```

The canonicalization in four lines:
1. Compute `g = gcd(|dx|, |dy|)`.
2. Divide out.
3. If dx < 0, flip signs (ensures dx ≥ 0).
4. If dx = 0 (vertical) and dy < 0, flip dy (ensures dy > 0).

After these steps, equivalent slopes hash identically.

----------------------------------------

## Step 11: Follow-up Questions

- **3D points on a line.** Direction vectors are 3D; canonicalize a triple.
- **Minimum lines covering all points.** Different (NP-hard in general).
- **Collinearity with tolerance (points approximately on a line).** Use robust fitting (RANSAC).
- **Dynamic: points arrive over time.** Maintain slope maps per pivot; update as new points arrive.
- **Return the line itself (not just count).** Record two defining points for the winning slope.
- **Why use GCD instead of comparing slopes as fractions?** GCD reduction gives a unique canonical form; fraction comparison still has edge cases.
