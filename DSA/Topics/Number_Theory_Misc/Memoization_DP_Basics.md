# Memoization / DP Basics

**Problem Link:**
https://leetcode.com/tag/dynamic-programming/

**Topic:**
Number Theory / Misc (concepts primer)

----------------------------------------

## Step 1: Why Dynamic Programming Exists

Some recursive problems have **overlapping subproblems** — the same sub-computation is requested many times. Without caching, this leads to exponential blowup.

Example: Fibonacci. `fib(n) = fib(n-1) + fib(n-2)`. Naive recursion calls `fib(5)` via two branches that both eventually hit `fib(2)`, `fib(1)`, ... many times. For `fib(40)`, we do ~1 billion redundant calls.

**DP's promise**: compute each subproblem **once**; reuse the answer.

----------------------------------------

## Step 2: Two Flavors of DP

**Top-down (memoization):** recursive function with a cache. Call it; it computes or returns cached.

```
memo = {}
def f(state):
    if state in memo: return memo[state]
    compute using recursive calls to f(other_states)
    memo[state] = result
    return result
```

**Bottom-up (tabulation):** fill a table in the right order, so every value is ready when needed.

```
table = array sized over state space
for state in some_topological_order:
    table[state] = compute from table[earlier states]
return table[goal]
```

Both have the same time complexity. Top-down is easier to derive from the recurrence; bottom-up is faster (no recursion overhead) and sometimes allows space optimization.

----------------------------------------

## Step 3: Key Ingredients

For DP to apply, your problem needs:
- **Overlapping subproblems**: same subproblem computed multiple ways.
- **Optimal substructure**: the optimal answer to the whole is built from optimal answers to subproblems.

If either is missing, DP won't help.

Example of **no overlapping subproblems**: a pure tree recursion where every leaf is unique (like enumerating all permutations). DP doesn't reduce anything — it's just recursion.

Example of **no optimal substructure**: finding the longest **simple** path in a general graph. Optimal for subpath doesn't imply optimal for the whole.

----------------------------------------

## Step 4: Formulating a DP — Five Questions

1. **What's the state?** What parameters uniquely identify a subproblem? (For LCS: (i, j) = positions in two strings.)
2. **What's the base case?** Smallest state with a trivial answer. (LCS: if either i = 0 or j = 0, answer is 0.)
3. **What's the recurrence?** How does a state relate to smaller states?
4. **What order fills the table?** (Bottom-up only — which states depend on which?)
5. **Where's the answer?** Which state(s) contain the final result?

Answering all five gives the DP.

----------------------------------------

## Step 5: Walkthrough — Fibonacci

**State**: n (one integer).
**Base**: fib(0) = 0, fib(1) = 1.
**Recurrence**: fib(n) = fib(n-1) + fib(n-2).
**Order**: increasing n.
**Answer**: fib(n).

Top-down:
```
def fib(n, memo = {}):
    if n < 2: return n
    if n in memo: return memo[n]
    memo[n] = fib(n-1, memo) + fib(n-2, memo)
    return memo[n]
```

Bottom-up:
```
dp[0] = 0; dp[1] = 1
for i in 2..n:
    dp[i] = dp[i-1] + dp[i-2]
return dp[n]
```

Both O(n) time, O(n) space. Bottom-up further optimized to O(1) space by keeping only two variables.

----------------------------------------

## Step 6: Walkthrough — Climbing Stairs

n steps; 1 or 2 steps per move. How many ways to reach step n?

**State**: i (current step).
**Recurrence**: f(i) = f(i - 1) + f(i - 2).
**Base**: f(0) = 1 (one way to stand at start), f(1) = 1.
**Answer**: f(n).

Same shape as Fibonacci. Many DP problems reduce to Fibonacci-like recurrences.

----------------------------------------

## Step 7: Walkthrough — Longest Common Subsequence

Given strings s, t: length of longest common subsequence.

**State**: (i, j) = "considering first i chars of s and first j chars of t."
**Recurrence**:
- If s[i-1] == t[j-1]: `lcs(i, j) = 1 + lcs(i-1, j-1)`.
- Else: `lcs(i, j) = max(lcs(i-1, j), lcs(i, j-1))`.

**Base**: `lcs(0, j) = 0 = lcs(i, 0)`.
**Answer**: lcs(|s|, |t|).

