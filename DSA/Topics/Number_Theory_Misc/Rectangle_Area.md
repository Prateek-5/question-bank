# Rectangle Area

**Problem Link:**
https://leetcode.com/problems/rectangle-area/description/

**Topic:**
Number Theory / Misc (geometry / inclusion-exclusion)

----------------------------------------

## Step 1: The Setup

Two axis-aligned rectangles A and B, given by their bottom-left and top-right corners:
- Rectangle A: (ax1, ay1, ax2, ay2).
- Rectangle B: (bx1, by1, bx2, by2).

Compute the **total area covered** by the union of the two rectangles.

Example:
```
A: (0, 0) to (2, 2).  area = 4.
B: (1, 1) to (3, 3).  area = 4.
Overlap: (1, 1) to (2, 2). area = 1.
Union = 4 + 4 - 1 = 7.
```

----------------------------------------

## Step 2: Inclusion-Exclusion

`Area(A ∪ B) = Area(A) + Area(B) - Area(A ∩ B)`.

- Area(A) = (ax2 - ax1) × (ay2 - ay1).
- Area(B) = (bx2 - bx1) × (by2 - by1).
- Area(A ∩ B) depends on whether the rectangles overlap, and if so by how much.

----------------------------------------

## Step 3: Computing the Intersection

The intersection is the rectangle:
- x_lo = max(ax1, bx1).
- x_hi = min(ax2, bx2).
- y_lo = max(ay1, by1).
- y_hi = min(ay2, by2).

If x_hi > x_lo AND y_hi > y_lo, the rectangles overlap and the overlap area is (x_hi - x_lo) × (y_hi - y_lo).

Otherwise (rectangles don't overlap or only touch at a boundary), intersection area is 0.

----------------------------------------

## Step 4: Algorithm

```
areaA = (ax2 - ax1) * (ay2 - ay1)
areaB = (bx2 - bx1) * (by2 - by1)

overlap_x = max(0, min(ax2, bx2) - max(ax1, bx1))
overlap_y = max(0, min(ay2, by2) - max(ay1, by1))
overlap = overlap_x * overlap_y

return areaA + areaB - overlap
```

One-liner per coordinate. O(1) time and space.

The `max(0, ...)` idiom elegantly handles the "no overlap" case: if the rectangles don't share x-range, min(ax2, bx2) - max(ax1, bx1) is negative, and max(0, ...) clamps to 0.

----------------------------------------

## Step 5: Trace

A: (0, 0, 2, 2). B: (1, 1, 3, 3).

- areaA = 2 * 2 = 4.
- areaB = 2 * 2 = 4.
- overlap_x = max(0, min(2, 3) - max(0, 1)) = max(0, 2 - 1) = 1.
- overlap_y = max(0, min(2, 3) - max(0, 1)) = max(0, 2 - 1) = 1.
- overlap = 1.
- Union = 4 + 4 - 1 = **7**. ✓

Try A: (0, 0, 1, 1). B: (2, 2, 3, 3) — no overlap.

- areaA = 1. areaB = 1.
- overlap_x = max(0, min(1, 3) - max(0, 2)) = max(0, 1 - 2) = max(0, -1) = 0.
- overlap = 0.
- Union = 2.

Correct — two disjoint unit squares have total area 2.

Try A: (0, 0, 2, 2). B: (2, 0, 4, 2) — touching edge.

- overlap_x = max(0, min(2, 4) - max(0, 2)) = max(0, 2 - 2) = 0.
- overlap = 0.
- Union = 4 + 4 - 0 = 8.

Correct: touching edge has area 0.

----------------------------------------

## Step 6: Why Inclusion-Exclusion?

For any two sets, |A ∪ B| = |A| + |B| - |A ∩ B|. Counting each element's area once means subtracting the double-counted overlap. This principle generalizes to n sets (inclusion-exclusion formula), growing quickly in complexity.

For n = 2, the formula has just three terms. Simple and clean.

----------------------------------------

## Step 7: Name It

**Inclusion-exclusion principle** for set unions — a fundamental counting / measure technique. Applications:
- Two-rectangle union area (this problem).
- Three-set union (harder: |A∪B∪C| = Σ|A| - Σ|A∩B| + |A∩B∩C|).
- Counting integers in [1, N] divisible by none of some primes.
- Probability of at least one of several events occurring.

For rectangles, the axis-aligned property makes intersection computation trivial — just max/min on coordinates.

----------------------------------------

## Step 8: Complexity

Time: **O(1)**.
Space: **O(1)**.

The problem is purely arithmetic.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int computeArea(int ax1, int ay1, int ax2, int ay2,
                int bx1, int by1, int bx2, int by2) {
    long long areaA = (long long)(ax2 - ax1) * (ay2 - ay1);
    long long areaB = (long long)(bx2 - bx1) * (by2 - by1);

    long long overlapX = max(0, min(ax2, bx2) - max(ax1, bx1));
    long long overlapY = max(0, min(ay2, by2) - max(ay1, by1));
    long long overlap = overlapX * overlapY;

    return (int)(areaA + areaB - overlap);
}
```

Use `long long` for intermediate arithmetic: coordinates can be near ±10⁴, so dimensions squared can overflow 32-bit for some inputs. Cast back at the end (problem guarantees answer fits in int).

----------------------------------------

## Step 10: Follow-up Questions

- **Three or more rectangles union.** Use sweep-line or coordinate compression; inclusion-exclusion becomes unwieldy.
- **Area of intersection only (not union).** Return just `overlap_x * overlap_y`.
- **Rotated (non-axis-aligned) rectangles.** Much harder — needs polygon intersection (Sutherland-Hodgman or shapely).
- **Perimeter instead of area.** Different problem; involves counting shared boundaries.
- **Infinite axes (unbounded rectangle).** Use signed-infinity coordinates; `max(0, ...)` still works.
- **Why max(0, ...)?** Because overlap dimensions can't be negative; no overlap means 0, not a negative area.
