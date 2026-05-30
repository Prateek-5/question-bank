# Longest Valid Parentheses

**Problem Link:**
<a href="https://leetcode.com/problems/longest-valid-parentheses/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/longest-valid-parentheses/</a>

**Topic:**
Queues / Deque / Monotonic Queue (also: Stack, DP)

----------------------------------------

## Step 1: Define "Valid"

Given a string containing only `(` and `)`, find the length of the **longest contiguous substring** that forms a valid parentheses expression.

Valid = well-formed: every `(` has a matching `)` later, with proper nesting.

Example: `"(()"`. Valid substrings: `"()"` at positions 1-2. Longest = **2**.
Example: `")()())"`. Valid substrings: `"()"` (pos 1-2), `"()"` (pos 3-4), `"()()"` (pos 1-4). Longest = **4**.
Example: `"()(())"`. Entire string valid. Longest = **6**.

----------------------------------------

## Step 2: Tracking with a Stack

Classic idea: a stack of **indices**. Push `i` when we see `(`. Pop when we see `)`.

But naive popping loses length information. Trick: store **indices of unmatched positions** in the stack. After scanning, unmatched positions divide the string into "valid runs" — distances between consecutive unmatched indices give run lengths.

Even cleaner approach: **pre-populate the stack with -1** as a "floor" index (one before the start). Then:
- Push `i` when seeing `(`.
- On seeing `)`: pop. If the stack is now empty, push `i` (marks this `)` as a new "floor"). Otherwise, the current run's length = `i - stack.top()`.

----------------------------------------

## Step 3: Why the -1 Floor?

The valid run after an unmatched close-paren starts just **after** that close-paren. To compute the length of the valid run ending at index `i`, we need to know where it started — which is just after the most recent unmatched position.

The stack's top, after processing index `i`, holds the index of the most recent unmatched position (either an open-paren still awaiting a match, or a close-paren that had no match). The run ending at `i` has length `i - stack.top()`.

The initial -1 handles the case where the valid run starts from the very beginning of the string (index 0). Without it, we'd need a special case for "run from position 0."

----------------------------------------

## Step 4: Algorithm

```
stack = [-1]          # floor
best = 0

for i in 0..n-1:
    if s[i] == '(':
        push(i)
    else:             # s[i] == ')'
        pop()
        if stack is empty:
            push(i)              # ')' has no match; becomes new floor
        else:
            best = max(best, i - stack.top())

return best
```

Single pass. O(n) time, O(n) space (stack).

----------------------------------------

## Step 5: Trace on `")()())"`

Indices: 0=')', 1='(', 2=')', 3='(', 4=')', 5=')'.

```
stack = [-1]. best = 0.

i=0, s=')': pop (removes -1). Stack empty. Push 0. stack = [0].
i=1, s='(': push 1. stack = [0, 1].
i=2, s=')': pop (removes 1). stack = [0]. Not empty. best = max(0, 2 - 0) = 2.
i=3, s='(': push 3. stack = [0, 3].
i=4, s=')': pop (removes 3). stack = [0]. best = max(2, 4 - 0) = 4.
i=5, s=')': pop (removes 0). Stack empty. Push 5. stack = [5].
```

Return **4**. ✓

Walk-through check: the valid substring `"()()"` at positions 1..4 has length 4. ✓

----------------------------------------

## Step 6: Trace on `"()(())"`

Indices: 0='(', 1=')', 2='(', 3='(', 4=')', 5=')'.

```
stack = [-1]. best = 0.

i=0, s='(': push 0. stack = [-1, 0].
i=1, s=')': pop (removes 0). stack = [-1]. best = max(0, 1 - (-1)) = 2.
i=2, s='(': push 2. stack = [-1, 2].
i=3, s='(': push 3. stack = [-1, 2, 3].
i=4, s=')': pop (removes 3). stack = [-1, 2]. best = max(2, 4 - 2) = 2.
i=5, s=')': pop (removes 2). stack = [-1]. best = max(2, 5 - (-1)) = 6.
```

