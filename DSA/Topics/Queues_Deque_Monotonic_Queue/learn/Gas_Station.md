# Gas Station — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Gas_Station.md`](../Gas_Station.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/gas-station/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/gas-station/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **A beautiful "skip-the-failures" greedy problem.** The lesson: **if you fail at station i starting from s, ALL stations between s and i also fail — so jump straight to i+1 as the next candidate. O(n) one pass with O(1) space.** This "skip the impossible prefix" trick reappears in Maximum Subarray (Kadane's) and many greedy circuit problems.

**Map of this file (11 sections):**

1. Read the problem
2. The brute force
3. The necessary condition — total gas vs total cost
4. The skip-failures insight
5. Why skipping all the way works
6. The algorithm
7. Code
8. Trace it
9. Why a single pass suffices (no wrap-around check)
10. Common pitfalls
11. The shape — Kadane-style reset

---

## 1. Read the problem

There are `n` gas stations arranged in a **circle**. At station `i`:
- `gas[i]` = liters of gas available.
- `cost[i]` = liters of gas needed to travel from station `i` to station `i + 1` (next station, with wrap-around at the end).

Starting with an empty tank at some station, return the index of the starting station that lets you complete the full circuit. If impossible, return `-1`. The answer is **unique** if it exists.

**Examples:**

- `gas = [1, 2, 3, 4, 5]`, `cost = [3, 4, 5, 1, 2]` → **3**. (Start at station 3.)
- `gas = [2, 3, 4]`, `cost = [3, 4, 3]` → **-1**. (Total gas 9 < total cost 10.)

---

## 2. The brute force

For each candidate start s, simulate the full circuit. Check if the tank ever goes negative.

```
for s in 0..n-1:
    tank = 0
    feasible = True
    for offset in 0..n-1:
        i = (s + offset) % n
        tank += gas[i] - cost[i]
        if tank < 0:
            feasible = False
            break
    if feasible:
        return s
return -1
```

O(n²). For n = 10^5, that's 10^10 ops — TLE.

We need O(n). Greedy is the path.

---

## 3. The necessary condition — total gas vs total cost

> **Mini-refresher: total gas vs total cost.**
>
> If `sum(gas) < sum(cost)`, the total gas available across the whole circuit is less than the total cost. Starting ANYWHERE, you'd run out before completing the loop.
>
> Conversely, **if `sum(gas) >= sum(cost)`, a valid starting station ALWAYS exists.** (Proof in Section 5.)
>
> So step 1: compute the total. If negative, return -1. Otherwise, find the start.

This necessary condition is also sufficient — once you accept that fact, finding the start becomes easier.

---

## 4. The skip-failures insight

Walk through stations 0, 1, 2, ... in order. Maintain:
- `total`: cumulative net (gas - cost) across all stations seen.
- `tank`: cumulative net since the current candidate start.
- `start`: the current candidate starting station.

When does `tank` go NEGATIVE at station i?

It means: starting from `start`, we couldn't make it past station i (the tank ran dry).

**Claim:** if we failed at station i starting from `start`, then **ANY** station between `start` and i (inclusive) also fails as a starting point.

So we don't need to try them. Skip directly to `i + 1` as the next candidate.

