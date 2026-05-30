# Russian Doll Envelopes — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Russian_Doll_Envelopes.md`](../Russian_Doll_Envelopes.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/russian-doll-envelopes/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/russian-doll-envelopes/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: reduce 2D nesting to 1D LIS. Sort by width ASC, height DESC on ties; then run strict LIS on heights. The DESC tie-break is the subtle trick — without it, same-width envelopes would falsely "nest."**

**Map of this file (9 sections):**

1. Read the problem
2. The "fits inside" definition
3. Sort-then-LIS strategy
4. Why height DESCENDING on ties
5. Code
6. Trace it
7. Common pitfalls
8. The shape — multi-dim LIS via sort
9. Self-check

---

## 1. Read the problem

`envelopes[i] = [w, h]`. Envelope A fits STRICTLY INSIDE envelope B iff `A.w < B.w` AND `A.h < B.h` (both strict). No rotations. Return the MAX number of envelopes nestable into a single chain.

**Example:** `[[5,4], [6,4], [6,7], [2,3]]` → chain `[2,3] → [5,4] → [6,7]` → **3**.

---

## 2. The "fits inside" definition

> **Mini-refresher: nesting needs STRICT inequality in BOTH dimensions.**
>
> `[6, 4]` and `[6, 7]` CAN'T nest (same width). Neither can `[5, 5]` and `[5, 6]` (same width). Equality is BLOCKED.

This "strict in both" is what makes the problem tricky — equal-width envelopes need careful handling.

---

## 3. Sort-then-LIS strategy

> **Mini-refresher: sort one dimension; LIS on the other.**
>
> Step 1: Sort envelopes by width ascending. After sorting, any nesting chain has non-decreasing widths.
>
> Step 2: Among those, find the longest STRICTLY INCREASING subsequence of HEIGHTS. That's LIS — O(n log n) via patience sorting.
>
> But: equal widths can't nest. How do we prevent the LIS from picking two same-width envelopes whose heights happen to be increasing?

The answer is the tie-break order.

---

## 4. Why height DESCENDING on ties

> **Mini-refresher: same-width envelopes in DESCENDING height order.**
>
> When two envelopes share width, place them with LARGER height FIRST in the sorted list.
>
> Then their heights, in sorted order, are DECREASING — so LIS (strictly increasing) will skip them naturally.
>
> If we instead sorted heights ascending on ties, LIS would happily extend across same-width envelopes, falsely counting them as nestable.

Example: `[[6, 4], [6, 7]]`.
- Width-asc, height-DESC: `[[6, 7], [6, 4]]` → heights `[7, 4]` → LIS = 1 (correct).
- Width-asc, height-ASC: `[[6, 4], [6, 7]]` → heights `[4, 7]` → LIS = 2 (WRONG — these can't nest).

The DESC tie-break is doing important work.

---

## 5. Code

**C++:**

```cpp
int maxEnvelopes(vector<vector<int>>& envelopes) {
    sort(envelopes.begin(), envelopes.end(),
         [](const vector<int>& a, const vector<int>& b) {
             if (a[0] != b[0]) return a[0] < b[0];
             return a[1] > b[1];   // height DESC on tied widths
         });

    vector<int> tails;
    for (auto& e : envelopes) {
        int h = e[1];
        auto it = lower_bound(tails.begin(), tails.end(), h);
        if (it == tails.end()) tails.push_back(h);
        else *it = h;
    }
    return tails.size();
}
```

**Python:**

```python
from bisect import bisect_left
def maxEnvelopes(envelopes):
    envelopes.sort(key=lambda e: (e[0], -e[1]))
    tails = []
    for w, h in envelopes:
        p = bisect_left(tails, h)
        if p == len(tails):
            tails.append(h)
        else:
            tails[p] = h
    return len(tails)
```

Complexity: **O(n log n)** time (sort + LIS), **O(n)** space.

---

## 6. Trace it

`envelopes = [[5,4], [6,4], [6,7], [2,3]]`.

Sort (width asc, height desc on ties): `[[2,3], [5,4], [6,7], [6,4]]`.

Heights: `[3, 4, 7, 4]`. LIS:

```
h=3: tails empty → append. tails = [3].
h=4: 4 > 3 → append. tails = [3, 4].
h=7: 7 > 4 → append. tails = [3, 4, 7].
h=4: lower_bound(tails, 4) = 1 (first ≥ 4). Replace. tails = [3, 4, 7].
```

len(tails) = 3.  ✓

The last h=4 (from envelope `[6, 4]`) didn't extend the LIS because of the DESC tie-break (it came AFTER `[6, 7]`). Patience sorting correctly handles the "same-width" issue.

---

## 7. Common pitfalls

1. **Sorting both dimensions ASC.** Allows same-width envelopes to "nest" — wrong.
2. **`upper_bound` instead of `lower_bound`.** Would allow equal heights to extend, but we need STRICT increase.
3. **Trying 2D LIS directly.** O(n²) and complex; the sort-and-reduce makes it O(n log n) and clean.
4. **Returning `envelopes.size()` if all unique.** Doesn't account for actual nestability.
5. **Returning `tails` as the chain.** It's just LIS bookkeeping — same caveat as plain LIS.

---

## 8. The shape — multi-dim LIS via sort

The pattern: **sort one dimension to reduce a multi-dim chain problem to 1D LIS.**

| Problem | Sort key | LIS on |
|---|---|---|
| **This problem** | width asc + height DESC on ties | heights |
| Box Stacking (3D) | width asc + length desc / height for ties | length + height |
| Longest Chain of Pairs (LC 646) | a[0] asc | a[1] strictly > prev a[1] (greedy) |
| Schedule Maximum Number of Tasks | start time | duration / value |

**Pattern to internalize:**

> "For chain problems with MULTIPLE strict inequalities, sort by one dimension with a CAREFUL tie-break (descending on the secondary), then LIS on the secondary."

The tie-break encodes the "strict in both" rule.

---

## 9. Self-check

> **The question to ask next time:**
>
> > **"Multi-dim chain problem? Sort primary asc, secondary DESC on ties, then strict LIS on secondary. The DESC tie-break enforces strictness on the primary."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Russian_Doll_Envelopes.md`](../Russian_Doll_Envelopes.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Longest_Increasing_Subsequence.md`](./Longest_Increasing_Subsequence.md), [`Longest_Arithmetic_Subsequence.md`](./Longest_Arithmetic_Subsequence.md).
  - Coming next: [`Maximum_Height_by_Stacking_Cuboids.md`](./Maximum_Height_by_Stacking_Cuboids.md), [`Longest_Common_Subsequence.md`](./Longest_Common_Subsequence.md).
