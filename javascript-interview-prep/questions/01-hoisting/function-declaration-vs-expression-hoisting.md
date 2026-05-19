# Function declaration vs expression hoisting

> **Difficulty:** Medium   |   **Time:** ~12 min   |   **Prereqs:** [hoisting-in-javascript.md](./hoisting-in-javascript.md), [tdz-let-const.md](./tdz-let-const.md)
>
> **Source:** MDN function hoisting. Senior JS gate question.

---

## 1. Problem statement

How do these four forms differ in hoisting behavior?

```js
declared();        // works
expressed();       // TypeError: not a function
constArrow();      // ReferenceError: TDZ
varArrow();        // TypeError: not a function

function declared() {}
var expressed = function () {};
const constArrow = () => {};
var varArrow = () => {};
```

**Verification examples**

| Form                                  | Pre-line-of-declaration                            |
|---------------------------------------|----------------------------------------------------|
| `function foo() {}`                   | callable (fully hoisted with body)                |
| `var foo = function() {}`             | `undefined` → calling = `TypeError`               |
| `let/const foo = function() {}`       | TDZ → `ReferenceError`                            |
| `var foo = () => {}` (arrow)          | same as var-fn-expression                          |
| `let/const foo = () => {}` (arrow)    | TDZ                                                |
| Named fn expression: `const f = function bar() {}` | `bar` only callable INSIDE the function   |

**Constraints**
- Only **function declarations** are fully hoisted (binding + body).
- Function expressions on right-hand side: only the BINDING is hoisted.
- Arrow functions follow their declarator (var/let/const).
- Named fn expression name (`bar`) is locally scoped to the function body.

---

## 2. Plain-English restatement

`function foo() {}` is a STATEMENT — fully hoisted with body, callable from line 1. `var foo = function() {}` is an EXPRESSION on the right side — only `foo` is hoisted (as `undefined`), the function object doesn't exist until the assignment runs. Arrow functions are expressions too; they follow their declarator.

---

## 3. Why this matters in interviews

The "do you know what gets hoisted?" gate. Mid-level says "all functions are hoisted." Senior knows: only declarations are; expressions follow their declarator.

---

## 4. Mental model

```
   Ask two questions per identifier:
   
   1. What's the declarator?
      function statement → fully hoisted (body + name) ✓
      var foo = ...       → foo hoisted as undefined; RHS evaluates at execution
      let/const foo = ... → foo in TDZ until line runs
   
   2. Is the RHS an expression?
      If yes → function object only exists after assignment line.

   Examples:
   
   function declared() {}            ← STATEMENT
     → declared: <function> at creation
   
   var expressed = function () {};   ← EXPRESSION (RHS)
     → expressed: undefined at creation
     → function object created + assigned at execution line
   
   const arrowed = () => {};         ← EXPRESSION (RHS)
     → arrowed: <uninitialized> (TDZ) at creation
     → assigned at execution line
   
   const f = function bar() {};      ← NAMED FN EXPRESSION
     → f follows const TDZ; bar is local to function body only
     → typeof bar === 'undefined' outside
```

---

## 5. Try it yourself first

> **Predict before reading on:**
> 1. What does `expressed(); var expressed = function() {}` throw — TypeError or ReferenceError?
> 2. Is `arrow()` (where `arrow = () => {}`) callable before its line?
> 3. Can you call `bar()` after `const f = function bar() {}`?

---

## 6. Brute force — walked through

### Wrong attempt 1: "all functions are hoisted"
Only declarations. Expressions follow declarator.

### Wrong attempt 2: "calling expressed() before line throws ReferenceError"
For `var`, it's `TypeError: foo is not a function` (foo is undefined, not missing). For `let`/`const`, ReferenceError.

### Wrong attempt 3: arrow has special hoisting
No — arrow is an expression; follows var/let/const rules.

---

## 7. The unlocking insight

> **Function declarations are fully hoisted (statement form). Function expressions only have their binding hoisted — `var` → `undefined`, `let`/`const` → TDZ. Arrow functions are expressions; follow declarator. Named fn expression's inner name is local-only.**

Three properties:

1. **Statement vs expression** form determines hoisting.
2. **Arrow follows declarator** — no special hoisting.
3. **Named fn expression's name** is scoped to its body.

---

## 8. Solution (annotated)

```js
// All four forms in one script
declared();                                                            // 'declaration'
try { expressed(); } catch (e) { console.log('var-fn:', e.message); }  // TypeError
try { arrowed(); }   catch (e) { console.log('const-arrow:', e.message); }  // TDZ

function declared() { console.log('declaration'); }                    // step 1: STATEMENT, fully hoisted

var expressed = function () { console.log('var-fn'); };                 // step 2: var hoisted as undefined

const arrowed = () => console.log('const-arrow');                       // step 3: const TDZ

// After declarations:
expressed();                                                            // 'var-fn'
arrowed();                                                              // 'const-arrow'

// Named function expression
const f = function bar() { return 'inner'; };
f();                                                                    // 'inner'
try { bar(); } catch (e) { console.log('bar outside:', e.message); }   // ReferenceError

// Name shadowing
function shadow() { return 'fn-decl'; }
var shadow = 'string assigned later';                                   // step 4: var assignment overwrites
console.log(shadow);                                                    // 'string assigned later'
console.log(typeof shadow);                                             // 'string'
```

