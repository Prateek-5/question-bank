# Valid Parentheses — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Valid_Parentheses.md`](../Valid_Parentheses.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** https://leetcode.com/problems/valid-parentheses/

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. **This is THE introduction to the stack data structure.** The lesson isn't memorizing "use a stack for parentheses" — it's recognizing WHY the stack matches the problem's structure: "the next closer must match the MOST RECENT unclosed opener." Once you see that mapping, you'll spot stacks in dozens of later problems.

**Map of this file (10 short sections):**

1. Read the problem
2. Why the brute force is harder than it looks
3. How would a human do this?
4. The data structure for "most recent" — meet the stack
5. The algorithm drops out
6. Trace it
7. Edge cases
8. Code
9. Common pitfalls
10. The shape — stack as "most recent" tracker

---

## 1. Read the problem

You're given a string `s` containing only bracket characters: `(`, `)`, `[`, `]`, `{`, `}`. Return `true` if the string is **valid** (balanced), `false` otherwise.

**Valid means:**

1. Every opening bracket has a matching closing bracket of the SAME TYPE.
2. Brackets close in the correct ORDER (the most recently opened must be closed first).
3. Every closing bracket has a corresponding earlier opening bracket.

**Examples:**

- `"()"` — valid.
- `"()[]{}"` — valid (three independent pairs).
- `"{[()]}"` — valid (nested).
- `"(]"` — INVALID (type mismatch).
- `"([)]"` — INVALID (wrong order — the `)` arrived before `]`, but the most recent opener is `[`).
- `"("` — INVALID (opener never closed).
- `")"` — INVALID (closer with no opener).
- `""` — VALID (empty string is vacuously balanced).

---

## 2. Why the brute force is harder than it looks

A first thought: "count parens. If `(` count equals `)` count, valid."

```
count_open = count of '(' in s
count_close = count of ')' in s
return count_open == count_close
```

**This fails immediately** on `"(]"` (different types) and on `")("` (right order: closer before opener — wrong!).

A more careful brute force: repeatedly find adjacent `()`, `[]`, or `{}` pairs and delete them, until no more pairs exist. Valid iff the final string is empty.

```
while True:
    if "()" in s: s = s.replace("()", "", 1)
    elif "[]" in s: s = s.replace("[]", "", 1)
    elif "{}" in s: s = s.replace("{}", "", 1)
    else: break
return s == ""
```

Works, but quadratic (each replacement scans and rebuilds the string). For `n = 10⁴`, that's `10⁸` ops — borderline.

There's a much cleaner one-pass algorithm. To find it, let me think about what makes the problem hard.

---

## 3. How would a human do this?

Forget code. Just imagine validating `{[()]}` by hand.

I read left-to-right:

```
'{' — note: I have an unclosed '{'.
'['  — note: I have unclosed '{' and '['. The MOST RECENT is '['.
'('  — most recent unclosed is now '('.
')' — closes the most recent unclosed (which was '('). Match? Yes. Now unclosed: '{', '['. Most recent: '['.
']' — closes most recent ('['). Match? Yes. Most recent: '{'.
'}' — closes most recent ('{'). Match? Yes. No more unclosed.
End: all closed. VALID.
```

The pattern: at every step, I only care about the **MOST RECENT UNCLOSED OPENER**. When a closer arrives, it must match THAT opener. Then I "remove" that opener and the previous one becomes the most recent.

This is the shape of the problem. We need a data structure that handles "track most recent" efficiently.

---

## 4. The data structure for "most recent" — meet the stack

> **Mini-refresher: what's a stack?**
>
> A **stack** is a data structure that follows the **LIFO (Last In, First Out)** rule. You can:
>
> - **`push(x)`** — add `x` to the top.
> - **`pop()`** — remove and return the top.
> - **`peek()` / `top()`** — look at the top without removing.
>
> Think of a stack of plates. You can only add or remove at the top. The bottom plates wait until the top ones are gone.
>
> All three operations are **O(1)**.
>
> Common implementations:
> - C++: `std::stack<T>`, or just `std::vector<T>` with `push_back` and `pop_back`.
> - Python: `list` with `append` and `pop`.
> - JavaScript: `Array` with `push` and `pop`.

