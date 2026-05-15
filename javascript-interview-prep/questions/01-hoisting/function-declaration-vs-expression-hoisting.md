# Function declaration vs function expression hoisting

## Source
Canonical senior-JS interview problem. MDN reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/function#hoisting

## Why this question matters in interviews
This question separates candidates who memorized "JS hoists functions" from those who actually understand **what** gets hoisted. The interviewer's hidden agenda: do you know that `function foo() {}` and `var foo = function() {}` have completely different lifecycles, even though they look syntactically similar? In Node services this matters when you split a module into helpers and reorder things, or when you start mixing arrow functions with default exports. The output-prediction variant of this question shows up in roughly 1 in 3 senior JS screens.

## Concepts involved

### Syntax to lock in
```js
// Function declaration — FULLY hoisted (body + name)
sayHi();                // works — prints 'hi'
function sayHi() { console.log('hi'); }

// Function expression assigned to var — name hoisted as undefined
sayHello();             // TypeError: sayHello is not a function
var sayHello = function () { console.log('hello'); };

// Function expression assigned to let/const — TDZ
sayHey();               // ReferenceError: Cannot access 'sayHey' before initialization
const sayHey = function () { console.log('hey'); };

// Arrow function — same lifecycle as the var/let/const that holds it
greet();                // TypeError or ReferenceError depending on var vs let
var greet = () => console.log('greet');

// Named function expression — name is local to the expression only
const f = function bar() { /* `bar` only callable inside here */ };
// bar();   // ReferenceError outside
```

### Runtime / engine behavior
- During the **creation phase** of an Execution Context, the engine scans for declarations:
  - **Function declarations** (`function foo() {}`) are registered in the Variable Environment with the **full function object** as the value. Callable from line 1.
  - **`var` declarations** (`var foo = ...`) are registered with `undefined`. The assignment to the function expression happens in the execution phase.
  - **`let`/`const` declarations** are registered as `<uninitialized>` (TDZ).
- Function declarations take precedence over `var` for the same name during creation — but a later `var foo = something` will overwrite the binding at execution time.
- **Named function expressions** create a binding for the inner name (`bar` in `const f = function bar() {}`) that is visible only inside the function body — useful for recursion.
- An **arrow function** is just a function expression with shorter syntax and no own `this`/`arguments`. Its hoisting follows the declarator (`var` / `let` / `const`) — not function-declaration rules.

