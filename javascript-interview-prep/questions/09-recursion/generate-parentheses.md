# Generate all valid parentheses combinations (n pairs)

## Source
- Canonical recursion / backtracking interview problem.
- LeetCode #22 "Generate Parentheses": https://leetcode.com/problems/generate-parentheses/
- Reference (Catalan numbers): https://en.wikipedia.org/wiki/Catalan_number

## Why this question matters in interviews
Generate-parentheses is the **cleanest "backtracking with a constraint" problem on the interview circuit.** It's a 15-minute warm-up at FAANG-tier interviews because it tests three signals in a compact problem: (1) recognizing the constraint (`close` can never exceed `open`), (2) building output incrementally with two counters, and (3) knowing the output count is **the n-th Catalan number** `C(n) = (2n)! / ((n+1)! n!)`. Senior interviewers love it because the wrong solution — "generate all `2^(2n)` strings of length 2n and filter validly balanced ones" — wastes massive work; the right one prunes to exactly `C(n)` results from the get-go. Also, the same constraint-driven recursion shape powers parser-generator output, AST-shape enumeration, JSON-template generation, and SQL-clause permutation for property-based testing.

## Concepts involved

### Syntax to lock in

The textbook solution uses two counters: `open` (how many `(` we've placed) and `close` (how many `)` we've placed). The invariants:

- We may place `(` if `open < n`.
- We may place `)` if `close < open` (otherwise the string would have a `)` with no matching `(`).
- We're done when `open === n && close === n` — the string is length `2n` and balanced.

```js
function generateParenthesis(n) {
  const result = [];
  function backtrack(current, open, close) {
    if (current.length === 2 * n) {
      result.push(current);
      return;
    }
    if (open < n)        backtrack(current + '(', open + 1, close);
    if (close < open)    backtrack(current + ')', open, close + 1);
  }
  backtrack('', 0, 0);
  return result;
}
```

### Runtime / engine behavior
- **Output size is the n-th Catalan number** `C(n) = C(2n, n) / (n+1)`. Values: `C(0)=1, C(1)=1, C(2)=2, C(3)=5, C(4)=14, C(5)=42, C(10)=16796, C(15)=9.7M`.
- **Asymptotic count:** `C(n) ≈ 4^n / (n^(3/2) √π)` — grows roughly like `4^n / n^(3/2)`. Sub-exponential vs `2^(2n) = 4^n` of unconstrained strings; the pruning saves `Θ(n^(3/2))` factor.
- **Time complexity:** `O(4^n / √n)` — the standard bound, dominated by output size times the cost of producing each string.
- **Space:** `O(n)` recursion depth (the string is length `2n`), plus the output array.
- **String concatenation `current + '('`** — in V8 short strings are interned and concatenation builds **cons-strings** in O(1) until flattening. For n ≤ 15 this is negligible; for very large n consider an explicit `char[]` array with `push`/`pop`.
- **Why two counters work** — the constraint "every prefix has `open ≥ close`" is *exactly* the Dyck-path condition that defines balanced parentheses. The counters maintain it as an invariant rather than checking after generation.

### Edge cases
1. **n = 0** — exactly one valid string, the empty string. Output: `['']`. Many candidates return `[]`. Wrong.
2. **n = 1** — `['()']`.
3. **Large n** — `n = 15` produces ~10M strings of length 30; `n = 20` produces ~6.5 billion. Cap any real test at `n ≤ 12`.
4. **Why no `if (close < n)` check?** — `close < open` is strictly stronger because `open ≤ n`. Adding it is harmless but redundant. Interviewers may quiz you on this.
5. **Pruning vs filtering** — never generate all `2^(2n)` strings and validate. That's `~4^n` work to keep `~4^n / n^(3/2)` — wastes a `n^(3/2)` factor.
6. **Mutating the builder** — if you use an array builder for performance, **don't forget to pop** after each recursive call. Same backtracking discipline as permutations.

## Brute force approach
Generate all `2^(2n)` binary strings (treating `(` as 0, `)` as 1), then validate each by stack-counting parens. For `n=10` that's 1M candidates to filter into ~16k results — 60x wasted work; for `n=15` it's ~10⁹ candidates. Mention only to dismiss.

