# Minimum Platforms — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Minimum_Platforms.md`](../Minimum_Platforms.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://www.geeksforgeeks.org/minimum-number-platforms-required-railwaybus-station/" target="_blank" rel="noopener noreferrer">https://www.geeksforgeeks.org/minimum-number-platforms-required-railwaybus-station/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **The lesson: SWEEP LINE. Sort arrivals and departures separately; walk both with two pointers, +1 on arrival, -1 on departure. Track running peak. NOT the same as interval scheduling — this is interval PARTITIONING.**

**Map of this file (9 sections):**

1. Read the problem
2. The "peak concurrency" reframe
3. Sweep line via two sorted arrays
4. Tie-handling
5. Code
6. Trace it
7. Why it works
8. Common pitfalls
9. The shape — interval partitioning

---

## 1. Read the problem

Two arrays: `arrival[i]` and `departure[i]` for each train. A train occupies one platform during `[arrival, departure]`. Find the MINIMUM platforms needed so all trains can be accommodated.

**Example:**
```
arrival   = [900, 940, 950, 1100, 1500, 1800]
departure = [910, 1200, 1120, 1130, 1900, 2000]
```

Maximum concurrent trains: at 1100, three trains overlap → **3** platforms.

---

## 2. The "peak concurrency" reframe

> **Mini-refresher: minimum platforms = maximum concurrent trains at any moment.**
>
> The "number of trains currently at the station" is a step function over time: +1 at each arrival, -1 at each departure. The PEAK of this step function = minimum platforms needed.

This converts the problem from "minimum platforms" into "find the peak of a step function."

---

## 3. Sweep line via two sorted arrays

> **Mini-refresher: two-pointer merge on sorted arrivals and departures.**
>
> Sort BOTH arrival[] and departure[] ascending. Use pointers i and j.
>
> - If next arrival is earlier than next departure: train arrives → `current++`. Update peak. Advance i.
> - Else: train departs → `current--`. Advance j.
>
> Continue until all arrivals processed. (Remaining departures only decrement — they can't raise the peak.)

This is the cleanest implementation of the sweep — no explicit event list needed.

---

## 4. Tie-handling

If a train arrives at the EXACT instant another departs (`arrival == departure`), do they share a platform?

> **Mini-refresher: convention-dependent tie-break.**
>
> - If "departure first" (a train clears the platform before a new one needs it) → use `arrival[i] > departure[j]` (departure wins ties).
> - If "arrival first" (the new train can't use the same platform at the same instant) → use `arrival[i] >= departure[j]` (arrival wins ties).
>
> Most interview formulations treat ties as conflict — both trains need different platforms. Use `<=` (or equivalently, arrival wins) for the conservative upper bound.

For this walkthrough we'll use `arrival[i] <= departure[j]` (conservative — they conflict at the tie).

---

## 5. Code

**C++:**

```cpp
int findPlatform(vector<int>& arrival, vector<int>& departure) {
    int n = arrival.size();
    sort(arrival.begin(), arrival.end());
    sort(departure.begin(), departure.end());

    int i = 0, j = 0;
    int current = 0, peak = 0;
    while (i < n) {
        if (arrival[i] <= departure[j]) {
            current++;
            peak = max(peak, current);
            i++;
        } else {
            current--;
            j++;
        }
    }
    return peak;
}
```

**Python:**

```python
def findPlatform(arrival, departure):
    arrival.sort()
    departure.sort()
    n = len(arrival)
    i = j = current = peak = 0
    while i < n:
        if arrival[i] <= departure[j]:
            current += 1
            peak = max(peak, current)
            i += 1
        else:
            current -= 1
            j += 1
    return peak
```

Complexity: **O(n log n)** time (sorting), **O(1)** extra space.

---

## 6. Trace it

`arrival = [900, 940, 950, 1100, 1500, 1800]` (already sorted).
`departure` sorted: `[910, 1120, 1130, 1200, 1900, 2000]`.

```
i=0, j=0, cur=0, peak=0.

900 <= 910: cur=1, peak=1. i=1.
940 <= 910? no (940 > 910). cur=0. j=1.
940 <= 1120: cur=1, peak=1. i=2.
950 <= 1120: cur=2, peak=2. i=3.
1100 <= 1120: cur=3, peak=3. i=4.
1500 <= 1120? no. cur=2. j=2.
1500 <= 1130? no. cur=1. j=3.
1500 <= 1200? no. cur=0. j=4.
1500 <= 1900: cur=1, peak=3. i=5.
1800 <= 1900: cur=2, peak=3. i=6.

i == n. Exit.

Return peak = 3.  ✓
```

---

## 7. Why it works

The sweep line computes the EXACT step function value at every event time. The peak is observed by tracking `max(current)` immediately AFTER each arrival.

> **Mini-refresher: peak always follows an arrival, never a departure.**
>
> Departures only decrement `current` — never raise the peak. So we don't need to update `peak` after departures. (Updating only on arrival is a micro-optimization.)

---

## 8. Common pitfalls

1. **Sorting arrival and departure together as pairs.** Wrong — they need to be sorted INDEPENDENTLY.
2. **Confusing with interval scheduling.** This is interval PARTITIONING — count concurrent intervals. Interval scheduling is "max non-overlapping" — sort by end and pick greedily. Different problems!
3. **Incrementing j on arrival (or vice versa).** Each branch advances ITS pointer only.
4. **Updating peak after departure.** Harmless but wasteful.
5. **Off-by-one with tie-breaking.** Decide the convention up front (`<=` or `<`) and stick with it.
6. **Forgetting to drain remaining departures.** No need — remaining departures only decrement, can't raise the peak. Loop exits when arrivals are done.

---

## 9. The shape — interval partitioning

The pattern: **how many concurrent intervals at any moment? = SWEEP LINE.**

| Problem | Twist |
|---|---|
| **This problem** | trains and platforms |
| Meeting Rooms II | meetings and rooms (identical) |
| Maximum CPU Load | jobs at any moment |
| Range Module | track active ranges |
| Car Pooling | passenger count along route |
| Maximum Population Year | birth-year sweep over deaths |

**Pattern to internalize:**

> "For 'max concurrent items' problems, sweep events in time order. +1 on start, -1 on end. Track running peak. O(n log n) for the sort."

The two-array trick avoids building an explicit event list — same effect, less code.

---

> **Self-check — the question to ask next time.**
>
> When you need "how many rooms/platforms/etc. for all the events?", ask:
>
> > **"Is this peak concurrency? Sort starts and ends separately, two-pointer merge, +1/-1, max(current). NOT to be confused with interval scheduling."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Minimum_Platforms.md`](../Minimum_Platforms.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Non_overlapping_Intervals.md`](./Non_overlapping_Intervals.md) (interval scheduling — the OTHER greedy).
  - Coming next: [`Bulb_Switcher.md`](./Bulb_Switcher.md).
