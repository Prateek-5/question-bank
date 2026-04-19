# Satisfiability of Equality Equations

## Problem Link
https://leetcode.com/problems/satisfiability-of-equality-equations/

## Topic
Graph BFS DFS Dijkstra DSU

## Core Concept
Union-Find — union equals, then check inequalities for contradictions.

## Intuition
Equalities form equivalence classes. Inequalities must separate classes. Process equalities first to build classes, then verify each inequality has endpoints in different classes.

## Detailed Explanation
For each '==' equation union the two variables. For each '!=' equation ensure find(a) != find(b). If any fails, return false.

## Dry Run
['a==b','b!=a']. Union a,b. Check a!=b: find(a)==find(b) → false.

## Approach
Two-pass DSU over 26 lowercase letters.

## Time and Space Complexity
Time: O(N α). Space: O(26).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
struct DSU { vector<int> p; DSU(int n):p(n){iota(p.begin(),p.end(),0);} int f(int x){return p[x]==x?x:p[x]=f(p[x]);} void u(int a,int b){p[f(a)]=f(b);} };

bool equationsPossible(vector<string>& eq) {
    DSU d(26);
    for (auto& e : eq) if (e[1]=='=') d.u(e[0]-'a', e[3]-'a');
    for (auto& e : eq) if (e[1]=='!' && d.f(e[0]-'a')==d.f(e[3]-'a')) return false;
    return true;
}
```

## Follow-up Questions
- Generalize to arbitrary variable names.
- Arithmetic relations (a - b = k).
- Incremental online constraints.
