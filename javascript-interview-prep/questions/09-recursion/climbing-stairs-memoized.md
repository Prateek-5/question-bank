# Climbing stairs — recursive with memoization

## Source
- Canonical recursion → memoization → DP interview progression.
- LeetCode #70 "Climbing Stairs": https://leetcode.com/problems/climbing-stairs/
- Reference (top-down vs bottom-up DP): https://en.wikipedia.org/wiki/Memoization

## Why this question matters in interviews
Climbing stairs is the **rosetta stone** of dynamic programming interviews. It's the simplest non-trivial recurrence — `f(n) = f(n-1) + f(n-2)` — but it lets interviewers walk you through *three solutions in escalating sophistication*: naive recursion (exponential, broken), top-down memoization (`O(n)`), bottom-up DP (`O(n)` time, `O(1)` space). They use this progression as a **diagnostic**: senior candidates volunteer the naive version, recognize the overlapping-subproblem hit, then walk through space optimization unprompted. The recurrence is Fibonacci-equivalent and is the same shape as many real problems: tiling a 2×n grid, decoding numeric strings, counting paths in a grid. **Critical V8 trap:** the naive recursion call-stack-overflows at ~n=10k *and* takes hours at n=40 due to no tail-call optimization. Mention this — it's a senior signal.

## Concepts involved

### Syntax to lock in

Three solutions, in the exact order an interviewer wants to hear them:

```js
// (1) Naive recursion — EXPONENTIAL O(2^n), DO NOT submit
function climbStairsNaive(n) {
  if (n <= 2) return n;
  return climbStairsNaive(n - 1) + climbStairsNaive(n - 2);
}

// (2) Top-down memoization — O(n) time, O(n) space
function climbStairsMemo(n, memo = new Array(n + 1)) {
  if (n <= 2) return n;
  if (memo[n] !== undefined) return memo[n];
  return memo[n] = climbStairsMemo(n - 1, memo) + climbStairsMemo(n - 2, memo);
}

// (3) Bottom-up iterative — O(n) time, O(1) space
function climbStairs(n) {
  if (n <= 2) return n;
  let prev2 = 1, prev1 = 2;
  for (let i = 3; i <= n; i++) {
    const curr = prev1 + prev2;
    prev2 = prev1;
    prev1 = curr;
  }
  return prev1;
}
```

### Runtime / engine behavior
- **Naive recursion** has recurrence `T(n) = T(n-1) + T(n-2) + O(1)` ≈ `O(φ^n)` ≈ `O(1.618^n)`. For n=40 that's ~165 million calls — runs for many seconds in V8. For n=50 it's tens of seconds to minutes.
- **Memoization (top-down)** turns the exponential tree into a DAG with n nodes. Each `f(k)` is computed once and reused. Time `O(n)`, space `O(n)` for the memo + `O(n)` for the recursion stack.
- **Bottom-up DP** drops the call stack and the memo array. Two variables suffice because `f(n)` only depends on `f(n-1)` and `f(n-2)`. **`O(1)` space.** This is the answer interviewers expect as the final form.
- **V8 has no tail-call optimization (TCO).** Even though ES2015 spec'd TCO, V8 never shipped it (Safari did, then reverted). So the naive recursion blows the stack at depth ~10k–15k (default `--stack-size`). The memoized version recurses up to depth `n` — for `n = 50_000` you'll also stack-overflow despite the `O(n)` total work. **Bottom-up iterative is the only safe solution for large `n`.**
- **Result overflow:** `f(78) > Number.MAX_SAFE_INTEGER` (2^53 - 1). For larger inputs use `BigInt`. Interviewers may not ask about this for n ≤ 50 but it's a senior-tier callout.

### Edge cases
1. **n = 0** — depends on the problem statement. LeetCode defines `n >= 1`. If asked, one common interpretation is "there's 1 way to climb zero stairs (stand still)" → return 1. Clarify with interviewer.
2. **n = 1** — 1 way: `[1]`. Return 1.
3. **n = 2** — 2 ways: `[1,1]` and `[2]`. Return 2.
4. **Large n** — V8 stack overflow on recursive solutions at ~10k. Memoization doesn't save you from stack depth; only iteration does.
5. **Integer overflow** — `f(78) > 2^53`. JS silently loses precision. Use `BigInt` for unbounded `n`.
6. **Negative n** — undefined by problem; clarify or throw `RangeError`.
7. **Memo as default parameter** — `memo = new Array(n + 1)` allocates a fresh memo on each top-level call, which is correct. **Do not** use `memo = {}` defined outside the function — it leaks state across calls.

