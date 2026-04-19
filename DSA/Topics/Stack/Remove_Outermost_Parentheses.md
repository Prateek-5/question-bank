# Remove Outermost Parentheses

**Problem Link:**
https://leetcode.com/problems/remove-outermost-parentheses/

**Topic:**
Stack

----------------------------------------

## Step 1: Define "Primitive Decomposition"

A valid parentheses string can be split into "primitive" pieces — maximal balanced substrings that don't properly contain another such substring. Each primitive has a single outermost pair of parentheses wrapping everything inside.

Remove those outermost pairs and concatenate what's inside.

Example: `s = "(()())(())"`.

Decompose into primitives:
- `(()())`  : balanced, outermost at the first '(' and the 6th ')'.
- `(())`    : balanced.

Remove outermost from each:
- `(()())` → `()()`.
- `(())` → `()`.

Result: `"()()()"`.

Example: `s = "(()())(())(()(()))"`.

Primitives: `(()())`, `(())`, `(()(()))`.

Remove outermost from each:
- `(()())` → `()()`.
- `(())` → `()`.
- `(()(()))` → `()(())`.

Result: `()()()(())`. Concatenate: `"()()()" + "()(())"` = `"()()()()(())"`. Length 12.

----------------------------------------

## Step 2: How to Identify Primitive Boundaries?

A primitive starts at an `'('` when we have **zero unmatched opens** (we're at depth 0 before entering). A primitive ends at `')'` that returns us to **depth 0**.

So track depth as we scan. When depth reaches 0 at a ')', that's the end of a primitive. Everything from the primitive's start to this end is one primitive piece.

But we want to **remove the outermost pair** of each primitive, not emit the whole primitive. So:
- At the very start of a primitive (depth 0, reading '(' which will become depth 1): skip this '('.
- At the end of a primitive (depth back to 0 via ')'): skip this ')'.
- For every other char: keep it.

----------------------------------------

## Step 3: Simplified Rule

Track depth. Process char c:
- If c == '(':
  - depth > 0: keep c.
  - depth == 0: skip c (it's an outermost open).
  - depth += 1.
- If c == ')':
  - depth -= 1.
  - depth > 0: keep c.
  - depth == 0: skip c (it's an outermost close).

Or, equivalently:
- If c == '(' and depth > 0: keep.
- If c == ')' and depth > 1: keep.
- (Others skipped.)

With the depth-update properly sequenced.

----------------------------------------

## Step 4: Cleaner Form

Let me restructure for clarity:

```
result = []
depth = 0
for c in s:
    if c == '(':
        if depth > 0: result.append('(')
        depth++
    else:   # c == ')'
        depth--
        if depth > 0: result.append(')')
return ''.join(result)
```

Depth increments on '(' (after the conditional keep), decrements on ')' (before the conditional keep). We keep `(` only when depth was already > 0, and `)` only when depth is still > 0 after decrement.

These conditions are precisely "not at the outermost layer."

----------------------------------------

## Step 5: Trace on `"(()())(())"`

```
depth=0. result=[].

'(': depth=0, don't keep. depth=1.
'(': depth=1>0, keep. result=['(']. depth=2.
')': depth=1. 1>0, keep. result=['(', ')']. depth=1... wait I went wrong.
```

Let me redo. Depth starts 0.

```
'(': before increment, depth=0. 0 > 0? No, skip. depth becomes 1.
'(': before increment, depth=1. 1 > 0? Yes, keep '('. depth becomes 2.
')': depth becomes 1. 1 > 0? Yes, keep ')'.
'(': before increment, depth=1. 1 > 0? Yes, keep '('. depth becomes 2.
')': depth becomes 1. 1 > 0? Yes, keep ')'.
')': depth becomes 0. 0 > 0? No, skip.
'(': before increment, depth=0. Skip. depth becomes 1.
'(': before increment, depth=1. Keep '('. depth becomes 2.
')': depth becomes 1. Keep ')'.
')': depth becomes 0. Skip.
```

Result: `(` `)` `(` `)` `(` `)` = `"()()()"`. 

Wait, expected was `()()()` but my decomposition at Step 1 had primitives `(()())` → `()()` and `(())` → `()`. Concatenating: `()()` + `()` = `()()()`. ✓

So output is `"()()()"`. Matches.

----------------------------------------

## Step 6: Do We Need an Explicit Stack?

We're tracking depth (a single integer) — technically a **counter**, not a stack. But conceptually, depth tracks the number of unmatched opens on the stack. Since we only care about the depth count, we don't need to store the actual stack contents.

In this problem, "the stack" degenerates to a counter. That's fine — it's still the stack pattern applied.

More generally, when the only stack info you need is "how many items are on the stack?", a counter suffices.

----------------------------------------

## Step 7: Name It

**Depth tracking for parenthesis nesting** — a specialized stack pattern. Related:
- Valid Parentheses (explicit stack for matching).
- Max Nesting Depth.
- Minimum Add to Make Parentheses Valid.
- Score of Parentheses.

The trick "counter, not stack" works when only nesting depth matters.

----------------------------------------

## Step 8: Complexity

Time: **O(n)** — single pass.
Space: **O(n)** for the result string. O(1) auxiliary beyond that.

----------------------------------------

## Step 9: C++ Implementation

```cpp
string removeOuterParentheses(string s) {
    string result;
    int depth = 0;
    for (char c : s) {
        if (c == '(') {
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

Eight lines. The key is getting the "depth check vs depth update" sequence right:
- For '(': check first, then increment.
- For ')': decrement first, then check.

That asymmetry correctly treats the outermost boundaries.

----------------------------------------

## Step 10: Follow-up Questions

- **Count the primitives (don't construct result).** Count the number of times depth reaches 0 at a ')'.
- **Total length of primitives (useless since it equals len(s) / 2 pairs, but conceptually interesting).** Same counter approach.
- **Extract each primitive separately into a list.** Track the start of each primitive (when depth goes 0 → 1).
- **Malformed input.** Add validity checks (depth never negative, ends at 0).
- **Alternative: actually use a stack (not just counter).** Push '(' positions; on matching ')', check stack size to decide outermost-ness.
- **Multiple bracket types.** More complex nesting; requires per-type tracking.
