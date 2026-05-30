# Remove All Adjacent Duplicates in String — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Remove_All_Adjacent_Duplicates_in_String.md`](../Remove_All_Adjacent_Duplicates_in_String.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/remove-all-adjacent-duplicates-in-string/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/remove-all-adjacent-duplicates-in-string/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~18 minutes. This is **the canonical stack-as-cancellation pattern**: as you walk a sequence, the next element "cancels" the top of the stack if they match. Cascading cancellations (one cancel exposes a new top that might cancel against the next) handle automatically. The pattern transfers to Asteroid Collision, Score of Parentheses, simplifying file paths, and more. **Read [`Valid_Parentheses.md`](./Valid_Parentheses.md) first.**

**Map of this file (9 short sections):**

1. Read the problem
2. The brute force and the cascading-removal trap
3. The pivot — build the result left-to-right with a stack
4. Why this handles cascades automatically
5. Code
6. Trace it
7. Common pitfalls
8. The shape — stack-as-cancellation
9. Cross-references

---

## 1. Read the problem

You're given a string `s` of lowercase English letters. **Repeatedly remove any two adjacent equal characters until no such pair remains.** Return the result.

**Important:** removals cascade — after removing one pair, new adjacent duplicates may appear, and those should also be removed.

**Examples:**

- `s = "abbaca"`. Process:
  - `"abbaca"` — see `bb`, remove → `"aaca"`.
  - `"aaca"` — see `aa`, remove → `"ca"`.
  - No more pairs. Return `"ca"`.

- `s = "azxxzy"`. Process:
  - `xx` removed → `"azzy"`.
  - `zz` removed → `"ay"`. Return `"ay"`.

- `s = "aaaa"`. Process:
  - `aa` → `"aa"`. `aa` → `""`. Return `""`.

- `s = "abc"`. No duplicates. Return `"abc"`.

---

## 2. The brute force and the cascading-removal trap

**Naïve:** repeatedly scan the string for any adjacent duplicate; remove it; restart.

```python
while True:
    found = False
    for i in range(len(s) - 1):
        if s[i] == s[i + 1]:
            s = s[:i] + s[i + 2:]
            found = True
            break
    if not found:
        break
return s
```

Each scan is O(n). In the worst case (`"aaaa...aa"` with n/2 pairs), we do n/2 full scans → **O(n²)**. For `n = 10⁵`, that's `5 × 10⁹` ops. TLE.

The waste: each removal forces a rescan from the beginning. We re-check characters that haven't changed.

**The cascading-removal trap** also makes a "one-pass remove all adjacent pairs" approach wrong:

```python
# WRONG — one-pass mark-then-remove
i = 0
while i < len(s) - 1:
    if s[i] == s[i + 1]:
        s = s[:i] + s[i + 2:]
        # don't increment i — same position needs re-check
    else:
        i += 1
return s
```

This kind of works but is still O(n²) because string slicing is O(n) per removal.

There's a smarter approach using a stack.

---

## 3. The pivot — build the result left-to-right with a stack

**Pivot question:** instead of repeatedly modifying the string, can we **build the result one character at a time**, checking each incoming character against the LAST character we placed?

Imagine I'm typing out the result one character at a time, reading `s` from left to right. Each time I'm about to type a character `c`, I check: does `c` equal the last character I just typed?

- **Yes** → I've created an adjacent duplicate. Erase the last character (don't type `c` either). Both are gone.
- **No** → type `c` normally.

The "last character I typed" is the **top of a stack**. Type = push. Erase = pop.

```
stack = []
for c in s:
    if stack and stack.top() == c:
        stack.pop()                    # cancellation: both characters gone
    else:
        stack.push(c)                  # no cancellation: add new character
result = string from stack (bottom to top)
return result
```

The stack ends up containing the final string (in correct order, since we pushed from left to right).

**O(n) time** — each character is pushed at most once and popped at most once. **O(n) space** for the stack in the worst case.

---

## 4. Why this handles cascades automatically

The beauty: cascading removals are HANDLED FOR FREE.

When we pop the top due to a match with the incoming character `c`, the NEW top is whatever was just below. If the next character we read (after `c`) matches that new top, it'll cancel again on the next iteration.

> **Trace the cascade on `"abbaca"`:**
>
> ```
> stack = [].
>
> 'a': stack empty. push. stack = ['a'].
> 'b': top is 'a' ≠ 'b'. push. stack = ['a', 'b'].
> 'b': top is 'b' == 'b'. POP. stack = ['a'].
> 'a': top is 'a' == 'a'. POP. stack = [].         ← cascade! the freshly-exposed 'a' was canceled by the new 'a'.
> 'c': stack empty. push. stack = ['c'].
> 'a': top 'c' ≠ 'a'. push. stack = ['c', 'a'].
>
> Result: "ca". ✓
> ```

The cascade at characters 3 and 4 (`b` cancels `b`, then `a` cancels the freshly-exposed `a`) happens in TWO consecutive iterations of the loop. The stack naturally exposed the new top after the first pop; the next iteration's character handled it.

No retroactive scanning needed. No special-case logic. The stack semantics give us cascading cancellation for free.

---

## 5. Code

**C++ — using `std::string` as the stack** (clean, no separate container needed):

```cpp
string removeDuplicates(string s) {
    string result;
    for (char c : s) {
        if (!result.empty() && result.back() == c) {
            result.pop_back();
        } else {
            result.push_back(c);
        }
    }
    return result;
}
```