Bottom-up:
```
dp = 2D array (|s|+1) x (|t|+1), init 0
for i in 1..|s|:
    for j in 1..|t|:
        if s[i-1] == t[j-1]:
            dp[i][j] = 1 + dp[i-1][j-1]
        else:
            dp[i][j] = max(dp[i-1][j], dp[i][j-1])
return dp[|s|][|t|]
```

O(|s| · |t|) time and space.

----------------------------------------

## Step 8: When to Use Memoization vs. Tabulation

**Top-down (memoization)** is preferred when:
- The state space is large but **many states are unreachable** from the initial call (e.g., sparse graphs of subproblems). Memoization visits only reachable states.
- The recurrence naturally falls out of the problem — just add a cache.

**Bottom-up (tabulation)** is preferred when:
- All states are reachable and you want maximum speed (no recursion overhead).
- You need space optimization — often a 2D table collapses to 1D.
- Recursion depth would exceed the stack.

----------------------------------------

## Step 9: Common DP Patterns

- **Linear (1D)**: Fibonacci, Climbing Stairs, Max Subarray (Kadane's variant).
- **Grid (2D)**: Unique Paths, Edit Distance, LCS.
- **Interval**: Matrix Chain Multiplication, Burst Balloons, Longest Palindromic Subsequence.
- **Subset / Bitmask**: TSP, Assignment, Subset Sum variants.
- **Tree DP**: rooted tree recurrences with children states.
- **Digit DP**: count numbers in [0, N] with digit constraints.
- **State-machine DP**: Buy/Sell Stock with Cooldown — multiple "modes" per index.

Recognizing the pattern is half the battle.

----------------------------------------

## Step 10: Space Optimization

Many 2D DPs only need the **current row and previous row** at any time. Collapse to two 1D arrays or one 1D array with careful updating order.

Example: in LCS, `dp[i][j]` depends on `dp[i-1][j-1]`, `dp[i-1][j]`, `dp[i][j-1]`. Keep two rows: prev and curr.

Some DPs (like Unique Paths II) can collapse to **one row** by updating in place — but requires care about when each cell's old value is still needed.

----------------------------------------

## Step 11: Common Pitfalls

- **Wrong base case.** Double-check small inputs.
- **Incorrect state definition.** If you can't derive the recurrence cleanly, your state is probably missing a dimension.
- **Off-by-one in grid DP.** Indexing `dp[i][j]` with string index `s[i-1]` is a common confusion — stay consistent.
- **Forgetting to memoize.** In top-down, if you forget to check the cache, you devolve to exponential.
- **Over-engineering.** If the brute force is already O(n), don't DP it.
- **Mutable default argument (Python).** `def f(n, memo={})` — the memo persists across calls, surprising many.

----------------------------------------

## Step 12: C++ Memoization Idiom

```cpp
vector<int> memo;
int f(int n) {
    if (n < 2) return n;
    if (memo[n] != -1) return memo[n];
    return memo[n] = f(n - 1) + f(n - 2);
}

// Caller:
memo.assign(N + 1, -1);
int ans = f(N);
```

The `memo[n] = ... ; return memo[n]` idiom is compact. For multi-dimensional state, use a nested vector or unordered_map.

----------------------------------------

## Step 13: Transitioning to Harder DPs

Once you've mastered linear and grid DPs, harder ones usually involve:
- **Augmented states**: an extra index or flag (e.g., "used item i or not").
- **Aggregating over decisions**: min / max / sum / count over some choice per step.
- **Ranges**: dp[l][r] for interval [l, r]; transitions split the interval.

Practice: Edit Distance → Regular Expression Matching → Dungeon Game → Burst Balloons.

----------------------------------------

## Step 14: Follow-up / Exploration

- **Memoization vs. tabulation — which is faster?** Tabulation, usually: no function call overhead, no recursion stack.
- **Space-optimized DP on very long strings.** Rolling array; O(min(m, n)) space.
- **Can all DPs be written as graph shortest-paths?** Often yes — state transitions form a DAG.
- **DP with real-valued states.** Needs discretization; pure DP over floats rarely works.
- **DP with non-polynomial state counts.** You might need better structure (exchange arguments, greedy, or reformulation).
- **Why is greedy sometimes enough?** When the optimal substructure is so strong that local choices are always globally optimal — rare.
