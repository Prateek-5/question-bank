# Minimum Number of Bottles Visible — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Minimum_Number_of_Bottles_Visible.md`](../Minimum_Number_of_Bottles_Visible.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/minimum-number-of-bottles-visible-when-standing-on-a-shelf/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/minimum-number-of-bottles-visible-when-standing-on-a-shelf/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~10 minutes. **A bite-sized "running max" puzzle.** The lesson: **a bottle is visible iff its height EXCEEDS every height seen so far (from the viewing direction). Maintain a running max, increment counter on new highs.** Same pattern: count "record-high" days, peaks-as-seen-from-side, monotonic-stack precursor.

**Map of this file (8 short sections):**

1. Read the problem
2. The visibility rule
3. The running-max approach
4. Code
5. Trace it
6. Common pitfalls
7. Variants (view from both sides, ties)
8. The shape — running summary

---

## 1. Read the problem

Bottles stand in a row on a shelf. Each has a known **height**. You view from the LEFT.

A bottle is **VISIBLE** iff no taller bottle stands between it and the viewer (i.e., to its LEFT).

Return the count of visible bottles.

**Example:** heights = `[3, 1, 4, 2, 5]`.

- Bottle 0 (h=3): nothing to its left. VISIBLE.
- Bottle 1 (h=1): 3 is in front. HIDDEN.
- Bottle 2 (h=4): 3 < 4 → 3 doesn't block. 1 < 4 → 1 doesn't block. VISIBLE.
- Bottle 3 (h=2): 4 in front blocks. HIDDEN.
- Bottle 4 (h=5): everything in front is shorter. VISIBLE.

Visible count: **3**.

---

## 2. The visibility rule

> **Mini-refresher: when is a bottle visible from the left?**
>
> Bottle at index `i` is visible from the left iff:
>
> > `heights[i] > max(heights[0], heights[1], ..., heights[i-1])`
>
> i.e., it's STRICTLY TALLER than every bottle to its left.
>
> Equivalently: it's a "NEW MAXIMUM" as we scan left to right.

The first bottle (index 0) is always visible (the max-of-empty is `-∞`, so any positive height exceeds it).

---

## 3. The running-max approach

Scan left to right. Maintain a `max_so_far`. Each bottle: compare with max_so_far. If taller, it's a new record — increment count, update max.

```
max_so_far = -infinity
visible = 0
for h in heights:
    if h > max_so_far:
        visible += 1
        max_so_far = h
return visible
```

O(n) time, O(1) space.

---

## 4. Code

**C++:**

```cpp
int minVisibleBottles(vector<int>& heights) {
    int maxSoFar = INT_MIN, visible = 0;
    for (int h : heights) {
        if (h > maxSoFar) {
            visible++;
            maxSoFar = h;
        }
    }
    return visible;
}
```

**Python:**

```python
def minVisibleBottles(heights):
    max_so_far = float('-inf')
    visible = 0
    for h in heights:
        if h > max_so_far:
            visible += 1
            max_so_far = h
    return visible
```

**JavaScript:**

```javascript
function minVisibleBottles(heights) {
    let maxSoFar = -Infinity, visible = 0;
    for (const h of heights) {
        if (h > maxSoFar) {
            visible++;
            maxSoFar = h;
        }
    }
    return visible;
}
```

Complexity: **O(n) time, O(1) space.**

---

## 5. Trace it

**`heights = [3, 1, 4, 2, 5]`:**

```
max=-∞, visible=0.

h=3: 3 > -∞ → visible=1, max=3.
h=1: 1 > 3? NO.
h=4: 4 > 3 → visible=2, max=4.
h=2: 2 > 4? NO.
h=5: 5 > 4 → visible=3, max=5.

Return 3.  ✓
```

**`heights = [1, 2, 3, 4]`** (strictly increasing — everything visible):

```
h=1: visible=1, max=1.
h=2: visible=2, max=2.
h=3: visible=3, max=3.
h=4: visible=4, max=4.

Return 4.  ✓
```

**`heights = [4, 3, 2, 1]`** (strictly decreasing — only first visible):

```
h=4: visible=1, max=4.
h=3: 3 > 4? NO.
h=2: 2 > 4? NO.
h=1: 1 > 4? NO.

Return 1.  ✓
```

---

## 6. Common pitfalls

1. **Using `>=` instead of `>`.** If equal heights "tie," the rear one is BLOCKED. Use strict `>` for new visibility.

2. **Initializing `max_so_far` to 0.** Wrong for negative heights (rare for this problem but principled). Use `-infinity`.

3. **Counting the wrong thing.** This problem counts VISIBLE bottles, not hidden ones.

4. **Trying to use a stack.** Overkill — running max suffices.

5. **Confusing "view from the left" with "from the right."** Read the problem carefully. If viewing from the right, scan right-to-left.

6. **Not handling empty input.** Loop doesn't execute. Return 0.

---

## 7. Variants (view from both sides, ties)

**View from BOTH sides:** scan left-to-right counting new max's; scan right-to-left counting new max's. A bottle is visible from EITHER side if it's a new max in some direction. Union the two visible sets (using indices) for the total visible count.

**Equal heights don't block:** use `>=` instead of `>`. A bottle as tall as anything to its left is still visible.

**Bottles with widths:** the blocking condition changes; pure height comparison fails. Need a more careful geometric analysis.

---

## 8. The shape — running summary

The pattern:

> **"Maintain a running SUMMARY of the past (max, min, sum, parity, ...) and answer questions about the current element relative to that summary in O(1)."**

Where it appears:

| Problem | Running summary |
|---|---|
| **This problem** | running max |
| Best Time to Buy/Sell Stock | running min of buy prices |
| Maximum Subarray (Kadane) | running max ending here |
| Pascal's Triangle row | running cumulative array |
| Running median | balanced two heaps |
| Stock span (similar but with stack) | when running max would be expensive to maintain, fall back to monotonic stack |

**Pattern to internalize:**

> "Whenever a problem asks about an element's relationship to its PAST (max so far, sum so far, count of X so far), maintain a running scalar summary. O(n) time, O(1) space."

The running-max idiom is the simplest version. More complex problems use running structures (stacks, heaps, deques).

---

> **Self-check — the question to ask next time.**
>
> When you face a problem asking "for each position, compare to the past," ask:
>
> > **"Can I maintain a SCALAR running summary (max, min, sum, count) and compare each element to it?"**
>
> If yes, O(n) single pass.

---

## Cross-references

- **Reference card (post-mastery):** [`../Minimum_Number_of_Bottles_Visible.md`](../Minimum_Number_of_Bottles_Visible.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Sort_Colors.md`](./Sort_Colors.md), [`Kth_Largest_Element_in_an_Array.md`](./Kth_Largest_Element_in_an_Array.md).
  - Coming next: [`Reverse_Pairs.md`](./Reverse_Pairs.md), [`Count_of_Smaller_Numbers_After_Self.md`](./Count_of_Smaller_Numbers_After_Self.md) — merge sort tricks.
