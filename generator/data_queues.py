DATA = {
"Gas Station": {
  "concept": "Greedy running-tank: if total gas ≥ total cost, starting station is the one after the last negative prefix.",
  "intuition": "If total gas - total cost < 0, no solution. Else a valid starting point exists; resetting start whenever tank goes negative finds it.",
  "explanation": "total=0, tank=0, start=0. For i: diff=gas[i]-cost[i]; total+=diff; tank+=diff; if tank<0: start=i+1, tank=0. Return total<0 ? -1 : start.",
  "dry_run": "gas=[1,2,3,4,5], cost=[3,4,5,1,2]. total=3. Reset points; final start=3.",
  "approach": "Single-pass greedy.",
  "complexity": "Time: O(n). Space: O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int canCompleteCircuit(vector<int>& g, vector<int>& c) {
    int tot = 0, tank = 0, start = 0;
    for (int i = 0; i < (int)g.size(); ++i) {
        int d = g[i] - c[i];
        tot += d; tank += d;
        if (tank < 0) { start = i + 1; tank = 0; }
    }
    return tot < 0 ? -1 : start;
}""",
  "followups": "- Multiple valid starts — find all.\n- Minimum refill stops given range.\n- Weighted gas tanks."
},

"Implement Queue using Stacks": {
  "concept": "Two stacks — in and out.",
  "intuition": "Push to 'in'. For peek/pop, if 'out' is empty transfer all from 'in' (reverses order), then operate on 'out'.",
  "explanation": "Push: in.push. Pop/Peek: if out empty, while in not empty move top to out. Then pop/peek out.",
  "dry_run": "Push 1,2. Pop: transfer to out=[2,1], pop 1. Push 3. Pop: out=[2], pop 2. Pop: out empty, transfer in=[3] → [3], pop 3.",
  "approach": "Amortized O(1) per op.",
  "complexity": "Amortized O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
class MyQueue {
    stack<int> in, out;
    void shift() { while (!in.empty()) { out.push(in.top()); in.pop(); } }
public:
    void push(int x) { in.push(x); }
    int pop() { if (out.empty()) shift(); int v = out.top(); out.pop(); return v; }
    int peek() { if (out.empty()) shift(); return out.top(); }
    bool empty() { return in.empty() && out.empty(); }
};""",
  "followups": "- Implement stack using queues.\n- Double-ended queue.\n- Concurrent queue."
},

"Implement Stack using Queues": {
  "concept": "Two queues or one-queue rotation.",
  "intuition": "One-queue approach: after every push, rotate queue by size-1 so the new element is always at front.",
  "explanation": "Push x: q.push(x); rotate size-1 times by pop-push. Top: q.front(). Pop: q.pop().",
  "dry_run": "Push 1 → [1]. Push 2 → [2,1]. Push 3 → [3,2,1]. Pop → 3.",
  "approach": "Queue rotation.",
  "complexity": "Push O(n), pop/top O(1).",
  "code": """#include <bits/stdc++.h>
using namespace std;
class MyStack {
    queue<int> q;
public:
    void push(int x) { q.push(x); for (int i = 0; i < (int)q.size() - 1; ++i) { q.push(q.front()); q.pop(); } }
    int pop() { int v = q.front(); q.pop(); return v; }
    int top() { return q.front(); }
    bool empty() { return q.empty(); }
};""",
  "followups": "- Use two queues.\n- Implement min-stack with queues.\n- Thread-safe version."
},

"Longest Valid Parentheses": {
  "concept": "Stack of indices with sentinel base.",
  "intuition": "Push -1 initially. On '(' push index. On ')' pop; if stack empty push current index as new base; else current length = i - stack.top().",
  "explanation": "Track best as we iterate.",
  "dry_run": "'(()' → stack starts [-1]. '(': [-1,0]. '(': [-1,0,1]. ')': pop 1 → [-1,0]; len=2-0=2. Best=2.",
  "approach": "Stack indexing.",
  "complexity": "Time: O(n). Space: O(n).",
  "code": """#include <bits/stdc++.h>
using namespace std;
int longestValidParentheses(string s) {
    stack<int> st; st.push(-1);
    int best = 0;
    for (int i = 0; i < (int)s.size(); ++i) {
        if (s[i] == '(') st.push(i);
        else {
            st.pop();
            if (st.empty()) st.push(i);
            else best = max(best, i - st.top());
        }
    }
    return best;
}""",
  "followups": "- Return the actual substring.\n- Count valid substrings.\n- Multiple bracket types."
},

"Sliding Window Maximum": {
  "concept": "Monotonic decreasing deque of indices.",
  "intuition": "Deque holds indices in decreasing value order. Front is current window max. Pop back smaller values to maintain order; pop front when out of window.",
  "explanation": "For each i: remove front if index <= i-k. While back's value <= nums[i]: pop back. Push i. If i>=k-1, record deque front value.",
  "dry_run": "nums=[1,3,-1,-3,5,3,6,7], k=3. Maxes: [3,3,5,5,6,7].",
  "approach": "Monotonic deque.",
  "complexity": "Time: O(n). Space: O(k).",
  "code": """#include <bits/stdc++.h>
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
}""",
  "followups": "- Sliding window minimum.\n- Sliding window median (two heaps).\n- First negative in window."
},
}
