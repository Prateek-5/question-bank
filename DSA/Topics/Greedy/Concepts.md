# Greedy — Concepts Guide

----------------------------------------

## 1. Introduction

Greedy algorithms are deceptively simple: at each step, make the locally optimal choice and hope it leads to a globally optimal answer. Sometimes it does, sometimes it doesn't — and that's the hard part. The discipline of a greedy algorithm is proving that the local choice is safe.

----------------------------------------

## 2. Real-Life Analogy

Think of packing for a trip with a weight limit. A greedy strategy: pack the most valuable item you can still afford, repeat. For some problems this is optimal (e.g., items are infinitely divisible). For others it isn't (the classic 0/1 knapsack). Recognizing which is which is the core skill.

----------------------------------------

## 3. Core Idea

Greedy works when the problem has the **greedy-choice property** (a globally optimal solution contains the local greedy pick) and **optimal substructure** (optimal solutions for the whole are built from optimal solutions for parts). When both hold, sort or heap-prioritize by the right key, pick greedily, and move on. Proving it requires an exchange argument: show that swapping any other choice with the greedy choice doesn't make things worse.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Signals that suggest greedy:

- **'Minimum' or 'maximum' with no overlap complications.**
- **Scheduling, interval, or resource-allocation problems.**
- **Huffman-style problems** (combine two smallest).
- **Problems where local and global optimum visibly align.**

When greedy is wrong, DP is almost always right. If your greedy produces a wrong answer on a small test case, abandon it — don't patch.

----------------------------------------

## 5. Types / Variations

- **Activity Selection / Interval Scheduling:** sort by end time, pick earliest-ending non-overlapping.
- **Huffman coding / Connect ropes:** min-heap of two smallest.
- **Fractional knapsack:** sort by value/weight ratio.
- **Job scheduling with deadlines:** sort by deadline (or by profit, depending on variant).
- **Minimum spanning tree:** Kruskal's uses edge-sorted greedy; Prim's uses heap-frontier greedy.

----------------------------------------

## 6. Step-by-Step Working

**Interval Scheduling:**
1. Sort intervals by end time ascending.
2. Pick the first (earliest-ending) interval.
3. For each subsequent interval, if its start is ≥ the last picked interval's end, pick it.
4. Skip otherwise.

**Huffman merge cost:**
1. Put all weights in a min-heap.
2. Extract the two smallest, combine their sum, push back.
3. Accumulate the combined sum as cost.
4. Repeat until one element remains.

----------------------------------------

## 7. Visual Explanation

**Interval scheduling on [ [1,3], [2,4], [3,5], [5,7] ]:**

```
Sort by end:  [1,3] [2,4] [3,5] [5,7]

Pick [1,3]: accepted
[2,4]: start 2 < 3, skip
[3,5]: start 3 ≥ 3, accept, last end = 5
[5,7]: start 5 ≥ 5, accept

Final kept: [1,3], [3,5], [5,7]  → 3 intervals
```

----------------------------------------

## 8. Code Templates (C++)

```cpp
// Interval scheduling (max non-overlapping)
sort(intervals.begin(), intervals.end(),
     [](const auto& a, const auto& b) { return a[1] < b[1]; });
int lastEnd = INT_MIN, count = 0;
for (auto& iv : intervals) {
    if (iv[0] >= lastEnd) {
        count++;
        lastEnd = iv[1];
    }
}

// Huffman-style min cost to merge
priority_queue<long long, vector<long long>, greater<long long>> pq;
for (int x : weights) pq.push(x);
long long cost = 0;
while (pq.size() > 1) {
    long long a = pq.top(); pq.pop();
    long long b = pq.top(); pq.pop();
    cost += a + b;
    pq.push(a + b);
}
```

----------------------------------------

## 9. Common Mistakes

- **Applying greedy without proof.** It feels right, but produces wrong answers on adversarial inputs.
- **Wrong sort key.** 'Sort by start' vs 'sort by end' drastically changes correctness for interval problems.
- **Not handling ties.** Decide the tie-break rule explicitly.
- **Confusing greedy with DP.** If local choices interact, you probably need DP.

----------------------------------------

## 10. Interview Insights

Greedy problems test whether you can justify your algorithm, not just state it. Interviewers want to see:

1. **Can you articulate the greedy choice and why it's safe?**
2. **Can you sketch an exchange argument for correctness?**
3. **Can you recognize when greedy *doesn't* work and switch to DP?**
4. **Can you pick the right sort key?**

If you ever catch yourself saying 'I think this greedy works', try one or two small adversarial cases before coding. That five-minute test saves twenty-five minutes of debugging.
