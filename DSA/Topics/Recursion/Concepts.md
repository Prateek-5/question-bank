# Recursion — Concepts

## Core Theory
Recursion expresses a problem in terms of smaller instances. Essential ingredients: base case, recursive case, and progress toward the base. Often paired with backtracking to explore combinatorial spaces.

## Common Patterns
- **Divide-and-conquer**: split, solve, combine.
- **Backtracking**: try, recurse, undo.
- **Tail recursion**: can be rewritten iteratively.

## When to Use
For tree/graph traversals, combinatorial enumeration, and any naturally self-similar problem. Beware deep recursion — convert to iterative with explicit stack when depth ~ n.

## Template
```cpp
void dfs(State s, vector<State>& out) {
    if (done(s)) { out.push_back(s); return; }
    for (Move m : moves(s)) { apply(s, m); dfs(s, out); undo(s, m); }
}
```

## Common Mistakes
- Missing or wrong base case.
- Forgetting to undo state after recursive call.
- Stack overflow on deep recursion — use iterative when possible.
