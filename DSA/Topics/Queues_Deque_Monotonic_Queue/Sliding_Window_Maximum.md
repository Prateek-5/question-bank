# Sliding Window Maximum

## Problem Link
https://leetcode.com/problems/sliding-window-maximum/

## Topic
Queues Deque Monotonic Queue

## Core Concept
Monotonic decreasing deque of indices.

## Intuition
Deque holds indices in decreasing value order. Front is current window max. Pop back smaller values to maintain order; pop front when out of window.

## Detailed Explanation
For each i: remove front if index <= i-k. While back's value <= nums[i]: pop back. Push i. If i>=k-1, record deque front value.

## Dry Run
nums=[1,3,-1,-3,5,3,6,7], k=3. Maxes: [3,3,5,5,6,7].

## Approach
Monotonic deque.

## Time and Space Complexity
Time: O(n). Space: O(k).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<int> maxSlidingWindow(vector<int>& a, int k) {
    deque<int> dq;
    vector<int> res;
    for (int i = 0; i < (int)a.size(); ++i) {
        if (!dq.empty() && dq.front() <= i - k) dq.pop_front();
        while (!dq.empty() && a[dq.back()] <= a[i]) dq.pop_back();
        dq.push_back(i);
        if (i >= k - 1) res.push_back(a[dq.front()]);
    }
    return res;
}
```

## Follow-up Questions
- Sliding window minimum.
- Sliding window median (two heaps).
- First negative in window.
