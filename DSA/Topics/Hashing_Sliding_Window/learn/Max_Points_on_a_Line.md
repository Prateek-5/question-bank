# Max Points on a Line — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Max_Points_on_a_Line.md`](../Max_Points_on_a_Line.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/max-points-on-a-line/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~30 minutes. This problem teaches a critical lesson: **never use floating-point as a hashmap key.** Slopes are tempting to represent as `dy / dx` (a float), but rounding errors break equality. The fix — canonical reduced integer pairs via GCD — appears in many problems involving fractions, angles, or ratios.

**Map of this file (12 short sections):**

1. Read the problem
2. The natural brute force
3. The "pivot point" insight
4. What does it mean for two points to be on the same line through a pivot?
5. The floating-point slope trap
6. The fix — canonical (dy, dx) via GCD
7. Sign normalization
8. Handling duplicates
9. Code
10. Trace it
11. Common pitfalls
12. The shape — canonical-form hashing

---

## 1. Read the problem

You're given a list of 2D points. Find the **maximum number of points that lie on the same straight line**.

**Example 1:** `points = [[1, 1], [2, 2], [3, 3]]`. All three lie on the line `y = x`. Answer: **3**.

**Example 2:** `points = [[1, 1], [2, 2], [2, 3]]`. The first two are on `y = x`, but `(2, 3)` is not. The maximum line contains 2 points. Answer: **2**.

**Example 3:** `points = [[0, 0], [4, 5], [7, 8], [8, 9], [5, 6], [3, 4], [1, 1]]`. Many points; need to find the line with the most.

Edge cases:

- `n ≤ 1`: trivially `n` (one point is on a line; zero points is `0`).
- All points duplicate: any number of duplicates count as the same point, but they all "lie on every line." For our purposes, all `n` duplicates form a "line" of length `n`.

---

## 2. The natural brute force

A line is determined by any **two** points. For each pair of points, find the line they define, then count how many other points lie on that line. Track the max.

```python
best = 1
n = len(points)
for i in range(n):
    for j in range(i + 1, n):
        line = line_through(points[i], points[j])
        count = 2
        for k in range(n):
            if k == i or k == j: continue
            if on_line(points[k], line): count += 1
        best = max(best, count)
return best
```

- Pairs: O(n²).
- For each pair, count: O(n).
- Total: **O(n³)**.

