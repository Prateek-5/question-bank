# Recursive Descent Parser (Mini Expression Parser)

## Source / Origin
- Standard compiler-construction technique.
- Asked at: Razorpay, Atlassian, anywhere parsers come up.
- Concept reference: `concepts/recursion.md`, sibling `10-machine-coding-patterns/json-parse-recursive-descent.md`.

## Why this question matters in interviews
"Parse an arithmetic expression `1 + 2 * 3` and evaluate." Tests grammar design + recursion + tokenization. Senior bar: you split lexer from parser, follow LL(1) descent, handle operator precedence via grammar levels, and avoid left-recursion pitfalls.

## Concepts involved

```js
// Grammar (LL(1)):
//   expr   := term ('+' | '-') term *
//   term   := factor ('*' | '/') factor *
//   factor := NUMBER | '(' expr ')'

function tokenize(input) {
  const tokens = [];
  let i = 0;
  while (i < input.length) {
    const c = input[i];
    if (/\s/.test(c)) { i++; continue; }
    if (/\d/.test(c)) {
      let j = i;
      while (j < input.length && /[\d.]/.test(input[j])) j++;
      tokens.push({ type: 'NUM', value: Number(input.slice(i, j)) });
      i = j;
    } else if ('+-*/()'.includes(c)) {
      tokens.push({ type: c, value: c });
      i++;
    } else throw new Error(`Unexpected ${c}`);
  }
  return tokens;
}

function parse(input) {
  const tokens = tokenize(input);
  let pos = 0;
  const peek = () => tokens[pos];
  const eat = (type) => {
    if (tokens[pos]?.type === type) return tokens[pos++];
    throw new Error(`Expected ${type}, got ${tokens[pos]?.type ?? 'EOF'} at ${pos}`);
  };
  function expr() {
    let left = term();
    while (peek() && (peek().type === '+' || peek().type === '-')) {
      const op = eat(peek().type).type;
      const right = term();
      left = { type: 'Binary', op, left, right };
    }
    return left;
  }
  function term() {
    let left = factor();
    while (peek() && (peek().type === '*' || peek().type === '/')) {
      const op = eat(peek().type).type;
      const right = factor();
      left = { type: 'Binary', op, left, right };
    }
    return left;
  }
  function factor() {
    if (peek().type === 'NUM') return { type: 'Num', value: eat('NUM').value };
    eat('(');
    const e = expr();
    eat(')');
    return e;
  }
  const ast = expr();
  if (pos < tokens.length) throw new Error(`Unexpected token at ${pos}`);
  return ast;
}

function evaluate(ast) {
  if (ast.type === 'Num') return ast.value;
  const l = evaluate(ast.left), r = evaluate(ast.right);
  switch (ast.op) { case '+': return l+r; case '-': return l-r; case '*': return l*r; case '/': return l/r; }
}
```

### Edge cases / traps
1. **Operator precedence** = grammar levels. `+/-` lower than `*//`. Don't try to encode precedence with conditionals in one function.
2. **Left-associative iteration** — use `while`, not recursion, at each precedence level, to make `1-2-3 = (1-2)-3`, not `1-(2-3)`.
3. **Left recursion** (grammar `expr := expr + term`) is forbidden in LL(1) — would infinite-loop. Use iteration.
4. **Unary minus** — add to factor: `factor := '-' factor | NUMBER | '(' expr ')'`.
5. **Function calls / variables** — extend grammar with IDENT and `IDENT '(' args ')'`.
6. **Error messages** — include position and expected/got. Don't just throw "syntax error."
7. **AST vs eval-on-the-fly** — AST is cleaner for further passes (optimization, codegen).

## Mental Model

```
   1 + 2 * 3
   
   tokenize → [NUM 1, +, NUM 2, *, NUM 3]
   
   expr ────┐
            term ────┐                 left=Num(1)
                     factor → Num(1)
                     (no */)
                     return Num(1)
                                       op=+
                     term ────┐
                              factor → Num(2)
                              (sees *) factor → Num(3)
                              → Binary(*, 2, 3)
                                       right=Binary(*, 2, 3)
            return Binary(+, 1, Binary(*, 2, 3))
   
   eval: 1 + (2*3) = 7
```

## Solution

See "Syntax to lock in" above. With unary support:

```js
function factor() {
  if (peek().type === '-') { eat('-'); return { type: 'Unary', op: '-', expr: factor() }; }
  if (peek().type === 'NUM') return { type: 'Num', value: eat('NUM').value };
  eat('(');
  const e = expr();
  eat(')');
  return e;
}

// evaluate adds Unary case
function evaluate(ast) {
  if (ast.type === 'Num') return ast.value;
  if (ast.type === 'Unary') return -evaluate(ast.expr);
  const l = evaluate(ast.left), r = evaluate(ast.right);
  switch (ast.op) { case '+': return l+r; ... }
}

// Pratt-parser variant: precedence table, single function
function parsePratt(tokens) {
  let pos = 0;
  const prec = { '+': 1, '-': 1, '*': 2, '/': 2 };
  function parse(minPrec = 0) {
    let left = parsePrimary();
    while (pos < tokens.length && prec[tokens[pos]?.type] >= minPrec) {
      const op = tokens[pos++].type;
      const right = parse(prec[op] + 1);   // left-associative; right-assoc would use prec[op]
      left = { type: 'Binary', op, left, right };
    }
    return left;
  }
  // ...
}
```

## Dry run

`(1+2)*3`:

```
tokens: [(, NUM 1, +, NUM 2, ), *, NUM 3]

expr → term → factor:
  peek = '(' → eat '('
  expr (recursive):
    term → factor:
      peek = NUM → Num(1)
    (loop: peek='+', not */ → exit)
    (back in outer expr, peek='+')
    op='+', eat '+'
    term → factor: Num(2)
    left = Binary(+, 1, 2)
    (peek=')', not +/- → exit)
  eat ')'
  return Binary(+, 1, 2)
(back in outer term, peek='*')
op='*', eat '*'
factor → Num(3)
left = Binary(*, Binary(+,1,2), 3)
return

eval: (1+2)*3 = 9
```

## How to think aloud

> "Recursive descent: one function per grammar production. Precedence = nesting level: lowest precedence at top, highest at leaf. Iterate within a level for left-associativity. No left recursion in the grammar. Separate lexer simplifies the parser. AST as output, evaluator as a second pass. For richer grammars, Pratt parsing is cleaner — single function + precedence table."

## Important takeaways

- **One function per grammar production.**
- **Precedence = nesting** (outer = lower precedence).
- **Iterate within a level** for left-associativity.
- **No left recursion** in LL(1).
- **AST then evaluate**, two passes.
- **Pratt** for compact precedence-driven parsing.

## Variants

- **Pratt parser** — precedence-climbing.
- **Parser combinators** (e.g., Parsimmon) — composable parsers.
- **Earley / GLR** for ambiguous grammars (rare in interviews).
- **PEG** — packrat parsers with memoization.

## Revision notes

```
LL(1) recursive descent:
  one function per non-terminal
  lower precedence → outer function (expr)
  higher precedence → inner (term, factor)
  iterate WITHIN level (left-assoc)
  no left recursion

grammar:
  expr   := term ('+'|'-') term *
  term   := factor ('*'|'/') factor *
  factor := NUM | '(' expr ')' | '-' factor

split lexer (tokens) from parser (AST)
evaluator = second pass over AST

USES:
  expression evaluators
  config languages
  query DSLs
  JSON-like formats

ALT: Pratt parser for compact precedence
```