## Brute force approach
The naive recursion *is* the brute force. It's correct but exponential. The conversation interviewers want:
> "I can write `f(n) = f(n-1) + f(n-2)` directly, but the call tree has `~φ^n` nodes — we re-compute `f(k)` exponentially many times. I'll memoize."

You should always state this transition explicitly. The pattern "draw the recursion tree → notice overlapping subproblems → memoize" is the **canonical DP discovery process** and the interviewer is grading that meta-skill.

## Optimal approach
Bottom-up DP with **two rolling variables.** Recognize `f(n)` depends only on the previous two values. Drop the array. `O(n)` time, `O(1)` space. There's no asymptotically faster algorithm short of the closed-form Fibonacci (Binet's formula or matrix exponentiation in `O(log n)`) — usually overkill in interview unless asked.

## Solution (JavaScript)

```js
/**
 * Count distinct ways to climb n stairs taking 1 or 2 steps at a time.
 * f(n) = f(n-1) + f(n-2) — same recurrence as Fibonacci.
 *
 * Returns the bottom-up O(1)-space version.
 * Time:  O(n).
 * Space: O(1).
 *
 * @param {number} n  number of stairs, n >= 1
 * @returns {number}  number of distinct climb sequences
 */
function climbStairs(n) {
  if (n <= 0) return 0;
  if (n <= 2) return n;
  let prev2 = 1;     // f(1)
  let prev1 = 2;     // f(2)
  for (let i = 3; i <= n; i++) {
    const curr = prev1 + prev2;
    prev2 = prev1;
    prev1 = curr;
  }
  return prev1;
}

/**
 * Top-down memoization variant — same O(n) work but uses
 * O(n) stack + O(n) memo array. Useful as a teaching solution
 * but stack-overflows on n > ~10k in V8 (no tail-call optimization).
 */
function climbStairsMemo(n) {
  const memo = new Array(n + 1);
  function go(k) {
    if (k <= 2) return k;
    if (memo[k] !== undefined) return memo[k];
    return memo[k] = go(k - 1) + go(k - 2);
  }
  return n <= 0 ? 0 : go(n);
}

/**
 * BigInt version for n where the result overflows 2^53.
 * f(78) is the first value > Number.MAX_SAFE_INTEGER.
 */
function climbStairsBigInt(n) {
  if (n <= 0) return 0n;
  if (n <= 2) return BigInt(n);
  let prev2 = 1n, prev1 = 2n;
  for (let i = 3; i <= n; i++) {
    [prev2, prev1] = [prev1, prev1 + prev2];
  }
  return prev1;
}
```

## Step-by-step dry run

### Naive recursion for n=5 — counting calls

```
                           f(5)
                       /          \
                    f(4)           f(3)
                  /     \         /    \
               f(3)    f(2)    f(2)   f(1)
              /   \
           f(2)  f(1)
```

Tree node count: 9 calls to compute `f(5)`. For n=10 it's 177 calls; n=20 it's 21,891; n=30 it's ~2.7M; n=40 it's ~331M. Exponential explosion — this is what the senior interviewer wants you to *show* on the whiteboard.

### Memoized walk for n=5

- Call `go(5)`. memo empty.
- `go(5)` → calls `go(4)` then `go(3)`.
- `go(4)` → calls `go(3)` then `go(2)`.
- `go(3)` → calls `go(2)` then `go(1)`. Returns 2+1 = 3. memo[3]=3.
- `go(2)` → returns 2. (base case; not memoized since base.)
- `go(4)` resumes: returns `memo[3]=3` + 2 = 5. memo[4]=5.
- `go(3)` (second call from go(5)) → hits memo[3]=3, returns immediately.
- `go(5)` returns `memo[4]=5` + `memo[3]=3` = 8.

Total calls: 9 → 7 (memo saved 2). For large n the savings are exponential.

### Bottom-up walk for n=5

| i | prev2 | prev1 | curr |
|---|-------|-------|------|
| init | 1 | 2 | — |
| 3 | 2 | 3 | 3 |
| 4 | 3 | 5 | 5 |
| 5 | 5 | 8 | 8 |

Return `prev1 = 8`. Two variables, no array, no recursion. Matches the memoized answer.

For sanity: f(1..10) = 1, 2, 3, 5, 8, 13, 21, 34, 55, 89 — Fibonacci shifted by one.

## Important takeaways

