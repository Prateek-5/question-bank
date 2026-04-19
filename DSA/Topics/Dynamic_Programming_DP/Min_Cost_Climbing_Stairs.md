# Min Cost Climbing Stairs

**Problem Link:**
https://leetcode.com/problems/min-cost-climbing-stairs/

**Topic:**
Dynamic Programming (DP)

----------------------------------------

## Step 1: Read the Problem Twice — Really

There's a staircase. Each step has a cost `cost[i]`. You can start from either step 0 or step 1 **for free**. From any step you stand on, you pay that step's cost, then move 1 or 2 steps forward. The **top** is not the last step of the array — it's the position *just past* the array.

That last detail trips up almost everyone on their first read. Let me emphasize it. If `cost = [10, 15, 20]` has 3 entries, "the top" is position **3** (out of bounds). You don't need to pay the cost of the final array step unless you actually land on it.

----------------------------------------

## Step 2: Play With a Ridiculously Small Case

`cost = [1, 100]`. The top is position 2.

List all possible paths:
- Start at step 0 (free). Pay cost[0] = 1. Jump 2. Land at position 2 (top). Total: **1**.
- Start at step 0 (free). Pay cost[0] = 1. Jump 1. Land at step 1. Pay cost[1] = 100. Jump 1 or 2 (either overshoots or reaches top). Total: 1 + 100 = **101**.
- Start at step 1 (free). Pay cost[1] = 100. Jump 1. Land at top. Total: **100**.
- Start at step 1 (free). Pay cost[1] = 100. Jump 2. Overshoots — if overshooting is allowed as "reached the top," still 100.

Minimum: **1**.

Notice something interesting: the cheapest path doesn't even touch step 1. The free start at step 0 plus a 2-jump skips it entirely. This is what "free start" gives us — the ability to bypass one early step.

----------------------------------------

## Step 3: A Slightly Bigger Case

`cost = [10, 15, 20]`. Top is position 3.

Paths:
- Start 0, pay 10, jump 2 → top. Cost: 10.
- Start 0, pay 10, jump 1 → step 1, pay 15, jump 2 → top. Cost: 25.
- Start 0, pay 10, jump 1 → step 1, pay 15, jump 1 → step 2, pay 20, jump 1 or 2 → top. Cost: 45.
- Start 0, pay 10, jump 2 → step 2, pay 20, jump 1 → top. Cost: 30.
- Start 1, pay 15, jump 2 → top. Cost: 15.
- Start 1, pay 15, jump 1 → step 2, pay 20, jump 1 → top. Cost: 35.

Minimum: **10** — start 0, skip step 1.

Wait, the expected answer is 15? Let me re-check... `[10, 15, 20]`, pay 10 then jump 2 → land at index 2 (which costs 20, must pay) → jump to top. That's 30. Or pay 10, jump 1, pay 15, jump 2 → top. That's 25. Or start at 1, pay 15, jump 2 → top. That's 15. So minimum is **15** actually.

I confused myself! Let me re-read the rules: from a step, you **pay its cost then move**. Jumping 2 from step 0 lands you at step 2 — which is on the staircase still, not past it. You don't instantly reach the top. You'd have to *land* at position 3 to have reached the top.

So "jumping 2 from step 0" lands on step 2 — you have to pay that too before moving on. My correction: minimum is 15.

This confusion is actually useful. It forces me to be precise about what "reaching the top" means: the top is position n (if indices run 0..n-1), and we reach it only when we make a move that ends at position n or beyond.

----------------------------------------

## Step 4: The Key Realization From the Confusion

OK let me now rephrase: **"reaching the top" means being at position n after a jump from position n-1 or n-2 (which are the only positions that can jump to n)**. You don't pay anything at position n — there's no step there.

So to reach the top, your last move is either:
- From step n-1: pay cost[n-1], jump 1, arrive at n.
- From step n-2: pay cost[n-2], jump 2, arrive at n.

