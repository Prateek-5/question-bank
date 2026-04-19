# Stack — Concepts Guide

----------------------------------------

## 1. Introduction

Stacks give LIFO (last-in-first-out) access. They shine in problems with nested structure (parentheses, expression evaluation) and in 'next greater / previous smaller' sweeps via **monotonic stacks** — a pattern that appears in dozens of interview favorites.

----------------------------------------

## 2. Real-Life Analogy

Think of a stack of trays in a cafeteria. The last tray placed is the first one taken. You can only access the top. That LIFO discipline turns out to be perfect for matching brackets, evaluating expressions, and resolving 'find the next bigger thing' questions.

----------------------------------------

## 3. Core Idea

A stack supports push, pop, and peek in O(1). A **monotonic stack** additionally maintains a sorted order: when inserting, pop elements that violate the order first. This technique resolves 'next greater element', 'previous smaller', and 'largest rectangle in histogram' in a single linear pass.

----------------------------------------

## 4. When to Use This (Pattern Recognition)

Signals for stacks:

- **Nested or matching structure** (parentheses, HTML tags).
- **Expression evaluation** (RPN, infix → postfix).
- **'Next/previous greater/smaller'** → monotonic stack.
- **'Largest rectangle in histogram'** → monotonic stack.
- **Simulating recursion iteratively.**

----------------------------------------

## 5. Types / Variations

- **Plain stack** for matching/parsing.
- **Monotonic increasing stack** (finds next smaller).
- **Monotonic decreasing stack** (finds next greater).
- **Two-stack approaches** (min stack, stack-queue simulation).

----------------------------------------

## 6. Step-by-Step Working

**Next greater element (monotonic decreasing stack):**
1. Iterate i from 0 to n-1.
2. While stack is non-empty and `a[stack.top()] < a[i]`: pop and record `answer[top] = a[i]`.
3. Push i.
4. After iteration, remaining stack elements have no next greater (answer = -1).

**Largest rectangle in histogram:**
1. Walk through bars; maintain an increasing-height stack of indices.
2. When a new bar is shorter, pop: for each popped bar, its rectangle's width is (current - stack.top() - 1).
3. Track the max area.

----------------------------------------

## 7. Visual Explanation

**Next greater element in [2, 1, 2, 4, 3]:**

```
i=0: stack=[0]  ([2])
i=1: a[1]=1 < a[0]=2, push; stack=[0,1]  ([2,1])
i=2: a[2]=2, pop 1 (a[1]=1<2): answer[1]=2
     a[2]=2 == a[0]=2, push; stack=[0,2]  ([2,2])
i=3: a[3]=4, pop 2 (2<4): answer[2]=4
     pop 0 (2<4): answer[0]=4
     push; stack=[3]  ([4])
i=4: a[4]=3<4, push; stack=[3,4]  ([4,3])

Remaining: 3 and 4 have no next greater → answer = -1
Final: [4, 2, 4, -1, -1]
```

----------------------------------------

## 8. Code Templates (C++)

```cpp
// Valid parentheses
bool isValid(string s) {
    stack<char> st;
    for (char c : s) {
        if (c == '(' || c == '[' || c == '{') st.push(c);
        else {
            if (st.empty()) return false;
            char t = st.top(); st.pop();
            if ((c == ')' && t != '(') ||
                (c == ']' && t != '[') ||
                (c == '}' && t != '{')) return false;
        }
    }
    return st.empty();
}

// Next greater element
vector<int> nextGreater(vector<int>& a) {
    int n = a.size();
    vector<int> res(n, -1);
    stack<int> st;
    for (int i = 0; i < n; ++i) {
        while (!st.empty() && a[st.top()] < a[i]) {
            res[st.top()] = a[i];
            st.pop();
        }
        st.push(i);
    }
    return res;
}
```

----------------------------------------

## 9. Common Mistakes

- **Not accounting for unmatched opens** at the end.
- **Mixing index and value semantics.**
- **Recursion-based solutions overflowing** on deep inputs — prefer iterative stacks.
- **Forgetting sentinels** that simplify end-of-array handling.

----------------------------------------

## 10. Interview Insights

Stack problems reward pattern recognition. Interviewers want to see:

1. **Quick identification of monotonic-stack patterns.**
2. **Clean invariants on the stack's order.**
3. **Correct sentinel use.**
4. **Linear-time reasoning** via amortized analysis.
