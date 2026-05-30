# Divisor Game

**Problem Link:**
<a href="https://leetcode.com/problems/divisor-game/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/divisor-game/</a>

**Topic:**
Number Theory / Misc

----------------------------------------

## Step 1: Understand the Game

Alice and Bob take turns. Alice goes first. On each turn, a player:
- Choose any `x` with `0 < x < n` and `n % x == 0` (x is a proper divisor of n).
- Replace `n` with `n - x`.

The player who **cannot make a move** loses. Determine if Alice wins (with both playing optimally).

Return true if Alice wins, false otherwise.

Example: n = 2.
- Alice's turn. Divisors of 2 less than 2: {1}. Alice picks 1. n becomes 1.
- Bob's turn. Divisors of 1 less than 1: {}. Bob can't move. Bob loses. Alice wins.

Return true.

Example: n = 3.
- Alice: divisors of 3 less than 3: {1}. n becomes 2.
- Bob: divisors of 2 less than 2: {1}. n becomes 1.
- Alice: no moves. Alice loses.

Return false.

----------------------------------------

## Step 2: Simulate Small Cases

- n = 1: no moves. Current player loses.
- n = 2: Alice → 1, Bob loses. **Alice wins.**
- n = 3: Alice → 2, Bob → 1, Alice loses. **Bob wins.**
- n = 4: Alice can choose 1 (→ 3, Bob in "n=3" position, Bob loses per Step 1) or 2 (→ 2, Bob wins). Alice picks 1. Alice wins.
- n = 5: Alice's only move is 1 → 4, Bob is at n=4. From Step 1, n=4 means current player wins. So Bob wins. Alice loses.
- n = 6: Alice can pick 1 → 5 (Bob loses per above), or 2 → 4 (Bob wins), or 3 → 3 (Bob loses). Alice picks 1 or 3. Alice wins.

Pattern so far:
- n = 1: lose.
- n = 2: win.
- n = 3: lose.
- n = 4: win.
- n = 5: lose.
- n = 6: win.

Alice wins iff n is even.

----------------------------------------

## Step 3: Prove "Alice Wins iff n Is Even"

**Induction on n.**

Base: n = 1: cannot move, current player loses. (1 is odd, and "current loses" matches the claim.)

Inductive step. Assume the claim holds for all smaller n.

- If n is **even**: Alice can pick `x = 1`. Now n becomes n - 1, which is **odd**. Bob is now at an odd n — by induction, current player (Bob) loses. Alice wins. ✓

- If n is **odd**: every divisor x of n is odd (divisors of odd numbers are odd). So n - x = odd - odd = even. Bob is now at even n. By induction, current player (Bob) wins. Alice loses. ✓

Done. Alice wins iff n is even.

----------------------------------------

## Step 4: The One-Line Solution

```
return n % 2 == 0
```

No DP, no simulation. Pure number-theoretic parity.

----------------------------------------

## Step 5: Trace vs. Formula

For n = 2, 4, 6, 8 (even): return true. Alice wins.
For n = 1, 3, 5, 7 (odd): return false. Alice loses.

Matches the pattern and matches the proof.

----------------------------------------

## Step 6: Why the Proof Works Intuitively

Odd numbers have only odd divisors. Subtracting an odd from an odd gives an even.

Even numbers have **both even and odd** divisors (at least 1, which is odd). So from even n, you can always subtract 1 to give the opponent an odd n.

This forces a strict alternation: even → odd → even → odd → ... With Alice starting on even, Alice hands Bob odd every turn, eventually reaching n=1, where Bob loses.

The player at an odd n is "stuck" — they have to hand an even n back. The player at an even n has control — they can force odd.

----------------------------------------

## Step 7: Name It

**Game theory via parity / Grundy-like analysis.** The specific game is Divisor Game, but the method — prove that a simple invariant (parity) decides outcomes — is broadly applicable.

Related:
- Stone Game variants.
- Nim-like games.
- Sprague-Grundy theorem for impartial games.

Sometimes full game-DP is overkill; a parity argument suffices.

----------------------------------------

## Step 8: Complexity

Time: **O(1)**.
Space: **O(1)**.

Even a DP with memoization (which naive solvers write) is O(n²) or so — dramatically worse than the formula.

----------------------------------------

## Step 9: C++ Implementation

```cpp
bool divisorGame(int n) {
    return n % 2 == 0;
}
```

One line.

For educational purposes, the DP version:

```cpp
bool divisorGame(int n) {
    vector<bool> dp(n + 1, false);   // dp[i] = can current player win at state i
    for (int i = 2; i <= n; ++i) {
        for (int x = 1; x * x <= i; ++x) {
            if (i % x == 0) {
                if (!dp[i - x]) { dp[i] = true; break; }
                // also check x != i / x
            }
        }
    }
    return dp[n];
}
```

This would compute dp[i] = true iff there's a move leaving the opponent in a losing state. Matches the parity formula but uses O(n · sqrt(n)) work.

----------------------------------------

## Step 10: Follow-up Questions

- **Same rules but start with n = some specific value, different first-player analysis.** Still parity.
- **Allow x = n (reduce to 0).** Changes the game; re-analyze.
- **Alice can pick two divisors per turn.** Different parity structure.
- **3 or more players.** Game theory extends; Grundy values or XOR-like computations.
- **Why does parity suffice?** Because the state space splits cleanly into "forced bad" (odd) and "good" (even), with the move-rule respecting this partition.
- **Variant: subtract a PRIME divisor.** Different analysis; prime parity matters.
