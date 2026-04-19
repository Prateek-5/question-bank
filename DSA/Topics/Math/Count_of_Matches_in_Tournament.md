# Count of Matches in Tournament

## Problem Link
https://leetcode.com/problems/count-of-matches-in-tournament/

## Topic
Math

## Core Concept
Single-elimination: total matches = n - 1.

## Intuition
Every match eliminates exactly one team. To go from n teams down to 1 champion, exactly n-1 teams must be eliminated, hence n-1 matches.

## Detailed Explanation
Whether the bracket has byes or not, the invariant holds: each match produces one loser. Therefore the answer is simply n-1, regardless of how odd n is handled.

## Dry Run
n=7: matches = 6. (Round 1: 3 matches + 1 bye → 4 teams; Round 2: 2 matches → 2 teams; Round 3: 1 match. Total 6.)

## Approach
Direct formula n-1.

## Time and Space Complexity
O(1).

## C++ Implementation
```cpp
int numberOfMatches(int n) { return n - 1; }
```

## Follow-up Questions
- Double elimination tournaments.
- Round-robin: C(n,2) matches.
- Best-of-k series: multiply by k.