For `n = 300` (LeetCode's constraint), that's `2.7 × 10⁷` — fast enough. But there's a cleaner O(n²) approach.

---

## 3. The "pivot point" insight

> **The pivot question:** instead of enumerating PAIRS of points, can we enumerate ONE point at a time and ask "how many other points share a line through me?"

For each candidate "pivot" point `p`, every other point determines a unique line through `p` (the line from `p` to that other point). **Two points share a line through `p` if and only if they're on the same line through `p` — which means they have the same SLOPE relative to `p`.**

So for each pivot:

1. Compute the slope from the pivot to every other point.
2. Group other points by slope.
3. The largest group + 1 (for the pivot itself) is the number of points on the most populous line through this pivot.

Take the max across all pivots.

- For each pivot (n of them):
  - For each other point (n-1 of them):
    - Compute slope: O(1).
    - Hash insert / increment: O(1) amortized.
- Total: **O(n²)**.

Better. Now the only question: **how do we represent and hash a slope?**

---

## 4. What does it mean for two points to be on the same line through a pivot?

Two points `q` and `r` are on the same line through pivot `p` iff:

```
slope(p, q) == slope(p, r)
```

where `slope(p, q) = (q.y - p.y) / (q.x - p.x)` (rise over run).

If we use this as a hashmap key, we can group points by slope and find the largest group.

**But** — there's a giant trap in representing this slope. Let me explain.

---

## 5. The floating-point slope trap

> **Mini-refresher: why floating-point comparisons are unreliable.**
>
> Floating-point numbers (`double` in C++, `float` in Python) are approximations. The value `1/3` cannot be represented exactly in binary floating-point — it's stored as `0.333333...3` truncated to ~15 decimal digits.
>
> Worse: the same MATHEMATICAL value can produce DIFFERENT floating-point representations depending on the order of operations. `2.0 / 6.0` might NOT bit-equal `1.0 / 3.0` even though they're mathematically the same.
>
> So using a float as a hashmap key is fragile: two "equal" slopes might hash to different keys due to rounding. False negatives. Hard to debug.

The classic example:

```
slope between (0, 0) and (3, 1) = 1.0 / 3.0 = 0.333...
slope between (0, 0) and (6, 2) = 2.0 / 6.0 = 0.333...
```

These should hash to the same bucket — they DO represent the same line. But in floating point, they might not be bit-identical.

Plus: **vertical lines have infinite slope** (dx = 0). `dy / 0` is undefined or `Infinity` depending on the language. Either way, ugly.

We need a representation that's both **mathematically exact** and **handles vertical lines cleanly**.

---

## 6. The fix — canonical (dy, dx) via GCD

> **Insight:** instead of representing a slope as `dy / dx` (a fraction we then divide), represent it as a REDUCED PAIR `(dy, dx)` — two integers in lowest terms.

For two points `p` and `q`:

- Compute `dx = q.x - p.x`, `dy = q.y - p.y`.
- Reduce: `g = gcd(|dx|, |dy|)`. Divide both: `dx /= g`, `dy /= g`.

Now `(dy, dx)` is the canonical "rise over run" pair, in lowest terms.

> **Mini-refresher: GCD (greatest common divisor).**
>
> `gcd(a, b)` is the largest integer that divides both `a` and `b` evenly.
>
> Examples: `gcd(12, 18) = 6`. `gcd(7, 5) = 1`. `gcd(0, 7) = 7` (any number divides 0).
>
> Standard algorithm (Euclid): `gcd(a, b) = gcd(b, a mod b)`, base case `gcd(a, 0) = a`. Built into `std::__gcd` (C++), `math.gcd` (Python), no built-in in standard JS (write Euclid's manually).

After reduction, two slopes that are mathematically equal have IDENTICAL canonical pairs:

- Points `(0, 0)` and `(3, 1)`: `dx = 3, dy = 1`. `gcd(3, 1) = 1`. Canonical: `(1, 3)`.
- Points `(0, 0)` and `(6, 2)`: `dx = 6, dy = 2`. `gcd(6, 2) = 2`. Canonical: `(1, 3)`.

Same canonical → same hashmap bucket. ✓

**Vertical lines:** `dx = 0`. After reduction: `dx = 0, dy = ±1`. Canonical: `(dy, 0)`. No division-by-zero — we just use the pair as-is.

**Horizontal lines:** `dy = 0`. Canonical: `(0, ±1)`. Same trick.

---

## 7. Sign normalization

There's one more catch. Consider two pairs of points:

- `p = (0, 0)`, `q = (3, 1)`. `dx = 3, dy = 1`. Canonical: `(1, 3)`.
- `p = (3, 1)`, `q = (0, 0)`. `dx = -3, dy = -1`. After GCD reduction: `dx = -3, dy = -1` (gcd of `|-3|=3, |-1|=1` is 1, so no reduction).

Same line, but different canonical pairs: `(1, 3)` vs `(-1, -3)`. We need to NORMALIZE the sign so equivalent slopes hash the same.

**Convention:** ensure `dx > 0`. If `dx < 0`, flip both signs: `dx = -dx; dy = -dy`. Now both canonical forms become `(1, 3)`.

**Edge case:** if `dx == 0` (vertical line), `dy` could be positive or negative. Convention: ensure `dy > 0`. Flip if needed.

Full canonicalization:

```
g = gcd(|dx|, |dy|)
dx /= g
dy /= g
if dx < 0:
    dx = -dx
    dy = -dy
elif dx == 0 and dy < 0:
    dy = -dy
```

After these steps, equivalent slopes always have identical `(dy, dx)` pairs.

---

## 8. Handling duplicates

What if two points in the input are IDENTICAL — same x, same y? Then `dx = dy = 0`. GCD reduction would divide by zero.

We need to count them separately. A "duplicate" of the pivot point is ON EVERY line through the pivot, so it adds 1 to every slope's count (effectively, it's on whatever line we're examining through the pivot).

```
duplicates = 0
for each point q != pivot p:
    if q == p:
        duplicates++
        continue
    ... canonicalize and count slope ...

# After the inner loop, the maximum line through pivot has
# (max slope count) + duplicates + 1 (the pivot itself) points.
```

---

## 9. Code

**C++:**

```cpp
int maxPoints(vector<vector<int>>& points) {
    int n = points.size();
    if (n <= 2) return n;

    int best = 1;
    for (int i = 0; i < n; i++) {
        map<pair<int, int>, int> slopeCount;
        int duplicates = 0;
        int localBest = 0;

        for (int j = 0; j < n; j++) {
            if (i == j) continue;

            int dx = points[j][0] - points[i][0];
            int dy = points[j][1] - points[i][1];

            if (dx == 0 && dy == 0) {
                duplicates++;
                continue;
            }

            // Canonicalize
            int g = __gcd(abs(dx), abs(dy));
            dx /= g;
            dy /= g;
            if (dx < 0) { dx = -dx; dy = -dy; }
            else if (dx == 0 && dy < 0) { dy = -dy; }

            slopeCount[{dx, dy}]++;
            localBest = max(localBest, slopeCount[{dx, dy}]);
        }

        best = max(best, localBest + duplicates + 1);   // +1 for pivot
    }

    return best;
}
```

**Python:**

```python
def maxPoints(points):
    from math import gcd

    n = len(points)
    if n <= 2:
        return n

    best = 1
    for i in range(n):
        slope_count = {}
        duplicates = 0
        local_best = 0

        for j in range(n):
            if i == j:
                continue

            dx = points[j][0] - points[i][0]
            dy = points[j][1] - points[i][1]

            if dx == 0 and dy == 0:
                duplicates += 1
                continue

            g = gcd(abs(dx), abs(dy))
            dx //= g
            dy //= g
            if dx < 0:
                dx, dy = -dx, -dy
            elif dx == 0 and dy < 0:
                dy = -dy

            key = (dx, dy)
            slope_count[key] = slope_count.get(key, 0) + 1
            local_best = max(local_best, slope_count[key])

        best = max(best, local_best + duplicates + 1)

    return best
```

Both O(n² log V) time (n² pivot-point comparisons, log V GCD per comparison where V is max coordinate value), O(n) space per pivot.

---

## 10. Trace it

`points = [[1, 1], [2, 2], [3, 3]]`. n = 3.

**Pivot i = 0 (point (1, 1)):**

```
slope_count = {}. duplicates = 0. local_best = 0.

j = 1 (point (2, 2)):
    dx = 1, dy = 1. Not duplicate.
    gcd(1, 1) = 1. Canonical: (1, 1) (dx=1, dy=1; both positive).
    slope_count[(1, 1)] = 1. local_best = 1.

j = 2 (point (3, 3)):
    dx = 2, dy = 2. Not duplicate.
    gcd(2, 2) = 2. Canonical: (1, 1) (dx=1, dy=1).
    slope_count[(1, 1)] = 2. local_best = 2.

best = max(best, local_best + duplicates + 1) = max(1, 2 + 0 + 1) = 3.
```

**Pivots i = 1 and i = 2:** by symmetry, also produce `best = 3`.

Final: **3**. ✓

---

**`points = [[1, 1], [2, 2], [2, 3]]`:**

**Pivot i = 0 (point (1, 1)):**

```
j = 1 (2, 2):  dx = 1, dy = 1. Canonical (1, 1). slope_count[(1, 1)] = 1.
j = 2 (2, 3):  dx = 1, dy = 2. gcd(1, 2) = 1. Canonical (1, 2). slope_count[(1, 2)] = 1.

local_best = 1. best = 1 + 0 + 1 = 2.
```

**Other pivots:** similar — best stays at 2.

Final: **2**. ✓

---

**Edge case: `points = [[0, 0], [1, -1], [1, 1], [2, 2]]`:**

**Pivot i = 0 (point (0, 0)):**

```
j = 1 (1, -1):  dx = 1, dy = -1. gcd = 1. Canonical (1, -1).
                (dx > 0, no flip needed.) slope_count[(1, -1)] = 1.

j = 2 (1, 1):   dx = 1, dy = 1. Canonical (1, 1). slope_count[(1, 1)] = 1.

j = 3 (2, 2):   dx = 2, dy = 2. gcd = 2. Canonical (1, 1). slope_count[(1, 1)] = 2.

local_best = 2. best = 2 + 0 + 1 = 3.
```

Line `y = x` has 3 points: (0,0), (1,1), (2,2). (1, -1) is on a different line.

Final: **3**.

---

## 11. Common pitfalls

1. **Using floating-point slope as the hashmap key.** Two equal slopes might not bit-equal due to rounding. False negatives. Use canonical integer pairs.

2. **Forgetting to handle `dx = 0` (vertical lines).** `dy / 0` is invalid. With canonical pairs, `(dy, 0)` is just a key — no special-case logic needed.

3. **Forgetting sign normalization.** Slopes `(1, 3)` and `(-1, -3)` represent the same line, but hash differently. Normalize so `dx >= 0` (and if `dx == 0`, `dy > 0`).

4. **Forgetting to handle duplicates (`dx = dy = 0`).** GCD of 0 and 0 is undefined (or 0). Count duplicates separately; they don't contribute to a slope group but DO add to the line count.

5. **The `+ 1` for the pivot.** The slope_count only counts OTHER points sharing a slope. The pivot itself is on the line too. Don't forget the `+ 1`.

6. **Re-computing GCD on the absolute values.** `gcd(dx, dy)` in C++ handles negative inputs correctly (returns positive). In Python, `math.gcd` handles negatives. But to be safe and explicit, use `abs()`.

7. **Comparing slopes with `==` after division-truncation.** Don't use `int dx / dy` (integer division) as a slope key — it truncates to integer ratios. Always use the canonical pair.

8. **Initial value of `best` should be at least 1.** Even for n = 1, the answer is 1 (a single point lies on infinitely many lines, but "max points on a line" is just that one point). For n = 0, return 0.

---

## 12. The shape — canonical-form hashing

The lesson generalizes beyond slopes: **whenever you want to hash a mathematical object that has multiple equivalent representations, find a UNIQUE CANONICAL FORM and hash that.**

| Problem | Object | Multiple representations | Canonical form |
|---|---|---|---|
| **This problem** | slope (line direction) | `(2, 6), (1, 3), (-1, -3), ...` | reduced (dy, dx) with sign convention |
| Group anagrams | character multiset | many orderings | sorted string or char-count tuple |
| Group palindromic permutations | string | many anagrams | sorted by character |
| Hash a directed edge | (u, v) | distinct | `(u, v)` as-is |
| Hash an undirected edge | {u, v} | (u, v) and (v, u) | `(min(u, v), max(u, v))` |
| Hash a fraction | a/b | `(2/4), (1/2), (-1/-2), ...` | reduced numerator/denominator with sign |
| Hash a 2D rotation/orientation | angle in radians | `(0, 2π, 4π, ...)` | mod 2π |
| Hash a graph node by isomorphism class | many labelings | canonical labeling (hard in general) | depends on graph structure |

**Pattern to internalize:**

> "When hashing a mathematical object: identify the EQUIVALENCE relation, pick a unique REPRESENTATIVE per equivalence class, and hash the representative. Avoid floating-point at all costs."

---

> **Self-check — the question to ask next time.**
>
> When you face a problem where you need to **group items by some mathematical property** (slope, ratio, angle, parity, equivalence under some operation), before reaching for floats, ask:
>
> > **"Can I express this property as a CANONICAL form using integers, GCD reduction, and sign normalization? Then I can use it as an exact hashmap key with no rounding issues."**
>
> If yes, you get exact equality comparison and clean handling of edge cases (vertical lines, zero-vectors, etc.).

---

## Cross-references

- **Reference card (post-mastery):** [`../Max_Points_on_a_Line.md`](../Max_Points_on_a_Line.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Valid_Anagram.md`](./Valid_Anagram.md), [`Valid_Sudoku.md`](./Valid_Sudoku.md) — earlier "hashmap as building block" problems.
  - Coming later in Math topic: Find Greatest Common Divisor of Array — GCD usage in a different context.
