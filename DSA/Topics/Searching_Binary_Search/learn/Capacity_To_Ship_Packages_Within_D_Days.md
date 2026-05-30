# Capacity To Ship Packages Within D Days — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Capacity_To_Ship_Packages_Within_D_Days.md`](../Capacity_To_Ship_Packages_Within_D_Days.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~25 minutes. **This is the canonical "binary search on the ANSWER" problem.** The lesson: **binary search isn't just for finding a value in an array — it's for finding the smallest/largest value in a NUMERIC RANGE that satisfies a monotonic feasibility predicate.** Master this pattern and you've unlocked an entire category: Koko Eating Bananas, Split Array Largest Sum, Aggressive Cows, Minimize Max Distance, and more. **Read [`Find_First_and_Last_Position_of_Element_in_Sorted_Array.md`](./Find_First_and_Last_Position_of_Element_in_Sorted_Array.md) first** for the lower-bound template.

**Map of this file (12 sections):**

1. Read the problem
2. The brute force
3. The pivot — search the ANSWER, not the data
4. The feasibility predicate
5. Why feasibility is monotonic
6. The search range — lo and hi
7. The algorithm
8. Code
9. Trace it
10. Complexity
11. Common pitfalls
12. The shape — binary search on the answer

---

## 1. Read the problem

You have `n` packages in a FIXED ORDER, each with weight `weights[i]`. You need to ship all packages within `days` days. Each day:
- Load packages **IN ORDER** onto one ship (no reordering).
- Stop loading when adding the next package would exceed the ship's capacity.
- Move to the next day.

Find the **MINIMUM SHIP CAPACITY** that allows shipping all packages within `days` days.

**Example:**

```
weights = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], days = 5
```

Answer: **15**. Demonstration:
- Day 1: 1, 2, 3, 4, 5 (sum 15)
- Day 2: 6, 7 (sum 13)
- Day 3: 8 (sum 8)
- Day 4: 9 (sum 9)
- Day 5: 10 (sum 10)

5 days used. Capacity 14 wouldn't fit "6+7+...": 1+2+3+4+5 = 15, can't fit on capacity 14, would need different splits — total > 5 days.

> **Mini-refresher: greedy loading.**
>
> The loading strategy is forced: walk packages in order; each day, load until the next package would overflow; then close the day. This is a **greedy** simulation — no choice on how to split.
>
> The only thing we control is the CAPACITY. That's our optimization variable.

---

## 2. The brute force

Try every capacity `C` starting from the minimum (= max weight) upward. For each `C`, simulate the loading and count days. Return the first `C` with `days_needed(C) <= days`.

```
for C from max(weights) to sum(weights):
    if days_needed(C) <= days:
        return C
```

Each simulation is O(n). Up to `sum(weights) - max(weights) + 1` candidates. Worst case: O(n × sum(weights)). For sum 10^7, that's 10^9 ops — TLE.

We need fewer candidates to test. Binary search.

---

## 3. The pivot — search the ANSWER, not the data

> **Mini-refresher: "binary search on the answer."**
>
> Normally binary search FINDS a value in sorted data. Here, the DATA isn't sorted in any useful way. But the **answer itself** (the capacity) lives in a numeric range `[lo, hi]`, and we can BINARY-SEARCH that range.
>
> The trick: we need a way to TEST any candidate value `C` and decide "yes, C works" or "no, C is too small." If this test is monotonic — once `C` is big enough, all larger `C` also work — binary search finds the boundary.

So the search space isn't the `weights` array. It's the range of POSSIBLE CAPACITIES. We binary-search that range.

For each candidate `C`, we DO an O(n) simulation to check feasibility. Total: O(n × log(range)) — way better than O(n × range).

---

## 4. The feasibility predicate

Define:
```
days_needed(C) = number of days required to ship all packages with capacity C
```

Computed greedily:

```
days_needed(C):
    days = 1
    load = 0
    for w in weights:
        if load + w > C:        # cannot fit; close current day, start new
            days += 1
            load = 0
        load += w
    return days
```

If `days_needed(C) <= days`, capacity `C` works.

**Edge case:** if `C < max(weights)`, we can't even ship the largest single package. `days_needed(C)` would be infinite. We avoid this by setting `lo = max(weights)`.

---

## 5. Why feasibility is monotonic

This is the CRITICAL insight that lets us binary-search.

**Claim:** if `C` works (`days_needed(C) <= days`), then ALL larger `C'` also work.

**Why?** A bigger ship can carry strictly MORE per day (or the same). So with more capacity, every day fits AT LEAST as much. The number of days NEVER goes UP when capacity goes UP. Therefore `days_needed(C')` ≤ `days_needed(C)`, and if `days_needed(C) <= days`, so is `days_needed(C')`.

So the predicate `P(C) = (days_needed(C) <= days)` is **monotonic in C**:
- For small `C`: P is FALSE.
- For large `C`: P is TRUE.
- There's exactly ONE boundary where P flips from FALSE to TRUE.

