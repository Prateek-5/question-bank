# Non-overlapping Intervals

**Problem Link:**
https://leetcode.com/problems/non-overlapping-intervals/

**Topic:**
Greedy

----------------------------------------

## Step 1: Read the Problem, Recast It

You're given a collection of intervals `[start, end)`. Return the **minimum number of intervals you need to remove** so that the remaining ones don't overlap.

Example: `[[1,2], [2,3], [3,4], [1,3]]`.
- If I keep `[1,2], [2,3], [3,4]`, they are non-overlapping (touching at endpoints is fine). That's 3 intervals kept. I removed 1 (the `[1,3]`).
- If I kept all 4, they'd overlap. So 1 is the minimum I can remove.

Answer: **1**.

Note the equivalence: "remove min intervals" = "keep max non-overlapping intervals, answer is `n - kept`." So I can think of it as **how many can I keep?**

----------------------------------------

## Step 2: Play With a Small Example

`[[1,2], [1,3], [2,4], [3,5]]`. Which intervals can coexist without overlap?

Let me draw them on a timeline:
```
1 2 3 4 5
[ ]           (1-2)
[    ]        (1-3)
  [    ]      (2-4)
    [    ]    (3-5)
```

`[1,2]` and `[2,4]` don't overlap (2-4 starts at 2, when 1-2 ended). Kept: 2.
`[1,2]` and `[3,5]` don't overlap. Kept: 2.
`[1,2], [2,4]` together — can I add `[3,5]`? 3 < 4, overlaps with `[2,4]`. No.
`[1,2], [3,5]` — can I add another? `[1,3]` overlaps with `[3,5]` (touching at 3)? No — at 3 exactly, `[1,3)` has ended. Let me check: `[1,3]` vs `[3,5]`. If endpoints are inclusive ("closed"), they share 3. The problem typically treats endpoints as open (start inclusive, end exclusive) — "touch is fine." So `[1,3]` and `[3,5]` don't overlap.

So a kept set could be: `[1,2], [3,5]` or `[1,3], [3,5]`, etc. Max size = 2 (since we have 4 intervals and 2 remove).

Actually I need to check more carefully. In this example we probably can keep exactly 2 intervals non-overlapping; answer = 4 - 2 = 2 removed.

----------------------------------------

## Step 3: What's the Right Strategy?

Suppose I need to pick a maximum set of non-overlapping intervals. What's a sensible greedy choice?

Option A: always pick the interval with the **earliest start**. Does this work? Consider `[[1,100], [2,3], [4,5]]`. Earliest start is `[1,100]`. If I pick it, nothing else fits. Kept: 1. But the best is 2 (the two short ones). So earliest-start greedy fails.

Option B: always pick the **shortest** interval. Consider `[[1,5], [2,3], [3,4], [4,10]]`. Shortest is either `[2,3]` or `[3,4]` (both length 1). If I pick `[2,3]`, now `[3,4]` is still available, and `[4,10]` is available. Kept: 3. Actually that's the best. But is shortest-first always right? Consider `[[1,4], [2,3], [3,6]]`. Shortest is `[2,3]`. Picking it blocks both others. Kept: 1. But best is 2 (`[1,4]` blocks `[2,3]` but allows `[3,6]`... wait no, `[1,4]` and `[3,6]` overlap at 3-4.) Hmm. Actually in this example kept is at most 2: `[2,3], [3,6]` — let me verify overlap. 3 is the endpoint. If open-end: no overlap. Kept: 2. So shortest-first gave us 1 when 2 was possible. Fails.

Option C: always pick the interval that **ends earliest**. Let me try `[[1,100], [2,3], [4,5]]`. Ends are 100, 3, 5. Earliest end is `[2,3]`. Pick it; now we can't pick anything overlapping it. `[4,5]` starts at 4 ≥ 3, pick it. `[1,100]` overlaps both. Kept: 2. That's the best.

Let me try the other example: `[[1,4], [2,3], [3,6]]`. Ends: 4, 3, 6. Earliest end: `[2,3]`. Pick it. Next candidates start ≥ 3: `[3,6]`. Pick it. `[1,4]` starts at 1, overlaps `[2,3]`. Skip. Kept: 2. Correct.

