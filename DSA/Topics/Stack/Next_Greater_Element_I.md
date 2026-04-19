# Next Greater Element I

## Problem Link
https://leetcode.com/problems/next-greater-element-i/

## Topic
Stack

## Core Concept
Monotonic stack on nums2; map each value to its next greater.

## Intuition
Scan nums2, maintain a decreasing stack. When a larger value appears, all smaller on stack know their next greater.

## Detailed Explanation
For each x in nums2: while stack non-empty and top<x, map[st.top()]=x, pop. Push x. Then for nums1 look up map (default -1).

## Dry Run
nums2=[1,3,4,2]. map {1→3, 3→4, 4→-1, 2→-1}. nums1=[4,1,2] → [-1,3,-1].

## Approach
Monotonic stack + hashmap.

## Time and Space Complexity
Time: O(n1+n2). Space: O(n2).

## C++ Implementation
```cpp
#include <bits/stdc++.h>
using namespace std;
vector<int> nextGreaterElement(vector<int>& a, vector<int>& b) {
    unordered_map<int,int> nxt;
    stack<int> st;
    for (int x : b) {
        while (!st.empty() && st.top() < x) { nxt[st.top()] = x; st.pop(); }
        st.push(x);
    }
    vector<int> res;
    for (int x : a) res.push_back(nxt.count(x) ? nxt[x] : -1);
    return res;
}
```

## Follow-up Questions
- Next Greater Element II (circular).
- Previous greater element.
- Next Greater Node in linked list.
