# Dynamic Programming (DP) — Concepts Guide

----------------------------------------

## 1. Introduction

Dynamic programming is the art of trading time for memory: you identify overlapping subproblems in a recursion and remember their answers so you don't re-solve them. The hard part is almost never the memo — it's identifying the right **state** (what uniquely defines a subproblem).

----------------------------------------

## 2. Real-Life Analogy

Imagine you're climbing stairs and someone asks 'how many ways to reach step n?'. You'd quickly realize: ways to reach n = ways to reach n-1 (take 1 step) + ways to reach n-2 (take 2 steps). That's the recurrence. But if you compute it naively, you'll compute ways-to-reach-5 many times as you compute ways-to-reach-10. DP is just writing them down as you go.

----------------------------------------

## 3. Core Idea

DP has three ingredients: (1) **state** — the parameters that describe a subproblem, (2) **transition** — the recurrence that expresses a state in terms of smaller states, (3) **base cases** — the atomic subproblems you solve directly. Top-down DP (memoization) writes recursion with a cache; bottom-up DP (tabulation) fills an array in dependency order. Space optimization replaces full tables with rolling windows when only the last 1 or 2 rows matter.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Classic signals for DP:

- **Overlapping subproblems** in a recursive formulation.
- **Optimal substructure** — optimal solution composed of optimal sub-solutions.
- **'Count the number of ways'** — almost always DP.
- **'Find the minimum/maximum cost / length'** with choices at each step.
- **State can be captured in a small number of parameters** (index, remaining capacity, last choice, etc.).

----------------------------------------

## 5. Types / Variations

- **1D DP** (Climbing Stairs, LIS, Kadane).
- **2D DP** (LCS, Edit Distance, Interleaving).
- **Knapsack** (0/1, unbounded, bounded).
- **Interval DP** (Matrix Chain, Palindrome Partitioning).
- **Tree DP** (subtree computations).
- **Bitmask DP** (TSP-like when n ≤ ~20).
- **Digit DP** (count numbers in range with digit property).

----------------------------------------

## 6. Step-by-Step Working

**General DP recipe:**
1. **Identify state.** What parameters uniquely determine the subproblem?
2. **Write the recurrence.** How does the answer for a state depend on smaller states?
3. **Specify base cases.** What are the atomic answers?
4. **Pick top-down or bottom-up.** Top-down is easier to write; bottom-up is often faster due to no call overhead.
5. **Consider space optimization.** Often only the last few rows matter.

----------------------------------------

## 7. Visual Explanation

**LCS of `s = 'abc'` and `t = 'ac'`:**

```
      ""  a  c
"" |  0  0  0
a  |  0  1  1
b  |  0  1  1
c  |  0  1  2
```

Each cell dp[i][j] = LCS of first i chars of s and first j chars of t. Cell dp[3][2] = 2 → LCS 'ac'.

----------------------------------------

## 8. Code Templates (C++)

```cpp
// Memoized recursion (top-down)
int memo[MAXN];
int solve(int i) {
    if (i <= 1) return 1;
    if (memo[i] != -1) return memo[i];
    return memo[i] = solve(i-1) + solve(i-2);
}

// Tabulation (bottom-up) with space optimization
int climbStairs(int n) {
    int a = 1, b = 1;
    for (int i = 2; i <= n; ++i) {
        int c = a + b;
        a = b; b = c;
    }
    return b;
}

// Classic 2D DP (LCS)
int lcs(string s, string t) {
    int n = s.size(), m = t.size();
    vector<vector<int>> dp(n+1, vector<int>(m+1, 0));
    for (int i = 1; i <= n; ++i) for (int j = 1; j <= m; ++j)
        dp[i][j] = (s[i-1] == t[j-1]) ? dp[i-1][j-1] + 1
                                      : max(dp[i-1][j], dp[i][j-1]);
    return dp[n][m];
}
```

----------------------------------------

## 9. Common Mistakes

- **Wrong state definition** — missing a dimension (e.g., needing 'last char used').
- **Off-by-one in base cases.**
- **Iteration order** must respect dependencies in bottom-up.
- **Forgetting to initialize memo.**
- **Overflow in counting DPs** — use long long or mod.

----------------------------------------

## 10. Interview Insights

DP interviews test state-thinking. Interviewers want to see:

1. **You articulate the state clearly** before coding.
2. **You write a clean recurrence.**
3. **You handle base cases explicitly.**
4. **You analyze time and space correctly.**
5. **You can convert top-down to bottom-up if asked.**

The most common mistake under pressure is trying to code before defining state. Resist. Spend the first minutes on 'what parameters describe a subproblem?' That's the single highest-leverage moment in the interview.
