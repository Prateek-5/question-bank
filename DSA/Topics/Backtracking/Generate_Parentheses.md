# Generate Parentheses

**Problem Link:**
https://leetcode.com/problems/generate-parentheses/

**Topic:**
Backtracking

----------------------------------------

## Step 1: Understand the Goal

Given an integer `n`, generate **all valid** strings made of exactly `n` pairs of parentheses (so length `2n`). "Valid" means every `(` is properly matched with a `)`.

Example for `n = 3`:
- `"((()))"`
- `"(()())"`
- `"(())()"`
- `"()(())"`
- `"()()()"`

That's 5 valid strings. (Not coincidentally, 5 is the 3rd Catalan number.)

----------------------------------------

## Step 2: First Thoughts — Generate All Strings?

Most naïve approach: generate all 2^(2n) binary strings over `{'(', ')'}`, keep the valid ones. For n = 3, that's 64 strings to check — manageable. For n = 10, it's a million — tolerable. For n = 100, forget it.

Also, we'd spend a lot of work generating obviously broken strings like `"))))((((" ` just to throw them out. We should be smarter.

Can we *construct* only valid strings, never touching the invalid ones? Let's think about the constraints that make a string valid.

----------------------------------------

## Step 3: What Makes a Partial String Potentially Extendable?

Suppose I'm building a string character by character from left to right. At any point, I've placed some opens `o` and some closes `c`. A partial string is **on track** to be valid if:

1. **`o ≤ n`** — I haven't placed more opens than allowed.
2. **`c ≤ o`** — I haven't closed more than I've opened (otherwise a `)` would have no matching `(`).

At the end, we need `o = c = n`.

So at each position, the question is: given current `(o, c)`, what characters can I safely append?

- Append `(` is allowed if `o < n`.
- Append `)` is allowed if `c < o` (there's an unmatched open to close).

If neither is allowed, we can't extend — but that should only happen when `o = n` and `c = n`, i.e., the string is done.

----------------------------------------

## Step 4: The Recursive Construction

Think of it as a tree of choices: at each position we branch on the valid characters.

```
build(partial, o, c):
    if len(partial) == 2n:
        result.append(partial)
        return
    if o < n:  build(partial + '(', o + 1, c)
    if c < o:  build(partial + ')', o, c + 1)
```

This is **backtracking**. We try each valid choice, recurse, and when we come back we try the next choice. The beauty is that we never build an invalid partial string — we only explore the space of potentially valid ones.

----------------------------------------

## Step 5: Trace for n = 2

Let's hand-trace.

```
build("", 0, 0):
  o=0 < 2: try '('
  build("(", 1, 0):
    o=1 < 2: try '('
    build("((", 2, 0):
      o == n, no '('
      c=0 < o=2: try ')'
      build("(()", 2, 1):
        o == n, no '('
        c=1 < 2: try ')'
        build("(())", 2, 2):
          len = 4 == 2n. RECORD "(())".
    c=0 < o=1: try ')'
    build("()", 1, 1):
      o=1 < 2: try '('
      build("()(", 2, 1):
        c=1 < 2: try ')'
        build("()()", 2, 2):
          RECORD "()()".
      c=1 < o=1? No. Skip.
```

Results: `"(())"`, `"()()"`. Both valid. Total: 2, matching the 2nd Catalan number.

----------------------------------------

## Step 6: Why the Constraints Are Both Necessary and Sufficient

**Necessary:** if `o > n`, the final count of opens will exceed n, which is wrong. If `c > o` at any intermediate point, there's an unmatched close, which can't be fixed by appending more.

**Sufficient:** if we always maintain `o ≤ n` and `c ≤ o`, can we always finish with a valid string? Yes. Reason: we can always close remaining opens before running out of space. Specifically, if the string currently has `o` opens and `c` closes with `o ≤ n` and `c ≤ o`, we can append `(n - o)` more opens followed by `(n - c)` more closes in some order to reach `2n` length with `n` of each.

So the two invariants exactly characterize "this partial string can potentially be extended to a valid one."

----------------------------------------

## Step 7: Name It

This is a classic **backtracking** problem — we build solutions incrementally, pruning branches that violate constraints. The general template is:

```
backtrack(state):
    if state is complete: record it
    else for each valid extension:
        apply extension
        backtrack(extended state)
        undo extension
```

Our version uses pass-by-value strings (since C++ string concatenation creates copies), so we don't literally "undo" — the recursion returns and the caller's state is unaffected. If we wanted efficiency, we'd use a mutable buffer and explicitly pop the last char after recursing.

The "validity invariants per partial state" idea generalizes to many problems: valid Sudoku, N-Queens, word ladders, etc.

----------------------------------------

## Step 8: Complexity

Time: the number of valid strings is the n-th **Catalan number**, roughly `4^n / (n * √n)`. We do O(n) work per string (copy and store). Total: `O(4^n / √n)`.

Space: recursion depth `2n`, plus the output list. **O(n)** stack, `O(Catalan(n) · n)` output.

The algorithm is output-sensitive — we spend time proportional to how much we produce, which is near-optimal.

----------------------------------------

## Step 9: C++ Implementation

```cpp
void build(string& cur, int o, int c, int n, vector<string>& res) {
    if ((int)cur.size() == 2 * n) {
        res.push_back(cur);
        return;
    }
    if (o < n) {
        cur.push_back('(');
        build(cur, o + 1, c, n, res);
        cur.pop_back();         // undo
    }
    if (c < o) {
        cur.push_back(')');
        build(cur, o, c + 1, n, res);
        cur.pop_back();         // undo
    }
}

vector<string> generateParenthesis(int n) {
    vector<string> res;
    string cur;
    cur.reserve(2 * n);
    build(cur, 0, 0, n, res);
    return res;
}
```

The `cur.push_back` / `cur.pop_back` pair is the explicit "apply then undo" — faster than passing strings by value.

----------------------------------------

## Step 10: Follow-up Questions

- **Count the number of valid parenthesizations without generating them.** Catalan number formula or DP: `C_n = sum of C_i * C_{n-1-i} for i in 0..n-1`.
- **Generate valid strings of multiple bracket types (e.g., `( { [ ] } )`).** Extend the constraints: we can close a bracket only if its corresponding open is the most recent unclosed one (stack-based).
- **Generate all valid balanced strings of length 2n allowing empty brackets pattern modifications.** Depends on specifics.
- **Generate with constraints (e.g., no two consecutive `(`).** Add conditions in the recursive branches.
- **Check if a given string is valid — don't generate.** Simple stack-based check in O(n).
- **Variable-length generation up to n.** Collect from builds of every length 0..n.