That boundary IS the answer (the smallest capacity that works). Binary-search it.

> **Mini-refresher: monotonic predicate = binary-search-able.**
>
> Any monotonic boolean function `P(x)` over a numeric range can be binary-searched in O(log(range)). Just like the lower-bound template:
> ```
> lo = min, hi = max + 1
> while lo < hi:
>     mid = (lo + hi) / 2
>     if not P(mid):
>         lo = mid + 1
>     else:
>         hi = mid
> return lo   # first x where P(x) is true
> ```
> For this problem, `P(x) = (days_needed(x) <= days)`. Same template; different predicate.

---

## 6. The search range — lo and hi

**Lower bound (`lo`):** the smallest possible capacity. Must be at least `max(weights)` — otherwise we can't ship the heaviest single package. Set `lo = max(weights)`.

**Upper bound (`hi`):** the largest necessary capacity. If `C = sum(weights)`, we ship EVERYTHING in 1 day — always works for `days >= 1`. Set `hi = sum(weights)`.

So the search range is `[max(weights), sum(weights)]`. Width: ~sum. Binary search takes O(log(sum)) iterations.

---

## 7. The algorithm

```
lo = max(weights)
hi = sum(weights)

while lo < hi:
    mid = (lo + hi) // 2
    if days_needed(mid) <= days:
        hi = mid             # mid works; try smaller
    else:
        lo = mid + 1         # mid doesn't work; need larger

return lo
```

When `lo == hi`, we've found the smallest capacity satisfying the predicate.

> **Mini-refresher: lower-bound template, applied.**
>
> This is EXACTLY the lower-bound template from Find First and Last Position. The only differences:
> - `lo` starts at `max(weights)` not `0`.
> - `hi` starts at `sum(weights)` not `n`.
> - The condition is `not days_needed(mid) <= days` (i.e., `days_needed(mid) > days`) instead of `nums[mid] < target`.
>
> Same shape: find the smallest x in the range where predicate is true.

---

## 8. Code

**C++:**

```cpp
int shipWithinDays(vector<int>& weights, int days) {
    int lo = *max_element(weights.begin(), weights.end());
    int hi = accumulate(weights.begin(), weights.end(), 0);

    auto daysNeeded = [&](int cap) {
        int d = 1, load = 0;
        for (int w : weights) {
            if (load + w > cap) { d++; load = 0; }
            load += w;
        }
        return d;
    };

    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (daysNeeded(mid) <= days) {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }
    return lo;
}
```

**Python:**

```python
def shipWithinDays(weights, days):
    lo, hi = max(weights), sum(weights)

    def days_needed(cap):
        d, load = 1, 0
        for w in weights:
            if load + w > cap:
                d += 1
                load = 0
            load += w
        return d

    while lo < hi:
        mid = (lo + hi) // 2
        if days_needed(mid) <= days:
            hi = mid
        else:
            lo = mid + 1
    return lo
```

**JavaScript:**

```javascript
function shipWithinDays(weights, days) {
    let lo = Math.max(...weights);
    let hi = weights.reduce((a, b) => a + b, 0);

    const daysNeeded = (cap) => {
        let d = 1, load = 0;
        for (const w of weights) {
            if (load + w > cap) { d++; load = 0; }
            load += w;
        }
        return d;
    };

    while (lo < hi) {
        const mid = Math.floor((lo + hi) / 2);
        if (daysNeeded(mid) <= days) {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }
    return lo;
}
```

Complexity: **O(n log(sum)) time, O(1) space.**

---

## 9. Trace it

**`weights = [3, 2, 2, 4, 1, 4]`, `days = 3`.**

`max = 4`, `sum = 16`. Search `[4, 16]`.

```
lo=4, hi=16.

Iter 1: mid = 10. days_needed(10):
  load=0. +3 → 3. +2 → 5. +2 → 7. +4 → 11 > 10! d=2, load=0. +4 → 4. +1 → 5. +4 → 9.
  d = 2 days. 2 <= 3 → works. hi = 10.

Iter 2: lo=4, hi=10. mid=7. days_needed(7):
  +3 → 3. +2 → 5. +2 → 7. +4 → 11 > 7! d=2, load=0. +4 → 4. +1 → 5. +4 → 9 > 7! d=3, load=0. +4 → 4.
  d = 3 days. 3 <= 3 → works. hi = 7.

Iter 3: lo=4, hi=7. mid=5. days_needed(5):
  +3 → 3. +2 → 5. +2 → 7 > 5! d=2, load=0. +2. +4 → 6 > 5! d=3, load=0. +4. +1 → 5. +4 → 9 > 5! d=4, load=0. +4.
  d = 4 days. 4 > 3 → fails. lo = 6.

Iter 4: lo=6, hi=7. mid=6. days_needed(6):
  +3 → 3. +2 → 5. +2 → 7 > 6! d=2, load=0. +2. +4 → 6. +1 → 7 > 6! d=3, load=0. +1. +4 → 5.
  d = 3 days. 3 <= 3 → works. hi = 6.

lo=6, hi=6. EXIT.

Return 6.  ✓
```

