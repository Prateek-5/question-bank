# Recursive descent parser — mini expression evaluator

> **Difficulty:** Senior   |   **Time:** ~20 min   |   **Prereqs:** [backtracking-template.md](./backtracking-template.md), [json-path-resolver.md](./json-path-resolver.md)
>
> **Source:** Compiler construction. Razorpay, Atlassian.

---

## 1. Problem statement

Parse and evaluate arithmetic expression: `1 + 2 * 3` → 7. LL(1) recursive descent. Lexer + parser separate.

**Verification examples**

```js
evalExpr('1 + 2 * 3');                   // 7
evalExpr('(1 + 2) * 3');                 // 9
evalExpr('10 / 2 - 1');                  // 4
evalExpr('1.5 + 2.5');                   // 4
```

**Constraints**
- Grammar: `expr := term (('+'|'-') term)*`; `term := factor (('*'|'/') factor)*`; `factor := NUMBER | '(' expr ')'`.
- Operator precedence: `*` `/` over `+` `-`.
- Avoid left-recursion (would infinite-loop).
- Separate lexer (tokenize) from parser (recurse).

---

## 2. Plain-English restatement

LL(1) parser: each grammar rule becomes a function; recurse into sub-rules; consume tokens left-to-right; precedence via rule nesting.

---

## 3. Why this matters in interviews

Tests grammar design + recursion + tokenization. Senior bar: split lexer from parser, follow LL(1), handle precedence via grammar levels.

---

## 4. Mental model

```
   Grammar (LL(1) — no left recursion):
     expr   := term (('+' | '-') term)*
     term   := factor (('*' | '/') factor)*
     factor := NUMBER | '(' expr ')'
   
   Precedence:
     Lower rule = higher precedence.
     factor binds tightest; term next; expr loosest.
   
   Tokens (lexer):
     NUM, +, -, *, /, (, )
   
   Parser state:
     tokens[]
     pos (current index)
   
   Each rule function:
     consume tokens; return AST node or value.
   
   Why recursive descent:
     One function per rule. Mirrors grammar exactly.
     Easy to extend.
     Limit: LL(1) — one-token lookahead. Doesn't handle ambiguous/left-recursive grammars.
   
   Left recursion problem:
     expr := expr '+' term   (LEFT-recursive)
     Function expr() would call expr() infinitely.
     Fix: loop-based (term followed by more terms).
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. Why split lexer from parser?
> 2. What is left recursion and why avoid it?
> 3. How does precedence emerge from grammar structure?

---

## 6. Brute force — walked through

```js
function brute(s) {
  return eval(s);   // ← SECURITY HOLE; never ship.
}
```

`eval` is dangerous, slow, leaks scope. Never use for untrusted input.

---

## 7. The unlocking insight

> **One function per grammar rule. Lower rule = higher precedence. Loop instead of left-recurse. Lexer separate.**

Three properties:

1. **Function per rule**.
2. **Loop, not left-recurse.**
3. **Lexer separate** from parser.

---

## 8. Solution (annotated)

```js
function tokenize(input) {
  const tokens = [];
  let i = 0;
  while (i < input.length) {
    const c = input[i];
    if (/\s/.test(c)) { i++; continue; }                                    // step 1: skip whitespace
    if (/\d/.test(c)) {
      let j = i;
      while (j < input.length && /[\d.]/.test(input[j])) j++;
      tokens.push({ type: 'NUM', value: Number(input.slice(i, j)) });
      i = j;
    } else if ('+-*/()'.includes(c)) {
      tokens.push({ type: c });
      i++;
    } else {
      throw new SyntaxError(`Unexpected '${c}' at ${i}`);
    }
  }
  return tokens;
}

function parse(input) {
  const tokens = tokenize(input);
  let pos = 0;

  function peek() { return tokens[pos]; }
  function consume(type) {                                                  // step 2: helper
    if (peek()?.type !== type) {
      throw new SyntaxError(`Expected ${type}, got ${peek()?.type ?? 'EOF'}`);
    }
    return tokens[pos++];
  }

  function expr() {                                                          // step 3: lowest precedence
    let result = term();
    while (peek()?.type === '+' || peek()?.type === '-') {
      const op = tokens[pos++].type;
      const right = term();
      result = op === '+' ? result + right : result - right;
    }
    return result;
  }

  function term() {                                                          // step 4: higher precedence
    let result = factor();
    while (peek()?.type === '*' || peek()?.type === '/') {
      const op = tokens[pos++].type;
      const right = factor();
      result = op === '*' ? result * right : result / right;
    }
    return result;
  }

  function factor() {                                                        // step 5: highest precedence
    const tok = peek();
    if (tok?.type === 'NUM') { pos++; return tok.value; }
    if (tok?.type === '(') {
      consume('(');
      const result = expr();
      consume(')');
      return result;
    }
    throw new SyntaxError(`Unexpected ${tok?.type ?? 'EOF'}`);
  }

  const result = expr();
  if (pos < tokens.length) throw new SyntaxError(`Unexpected '${tokens[pos].type}'`);
  return result;
}

const evalExpr = parse;
```

**Try it yourself**

```js
evalExpr('1 + 2 * 3');                                        // 7
evalExpr('(1 + 2) * 3');                                      // 9
evalExpr('10 / 2 - 1');                                       // 4
evalExpr('1.5 + 2.5');                                        // 4

// Errors
try { evalExpr('1 +'); } catch (e) { console.log(e.message); }
try { evalExpr('(1'); } catch (e) { console.log(e.message); }
try { evalExpr('1 # 2'); } catch (e) { console.log(e.message); }

