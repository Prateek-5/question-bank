# Greedy — Concepts

## Core Theory
Greedy algorithms make a locally optimal choice at each step that also happens to lead to a global optimum. Correctness relies on either the **greedy-choice property** (a globally optimal solution contains a specific greedy choice) or a **matroid / exchange argument**.

## Common Patterns
- **Interval scheduling by end time** (activity selection, Non-overlapping Intervals).
- **Huffman-style two-smallest merges**.
- **Two-pointer pairing** for min-max problems after sorting.
- **Sweep-line counting** for concurrent resource usage.

## When to Use
When brute force is exponential and a careful local choice provably doesn't compromise future options. Verify by exchange argument before trusting a greedy.

## Template
```cpp
sort(intervals.begin(), intervals.end(), byEnd);
int last = INT_MIN, cnt = 0;
for (auto& iv : intervals) if (iv.start >= last) { last = iv.end; cnt++; }
```

## Common Mistakes
- Applying greedy without proof — DP is often safer.
- Wrong sort key (by start vs end vs length) changes correctness.
- Ignoring ties or boundary cases that break the invariant.