### Edge cases (interview traps)
1. **Function-in-block hoisting is implementation-defined (in legacy)** — `if (true) { function foo() {} }` was historically inconsistent across browsers. In strict mode and ES modules, the function is block-scoped. In sloppy mode, behavior varies.
2. **Order of identical names** — `function foo() { return 1 } function foo() { return 2 }` → the second wins. Both are hoisted; the later one overwrites in creation phase.
3. **`var foo = ...; function foo() {}`** — at end of creation phase the binding is the function (declarations beat `var`). Then `var foo = ...` runs in execution phase and overwrites it.
4. **Named function expression's inner name** — `const f = function inner() {}` — `inner` is only callable from inside `f`. Outside, `typeof inner === 'undefined'`.
5. **Hoisting and `default export`** — `export default function foo() {}` IS hoisted within its module. `export default () => {}` is NOT (it's an expression).
6. **IIFE hoisting** — the IIFE body isn't named-hoisted; the IIFE just runs. `(function () {})()` evaluates immediately.

## Brute force approach
Rusty candidate: *"All functions are hoisted, so both work."* Wrong — only function **declarations** are. Or worse: *"Neither works because you can't call before declaration."* Also wrong for the declaration case. The candidate needs to internalize that **what's on the right side of `=` is an expression**, and expressions only evaluate at their line during the execution phase.

## Optimal approach
Ask one question per identifier:

1. **What's the declarator?** `function` keyword as a statement → fully hoisted. `var` / `let` / `const` → only the binding is hoisted, with `undefined` / TDZ respectively.
2. **Is the RHS an expression?** If yes, the function object only exists after the assignment line runs.

These two checks resolve every variant.

## Solution (JavaScript)

```js
// === Setup ===
declared();          // 'I am a declaration'           ✅
expressed();         // TypeError: expressed is not a function   ❌
arrowed();           // ReferenceError (TDZ on const)            ❌

function declared() {
  console.log('I am a declaration');
}

var expressed = function () {
  console.log('I am a var expression');
};

const arrowed = () => console.log('I am an arrow on const');

// === After all declarations are processed ===
expressed();   // 'I am a var expression'
arrowed();     // 'I am an arrow on const'

// === Name shadowing example ===
function shadow() { return 'fn-decl'; }
var shadow = 'overwritten by assignment';
console.log(shadow);       // 'overwritten by assignment'
console.log(typeof shadow); // 'string'
```

## Step-by-step dry run

**Module/Global Execution Context — Creation phase**

| Identifier | Hoisted as            | Notes |
|------------|-----------------------|-------|
| `declared` | `<function declared>` | Full body hoisted |
| `expressed`| `undefined`           | `var` binding only |
| `arrowed`  | `<uninitialized>` (TDZ) | `const` binding |
| `shadow`   | `<function shadow>`   | Function decl wins over `var shadow` |

**Execution phase**, line by line:

1. `declared()` → resolves to the hoisted function → prints `'I am a declaration'`.
2. `expressed()` → `expressed` is `undefined` → calling `undefined()` throws `TypeError: expressed is not a function`. *(If the script were wrapped in try/catch we'd continue.)*

Assume the first two error lines are commented out so we proceed:

3. `arrowed()` → `arrowed` is in TDZ → `ReferenceError: Cannot access 'arrowed' before initialization`.
4. `function declared() {...}` — no-op at execution time (already hoisted).
5. `var expressed = function () {...}` — binding `expressed` now holds the function object.
6. `const arrowed = () => ...` — TDZ ends; binding now holds the arrow.
7. `expressed()` → prints `'I am a var expression'`.
8. `arrowed()` → prints `'I am an arrow on const'`.
9. `function shadow() {...}` — no-op at execution.
10. `var shadow = 'overwritten by assignment'` — binding now holds the string. The function is gone.
11. `console.log(shadow)` → `'overwritten by assignment'`.
12. `console.log(typeof shadow)` → `'string'`.

## Important takeaways

**Syntax to memorize**
- `function foo() {}` as a **statement** → fully hoisted (callable before its source line).
- `var foo = function () {}` → only `foo` is hoisted (as `undefined`). The function object exists only after the assignment.
- `let`/`const foo = function () {}` → `foo` is in TDZ until the line runs.
- Arrow functions follow their declarator's rules — no special hoisting.

**Patterns to reuse**
- For library code that needs to be usable in any order: use function declarations.
- For everything else (especially with bundlers and tree-shaking): use `const fn = () => ...`. The TDZ enforces declaration-before-use, which is a good discipline.
- Named function expressions (`const f = function recur() {}`) are useful for self-recursion when you don't want to leak the name to the outer scope.

**Common mistakes**
- Treating `var foo = function () {}` as if `foo` is callable before its line. It's not — it's `undefined`.
- Forgetting that `function foo() {}` inside an `if` block has implementation-defined hoisting in sloppy mode. Avoid this pattern; if you need conditional functions, assign to a `let`/`const` outside.
- Assuming arrow functions are "hoisted" because they look like functions. They are not — the **arrow expression** is evaluated at its line.

**Related questions**
- `var` hoisting output prediction
- TDZ with `let`/`const`
- Class declaration hoisting
- ES module export hoisting

## Variants

1. **Two declarations + one assignment** — `function foo(){return 'A'} var foo = 'B'; function foo(){return 'C'}` → at end of creation phase, `foo` is the second function (latest decl wins). Then the assignment runs → `foo === 'B'`. Tests order-of-operations between hoisting and runtime assignment.

2. **Function inside block (strict mode)** — `'use strict'; if (true) { function inner() {} } typeof inner;` → in strict ESM, prints `'undefined'` (block-scoped). In sloppy mode pre-ES6, prints `'function'`. Demonstrates the legacy quirk.

3. **Named function expression recursion** — write `factorial` without polluting outer scope: `const factorial = function fact(n) { return n <= 1 ? 1 : n * fact(n - 1); };`. Tests whether you know the inner name is locally scoped.

## Revision notes

> **fn decl vs expr hoisting — 60 second recap**
> - **Function declaration** → fully hoisted (body included). Callable from line 1.
> - **Function expression** (`var`/`let`/`const = function...`) → only the **binding** is hoisted: `var` → `undefined`, `let`/`const` → TDZ.
> - **Arrow function** → no special hoisting. Follows its declarator (`var` / `let` / `const`).
> - Function decls **beat** `var` for the same name during creation; later `var` assignment **overwrites** at execution.
> - **Named function expression** name (`function bar()` on RHS) → callable only inside the function. Good for recursion.
> - **Trap:** `var foo = function () {}; foo();` BEFORE the line → `TypeError: foo is not a function`, not `ReferenceError`.
> - **Trap:** `if (true) { function f() {} }` is implementation-defined in sloppy mode — avoid.
