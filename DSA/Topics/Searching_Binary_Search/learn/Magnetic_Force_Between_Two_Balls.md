# Magnetic Force Between Two Balls — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Magnetic_Force_Between_Two_Balls.md`](../Magnetic_Force_Between_Two_Balls.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/magnetic-force-between-two-balls/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/magnetic-force-between-two-balls/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~20 minutes. **This is the "maximize the minimum" variant of binary search on the answer.** Subtle twist: we want the LARGEST feasible value, not the smallest — flips the loop pattern and introduces the "upper-mid" trick. Same pattern is called "Aggressive Cows" in competitive programming. **Read [`Capacity_To_Ship_Packages_Within_D_Days.md`](./Capacity_To_Ship_Packages_Within_D_Days.md) first.**

**Map of this file (10 short sections):**

1. Read the problem
2. The brute force
3. The pivot — binary search the distance
4. The feasibility check (greedy placement)
5. Why we need the "upper-mid" trick
6. The algorithm
7. Code
8. Trace it
9. Common pitfalls
10. The shape — "maximize the minimum" family

---

## 1. Read the problem

You have `n` baskets at integer positions on a 1D line (given in `position` array). You must place `m` balls (one per basket) into `m` of the baskets such that the **minimum pairwise distance** between any two balls is **MAXIMIZED**.

Return that maximum-minimum distance.

**Required:** the algorithm should run efficiently — O(n log(max_pos)).

**Examples:**

- `position = [1, 2, 3, 4, 7]`, `m = 3`. Best placement: positions 1, 4, 7. Min pairwise gap: min(4-1, 7-4) = 3. Answer: **3**.
- `position = [5, 4, 3, 2, 1, 1000000000]`, `m = 2`. Place at 1 and 10^9. Distance: ~10^9. Answer: **999999999**.

> **Mini-refresher: "max-min" optimization.**
>
> "Maximize the minimum" optimizations ask: choose a configuration such that the WORST pairwise/element value is as large as possible. The OBJECTIVE is the smallest value in the configuration; we maximize that.
>
> Other framings:
> - "Maximum bottleneck."
> - "Fairest distribution."
> - "Largest possible safety margin."
>
> Common technique: binary-search the answer. For each candidate `d`, check if a configuration ACHIEVING at least `d` exists.

---

## 2. The brute force

Try every subset of `m` baskets. For each, compute the min pairwise distance. Track the maximum. Combinatorial: `C(n, m)` subsets — exponential. TLE.

Need a structural approach.

---

## 3. The pivot — binary search the distance

The numeric ANSWER is the maximum-minimum distance `d`. Binary-search the value of `d`.

For a candidate distance `d`, define the predicate:

> **`canPlace(d)` = "can we place m balls into the baskets such that every pair is at distance ≥ d?"**