Return **6**. ✓ (Entire string is valid.)

Key moment: at i=5, pop clears out the index 2 (the outer `(`); stack.top() now = -1 (the floor). Length = 5 - (-1) = 6. The floor remembers "everything from index 0 onward is part of a run."

----------------------------------------

## Step 7: Alternative — DP

Define `dp[i]` = length of the longest valid substring ending at index i.

```
if s[i] == '(':
    dp[i] = 0   # can't end a valid substring with '('

elif s[i] == ')':
    if s[i-1] == '(':
        dp[i] = dp[i-2] + 2   # "()" extends the valid run from i-2
    elif s[i-1] == ')' and s[i - dp[i-1] - 1] == '(':
        dp[i] = dp[i-1] + 2 + dp[i - dp[i-1] - 2]
        # Close matches the '(' before the inner run, and we extend with anything before that
    else:
        dp[i] = 0
```

Same O(n) complexity, O(n) space. The stack version is usually cleaner to implement.

----------------------------------------

## Step 8: Alternative — Two-Pass Counting

Walk left-to-right tracking open/close counts; when close > open, reset. When equal, record the length (2 × open).

Walk right-to-left similarly; when open > close, reset. This catches cases like `"(()"` where left-to-right leaves open > close at the end without recording.

O(n) time, O(1) space — the most memory-efficient solution.

----------------------------------------

## Step 9: Name It

**Stack-based bracket matching with index floors**. A staple of parsing / compiler problems.

Related:
- Valid Parentheses (simpler: "is the whole string valid?").
- Generate Parentheses (enumerate valid strings).
- Score of Parentheses (evaluate nested expressions).

The "sentinel / floor" trick (-1 at the start) reduces edge-case clutter. General pattern in interval problems.

----------------------------------------

## Step 10: Complexity

Time: **O(n)**.
Space: **O(n)** for the stack. (O(1) for the two-pass counting variant.)

----------------------------------------

## Step 11: C++ Implementation (Stack Version)

```cpp
int longestValidParentheses(string s) {
    stack<int> st;
    st.push(-1);
    int best = 0;

    for (int i = 0; i < (int)s.size(); ++i) {
        if (s[i] == '(') {
            st.push(i);
        } else {
            st.pop();
            if (st.empty()) st.push(i);
            else best = max(best, i - st.top());
        }
    }
    return best;
}
```

Six lines of loop body. Key invariant: stack top holds the index just before the current valid run's start — or -1 if we're still in the initial run.

## Step 12: Two-Pass Alternative

```cpp
int longestValidParentheses(string s) {
    int best = 0, open = 0, close = 0;
    for (char c : s) {
        if (c == '(') open++; else close++;
        if (open == close) best = max(best, 2 * close);
        else if (close > open) open = close = 0;
    }
    open = close = 0;
    for (int i = s.size() - 1; i >= 0; --i) {
        if (s[i] == '(') open++; else close++;
        if (open == close) best = max(best, 2 * open);
        else if (open > close) open = close = 0;
    }
    return best;
}
```

No stack. The two passes handle asymmetric failures (more opens-than-closes is caught in the reverse pass, more closes than opens in the forward pass).

----------------------------------------

## Step 13: Follow-up Questions

- **Multiple bracket types ({}, [], ()).** Stack pairs types; longest valid substring tracks accordingly.
- **Return the valid substring itself.** Track the start of the best run; slice at the end.
- **Longest **sub-sequence** (non-contiguous) valid parens.** Different, simpler: count pairs of matched parens = min(opens, closes) × 2 (roughly).
- **Count how many longest valid substrings.** Track ties in best length.
- **Why does the stack's top always point to the "floor"?** Because when we pop on a match and something remains, what remains is the most recent unmatched opening *before* the current valid run. Extending the run "ends at i, starts just after stack.top()."
- **Edge case: empty string.** best stays 0. Correct.
