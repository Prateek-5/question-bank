# Named Function Expression — Inner Binding & Hoisting

## Source / Origin
- Spec section "RuntimeSemantics: Evaluation" of FunctionExpression.
- Classic output-prediction puzzle; common in senior screens.
- Concept reference: `concepts/hoisting.md`, `concepts/closures.md`.

## Why this question matters in interviews
`const f = function inner() { ... }` creates *two* bindings: the outer `f` and an *inner* `inner` only visible inside the function. People reach for this when they want recursion without name collision; engines use it for stack-trace clarity. Senior bar: you know it's read-only inside (strict mode throws on assignment), you can predict subtle hoisting questions, and you understand it's NOT the same as a declaration.

## Concepts involved

### Syntax to lock in
```js
// Anonymous function expression
const a = function () { /* arguments.callee deprecated */ };

// Named function expression — `inner` is visible only inside
const b = function inner(n) {
  if (n === 0) return 1;
  return n * inner(n - 1);            // safe recursion
};
inner;                                 // ReferenceError — not visible outside
b.name === 'inner';                    // true

// Function declaration is different (visible in enclosing scope)
function decl() {}
decl();                                // OK

// NFE name is read-only
const c = function self() {
  self = 99;                           // silently fails in sloppy; TypeError in strict
};
```

### Edge cases / interview traps
1. **Inner name is not visible outside** the expression. `inner` is only inside.
2. **The inner name is read-only** in strict mode. Assignment throws.
3. **`f.name` returns the NFE name**, useful for debugging and serialization.
4. **Function declarations vs expressions** — declarations hoist (name + body); expressions hoist only the variable (which is `undefined` until assigned).
5. **NFE never hoists into outer scope.** Even with `var`, only the variable name hoists; the body is assigned later.
6. **`arguments.callee`** is the historical way to recurse from anonymous expressions — banned in strict.
7. **Class expression analog** — `const C = class Inner { ... }`. `Inner` only visible inside class body.
8. **NFE in IIFE** — `(function self() { self() })()` infinite-loops; you have your own name without polluting outer scope.

## Mental Model

A named function expression is **a function with a backstage badge that only the function itself can see**:

```
   ┌────────────────────────────────────┐
   │ outer scope:                       │
   │   var b → assigned later           │
   │                                    │
   │   ┌──────────────────────────────┐ │
   │   │ NFE inner scope:             │ │
   │   │   inner (read-only, points   │ │
   │   │           to the function)   │ │
   │   │   ...body...                 │ │
   │   └──────────────────────────────┘ │
   │                                    │
   │   inner   ← not visible here       │
   └────────────────────────────────────┘
```

When the function is invoked, JS adds an extra scope with the `inner` binding *before* the body's local scope. That's why `inner` works inside but not outside.

## Why interviewers care

- **Hoisting nuance** — knowing the difference between declarations and expressions.
- **Self-recursion patterns** — avoiding `arguments.callee`.
- **Spec literacy** — the inner binding rule is non-obvious.

## Common beginner confusion

- **"NFE hoists the name into the outer scope."** Nope. Only the variable (if any) hoists, and only its name (not value).
- **"You can reassign the inner name."** Read-only inside.
- **"`arguments.callee` is fine."** Banned in strict mode; use NFE instead.
- **"NFE adds another `function.name`."** The inner name *is* `function.name`.
- **"Anonymous functions can't recurse."** They can, via the variable (`const f = function(n) { f(n-1); }`) — but that breaks if `f` is reassigned. NFE is safer.

## Brute force approach

```js
// Anonymous — uses outer var; breaks if var reassigned
const fact = function (n) {
  return n === 0 ? 1 : n * fact(n - 1);
};
const f2 = fact;
fact = null;                            // strict: TypeError; sloppy: succeeds
f2(5);                                  // crashes: fact is null
```

## Optimal approach

NFE — the inner name is safe from outer reassignment.

```js
const fact = function fact_(n) {
  return n === 0 ? 1 : n * fact_(n - 1);   // inner name; not affected by outer mutation
};
const f2 = fact;
fact = null;                                // safe; inner fact_ still points to function
f2(5);                                       // 120
```

## Solution (JavaScript)

```js
// Pattern 1: recursive NFE
const fib = function fibInner(n) {
  if (n < 2) return n;
  return fibInner(n - 1) + fibInner(n - 2);
};

// Pattern 2: better stack traces
const debounce = function debounceInner(fn, ms) {
  let timer;
  return function debounceWrapper(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
};
debounce(() => {})(/* throws here */);   // stack trace shows debounceWrapper, not <anonymous>

// Pattern 3: NFE in IIFE for module-private state
const counter = (function counterImpl() {
  let n = 0;
  return { inc: () => ++n, peek: () => n };
})();
counter.inc(); counter.inc(); counter.peek();   // 2
```

## Step-by-step dry run

```js
const a = function inner(n) {
  if (n === 0) return 'done';
  return inner(n - 1);
};
a(2);            // 'done'
inner;           // ReferenceError
```

```
declaration of `a`:
  const a in TDZ
  evaluate RHS: create function {
    body: ...
    name: 'inner'
    inner scope: { inner: this-function (read-only) }
  }
  a := this function
  a.name === 'inner'

call a(2):
  enter function scope (with inner-binding)
  enter body scope (local vars)
  body: n=2, not 0, return inner(1)
  call inner(1) [resolves via inner-binding scope]
  ... recursion ...

`inner` lookup in outer scope:
  outer scope has `a`, not `inner` → ReferenceError
```

Reassignment trap:

```js
const a = function inner() {
  inner = 99;                            // strict: TypeError; sloppy: silently fails
  return inner;                          // returns the function (sloppy) or unreachable (strict)
};
a();
```

## How to think aloud in the interview

> "Named function expression: `function name() {}` on the RHS of an assignment. The name is bound only inside the function, read-only, and gives me safe recursion + better stack traces. The outer variable is the public name; the inner is the recursion handle. Inner doesn't pollute the outer scope. Replaces `arguments.callee` (banned in strict). Class expressions have the same pattern."

## Important takeaways

- **NFE: outer var + read-only inner name.**
- **Inner only visible inside the function.**
- **Replaces `arguments.callee`** for recursion.
- **Better stack traces** (named, not `<anonymous>`).
- **`function.name`** reflects the inner name.
- **Class expressions** (`class Inner { }`) follow the same pattern.

## Variants

- **Class expression** — `const C = class Inner { static method() { return Inner.X; } }`; `Inner` inside, `C` outside.
- **Object-method shorthand** — `{ method() {} }` — the function's name is `method`.
- **Generator NFE** — `function* gen() {}` — same rules.
- **Async NFE** — `async function self() {}` — same rules.
- **Default-export named** — `export default function name() {}` — `name` is local; outside, the export is `default`.

## Revision notes

```
Named Function Expression (NFE):
  const v = function inner() { ... };
  outer: `v` (assignable)
  inner: `inner` (read-only, function-scope only)
  
  USES:
    - safe recursion (outer var can be reassigned)
    - clean stack traces
    - replacement for arguments.callee
    
  TRAPS:
    - inner name is NOT visible outside
    - read-only in strict (TypeError on assign)
    - inner binding is FUNCTION-scope, not enclosing scope
    
  vs declaration:
    function decl() {}  — hoisted (name+body), visible in enclosing scope
    const v = function() {}  — only `v` hoists (as undefined until assigned)
```
