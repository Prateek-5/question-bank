# Longest Valid Parentheses — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Longest_Valid_Parentheses.md`](../Longest_Valid_Parentheses.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/longest-valid-parentheses/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~22 minutes. **The lesson: maintain a stack of INDICES of UNMATCHED positions, and use the gap to the previous unmatched index to compute valid-run lengths.** A senior-bar problem. **Read [`../../Stack/learn/Valid_Parentheses.md`](../../Stack/learn/Valid_Parentheses.md) first** for the stack-bracket-matching basics.

**Map of this file (10 short sections):**

1. Read the problem
2. The brute force
3. The pivot — stack of unmatched indices
4. Why the -1 "floor" sentinel
5. The algorithm
6. Code
7. Trace it
8. The two-pass O(1)-space alternative
9. Common pitfalls
10. The shape — sentinels + index gaps

---

## 1. Read the problem

Given a string `s` containing ONLY the characters `'('` and `')'`, find the length of the **LONGEST contiguous substring** that forms a VALID parentheses expression.

**Examples:**

- `s = "(()"` → longest valid substring is `"()"` (length 2). Answer: **2**.
- `s = ")()())"` → longest is `"()()"` (length 4). Answer: **4**.
- `s = "()(())"` → entire string valid. Answer: **6**.
- `s = ""` → 0.

> **Mini-refresher: "valid" parentheses.**
>
> A valid (well-formed) parentheses string:
> - Every `(` has a matching `)` later.
> - Properly nested.
>
> Examples of valid: `""`, `"()"`, `"(())"`, `"()()"`, `"(()())"`.
>
> Examples of invalid: `"("`, `")"`, `")("`, `"(()"`.

---

## 2. The brute force

For every (l, r) substring, check if it's valid. Track the max length.

O(n²) substrings × O(n) validation = O(n³). Too slow.

Even validating each substring in O(n) total via prefix counts → O(n²). Still too slow for n = 30,000.

We need O(n). Two approaches: STACK or DP. We'll focus on stack.

---

## 3. The pivot — stack of unmatched indices

Maintain a stack of **INDICES of positions that are still UNMATCHED** (no partner yet).

- For an `(`: push its index (it's an opener awaiting a closer).
- For a `)`: try to match with the top.
  - If the top is an `(`'s index: pop it (match found).
  - If the top is itself a `)`'s index (an unmatched closer from earlier): push this `)`'s index (it can't be matched).

Hmm — that's not quite right. Let me restate.

The cleaner formulation:

**Push every `(`'s index. On `)`, pop the top.**
- If after the pop the stack is empty, the `)` has no opener — it CAN'T be matched. Push the `)`'s index (it becomes a new "barrier" between valid runs).
- If after the pop the stack is non-empty, the `)` paired up. The current valid run extends from `stack.top() + 1` to `i`, so length = `i - stack.top()`.

The stack stores indices of "barrier" characters: unmatched openers OR unmatched closers.

> **Mini-refresher: what the stack represents.**
>
> At any point, the stack holds indices that ANCHOR valid runs. Specifically, the top of the stack is the LAST UNMATCHED CHARACTER before position i. The valid run ending at i (if any) starts immediately AFTER the top.

---

## 4. Why the -1 "floor" sentinel

There's a corner case: what if a valid run starts from index 0?

Example: `"()"`. Position 0 = `(`, position 1 = `)`. When we process `)`:
- Pop the `(`'s index (0). Stack is now empty.
- We want to compute the run length as `1 - (something)`, where "something" represents "just before position 0," i.e., -1.

Without a sentinel, the stack is empty, and we'd need a special case ("length = i + 1").

**Solution:** initialize the stack with `-1`. This represents "the position before index 0." Now:
- The valid run ending at `i` has length `i - stack.top()`.
- For `"()"`: after processing `)`, stack = `[-1]`. Top = -1. Length = `1 - (-1) = 2`. ✓

---

## 5. The algorithm

```
stack = [-1]
best = 0

for i in 0..n-1:
    if s[i] == '(':
        stack.push(i)
    else:                              # s[i] == ')'
        stack.pop()
        if stack is empty:
            stack.push(i)              # ')' has no match; new barrier
        else:
            best = max(best, i - stack.top())

return best
```

**Loop invariants:**
- Stack contains indices of barriers (unmatched openers, unmatched closers, or the initial -1).
- The valid run ending at `i` (if any) is `[stack.top() + 1, i]`.

O(n) time, O(n) space.

---

## 6. Code

**C++:**

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
            if (st.empty()) {
                st.push(i);
            } else {
                best = max(best, i - st.top());
            }
        }
    }
    return best;
}
```

**Python:**

```python
def longestValidParentheses(s):
    stack = [-1]
    best = 0
    for i, ch in enumerate(s):
        if ch == '(':
            stack.append(i)
        else:
            stack.pop()
            if not stack:
                stack.append(i)
            else:
                best = max(best, i - stack[-1])
    return best
```

**JavaScript:**

```javascript
function longestValidParentheses(s) {
    const stack = [-1];
    let best = 0;
    for (let i = 0; i < s.length; i++) {
        if (s[i] === '(') {
            stack.push(i);
        } else {
            stack.pop();
            if (stack.length === 0) {
                stack.push(i);
            } else {
                best = Math.max(best, i - stack[stack.length - 1]);
            }
        }
    }
    return best;
}
```

Complexity: **O(n) time, O(n) space.**

---

## 7. Trace it

**`s = ")()())"`.**

```
Indices: 0=')', 1='(', 2=')', 3='(', 4=')', 5=')'.
Initial: stack = [-1]. best = 0.

