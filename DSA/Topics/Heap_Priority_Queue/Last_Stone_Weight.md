# Last Stone Weight

## Problem Link
https://leetcode.com/problems/last-stone-weight/

## Topic
Heap Priority Queue

## Core Concept
Max-heap — repeatedly smash the two largest stones.

## Intuition
Each round we need the two largest stones. A max-heap answers this in O(log n). The remaining difference is pushed back. Repeat until ≤1 stone.

## Detailed Explanation
Push all stones into a max-heap. Pop top two (y ≥ x). If y != x, push y − x. Continue until fewer than two stones remain. Return 0 if empty, else the top.

## Dry Run
stones=[2,7,4,1,8,1]. Heap top order: 8,7 → push 1. Heap=[4,2,1,1,1]. Pop 4,2 → push 2 → [2,1,1,1]. Pop 2,1 → push 1 → [1,1,1]. Pop 1,1 → nothing → [1]. Answer=1.

## Approach
Greedy with a max-heap. Each iteration is O(log n). Correct because the optimal strategy is fixed — always smash the two largest.

## Time and Space Complexity
Time: O(n log n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;

int lastStoneWeight(vector<int>& stones) {
    priority_queue<int> pq(stones.begin(), stones.end());
    while (pq.size() > 1) {
        int y = pq.top(); pq.pop();
        int x = pq.top(); pq.pop();
        if (y != x) pq.push(y - x);
    }
    return pq.empty() ? 0 : pq.top();
}
```

## Follow-up Questions
- Last Stone Weight II — can we split into two subsets with minimal difference? (DP/subset-sum.)
- What if smashing allows partial destruction?
- Stream version: stones arrive online.
