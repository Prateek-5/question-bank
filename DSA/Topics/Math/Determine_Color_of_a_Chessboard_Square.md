# Determine Color of a Chessboard Square

## Problem Link
https://leetcode.com/problems/determine-color-of-a-chessboard-square/

## Topic
Math

## Core Concept
Parity of (column_letter + row_number).

## Intuition
Chessboard colors alternate along both axes. A square is white if column index + row number is even — or equivalently, if their sum is odd when taking 'a'=1 the known rule inverts; careful with conventions.

## Detailed Explanation
Let c = coords[0] - 'a' (0-indexed column), r = coords[1] - '1' (0-indexed row). Return (c + r) % 2 == 0 ? false : true, where 'a1' is black (false). Alternatively: if (c + r) is odd → white.

## Dry Run
'a1': c=0, r=0, sum=0, even → black (false). 'h3': c=7, r=2, sum=9, odd → white (true).

## Approach
O(1) parity check.

## Time and Space Complexity
O(1).

## C++ Implementation
```cpp
bool squareIsWhite(string c) {
    return (c[0] + c[1]) % 2 == 1;
}
```

## Follow-up Questions
- Generalize to rectangular boards.
- Count squares of each color on an N×M grid.
- Knight's color-changing property between moves.
