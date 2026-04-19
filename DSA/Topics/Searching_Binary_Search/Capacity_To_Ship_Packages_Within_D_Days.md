# Capacity To Ship Packages Within D Days

**Problem Link:**
https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/

**Topic:**
Searching / Binary Search

----------------------------------------

## Step 1: Understand the Setup

You have packages to ship, each with a known weight, in a given order. You have `days` days to finish shipping. Each day, you load consecutive packages in order onto one ship, up to the ship's capacity. Once full, you close the day and start fresh tomorrow.

You need to find the **minimum ship capacity** such that everything ships within `days` days.

Example: `weights = [3, 2, 2, 4, 1, 4]`, `days = 3`. A ship capacity of 6 works:
- Day 1: 3 + 2 = 5. Next is 2, total would be 7 > 6. Close day.
- Day 2: 2 + 4 = 6. Next is 1, total would be 7 > 6. Close day.
- Day 3: 1 + 4 = 5. Close day. Done.

Could 5 work?
- Day 1: 3 + 2 = 5. Next is 2, 7 > 5. Close.
- Day 2: 2 + 1 = 3. Wait no, after day 1 we consumed packages 3 and 2. Next is 2 (the third package), then 4. 2 + 4 = 6 > 5. So day 2 packs just 2. Close.
- Day 3: 4. 4 + 1 = 5. Close.
- Day 4: 4.

Four days. Too many. So 5 doesn't work; 6 is the minimum. (For this problem, the expected answer is actually 6.)

----------------------------------------

## Step 2: What Are We Really Optimizing?

The question is "what's the smallest capacity C such that the greedy load-until-it-overflows strategy uses ≤ days days?"

Let me denote this as `daysNeeded(C)`. For any proposed capacity C, we can simulate the greedy in O(n) and count the days used.

Key question: **how does `daysNeeded(C)` behave as C grows?**

Intuitively: bigger ship → fewer days. Let me verify:

- If C is tiny (smaller than the largest weight), we literally can't ship that one package. `daysNeeded = infinity`.
- If C equals the largest weight, we can always fit any single package. Days used: at most n (one package per day).
- As C grows, we can combine more packages per day. Days decrease.
- When C is the sum of all weights, we ship everything in 1 day.

So `daysNeeded(C)` is a **non-increasing** function of C. That's not quite "monotonic predicate" language — let me be more precise.

Consider the predicate `p(C) = (daysNeeded(C) ≤ days)`. As C increases:
- For small C, daysNeeded > days → `p(C) = false`.
- For large C, daysNeeded ≤ days → `p(C) = true`.

Somewhere in between, `p` flips from false to true. And once it's true, it stays true (bigger ship can only help). So the predicate has exactly one false-to-true boundary — the minimum C we want.

**That's the structure binary search loves: a monotonic flip.** Once I see this, I know the approach.

----------------------------------------

## Step 3: Establish the Search Range

What values of C should we search over?

**Lower bound:** C must be at least `max(weights)`. If it's smaller, we can't ship the heaviest single package — the answer would be impossible. So `lo = max(weights)`.

**Upper bound:** C equal to `sum(weights)` ships everything in 1 day — always works for any days ≥ 1. So `hi = sum(weights)`.

Our binary search operates on `[lo, hi]`, looking for the smallest C where `p(C)` is true.

----------------------------------------

## Step 4: The Greedy Simulation

For any capacity C, how do we compute `daysNeeded(C)`?

Walk the weights in order. Maintain today's running load. When adding the next weight would overflow C, close the day and start a new one with that weight.

```
daysNeeded(C):
    days = 1
    load = 0
    for w in weights:
        if load + w > C:
            days += 1
            load = 0
        load += w
    return days
```

Each package is visited once. O(n).

Why is the greedy optimal? Because packing any package onto a later day can only cost more days overall (we've delayed it for nothing — no future day can fit more cumulatively than today could). The formal proof is an exchange argument.

----------------------------------------

## Step 5: Binary Search Over Capacity

Now combine: binary search `C` in `[lo, hi]`, using `daysNeeded(C) ≤ days` as the decision predicate.

```
while lo < hi:
    mid = (lo + hi) / 2
    if daysNeeded(mid) <= days:
        hi = mid        # mid works; try smaller
    else:
        lo = mid + 1    # mid doesn't work; need bigger
return lo
```

Loop invariant: the answer is always in `[lo, hi]`. When they meet, that value is the answer.

----------------------------------------

## Step 6: Trace on `[3, 2, 2, 4, 1, 4]`, days = 3

`max(weights) = 4`, `sum(weights) = 16`. Search `[4, 16]`.

```
lo=4, hi=16. mid=10.
  daysNeeded(10): load=3, +2=5, +2=7, +4=11>10 so day2 load=4, +1=5, +4=9. Days=2.
  2 ≤ 3 → works. hi=10.

lo=4, hi=10. mid=7.
  daysNeeded(7): 3, +2=5, +2=7, +4=11>7 day2: 4, +1=5, +4=9>7 day3: 4. Days=3.
  3 ≤ 3 → works. hi=7.

lo=4, hi=7. mid=5.
  daysNeeded(5): 3, +2=5, +2=7>5 day2: 2, +4=6>5 day3: 4, +1=5, +4=9>5 day4: 4. Days=4.
  4 > 3 → fails. lo=6.

lo=6, hi=7. mid=6.
  daysNeeded(6): 3, +2=5, +2=7>6 day2: 2, +4=6, +1=7>6 day3: 1, +4=5. Days=3.
  3 ≤ 3 → works. hi=6.

lo=6, hi=6. Return 6.
```

Answer: **6**. ✓ Matches my hand analysis at the top.

----------------------------------------

## Step 7: Name What We Used

This is **binary search on the answer** — applicable whenever the answer lives in a numeric range and a monotonic predicate tells us whether a candidate works. The same template fits Koko Eating Bananas, Split Array Largest Sum, Minimum Number of Days to Make Bouquets, and countless other interview problems.

The recipe:
1. Recognize that the answer is numeric and bounded.
2. Define `works(x)`: a boolean that's true for large x, false for small x (or vice versa).
3. Binary search for the boundary.
4. Implement `works` as an efficient check (often a greedy simulation).

----------------------------------------

## Step 8: Complexity

Time: binary search makes `O(log(sum - max))` iterations. Each runs the greedy simulation in O(n). Total: **O(n · log(sum - max))**.

Space: **O(1)**.

----------------------------------------

## Step 9: C++ Implementation

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
        if (daysNeeded(mid) <= days) hi = mid;
        else lo = mid + 1;
    }
    return lo;
}
```

Notes:
- `lo + (hi - lo) / 2` avoids integer overflow for very large inputs.
- The lambda captures everything by reference for cleanliness.
- When `lo == hi`, we exit with the minimum capacity that works.

----------------------------------------

## Step 10: Follow-up Questions

- **Fixed capacity, find minimum days.** Just run the greedy once — no binary search.
- **Packages can be re-ordered (no fixed order).** Different problem — NP-hard (bin packing).
- **Variable day lengths / different daily capacities.** Replace `load + w > cap` with `load + w > cap[d]`.
- **Maximum capacity that *fails* (instead of minimum that succeeds).** Return `lo - 1` at the end.
- **Online version — packages arrive over time.** Binary search doesn't apply directly; use a simulation with a priority queue.