i=0, ')': pop → stack=[]. Empty → push 0. stack=[0].
i=1, '(': push 1. stack=[0, 1].
i=2, ')': pop → stack=[0]. Not empty. best = max(0, 2 - 0) = 2.
i=3, '(': push 3. stack=[0, 3].
i=4, ')': pop → stack=[0]. best = max(2, 4 - 0) = 4.
i=5, ')': pop → stack=[]. Empty → push 5. stack=[5].

Return 4.  ✓
```

The "()()" at positions 1-4 has length 4 — matches.

**`s = "()(())"`.**

```
Initial: stack=[-1]. best=0.

i=0, '(': push 0. stack=[-1, 0].
i=1, ')': pop → stack=[-1]. best = max(0, 1 - (-1)) = 2.
i=2, '(': push 2. stack=[-1, 2].
i=3, '(': push 3. stack=[-1, 2, 3].
i=4, ')': pop → stack=[-1, 2]. best = max(2, 4 - 2) = 2.
i=5, ')': pop → stack=[-1]. best = max(2, 5 - (-1)) = 6.

Return 6.  ✓
```

The entire string is valid (length 6).

---

## 8. The two-pass O(1)-space alternative

There's a cute O(1)-space solution using two passes:

**Pass 1 (left to right):** track `open` and `close` counts.
- When `open == close`: record `2 * close` as a candidate length.
- When `close > open`: reset (both to 0).

**Pass 2 (right to left):** mirror.
- When `open == close`: record `2 * open`.
- When `open > close`: reset.

Why two passes? Pass 1 catches valid runs that end with a `)` deficit (e.g., `(())(`). Pass 2 catches ones with an `(` deficit (e.g., `(()`).

```python
def longestValidParentheses(s):
    best = 0
    open_, close_ = 0, 0

    for c in s:
        if c == '(': open_ += 1
        else: close_ += 1
        if open_ == close_:
            best = max(best, 2 * close_)
        elif close_ > open_:
            open_ = close_ = 0

    open_, close_ = 0, 0
    for c in reversed(s):
        if c == '(': open_ += 1
        else: close_ += 1
        if open_ == close_:
            best = max(best, 2 * open_)
        elif open_ > close_:
            open_ = close_ = 0

    return best
```

O(n) time, **O(1) space.** Memory-efficient, but the stack version is usually clearer.

---

## 9. Common pitfalls

1. **Forgetting the -1 sentinel.** Then the algorithm needs special case for valid runs starting at index 0.

2. **Pushing `(` indices but not pushing UNMATCHED `)` indices.** Both need to be pushed (the `)` becomes a barrier).

3. **Popping the `)` even when it can't be matched.** Don't — if the stack is empty after the pop (or you can't even pop), the `)` is unmatched and becomes a barrier.

4. **Counting CHARACTERS instead of indices.** The length is computed via index difference; values matter only for the if-branch.

5. **Confusing this with "is the WHOLE string valid?"** That's a simpler problem (Valid Parentheses). This is longest CONTIGUOUS valid SUBSTRING.

6. **Using a stack of characters instead of indices.** You need indices to compute lengths.

7. **Returning the stack's content instead of `best`.** The answer is the length, tracked separately.

8. **Off-by-one in length computation.** `i - stack.top()` is correct (not `i - stack.top() + 1` or `i - stack.top() - 1`).

---

## 10. The shape — sentinels + index gaps

Two patterns this problem teaches:

**Pattern 1: SENTINEL VALUES** to avoid edge cases.

A sentinel is a fake value that simplifies boundary logic. The `-1` in the stack represents "position before index 0." Many algorithms use sentinels:
- Linked list with dummy head.
- Prefix sum with sentinel `prefix[0] = 0`.
- Tree traversal with a dummy parent.
- Algorithms with `INT_MIN` / `INT_MAX` sentinels.

**Pattern 2: INDEX GAPS** to compute spans.

Tracking POSITIONS (not just values) lets you compute distances. When the stack pops, the new top is the most recent UNMATCHED position; the current position minus that gives the valid span length.

Where this pattern reappears:
- Largest Rectangle in Histogram (monotonic stack of indices; width = right - left - 1).
- Sliding Window Maximum (deque of indices; check staleness via index gap).
- Trapping Rain Water (stack of indices; water above bar = (right - left - 1) × min_height).

**Pattern to internalize:**

> "For 'longest valid SOMETHING' problems on strings/arrays, the answer often comes from MAX(index - prev_unmatched_index) across the walk. A stack-of-indices + sentinel handles this cleanly."

---

> **Self-check — the question to ask next time.**
>
> When you face "longest contiguous valid substring/sub-array," ask:
>
> > **"Can I track INDICES of UNMATCHED / BOUNDARY positions in a stack, and compute the answer as the max gap between consecutive boundaries?"**
>
> If yes, you've got an O(n) stack solution.

---

## Cross-references

- **Reference card (post-mastery):** [`../Longest_Valid_Parentheses.md`](../Longest_Valid_Parentheses.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`../../Stack/learn/Valid_Parentheses.md`](../../Stack/learn/Valid_Parentheses.md) — simpler version.
  - Coming next: [`Sliding_Window_Maximum.md`](./Sliding_Window_Maximum.md) — monotonic deque.
