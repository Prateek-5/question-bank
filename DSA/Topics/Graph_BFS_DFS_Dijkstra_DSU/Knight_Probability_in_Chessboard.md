# Knight Probability in Chessboard

## Problem Link
https://leetcode.com/problems/knight-probability-in-chessboard/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
DP over (moves_left, row, col) with transitions over 8 knight moves.

## Intuition
Probability of staying on board after k moves from (r,c) is average over 8 legal moves of the probability from those positions after k-1 moves. Base: p(0, r, c) = 1 if in-board else 0.

## Detailed Explanation
Let f(k, r, c) = probability. Transition: f(k, r, c) = (1/8) Σ f(k-1, r', c') over 8 moves (counting off-board as 0). Bottom-up DP over two layers.

## Dry Run
n=3, k=2, start (0,0). From (0,0) knight has 2 in-board moves: (1,2) and (2,1). Each contributes 1/8 * p(1,...). Expand recursively until 0 moves.

## Approach
DP with two 2D layers, rolling.

## Time and Space Complexity
Time: O(k·n²). Space: O(n²).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
double knightProbability(int n, int k, int r, int c) {
    vector<vector<double>> dp(n, vector<double>(n, 0));
    dp[r][c] = 1.0;
    int dr[] = {-2,-2,-1,-1,1,1,2,2}, dc[] = {-1,1,-2,2,-2,2,-1,1};
    for (int step = 0; step < k; ++step) {
        vector<vector<double>> nd(n, vector<double>(n, 0));
        for (int i=0;i<n;i++) for (int j=0;j<n;j++) if (dp[i][j] > 0) {
            for (int m=0;m<8;m++) {
                int ni=i+dr[m], nj=j+dc[m];
                if (ni>=0&&nj>=0&&ni<n&&nj<n) nd[ni][nj] += dp[i][j] / 8.0;
            }
        }
        dp = nd;
    }
    double s = 0;
    for (auto& row : dp) for (double v : row) s += v;
    return s;
}
```

## Follow-up Questions
- Expected number of steps to leave the board.
- Probability of reaching a target cell in ≤k moves.
- Variable-size board.