For our problem:

- **Push** every opener as we encounter it.
- **When a closer arrives**, the most recent unclosed opener is `stack.top()`. Pop it and check it matches the closer.
- **At the end**, if any opener remains in the stack, those were never closed → invalid.

LIFO is exactly the "most recent unclosed" semantics. We didn't pick a stack because "bracket problems use stacks." We picked it because the structural rule of the problem MAPS DIRECTLY to LIFO behavior.

---

## 5. The algorithm drops out

```
stack = empty
for each character c in s:
    if c is an opener ('(', '[', or '{'):
        stack.push(c)
    else:    # c is a closer
        if stack is empty:
            return False                # closer with no opener
        top = stack.pop()
        if (c, top) is not a matching pair:
            return False                # wrong type
return stack is empty                   # any leftover openers → invalid
```

Pattern checks:

| Opener | Matching closer |
|---|---|
| `(` | `)` |
| `[` | `]` |
| `{` | `}` |

For each closer, check the pop'd top against the expected opener. If mismatched: return false.

---

## 6. Trace it

**`s = "{[()]}"`:**

```
stack = [].

'{':  opener. Push. stack = ['{'].
'[':  opener. Push. stack = ['{', '['].
'(':  opener. Push. stack = ['{', '[', '('].
')':  closer. Stack not empty. Pop '('. Match ')'? Yes. stack = ['{', '['].
']':  closer. Pop '['. Match ']'? Yes. stack = ['{'].
'}':  closer. Pop '{'. Match '}'? Yes. stack = [].

End. Stack empty. Return TRUE.  ✓
```

**`s = "([)]"`:**

```
stack = [].

'(':  opener. Push. stack = ['('].
'[':  opener. Push. stack = ['(', '['].
')':  closer. Pop '['. Match ')'? No! '[' should match ']'.

Return FALSE.  ✓ (correctly caught the wrong order)
```

**`s = "((("`:**

```
'(':  push. stack = ['('].
'(':  push. stack = ['(', '('].
'(':  push. stack = ['(', '(', '('].

End. Stack non-empty. Return FALSE.  ✓
```

**`s = "))"`:**

```
')':  closer. Stack empty. Return FALSE.  ✓
```

---

## 7. Edge cases

- **Empty string** `""`: the loop never runs; stack is empty at the end; return TRUE (vacuously valid).
- **Single character `"("`:** push, end with non-empty stack, return FALSE.
- **Single character `")"`:** closer on empty stack, immediately FALSE.
- **Odd length** (e.g., `"((("`): cannot be valid since every bracket needs a partner — but the algorithm catches this naturally (stack non-empty at end or empty when closer arrives). No special-case needed.

---

## 8. Code

**C++:**

```cpp
bool isValid(string s) {
    stack<char> st;
    for (char c : s) {
        if (c == '(' || c == '[' || c == '{') {
            st.push(c);
        } else {
            // c is a closer
            if (st.empty()) return false;
            char top = st.top();
            st.pop();
            if ((c == ')' && top != '(') ||
                (c == ']' && top != '[') ||
                (c == '}' && top != '{')) {
                return false;
            }
        }
    }
    return st.empty();
}
```

Twelve lines.

**C++ with a matching map (more extensible):**

```cpp
bool isValid(string s) {
    stack<char> st;
    unordered_map<char, char> closeToOpen = {
        {')', '('}, {']', '['}, {'}', '{'}
    };
    for (char c : s) {
        if (closeToOpen.count(c)) {                       // c is a closer
            if (st.empty() || st.top() != closeToOpen[c]) return false;
            st.pop();
        } else {                                            // c is an opener
            st.push(c);
        }
    }
    return st.empty();
}
```

