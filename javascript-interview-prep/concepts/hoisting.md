# Hoisting

## TL;DR
- **Hoisting = the engine allocates bindings during the "creation phase" of an execution context BEFORE running code line-by-line.**
- `var` is hoisted and initialized to `undefined`. `let`/`const`/`class` are hoisted but NOT initialized — accessing them throws → **Temporal Dead Zone (TDZ)**.
- **Function declarations** are fully hoisted (binding + value). **Function expressions / arrow functions** assigned to `var` hoist only the variable.
- ES Modules: top-level `var`/`function` do NOT pollute global; `import` bindings are hoisted and live (read-only).
- "Hoisting" is a mental model — V8 actually does this via the lexical environment + variable environment created at scope entry.

## Why backend interviewers care
- Backend code runs in long-lived Node processes; subtle TDZ bugs in module init can crash workers at boot.
- Understanding hoisting clarifies module load order, circular dependency hazards, and why `require` (CJS) vs `import` (ESM) behave differently.
- Output-prediction questions on hoisting are the cheapest filter interviewers use to gauge JS depth.

## Core mental model
Every execution context (global, function, block for `let`/`const`) goes through two phases:

1. **Creation phase**: the engine scans the scope and registers all declarations. `var` → bound to `undefined`. `function` declarations → bound to the function object. `let`/`const`/`class` → bindings created but marked *uninitialized* (TDZ).
2. **Execution phase**: code runs top-to-bottom.

In V8, this is implemented via two environment records attached to the context: the **VariableEnvironment** (for `var`/function decls) and the **LexicalEnvironment** (for `let`/`const`/block scopes). The TDZ is literally a flag on the binding — reading it before initialization throws `ReferenceError`.

```js
console.log(a); // undefined   ← var hoisted + initialized
console.log(b); // ReferenceError ← let in TDZ
console.log(foo()); // "hi"    ← function decl fully hoisted

var a = 1;
let b = 2;
function foo() { return "hi"; }
```

Function declarations are special because their *value* is hoisted, not just the name. Function expressions (`var f = function(){}`) only hoist the `var` binding (= undefined) — calling `f()` before the line throws TypeError.

Classes are hoisted but TDZ'd, so `new Foo()` before the `class Foo {}` line throws ReferenceError — unlike functions.

## Syntax cheat sheet
```js
// var: hoisted, initialized to undefined, function-scoped
console.log(x); // undefined
var x = 5;

// let/const: hoisted but TDZ until declaration line
// console.log(y); // ReferenceError
let y = 5;
const z = 6;

// function declaration: fully hoisted
greet(); // works
function greet() { console.log("hi"); }

// function expression: only var is hoisted
// sayHi();        // TypeError: sayHi is not a function
var sayHi = function() {};

// arrow on let: TDZ
// say();          // ReferenceError
let say = () => {};

// class: hoisted but TDZ
// new Foo();      // ReferenceError
class Foo {}

// Block scope for let/const/class; var ignores blocks
{
  var leaks = 1;  // accessible outside
  let stays = 2;  // block-scoped
}
console.log(leaks); // 1
// console.log(stays); // ReferenceError

// var redeclaration allowed; let/const not
var a = 1; var a = 2; // ok
let b = 1; // let b = 2; // SyntaxError

// for-loop binding: var shares one binding; let creates one per iter
for (var i = 0; i < 3; i++) setTimeout(() => console.log(i)); // 3 3 3
for (let j = 0; j < 3; j++) setTimeout(() => console.log(j)); // 0 1 2

// typeof on TDZ var still throws (unlike undeclared)
// typeof undeclared; // "undefined"
// typeof tdzVar;     // ReferenceError
let tdzVar;
```