---

## 9. Step-by-step dry run

```
Creation phase:
  declared    → <function declared>           (statement, fully hoisted)
  expressed   → undefined                      (var hoisted)
  arrowed     → <uninitialized> (TDZ)          (const)
  f           → <uninitialized> (TDZ)          (const)
  shadow      → <function shadow>              (function decl wins over var of same name)

Execution phase:
  1. declared()              → resolves to fn → prints 'declaration'
  2. expressed()             → expressed = undefined → calling undefined() → TypeError
  3. arrowed()               → arrowed in TDZ → ReferenceError
  4. function declared() {}  → no-op (already hoisted)
  5. var expressed = ...     → expressed = function object
  6. const arrowed = ...     → arrowed transitions from TDZ to arrow fn
  7. expressed()             → 'var-fn'
  8. arrowed()               → 'const-arrow'
  9. const f = function bar() ...  → f assigned; bar scoped to fn body
  10. f()                    → 'inner'
  11. bar() outside          → ReferenceError (bar not in outer scope)
  12. function shadow() {}   → no-op (already hoisted)
  13. var shadow = 'string'  → binding now 'string' (function gone)
  14. console.log(shadow)    → 'string assigned later'
  15. typeof shadow          → 'string'
```

---

## 10. Common confusion + traps

1. **"All functions hoisted"** — only declarations.
2. **`expressed()` before line throws ReferenceError** — TypeError (undefined is not a function).
3. **Arrow has special hoisting** — no, follows declarator.
4. **Named fn expression's `bar` accessible outside** — no, local to function body.
5. **Function decl in block (sloppy)** — implementation-defined; avoid.
6. **`default export function`** — hoisted within module. `default export ()=>` — not.
7. **Order of identical names** — function decls hoisted, later var assignment wins at execution.

---

## 11. Senior follow-ups & variants

### Variant 1 — Two declarations + one assignment
`function foo(){return 'A'} var foo = 'B'; function foo(){return 'C'}` → at end of creation, foo is 2nd function (latest decl wins). Then var assignment → foo === 'B'.

### Variant 2 — Function in block strict mode
`'use strict'; if (true) { function inner() {} } typeof inner` → 'undefined' (block-scoped in strict ESM).

### Variant 3 — Named fn expression for recursion
`const factorial = function fact(n) { return n <= 1 ? 1 : n * fact(n-1); }`. `fact` is callable inside without polluting outer scope.

### Variant 4 — Arrow vs function decl `this`
Arrow has lexical `this`; function decl has dynamic `this`. Separate from hoisting; mention.

### Variant 5 — Hoisting + `default export`
`export default function foo() {}` → hoisted. `export default () => {}` → not.

---

## 12. How to think aloud

> "Two questions per identifier: (1) what's the declarator — `function` statement, `var`, `let`/`const`? (2) Is the RHS an expression? Function declarations (statement form) are fully hoisted with body — callable from line 1. Function expressions (RHS of assignment) have only the BINDING hoisted: `var` → `undefined` → calling it pre-assignment throws TypeError; `let`/`const` → TDZ → ReferenceError. Arrow functions are expressions; follow their declarator — no special hoisting. Named fn expression like `const f = function bar() {}` — `bar` is callable INSIDE the function body for recursion but invisible outside. Trap: 'all functions are hoisted'; arrow is special; TypeError vs ReferenceError distinction."

---

## 13. 60-second revision

> - **Function declaration** (`function foo() {}`) → fully hoisted (body included). Callable from line 1.
> - **Function expression** (`var/let/const = function...`) → only BINDING hoisted: var → undefined, let/const → TDZ.
> - **Arrow function** → no special hoisting; follows declarator.
> - **Named fn expression** name → callable only inside body (good for recursion).
> - **Function decl beats var** for same name at creation; runtime var assignment overwrites.
> - **`var foo = function() {}; foo()` before line** → `TypeError: foo is not a function` (NOT ReferenceError).
> - **Trap:** "all functions hoisted"; arrow special; TypeError/ReferenceError confusion; functions in blocks (sloppy quirks).

---

**Related:** [hoisting-in-javascript.md](./hoisting-in-javascript.md) · [tdz-let-const.md](./tdz-let-const.md) · [named-fn-expression-binding.md](./named-fn-expression-binding.md) · [func-expr-in-conditional.md](./func-expr-in-conditional.md) · [class-hoisting.md](./class-hoisting.md)

**Concept primer:** [`concepts/hoisting.md`](../../concepts/hoisting.md)
