# Valid Sudoku

## Problem Link
https://leetcode.com/problems/valid-sudoku/

## Topic
Hashing Sliding Window

## Core Concept
Three tracking sets — rows, cols, 3×3 boxes.

## Intuition
For each filled cell, record it in row, column, and box; any duplicate means invalid.

## Detailed Explanation
Use boolean[9][9] for row, col, box. For (i,j): d = board[i][j]-'1'; b = (i/3)*3 + j/3. If any of the three already true → invalid. Else mark them true.

## Dry Run
Standard valid Sudoku → true.

## Approach
Single pass.

## Time and Space Complexity
Time: O(81). Space: O(81).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
bool isValidSudoku(vector<vector<char>>& b) {
    bool r[9][9] = {}, c[9][9] = {}, bx[9][9] = {};
    for (int i = 0; i < 9; ++i) for (int j = 0; j < 9; ++j) if (b[i][j] != '.') {
        int d = b[i][j] - '1', k = (i/3)*3 + j/3;
        if (r[i][d] || c[j][d] || bx[k][d]) return false;
        r[i][d] = c[j][d] = bx[k][d] = true;
    }
    return true;
}
```

## Follow-up Questions
- Sudoku solver (backtracking).
- Bigger boards (16x16).
- Partial validation.