## Edge cases & interview traps
1. **`typeof` on a TDZ variable throws** — but `typeof` on a truly undeclared identifier returns `"undefined"`.
2. **Function declaration inside `if`** — pre-ES6 hoisted to enclosing function; in strict mode/ESM, block-scoped. Don't rely on it.
3. **`var` redeclaration is silent**; `let` redeclaration is a `SyntaxError` at parse time.
4. **Hoisting order**: function decls hoist *after* `var` bindings, so a same-named function decl wins over `var x;` at creation.
5. **`let` in `for`-loop creates a new binding per iteration** — fixes the classic closure-over-loop bug.
6. **TDZ applies even to `let x = x;`** — the right-hand `x` is accessed before init → throws.
7. **Classes are NOT hoisted like functions** — TDZ until declaration line.
8. **`var` declared inside a `try/catch` parameter shadows** the catch binding in weird ways pre-ES2019.
9. **`function` inside a function is hoisted to the enclosing function scope**, not the block.
10. **CJS `require`** runs the module top-to-bottom synchronously — circular requires return a partial `module.exports`. Hoisting of `function` decls means they're available before the require returns.
11. **ESM `import`** bindings are hoisted to the top of the module and are *live*; reassigning the import throws.
12. **`var` at module top-level in ESM is NOT a global** — unlike scripts where `var x` becomes `globalThis.x`.
13. **Arrow assigned to `const` before use** throws ReferenceError, not TypeError — different signal in stack traces.
14. **Destructuring with `let { a } = obj` is TDZ'd** the same way — `a` doesn't exist until the line runs.
    ```js
    const obj = { a: 1 };
    // console.log(a); // ReferenceError — a is in TDZ
    let { a } = obj;
    ```

## Interview worked examples

### Example 1 — Predict the output (var hoisting)
**Asked as:** "What does this print? `console.log(foo); var foo = 'bar'; console.log(foo);`"

I'd say: "var is hoisted to the top of the function/module scope and initialized to undefined during the creation phase. So the first log sees the binding but not its value yet. Only when execution reaches the assignment does foo become 'bar'."

```js
console.log(foo); // undefined  — binding exists, value not yet assigned
var foo = "bar";
console.log(foo); // "bar"
```

**What the interviewer is testing:** Do you separate "declaration hoisting" from "initialization"?
**Sharp follow-up they often ask:** "What changes if you replace `var` with `let`?" → first log throws ReferenceError (TDZ).

### Example 2 — `typeof` on a TDZ variable
**Asked as:** "Is `typeof x` always safe? Predict: `typeof x; let x = 1;`"

I'd say: "`typeof` is safe on truly undeclared names — returns 'undefined'. But here `x` IS declared as let, so it sits in the TDZ from the start of the block until the `let x = 1` line. Reading it, even via typeof, throws."

```js
typeof undeclared;  // "undefined" — safe
// typeof x;        // ReferenceError — x is declared but in TDZ
let x = 1;
```

**What the interviewer is testing:** TDZ exists for `let`/`const`/`class` from scope start, not from the line.
**Sharp follow-up they often ask:** "What about `class Foo {}`? Same TDZ rule."

### Example 3 — Function declaration vs expression
**Asked as:** "Why does this work for one and not the other?"

I'd say: "Function declarations hoist both the name and the function value. Function expressions assigned to `var` only hoist the `var` binding as undefined — calling undefined throws TypeError."

```js
greet();        // "hi" — function decl fully hoisted
function greet() { console.log("hi"); }

// sayHi();     // TypeError: sayHi is not a function
var sayHi = function () { console.log("hi"); };
```

**What the interviewer is testing:** Function decl vs function expression hoisting asymmetry.
**Sharp follow-up they often ask:** "What if `sayHi` is on `let` or `const`?" → ReferenceError instead of TypeError, signalling TDZ vs undefined.

### Example 4 — `let` in `for` + `setTimeout` (the classic)
**Asked as:** "What does each loop print?"

I'd say: "With `var`, all three closures share one binding `i`, which is 3 by the time the timers fire. With `let`, the spec creates a fresh `i` binding per iteration, so each closure captures its own."

```js
for (var i = 0; i < 3; i++) setTimeout(() => console.log(i)); // 3 3 3
for (let j = 0; j < 3; j++) setTimeout(() => console.log(j)); // 0 1 2
```