// Build AST instead of evaluating
function parseAst(input) {
  const tokens = tokenize(input);
  let pos = 0;
  function peek() { return tokens[pos]; }
  function expr() {
    let left = term();
    while (peek()?.type === '+' || peek()?.type === '-') {
      const op = tokens[pos++].type;
      const right = term();
      left = { type: 'BinOp', op, left, right };
    }
    return left;
  }
  function term() {
    let left = factor();
    while (peek()?.type === '*' || peek()?.type === '/') {
      const op = tokens[pos++].type;
      const right = factor();
      left = { type: 'BinOp', op, left, right };
    }
    return left;
  }
  function factor() {
    const t = peek();
    if (t?.type === 'NUM') { pos++; return { type: 'Num', value: t.value }; }
    if (t?.type === '(') {
      pos++;
      const e = expr();
      if (peek()?.type !== ')') throw new SyntaxError(')');
      pos++;
      return e;
    }
  }
  return expr();
}
parseAst('1 + 2 * 3');
// {type:'BinOp', op:'+', left:{Num:1}, right:{BinOp:'*', left:{Num:2}, right:{Num:3}}}

// Add right-associative power '^'
// factor := atom ('^' factor)?
function factorPow() { /* recursive call on right side for right-associative */ }
```

---

## 9. Step-by-step dry run

```
evalExpr('1 + 2 * 3'):

Tokenize: [NUM(1), +, NUM(2), *, NUM(3)].
pos=0.

expr():
  result = term():
    result = factor():
      tok=NUM(1). pos=1. return 1.
    peek=+, not * or /, exit loop.
    return 1.
  peek=+ → op='+', pos=2. right = term():
    result = factor():
      tok=NUM(2). pos=3. return 2.
    peek=*, * → op='*', pos=4. right = factor():
      tok=NUM(3). pos=5. return 3.
    result = 2 * 3 = 6.
    peek=undefined, exit.
    return 6.
  result = 1 + 6 = 7.
  peek=undefined, exit.
  return 7.

Return 7. ✓

Precedence via nesting:
  expr() calls term() for operands.
  term() calls factor() for operands.
  factor() can recurse to expr() (for parens).
  
  '*' is processed in term() before '+' in expr() consumes left operand.

(1 + 2) * 3:
  Tokens: [(, NUM(1), +, NUM(2), ), *, NUM(3)].
  expr():
    result = term():
      result = factor():
        peek=(, consume.
        result' = expr():
          ... 1 + 2 = 3.
        consume ).
        return 3.
      peek=*, op=*. right = factor():
        NUM(3) → 3.
      result = 3 * 3 = 9.
    Return 9.
```

---

## 10. Common confusion + traps

1. **Left recursion** — `expr := expr '+' term` loops infinitely.
2. **No lookahead** — can't distinguish '`-`' unary vs binary without context.
3. **No error position** — report `pos` for debugging.
4. **Missing token after operator** — should throw, not return.
5. **Stuck in factor** — endless recursion if grammar misdesigned.
6. **Eval `eval()`** — security/perf horror.
7. **String concat for AST nodes** — use objects.

---

## 11. Senior follow-ups & variants

### Variant 1 — Build AST
Don't evaluate; return tree node.

### Variant 2 — Unary minus
factor := '-' factor | NUM | '(' expr ')'.

### Variant 3 — Right-associative power
factor := atom ('^' factor)?.

### Variant 4 — JSON parser
Same technique; values: string/number/object/array/true/false/null.

### Variant 5 — Pratt parsing
Top-down operator precedence; cleaner for many operators.

---

## 12. How to think aloud

> "Recursive descent: one function per grammar rule. Grammar must be LL(1) (one-token lookahead) and non-left-recursive (would infinite-loop). Strategy: lower grammar rules = higher operator precedence. For arithmetic: `expr := term (('+'|'-') term)*` (lowest precedence), `term := factor (('*'|'/') factor)*`, `factor := NUMBER | '(' expr ')'` (highest precedence). Each function consumes tokens left-to-right and returns the evaluated value (or AST node). Loop pattern instead of left-recursion: `let result = term(); while (next is +/-) { result = result op term(); }` — this avoids `expr := expr '+' term` which would loop forever. Lexer SEPARATE: tokenize() returns array of `{type, value?}`; parser has `pos` cursor. Helpers: `peek()` looks at current; `consume(type)` advances or throws. Parens: factor recurses into expr — circular dependency, which is fine. Build AST instead of evaluating: return `{type: 'BinOp', op, left, right}` nodes; evaluator is a separate tree walk. Variants: unary minus (`factor := '-' factor | ...`); right-associative power (`factor := atom ('^' factor)?` recurses RIGHT-side to make `^` right-assoc); JSON parser (string/number/object/array). Pratt parsing is the elegant alternative for many operators. NEVER use `eval()` — security disaster. Trap: left recursion (infinite); no lookahead for unary; missing token errors silent; recurse into wrong rule (precedence wrong)."

---

## 13. 60-second revision

> - **One function per rule.**
> - **Lower rule = higher precedence.**
> - **Loop, don't left-recurse.**
> - **Lexer separate** from parser.
> - **`pos` cursor; `peek/consume` helpers.**
> - **Parens via factor → expr** circular.
> - **Build AST** for compilation.
> - **Pratt parsing** alternative.
> - **Trap:** left recursion; missing tokens; eval().

---

**Related:** [backtracking-template.md](./backtracking-template.md) · [json-path-resolver.md](./json-path-resolver.md) · [`08-maps-sets/convert-object-to-json-string.md`](../08-maps-sets/convert-object-to-json-string.md)

**Concept primer:** [`concepts/recursion-and-the-call-stack.md`](../../concepts/recursion-and-the-call-stack.md)
