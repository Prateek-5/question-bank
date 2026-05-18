# Temporal Dead Zone with Default Parameters

## Source / Origin
- ECMAScript 2015 — let/const + default-parameter semantics.
- Asked at: Stripe, Atlassian, Razorpay, Cloudflare — output-prediction trivia.
- Concept reference: `concepts/hoisting.md`.

## Why this question matters in interviews
Default parameters introduce a tiny per-call lexical scope that's separate from the function body. Combined with `let`/`const`'s TDZ, you get surprising errors: a parameter that *seems* defined throws `ReferenceError`. Senior bar: you can predict the output, explain the scope chain, and reason from first principles about why the spec was designed this way (avoid the var-style "use before declared = undefined" footgun).

## Concepts involved

### Syntax to lock in
```js
// Each parameter creates its own lexical scope; later params can see earlier ones
function ok(a, b = a) { return [a, b]; }
ok(1);           // [1, 1]

function tdz(a = b, b = 1) { return [a, b]; }     // throws ReferenceError
tdz();           // ReferenceError: Cannot access 'b' before initialization

function shadow(x) {
  return function (x = x) { return x; };           // x in default refers to outer? NO — inner TDZ
}
shadow(5)();     // ReferenceError: Cannot access 'x' before initialization

let n = 1;
function (n = n) {}                                // ReferenceError too
```

### Edge cases / interview traps
1. **Parameter scope ≠ body scope.** They are separate lexical scopes. The body can shadow params but the default can refer only to params declared *earlier*.
2. **TDZ applies to params.** A param is "declared but not initialized" until its initializer runs. Referring to a later one throws.
3. **Self-reference is TDZ.** `function f(x = x)` — RHS `x` is the *param* `x` (not outer `x`), still TDZ.
4. **`var` in body cannot shadow** a same-named param without weird "preserve binding" quirks (strict vs sloppy).
5. **`arguments` object** still holds positional values, even with destructuring defaults.
6. **Destructuring defaults** also TDZ — `function f({a = b, b = 1}) {}` is order-sensitive.
7. **Cross-param closures** — a default function expression can close over later params if it's invoked later; usually no.
8. **Block scope inside body** — `{ let x = 1; }` does not affect params.

## Mental Model

Two lexical scopes per call:

```
   function f(a = expr1, b = expr2) {
     // body scope (separate from parameter scope)
     let local;
   }

   parameter scope at call:
     ┌──────────────────────────┐
     │ a (declared, uninitialized) │   ← TDZ until expr1 runs
     │ b (declared, uninitialized) │   ← TDZ until expr2 runs
     └──────────────────────────┘
   
   evaluation order (per call):
     1. enter parameter scope with all params in TDZ
     2. for each param i in order:
          if argument provided: a_i := arg
          else: a_i := evaluate expr_i in parameter scope
            (can read earlier a_j; later a_j still TDZ)
     3. enter body scope
```

## Why interviewers care

- **TDZ understanding** beyond the canonical `let x = x` case.
- **Scope chain awareness** — the parameter-scope/body-scope distinction.
- **Spec-level intuition** — senior signal.

## Common beginner confusion

- **"Parameters are like `var`."** They're not — they're like `let` (TDZ-aware).
- **"Default values are evaluated once at function definition."** No — once per call, in parameter scope, at call time.
- **"`function f(x = x)` uses outer x."** No — the local `x` shadows. RHS `x` is the same `x`, still TDZ.
- **"Order doesn't matter."** It does — params must reference only previously-evaluated params.
- **"Arrow functions behave differently."** They don't (for this rule).

## Brute force approach

Memorize the patterns. Or just put initializers in body:

```js
function f(a, b) {
  if (a === undefined) a = 1;
  if (b === undefined) b = a;
  ...
}
```

Works but loses the elegance and the `length` property (default-param functions report `length` of params *before* the first default).

## Optimal approach

Order params so each default references only previously-declared params, and never the same name as itself:

