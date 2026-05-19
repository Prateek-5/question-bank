# Generate all valid parentheses combinations

> **Difficulty:** Medium   |   **Time:** ~12 min   |   **Prereqs:** [backtracking-template.md](./backtracking-template.md)
>
> **Source:** LeetCode #22. Catalan-number classic.

---

## 1. Problem statement

Generate all strings of n pairs of well-formed parentheses.

**Verification examples**

```js
generateParenthesis(3);
// ['((()))', '(()())', '(())()', '()(())', '()()()']

generateParenthesis(0);                   // ['']
generateParenthesis(1);                   // ['()']
```

**Constraints**
- Output count = C(n) (n-th Catalan number).
- C(0)=1, C(1)=1, C(2)=2, C(3)=5, C(4)=14.
- Constraint: `open < n` to place `(`; `close < open` to place `)`.
- Time O(4^n / √n).

---

## 2. Plain-English restatement

Two counters: `open` (placed `(`) and `close` (placed `)`). Place `(` if `open < n`; place `)` if `close < open`. Complete at length 2n.

---

## 3. Why this matters in interviews

Cleanest "backtracking with constraint" problem. Tests: constraint recognition, incremental build with two counters, Catalan literacy.

---

## 4. Mental model

```
   Two counters:
     open: how many '(' placed.
     close: how many ')' placed.
   
   Invariants:
     close ≤ open (otherwise unbalanced).
     open ≤ n (don't exceed budget).
   
   Place '(': if open < n.
   Place ')': if close < open.
   Complete: open + close == 2n, i.e., open == n && close == n.
   
   Why not "generate all 2^(2n) and filter"?
     Generates 4^n strings (n=10: ~1M); only C(n) valid (n=10: 16k).
     Pruning saves Θ(√n) work.
   
   Catalan: C(n) = C(2n, n) / (n+1) ≈ 4^n / (n^(3/2) √π).
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Output count for n=3?
> 2. When can you place `)`?
> 3. Why is unfiltered O(4^n) worse?

---

## 6. Brute force — walked through

```js
// Generate all 2^(2n), filter valid
function brute(n) {
  const out = [];
  function gen(s) {
    if (s.length === 2*n) { if (isValid(s)) out.push(s); return; }
    gen(s + '(');
    gen(s + ')');
  }
  gen('');
  return out;
}
```

O(4^n) generation; only C(n) valid. Massive waste.

---

## 7. The unlocking insight

> **Two counters; place `(` if `open<n`; place `)` if `close<open`. Prunes to exactly C(n) valid.**

Three properties:

1. **Two counters** `open, close`.
2. **`close < open`** invariant.
3. **Exactly C(n)** outputs.

---

## 8. Solution (annotated)

```js
function generateParenthesis(n) {
  const result = [];
  function backtrack(current, open, close) {
    if (current.length === 2 * n) {                                        // step 1: complete
      result.push(current);
      return;
    }
    if (open < n) backtrack(current + '(', open + 1, close);              // step 2: place (
    if (close < open) backtrack(current + ')', open, close + 1);          // step 3: place )
  }
  backtrack('', 0, 0);
  return result;
}

// Array variant — slightly faster (no string concat)
function generateParenthesisArr(n) {
  const result = [];
  const buf = [];
  function bt(open, close) {
    if (buf.length === 2 * n) { result.push(buf.join('')); return; }
    if (open < n) { buf.push('('); bt(open + 1, close); buf.pop(); }
    if (close < open) { buf.push(')'); bt(open, close + 1); buf.pop(); }
  }
  bt(0, 0);
  return result;
}

// Iterative via Catalan structure
function generateParenthesisDP(n) {
  if (n === 0) return [''];
  const dp = [[''], ['()']];
  for (let i = 2; i <= n; i++) {
    const cur = [];
    for (let j = 0; j < i; j++) {
      for (const left of dp[j]) {
        for (const right of dp[i - 1 - j]) {
          cur.push('(' + left + ')' + right);
        }
      }
    }
    dp.push(cur);
  }
  return dp[n];
}
```

**Try it yourself**

```js
generateParenthesis(3);
// ['((()))', '(()())', '(())()', '()(())', '()()()']  (5 strings)

