# Stack — Concepts

## Core Theory
Stacks follow LIFO. They shine in problems with nested structure (parentheses) and in "next greater/smaller" sweeps via monotonic stacks.

## Common Patterns
- **Monotonic stack** for next greater / previous smaller.
- **Parentheses matching**.
- **Expression evaluation** (RPN).
- **Histogram largest rectangle**.

## When to Use
Whenever you need to remember context for a later operation, especially nested structure or bar-shaped scans.

## Template
```cpp
stack<int> st;
for (int i = 0; i < n; ++i) {
    while (!st.empty() && a[st.top()] < a[i]) st.pop();
    st.push(i);
}
```

## Common Mistakes
- Not accounting for unmatched elements at the end — use sentinels.
- Mixing index and value semantics.
- Recursion-based solutions overflowing stack with deep input.