> **Mini-refresher: why skipping works.**
>
> Suppose starting at `start` failed at i (tank went negative after i). Consider any intermediate candidate s' (where `start < s' ≤ i`).
>
> - The cumulative net from `start` to `s' - 1` (just before s') is `≥ 0` (else we would have already failed and reset before reaching s').
> - So the cumulative net from `s'` to i = (cumulative `start..i`) - (cumulative `start..s'-1`). The first is NEGATIVE (we failed); the second is `≥ 0`. So the difference is at most as negative as the first, i.e., NEGATIVE.
>
> So `s'` also fails before or at i. Every intermediate start is doomed. Skip to `i + 1`.

This is the key insight that turns O(n²) into O(n).

---

## 5. Why skipping all the way works

The algorithm finds A start. But how do we know it finds THE start (or any valid start)?

> **Claim:** if `total ≥ 0`, the `start` found by the algorithm is a valid starting point.

**Proof sketch:** consider the running prefix sums `p(i) = sum of (gas[j] - cost[j]) for j in 0..i`. Let `min_i` be the index where `p` is minimum (most negative).

The candidate start that the algorithm settles on is `min_i + 1` (mod n). Starting from `min_i + 1`, the running tank relative to this restart equals `p(j) - p(min_i)`, which is ALWAYS ≥ 0 (since `min_i` is the minimum).

So no station after `min_i + 1` causes a deficit; we complete the loop. ✓

The algorithm finds this implicitly: every reset advances `start` past a "bad segment." The LAST reset lands `start` right after the minimum prefix.

---

## 6. The algorithm

```
total = 0
tank = 0
start = 0

for i in 0..n-1:
    diff = gas[i] - cost[i]
    total += diff
    tank += diff
    if tank < 0:
        start = i + 1
        tank = 0

return start if total >= 0 else -1
```

**O(n) time, O(1) space.** Single pass.

---

## 7. Code

**C++:**

```cpp
int canCompleteCircuit(vector<int>& gas, vector<int>& cost) {
    int total = 0, tank = 0, start = 0;
    for (int i = 0; i < (int)gas.size(); ++i) {
        int diff = gas[i] - cost[i];
        total += diff;
        tank += diff;
        if (tank < 0) {
            start = i + 1;
            tank = 0;
        }
    }
    return total >= 0 ? start : -1;
}
```

**Python:**

```python
def canCompleteCircuit(gas, cost):
    total = 0
    tank = 0
    start = 0
    for i in range(len(gas)):
        diff = gas[i] - cost[i]
        total += diff
        tank += diff
        if tank < 0:
            start = i + 1
            tank = 0
    return start if total >= 0 else -1
```

**JavaScript:**

```javascript
function canCompleteCircuit(gas, cost) {
    let total = 0, tank = 0, start = 0;
    for (let i = 0; i < gas.length; i++) {
        const diff = gas[i] - cost[i];
        total += diff;
        tank += diff;
        if (tank < 0) {
            start = i + 1;
            tank = 0;
        }
    }
    return total >= 0 ? start : -1;
}
```

Complexity: **O(n) time, O(1) space.**

---

## 8. Trace it

**`gas = [1, 2, 3, 4, 5]`, `cost = [3, 4, 5, 1, 2]`.**

diffs = `[-2, -2, -2, 3, 3]`. sum = 0.

```
i=0: diff=-2. total=-2. tank=-2. tank<0 → start=1, tank=0.
i=1: diff=-2. total=-4. tank=-2. tank<0 → start=2, tank=0.
i=2: diff=-2. total=-6. tank=-2. tank<0 → start=3, tank=0.
i=3: diff=3.  total=-3. tank=3.  OK.
i=4: diff=3.  total=0.  tank=6.  OK.

total = 0 ≥ 0. Return start = 3.  ✓
```

Verify by simulation from station 3:
- Start at 3: tank = 0. Pick up gas[3]=4 → tank=4.
- Drive to 4: cost 1 → tank=3.
- Pick up 5 → tank=8.
- Drive to 0: cost 2 → tank=6.
- Pick up 1 → tank=7.
- Drive to 1: cost 3 → tank=4.
- Pick up 2 → tank=6.
- Drive to 2: cost 4 → tank=2.
- Pick up 3 → tank=5.
- Drive to 3 (wrap): cost 5 → tank=0. Back at start. ✓

---

## 9. Why a single pass suffices (no wrap-around check)

After finding `start`, do we need to SIMULATE the wrap-around from `start` through n-1 back to `start - 1`?

**No.** The proof in Section 5 guarantees that if `total ≥ 0`, the algorithm's `start` is valid. No verification needed.

> **Mini-refresher: the proof's crux.**
>
> - The algorithm's `start` is `min_prefix_index + 1` (where the running prefix sum is minimum).
> - From this start, every subsequent partial sum is `>= 0`.
> - Total = `0` (or positive) means the loop closes.
>
> No deficit can occur on the rest of the trip. One pass is enough.

---

## 10. Common pitfalls

1. **Trying brute-force simulation.** O(n²); TLE for large n.

2. **Skipping just one step on failure.** Skip ALL THE WAY to `i + 1` after a tank deficit. Every intermediate start is also bad.

3. **Forgetting the `total >= 0` global check.** Without it, you'd return a `start` even when no valid start exists.

4. **Wrap-around simulation.** Don't simulate it. The math handles it.

5. **Off-by-one on `start = i + 1`.** If `i == n - 1` and tank goes negative, `start = n` is out of range. But then `total < 0`, so we'd return -1 anyway.

6. **Using two passes (one for total, one for start).** Works but can be combined into a single pass.

7. **Confusing "candidate start" with "global start."** The candidate may update multiple times; only the FINAL value is checked.

---

## 11. The shape — Kadane-style reset

The pattern: **when scanning a sequence with a "running budget," and the budget goes negative, RESET past the failure point and continue.**

| Problem | "Budget" | Reset rule |
|---|---|---|
| **This problem** | tank (gas - cost cumulative) | reset start to i + 1 when tank < 0 |
| Maximum Subarray (Kadane's) | running sum | reset to 0 when sum < 0 |
| Jump Game | farthest reachable index | step-by-step reachability |
| Best Time to Buy/Sell Stock | running minimum buy price | update min on new low |
| Find First Positive Sum Subarray | cumulative sum | reset when negative |

**Pattern to internalize:**

> "When you maintain a running sum/budget across a sequence, and the rules allow you to 'restart' on a failure, doing so is often O(n) instead of O(n²) brute force."

The skip-failures move is the heart of Kadane's algorithm. Once you see it here, you'll recognize it everywhere.

---

> **Self-check — the question to ask next time.**
>
> When you face a "find starting point for a circular/linear traversal" problem, ask:
>
> > **"If I fail starting from s and again at position i, can I PROVE that all intermediate starts also fail? If yes, skip directly to i + 1 — O(n) instead of O(n²)."**
>
> If yes, you've got the Kadane-style greedy.

---

## Cross-references

- **Reference card (post-mastery):** [`../Gas_Station.md`](../Gas_Station.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Implement_Queue_using_Stacks.md`](./Implement_Queue_using_Stacks.md), [`Implement_Stack_using_Queues.md`](./Implement_Stack_using_Queues.md) — design problems.
  - Coming next: Longest_Valid_Parentheses, Sliding_Window_Maximum.