generateParenthesis(4).length;                                // 14 (C(4))
generateParenthesis(5).length;                                // 42
generateParenthesis(10).length;                               // 16_796

// Validate manually
function isValid(s) {
  let depth = 0;
  for (const c of s) {
    if (c === '(') depth++;
    else if (--depth < 0) return false;
  }
  return depth === 0;
}

generateParenthesis(3).every(isValid);                         // true (all valid)
```

---

## 9. Step-by-step dry run

```
generateParenthesis(2):

backtrack('', 0, 0):
  length 0 < 4.
  open=0 < 2 → backtrack('(', 1, 0):
    length 1 < 4.
    open=1 < 2 → backtrack('((', 2, 0):
      length 2 < 4.
      open=2 < 2 false.
      close=0 < open=2 → backtrack('(()', 2, 1):
        length 3 < 4.
        open=2 < 2 false.
        close=1 < open=2 → backtrack('(())', 2, 2):
          length 4 == 4 → push '(())'. return.
        return.
      return.
    close=0 < open=1 → backtrack('()', 1, 1):
      open=1 < 2 → backtrack('()(', 2, 1):
        close=1 < open=2 → backtrack('()()', 2, 2):
          push '()()'.
        return.
      close=1 < open=1 false.
      return.
    return.
  open=0 < open=0 false. (close=0 < open=0 false)
  return.

Result: ['(())', '()()'] — C(2) = 2.

Catalan tree:
  n=2 has 2 results.
  n=3 has 5 results.
  n=4 has 14 results.
  Grows ~4^n / n^(3/2).
```

---

## 10. Common confusion + traps

1. **Generate all 2^(2n), filter** — wasteful.
2. **Stack-based validity per result** — slower than counter.
3. **`open <= n`** vs `<` — typo causes off-by-one.
4. **Concat string per call** — alloc per char.
5. **Forget base case** — infinite.
6. **`close < open` vs `<= open`** — `<= open` allows close=open=n at end (correct path takes equality at base case).
7. **Push live (no copy)** — strings are immutable; safe.

---

## 11. Senior follow-ups & variants

### Variant 1 — DP / Catalan structure
Build from smaller n.

### Variant 2 — Multiple bracket types
() [] {} — track open stack.

### Variant 3 — Count only (no generate)
`C(n) = C(2n, n) / (n+1)` formula.

### Variant 4 — Streaming generator
Yield one at a time; pause-able.

### Variant 5 — Random valid parens
Sample one uniformly; harder.

---

## 12. How to think aloud

> "Generate parentheses: two counters `open` (placed `(`) and `close` (placed `)`). Two rules: place `(` if `open < n`; place `)` if `close < open` (otherwise the string would have an unmatched `)`). Complete when `current.length === 2*n` (equivalent to `open === n && close === n`). The wrong approach: generate all `2^(2n) = 4^n` strings and filter — wastes massive work because only the n-th Catalan number `C(n) ≈ 4^n / (n^(3/2)√π)` are valid. Pruning saves `Θ(n^(3/2))` factor. Time complexity O(4^n / √n) — bounded by output size × per-string cost. C(3) = 5, C(4) = 14, C(10) = 16,796. Variants: array buffer (slightly faster than string concat); DP using Catalan structure `result(n) = sum over j of '(' result(j) ')' result(n-1-j)`; multiple bracket types use explicit open-stack; count-only via closed-form `C(n) = C(2n, n) / (n+1)`. Trap: brute force generate-then-filter; off-by-one (`open <= n` vs `<`); array buffer not popped (would corrupt sibling iterations); incorrect close condition (`close < open` is right)."

---

## 13. 60-second revision

> - **Two counters** `open, close`.
> - **Place `(`** if `open < n`.
> - **Place `)`** if `close < open`.
> - **Complete** at length `2n`.
> - **Count = C(n)** (Catalan).
> - **O(4^n / √n)** time.
> - **Strings immutable** — push safe.
> - **DP variant** — fold by structure.
> - **Trap:** generate-all-filter; off-by-one; concat alloc.

---

**Related:** [backtracking-template.md](./backtracking-template.md) · [permutations.md](./permutations.md) · [power-set.md](./power-set.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