## Optimal approach
Backtracking with the two-counter invariant. Each recursive call extends `current` with either `(` (if `open < n`) or `)` (if `close < open`). Every leaf is by construction a valid balanced string of length `2n`. No filtering needed; we generate exactly `C(n)` results and do `O(n)` work per result (string concat). Total `O(4^n / √n)` — optimal up to constants because that's the output size.

## Solution (JavaScript)

```js
/**
 * All well-formed parenthesis strings using exactly n '(' and n ')'.
 * Output size: C(n) — the n-th Catalan number.
 * Time:  O(4^n / √n).
 * Space: O(n) call stack + O(C(n) · n) output.
 *
 * @param {number} n
 * @returns {string[]}
 */
function generateParenthesis(n) {
  if (n === 0) return [''];
  const result = [];
  function backtrack(current, open, close) {
    if (current.length === 2 * n) {
      result.push(current);
      return;
    }
    if (open  < n)     backtrack(current + '(', open + 1, close);
    if (close < open)  backtrack(current + ')', open, close + 1);
  }
  backtrack('', 0, 0);
  return result;
}

/**
 * Higher-performance variant using an array builder.
 * Avoids creating O(n) intermediate strings; one per result instead.
 */
function generateParenthesisFast(n) {
  if (n === 0) return [''];
  const result = [];
  const buf = new Array(2 * n);
  function backtrack(i, open, close) {
    if (i === 2 * n) {
      result.push(buf.join(''));
      return;
    }
    if (open < n) {
      buf[i] = '(';
      backtrack(i + 1, open + 1, close);
    }
    if (close < open) {
      buf[i] = ')';
      backtrack(i + 1, open, close + 1);
    }
  }
  backtrack(0, 0, 0);
  return result;
}

/**
 * Lazy generator — yields one valid string at a time.
 * Useful for n where the full list would OOM.
 */
function* generateParenthesisLazy(n) {
  const buf = new Array(2 * n);
  function* go(i, open, close) {
    if (i === 2 * n) { yield buf.join(''); return; }
    if (open < n)    { buf[i] = '('; yield* go(i + 1, open + 1, close); }
    if (close < open){ buf[i] = ')'; yield* go(i + 1, open, close + 1); }
  }
  yield* go(0, 0, 0);
}
```

## Step-by-step dry run

Input: `generateParenthesis(3)`. Expected: `C(3) = 5` results.

Recursion tree (state: `current`, `open`, `close`):
```
                ('', 0, 0)
                    | open<3
                ('(' , 1, 0)
              /             \
        open<3              close<open
       ('((' , 2, 0)         ('()', 1, 1)
       /          \                | open<3
    open<3      close<open      ('()(' , 2, 1)
  ('(((' ,3,0)  ('(()',2,1)    /         \
    | close       /     \    open<3     close<open
  ('((()' ,3,1)  '(()('  '(())'  ...   ('()()' , 2, 2)
    | close      ↓
  ('(())' --     ↓
   wait, let's redo precisely:
```

Let me trace more carefully for clarity. I'll list each leaf with its full string.