**Python:**

```python
def isValid(s):
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    for c in s:
        if c in pairs:                       # closer
            if not stack or stack[-1] != pairs[c]:
                return False
            stack.pop()
        else:                                  # opener
            stack.append(c)
    return not stack
```

**JavaScript:**

```javascript
function isValid(s) {
    const stack = [];
    const pairs = { ')': '(', ']': '[', '}': '{' };
    for (const c of s) {
        if (c in pairs) {
            if (stack.length === 0 || stack[stack.length - 1] !== pairs[c]) {
                return false;
            }
            stack.pop();
        } else {
            stack.push(c);
        }
    }
    return stack.length === 0;
}
```

All O(n) time, O(n) space (worst case: all openers).

---

## 9. Common pitfalls

1. **Calling `top()` (or `back()`) on an empty stack.** In C++ this is undefined behavior. Always check `st.empty()` BEFORE accessing the top.

2. **Forgetting to check if the stack is empty at the end.** A string of all openers like `"(((("` will leave openers in the stack. Don't return `true` blindly after the loop.

3. **Using a counter instead of a stack.** A counter (incrementing on `(`, decrementing on `)`) works for SINGLE-type parentheses. For mixed types `(`, `[`, `{`, you NEED to remember which TYPE was opened. A counter loses that info.

4. **Returning on the first mismatch only.** Some implementations return `true` after a single successful match — wrong. Must check the ENTIRE string and the final stack state.

5. **Treating all closers as interchangeable.** Each closer must match its specific type of opener. `(` matches only `)`, not `]` or `}`.

6. **Trying recursion for "nesting feels recursive."** Recursion works but is heavier than a stack. The stack approach is canonical here.

7. **Confusing "balanced" with "equal counts."** `")("` has equal counts but is INVALID. Order matters.

---

## 10. The shape — stack as "most recent" tracker

The stack pattern in this problem generalizes to **any situation where the next event/element must interact with the MOST RECENT unresolved one**:

| Problem | What "opener" / "closer" means |
|---|---|
| **This problem** | bracket opener / closer |
| Evaluate Reverse Polish Notation | numbers pushed; operators pop the two most recent numbers |
| Daily Temperatures | each day's temp; when a warmer day arrives, pop colder days |
| Largest Rectangle in Histogram | bars pushed; when a shorter bar arrives, pop taller bars (compute rectangles) |
| Asteroid Collision | right-moving asteroids on the stack; left-movers can pop them |
| Decode String (e.g., "3[a2[c]]") | push state when encountering '['; pop and combine on ']' |
| Iterative tree traversal | push nodes; pop and process |
| Function call stack (in compilers / runtimes) | call frames pushed/popped |

**Pattern to internalize:**

> "When a problem's rules say 'the next event must resolve against the MOST RECENTLY UNRESOLVED prior event,' use a stack. Push on each new event; pop on resolution. Total work O(n) because each event is pushed and popped at most once."

The stack isn't a memorized "bracket problems use stacks" rote — it's the data structure whose semantics MATCH the problem's structure.

---

> **Self-check — the question to ask next time.**
>
> When you face a problem where elements arrive in order and the **next element interacts with the MOST RECENT unresolved prior one**, before nesting loops, ask:
>
> > **"Is this a stack problem? Can I push each element as it arrives, and pop when the next element 'resolves' or 'cancels' the top?"**
>
> If yes, you've turned what looks like O(n²) into O(n).

---

## Cross-references

- **Reference card (post-mastery):** [`../Valid_Parentheses.md`](../Valid_Parentheses.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - Coming next: Remove_Outermost_Parentheses (depth counter — stack reduced to a number), Remove_All_Adjacent_Duplicates_in_String (stack-based cancellation).
  - Coming later: Daily_Temperatures, Next_Greater_Element_I, Largest_Rectangle_in_Histogram — monotonic stack family.