---

## 10. Complexity

- **Time:** O(n × log(sum - max)) ≈ O(n × log(sum)).
  - Binary search: O(log(range)) ≈ O(log(sum)) iterations.
  - Each iteration: O(n) feasibility check.
- **Space:** O(1).

For `n = 5 × 10^4` and `sum = 5 × 10^8`, that's about `5 × 10^4 × 30 = 1.5 × 10^6` ops — fast.

> **Mini-refresher: comparing to brute force.**
>
> Brute force: O(n × sum) ≈ 2.5 × 10^13 ops — TLE.
> Binary search on answer: O(n × log(sum)) ≈ 1.5 × 10^6 ops — instant.
>
> The log factor is decisive. Binary search on the answer beats brute force by HUGE margins whenever the answer range is large.

---

## 11. Common pitfalls

1. **Searching the wrong space.** Beginners try binary-searching `weights`. The data isn't sorted in a useful way for this problem. Search the ANSWER (capacity), not the data.

2. **Wrong `lo`.** Setting `lo = 1` or `lo = 0` is wrong — capacities smaller than `max(weights)` are infeasible (can't fit the heaviest single package). Use `lo = max(weights)`.

3. **Wrong `hi`.** Using `hi = max(weights)` is wrong — could need a bigger ship. Use `hi = sum(weights)` (definitely sufficient).

4. **Confusing "fewer days" with "smaller capacity."** Bigger capacity → FEWER days. Smaller capacity → MORE days. Monotonicity in the predicate `days_needed(C) <= days`: small C → FALSE; large C → TRUE.

5. **Off-by-one in the feasibility check.** Common bug: `if (load + w >= cap)` instead of `>`. The condition is `load + w > cap` (can't fit) — strict greater than.

6. **Forgetting to add the last package's weight after closing a day.** When `load + w > cap`, you DO move to a new day. But then you MUST add `w` to the new (empty) day's load. Easy to forget.

7. **Using `lo <= hi` with `hi = mid`.** Infinite loop. Pair `lo < hi` with `hi = mid`.

8. **Computing `(lo + hi) / 2` and overflowing in C++.** Use `lo + (hi - lo) / 2`.

9. **Not validating that the initial range is non-empty.** If `n == 0`, `max(weights)` is undefined. Edge case; the problem likely guarantees `n >= 1`.

10. **Optimizing for "max days = days exactly" instead of "<= days."** Read the spec: ≤ days is the correct condition. The problem allows finishing EARLY.

---

## 12. The shape — binary search on the answer

This pattern reappears constantly. Recognize it via three features:
1. The answer is a NUMBER in a known range.
2. There's a way to TEST any candidate (often a greedy O(n) simulation).
3. The test result is MONOTONIC in the candidate.

| Problem | Search variable | Feasibility check |
|---|---|---|
| **This problem** | capacity | days_needed(C) <= days |
| Koko Eating Bananas (LC #875) | eating rate K | hours_needed(K) <= h |
| Split Array Largest Sum (LC #410) | max subarray sum | can split into ≤ m subarrays |
| Aggressive Cows | min distance d | can place ≥ k cows with gap ≥ d |
| Find K-th Smallest Pair Distance | distance d | count of pairs ≤ d ≥ k |
| Minimum Time to Complete Trips | time T | sum(T // trip[i]) >= totalTrips |
| Cutting Ribbons | length L | sum(ribbon // L) >= K |
| Magnetic Force Between Two Balls | distance d | can place ≥ m balls with gap ≥ d |

**Pattern to internalize:**

> "When the question is 'what's the MIN/MAX value of x such that some condition holds,' and you can TEST any candidate x in O(n) (or O(n log n)), binary search the answer range. Time: O(test × log(range))."

The shape unlocks problems that would otherwise need DP or are NP-hard in general.

---

> **Self-check — the question to ask next time.**
>
> When you face an optimization problem with a numeric answer and the question is "min/max value such that some condition is met," ask:
>
> > **"Can I write a function `works(x)` that's TRUE for some range of x and FALSE for the rest, in a monotonic way? If yes, binary-search the boundary."**
>
> If yes, you've turned an optimization problem into a binary-search problem.

---

## Cross-references

- **Reference card (post-mastery):** [`../Capacity_To_Ship_Packages_Within_D_Days.md`](../Capacity_To_Ship_Packages_Within_D_Days.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Find_First_and_Last_Position_of_Element_in_Sorted_Array.md`](./Find_First_and_Last_Position_of_Element_in_Sorted_Array.md) — base template.
  - Coming next: [`Magnetic_Force_Between_Two_Balls.md`](./Magnetic_Force_Between_Two_Balls.md) — max-min twist on the same pattern.
  - Coming after: [`Smallest_Good_Base.md`](./Smallest_Good_Base.md) — binary search on a number-theoretic predicate.