**What the interviewer is testing:** Per-iteration binding semantics of `let` in `for` headers.
**Sharp follow-up they often ask:** "Fix the var version without using let." → wrap body in IIFE `(function(j){ setTimeout(...); })(i)`.

### Example 5 — Class hoisting
**Asked as:** "Will this run? `new Foo(); class Foo {}`"

I'd say: "No — classes are hoisted but TDZ-locked until the declaration line, unlike function declarations. The `new Foo()` call sits in the TDZ window and throws ReferenceError."

```js
// new Foo();          // ReferenceError: Cannot access 'Foo' before initialization
class Foo { constructor() { this.x = 1; } }
new Foo();             // works
```

**What the interviewer is testing:** Whether you know class differs from function in hoisting.
**Sharp follow-up they often ask:** "Why did the designers choose TDZ for class?" → Catch bugs early; avoid the foot-gun of partial constructor before fields.

### Example 6 — Function declaration inside `if`
**Asked as:** "Is this code portable? `if (true) { function bar() {} } bar();`"

I'd say: "Pre-ES6 / sloppy mode in some engines, `bar` leaked to the function scope. In strict mode and ESM (and per spec), function declarations inside blocks are block-scoped — so `bar()` outside the block throws. Treat this as undefined behavior in production."

```js
"use strict";
if (true) { function bar() { return 1; } }
// bar(); // ReferenceError in strict mode
```

**What the interviewer is testing:** Awareness of strict mode block-scoped function declarations.
**Sharp follow-up they often ask:** "How would you reliably declare bar conditionally?" → assign a function expression to a `let` declared outside the block.

## Common machine-coding patterns
- **Output prediction with var/let mix** — when used: warm-up rounds. Sketch: `console.log(x); var x = 1; let y;` predict outputs.
- **Loop closure fix using `let`** — when used: async callbacks inside loops. Sketch:
  ```js
  for (let i = 0; i < n; i++) queue.push(() => i);
  ```
- **IIFE to avoid `var` leakage** — when used: legacy code, sandboxing. Sketch:
  ```js
  (function() { var private = 1; })();
  ```
- **Function declaration vs expression for circular deps** — when used: CJS modules referencing each other. Hoisted `function` decls survive partial loads; `module.exports = () => ...` assignments don't.

## Backend-specific notes
In Node, every CommonJS file is wrapped in a function `(function(exports, require, module, __filename, __dirname){ ... })`, so module top-level `var` is function-scoped — never global. Circular `require` returns whatever `module.exports` looked like at the point of re-entry; if you rely on a hoisted function declaration that was assigned to `module.exports` *after* the require, the partial export bites you. Defensive pattern: `module.exports.fn = function fn(){}` instead of `module.exports = { fn }` at the bottom.

In ESM (`.mjs` / `"type": "module"`), imports are statically resolved and hoisted — the engine builds the dependency graph before executing any module body, so circular ESM works better than circular CJS, but live bindings means you read the *current* value, not the value at import time.

## 60-second revision (day-before)
```text
┌──────────────────────────────────────────────────────────┐
│ HOISTING — DAY-BEFORE CRAM                               │
├──────────────────────────────────────────────────────────┤
│ • var: hoisted, = undefined, function-scoped, redeclare ok│
│ • let/const/class: hoisted + TDZ (ReferenceError)        │
│ • function decl: hoisted with VALUE; can call above line │
│ • function expr / arrow: only var name hoisted           │
│ • typeof TDZ → throws; typeof undeclared → "undefined"   │
│ • for(let): new binding per iter → closure-loop fix      │
│ • Classes: TDZ, NOT function-style hoisted               │
│ • ESM: imports hoisted + live + read-only                │
│ • CJS: top-down sync; circular → partial module.exports  │
│ • let x = x → TDZ on RHS → throws                        │
│ • Function decl beats var of same name in creation phase │
└──────────────────────────────────────────────────────────┘
```
