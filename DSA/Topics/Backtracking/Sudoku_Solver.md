# Sudoku Solver

## Problem Link
https://leetcode.com/problems/sudoku-solver/

## Topic
Backtracking

## Core Concept
Backtracking with row/col/box masks.

## Intuition
Fill empty cells one at a time. For each, try digits 1–9; check validity with masks; recurse.

## Detailed Explanation
Maintain rowMask[9], colMask[9], boxMask[9] of used digits. DFS over empty cells trying 1–9 where masks allow.

## Dry Run
Standard 9x9 fills left-to-right, top-down.

## Approach
Backtracking with bitmasks.

## Time and Space Complexity
Exponential worst; fast with masking.

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
bool solve(vector<vector<char>>& b, int r, int c, int rm[9], int cm[9], int bm[9]) {
    if (r == 9) return true;
    if (c == 9) return solve(b, r+1, 0, rm, cm, bm);
    if (b[r][c] != '.') return solve(b, r, c+1, rm, cm, bm);
    int bi = (r/3)*3 + c/3;
    for (int d = 0; d < 9; ++d) {
        int bit = 1 << d;
        if ((rm[r] | cm[c] | bm[bi]) & bit) continue;
        b[r][c] = '1' + d;
        rm[r] |= bit; cm[c] |= bit; bm[bi] |= bit;
        if (solve(b, r, c+1, rm, cm, bm)) return true;
        b[r][c] = '.';
        rm[r] &= ~bit; cm[c] &= ~bit; bm[bi] &= ~bit;
    }
    return false;
}
void solveSudoku(vector<vector<char>>& b) {
    int rm[9] = {}, cm[9] = {}, bm[9] = {};
    for (int i = 0; i < 9; ++i) for (int j = 0; j < 9; ++j) if (b[i][j] != '.') {
        int d = b[i][j] - '1', bi = (i/3)*3 + j/3;
        rm[i] |= 1<<d; cm[j] |= 1<<d; bm[bi] |= 1<<d;
    }
    solve(b, 0, 0, rm, cm, bm);
}
```

## Follow-up Questions
- Count all solutions.
- Difficulty estimation via solve steps.
- 16×16 Sudoku.
