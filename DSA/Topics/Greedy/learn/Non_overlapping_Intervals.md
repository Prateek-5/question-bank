# Non-overlapping Intervals — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Non_overlapping_Intervals.md`](../Non_overlapping_Intervals.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/non-overlapping-intervals/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: max non-overlapping intervals = sort by END time + greedy pick. Other greedy orderings (earliest start, shortest) FAIL. The exchange argument proves end-time ordering is optimal.**

**Map of this file (9 sections):**

1. Read the problem
2. Reframe: max kept = min removed
3. Which greedy works?
4. Why earliest-end is optimal
5. Code
6. Trace it
7. Common pitfalls
8. The shape — interval scheduling
9. Self-check

---

## 1. Read the problem

Given a list of intervals `[start, end)`, return the MINIMUM number of intervals to REMOVE so the remaining set has no overlaps.

**Example:** `[[1,2], [2,3], [3,4], [1,3]]`. Removing `[1,3]` leaves three non-overlapping intervals. Return **1**.

---

## 2. Reframe: max kept = min removed

> **Mini-refresher: "remove min to keep non-overlapping" = "keep max non-overlapping".**
>
> Answer = `n - (max non-overlapping kept)`.
>
> This converts the problem into a classic INTERVAL SCHEDULING question.

---

## 3. Which greedy works?

Three plausible greedies:

| Strategy | Counterexample | Verdict |
|---|---|---|
| Earliest START | `[[1,100], [2,3], [4,5]]` → pick `[1,100]` (kept=1); optimal is 2 | **FAIL** |
| Shortest length | `[[1,4], [2,3], [3,6]]` → pick `[2,3]` (kept=1); optimal is 2 | **FAIL** |
| Earliest END | always optimal (proved next) | **WORKS** |

---

## 4. Why earliest-end is optimal

> **Mini-refresher: exchange argument for interval scheduling.**
>
> Let greedy's first pick be g (smallest end time). Take any optimal OPT.
>
> OPT's first pick o has `o.end ≥ g.end` (because g.end is the minimum). Replace o with g in OPT. Anything that came AFTER o starts at `≥ o.end ≥ g.end`, so it's still compatible with g.
>
> Swap: OPT's count unchanged, but now matches greedy's first choice. Recurse on the rest. So greedy ≥ OPT for all initial segments.

The end-time ordering "leaves the most room" for future picks — which is exactly what we want.

---

## 5. Code

**C++:**

```cpp
int eraseOverlapIntervals(vector<vector<int>>& intervals) {
    if (intervals.empty()) return 0;
    sort(intervals.begin(), intervals.end(),
         [](const vector<int>& a, const vector<int>& b) {
             return a[1] < b[1];
         });
    int removed = 0;
    int lastEnd = INT_MIN;
    for (const auto& iv : intervals) {
        if (iv[0] >= lastEnd) lastEnd = iv[1];   // keep
        else removed++;                           // overlaps with kept
    }
    return removed;
}
```

**Python:**

```python
def eraseOverlapIntervals(intervals):
    intervals.sort(key=lambda x: x[1])
    removed = 0
    last_end = float('-inf')
    for s, e in intervals:
        if s >= last_end:
            last_end = e
        else:
            removed += 1
    return removed
```

Complexity: **O(n log n)** time (sort), **O(1)** extra space.

---

## 6. Trace it

`intervals = [[1,2], [2,3], [3,4], [1,3]]`.

Sort by end: `[[1,2], [2,3], [1,3], [3,4]]` (ends 2, 3, 3, 4).

```
lastEnd = -∞, removed = 0.

[1,2]: 1 ≥ -∞. Keep. lastEnd = 2.
[2,3]: 2 ≥ 2. Keep. lastEnd = 3.
[1,3]: 1 < 3. Overlaps. removed = 1.
[3,4]: 3 ≥ 3. Keep. lastEnd = 4.

Return 1.  ✓
```

---

## 7. Common pitfalls

1. **Sorting by START.** Fails on `[[1,100], [2,3], [4,5]]`. Sort by END.
2. **Treating touching endpoints as overlap.** Convention: `[1,2]` and `[2,3]` are NOT overlapping (start of one = end of other). Use `>=` not `>`. If the problem says touching IS overlap, swap to `>`.
3. **Returning kept count instead of removed.** Answer = `n - kept`. Or count removals directly.
4. **Using DP for unweighted case.** Greedy is exact here. DP is needed ONLY for weighted interval scheduling.
5. **Forgetting empty input check.** `intervals = []` → return 0.

---

## 8. The shape — interval scheduling

The pattern: **max non-overlapping intervals = sort by end + greedy.**

| Problem | Twist |
|---|---|
| **This problem** | min to remove (= n - max kept) |
| Maximum Number of Events That Can Be Attended | min-heap variant |
| Maximum Number of Meetings | same as this |
| Minimum Arrows to Burst Balloons | overlapping → one arrow group |
| Two City Scheduling | sort by cost difference + greedy |
| Partition Labels | greedy by last-occurrence |

**Pattern to internalize:**

> "For UNWEIGHTED max non-overlapping selection, sort by END time and pick greedily. For WEIGHTED, you need DP (with binary search)."

---

## 9. Self-check

> **The question to ask next time:**
>
> > **"Is this UNWEIGHTED interval scheduling? Sort by END, greedy pick. Don't confuse with interval PARTITIONING (rooms count → sweep line)."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Non_overlapping_Intervals.md`](../Non_overlapping_Intervals.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Assign_Cookies.md`](./Assign_Cookies.md), [`Maximize_Sum_After_K_Negations.md`](./Maximize_Sum_After_K_Negations.md).
  - Coming next: [`Minimum_Platforms.md`](./Minimum_Platforms.md), [`Bulb_Switcher.md`](./Bulb_Switcher.md).
