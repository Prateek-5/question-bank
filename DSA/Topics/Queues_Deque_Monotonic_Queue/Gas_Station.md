# Gas Station

**Problem Link:**
https://leetcode.com/problems/gas-station/

**Topic:**
Queues / Deque / Monotonic Queue

----------------------------------------

## Step 1: The Setup

There are `n` gas stations arranged in a circle. At station i:
- `gas[i]` units of gas can be acquired.
- `cost[i]` units are needed to travel from station i to station i+1.

Starting with an empty tank at some station, can you travel around the whole circle once, never running out of gas mid-way?

If yes, return the starting station's index (the unique valid one, if one exists). If no, return -1.

Example: `gas = [1, 2, 3, 4, 5]`, `cost = [3, 4, 5, 1, 2]`.
- Try starting at 3: tank starts 0, picks up 4. Drive to 4 (cost 1), tank = 3. Pick up 5, tank = 8. Drive to 0 (cost 2), tank = 6. Pick up 1, tank = 7. Drive to 1 (cost 3), tank = 4. Pick up 2, tank = 6. Drive to 2 (cost 4), tank = 2. Pick up 3, tank = 5. Drive to 3 (cost 5), tank = 0. Back to start with 0 left — success!
- Answer: **3**.

Example: `gas = [2, 3, 4]`, `cost = [3, 4, 3]`. Total gas = 9, total cost = 10. Total gas < total cost. **Impossible** from anywhere. Return -1.

----------------------------------------

## Step 2: Necessary Condition — Total Gas ≥ Total Cost

If sum(gas) < sum(cost), we can never make a full loop from any starting point (we'd run out).

Contrapositive: if sum(gas) ≥ sum(cost), it turns out a valid start **always exists**. (Not obvious yet — we'll prove it below.)

So step 1 of the algorithm: compute the total. If total < 0, return -1. Otherwise, find the start.

----------------------------------------

## Step 3: Key Observation — When We Can't Extend, Restart After

Walk stations 0, 1, 2, ..., tracking the running tank. At each station i, net gain = `gas[i] - cost[i]`. Add it to a "current tank" counter.

If at any point `current_tank < 0`, it means: starting from our current candidate start, we failed to reach station i+1. So the start must be **after** i — try i+1 as the next candidate, reset tank to 0.

Why can we jump all the way to i+1? Because starting from any station between the current start and i also fails. (They all pass through the same deficit at station i, since the sum along the path only decreases — actually let me think again.)

Let me justify: suppose our current start is s, and tank went negative at station i (meaning `sum(gas[s..i] - cost[s..i]) < 0`). Consider any start s' with `s < s' ≤ i`. The tank from s' to i equals `sum(gas[s'..i] - cost[s'..i])`. The route s → s' → ... → i has non-negative prefix sums up to just before s' (else we'd have reset earlier). Specifically, `sum(gas[s..s'-1] - cost[s..s'-1]) ≥ 0`. So:

```
sum(gas[s'..i] - cost[s'..i]) = sum(gas[s..i] - cost[s..i]) - sum(gas[s..s'-1] - cost[s..s'-1])
                             ≤ sum(gas[s..i] - cost[s..i]) < 0
```

So starting at s' also fails before or at i. **Every station between s and i is a bad start.** We can safely skip to i+1.

----------------------------------------

## Step 4: Algorithm (O(n), Single Pass)

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

One pass. O(n) time, O(1) space.

----------------------------------------

## Step 5: Trace on `gas = [1, 2, 3, 4, 5]`, `cost = [3, 4, 5, 1, 2]`

diff = [-2, -2, -2, 3, 3]. total ends at 0 (≥ 0, so answer exists).

```
i=0: diff=-2. total=-2. tank=-2. tank<0. start=1, tank=0.
i=1: diff=-2. total=-4. tank=-2. tank<0. start=2, tank=0.
i=2: diff=-2. total=-6. tank=-2. tank<0. start=3, tank=0.
i=3: diff=3. total=-3. tank=3. OK.
i=4: diff=3. total=0. tank=6. OK.
```

total = 0 ≥ 0. Return **start = 3**. ✓

----------------------------------------

## Step 6: Why the Existence Claim?

Claim: if `sum(gas) ≥ sum(cost)`, a valid start always exists.

Proof sketch: consider the running prefix sum `p(i) = sum(diff[0..i])`. Let `min_i` be the index where `p` is minimized (most negative). Starting from `min_i + 1` (modulo n), the running tank is always ≥ 0 — because any subsequent prefix, relative to the reset at min_i + 1, equals `p(j) - p(min_i) ≥ 0`.

So `start = (min_i + 1) mod n` always works when total ≥ 0. The algorithm finds this start implicitly: every time tank goes negative, we advance past a "bad segment," and the last reset sits right after the minimum prefix — which is the correct start.

----------------------------------------

## Step 7: Why No Need to Simulate Wrap-Around?

One might worry: after finding candidate `start`, do we need to verify the full loop from `start` through n-1 and back to `start - 1`?

**No.** The proof above guarantees: if total ≥ 0 and we find a start via the algorithm, that start completes the full loop without wrap-around issues. A single pass is enough.

----------------------------------------

## Step 8: Name It

**Greedy + prefix-minimum argument.** Also called the "Kadane-style reset" idea: maintain a running tally; reset on negative.

Related problems:
- Maximum Subarray (Kadane's algorithm) — similar reset-on-negative structure.
- Jump Game (greedy reachability).
- Circular array problems in general often benefit from doubling the array or prefix-sum reasoning.

----------------------------------------

## Step 9: Complexity

Time: **O(n)**.
Space: **O(1)**.

Cannot do better — we must at least read every (gas, cost) pair.

----------------------------------------

## Step 10: C++ Implementation

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

Three variables: total (global feasibility), tank (current trip's fuel), start (current candidate).

----------------------------------------

## Step 11: Follow-up Questions

- **Multiple valid starts?** The problem states "unique if exists." If multiple existed, any is acceptable — but typically constraints ensure uniqueness or call for the smallest index.
- **Return all valid starts.** Simulate from each candidate (O(n²) brute force) or use the prefix-min reasoning to find all tied minima.
- **Return the minimum starting tank capacity.** Track the minimum running prefix; required capacity = -min_prefix.
- **Real-world analog.** Route planning with refueling constraints.
- **Why one pass suffices.** The skip-to-i+1 move never leaves behind a valid start (proven above), so we never need to re-examine earlier indices.
- **Variant: cost can be paid later (credit).** Changes feasibility logic; no longer a single-pass greedy.
