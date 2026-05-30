# Generate Parentheses — Teaching Walkthrough

> **Reference card (post-mastery):** [`../Generate_Parentheses.md`](../Generate_Parentheses.md). Use that once you've solved this. This file is for the first time.
>
> **Problem link:** <a href="https://leetcode.com/problems/generate-parentheses/" target="_blank" rel="noopener noreferrer">https://leetcode.com/problems/generate-parentheses/</a>

---

## How to use this file

Paced for someone seeing this problem for the first time. Reading time: ~16 minutes. **The lesson: track TWO COUNTERS (open and close) as state and PRUNE invalid extensions in advance.** Backtracking shines when the constraints can be checked CHEAPLY during construction — we only ever build valid prefixes, never invalid ones. **Read [`Subsets.md`](../../Recursion/learn/Subsets.md) first** for the backtracking template.

**Map of this file (8 short sections):**

1. Read the problem
2. The brute force
3. The validity invariants
4. The counter-based pruning
5. Code
6. Trace it
7. Common pitfalls
8. The shape — invariant-preserving backtracking

---

## 1. Read the problem

Given an integer `n`, return all **WELL-FORMED** strings of `n` pairs of parentheses (length `2n`).

**Examples:**

- `n = 3` → 5 strings:
  ```
  ((()))
  (()())
  (())()
  ()(())
  ()()()
  ```
- `n = 1` → `["()"]`.
- `n = 0` → `[""]`.

Why 5 for n=3? These are the **Catalan numbers**: 1, 1, 2, 5, 14, 42, ...

---

## 2. The brute force

Generate ALL 2^(2n) binary strings of length 2n using `(` and `)`. Filter the valid ones.

For n=3: 64 candidates. n=10: ~1 million. n=15: ~1 billion (TLE).

Worse: we waste time generating obviously-invalid strings like `))))((((` and then throwing them out.

**Smarter:** construct ONLY valid strings, never generating invalid ones.

---

## 3. The validity invariants

> **Mini-refresher: what makes a partial string still extensible to valid?**
>
> Build the string left to right. Track:
> - `open`: count of `(` placed so far.
> - `close`: count of `)` placed so far.
>
> A partial string is "still extensible" iff:
> 1. **`open <= n`** — we haven't exceeded the allowed opens.
> 2. **`close <= open`** — we haven't closed more than we've opened.
>
> Together: the partial string is a PREFIX of some valid n-pair string.

