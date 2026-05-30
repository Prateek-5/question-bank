# Rectangle Area — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Rectangle_Area.md`](../Rectangle_Area.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/rectangle-area/description/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/rectangle-area/description/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~10 minutes. **The lesson: INCLUSION-EXCLUSION. `Area(A ∪ B) = Area(A) + Area(B) - Area(A ∩ B)`. For axis-aligned rectangles, intersection is `max(0, min(x2) - max(x1)) × max(0, min(y2) - max(y1))`.**

**Map of this file (7 sections):**

1. Read the problem
2. Inclusion-exclusion
3. Intersection of axis-aligned rectangles
4. Code
5. Trace it
6. Common pitfalls
7. The shape — geometric inclusion-exclusion

---

## 1. Read the problem

Two axis-aligned rectangles A=(ax1, ay1, ax2, ay2) and B=(bx1, by1, bx2, by2) (bottom-left, top-right). Return the total area covered by their UNION.

**Example:** A=(0,0,2,2), B=(1,1,3,3) → each area 4, overlap area 1 → union = **7**.

---

## 2. Inclusion-exclusion

> **Mini-refresher: |A ∪ B| = |A| + |B| - |A ∩ B|.**
>
> Sum the areas, subtract the double-counted overlap.

For two sets it's three terms. For three sets it grows; for n sets, it has 2^n - 1 terms.

---

## 3. Intersection of axis-aligned rectangles

> **Mini-refresher: clamp the intersection projections.**
>
> Intersection rectangle:
> - `x_lo = max(ax1, bx1)`, `x_hi = min(ax2, bx2)`.
> - `y_lo = max(ay1, by1)`, `y_hi = min(ay2, by2)`.
>
> If `x_hi > x_lo` AND `y_hi > y_lo`: overlap = (x_hi - x_lo) × (y_hi - y_lo).
> Else: 0 (disjoint or touching at edge).
>
> Use `max(0, ...)` per dimension to handle the disjoint case cleanly.

---

## 4. Code

**C++:**

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

Complexity: **O(1)** time and space.

`long long` guards intermediate products against 32-bit overflow.

---

## 5. Trace it

A=(0,0,2,2), B=(1,1,3,3):
- areaA = 4, areaB = 4.
- overlapX = min(2,3) - max(0,1) = 1. overlapY = 1. overlap = 1.
- Union = 4 + 4 - 1 = **7**.  ✓

Disjoint A=(0,0,1,1), B=(2,2,3,3):
- overlapX = max(0, min(1,3) - max(0,2)) = max(0, -1) = 0. overlap = 0.
- Union = 1 + 1 = **2**.

Touching edge A=(0,0,2,2), B=(2,0,4,2):
- overlapX = max(0, 2 - 2) = 0. overlap = 0. Union = **8** (edge contact has 0 area).

---

## 6. Common pitfalls

1. **Forgetting `max(0, ...)`.** A negative dimension would multiply to spurious positive overlap.
2. **32-bit overflow.** Dimensions up to ~2 × 10⁴; squared ≈ 4 × 10⁸ fits in 32 bits but products of two such can exceed. Use `long long`.
3. **Confusing inclusive/exclusive bounds.** This problem uses HALF-OPEN: (x1, y1) inclusive, (x2, y2) exclusive — dimensions are `x2 - x1`. Touching at x2 = x1' is NO overlap.
4. **Trying to handle disjoint as a special case.** The `max(0, ...)` does it automatically.
5. **Computing intersection bounds wrong.** `x_lo = max(x1)`, `x_hi = min(x2)` — careful which goes where.

---

## 7. The shape — geometric inclusion-exclusion

The pattern: **for unions of geometric regions, sum areas and subtract pairwise (and triple) overlaps.**

| Problem | Use |
|---|---|
| **This problem** | 2 rectangles |
| Rectangle Overlap (boolean) | intersection > 0 ? |
| Area of 3+ rectangles | inclusion-exclusion OR sweep line |
| Counts in [L, R] divisible by primes p, q | inclusion-exclusion over prime sets |
| Probability of union of events | P(A ∪ B) = P(A) + P(B) - P(A ∩ B) |

**Pattern to internalize:**

> "Two-set union? Inclusion-exclusion: |A| + |B| - |A ∩ B|. For axis-aligned geometry, intersection is just min/max on coordinates with `max(0, ...)` clipping."

---

> **Self-check — the question to ask next time.**
>
> When asked for the union area of two rectangles:
>
> > **"areaA + areaB - overlap. Overlap = clamp(min(x2)-max(x1)) × clamp(min(y2)-max(y1))."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Rectangle_Area.md`](../Rectangle_Area.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Teemo_Attacking.md`](./Teemo_Attacking.md).
  - Coming next: [`Subsequence_of_Size_K_With_Largest_Sum.md`](./Subsequence_of_Size_K_With_Largest_Sum.md), [`Number_of_Digit_One.md`](./Number_of_Digit_One.md).
