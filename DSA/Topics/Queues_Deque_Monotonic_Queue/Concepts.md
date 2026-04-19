# Queues / Deque / Monotonic Queue — Concepts Guide

----------------------------------------

## 1. Introduction

Queues give us FIFO (first-in-first-out) access. Deques generalize to both ends. Monotonic deques add a twist: they only keep 'useful' candidates, giving us sliding window max/min in O(n).

----------------------------------------

## 2. Real-Life Analogy

Think of a line at a grocery counter. A queue: first in, first out. A deque: customers can join or leave from either end. A monotonic queue: a 'VIP line' where, as a VIP joins, any less-senior customer ahead of them is kicked out — so the line is always ordered by priority. That selectivity is what makes monotonic deques efficient.

----------------------------------------

## 3. Core Idea

A queue (FIFO) has O(1) push-back and pop-front. A deque (double-ended queue) has O(1) at both ends. A monotonic deque maintains elements in increasing or decreasing order: when inserting, pop everything that violates the order. Each element is inserted and popped once, giving amortized O(1) per operation and O(n) total for a pass over the array.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Reach for queues/deques when:

- **BFS** — always a queue.
- **Sliding window max/min in O(n)** — monotonic deque.
- **Implementing queue via stacks or vice versa** — classic interview.
- **Tasks arriving with priorities** — priority_queue (heap) rather than plain queue.

----------------------------------------

## 5. Types / Variations

- **Plain queue / deque** for BFS and general FIFO.
- **Monotonic increasing deque** for min queries.
- **Monotonic decreasing deque** for max queries.
- **Priority queue** (heap) when priority matters more than insertion order.

----------------------------------------

## 6. Step-by-Step Working

**Sliding window maximum (decreasing deque):**
1. For each index i:
   - Remove front if it's out of the window (index ≤ i - k).
   - Remove back while `a[back] ≤ a[i]` (they can never be the max).
   - Push i to the back.
   - If i ≥ k - 1, the max for this window is `a[dq.front()]`.

----------------------------------------

## 7. Visual Explanation

**Sliding window max for [1, 3, -1, -3, 5, 3, 6, 7], k=3:**

```
i=0, a[i]=1: dq=[0]
i=1, a[i]=3: pop 0 (a[0]=1<3), push 1; dq=[1]
i=2, a[i]=-1: push 2; dq=[1,2]  window max=3
i=3, a[i]=-3: push 3; dq=[1,2,3] window max=3
i=4, a[i]=5: pop 3,2,1 (all ≤5), push 4; dq=[4] window max=5
...

Final maxes: [3, 3, 5, 5, 6, 7]
```

----------------------------------------

## 8. Code Templates (C++)

```cpp
// BFS template
queue<int> q; q.push(src);
vector<int> dist(n, -1); dist[src] = 0;
while (!q.empty()) {
    int u = q.front(); q.pop();
    for (int v : g[u]) if (dist[v] == -1) {
        dist[v] = dist[u] + 1;
        q.push(v);
    }
}

// Sliding window maximum (monotonic decreasing deque)
vector<int> maxSlidingWindow(vector<int>& a, int k) {
    deque<int> dq; vector<int> res;
    for (int i = 0; i < (int)a.size(); ++i) {
        if (!dq.empty() && dq.front() <= i - k) dq.pop_front();
        while (!dq.empty() && a[dq.back()] <= a[i]) dq.pop_back();
        dq.push_back(i);
        if (i >= k - 1) res.push_back(a[dq.front()]);
    }
    return res;
}
```

----------------------------------------

## 9. Common Mistakes

- **Storing values instead of indices** in monotonic deques — losing the position info.
- **Wrong pop direction** for min vs max queues.
- **Using queue when deque is needed.**
- **Off-by-one in window bounds.**

----------------------------------------

## 10. Interview Insights

Queue/deque problems test whether you can design the right container for the job. Interviewers want to see:

1. **Recognition of monotonic-deque patterns** for O(n) sliding-window queries.
2. **Clean amortized analysis** (each element in/out once).
3. **Clear differentiation** between queue, deque, and priority queue.