```js
function f(a = 1, b = a, c = a + b) { ... }     // OK
function bad(a = b, b = 1) { ... }              // throws
function badAlso(a = a) { ... }                 // throws
```

## Solution (JavaScript)

```js
// Various test cases for self-quiz
function q1(a, b = a) { return [a, b]; }
q1(2);                                          // [2, 2]
q1(2, 5);                                       // [2, 5]
q1(undefined, 5);                               // [undefined, 5]

function q2(a = b, b = 1) { return [a, b]; }
try { q2(); } catch (e) { console.log(e); }     // ReferenceError

let x = 5;
function q3(y = x) { return y; }
q3();                                           // 5 — uses outer x

function q4(x = x) {}                           // self-ref in param scope
try { q4(); } catch (e) { console.log(e); }     // ReferenceError

function q5(a = 1) {
  let a = 2;                                    // SyntaxError in strict mode (duplicate)
  // (parameter `a` is in parameter scope; `let a` in body is duplicate-name vs body scope is OK
  //  but most engines flag it as an error since it would shadow ambiguously)
}

function q6({a = 1, b = a} = {}) { return [a, b]; }
q6();                                           // [1, 1]  — destructuring also evaluates in order
q6({a: 3});                                     // [3, 3]
q6({b: 5});                                     // [1, 5]
```

## Step-by-step dry run

```js
function tdz(a = b, b = 1) { return [a, b]; }
tdz();
```

```
enter parameter scope
  a: declared, TDZ
  b: declared, TDZ

evaluate a:
  argument? no
  initializer expression: `b`
  look up `b` in parameter scope → b is in TDZ → THROW ReferenceError
```

For `function shadow(x) { return function (x = x) { return x; }; }; shadow(5)();`:

```
shadow(5):
  enter parameter scope of shadow: x=5
  return inner function
shadow(5)():
  enter parameter scope of inner: x is declared, TDZ
  evaluate x's initializer: `x` — refers to inner x (shadowing rule) → TDZ → THROW
```

## How to think aloud in the interview

> "Each call creates a parameter scope separate from the body scope. Params are declared in TDZ at the start and initialized in left-to-right order; defaults are evaluated lazily in this scope. So `function f(a = b, b = 1)` throws because when evaluating `a`'s default, `b` is still in TDZ. `function f(x = x)` throws because the local `x` shadows outer; the RHS resolves to the same local `x` in TDZ. To avoid: order params so later defaults reference earlier ones; never self-reference."

## Important takeaways

- **Params live in their own scope, with TDZ.**
- **Left-to-right initialization.** Later params unavailable to earlier defaults.
- **Self-reference is TDZ.**
- **Shadowing applies** — `function f(x = x)` resolves RHS to the local `x`.
- **Destructuring defaults** evaluate in declaration order, same TDZ rules.
- **`arguments`** is independent — still reflects positional args.

## Variants

- **Class field initializers** — analogous TDZ rules in class bodies.
- **Computed default expressions** — full statements/expressions allowed; can throw.
- **`function.length` quirk** — defaults reduce `length`; e.g., `function f(a, b = 1, c) { }.length === 1`.
- **`arguments` vs params** — they're synced in sloppy mode; not in strict mode (with defaults).
- **Rest + default combo** — `function f(...args, x = 1)` is a SyntaxError (rest must be last).

## Revision notes

```
Default parameter scope:
  each call → new parameter scope (separate from body)
  params declared in TDZ at entry
  initialize in declaration order
  default can reference EARLIER params only
  
  TRAPS:
    function f(a = b, b = 1)    → throws (b in TDZ when a's default evaluates)
    function f(x = x)           → throws (RHS = local x in TDZ)
    function f({a = b, b = 1})  → throws (same TDZ rule via destructuring)
  
  rule: forward-only references in defaults
  outer-scope `let x` IS visible (no shadowing yet at parameter scope entry... wait, the LOCAL x shadows)
  `function.length` reports count BEFORE first default
```