**Syntax to memorize**
- Recurrence: `f(n) = f(n-1) + f(n-2)`. Base: `f(1) = 1, f(2) = 2`.
- Rolling-variable pattern: `prev2 = 1, prev1 = 2; for i=3..n { curr = prev1+prev2; prev2 = prev1; prev1 = curr }`.
- Memo array: `memo[n] !== undefined` is safer than `memo[n]` because `0` is falsy but valid for some DP problems.
- Default-parameter memo `function f(n, memo = new Array(n+1))` — fresh per top-level call. Don't hoist memo into a module-level `{}`.

**Patterns to reuse**
- **Top-down memo → bottom-up DP → space-optimized rolling variables** is *the* canonical DP optimization sequence. Same shape applies to:
  - Decode Ways (LC #91) — also depends on last 1–2 chars.
  - House Robber (LC #198) — `f(i) = max(f(i-1), f(i-2) + nums[i])`.
  - Min cost climbing stairs (LC #746).
  - Tribonacci (LC #1137) — three rolling variables.
  - Unique paths in 2D grid → "rolling row" reduces O(m·n) space to O(n).
- Knowing `f(n) = f(n-1) + f(n-2)` is Fibonacci unlocks **matrix exponentiation** `O(log n)` for *huge* n — overkill in JS but the senior callout.

**Common mistakes**
- Submitting naive recursion. It's `O(φ^n)`. Times out on LeetCode at n ≈ 40.
- Using a module-level memo `const memo = {}` — leaks state across test runs; subtle bug.
- Forgetting that **V8 doesn't TCO**, so even memoized recursion stack-overflows at n ~ 10k. Always have the iterative answer ready.
- Returning `0` for `n = 0` without confirming the problem statement — clarify first.
- Confusing this with "ways using steps 1, 2, **or 3**" — that's tribonacci, a different recurrence.
- Saying "I'd use a `Map` for memo" — `Array` of length n+1 is faster (densely packed, integer keys). `Map` is for sparse keys.

**Related questions**
- House robber, decode ways, min-cost-climbing-stairs — same `f(n)` depends on `f(n-1)` and `f(n-2)` shape.
- Tribonacci — three-term recurrence; rolling 3 variables.
- Unique paths (2D DP), edit distance (2D DP) — the obvious next step.
- Fibonacci in `O(log n)` via matrix exponentiation — interesting curiosity for "what if n = 10^18?"

## Variants

1. **Steps of size 1, 2, or 3** (tribonacci) — `f(n) = f(n-1) + f(n-2) + f(n-3)`. Same pattern with 3 rolling variables.

2. **Variable step sizes** `steps = [1, 3, 5]` — `f(n) = Σ f(n - s)` for each valid `s`. Memoize over `n`.

3. **Min cost climbing stairs (LC #746)** — each stair has a cost; minimize total. `f(i) = cost[i] + min(f(i-1), f(i-2))`.

4. **Count distinct sequences (not just count)** — generate every step sequence as an array. Output size grows as Fibonacci — fine for small n. Use backtracking like permutations.

5. **`O(log n)` via matrix exponentiation** — `[[f(n+1)], [f(n)]] = [[1,1],[1,0]]^n · [[1],[0]]`. Compute the matrix power in `O(log n)` via fast exponentiation. Useful when n is `10^18`; pure interview flex otherwise.

6. **Closed form (Binet)** — `f(n) ≈ φ^n / √5`. Floating-point loses precision after n ~ 70; not practical for exact results.

## Revision notes

> **climbing stairs — 60 second recap**
> - Recurrence **`f(n) = f(n-1) + f(n-2)`**, base `f(1)=1, f(2)=2`. Fibonacci shifted by one.
> - Three solutions in this order:
>   1. Naive recursion — **`O(φ^n)`**, broken at n=40. Show it as motivation.
>   2. Top-down memo — `O(n)` time, `O(n)` space + `O(n)` stack.
>   3. Bottom-up DP with **two rolling variables** — `O(n)` time, **`O(1)` space**. Submit this.
> - **V8 has no TCO** — even memoized recursion stack-overflows at n ≈ 10k. Iterative is the only safe form.
> - **Trap 1:** `f(78) > Number.MAX_SAFE_INTEGER` — use `BigInt` for big n.
> - **Trap 2:** module-level memo leaks across calls. Use default-parameter or local memo.
> - **Trap 3:** naive recursion accepted on LeetCode at small n then TLE at larger — always upgrade.
> - Same DP shape: house robber, decode ways, min-cost-stairs.
> - For huge n (`10^18`), use matrix exponentiation in `O(log n)`.
