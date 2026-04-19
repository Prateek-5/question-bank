# N-Queens

## Problem Link
https://leetcode.com/problems/n-queens/

## Topic
Recursion

## Core Concept
Backtracking placing one queen per row; track columns and diagonals.

## Intuition
Recurse row by row trying each column. Maintain sets for used columns and two diagonal keys (r+c, r-c).

## Detailed Explanation
cols[col], d1[r+c], d2[r-c+n]. For each row try columns; on success record. Undo on backtrack.

## Dry Run
n=4 → 2 distinct solutions.

## Approach
Classical backtracking.

## Time and Space Complexity
Time: O(N!). Space: O(N).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<vector<string>> solveNQueens(int n) {
    vector<vector<string>> res;
    vector<string> board(n, string(n, '.'));
    vector<int> cols(n, 0), d1(2*n, 0), d2(2*n, 0);
    function<void(int)> bt = [&](int r) {
        if (r == n) { res.push_back(board); return; }
        for (int c = 0; c < n; ++c) {
            if (cols[c] || d1[r+c] || d2[r-c+n]) continue;
            board[r][c] = 'Q';
            cols[c] = d1[r+c] = d2[r-c+n] = 1;
            bt(r+1);
            board[r][c] = '.';
            cols[c] = d1[r+c] = d2[r-c+n] = 0;
        }
    };
    bt(0);
    return res;
}
```

## Follow-up Questions
- N-Queens II (count only).
- Bitmask optimization.
- Place k queens in a larger board.