**Monotonicity:** if we can place m balls with gap ≥ d, we can also do it with gap ≥ d' for any d' ≤ d (use the same placement; gaps still ≥ d' ≤ d).

So `canPlace(d)` is monotonic:
- Small d: TRUE (easy to spread balls apart).
- Large d: FALSE (not enough room).
- One boundary where it flips from TRUE to FALSE.

**We want the LARGEST d where `canPlace(d) = TRUE`** — the boundary distance.

---

## 4. The feasibility check (greedy placement)

For a candidate `d`, can we place m balls with all gaps ≥ d?

**Greedy strategy:** place the first ball at the leftmost basket. Then place each subsequent ball at the leftmost basket that's at least `d` away from the previous ball.

```
sort(position)
canPlace(d):
    count = 1
    last = position[0]
    for i in 1..n-1:
        if position[i] - last >= d:
            count += 1
            last = position[i]
            if count == m: return True
    return False
```

> **Mini-refresher: why greedy works.**
>
> **Exchange argument:** suppose an optimal placement uses balls at positions `p_1 < p_2 < ... < p_m`. We claim the greedy placement `g_1 = position[0], g_2 = leftmost ≥ g_1 + d, ...` ALSO places `m` balls.
>
> Why? At each step, the greedy places a ball at the EARLIEST possible position. So `g_i <= p_i` for all i. If optimal can place ball `i+1` after `p_i` with gap ≥ d, greedy (which has `g_i ≤ p_i`) can ALSO place it (the available positions form a SUPERSET of optimal's).
>
> By induction, greedy places at least as many balls as optimal — i.e., m. Done.

Sorting is needed so positions are in order — otherwise greedy can't pick "leftmost" sensibly.

---

## 5. Why we need the "upper-mid" trick

We're searching for the LARGEST feasible `d`. This means:

- If `canPlace(mid) = TRUE`: `d = mid` works. Try LARGER. `lo = mid`.
- If `canPlace(mid) = FALSE`: `mid` doesn't work. Try SMALLER. `hi = mid - 1`.

**Subtle bug:** with `mid = (lo + hi) / 2` (regular floor division), when `lo == 2, hi == 3`, mid is `2`. If `canPlace(2) = TRUE`, we set `lo = mid = 2`. INFINITE LOOP — we never progress.

**Fix:** use **upper-mid**: `mid = (lo + hi + 1) / 2`. Now for `lo = 2, hi = 3`, mid = `3`. If feasible, `lo = 3`. Loop exits (`lo == hi`).

```
Regular mid: mid = lo + (hi - lo) / 2          # rounds DOWN
Upper mid:    mid = lo + (hi - lo + 1) / 2      # rounds UP
```

> **Mini-refresher: which mid to use, succinctly.**
>
> - "Find SMALLEST feasible" → `lo = mid + 1`, `hi = mid`. Use regular mid.
> - "Find LARGEST feasible" → `lo = mid`, `hi = mid - 1`. Use UPPER mid.
>
> The choice prevents infinite loops when `lo` and `hi` are adjacent.

---

## 6. The algorithm

```
sort(position)
lo = 1                                    # smallest possible distance
hi = position[n-1] - position[0]          # largest possible distance

while lo < hi:
    mid = lo + (hi - lo + 1) // 2         # upper-mid
    if canPlace(mid):
        lo = mid                          # mid works; try larger
    else:
        hi = mid - 1                      # mid fails; try smaller

return lo
```

When `lo == hi`, that's the largest feasible distance.

---

## 7. Code

**C++:**

```cpp
class Solution {
    bool canPlace(vector<int>& position, int m, int d) {
        int count = 1;
        int last = position[0];
        for (int i = 1; i < (int)position.size(); ++i) {
            if (position[i] - last >= d) {
                count++;
                last = position[i];
                if (count >= m) return true;
            }
        }
        return false;
    }

public:
    int maxDistance(vector<int>& position, int m) {
        sort(position.begin(), position.end());
        int lo = 1;
        int hi = position.back() - position.front();

        while (lo < hi) {
            int mid = lo + (hi - lo + 1) / 2;     // upper-mid
            if (canPlace(position, m, mid)) lo = mid;
            else hi = mid - 1;
        }
        return lo;
    }
};
```

**Python:**

```python
def maxDistance(position, m):
    position.sort()
    n = len(position)

    def can_place(d):
        count = 1
        last = position[0]
        for i in range(1, n):
            if position[i] - last >= d:
                count += 1
                last = position[i]
                if count >= m:
                    return True
        return False

    lo, hi = 1, position[-1] - position[0]
    while lo < hi:
        mid = (lo + hi + 1) // 2     # upper-mid
        if can_place(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo
```

Complexity: **O(n log n + n log(max_pos))** time, **O(1)** space (besides sort).

---

## 8. Trace it

**`position = [1, 2, 3, 4, 7]`, `m = 3`:**

Sorted: already. lo = 1, hi = 7 - 1 = 6.

```
Iter 1: mid = (1+6+1)/2 = 4. canPlace(4)?
  Place at 1. i=1: 2-1=1<4. i=2: 3-1=2<4. i=3: 4-1=3<4. i=4: 7-1=6>=4 → place. count=2. End.
  count=2, m=3 → FAIL. hi = 3.

Iter 2: lo=1, hi=3. mid = (1+3+1)/2 = 2. canPlace(2)?
  Place at 1. i=1: 2-1=1<2. i=2: 3-1=2>=2 → place. count=2, last=3.
  i=3: 4-3=1<2. i=4: 7-3=4>=2 → place. count=3 → TRUE.
  lo = 2.

Iter 3: lo=2, hi=3. mid = (2+3+1)/2 = 3. canPlace(3)?
  Place at 1. i=1: 2-1=1<3. i=2: 3-1=2<3. i=3: 4-1=3>=3 → place. count=2, last=4.
  i=4: 7-4=3>=3 → place. count=3 → TRUE.
  lo = 3.

Iter 4: lo=3, hi=3. EXIT.

Return 3.  ✓
```

---

## 9. Common pitfalls

1. **Forgetting to sort.** Greedy placement REQUIRES positions in increasing order. Without sort, "leftmost" doesn't mean anything.

2. **Using regular mid instead of upper-mid.** Infinite loop when `lo + 1 == hi`. Always use upper-mid for "find largest feasible" pattern.

3. **Incorrect feasibility direction.** This problem WANTS max-min, so feasibility is "can place ≥ m balls with gap ≥ d." Misreading this as "can place ≤ m" or "≤ d" inverts everything.

4. **Counting starts wrong.** First ball is placed at the leftmost basket. count = 1 (not 0).

5. **Comparing to `m` vs `>= m`.** When count REACHES m, we can stop early — `>= m` is the correct condition.

6. **Using `>` instead of `>=` in the gap check.** Gap of EXACTLY d is acceptable (gap ≥ d means including d).

7. **Search bounds.** Lower bound: 1 (smallest distance that makes sense). Upper bound: `max - min` (max possible distance between any two baskets). Using lower bound 0 or upper bound `max + 1` causes off-by-one.

8. **Trying DP.** Possible but more complex. Binary search on answer is THE standard approach.

9. **Missing the monotonicity argument.** If you can't articulate WHY feasibility is monotonic in d, you don't have the right mental model. Recheck Section 3.

10. **Assuming "min pairwise distance" means ALL pairs.** For sorted positions, the minimum pairwise distance equals the minimum ADJACENT distance (any non-adjacent pair has distance ≥ the smaller intermediate). So you only need to enforce adjacent gaps ≥ d.

---

## 10. The shape — "maximize the minimum" family

The pattern: **maximize (minimize) some bottleneck value across a configuration**.

| Problem | What we maximize | Feasibility |
|---|---|---|
| **This problem** | min pairwise distance | can place m balls with gap ≥ d |
| Aggressive Cows | min distance between cows | can place k cows with gap ≥ d |
| Split Array Largest Sum (inverse: minimize the max) | max subarray sum | can split into ≤ m subarrays each ≤ max |
| Painter's Partition | max time any painter spends | feasibility(time) |
| Path with Minimum Effort (LC #1631) | min max-edge along the path | reachable with edge cap ≤ x |
| Maximum Average Subarray II | max average of contiguous subarray of length ≥ k | feasibility(avg) |

**Pattern to internalize:**

> "Maximize-the-minimum problems: binary-search the answer, with predicate 'can we achieve a configuration where the bottleneck is ≥ d?' Use UPPER-MID and `lo = mid, hi = mid - 1` to find the largest feasible value."

When the problem says "fairest" / "max smallest" / "min largest" — this is the pattern.

---

> **Self-check — the question to ask next time.**
>
> When you face "maximize the minimum X" or "minimize the maximum X," ask:
>
> > **"Can I binary-search the value of X? For each candidate, can I write an O(n) feasibility check that's monotonic in X?"**
>
> If yes, you've turned the optimization into binary search on the answer.

---

## Cross-references

- **Reference card (post-mastery):** [`../Magnetic_Force_Between_Two_Balls.md`](../Magnetic_Force_Between_Two_Balls.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Capacity_To_Ship_Packages_Within_D_Days.md`](./Capacity_To_Ship_Packages_Within_D_Days.md) — minimize the max, same pattern.
  - Coming next: [`Smallest_Good_Base.md`](./Smallest_Good_Base.md) — binary search with a math twist.