At each step, we can:
- Place `(` IF `open < n` (we have room for more opens).
- Place `)` IF `close < open` (there's an unmatched opener to close).

If neither, we're stuck — but that should only happen at the END (when `open == close == n`).

---

## 4. The counter-based pruning

Translate the invariants into a recursive function:

```
def backtrack(cur, open, close):
    if len(cur) == 2 * n:
        record cur
        return
    if open < n:
        backtrack(cur + '(', open + 1, close)
    if close < open:
        backtrack(cur + ')', open, close + 1)
```

**Each branch corresponds to a valid choice.** We never build an invalid partial string. This is the essence of constraint-aware backtracking.

For efficient state management, use a MUTABLE buffer:

```
def backtrack(cur, open, close):
    if len(cur) == 2 * n:
        record cur.copy()
        return
    if open < n:
        cur.append('(')
        backtrack(cur, open + 1, close)
        cur.pop()
    if close < open:
        cur.append(')')
        backtrack(cur, open, close + 1)
        cur.pop()
```

Standard apply-recurse-undo.

---

## 5. Code

**C++:**

```cpp
void build(string& cur, int open, int close, int n, vector<string>& res) {
    if ((int)cur.size() == 2 * n) {
        res.push_back(cur);
        return;
    }
    if (open < n) {
        cur.push_back('(');
        build(cur, open + 1, close, n, res);
        cur.pop_back();
    }
    if (close < open) {
        cur.push_back(')');
        build(cur, open, close + 1, n, res);
        cur.pop_back();
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

**Python:**

```python
def generateParenthesis(n):
    res = []
    def backtrack(cur, opn, cls):
        if len(cur) == 2 * n:
            res.append(''.join(cur))
            return
        if opn < n:
            cur.append('(')
            backtrack(cur, opn + 1, cls)
            cur.pop()
        if cls < opn:
            cur.append(')')
            backtrack(cur, opn, cls + 1)
            cur.pop()
    backtrack([], 0, 0)
    return res
```

Complexity: **O(4^n / √n)** (Catalan growth), **O(n) recursion depth**.

---

## 6. Trace it

**n = 2:**

```
backtrack("", 0, 0):
  open=0 < 2: try '(':
    backtrack("(", 1, 0):
      open=1 < 2: try '(':
        backtrack("((", 2, 0):
          open == n, no '('.
          close=0 < open=2: try ')':
            backtrack("(()", 2, 1):
              close=1 < 2: try ')':
                backtrack("(())", 2, 2):
                  len == 2n. RECORD "(())".
      close=0 < open=1: try ')':
        backtrack("()", 1, 1):
          open=1 < 2: try '(':
            backtrack("()(", 2, 1):
              close=1 < 2: try ')':
                backtrack("()()", 2, 2):
                  RECORD "()()".
          close=1 < open=1? No. Skip.

Records: ["(())", "()()"].  ✓
```

The recursion only explored 2 paths to leaves — exactly the Catalan number for n=2. No wasted work.

---

## 7. Common pitfalls

1. **No pruning → exponential blowup.** Without `open <= n` and `close <= open` checks, you'd generate ALL 4^n strings.

2. **Returning the live `cur`.** Mutating buffers requires SNAPSHOT copies when recording. `res.append(cur)` (Python) appends a REFERENCE — all entries would share the (eventually empty) buffer.

3. **Forgetting `cur.pop()` (undo).** State accumulates; results are garbage.

4. **Order of branches matters?** It changes the OUTPUT ORDER but not correctness. Either order works.

5. **Base case at `open + close == 2*n` vs `len(cur) == 2*n`.** Equivalent (counter sum equals length).

6. **Trying to enumerate all 2^(2n) and filter.** TLE for large n.

---

## 8. The shape — invariant-preserving backtracking

The pattern:

> **"Identify the STATE that captures partial-solution validity (a few counters or flags). At each step, BRANCH only into states that PRESERVE validity. No invalid branches generated."**

| Problem | State / invariants |
|---|---|
| **This problem** | (open count, close count); never close > open, never open > n |
| Letter Combinations of a Phone Number | digit index; always valid |
| Restore IP Addresses | (current segment, position); segment must be 0-255, no leading zeros |
| N-Queens | column/diagonal occupancy; no two queens attack |
| Sudoku Solver | row/col/box masks; no two same digit in same constraint group |
| Word Search | visited cells; only walk to unvisited adjacent matching cells |

**Pattern to internalize:**

> "Backtracking efficiency hinges on PRUNING via cheaply-checkable invariants. The invariants live in the recursion's STATE (counters, sets, masks). Apply choice → recurse → undo."

---

> **Self-check — the question to ask next time.**
>
> When you face "enumerate all valid configurations," ask:
>
> > **"What STATE captures partial-solution validity? Can I PRUNE invalid extensions before constructing them?"**
>
> If yes, you've got efficient backtracking — only valid branches explored.

---

## Cross-references

- **Reference card (post-mastery):** [`../Generate_Parentheses.md`](../Generate_Parentheses.md)
- **Topic navigator:** [`../LEARNING.md`](../LEARNING.md)
- **Related v2 walkthroughs:**
  - [`../../Recursion/learn/Subsets.md`](../../Recursion/learn/Subsets.md) — backtracking basics.
  - Coming next: [`Palindrome_Partitioning.md`](./Palindrome_Partitioning.md), [`Gray_Code.md`](./Gray_Code.md), [`Sudoku_Solver.md`](./Sudoku_Solver.md).