**Greedy by earliest end seems to work.**

----------------------------------------

## Step 4: Why Earliest-End Works

Let me argue formally why this strategy gives the maximum count of non-overlapping intervals.

**Claim:** Sorting by end time and greedily picking each interval whose start is ≥ the previously kept end gives the optimum.

**Proof sketch (exchange argument):** Suppose some optimal solution uses a different interval first than the one our greedy picks. The greedy picks the interval `g` with the smallest end time. Any optimal solution's first picked interval, `o`, must have `o.end ≥ g.end` (because `g.end` is the smallest). Now compare: if we replace `o` with `g` in the optimal solution, do we break anything? No — `g` ends no later than `o`, so anything that came after `o` in the optimal is still compatible with `g` (it starts no earlier than `o.end ≥ g.end`). So we can swap `o` for `g` without shrinking the optimal.

Applying this argument repeatedly, we transform any optimal into one that starts with the greedy's first choice, then proceeds recursively on the remaining intervals. So greedy matches optimum at every step.

This is a classic **interval scheduling** argument. The elegance of the proof convinces us that greedy isn't a heuristic here — it's exact.

----------------------------------------

## Step 5: The Algorithm

1. Sort intervals by `end` ascending.
2. Track `lastEnd` = end of the last kept interval, initially `-∞`.
3. For each interval in sorted order: if `interval.start >= lastEnd`, keep it — update `lastEnd = interval.end`. Otherwise, it overlaps; we remove it (increment a counter).
4. Return the count of removed.

----------------------------------------

## Step 6: Trace on the Original Example

`intervals = [[1,2], [2,3], [3,4], [1,3]]`.

Sort by end: `[[1,2], [2,3], [1,3], [3,4]]`. (Ends: 2, 3, 3, 4 — ties broken by start.)

```
lastEnd = -∞, removed = 0.

[1,2]: start 1 >= -∞. Keep. lastEnd = 2.
[2,3]: start 2 >= 2. Keep. lastEnd = 3.
[1,3]: start 1 < 3. Overlaps. Remove. removed = 1.
[3,4]: start 3 >= 3. Keep. lastEnd = 4.
```

Kept: 3. Removed: 1. ✓

----------------------------------------

## Step 7: Name What We Did

This is **interval scheduling** — a foundational greedy problem. The earliest-end-time selection appears in classroom scheduling, meeting-room allocation, job deadline problems, etc. Even if you see a problem with different wording ("attend max meetings," "fit max bookings"), the shape is often the same.

Be careful: interval scheduling's "earliest end" is distinct from **interval partitioning** (how many rooms needed). Different problem, different greedy.

----------------------------------------

## Step 8: Complexity

Time: sorting dominates. **O(n log n)**.
Space: sorting overhead. **O(log n)** or **O(n)** depending on algorithm. Beyond that, O(1).

----------------------------------------

## Step 9: C++ Implementation

```cpp
int eraseOverlapIntervals(vector<vector<int>>& intervals) {
    if (intervals.empty()) return 0;
    sort(intervals.begin(), intervals.end(),
         [](const vector<int>& a, const vector<int>& b) {
             return a[1] < b[1];       // sort by end time
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

A subtle style choice: I compare `iv[0] >= lastEnd` (non-strict). This lets touching-endpoint intervals both be kept, matching the usual "open-ended" interval convention of these problems. If the problem defines touch as overlap, change to `>`.

----------------------------------------

## Step 10: Follow-up Questions

- **Maximum number of meetings you can attend** (same problem, different framing). Answer = `n - eraseOverlapIntervals`.
- **Minimum number of meeting rooms needed to hold all meetings.** Different problem — interval partitioning. Sort start times and end times separately, sweep through to track concurrent meetings.
- **Weighted interval scheduling (each interval has value; maximize total value without overlap).** Greedy fails; use DP with binary search.
- **Intervals on a circle** (e.g., jobs around 24-hour clock). Split at some point and run scheduling on each half.
- **Handle touching-endpoint intervals as overlapping.** Change `iv[0] >= lastEnd` to `iv[0] > lastEnd`.
