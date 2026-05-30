# Count of Matches in Tournament

**Problem Link:**
<a href="https://leetcode.com/problems/count-of-matches-in-tournament/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/count-of-matches-in-tournament/</a>

**Topic:**
Math

----------------------------------------

## Step 1: Understand the Tournament Rules

A single-elimination tournament with `n` teams. Each round:
- If the current number of teams is **even**: pair them up. Each pair plays; loser out.
  - Total matches this round = teams / 2.
  - Remaining teams = teams / 2.
- If **odd**: one team gets a **bye** (skips the round). The rest pair up.
  - Total matches = (teams - 1) / 2.
  - Remaining = matches + 1 (for the bye).

Continue until one team remains. Return the **total number of matches** across all rounds.

Example: n = 7.
- Round 1: 7 odd. 3 matches, 1 bye. Teams remaining: 4. Total matches: 3.
- Round 2: 4 even. 2 matches. Remaining: 2. Total: 5.
- Round 3: 2 even. 1 match. Remaining: 1. Total: 6.
- Done.

Answer: 6.

Example: n = 14.
- Round 1: 14 even. 7 matches. Remaining: 7. Total: 7.
- Round 2: 7 odd. 3 matches, 1 bye. Remaining: 4. Total: 10.
- Round 3: 4 even. 2 matches. Remaining: 2. Total: 12.
- Round 4: 2 even. 1. Remaining: 1. Total: 13.

Answer: 13.

----------------------------------------

## Step 2: Simulate — The Straightforward Way

Just run the simulation:

```
matches = 0
while teams > 1:
    if teams % 2 == 0:
        matches += teams / 2
        teams /= 2
    else:
        matches += (teams - 1) / 2
        teams = (teams - 1) / 2 + 1
return matches
```

O(log n) iterations (each halves or almost-halves the teams). Simple.

But wait — there's a cleaner observation.

----------------------------------------

## Step 3: The "Each Match Eliminates One Team" Insight

In any single-elimination tournament, **each match produces exactly one loser who is eliminated**. Starting with n teams, we need to eliminate n - 1 to have a single winner.

Total matches = total eliminations = **n - 1**.

It doesn't matter how byes distribute, how many rounds there are, or how unbalanced the bracket is. One loss per match. To end with 1 team, we need n - 1 losses.

For n = 7: 7 - 1 = **6**. ✓
For n = 14: 14 - 1 = **13**. ✓

That's it. One-liner.

----------------------------------------

## Step 4: Why the Insight Is True

No matter how we structure the rounds:
- Each round produces some number of matches.
- Each match eliminates exactly one team (winner advances, loser out).
- Byes don't produce matches — they advance a team without elimination.

The total eliminations across all rounds = n - 1 (since we start at n teams and end with 1).

Total eliminations = total matches (one per match).

Therefore total matches = **n - 1**.

The structure of rounds, byes, brackets — all irrelevant to the total count.

----------------------------------------

## Step 5: Contrasting with the Simulation

Both approaches give the same answer. But the insight lets us skip simulation entirely.

- Simulation: O(log n) time.
- Formula: O(1) time.

For n up to 200, both are trivially fast. The difference is purely aesthetic — the insight is more elegant and "shows your work" as mathematical reasoning rather than code.

----------------------------------------

## Step 6: Name It

This is an **invariant-based counting** argument. The invariant: "each match eliminates one team." Invariants like these turn complex processes into simple counts.

Related problems:
- Elimination tournaments in general.
- "Count of operations" problems where each operation has a single effect on some monovariant.
- Problems where you count events rather than simulate them.

Spotting invariants is a skill that saves time in competitive settings.

----------------------------------------

## Step 7: C++ Implementation

**Formula version:**

```cpp
int numberOfMatches(int n) {
    return n - 1;
}
```

One line. The most elegant answer to this problem.

**Simulation version (for completeness):**

```cpp
int numberOfMatches(int n) {
    int matches = 0;
    while (n > 1) {
        if (n % 2 == 0) {
            matches += n / 2;
            n /= 2;
        } else {
            matches += (n - 1) / 2;
            n = (n - 1) / 2 + 1;
        }
    }
    return matches;
}
```

Works, but reads as overkill once you see the formula.

----------------------------------------

## Step 8: Follow-up Questions

- **Multiple-elimination tournaments (team has multiple chances).** Now each team might lose multiple times; the "one match per elimination" invariant doesn't directly apply.
- **Round-robin (everyone plays everyone).** Total matches = C(n, 2) = n·(n-1)/2.
- **Each match may have multiple eliminations (unusual format).** Invariant adjusts.
- **Matches until a specific team is eliminated.** Requires bracket knowledge.
- **What if the tournament format has no byes (only powers of 2 teams)?** Still n - 1 total matches. The invariant doesn't care.
- **Think of it as a graph/tree.** A single-elimination bracket is a binary tree with n leaves. The tree has n - 1 internal nodes (each representing a match). So n - 1 matches.
