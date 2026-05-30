# Memoization / DP Basics — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Memoization_DP_Basics.md`](../Memoization_DP_Basics.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/tag/dynamic-programming/" target="_blank" rel="noopener noreferrer">https://leetcode.com/tag/dynamic-programming/</a>

---

## How to use this file

Paced for someone seeing this for the first time. Reading time: ~16 minutes. **The lesson: DP applies when (a) subproblems overlap AND (b) optimal substructure holds. TOP-DOWN = recursion + memo; BOTTOM-UP = fill a table. The FIVE QUESTIONS (state, base, recurrence, order, answer) get you to any DP.**

**Map of this file (7 sections):**

1. Why DP exists
2. Top-down vs bottom-up
3. The two requirements
4. The five-question checklist
5. Walkthrough — Fibonacci
6. Walkthrough — LCS
7. The shape — DP fundamentals

---

## 1. Why DP exists

Naive recursion on certain problems creates EXPONENTIAL re-computation of the same subproblems.

Classic case: Fibonacci. `fib(n) = fib(n-1) + fib(n-2)` recurses on overlapping subproblems. fib(40) takes BILLIONS of calls without caching, but only ~40 distinct subproblems exist.

DP eliminates the redundancy.

---

## 2. Top-down vs bottom-up

> **Mini-refresher: same idea, two implementations.**
>
> **Top-down (memoization):** recursive function + cache. Calls only the states actually needed.
>
> ```
> memo = {}
> def f(state):
>     if state in memo: return memo[state]
>     memo[state] = combine recursive calls to subproblems
>     return memo[state]
> ```
>
> **Bottom-up (tabulation):** iterate through states in dependency order; fill the table.
>
> ```
> for state in topological order:
>     table[state] = combine table[earlier states]
> return table[goal]
> ```

Both: same time complexity. Bottom-up usually slightly faster (no recursion overhead); supports space optimization (rolling arrays).

---

## 3. The two requirements

> **Mini-refresher: DP applies iff:**
>
> 1. **Overlapping subproblems.** Same subproblem appears multiple times. (Without this, caching does nothing.)
> 2. **Optimal substructure.** The optimal answer to the whole is built from optimal answers to subproblems. (Without this, the recurrence is wrong.)
>
> Most "find best X" problems on combinatorial structures have both. Some (e.g., longest simple path in general graphs) lack optimal substructure → DP can't help directly.

---

## 4. The five-question checklist

To derive any DP, answer:

1. **State:** what parameters identify a subproblem?
2. **Base:** smallest state with a trivial answer.
3. **Recurrence:** how does a state combine smaller states?
4. **Fill order:** what topological ordering ensures dependencies are ready?
5. **Answer:** which state holds the final result?

If you can answer all five, you have a DP.

---

## 5. Walkthrough — Fibonacci

- **State:** n.
- **Base:** fib(0) = 0, fib(1) = 1.
- **Recurrence:** fib(n) = fib(n-1) + fib(n-2).
- **Order:** increasing n.
- **Answer:** fib(n).

Bottom-up:
```
dp[0] = 0, dp[1] = 1
for i in 2..n: dp[i] = dp[i-1] + dp[i-2]
return dp[n]
```

Space-optimized with two rolling variables → O(1) space.

---

## 6. Walkthrough — LCS

- **State:** (i, j) — first i chars of s, first j chars of t.
- **Base:** dp[0][j] = dp[i][0] = 0 (empty prefix).
- **Recurrence:**
  - If s[i-1] == t[j-1]: dp[i][j] = 1 + dp[i-1][j-1].
  - Else: dp[i][j] = max(dp[i-1][j], dp[i][j-1]).
- **Order:** i and j ascending.
- **Answer:** dp[|s|][|t|].

O(n · m) time and space; reducible to O(min(n, m)) space with row rolling.

---

## 7. The shape — DP fundamentals

Common DP families:

| Family | Examples |
|---|---|
| **Linear 1D** | Fibonacci, Climbing Stairs, Maximum Subarray |
| **Grid 2D** | Unique Paths, Edit Distance, LCS |
| **Interval** | Matrix Chain, Burst Balloons, Palindromic Subseq |
| **Knapsack / Subset** | 0/1 knapsack, partition, target sum |
| **Bitmask / Subset enumeration** | TSP, assignment, Subsets |
| **Tree DP** | rooted tree recurrences |
| **Digit DP** | counts of numbers with digit constraints |
| **State-machine DP** | stock trading with cooldown |

**Patterns to internalize:**

> "DP = identify the state, the recurrence, the base, the fill order, the answer. Top-down for sparsity / easier derivation; bottom-up for speed and space optimization."

---

## Common pitfalls

1. **State is too small** → recurrence doesn't close. Add another dimension.
2. **Off-by-one in indexing.** When state is "first i chars of s," s[i-1] is the LAST char of that prefix.
3. **Forgetting memoization.** Top-down without memo = exponential.
4. **Wrong fill order in bottom-up.** Dependencies must be ready before reading.
5. **Brute-forcing problems that don't need DP.** If brute force is O(n), DP is overengineering.

---

> **Self-check — the question to ask next time.**
>
> When approaching a new problem that smells like DP:
>
> > **"What's the STATE? What's the BASE? What's the RECURRENCE? What's the FILL ORDER? Where's the ANSWER? — Five questions. If I can answer all five, I have a DP."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Memoization_DP_Basics.md`](../Memoization_DP_Basics.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Climbing_Stairs.md`](../../Dynamic_Programming_DP/learn/Climbing_Stairs.md), [`Longest_Common_Subsequence.md`](../../Dynamic_Programming_DP/learn/Longest_Common_Subsequence.md), [`Edit_Distance.md`](../../Dynamic_Programming_DP/learn/Edit_Distance.md).
  - Coming next: [`Implement_Rand10_Using_Rand7.md`](./Implement_Rand10_Using_Rand7.md).
