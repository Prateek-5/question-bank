# Maximum XOR of Two Numbers

## Problem Link
https://leetcode.com/problems/maximum-xor-of-two-numbers-in-an-array/

## Topic
Trie Bit Manipulation Trie

## Core Concept
Bit Trie (size-2 branches) to pair bits maximizing XOR.

## Intuition
Insert each number's bits into a binary trie. For each number, traverse preferring the opposite bit at each level to maximize XOR.

## Detailed Explanation
Build a bit-trie (MSB to LSB). For each x, greedily pick child with bit (1 - xbit) where possible; accumulate XOR value.

## Dry Run
nums=[3,10,5,25,2,8]. Max XOR = 25 ^ 5 = 28.

## Approach
Bit-Trie with 32-level depth.

## Time and Space Complexity
Time: O(n·32). Space: O(n·32).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
int findMaximumXOR(vector<int>& a) {
    struct N { N* c[2] = {}; };
    N* root = new N();
    for (int x : a) { auto* n = root; for (int b = 31; b >= 0; --b) { int bit = (x >> b) & 1; if (!n->c[bit]) n->c[bit] = new N(); n = n->c[bit]; } }
    int best = 0;
    for (int x : a) {
        auto* n = root; int v = 0;
        for (int b = 31; b >= 0; --b) {
            int want = 1 - ((x >> b) & 1);
            if (n->c[want]) { v |= (1 << b); n = n->c[want]; }
            else n = n->c[1 - want];
        }
        best = max(best, v);
    }
    return best;
}
```

## Follow-up Questions
- Max XOR of subarray.
- Max XOR with at most k modifications.
- Min XOR pair.