Total cost to reach the top = `min(costToReach(n-1) + cost[n-1], costToReach(n-2) + cost[n-2])`.

Now I need `costToReach(i)` — the minimum total paid to stand at step i (before paying cost[i] itself, just to arrive there).

- `costToReach(0) = 0` (free start).
- `costToReach(1) = 0` (also a free start).
- `costToReach(i)` for i ≥ 2: came from step i-1 (paying cost[i-1]) or step i-2 (paying cost[i-2]).

```
costToReach(i) = min(costToReach(i-1) + cost[i-1], costToReach(i-2) + cost[i-2])
```

That's the recurrence. And the final answer is `costToReach(n)`.

----------------------------------------

## Step 5: Verify on `[10, 15, 20]`

```
costToReach(0) = 0
costToReach(1) = 0
costToReach(2) = min(0 + 15, 0 + 10) = 10.
costToReach(3) = min(10 + 20, 0 + 15) = 15.
```

Answer: 15. ✓ Matches our enumeration above.

And on `[1, 100]`:
```
costToReach(0) = 0
costToReach(1) = 0
costToReach(2) = min(0 + 100, 0 + 1) = 1.
```

Answer: 1. ✓

The recurrence is right, and I now understand it from hand-enumeration rather than blind formula.

----------------------------------------

## Step 6: Only Two Things Matter at Each Step

Look at the recurrence: `costToReach(i)` only depends on `costToReach(i-1)` and `costToReach(i-2)`. Nothing earlier. So we don't need a full array — just two variables rolling forward.

```
prev2 = 0     # costToReach(0)
prev1 = 0     # costToReach(1)
for i from 2 to n:
    cur = min(prev1 + cost[i-1], prev2 + cost[i-2])
    prev2 = prev1
    prev1 = cur
return prev1
```

----------------------------------------

## Step 7: What We Just Derived

If you squint, the recurrence `f(i) = min(f(i-1) + a, f(i-2) + b)` looks like the Climbing Stairs Fibonacci cousin — but with weighted edges. Each "jump" has a cost, and we're finding the cheapest way to reach the end.

We didn't start with "this is a DP problem." We hand-traced paths, got confused about rules, corrected ourselves, and arrived at a recurrence by asking "what's the last move?" That question is the entire trick — it reduces the global optimization to a small local choice.

----------------------------------------

## Step 8: Complexity

Time: one pass, **O(n)**.
Space: two rolling variables, **O(1)**.

----------------------------------------

## Step 9: C++ Implementation

```cpp
int minCostClimbingStairs(vector<int>& cost) {
    int n = cost.size();
    int prev2 = 0, prev1 = 0;
    for (int i = 2; i <= n; ++i) {
        int cur = min(prev1 + cost[i - 1], prev2 + cost[i - 2]);
        prev2 = prev1;
        prev1 = cur;
    }
    return prev1;
}
```

Reading it carefully: when `i` equals `n` (the top), we compute the final answer. The loop runs exactly `n - 1` times. `prev1` holds the value of `costToReach(i-1)` through each iteration, and `prev2` is the one before that.

----------------------------------------

## Step 10: Follow-up Questions

- **Steps of 1, 2, or 3 allowed.** Recurrence becomes `f(i) = min(f(i-1) + cost[i-1], f(i-2) + cost[i-2], f(i-3) + cost[i-3])`. Roll three variables instead of two.
- **Must stop at a specific "checkpoint" step.** Split into sub-problems: minimum cost from start to checkpoint, plus checkpoint to top.
- **Variable step sizes (can take any of `{1, 2, ..., k}` steps).** Recurrence widens to `k` terms — for large `k`, a sliding-window minimum keeps it O(n).
- **Recover the actual path.** Record which predecessor won at each step; walk back from position `n`.
- **Some steps are broken (can't land on them).** Set `cost[broken] = infinity`. The min-recurrence naturally avoids them.
