# Find the Smallest Binary Digit Multiple of Given Number

## Problem Link
https://www.geeksforgeeks.org/dsa/find-the-smallest-binary-digit-multiple-of-given-number/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
BFS over remainders mod n with digits 0 and 1.

## Intuition
Numbers consisting only of 0/1 digits form a tree. BFS by appending '0' or '1' and tracking remainder mod n. The first remainder 0 we reach (with leading '1') gives the minimal-length answer.

## Detailed Explanation
Start with '1' remainder 1%n. BFS: from (rem, num_str), expand to (rem*10 % n, num+'0') and (rem*10+1 % n, num+'1'). Mark remainders visited. Return the string when rem==0.

## Dry Run
n=4. Start '1' rem=1. Expand '10' rem=2, '11' rem=3. Expand '100' rem=0 → return '100'.

## Approach
BFS with remainder memoization — at most n states.

## Time and Space Complexity
Time: O(n). Space: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
string smallestBinaryMultiple(int n) {
    queue<pair<int,string>> q; q.push({1 % n, "1"});
    vector<int> seen(n, 0); seen[1 % n] = 1;
    while (!q.empty()) {
        auto [r, s] = q.front(); q.pop();
        if (r == 0) return s;
        for (int d : {0, 1}) {
            int nr = (r * 10 + d) % n;
            if (!seen[nr]) { seen[nr] = 1; q.push({nr, s + char('0'+d)}); }
        }
    }
    return "";
}
```

## Follow-up Questions
- Multiples of n with digits only 0 and k.
- Smallest multiple with sum of digits ≤ s.
- Modular BFS general technique.
