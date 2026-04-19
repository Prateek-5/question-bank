# Longest Consecutive Sequence

## Problem Link
https://leetcode.com/problems/longest-consecutive-sequence/

## Topic
Hashing Sliding Window

## Core Concept
Hash set + sequence anchor (only start from sequence starts).

## Intuition
For each value v, it's the start of a sequence only if v-1 isn't in the set. From such starts, count consecutive values.

## Detailed Explanation
Insert all into set. For each v with (v-1) absent, extend upward counting v, v+1, ... while present. Track max.

## Dry Run
nums=[100,4,200,1,3,2]. Start at 1 → 1,2,3,4 length 4. Start at 100,200 lengths 1 each. Answer=4.

## Approach
Hash set, amortized O(n).

## Time and Space Complexity
Time: O(n) average. Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int longestConsecutive(vector<int>& a) {
    unordered_set<int> s(a.begin(), a.end());
    int best = 0;
    for (int v : s) if (!s.count(v - 1)) {
        int u = v, len = 1;
        while (s.count(u + 1)) { u++; len++; }
        best = max(best, len);
    }
    return best;
}
```

## Follow-up Questions
- Return the sequence.
- Consecutive with gap tolerance.
- Streaming variant.
