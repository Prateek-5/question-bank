# Top K Frequent Elements

## Problem Link
https://leetcode.com/problems/top-k-frequent-elements/

## Topic
Heap Priority Queue

## Core Concept
Frequency map + min-heap of size k (or bucket sort by frequency).

## Intuition
We want the k most frequent values. Count frequencies, then keep only the top k. A min-heap of size k filters efficiently, or buckets indexed by frequency give O(n).

## Detailed Explanation
Build a hash map {value: count}. Push (count, value) into a min-heap; pop when size > k. Final heap holds top-k. Bucket approach: create n+1 buckets; place each value into buckets[count]; scan from high to low and collect k.

## Dry Run
nums=[1,1,1,2,2,3], k=2. Counts: {1:3,2:2,3:1}. Heap filter: push 1(3),2(2),3(1), pop smallest (3,1). Remaining heap {2:2,1:3}. Answer: [1,2].

## Approach
Bucket sort by frequency for O(n), or heap for O(n log k).

## Time and Space Complexity
Heap: O(n log k). Bucket: O(n).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;

vector<int> topKFrequent(vector<int>& nums, int k) {
    unordered_map<int,int> cnt;
    for (int x : nums) cnt[x]++;
    using P = pair<int,int>; // {count, value}
    priority_queue<P, vector<P>, greater<P>> pq;
    for (auto& [v, c] : cnt) {
        pq.push({c, v});
        if ((int)pq.size() > k) pq.pop();
    }
    vector<int> res;
    while (!pq.empty()) { res.push_back(pq.top().second); pq.pop(); }
    return res;
}
```

## Follow-up Questions
- Return the top-k least frequent.
- Stream version with updates.
- Tie-breaking by lexicographic order.
