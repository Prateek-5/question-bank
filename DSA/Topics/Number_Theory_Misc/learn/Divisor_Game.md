# Divisor Game — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Divisor_Game.md`](../Divisor_Game.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/divisor-game/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/divisor-game/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~12 minutes. **The lesson: Alice wins iff n is EVEN. Game-theory parity argument: odd has only odd divisors → subtracting gives even → opponent has the move; even can subtract 1 → opponent stuck on odd.**

**Map of this file (7 sections):**

1. Read the problem
2. Hand-simulate small cases
3. The parity pattern
4. Proof by induction
5. Code
6. Common pitfalls
7. The shape — parity game theory

---

## 1. Read the problem

Game on integer n. Alice moves first. On a turn, the player picks `x` with `0 < x < n` AND `n % x == 0`, then sets `n := n - x`. Player who CAN'T move LOSES. Both play optimally. Return true iff Alice wins.

**Example:** n=2 → Alice picks 1, n=1, Bob can't move → Alice wins (true).
n=3 → Alice picks 1, n=2 → Bob picks 1, n=1 → Alice can't move → Alice loses (false).

---

## 2. Hand-simulate small cases

- n=1: no move, current player loses. (Odd → lose.)
- n=2: Alice → 1, Bob stuck. Alice wins. (Even → win.)
- n=3: Alice → 2, Bob → 1, Alice stuck. Alice loses. (Odd → lose.)
- n=4: Alice picks 1 → 3, Bob in lose-position. Alice wins. (Even → win.)
- n=5: only divisor < 5 is 1; → 4, Bob wins. Alice loses. (Odd → lose.)

**Pattern: Alice wins iff n is EVEN.**

---

## 3. The parity pattern

> **Mini-refresher: odd vs even creates a forced alternation.**
>
> - Even n: Alice CAN pick x=1 (since 1 divides everything) → n becomes ODD. Bob is now at odd.
> - Odd n: Every divisor of n is ODD. Subtracting odd from odd gives EVEN. So Alice MUST hand Bob an even.

So the parity alternates from "current player's hand" to "opponent's hand" — but the controlling player is always the one with EVEN.

---

## 4. Proof by induction

**Claim:** current player wins iff n is even.

**Base:** n=1: no move → current loses. (1 is odd, current loses. ✓)

**Step:**
- **Even n:** current picks x=1 → n becomes odd. Opponent now at odd; by IH, opponent loses. Current wins. ✓
- **Odd n:** every divisor of n is odd. Any move gives opponent an EVEN n. By IH, opponent wins. Current loses. ✓

Done. Alice wins iff n is even.

---

## 5. Code

**C++:**

```cpp
bool divisorGame(int n) {
    return n % 2 == 0;
}
```

ONE LINE. **O(1)** time and space.

(A DP solution exists but is wildly overkill.)

---

## 6. Common pitfalls

1. **Implementing DP without spotting the parity.** Works (slowly) — O(n · √n) — but misses the elegance.
2. **Treating Alice's "optimal" as "any move."** Optimal play matters — both pick the move that leaves the opponent in a losing position.
3. **Forgetting that 1 divides everything.** This is why even n can always force the parity flip.
4. **Assuming game-theory problems always need DP / Sprague-Grundy.** Sometimes a parity invariant suffices.

---

## 7. The shape — parity game theory

The pattern: **find an INVARIANT (often parity) that decides who wins.**

| Problem | Invariant |
|---|---|
| **This problem** | n's parity |
| Nim (single pile) | pile size parity (for trivial Nim) |
| Stone Game (variants) | sum parity / position parity |
| Coins in a Line | DP for general; parity for specific |
| Reach a Number | triangular numbers parity |
| Game of Life on a coin row | DP or parity analysis |

**Pattern to internalize:**

> "Game theory: look for an INVARIANT (parity, mod-k value, XOR) that splits states into 'winning' and 'losing.' Often closes the problem in O(1) without DP."

---

> **Self-check — the question to ask next time.**
>
> When facing a two-player optimal-play game:
>
> > **"Is there a simple invariant (parity, mod) such that all states with one value of the invariant are losing and others winning? If so, return the invariant."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Divisor_Game.md`](../Divisor_Game.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Bulb_Switcher.md`](../../Greedy/learn/Bulb_Switcher.md), [`Number_of_Open_Doors.md`](./Number_of_Open_Doors.md).
  - Coming next: [`Memoization_DP_Basics.md`](./Memoization_DP_Basics.md), [`Implement_Rand10_Using_Rand7.md`](./Implement_Rand10_Using_Rand7.md).