DFS exploration (depth-first, `(` branch tried before `)`):
1. `'((('` (3,0) → can't `(`; can `)` → `'((()' ` (3,1) → `'((())'` (3,2) → `'((()))'` (3,3) ✓
2. Backtrack to (3,1): no more options. To (2,1) `'(()'` → try `)`: `'(())'` (2,2) → try `(`: nope (open=2, close=2, but open<n=3 still — wait, here open=2 and close=2, length=4, need length=6). Actually `'(())'` is at length 4; continue: open<3 → `'(())('` (3,2) → close<open → `'(())()'` (3,3) ✓
3. From (2,1) `'(()'`, also try `(` branch first... order matters. Re-doing in the order code actually walks it:

Going strictly by `(` first then `)`:
- `'((('` → `'((()'` → `'((())'` → `'((()))'` ✓ (1)
- Unwind to `'(('`, try `)`: `'(()'`
  - try `(`: `'(()('` → try `(`? no (open=3). try `)`: `'(()()'` → only `)` left: `'(()())'` ✓ (2)
  - try `)`: `'(())'` → try `(`: `'(())('` → only `)`: `'(())()'` ✓ (3)
- Unwind to `'('`, try `)`: `'()'`
  - try `(`: `'()('`
    - try `(`: `'()(('` → only `)` twice: `'()(()'` → `'()(())'` ✓ (4)
    - try `)`: `'()()'` → try `(`: `'()()('` → `'()()()'` ✓ (5)

Total: `['((()))', '(()())', '(())()', '()(())', '()()()'] ` — 5 results, which is `C(3) = 5`. Matches.

The pruning saved us: there are `2^6 = 64` total length-6 strings of `(` and `)`, and only 5 are balanced. The recursion never even materializes the other 59 candidates.

## Important takeaways

**Syntax to memorize**
- Two counters: `open` and `close`. Two conditions: `open < n` and `close < open`.
- Base case: `current.length === 2 * n`. Never `open + close === 2 * n` (same thing, but the length check is more readable).
- Try `(` branch first → output is in lexicographic order (well, with `(` < `)` in ASCII it is, since 40 < 41).

**Patterns to reuse**
- **Constraint-driven backtracking** — maintaining an invariant *during* recursion to avoid post-hoc filtering. Same pattern as: N-queens (`canPlace`), sudoku (`isValid`), word-break (`wordSet.has(prefix)`), letter-combinations-of-phone-number.
- **Catalan-counted outputs.** Same count appears in:
  - Number of distinct binary trees with n nodes
  - Number of full binary trees with 2n+1 nodes
  - Number of Dyck paths
  - Number of triangulations of an (n+2)-gon
  Recognizing C(n) helps you sanity-check output sizes.

**Common mistakes**
- Generating all `2^(2n)` strings and filtering — quadratic-factor wasted work.
- Returning `[]` for n=0 instead of `['']`.
- Using `close < n` instead of `close < open` — the latter is strictly tighter and is what prunes correctly.
- Forgetting to `pop` when using an array builder — every result becomes the last one.
- Trying to memoize — there's nothing to memoize. Every recursion path produces a unique string; the `current` parameter is the state, and it's never repeated.

**Related questions**
- LC #20 "Valid Parentheses" — the *validator* (stack-based, O(n)).
- LC #32 "Longest Valid Parentheses" — DP / stack hybrid.
- LC #301 "Remove Invalid Parentheses" — BFS or backtracking with removal.
- Power set, permutations — same backtracking template; different constraints.

## Variants

1. **Count only, don't generate** — return `C(n)`. Compute via DP or directly: `C(n) = C(2n, n) / (n+1)`. Useful when interviewer asks "what if n = 100?" — you can't generate 10^57 strings, but you can return the count.

2. **k-th valid string in lexicographic order** — given index `k`, return the k-th balanced string directly, using Catalan ranks for "how many strings start with this prefix." O(n) time, O(n) space.

3. **Mixed bracket types** — `()`, `[]`, `{}`. Same skeleton, more counters and a stack of open brackets. State space explodes; pruning gets messier.

4. **Generate all binary trees with n nodes (LC #95)** — same Catalan count, different output shape. Same recursion mental model (split n-1 children between left and right subtrees).

5. **Lazy iteration with generators** — `function*` + `yield` (provided in the solution). Essential for `n ≥ 15` where full materialization OOMs.

## Revision notes

> **generate parentheses — 60 second recap**
> - Output size **C(n)** (n-th Catalan number) — `C(3)=5, C(10)=16796, C(15)~10M`.
> - Time **`O(4^n / √n)`**, dominated by output size.
> - Backtracking with two counters: `open` and `close`.
>   - Place `(` if `open < n`.
>   - Place `)` if `close < open`.
> - Base case: `current.length === 2n`.
> - **Trap 1:** `n=0` returns `['']`, not `[]`.
> - **Trap 2:** using `close < n` instead of `close < open` — tighter constraint is the correct one.
> - **Don't filter** — prune. Generating all `4^n` strings and validating wastes `n^(3/2)` factor.
> - Family: N-queens, sudoku, word-break — constraint-driven backtracking.
> - Catalan count also appears in: binary tree shapes, Dyck paths, polygon triangulations.
