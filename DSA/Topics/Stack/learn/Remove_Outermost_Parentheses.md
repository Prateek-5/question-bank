# Remove Outermost Parentheses — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Remove_Outermost_Parentheses.md`](../Remove_Outermost_Parentheses.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/remove-outermost-parentheses/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/remove-outermost-parentheses/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~15 minutes. The lesson: **when you only need the SIZE of a stack (not its contents), you can replace the stack with a simple counter**. This "stack-degenerates-to-counter" trick is one of the most reusable optimizations in stack problems. **Read [`Valid_Parentheses.md`](./Valid_Parentheses.md) first** so the stack mental model is solid.

**Map of this file (9 short sections):**

1. Read the problem
2. What's a "primitive" decomposition?
3. The natural stack approach
4. Why we don't need the stack's CONTENTS — only its depth
5. Code
6. Trace it
7. Common pitfalls
8. The shape — counter instead of stack
9. Cross-references

---

## 1. Read the problem

You're given a string `s` that is a **valid** parentheses string (balanced — every `(` has a matching `)`). You can decompose `s` into one or more **"primitive"** parentheses strings concatenated. A primitive is a non-empty valid parentheses string that CANNOT be split further into multiple valid parentheses strings.

**Remove the outermost `(` and `)` of each primitive, then concatenate. Return the result.**

> **Mini-refresher: "primitive" in this problem.**
>
> Think of `s` as broken into the LARGEST valid pieces that, when concatenated, give `s`. Each piece is "primitive."
>
> Examples:
> - `"(())"` is ONE primitive (the outermost `(` and `)` wrap the whole thing).
> - `"()()"` is TWO primitives: `"()"` and `"()"`.
> - `"(()())"` is ONE primitive (the outer `(` and `)` wrap two inner `()`s).
> - `"(()())(())"` is TWO primitives: `"(()())"` and `"(())"`.
>
> The "boundary" between primitives is where the nesting depth returns to 0.

**Example:** `s = "(()())(())"`.

Decompose:
- Primitive 1: `"(()())"`. Strip outermost: `"()()"`.
- Primitive 2: `"(())"`. Strip outermost: `"()"`.

Concatenate: `"()()" + "()" = "()()()"`. Return that.

**Another example:** `s = "(()())(())(()(()))"`.

Primitives: `"(()())"`, `"(())"`, `"(()(()))"`. After stripping: `"()()"`, `"()"`, `"()(())"`. Concatenated: `"()()" + "()" + "()(())" = "()()()()(())"`.

---

## 2. What's a "primitive" decomposition?

A primitive starts when the nesting depth goes from 0 to 1 (a `(` arrives while depth is 0). It ends when depth returns to 0 (a `)` brings depth back down).

> **Mini-refresher: nesting depth.**
>
> Track a counter `depth`. Increment on `(`, decrement on `)`. The depth tells you "how many openers are currently unclosed."
>
> For `"(()(()))"`:
> ```
> '('  → depth 1
> '('  → depth 2
> ')'  → depth 1
> '('  → depth 2
> '('  → depth 3
> ')'  → depth 2
> ')'  → depth 1
> ')'  → depth 0   ← end of primitive
> ```

For a primitive (a single connected balanced piece), depth starts at 0, goes positive, and returns to 0 exactly once at the end. So depth = 0 between two consecutive characters marks a primitive boundary.

For each primitive, we want to STRIP THE OUTERMOST `(` and `)`. Those are:

- The `(` that takes depth from 0 to 1.
- The `)` that takes depth from 1 to 0.

Every OTHER character we KEEP.

---

## 3. The natural stack approach

