# Recursion — Concepts Guide

----------------------------------------

## 1. Introduction

Recursion is the natural language of self-similar problems. A function calls itself on a smaller version of the input, combines results, and returns. Once you internalize the recipe — base case, recursive case, combine — a huge slice of interview problems becomes writable almost by reflex.

----------------------------------------

## 2. Real-Life Analogy

Think of Russian nesting dolls. To count the dolls, you open one and 'ask' the inner doll how many it contains — then add 1 for yourself. Each doll delegates the counting to its inside. That's recursion: solve by delegating to smaller versions of yourself.

----------------------------------------

## 3. Core Idea

Recursion has three parts: (1) a **base case** that solves the smallest input directly, (2) a **recursive call** on a smaller version, (3) a **combine step** that uses the recursive result. The key discipline is ensuring the recursive call actually shrinks the input — otherwise you have infinite recursion. Backtracking is a recursion pattern that tries a choice, recurses, then *undoes* the choice before trying the next.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Recursion is natural when:

- **The problem has self-similar subproblems** (trees, subsets, permutations).
- **Divide-and-conquer** fits.
- **Backtracking exploration** of a state space.
- **Problems defined recursively** (Fibonacci, factorial).

If subproblems overlap, add memoization and you have DP.

----------------------------------------

## 5. Types / Variations

- **Plain recursion** for divide-and-conquer.
- **Backtracking** (try, recurse, undo) for enumeration.
- **Memoized recursion** (top-down DP).
- **Tail recursion** (can be iteratively rewritten).

----------------------------------------

## 6. Step-by-Step Working

**Generic recursion recipe:**
1. Write the base case — what's the smallest input's answer?
2. Write the recursive case — how does a non-base input decompose?
3. Combine child results with the current input.
4. Verify the recursion terminates (input always shrinks).

**Backtracking recipe:**
1. If the current state is a valid solution, record it.
2. For each possible next choice:
   - Apply the choice (update state).
   - Recurse.
   - Undo the choice (revert state).

----------------------------------------

## 7. Visual Explanation

**Subsets of [1, 2, 3] via backtracking:**

```
start: []
  choose 1:        [1]
    choose 2:      [1,2]
      choose 3:    [1,2,3]  record
      undo 3
    undo 2
    choose 3:      [1,3]    record
    undo 3
  undo 1
  ... etc.

All subsets: [], [1], [2], [3], [1,2], [1,3], [2,3], [1,2,3]
```

----------------------------------------

## 8. Code Templates (C++)

```cpp
// Simple recursion (factorial)
int fact(int n) {
    if (n <= 1) return 1;
    return n * fact(n - 1);
}

// Backtracking template
void bt(State& s, vector<Solution>& results) {
    if (isGoal(s)) { results.push_back(snapshot(s)); return; }
    for (auto choice : choices(s)) {
        if (!feasible(s, choice)) continue;
        apply(s, choice);
        bt(s, results);
        undo(s, choice);
    }
}

// Subsets (classic backtracking)
void dfs(vector<int>& a, int start, vector<int>& cur, vector<vector<int>>& res) {
    res.push_back(cur);
    for (int i = start; i < (int)a.size(); ++i) {
        cur.push_back(a[i]);
        dfs(a, i + 1, cur, res);
        cur.pop_back();
    }
}
```

----------------------------------------

## 9. Common Mistakes

- **Missing or wrong base case** — infinite recursion or wrong answer.
- **Forgetting to undo state** in backtracking.
- **Stack overflow on deep recursion.**
- **Redundant work** without memoization when subproblems overlap.

----------------------------------------

## 10. Interview Insights

Recursion problems reveal your comfort with self-reference. Interviewers want to see:

1. **Clear statement of base case and recursive case.**
2. **Explicit parameter choices** (what defines a subproblem?).
3. **Clean state-undo in backtracking.**
4. **Awareness of when to add memoization.**

If your recursion feels hard to write, you likely haven't nailed the state. Spend another minute on that before coding.
