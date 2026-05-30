# Teemo Attacking — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Teemo_Attacking.md`](../Teemo_Attacking.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/teemo-attacking/description/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/teemo-attacking/description/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~10 minutes. **The lesson: interval UNION on sorted starts with constant duration. For each attack i (except last), add `min(gap_to_next, duration)`. Final attack contributes full duration. O(n).**

**Map of this file (7 sections):**

1. Read the problem
2. Interval framing
3. Per-attack contribution
4. Code
5. Trace it
6. Common pitfalls
7. The shape — sorted-interval union

---

## 1. Read the problem

Attacks happen at sorted timestamps `timeSeries[i]`. Each attack poisons for `duration` seconds. If a new attack lands during ongoing poison, the timer RESETS to start fresh from the new attack. Return total time poisoned.

**Example:** timeSeries=`[1, 2]`, duration=2 → attack at 1 poisons t∈[1,2], attack at 2 resets to t∈[2,3]. Union = {1, 2, 3} → **3** seconds.

---

## 2. Interval framing

> **Mini-refresher: each attack contributes an interval [t, t + duration - 1].**
>
> Total poisoned time = MEASURE OF UNION of all intervals.
>
> Since starts are sorted, walking the list gives us the union in O(n).

---

## 3. Per-attack contribution

For each attack i (except the last):
- Gap to the next attack = `timeSeries[i+1] - timeSeries[i]`.
- This attack contributes `min(gap, duration)`:
  - If gap ≥ duration → no overlap; this attack contributes its full duration.
  - If gap < duration → next attack resets early; this one contributes only `gap` seconds.

The LAST attack always contributes the full `duration` (no follower to reset it).

---

## 4. Code

**C++:**

```cpp
int findPoisonedDuration(vector<int>& timeSeries, int duration) {
    int n = timeSeries.size();
    if (n == 0) return 0;
    int total = 0;
    for (int i = 0; i < n - 1; ++i) {
        total += min(timeSeries[i + 1] - timeSeries[i], duration);
    }
    total += duration;   // last attack runs to completion
    return total;
}
```

Complexity: **O(n)** time, **O(1)** space.

---

## 5. Trace it

- `[1, 4]`, d=2: gap=3, min(3, 2)=2. + last duration = 2+2 = **4**.
- `[1, 2]`, d=2: gap=1, min(1, 2)=1. + 2 = **3**.

---

## 6. Common pitfalls

1. **Forgetting the last attack's full contribution.** Loop should run i = 0..n-2; add duration after.
2. **Using `max` instead of `min`.** We want the SHORTER of (gap, duration) — that's how long this attack actually poisons.
3. **Treating duration as exclusive on the end.** It's INCLUSIVE: attack at t with duration d poisons t through t+d-1 (d total seconds).
4. **Sorting unnecessarily.** Input is already sorted.
5. **Handling empty input.** Return 0; guard early.

---

## 7. The shape — sorted-interval union

The pattern: **sorted intervals with FIXED duration → walk + min-gap accumulation.**

| Problem | Twist |
|---|---|
| **This problem** | constant duration per attack |
| Merge Intervals (LC 56) | variable intervals, sort by start |
| Minimum Meeting Rooms | sweep-line / heap |
| Interval Sum | running sum of intervals |
| Sleep / Wake periods | similar union |

**Pattern to internalize:**

> "Constant-duration sorted-start interval problems: each interval contributes `min(gap, duration)`. Last contributes full duration. O(n)."

---

> **Self-check — the question to ask next time.**
>
> When intervals start at sorted times with constant length:
>
> > **"For each i (except last), add min(gap_to_next, duration). Final attack adds full duration."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Teemo_Attacking.md`](../Teemo_Attacking.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Non_overlapping_Intervals.md`](../../Greedy/learn/Non_overlapping_Intervals.md), [`Minimum_Platforms.md`](../../Greedy/learn/Minimum_Platforms.md).
  - Coming next: [`Rectangle_Area.md`](./Rectangle_Area.md), [`Subsequence_of_Size_K_With_Largest_Sum.md`](./Subsequence_of_Size_K_With_Largest_Sum.md), [`Number_of_Digit_One.md`](./Number_of_Digit_One.md).
