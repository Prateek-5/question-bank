# Minimum Cost to Connect Ropes

## Problem Link
https://leetcode.com/problems/minimum-cost-to-connect-sticks/

## Topic
Heap Priority Queue

## Core Concept
Min-heap (priority queue) — repeatedly combine the two smallest elements to minimize total cost.

## Intuition
Connecting two ropes costs the sum of their lengths. To minimize total cost, we always want the smallest ropes combined first so their lengths contribute to fewer future sums. This is exactly the Huffman-coding greedy idea: always merge the two smallest.

## Detailed Explanation
Push all rope lengths into a min-heap. Repeatedly pop the two smallest, sum them, add the sum to a running cost, and push the sum back. Stop when only one rope remains. Each merge's cost equals the sum of the two smallest currently available, which is provably optimal by an exchange argument.

## Dry Run
Ropes = [4, 3, 2, 6]. Heap = [2,3,4,6]. Pop 2 and 3, cost = 5, push 5 → heap [4,5,6]. Pop 4 and 5, cost += 9 = 14, push 9 → heap [6,9]. Pop 6 and 9, cost += 15 = 29. Answer = 29.

## Approach
Greedy with a min-heap. At each step pick the two minimums (O(log n) per op). The total cost accumulates as you build a Huffman-like binary tree of merges.

## Time and Space Complexity
Time: O(n log n) — n pushes and n pops each O(log n). Space: O(n) for the heap.

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;

long long minCost(vector<int>& ropes) {
    priority_queue<long long, vector<long long>, greater<long long>> pq;
    for (int x : ropes) pq.push(x);
    long long cost = 0;
    while (pq.size() > 1) {
        long long a = pq.top(); pq.pop();
        long long b = pq.top(); pq.pop();
        cost += a + b;
        pq.push(a + b);
    }
    return cost;
}
```

## Follow-up Questions
- What if we wanted the *maximum* cost instead? Use a max-heap.
- How would you do this with a k-way merge cost function?
- Can you reduce space using an already-sorted input?
