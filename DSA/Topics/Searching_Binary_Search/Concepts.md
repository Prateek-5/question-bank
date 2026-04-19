# Searching / Binary Search — Concepts Guide

----------------------------------------

## 1. Introduction

Binary search is one of the most elegant algorithms in CS — halving the search space each step, turning O(n) into O(log n). But classic binary search on sorted arrays is just the tip of the iceberg. The real power is **binary search on the answer**: reframe any problem where the answer space is monotonic, and binary search it.

----------------------------------------

## 2. Real-Life Analogy

You're guessing a number between 1 and 100. Every time you guess, you're told 'higher' or 'lower'. Do you scan 1, 2, 3, ...? No — you guess 50, then 25 or 75, then halve again. That's binary search. The same intuition applies to algorithms: if you can efficiently check 'is answer X feasible?' with a monotonic predicate, binary search the answer.

----------------------------------------

## 3. Core Idea

Binary search works on a **monotonic predicate**: `ok(x)` is false for all x < T and true for all x ≥ T (or vice versa). The search finds the boundary T in O(log range) feasibility checks. For sorted arrays, the predicate is 'is a[mid] ≥ target?'. For 'binary search on answer' problems, the predicate is problem-specific (capacity works? days enough?).

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Look for binary search when:

- **Input is sorted** (classic).
- **The answer space is numeric and monotonic** ('if X works, so does X+1').
- **Brute-force over the answer would be O(n·range)** and the range is huge.
- **Keywords:** 'minimum capacity', 'maximum rate', 'fewest days'.

----------------------------------------

## 5. Types / Variations

- **Classic binary search** for exact match.
- **Lower bound** — first index ≥ target.
- **Upper bound** — first index > target.
- **Binary search on answer** — search a numeric range with a feasibility function.
- **Binary search on a function** — find where f(x) crosses zero.
- **Exponential search** for unbounded arrays (double until overshoot, then binary search).

----------------------------------------

## 6. Step-by-Step Working

**Classic search for target:**
1. lo = 0, hi = n - 1.
2. While lo ≤ hi: m = (lo + hi) / 2.
3. If a[m] == target, return m.
4. If a[m] < target, lo = m + 1.
5. Else hi = m - 1.
6. Return -1 (not found).

**Binary search on answer (smallest X such that ok(X)):**
1. Pick lo and hi as the valid range of answers.
2. While lo < hi: m = (lo + hi) / 2.
3. If ok(m), hi = m.
4. Else lo = m + 1.
5. Return lo.

----------------------------------------

## 7. Visual Explanation

**Binary search for 7 in [1, 3, 5, 7, 9, 11]:**

```
[1, 3, 5, 7, 9, 11]
        ↑ mid=5, 5 < 7, go right

         [7, 9, 11]
              ↑ mid=9, 9 > 7, go left

         [7]
          ↑ found!
```

----------------------------------------

## 8. Code Templates (C++)

```cpp
// Classic binary search
int binary_search(vector<int>& a, int target) {
    int lo = 0, hi = a.size() - 1;
    while (lo <= hi) {
        int m = lo + (hi - lo) / 2;
        if (a[m] == target) return m;
        if (a[m] < target) lo = m + 1;
        else hi = m - 1;
    }
    return -1;
}

// Binary search on answer: smallest capacity so that ok(cap) is true
int lo = maxPackage, hi = totalSum;
while (lo < hi) {
    int m = lo + (hi - lo) / 2;
    if (ok(m)) hi = m;
    else lo = m + 1;
}
return lo;
```

----------------------------------------

## 9. Common Mistakes

- **Overflow in `(lo + hi) / 2`** for large ints — use `lo + (hi - lo) / 2`.
- **Off-by-one** in `while (lo < hi)` vs `while (lo <= hi)`.
- **Wrong branch update** causing infinite loops.
- **Misidentifying the monotonic predicate** — test it on 2–3 small cases.
- **Assuming sortedness that isn't there.**

----------------------------------------

## 10. Interview Insights

Binary search problems test precision. Interviewers want to see:

1. **Clean invariants** — state clearly what `lo` and `hi` mean.
2. **Correct boundary updates.**
3. **Recognition of 'binary search on answer'** for non-sorted-array problems.
4. **Awareness of overflow** and edge cases.

Always verify your binary search on the *smallest* possible input (size 0, 1, 2) — that's where off-by-one errors live.