Eight lines. Why use `std::string` directly? Because:

- `result.back()` peeks at the last char (O(1)).
- `result.pop_back()` removes the last char (O(1)).
- `result.push_back(c)` adds a char (O(1) amortized).
- At the end, `result` is already in the correct order — no reversal needed.

**Python:**

```python
def removeDuplicates(s):
    stack = []
    for c in s:
        if stack and stack[-1] == c:
            stack.pop()
        else:
            stack.append(c)
    return ''.join(stack)
```

**JavaScript:**

```javascript
function removeDuplicates(s) {
    const stack = [];
    for (const c of s) {
        if (stack.length > 0 && stack[stack.length - 1] === c) {
            stack.pop();
        } else {
            stack.push(c);
        }
    }
    return stack.join('');
}
```

All O(n) time, O(n) space.

---

## 6. Trace it

**`s = "azxxzy"`:**

```
stack = [].

'a':  empty. push. stack = ['a'].
'z':  top 'a' ≠ 'z'. push. stack = ['a', 'z'].
'x':  top 'z' ≠ 'x'. push. stack = ['a', 'z', 'x'].
'x':  top 'x' == 'x'. POP. stack = ['a', 'z'].
'z':  top 'z' == 'z'. POP. stack = ['a'].   ← cascade
'y':  top 'a' ≠ 'y'. push. stack = ['a', 'y'].

Result: "ay".  ✓
```

The cascade fired at characters 4 and 5: the `xx` cancellation exposed `z`, and the next `z` canceled it.

**`s = "aaaa"`:**

```
'a':  push. stack = ['a'].
'a':  top 'a' == 'a'. POP. stack = [].
'a':  empty. push. stack = ['a'].
'a':  top 'a' == 'a'. POP. stack = [].

Result: "".  ✓
```

Even number of `a`s — everything cancels out.

**`s = "aaaaa"` (5 a's):**

```
'a': push. ['a'].
'a': pop. [].
'a': push. ['a'].
'a': pop. [].
'a': push. ['a'].

Result: "a".  ✓
```

Odd count — one character survives.

---

## 7. Common pitfalls

1. **Forgetting to check if the stack is empty before peeking.** Calling `.top()`, `.back()`, or `stack[-1]` on an empty stack is undefined behavior (C++) or an error (Python: `IndexError`).

2. **Pushing the character even when it matches.** Some candidates write `if match: pop; push` — but that LEAVES the new character on the stack, which is wrong. When characters match, BOTH should disappear.

3. **Trying to rescan after each removal.** Don't — the cascading-removal trap is exactly what the stack avoids. One forward pass handles all cascades.

4. **Using a separate stack PLUS a result string.** Redundant. The stack itself IS the result (just join the contents at the end).

5. **Reversing the stack at the end.** Unnecessary. We pushed from left to right, so the stack reads in left-to-right order from bottom to top. `string::push_back` + `pop_back` already maintains this. NO reversal needed.

6. **Trying to use regex or replace iteratively.** `s.replace("aa", "", 1)` in a loop works but is O(n²) — same as the original brute force.

7. **Confusing with `Remove K Adjacent Duplicates` (LC #1209).** That generalization requires removing k consecutive equal characters (not just 2). It needs a stack of `(char, count)` pairs.

---

## 8. The shape — stack-as-cancellation

The "match on top → pop both" pattern is one of the most reused stack idioms. Where else it appears:

| Problem | What "cancels" |
|---|---|
| **This problem** | adjacent equal characters |
| Valid Parentheses | opener with matching closer |
| Backspace String Compare | a `#` character cancels the previous one |
| Asteroid Collision | a left-moving asteroid cancels a smaller right-moving one |
| Remove K Adjacent Duplicates | k consecutive equal characters |
| Simplify Path (LC #71) | `..` pops the previous directory; `.` and empty don't add |
| Decode String "3[a2[c]]" | `]` triggers expansion of the topmost group |
| Make The String Great (LC #1544) | adjacent chars with same letter different case cancel |

**Pattern to internalize:**

> "When a problem says 'process a sequence, and each new element interacts with the most recent element by combining or canceling,' use a stack. Compare incoming element to the top; if they combine/cancel, pop; otherwise push. Cascading interactions happen automatically across iterations."

The key recognition cue: **CASCADING REMOVAL**. If removing one pair can expose a new adjacent pair, you need the stack — naïve "scan once and skip pairs" won't work.

---

> **Self-check — the question to ask next time.**
>
> When you face a problem where you process a sequence one element at a time and **each new element can CANCEL or MERGE with the most recent element**, before nesting loops, ask:
>
> > **"Can I use a stack: push each element, but if the new one cancels the top, pop instead? Cascading cancellations handle themselves across iterations."**
>
> If yes, you've turned O(n²) cascading removals into O(n) with a stack.

---

## 9. Cross-references

- **Reference card (post-mastery):** [`../Remove_All_Adjacent_Duplicates_in_String.md`](../Remove_All_Adjacent_Duplicates_in_String.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Valid_Parentheses.md`](./Valid_Parentheses.md), [`Remove_Outermost_Parentheses.md`](./Remove_Outermost_Parentheses.md) — earlier stack problems.
  - Coming next: Min_Stack, Baseball_Game, Evaluate_Reverse_Polish_Notation.
  - Coming later: Daily_Temperatures, Largest_Rectangle_in_Histogram (monotonic stack).
