# Teemo Attacking

**Problem Link:**
https://leetcode.com/problems/teemo-attacking/description/

**Topic:**
Number Theory / Misc (really interval merging)

----------------------------------------

## Step 1: The Game

Teemo attacks Ashe at timestamps given in `timeSeries` (sorted ascending). Each attack poisons Ashe for `duration` seconds: from the attack moment through `duration - 1` seconds after.

If a new attack lands while Ashe is already poisoned, the poison timer **resets** to start fresh at the new attack's moment — effectively extending the total poisoned time from the new attack.

Return the **total time** Ashe is poisoned.

Example: `timeSeries = [1, 4]`, `duration = 2`.
- Attack at t=1: poisoned from t=1 to t=2 (inclusive of t=1, for 2 seconds total: 1-2).
- Attack at t=4: poisoned from t=4 to t=5.
- No overlap. Total = 4.

Example: `timeSeries = [1, 2]`, `duration = 2`.
- Attack at t=1: poisoned t=1..2 (2 seconds).
- Attack at t=2: poisoned t=2..3. Overlaps the first poison at t=2.
- Total poisoned: t=1, 2, 3 → 3 seconds.

----------------------------------------

## Step 2: Interval Thinking

Each attack creates an interval [attackTime, attackTime + duration - 1] (inclusive on both ends). Since attacks are timestamped and sorted, and we measure discrete "seconds," total poisoned time equals the **union of all intervals**.

For sorted timestamps, computing the union is easy: walk the list; each new attack contributes either the full `duration` (if the previous interval has ended) or only the gap from the last attack (if still overlapping).

----------------------------------------

## Step 3: Algorithm

```
total = 0
for i in 0..n-1:
    if i == n - 1:
        total += duration
    else:
        gap = timeSeries[i + 1] - timeSeries[i]
        total += min(gap, duration)
return total
```

For each attack except the last, the contributed poison is either the full `duration` (if the next attack is far enough away) or only the gap up to the next attack (which resets the timer). The final attack always contributes its full duration.

O(n) time, O(1) space.

----------------------------------------

## Step 4: Trace on `[1, 2]`, duration = 2

i = 0: gap = 2 - 1 = 1. min(1, 2) = 1. total = 1.
i = 1 (last): total += 2 = 3.

Result: **3**. ✓

Trace on `[1, 4]`, duration = 2:
i = 0: gap = 3. min(3, 2) = 2. total = 2.
i = 1 (last): total += 2 = 4.

Result: **4**. ✓

----------------------------------------

## Step 5: Why `min(gap, duration)`?

If the gap to the next attack is **smaller** than duration, then the new attack interrupts (resets) the poison early — only the gap seconds count.

If the gap is **larger** than or equal to duration, the current attack's poison runs to completion (full duration) before the next attack begins.

Either way, min(gap, duration) captures how long this attack actually poisons.

----------------------------------------

## Step 6: Why the Last Attack Always Adds `duration`?

The last attack has no follower to interrupt it — it runs to its full duration. Special-case it.

Alternatively: pretend there's a dummy "infinity" attack after the last; then the gap is infinite and min(infinity, duration) = duration. Same result, unifies the loop.

----------------------------------------

## Step 7: Name It

**Interval union on sorted intervals**. A simple version of the broader "merge overlapping intervals" problem.

Since our intervals are defined by start times and have a fixed duration, and the starts are sorted, we don't need a separate "merge" pass — a single scan works.

Related:
- Merge Intervals (general case, needs sorting).
- Minimum Number of Conference Rooms.
- Interval Sum / Max Overlapping Intervals.

----------------------------------------

## Step 8: Complexity

Time: **O(n)**.
Space: **O(1)**.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int findPoisonedDuration(vector<int>& timeSeries, int duration) {
    int n = timeSeries.size();
    if (n == 0) return 0;
    int total = 0;
    for (int i = 0; i < n - 1; ++i) {
        total += min(timeSeries[i + 1] - timeSeries[i], duration);
    }
    total += duration;   // last attack's full poison
    return total;
}
```

Loop plus a final add. Handles empty timeSeries as a guard.

----------------------------------------

## Step 10: Follow-up Questions

- **Attacks in unsorted order.** Sort first; same algorithm. Or insert into a sorted data structure online.
- **Varying poison durations per attack.** Same technique but duration depends on the current attack.
- **Return the merged poison intervals.** Track start of each merged interval; close when a gap ≥ duration.
- **Partial overlap resolved differently (e.g., damage per second accumulates).** Different semantics.
- **Simulation with huge timestamp ranges.** Still O(n) — we never iterate seconds, only attacks.
- **Why +0 at i=n-1 in the loop but then `total += duration`?** Because the last attack has no i+1; handle it separately.
