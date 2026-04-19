# Knight Probability in Chessboard

**Problem Link:**
https://leetcode.com/problems/knight-probability-in-chessboard/

**Topic:**
Graph (BFS / DFS / Dijkstra / DSU)

----------------------------------------

## Step 1: Understand the Problem

On an `n × n` chessboard, a knight starts at cell `(row, column)`. The knight makes **exactly k moves**, each move chosen **uniformly at random** from the 8 possible knight moves. If a move would take the knight off the board, the knight is lost (doesn't rebounce).

Return the **probability** that the knight stays on the board for all k moves.

Example: n = 3, k = 2, start = (0, 0).

After move 1: 8 possible knight moves from (0, 0). Which stay on the 3×3 board?
- (+1, +2): (1, 2) — on board.
- (+2, +1): (2, 1) — on board.
- Others go negative or beyond 2. 6 moves off board.

So move 1 has 2/8 = 1/4 probability of staying.

If we're at (1, 2) after move 1 (prob 1/8):
- 8 knight moves from (1, 2). Which stay? 
- (-1, -2) → (0, 0) ✓, (-2, -1) → (-1, 1) ✗, etc. Let me enumerate. (1±1, 2±2) and (1±2, 2±1).
- (0, 0) ✓. (0, 4) ✗. (2, 0) ✓. (2, 4) ✗. (-1, 1) ✗. (-1, 3) ✗. (3, 1) ✗. (3, 3) ✗.
- 2 valid moves.

Similarly (2, 1) has 2 valid moves (symmetric).

So after 2 moves from (0, 0): 1/8 · 2/8 + 1/8 · 2/8 = 4/64 = 1/16.

Wait that's for landing at those specific cells. Total prob of being on board after 2 moves = (starting at (0,0), go to one of 8 choices, if on board go on). Let me reframe.

The expected answer for n=3, k=2, start=(0,0) is 0.0625. So 2/8 × 2/8 = 4/64 = 0.0625. ✓

----------------------------------------

## Step 2: Recurrence — Think Forward

Let `p(i, j, steps)` = probability of being at cell (i, j) after `steps` moves (starting from the initial cell).

Base: `p(row, col, 0) = 1`. All other cells at step 0 have probability 0.

Transition: to be at (i, j) after `s+1` moves, the knight was at some neighbor (i', j') of (i, j) after `s` moves, and chose the move that brings it to (i, j). That choice has probability 1/8 (each move equally likely).

```
p(i, j, s+1) = sum over (i', j') reachable-backward-from-(i,j) of p(i', j', s) × 1/8
```

Equivalently, knight-moves are symmetric (if A can reach B, B can reach A), so the reachable-backward neighbors are the 8 knight moves from (i, j).

Build the table step by step.

----------------------------------------

## Step 3: Or — Think Backward With "Surviving Probability"

A cleaner formulation:

Let `p(i, j, s)` = probability of staying on the board for the **remaining s moves**, starting from (i, j).

Base: `p(i, j, 0) = 1` (zero remaining moves — no risk of falling).

Transition: to stay on the board for s+1 moves, make one of the 8 knight moves. Each has 1/8 probability. For each move:
- If it lands on the board, continue with `p(ni, nj, s)`.
- If it goes off-board, contribute 0 (knight lost).

```
p(i, j, s+1) = sum over 8 moves of (1/8) × (p(ni, nj, s) if on-board else 0)
```

Answer: `p(row, col, k)`.

I prefer this backward DP — it's cleaner and initializes base cases trivially.

----------------------------------------

## Step 4: Implementation with Memoization

```
memo = {}
def p(i, j, s):
    if s == 0: return 1.0
    if (i, j, s) in memo: return memo[(i, j, s)]
    total = 0.0
    for each of 8 knight-moves (di, dj):
        ni, nj = i + di, j + dj
        if ni, nj on board:
            total += p(ni, nj, s - 1)
    result = total / 8
    memo[(i, j, s)] = result
    return result

return p(row, col, k)
```

O(n² · k) states, each with O(1) work (8 transitions). Total **O(n² · k)**.

For n ≤ 25 and k ≤ 100, that's at most 62500 states — very fast.

----------------------------------------

## Step 5: Trace for n = 3, k = 1, start = (0, 0)

```
p(0, 0, 1):
  Try 8 knight moves from (0, 0):
    (+1, +2) → (1, 2): on board. p(1, 2, 0) = 1.
    (+1, -2) → (1, -2): off board.
    (-1, +2) → (-1, 2): off board.
    (-1, -2) → (-1, -2): off board.
    (+2, +1) → (2, 1): on board. p(2, 1, 0) = 1.
    (+2, -1) → (2, -1): off board.
    (-2, +1) → (-2, 1): off board.
    (-2, -1) → (-2, -1): off board.
  total = 1 + 1 = 2.
  result = 2 / 8 = 0.25.
```

Return 0.25.

For k=2, we'd call p(0, 0, 2), which in turn calls p(1, 2, 1) and p(2, 1, 1) (the on-board neighbors from step 4), etc.

----------------------------------------

## Step 6: Bottom-Up Alternative

Can also do iteratively, filling a 2D table for each step.

```
# dp[i][j] = probability of being on board after 0 more moves (base)
dp = [[1.0 for _ in range(n)] for _ in range(n)]

for step in 1..k:
    new_dp = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in 0..n-1:
        for j in 0..n-1:
            total = 0
            for each (di, dj):
                ni, nj = i + di, j + dj
                if on-board(ni, nj): total += dp[ni][nj]
            new_dp[i][j] = total / 8
    dp = new_dp
return dp[row][col]
```

Equivalent, uses rolling tables for space O(n²).

----------------------------------------

## Step 7: Name It

**Probabilistic DP on a grid with backward time steps.** The recurrence "probability of surviving the next s moves" is natural for this kind of lattice random walk.

Similar patterns:
- Random walk on a grid with absorbing boundaries.
- Out-of-N Knight's Tour.
- Expected value computations with state-dependent transitions.

The `n²·k` state space is the signature.

----------------------------------------

## Step 8: Complexity

Time: **O(n² · k)** — n² cells × k steps × 8 transitions.
Space: O(n² · k) with full memoization, or O(n²) with rolling tables.

----------------------------------------

## Step 9: C++ Implementation

**Bottom-up with rolling tables:**

```cpp
double knightProbability(int n, int k, int row, int col) {
    vector<vector<double>> dp(n, vector<double>(n, 1.0));   // base: 0 moves left
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

Clean iterative DP. Each step builds `newDp` from the previous `dp`.

----------------------------------------

## Step 10: Follow-up Questions

- **Expected number of moves before falling off.** Different DP — compute expected stopping time.
- **Knight that can teleport (8 moves + teleport with some prob).** Add a teleport transition.
- **Larger board, many starting positions.** Precompute once; query in O(1).
- **Other pieces (rook, bishop, queen).** Different move set — plug into the same framework.
- **Graph representation.** The board is a graph where knight moves are edges. The algorithm is a DP on this graph.
- **Probability of reaching a specific target square in k moves.** Forward DP: p(i, j, s) = prob of being at (i, j) after s moves.