We could use an explicit stack tracking opener positions. When a `)` brings the stack down to size 1 (i.e., we're about to close the outermost), it's the primitive's closing `)` — skip it. When we push a `(` onto an EMPTY stack, it's the primitive's opening `(` — skip it.

```
stack = []
result = []
for c in s:
    if c == '(':
        if len(stack) > 0:        # not the outermost opener
            result.append('(')
        stack.append('(')
    else:                          # c == ')'
        stack.pop()
        if len(stack) > 0:         # not the outermost closer
            result.append(')')
return ''.join(result)
```

This works. But notice — we're only ever using `len(stack)`, never the contents of the stack. **We never look at what's IN the stack** — we just care about its size. That's a clue.

---

## 4. Why we don't need the stack's CONTENTS — only its depth

Since we only use `len(stack)`, we can replace the stack with a simple integer `depth`.

```
depth = 0
result = []
for c in s:
    if c == '(':
        if depth > 0:              # not the outermost opener
            result.append('(')
        depth += 1
    else:                           # c == ')'
        depth -= 1
        if depth > 0:               # not the outermost closer
            result.append(')')
return ''.join(result)
```

This works the same — and uses O(1) extra space (just the integer) instead of a stack that could grow to O(n).

**Key insight:** the structural rule "keep this character if it's NOT the outermost" only needs the current nesting depth. The stack's "what is the top" information is irrelevant.

The check direction matters:

- For `(`: increment depth AFTER the decision. The "depth before push" is 0 for the outermost opener; >0 for inner.
- For `)`: decrement depth BEFORE the decision. The "depth after pop" is 0 for the outermost closer; >0 for inner.

This asymmetry correctly identifies the outermost boundaries.

---

## 5. Code

**C++:**

```cpp
string removeOuterParentheses(string s) {
    string result;
    int depth = 0;

    for (char c : s) {
        if (c == '(') {
            if (depth > 0) result += c;    // keep if inner opener
            depth++;
        } else {                            // c == ')'
            depth--;
            if (depth > 0) result += c;    // keep if inner closer
        }
    }

    return result;
}
```

Nine lines.

**Python:**

```python
def removeOuterParentheses(s):
    result = []
    depth = 0
    for c in s:
        if c == '(':
            if depth > 0:
                result.append(c)
            depth += 1
        else:
            depth -= 1
            if depth > 0:
                result.append(c)
    return ''.join(result)
```

**JavaScript:**

```javascript
function removeOuterParentheses(s) {
    let result = '';
    let depth = 0;
    for (const c of s) {
        if (c === '(') {
            if (depth > 0) result += c;
            depth++;
        } else {
            depth--;
            if (depth > 0) result += c;
        }
    }
    return result;
}
```

All O(n) time, O(1) extra space (besides the output string).

---

## 6. Trace it

`s = "(()())(())"`. Walk through:

```
result = "". depth = 0.

'(':  depth 0, NOT inner — skip. depth = 1.
'(':  depth 1, IS inner — keep '('. result = "(". depth = 2.
')':  depth = 1 (decrement first). 1 > 0, IS inner — keep ')'. result = "()".
'(':  depth 1, IS inner — keep. result = "()(". depth = 2.
')':  depth = 1. Keep. result = "()()" 
')':  depth = 0. NOT inner — skip.   ← end of primitive 1
'(':  depth 0, NOT inner — skip. depth = 1.   ← start of primitive 2
'(':  depth 1, IS inner — keep. result = "()()(". depth = 2.
')':  depth = 1. Keep. result = "()()()" .
')':  depth = 0. Skip.

Return "()()()".  ✓
```

Watch depth: goes `0 → 1 → 2 → 1 → 2 → 1 → 0` (primitive 1) and then `0 → 1 → 2 → 1 → 0` (primitive 2). The `(` and `)` skipped are exactly those at the depth-0 boundaries.

Another trace, `s = "(()(()))"` (one big primitive):

```
'(':  depth 0, skip. depth = 1.
'(':  depth 1, keep. result = "(". depth = 2.
')':  depth = 1, keep. result = "()".
'(':  depth 1, keep. result = "()(". depth = 2.
'(':  depth 2, keep. result = "()((". depth = 3.
')':  depth = 2, keep. result = "()(()" — wait let me recount.

Actually:
'(':  depth 0, skip. depth = 1.
'(':  depth 1 > 0, keep '('. result = "(". depth = 2.
')':  depth = 1 (decrement). 1 > 0, keep ')'. result = "()". 
'(':  depth 1 > 0, keep '('. result = "()(". depth = 2.
'(':  depth 2 > 0, keep '('. result = "()((". depth = 3.
')':  depth = 2. 2 > 0, keep ')'. result = "()(()" — no wait.
```

Hmm let me redo carefully:

```
result = "". depth = 0.

s[0] = '(': depth=0, skip. depth=1.       result="", depth=1.
s[1] = '(': depth=1>0, keep '('. depth=2. result="(", depth=2.
s[2] = ')': depth-- → 1. 1>0, keep ')'.   result="()", depth=1.
s[3] = '(': depth=1>0, keep '('. depth=2. result="()(", depth=2.
s[4] = '(': depth=2>0, keep '('. depth=3. result="()((", depth=3.
s[5] = ')': depth-- → 2. 2>0, keep ')'.   result="()(()", depth=2.

Hmm wait — appending ')' gives "()((" + ")" = "()(()". Let me recount carefully:
"()(" is 3 chars: '(', ')', '('. Then append '(' → "()((". Then append ')' → "()(( )". 
No, "()((" plus ')' is "()(( )" — wait, just append the char: "()((" + ")" = "()((" + ')' = "()(()" — 5 chars.
Hmm, "()((" is 4 chars: ( ) ( ( . Append ')': ( ) ( ( ) — 5 chars. That spells "()(()" — yes.

s[6] = ')': depth-- → 1. 1>0, keep ')'.   result="()(())", depth=1.
s[7] = ')': depth-- → 0. 0>0 false, skip.  result="()(())", depth=0.

Return "()(())". 
```

Sanity check: input `"(()(()))"` is one primitive. Strip outermost `(` and `)` → `"()(())"`. ✓ Matches.

---

## 7. Common pitfalls

1. **Wrong order of "check vs update depth."** For `(`: check first, then increment. For `)`: decrement first, then check. Mixing this up incorrectly identifies outermost boundaries.

2. **Using a stack when a counter suffices.** Not WRONG, just wasteful. If you only need `len(stack)`, use an integer instead. Saves O(n) space.

3. **Trying to find primitive boundaries first, then strip each.** Two-pass solution that's harder to read than the one-pass counter. The counter approach handles boundaries implicitly.

4. **Confusing "primitive" with "matched pair."** A primitive can be LARGE (e.g., `"(()())(())"` has primitives `(()())` and `(())`, NOT 7 individual pairs). The notion of "primitive" is the LARGEST piece that can stand alone as a valid string.

5. **Forgetting `s` is guaranteed valid.** The problem promises valid input, so depth never goes negative and ends at 0. Don't add defensive checks — they're noise.

6. **Building the result with string concatenation (in C++).** Repeated `result += c` is fine in C++ (`string::operator+=` is amortized O(1)). In Python, joining a list at the end is faster than incremental `+=` (which copies). JS is similar — `Array.push` then `Array.join('')`.

---

## 8. The shape — counter instead of stack

The lesson generalizes:

> **When you only need the SIZE of a stack (not what's in it), replace the stack with an integer counter. Saves space, often clearer.**

Where this trick appears:

| Problem | What gets counted |
|---|---|
| **This problem** | depth of `(` nesting |
| Maximum Depth of Parentheses | same — track max counter |
| Score of Parentheses (LC #856) | also needs SIZE plus a coefficient — counter sometimes |
| Generate Valid Parentheses (recursion) | `open` and `close` counts |
| Balanced Brackets (single type) | imbalance counter; if it ever goes negative, fail |
| Tracking "active" connections in a stream | counter of open vs close events |

**Pattern to internalize:**

> "Before reaching for a stack, ask: 'Do I need to remember WHAT was pushed, or just HOW MANY are there?' If only the count matters, use a counter — O(1) space."

This isn't always applicable (Valid Parentheses NEEDS to remember WHICH opener was pushed because there are multiple types). But when applicable, it's cleaner.

---

> **Self-check — the question to ask next time.**
>
> When you find yourself using a stack to track nesting or "currently open" items of a SINGLE type, before reaching for a stack container, ask:
>
> > **"Do I need to remember WHAT was pushed, or only HOW MANY items are stacked? If only count matters, an integer suffices."**
>
> If yes, you've reduced O(n) space to O(1).

---

## Cross-references

- **Reference card (post-mastery):** [`../Remove_Outermost_Parentheses.md`](../Remove_Outermost_Parentheses.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`Valid_Parentheses.md`](./Valid_Parentheses.md) — full stack with multiple bracket types (where you NEED the contents, not just count).
  - Coming next: Remove_All_Adjacent_Duplicates_in_String — stack-as-cancellation pattern.
