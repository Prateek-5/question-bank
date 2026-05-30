# Count of Matches in Tournament — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Count_of_Matches_in_Tournament.md`](../Count_of_Matches_in_Tournament.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/count-of-matches-in-tournament/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/count-of-matches-in-tournament/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~10 minutes. **An invariant-based counting problem.** The lesson: **identify a one-to-one relationship between events you want to count and a simpler quantity.** Here: each match eliminates exactly one team; to end with one champion, n-1 teams must be eliminated; so n-1 matches total. This "count by invariant" technique is one of the great problem-solving moves.

**Map of this file (8 short sections):**

1. Read the problem
2. The simulation
3. The invariant — each match eliminates one team
4. The one-line formula
5. Code
6. Trace it
7. Why this works regardless of bracket structure
8. The shape — invariant-based counting

---

## 1. Read the problem

You have `n` teams in a single-elimination tournament. The rules:
- If the current number of teams is **even**: pair them up. Each pair plays one match. Winner advances; loser is eliminated.
- If **odd**: one team gets a **bye** (skips the round). The rest pair up.
- Repeat until one champion remains.

Return the **total number of matches** played across all rounds.

**Examples:**

- `n = 7`:
  - Round 1: 7 odd. 3 matches (one bye). 4 teams remain.
  - Round 2: 4 even. 2 matches. 2 teams remain.
  - Round 3: 2 even. 1 match. 1 team (champion).
  - Total: 3 + 2 + 1 = **6**.

- `n = 14`:
  - Round 1: 14 even. 7 matches. 7 teams.
  - Round 2: 7 odd. 3 matches (one bye). 4 teams.
  - Round 3: 4 even. 2 matches. 2 teams.
  - Round 4: 2 even. 1 match. 1 team.
  - Total: 7 + 3 + 2 + 1 = **13**.

---

## 2. The simulation

Direct translation:

```
matches = 0
while n > 1:
    if n % 2 == 0:
        matches += n // 2
        n //= 2
    else:
        matches += (n - 1) // 2
        n = (n - 1) // 2 + 1     # bye + matches
return matches
```

O(log n) iterations. Works.

But there's a one-liner. Let's find it.

---

## 3. The invariant — each match eliminates one team

Stand back. Forget rounds. Forget byes. Look at the BIG PICTURE.

**Each match eliminates EXACTLY ONE team** (the loser). The winner advances; the loser is out.

We start with `n` teams. We end with `1` team (the champion). So we need to eliminate `n - 1` teams.

Total eliminations = total matches (one elimination per match).

So **total matches = n - 1**.

> **Mini-refresher: counting by invariant.**
>
> Identify a property that increments/decrements by a fixed amount per event. Then the total event count is determined by the START and END states of that property.
>
> Here:
> - **Invariant:** team count.
> - **Initial value:** n.
> - **Final value:** 1.
> - **Each match changes the invariant by -1** (one team eliminated).
> - **Therefore:** number of matches = n - 1.
>
> No simulation needed. Just count the GAP.

---

## 4. The one-line formula

```
return n - 1
```

That's it.

It doesn't matter:
- How rounds are organized.
- How byes are distributed.
- Whether the bracket is balanced.
- Any other format details.

Each match: one elimination. Need n - 1 eliminations. So n - 1 matches.

---

## 5. Code

**C++ — formula:**

```cpp
int numberOfMatches(int n) {
    return n - 1;
}
```

**C++ — simulation (only for completeness):**

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

**Python — formula:**

```python
def numberOfMatches(n):
    return n - 1
```

Complexity: **O(1) time, O(1) space** for the formula. **O(log n)** for the simulation.

---

## 6. Trace it

- `n = 7`: formula gives `7 - 1 = 6`. ✓ (Matches the simulation's 3+2+1=6.)
- `n = 14`: formula gives `14 - 1 = 13`. ✓ (Matches 7+3+2+1=13.)
- `n = 1`: 0 matches (no opponents). Formula: `1 - 1 = 0`. ✓
- `n = 2`: 1 match. Formula: `1`. ✓
- `n = 100`: 99 matches. ✓

Always works.

---

## 7. Why this works regardless of bracket structure

Even if the tournament had a wildly different format:
- 17 byes in the first round, then a different elimination rule.
- A round-robin in some rounds, single-elimination in others.
- Players paired by Swiss system.

**As long as the rule "each match eliminates one team" holds, the formula stays correct.** Total matches = total eliminations = n - 1.

The "byes" in the problem don't produce matches — they just shuffle the schedule. Match count is invariant under scheduling.

> **Mini-refresher: scheduling doesn't change totals.**
>
> If you have to do `k` units of work, distributing them across rounds/days/people doesn't change `k`. The total stays the same; only the timing varies.
>
> Same principle here: the WORK is "eliminate n - 1 teams," and however it's scheduled, the work amount is fixed.

---

## 8. The shape — invariant-based counting

This pattern shows up everywhere in CS and math:

| Problem | Invariant | Total count |
|---|---|---|
| **This problem** | team count | matches = teams_initial - teams_final |
| Number of swaps to sort | inversions count | each swap fixes 1 inversion |
| Number of edges in a tree with n nodes | edges count | edges = n - 1 (tree property) |
| Comparisons to find min via tournament | each round halves comparisons | total = n - 1 |
| Number of joins in a graph union-find | components count | joins = initial - final components |
| Cuts to slice a rod into k pieces | piece count | cuts = k - 1 |
| Number of additions to compute Fibonacci recursively | function calls grow exponentially | NOT invariant-based; needs memoization |

**Pattern to internalize:**

> "When a problem asks 'how many EVENTS happen?', look for an INVARIANT that each event changes by a fixed amount. Then total events = (initial - final) / (change per event)."

The trick frees you from simulating the process. You count by SUBTRACTION.

---

> **Self-check — the question to ask next time.**
>
> When you face a counting problem about events / steps / matches, ask:
>
> > **"Is there a STATE QUANTITY (count of items, score, position) that EACH event changes by a FIXED amount? If yes, total events = (initial state - final state) / per-event change."**
>
> If yes, you've replaced a simulation with arithmetic.

---

## Cross-references

- **Reference card (post-mastery):** [`../Count_of_Matches_in_Tournament.md`](../Count_of_Matches_in_Tournament.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Add_Digits.md`](./Add_Digits.md), [`Determine_Color_of_a_Chessboard_Square.md`](./Determine_Color_of_a_Chessboard_Square.md) — other "closed form / observation" puzzles.
  - Coming next: Day_of_the_Week, Find_the_Pivot_Integer.
