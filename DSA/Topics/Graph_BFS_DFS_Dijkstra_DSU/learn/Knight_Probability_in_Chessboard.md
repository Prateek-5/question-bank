# Knight Probability in Chessboard — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Knight_Probability_in_Chessboard.md`](../Knight_Probability_in_Chessboard.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/knight-probability-in-chessboard/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/knight-probability-in-chessboard/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: probability of "knight stays on board for k moves" = DP over (row, col, moves_remaining). BACKWARD recursion: `p(i, j, s)` is the chance of surviving s more moves starting at (i, j). Each move contributes 1/8, weighted by neighbor's survival probability.**

**Map of this file (8 sections):**

1. Read the problem
2. The "probability on-board" reframe
3. Forward vs backward DP
4. The recurrence
5. Code
6. Trace it
7. Common pitfalls
8. The shape — random walk DP

---

## 1. Read the problem

On an `n × n` chessboard, a knight starts at `(row, col)` and makes EXACTLY k moves. Each move is one of 8 knight moves, chosen uniformly at random. If a move goes off the board, the knight is LOST (does not rebound). Return the probability the knight remains on the board after k moves.

**Example:** n=3, k=2, start=(0, 0). Answer **0.0625** (= 1/16).

---

## 2. The "probability on-board" reframe

Each move: 1/8 chance of going to each of 8 squares. If the chosen square is off-board, the chain "dies." Survival probability multiplies along the moves.

We want: P(after k moves, knight is still on board).

---

## 3. Forward vs backward DP

> **Mini-refresher: backward DP is cleaner here.**
>
> **Forward:** `p_forward(i, j, s)` = probability of being at (i, j) AFTER s moves from start. Base: `p(row, col, 0) = 1`, others 0. Transition: sum over preimages.
>
> **Backward:** `p(i, j, s)` = probability of SURVIVING s MORE moves starting at (i, j). Base: `p(i, j, 0) = 1` (zero moves to make = trivially survived). Transition: each of 8 moves contributes 1/8 × (neighbor's survival).
>
> Both are equivalent; backward is more natural because the base case is uniformly 1 across all cells.

Answer = `p(row, col, k)`.

---

## 4. The recurrence

For backward DP:

```
p(i, j, 0) = 1
p(i, j, s) = (1/8) * sum over 8 knight moves (di, dj) of:
                 p(i + di, j + dj, s - 1)  if (i+di, j+dj) on board
                 0                          otherwise
```

We sum the 8 neighbor probabilities (zero for off-board moves) and divide by 8.

---

## 5. Code

**C++ — bottom-up with rolling tables:**

```cpp
double knightProbability(int n, int k, int row, int col) {
    vector<vector<double>> dp(n, vector<double>(n, 1.0));   // 0 moves left: prob = 1
    int moves[8][2] = {{-2,-1},{-2,1},{-1,-2},{-1,2},{1,-2},{1,2},{2,-1},{2,1}};

    for (int step = 1; step <= k; ++step) {
        vector<vector<double>> newDp(n, vector<double>(n, 0.0));
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < n; ++j) {
                for (auto& m : moves) {
                    int ni = i + m[0], nj = j + m[1];
                    if (ni >= 0 && ni < n && nj >= 0 && nj < n) {
                        newDp[i][j] += dp[ni][nj];
                    }
                }
                newDp[i][j] /= 8.0;
            }
        }
        dp = newDp;
    }
    return dp[row][col];
}
```

Complexity: **O(n² · k)** time (n² cells × k steps × 8 neighbors per cell), **O(n²)** space.

---

## 6. Trace it

n=3, k=1, start=(0, 0).

```
dp (step=0): all 1.0.

Step 1: build newDp.
  newDp[0][0] = sum of dp[ni][nj] for the 8 knight moves of (0,0):
    (-2,-1), (-2,1), (-1,-2), (-1,2): off board.
    (1,-2), (2,-1): off board (negative col).
    (1, 2): on board. dp[1][2] = 1.
    (2, 1): on board. dp[2][1] = 1.
    Sum = 2. newDp[0][0] = 2 / 8 = 0.25.
  ...
dp[0][0] after step 1 = 0.25.  ✓
```

For k=2 we'd run another step, but newDp[0][0] now depends on the step-1 values of (1,2) and (2,1), each of which is 0.25 (they similarly have only 2 valid moves). Final: 2 × 0.25 / 8 = 0.0625.

---

## 7. Common pitfalls

1. **Forward DP without normalizing.** Forward `p_forward(i, j, s)` sums to ≤ 1 over (i, j) — that ≤ 1 IS the survival prob. Don't accidentally divide.
2. **Wrong knight moves.** The 8 offsets are (±1, ±2) and (±2, ±1) — 8 of them. Easy to enumerate only 4.
3. **Mutating dp in place.** Each step must read from the PREVIOUS step's table.
4. **Returning newDp[i][j] / 8.0 inside the move loop.** Divide ONCE at the end, not 8 times.
5. **Using integers — losing precision.** Probabilities require double.

---

## 8. The shape — random walk DP

The pattern: **k-step DP over grid states with bounded transitions.**

| Problem | State | Transitions |
|---|---|---|
| **This problem** | (cell, moves left) | 8 knight moves, 1/8 each |
| Out of Boundary Paths | (cell, moves left) | 4 directional moves |
| Frog Jump (lily pads) | (position, last jump) | three jump sizes |
| Dice Roll Simulation | (rolls, last face, repeats) | 6 faces with rules |
| Soup Servings | (a, b) | 4 serving choices, 1/4 each |

**Pattern to internalize:**

> "Random walk + bounded k steps + grid: DP over (state, steps remaining). Backward DP makes the base case trivial."

---

> **Self-check — the question to ask next time.**
>
> When the problem says "probability after k random moves," ask:
>
> > **"State = (cell, moves left). Base = 1 at 0 moves. Transition = (1/m) × sum of neighbor probabilities. Build k tables iteratively."**

---

## Cross-references

- **Reference card (post-mastery):** [`../Knight_Probability_in_Chessboard.md`](../Knight_Probability_in_Chessboard.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Shortest_Path_in_Binary_Matrix.md`](./Shortest_Path_in_Binary_Matrix.md), [`Cheapest_Flights_Within_K_Stops.md`](./Cheapest_Flights_Within_K_Stops.md).
  - Coming next: [`Count_Primes.md`](./Count_Primes.md), [`Find_the_Smallest_Binary_Digit_Multiple_of_Given_Number.md`](./Find_the_Smallest_Binary_Digit_Multiple_of_Given_Number.md), [`Minimum_Weight_Cycle.md`](./Minimum_Weight_Cycle.md).
