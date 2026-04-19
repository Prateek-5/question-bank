# Divisor Game

## Problem Link
https://leetcode.com/problems/find-the-divisor-game/

## Topic
Number Theory Misc

## Core Concept
Parity observation — Alice wins iff n is even.

## Intuition
Working backward, n=1 loses (no moves). n=2 wins. By induction, even → winning; odd → losing. So answer is n%2==0.

## Detailed Explanation
Return n%2==0 — Alice always picks 1, forcing Bob onto an odd number, and so on.

## Dry Run
n=2 → true. n=3 → false.

## Approach
Parity check.

## Time and Space Complexity
O(1).

## C++ Implementation
```cpp
bool divisorGame(int n) { return n % 2 == 0; }
```

## Follow-up Questions
- Divisor game with different rules.
- Game DP proof.
- Mis`ere variant.
